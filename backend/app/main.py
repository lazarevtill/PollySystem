# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.exceptions import PollySystemException, APIError
from app.core.plugin_manager import plugin_manager
from app.api.v1.router import get_api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application"""
    settings = get_settings()
    
    # Startup
    logger.info("Starting PollySystem...")
    try:
        # Register app with plugin manager
        plugin_manager.register_app(app)
        
        # Discover and initialize plugins
        await plugin_manager.discover_plugins()
        logger.info("All plugins loaded successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    # Shutdown
    logger.info("Shutting down PollySystem...")
    try:
        await plugin_manager.cleanup_plugins()
        logger.info("All plugins cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="A modular system for managing infrastructure and deployments",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=["*"]
    )

    # Rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        from app.core.auth import rate_limiter
        client_ip = request.client.host

        if not await rate_limiter.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )

        return await call_next(request)

    # Exception handlers
    @app.exception_handler(PollySystemException)
    async def pollysystem_exception_handler(request: Request, exc: PollySystemException):
        return JSONResponse(
            status_code=500,
            content=exc.to_dict()
        )

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "plugins": list(plugin_manager.plugins.keys())
        }

    # Include API routers
    app.include_router(
        get_api_router(),
        prefix=settings.API_V1_STR
    )

    return app

# Create application instance
app = create_app()

# Run application
if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )