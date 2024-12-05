# backend/app/plugins/base.py
from fastapi import APIRouter
from typing import Dict, Any

class Plugin(BasePlugin):
    """Base plugin implementation"""
    def __init__(self):
        self.router = APIRouter()
        self._state: Dict[str, Any] = {}

    def get_state(self) -> Dict[str, Any]:
        """Get plugin state"""
        return self._state

    def set_state(self, state: Dict[str, Any]):
        """Set plugin state"""
        self._state = state

