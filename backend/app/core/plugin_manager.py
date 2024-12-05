# backend/app/core/plugin_manager.py
from typing import Dict, Optional, Any, List
from fastapi import FastAPI, APIRouter
import importlib
import pkgutil
import logging
from contextlib import asynccontextmanager
import asyncio
from dataclasses import dataclass

from app.plugins.base import Plugin
from .exceptions import PluginError

logger = logging.getLogger(__name__)

@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    name: str
    version: str
    description: str
    dependencies: List[str]
    requires_auth: bool = True

class PluginManager:
    """Manages plugin lifecycle and interactions"""
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.app: Optional[FastAPI] = None
        self._initialized = False
        self._plugin_services: Dict[str, Any] = {}

    def register_app(self, app: FastAPI):
        """Register the FastAPI application"""
        self.app = app
        self.app.state.plugin_services = self._plugin_services

    async def discover_plugins(self):
        """Discover and load all available plugins"""
        if self._initialized:
            return

        if not self.app:
            raise PluginError("No FastAPI application registered", "plugin_manager")

        logger.info("Discovering plugins...")
        
        # Import all plugin modules
        import app.plugins as plugins_package
        discovered_plugins = {}

        for _, name, _ in pkgutil.iter_modules(plugins_package.__path__):
            try:
                module = importlib.import_module(f"app.plugins.{name}")
                
                # Look for plugin class
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                        plugin_class = attr
                        break

                if plugin_class:
                    # Get plugin metadata
                    metadata = plugin_class.get_metadata()
                    discovered_plugins[metadata.name] = (plugin_class, metadata)
                    logger.info(f"Discovered plugin: {metadata.name} v{metadata.version}")
                
            except Exception as e:
                logger.error(f"Failed to discover plugin {name}: {str(e)}")
                raise PluginError(f"Plugin discovery failed for {name}: {str(e)}", "plugin_manager")

        # Sort plugins by dependencies
        sorted_plugins = self._sort_plugins_by_dependencies(discovered_plugins)

        # Initialize plugins in order
        for plugin_name in sorted_plugins:
            plugin_class, metadata = discovered_plugins[plugin_name]
            try:
                plugin = plugin_class()
                plugin.register_app(self.app)
                await plugin.initialize()
                self.plugins[metadata.name] = plugin
                logger.info(f"Initialized plugin: {metadata.name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin_name}: {str(e)}")
                raise PluginError(f"Plugin initialization failed for {plugin_name}: {str(e)}", "plugin_manager")

        self._initialized = True
        logger.info(f"Loaded {len(self.plugins)} plugins successfully")

    def _sort_plugins_by_dependencies(self, plugins: Dict[str, tuple]) -> List[str]:
        """Sort plugins based on their dependencies"""
        sorted_plugins = []
        visited = set()
        visiting = set()

        def visit(name: str):
            if name in visiting:
                raise PluginError(f"Circular dependency detected for plugin {name}", "plugin_manager")
            if name in visited:
                return

            visiting.add(name)
            plugin_class, metadata = plugins[name]
            
            for dep in metadata.dependencies:
                if dep not in plugins:
                    raise PluginError(f"Plugin {name} depends on unknown plugin {dep}", "plugin_manager")
                visit(dep)

            visiting.remove(name)
            visited.add(name)
            sorted_plugins.append(name)

        for name in plugins:
            if name not in visited:
                visit(name)

        return sorted_plugins

    async def cleanup_plugins(self):
        """Cleanup all plugins"""
        logger.info("Cleaning up plugins...")
        cleanup_tasks = []

        for name, plugin in self.plugins.items():
            try:
                task = asyncio.create_task(plugin.cleanup())
                task.set_name(f"cleanup_{name}")
                cleanup_tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating cleanup task for plugin {name}: {str(e)}")

        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks)
            except Exception as e:
                logger.error(f"Error during plugin cleanup: {str(e)}")

        self.plugins.clear()
        self._plugin_services.clear()
        self._initialized = False
        logger.info("Plugin cleanup completed")

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name"""
        return self.plugins.get(name)

    def get_service(self, name: str) -> Optional[Any]:
        """Get a plugin service by name"""
        return self._plugin_services.get(name)

    def register_service(self, name: str, service: Any):
        """Register a plugin service"""
        self._plugin_services[name] = service

    def get_all_routers(self) -> Dict[str, APIRouter]:
        """Get all plugin routers"""
        return {name: plugin.router for name, plugin in self.plugins.items()}

    @property
    def initialized(self) -> bool:
        """Check if plugin manager is initialized"""
        return self._initialized

# Global plugin manager instance
plugin_manager = PluginManager()