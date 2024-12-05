# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.core.plugin_manager import plugin_manager

router = APIRouter()

def get_api_router() -> APIRouter:
    """Get the main API router with all plugin routes included"""
    # Include all plugin routers
    for name, plugin_router in plugin_manager.get_all_routers().items():
        router.include_router(
            plugin_router,
            prefix=f"/{name}",
            tags=[name.capitalize()]  # Use capitalized plugin name as tag
        )

    return router