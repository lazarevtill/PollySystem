# backend/app/__init__.py
"""
PollySystem Backend Application
"""
from app.core.config import get_settings

__version__ = get_settings().VERSION
