# backend/app/main.py
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from contextlib import asynccontextmanager
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import aioredis
from typing import Callable
import json
from datetime import datetime

from app.core.config import get_settings
from app.core.exceptions import PollySystemException, APIError
from app.core.plugin_manager import plugin_manager
from app.core.auth import rate_limiter
from app.api.v1.router import get_api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Setup structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

PLUGIN_OPERATIONS = Counter(
    'plugin_operations_total',
    'Total plugin operations',
    ['plugin', 'operation', 'status']
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application"""
    settings = get_settings()
    
    # Startup
    logger.info("starting_application", version=settings.VERSION)
    try:
        # Initialize Redis
        app.state.redis = aioredis.from_url(
            settings.get_redis_url(),
            encoding="utf-8",
            decode_responses=True
        )
        
        # Register app with plugin manager
        plugin_manager.register_app(app)
        
        # Discover and initialize plugins
        await plugin_manager.discover_plugins()
        logger.info("plugins_loaded", count=len(plugin_manager.plugins))
        
        yield
        
    except Exception as e:
        logger.error("startup_failed", error=str(e))
        raise
    
    # Shutdown
    logger.info("shutting_down_application")
    try:
        # Cleanup plugins
        await plugin_manager.cleanup_plugins()
        
        # Close Redis connection
        await app.state.redis.close()
        
        logger.info("shutdown_complete")
    except Exception as e:
        logger.error("shutdown_failed", error=str(e))

class RequestLoggingMiddleware:
    """Middleware for request logging and metrics"""
    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        request = Request(scope, receive)
        response = Response(content=None, media_type=None)
        
        # Create a response sender that captures the status code
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response.status_code = message["status"]
            await send(message)

        try:
            # Log request
            logger.info(
                "request_started",
                method=request.method,
                url=str(request.url),
                client_ip=request.client.host if request.client else None,
            )

            await self.app(scope, receive, send_wrapper)

            # Record metrics
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()

            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                duration=duration,
            )
            raise

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

    # Add request logging middleware
    app.middleware("http")(RequestLoggingMiddleware(app))

    # Rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: Callable):
        # Skip rate limiting for metrics and health check
        if request.url.path in ["/metrics", "/health"]:
            return await call_next(request)

        client_ip = request.client.host
        if not await rate_limiter.check_rate_limit(client_ip):
            logger.warning("rate_limit_exceeded", client_ip=client_ip)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"}
            )

        return await call_next(request)

    # Exception handlers
    @app.exception_handler(PollySystemException)
    async def pollysystem_exception_handler(request: Request, exc: PollySystemException):
        logger.error(
            "pollysystem_exception",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            details=exc.details
        )
        return JSONResponse(
            status_code=500,
            content=exc.to_dict()
        )

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        logger.error(
            "api_error",
            status_code=exc.status_code,
            error_message=str(exc.detail)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers
        )

    # Prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "plugins": [
                {
                    "name": name,
                    "version": plugin.get_metadata().version,
                    "status": "active" if plugin.is_enabled else "disabled"
                }
                for name, plugin in plugin_manager.plugins.items()
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    # System information endpoint
    @app.get("/system")
    async def system_info():
        return {
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "plugins_enabled": len(plugin_manager.plugins),
            "redis_connected": app.state.redis.ping(),
            "system_time": datetime.utcnow().isoformat()
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
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )