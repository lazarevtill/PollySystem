# backend/app/core/plugin_manager.py
from typing import Dict, List, Type
import importlib
import pkgutil
import inspect
from fastapi import APIRouter
from pydantic import BaseModel

class PluginMetadata(BaseModel):
    """Plugin metadata including its capabilities and requirements"""
    name: str
    version: str
    description: str
    dependencies: List[str] = []
    requires_auth: bool = False

class BasePlugin:
    """Base class for all plugins"""
    metadata: PluginMetadata
    router: APIRouter

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        """Return plugin metadata"""
        raise NotImplementedError()

    @classmethod
    def initialize(cls) -> 'BasePlugin':
        """Initialize plugin instance"""
        raise NotImplementedError()

class PluginManager:
    """Manages plugin discovery, loading, and lifecycle"""
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.routers: Dict[str, APIRouter] = {}

    def discover_plugins(self, plugins_package='app.plugins'):
        """Discover all available plugins"""
        package = importlib.import_module(plugins_package)
        
        for _, name, ispkg in pkgutil.iter_modules(package.__path__):
            if ispkg:
                module = importlib.import_module(f'{plugins_package}.{name}')
                for item_name, item in inspect.getmembers(module):
                    if (inspect.isclass(item) and 
                        issubclass(item, BasePlugin) and 
                        item != BasePlugin):
                        try:
                            plugin = item.initialize()
                            metadata = item.get_metadata()
                            self.plugins[metadata.name] = plugin
                            self.routers[metadata.name] = plugin.router
                        except Exception as e:
                            print(f"Failed to load plugin {name}: {str(e)}")

    def get_plugin(self, name: str) -> BasePlugin:
        """Get plugin instance by name"""
        return self.plugins.get(name)

    def get_all_routers(self) -> Dict[str, APIRouter]:
        """Get all plugin routers"""
        return self.routers
