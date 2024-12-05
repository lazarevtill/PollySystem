# backend/app/core/plugin_manager.py
from typing import Dict, Optional, Type, Any
from fastapi import FastAPI, APIRouter
import importlib
import pkgutil
import logging
from contextlib import asynccontextmanager

from app.plugins.base import Plugin
from .exceptions import PluginError

logger = logging.getLogger(__name__)

class PluginMetadata:
    """Metadata for a plugin"""
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        dependencies: list[str] = None,
        requires_auth: bool = True
    ):
        self.name = name
        self.version = version
        self.description = description
        self.dependencies = dependencies or []
        self.requires_auth = requires_auth

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.app: Optional[FastAPI] = None
        self._initialized = False

    def register_app(self, app: FastAPI):
        """Register the FastAPI application"""
        self.app = app

    async def discover_plugins(self):
        """Discover and load all available plugins"""
        if self._initialized:
            return

        if not self.app:
            raise PluginError("No FastAPI application registered")

        logger.info("Discovering plugins...")
        
        # Import all plugin modules
        import app.plugins as plugins_package
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
                    
                    # Check dependencies
                    for dep in metadata.dependencies:
                        if dep not in self.plugins:
                            raise PluginError(f"Plugin {name} depends on {dep} which is not loaded")
                    
                    # Initialize plugin
                    plugin = plugin_class()
                    await plugin.initialize()
                    
                    # Store plugin
                    self.plugins[metadata.name] = plugin
                    
                    logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
                
            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {str(e)}")
                raise PluginError(f"Plugin {name} failed to load: {str(e)}")

        self._initialized = True
        logger.info(f"Loaded {len(self.plugins)} plugins")

    async def cleanup_plugins(self):
        """Cleanup all plugins"""
        logger.info("Cleaning up plugins...")
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin: {str(e)}")

        self.plugins.clear()
        self._initialized = False

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name"""
        return self.plugins.get(name)

    def get_all_routers(self) -> Dict[str, APIRouter]:
        """Get all plugin routers"""
        return {name: plugin.router for name, plugin in self.plugins.items()}

# Global plugin manager instance
plugin_manager = PluginManager()