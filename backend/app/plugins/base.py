# backend/app/plugins/base.py
from fastapi import APIRouter, FastAPI
from typing import Dict, Any, Optional, ClassVar
from pydantic import BaseModel
from abc import ABC, abstractmethod

from app.core.plugin_manager import PluginMetadata

class PluginState(BaseModel):
    """Base class for plugin state"""
    pass

class Plugin(ABC):
    """Base plugin implementation"""
    def __init__(self):
        self.router = APIRouter()
        self._state: Optional[PluginState] = None
        self.app: Optional[FastAPI] = None

    @property
    def state(self) -> Optional[PluginState]:
        """Get plugin state"""
        return self._state

    @state.setter
    def state(self, state: PluginState):
        """Set plugin state"""
        self._state = state

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> PluginMetadata:
        """Get plugin metadata"""
        raise NotImplementedError

    async def initialize(self) -> None:
        """Initialize the plugin"""
        pass

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass

    def register_app(self, app: FastAPI):
        """Register the FastAPI application"""
        self.app = app

    def get_service(self, name: str) -> Any:
        """Get a service from another plugin"""
        if not self.app:
            raise RuntimeError("Plugin not initialized with FastAPI app")
        return self.app.state.plugin_services.get(name)

    def register_service(self, name: str, service: Any):
        """Register a service for other plugins to use"""
        if not self.app:
            raise RuntimeError("Plugin not initialized with FastAPI app")
        if not hasattr(self.app.state, 'plugin_services'):
            self.app.state.plugin_services = {}
        self.app.state.plugin_services[name] = service