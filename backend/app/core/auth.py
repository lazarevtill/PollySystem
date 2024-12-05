# backend/app/core/auth.py
from datetime import datetime, timedelta
import jwt
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

security = HTTPBearer()
settings = get_settings()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token with secure algorithm"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token with secure algorithm"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Additional security checks
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Check expiration
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get current user from JWT token"""
    try:
        payload = verify_token(credentials.credentials)
        if not payload.get("sub"):
            raise AuthenticationError("User ID not found in token")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

class RateLimiter:
    """Simple rate limiter implementation"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def check_rate_limit(self, key: str) -> bool:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests = {
            k: v for k, v in self.requests.items()
            if v[-1] > window_start
        }

        # Check current requests
        if key not in self.requests:
            self.requests[key] = []
        
        self.requests[key] = [
            t for t in self.requests[key]
            if t > window_start
        ]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True

# Initialize rate limiter
rate_limiter = RateLimiter()