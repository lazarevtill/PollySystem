# backend/app/core/plugin_manager.py
from typing import Dict, Optional, Any
from fastapi import FastAPI, APIRouter
import importlib
import pkgutil
import logging
import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict

from app.core.exceptions import PluginError
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class PluginMetadata:
    """Metadata for a plugin"""
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        dependencies: list[str] = None,
        requires_auth: bool = True,
        config_schema: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.version = version
        self.description = description
        self.dependencies = dependencies or []
        self.requires_auth = requires_auth
        self.config_schema = config_schema

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, 'Plugin'] = {}
        self.app: Optional[FastAPI] = None
        self._initialized = False
        self._services: Dict[str, Any] = {}
        self._dependency_graph: Dict[str, set] = defaultdict(set)
        self.settings = get_settings()

    def register_app(self, app: FastAPI):
        """Register the FastAPI application"""
        self.app = app
        self.app.state.plugin_services = {}

    def register_service(self, name: str, service: Any):
        """Register a service that can be used by other plugins"""
        self._services[name] = service
        if self.app:
            self.app.state.plugin_services[name] = service

    def get_service(self, name: str) -> Optional[Any]:
        """Get a registered service by name"""
        return self._services.get(name)

    async def discover_plugins(self):
        """Discover and load all available plugins"""
        if self._initialized:
            return

        if not self.app:
            raise PluginError("No FastAPI application registered", "system")

        logger.info("Discovering plugins...")
        
        try:
            # Import all plugin modules
            import app.plugins as plugins_package
            discovered_plugins = {}

            for _, name, _ in pkgutil.iter_modules(plugins_package.__path__):
                if name not in self.settings.ENABLED_PLUGINS:
                    continue

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
                        metadata = plugin_class.get_metadata()
                        discovered_plugins[metadata.name] = (plugin_class, metadata)
                        
                        # Build dependency graph
                        for dep in metadata.dependencies:
                            self._dependency_graph[metadata.name].add(dep)
                
                except Exception as e:
                    logger.error(f"Failed to load plugin {name}: {str(e)}")
                    raise PluginError(f"Plugin {name} failed to load: {str(e)}", name)

            # Initialize plugins in dependency order
            initialized_plugins = set()
            while discovered_plugins:
                ready_plugins = {
                    name: (cls, meta) for name, (cls, meta) in discovered_plugins.items()
                    if all(dep in initialized_plugins for dep in self._dependency_graph[name])
                }

                if not ready_plugins:
                    remaining = list(discovered_plugins.keys())
                    raise PluginError(
                        f"Circular dependency detected in plugins: {remaining}",
                        "system"
                    )

                for name, (plugin_class, metadata) in ready_plugins.items():
                    try:
                        plugin = plugin_class()
                        plugin.register_app(self.app)
                        await plugin.initialize()
                        self.plugins[name] = plugin
                        initialized_plugins.add(name)
                        del discovered_plugins[name]
                        logger.info(f"Initialized plugin: {name} v{metadata.version}")
                    except Exception as e:
                        logger.error(f"Failed to initialize plugin {name}: {str(e)}")
                        raise PluginError(f"Plugin {name} initialization failed: {str(e)}", name)

            self._initialized = True
            logger.info(f"Loaded {len(self.plugins)} plugins successfully")

        except Exception as e:
            logger.error(f"Plugin discovery failed: {str(e)}")
            raise

    async def cleanup_plugins(self):
        """Cleanup all plugins"""
        logger.info("Cleaning up plugins...")
        cleanup_tasks = []

        # Create cleanup tasks in reverse dependency order
        for name in reversed(list(self.plugins.keys())):
            plugin = self.plugins[name]
            task = asyncio.create_task(plugin.cleanup())
            cleanup_tasks.append(task)

        # Wait for all cleanup tasks to complete
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        self.plugins.clear()
        self._services.clear()
        self._dependency_graph.clear()
        self._initialized = False
        logger.info("All plugins cleaned up")

    def get_plugin(self, name: str) -> Optional['Plugin']:
        """Get a plugin by name"""
        return self.plugins.get(name)

    def get_all_routers(self) -> Dict[str, APIRouter]:
        """Get all plugin routers"""
        return {name: plugin.router for name, plugin in self.plugins.items()}

    @property
    def initialized(self) -> bool:
        """Check if plugin manager is initialized"""
        return self._initialized

# Global plugin manager instance
plugin_manager = PluginManager()