# backend/app/main.py
from fastapi import FastAPI
from app.core.plugin_manager import PluginManager

def create_app() -> FastAPI:
    app = FastAPI(title="PollySystem")
    
    # Initialize plugin manager
    plugin_manager = PluginManager()
    plugin_manager.discover_plugins()
    
    # Register plugin routers
    for name, router in plugin_manager.get_all_routers().items():
        app.include_router(router, prefix=f"/api/v1/{name}")
    
    return app

app = create_app()
