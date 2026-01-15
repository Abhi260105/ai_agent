"""
Logging Middleware
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import json
from datetime import datetime
from typing import Callable

# Configure logger
logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Log request and response details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Generate request ID
        request_id = f"req-{int(time.time() * 1000)}"
        
        # Log request
        start_time = time.time()
        
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        logger.info(f"Request: {json.dumps(log_data)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            response_data = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }
            
            # Add request ID header
            response.headers["X-Request-ID"] = request_id
            
            logger.info(f"Response: {json.dumps(response_data)}")
            
            return response
            
        except Exception as exc:
            # Log error
            duration = time.time() - start_time
            
            error_data = {
                "request_id": request_id,
                "error": str(exc),
                "duration_ms": round(duration * 1000, 2)
            }
            
            logger.error(f"Error: {json.dumps(error_data)}", exc_info=True)
            raise


class APILogger:
    """Structured API logger."""
    
    def __init__(self, name: str):
        """Initialize logger."""
        self.logger = logging.getLogger(name)
        
    def log_request(
        self,
        method: str,
        path: str,
        user_id: str = None,
        **kwargs
    ):
        """Log API request."""
        data = {
            "type": "request",
            "method": method,
            "path": path,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(data))
    
    def log_response(
        self,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """Log API response."""
        data = {
            "type": "response",
            "status_code": status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(data))
    
    def log_error(
        self,
        error: Exception,
        context: dict = None
    ):
        """Log error."""
        data = {
            "type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        self.logger.error(json.dumps(data), exc_info=True)
    
    def log_task_execution(
        self,
        task_id: str,
        status: str,
        duration_ms: float = None,
        **kwargs
    ):
        """Log task execution."""
        data = {
            "type": "task_execution",
            "task_id": task_id,
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(data))
    
    def log_tool_invocation(
        self,
        tool_name: str,
        parameters: dict,
        result: str,
        duration_ms: float,
        **kwargs
    ):
        """Log tool invocation."""
        data = {
            "type": "tool_invocation",
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(data))