"""
Rate Limiting Middleware
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent API abuse.
    
    Implements sliding window rate limiting per client IP or API key.
    """
    
    def __init__(self, app, requests_per_minute: int = 100, burst: int = 150):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute
            burst: Maximum burst requests
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.clients: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every minute
        
        # Start cleanup task
        asyncio.create_task(self.cleanup_old_entries())
        
    async def dispatch(self, request: Request, call_next):
        """
        Process request and apply rate limiting.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Get client identifier (API key or IP)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id):
            # Get retry-after time
            retry_after = self._get_retry_after(client_id)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Record request
        self._record_request(client_id)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining, reset_time = self._get_rate_limit_info(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Get requests in last minute
        recent_requests = [
            req_time for req_time in self.clients[client_id]
            if req_time > minute_ago
        ]
        
        # Check burst limit
        if len(recent_requests) >= self.burst:
            return False
        
        # Check per-minute limit
        if len(recent_requests) >= self.requests_per_minute:
            return False
        
        return True
    
    def _record_request(self, client_id: str):
        """Record a request for rate limiting."""
        self.clients[client_id].append(datetime.now())
    
    def _get_rate_limit_info(self, client_id: str) -> Tuple[int, datetime]:
        """Get current rate limit status."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Count recent requests
        recent_requests = [
            req_time for req_time in self.clients[client_id]
            if req_time > minute_ago
        ]
        
        remaining = max(0, self.requests_per_minute - len(recent_requests))
        
        # Calculate reset time (1 minute from oldest request)
        if recent_requests:
            oldest = min(recent_requests)
            reset_time = oldest + timedelta(minutes=1)
        else:
            reset_time = now + timedelta(minutes=1)
        
        return remaining, reset_time
    
    def _get_retry_after(self, client_id: str) -> int:
        """Calculate retry-after time in seconds."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        recent_requests = [
            req_time for req_time in self.clients[client_id]
            if req_time > minute_ago
        ]
        
        if not recent_requests:
            return 0
        
        # Time until oldest request expires
        oldest = min(recent_requests)
        retry_after = (oldest + timedelta(minutes=1) - now).total_seconds()
        return max(1, int(retry_after))
    
    async def cleanup_old_entries(self):
        """Periodically clean up old request records."""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            
            now = datetime.now()
            cutoff = now - timedelta(minutes=5)  # Keep 5 minutes of history
            
            # Clean up old entries
            for client_id in list(self.clients.keys()):
                self.clients[client_id] = [
                    req_time for req_time in self.clients[client_id]
                    if req_time > cutoff
                ]
                
                # Remove empty entries
                if not self.clients[client_id]:
                    del self.clients[client_id]


class RateLimiter:
    """Simple rate limiter for function-level rate limiting."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Check if a call is allowed."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # Filter old calls
        self.calls[key] = [
            call_time for call_time in self.calls[key]
            if call_time > cutoff
        ]
        
        # Check limit
        if len(self.calls[key]) >= self.max_calls:
            return False
        
        # Record call
        self.calls[key].append(now)
        return True
    
    def get_wait_time(self, key: str) -> float:
        """Get time to wait before next call is allowed."""
        if not self.calls[key]:
            return 0.0
        
        now = datetime.now()
        oldest = min(self.calls[key])
        wait_until = oldest + timedelta(seconds=self.time_window)
        
        if wait_until <= now:
            return 0.0
        
        return (wait_until - now).total_seconds()