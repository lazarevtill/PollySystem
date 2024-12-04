from pydantic_settings import BaseSettings
import secrets
from pathlib import Path

class Settings(BaseSettings):
    # Base settings
    PROJECT_NAME: str = "Infrastructure Manager"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./infra_manager.db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Nginx
    NGINX_TEMPLATE_PATH: Path = Path("/opt/infra-manager/backend/nginx/templates")
    NGINX_CONFIG_PATH: Path = Path("/etc/nginx/conf.d")
    
    # SSL/TLS
    SSL_CERT_PATH: Path = Path("/etc/letsencrypt/live/booktime.today/fullchain.pem")
    SSL_KEY_PATH: Path = Path("/etc/letsencrypt/live/booktime.today/privkey.pem")
    
    # Domain settings
    PUBLIC_DOMAIN: str = "booktime.today"
    VPN_DOMAIN: str = "in.lc"
    ADMIN_SUBDOMAIN: str = "kafa.lazarev.cloud"
    
    # SSH settings
    SSH_KEY_TYPE: str = "rsa"
    SSH_KEY_BITS: int = 4096
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
