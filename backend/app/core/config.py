# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    # Basic
    PROJECT_NAME: str = "PollySystem"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_V1_STR: str = "/api/v1"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    API_TOKEN_HEADER: str = "X-API-Token"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_USERNAME: Optional[str] = None
    REDIS_USE_SSL: bool = False

    # Plugin System
    PLUGIN_DIR: str = "app.plugins"
    ENABLED_PLUGINS: List[str] = ["machines", "docker", "monitoring"]
    PLUGIN_CONFIG_DIR: str = "config/plugins"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "logs/pollysystem.log"

    # Machine Management
    SSH_CONNECTION_TIMEOUT: int = 10
    SSH_RETRY_ATTEMPTS: int = 3
    SSH_RETRY_DELAY: int = 5
    DEFAULT_SSH_USER: str = "ubuntu"
    DEFAULT_SSH_PORT: int = 22

    # Docker
    DOCKER_SOCKET_PATH: str = "unix:///var/run/docker.sock"
    DOCKER_REGISTRY: Optional[str] = None
    DOCKER_REGISTRY_USERNAME: Optional[str] = None
    DOCKER_REGISTRY_PASSWORD: Optional[str] = None
    
    # Prometheus Metrics
    ENABLE_PROMETHEUS: bool = True
    PROMETHEUS_PORT: int = 9090

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        auth_part = ""
        if self.REDIS_USERNAME and self.REDIS_PASSWORD:
            auth_part = f"{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@"
        elif self.REDIS_PASSWORD:
            auth_part = f":{self.REDIS_PASSWORD}@"
        
        scheme = "rediss" if self.REDIS_USE_SSL else "redis"
        return f"{scheme}://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def ensure_directories(self) -> None:
        """Ensure required directories exist"""
        directories = [
            Path(self.PLUGIN_CONFIG_DIR),
            Path(self.LOG_FILE).parent if self.LOG_FILE else None,
            Path("logs")
        ]
        
        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.ensure_directories()
    return settings