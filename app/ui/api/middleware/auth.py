"""
Authentication Middleware
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional
import jwt
from datetime import datetime, timedelta

# Security schemes
security_bearer = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Configuration (in production, use environment variables)
SECRET_KEY = "your-secret-key-here"  # Change this!
ALGORITHM = "HS256"
API_KEYS = {
    "admin-key-123": {"role": "admin", "user_id": "admin-1"},
    "user-key-456": {"role": "user", "user_id": "user-1"}
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer)
) -> dict:
    """
    Verify JWT bearer token.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        User information from token
    """
    token = credentials.credentials
    return decode_token(token)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> dict:
    """
    Verify API key.
    
    Args:
        api_key: API key from header
        
    Returns:
        User information associated with API key
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return API_KEYS[api_key]


async def verify_admin(user_info: dict = Security(verify_api_key)) -> dict:
    """
    Verify admin role.
    
    Args:
        user_info: User information from API key
        
    Returns:
        User information if admin
    """
    if user_info.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user_info


async def optional_auth(api_key: Optional[str] = Security(api_key_header)) -> Optional[dict]:
    """
    Optional authentication - doesn't fail if no credentials provided.
    
    Args:
        api_key: Optional API key
        
    Returns:
        User information or None
    """
    if not api_key:
        return None
    
    return API_KEYS.get(api_key)


class AuthManager:
    """Manage authentication and authorization."""
    
    def __init__(self):
        self.api_keys = API_KEYS
        
    def validate_api_key(self, api_key: str) -> bool:
        """Check if API key is valid."""
        return api_key in self.api_keys
    
    def get_user_from_key(self, api_key: str) -> Optional[dict]:
        """Get user information from API key."""
        return self.api_keys.get(api_key)
    
    def is_admin(self, api_key: str) -> bool:
        """Check if API key has admin privileges."""
        user = self.get_user_from_key(api_key)
        return user and user.get("role") == "admin"
    
    def create_api_key(self, user_id: str, role: str = "user") -> str:
        """Generate a new API key for a user."""
        import secrets
        api_key = f"{role}-key-{secrets.token_hex(16)}"
        self.api_keys[api_key] = {"role": role, "user_id": user_id}
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            return True
        return False


# Global auth manager instance
auth_manager = AuthManager()