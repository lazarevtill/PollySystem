
# backend/app/api/__init__.py
"""
API package for PollySystem
"""
from fastapi import APIRouter
from .v1.router import get_api_router

router = APIRouter()
router.include_router(get_api_router(), prefix="/v1")
