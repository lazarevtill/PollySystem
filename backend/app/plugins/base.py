# backend/app/plugins/base.py
from fastapi import APIRouter, FastAPI
from typing import Dict, Any, Optional, ClassVar, Type
from pydantic import BaseModel
from abc import ABC, abstractmethod
import logging

from app.core.plugin_manager import PluginMetadata
from app.core.exceptions import PluginError

logger = logging.getLogger(__name__)

class PluginState(BaseModel):
    """Base class for plugin state"""
    enabled: bool = True
    initialized: bool = False
    config: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True

class Plugin(ABC):
    """Base plugin implementation"""
    state_model: ClassVar[Type[PluginState]] = PluginState

    def __init__(self):
        self.router = APIRouter()
        self._state: Optional[PluginState] = None
        self.app: Optional[FastAPI] = None
        self._cleanup_tasks: list = []

    @property
    def state(self) -> Optional[PluginState]:
        """Get plugin state"""
        return self._state

    @state.setter
    def state(self, state: PluginState):
        """Set plugin state"""
        if not isinstance(state, self.state_model):
            raise TypeError(f"State must be an instance of {self.state_model.__name__}")
        self._state = state

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> PluginMetadata:
        """Get plugin metadata"""
        raise NotImplementedError

    async def initialize(self) -> None:
        """Initialize the plugin"""
        try:
            metadata = self.get_metadata()
            logger.info(f"Initializing plugin: {metadata.name}")
            
            # Create initial state
            self._state = self.state_model(
                enabled=True,
                initialized=False,
                config={}
            )

            # Initialize state
            await self.setup_state()
            
            # Mark as initialized
            self._state.initialized = True
            logger.info(f"Plugin {metadata.name} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize plugin: {str(e)}")
            raise PluginError(f"Plugin initialization failed: {str(e)}", self.get_metadata().name)

    async def setup_state(self) -> None:
        """Setup plugin state - can be overridden by plugins"""
        pass

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        try:
            metadata = self.get_metadata()
            logger.info(f"Cleaning up plugin: {metadata.name}")
            
            # Execute cleanup tasks
            for task in self._cleanup_tasks:
                try:
                    if callable(task):
                        await task()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {str(e)}")

            # Clear state
            self._state = None
            logger.info(f"Plugin {metadata.name} cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during plugin cleanup: {str(e)}")
            raise PluginError(f"Plugin cleanup failed: {str(e)}", self.get_metadata().name)

    def register_app(self, app: FastAPI):
        """Register the FastAPI application"""
        self.app = app

    def register_cleanup_task(self, task):
        """Register a cleanup task"""
        self._cleanup_tasks.append(task)

    def get_service(self, name: str) -> Any:
        """Get a service from another plugin"""
        if not self.app:
            raise RuntimeError("Plugin not initialized with FastAPI app")
        
        service = self.app.state.plugin_services.get(name)
        if not service:
            raise PluginError(f"Service {name} not found", self.get_metadata().name)
        
        return service

    def register_service(self, name: str, service: Any):
        """Register a service for other plugins to use"""
        if not self.app:
            raise RuntimeError("Plugin not initialized with FastAPI app")
        
        if not hasattr(self.app.state, 'plugin_services'):
            self.app.state.plugin_services = {}
        
        self.app.state.plugin_services[name] = service
        logger.info(f"Registered service: {name}")

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized"""
        return self._state is not None and self._state.initialized

    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self._state is not None and self._state.enabled

    def enable(self):
        """Enable the plugin"""
        if self._state:
            self._state.enabled = True
            logger.info(f"Plugin {self.get_metadata().name} enabled")

    def disable(self):
        """Disable the plugin"""
        if self._state:
            self._state.enabled = False
            logger.info(f"Plugin {self.get_metadata().name} disabled")