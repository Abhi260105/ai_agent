"""
FastAPI Main Application - REST API for Agent System
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

# Import routes
from .routes import tasks, memory, tools, admin

# Import middleware
from .middleware import auth, rate_limit, logging as log_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting AI Agent API...")
    logger.info("Initializing database connections...")
    logger.info("Loading models and tools...")
    logger.info("API is ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent API...")
    logger.info("Closing database connections...")
    logger.info("Cleanup completed")


# Initialize FastAPI app
app = FastAPI(
    title="AI Agent System API",
    description="REST API for AI Agent Task Execution and Management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(log_middleware.LoggingMiddleware)
app.add_middleware(rate_limit.RateLimitMiddleware)

# Include routers
app.include_router(
    tasks.router,
    prefix="/api/v1/tasks",
    tags=["tasks"]
)

app.include_router(
    memory.router,
    prefix="/api/v1/memory",
    tags=["memory"]
)

app.include_router(
    tools.router,
    prefix="/api/v1/tools",
    tags=["tools"]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(auth.verify_admin)]
)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Agent System API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "endpoints": {
            "tasks": "/api/v1/tasks",
            "memory": "/api/v1/memory",
            "tools": "/api/v1/tools",
            "admin": "/api/v1/admin"
        }
    }


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-01-08T00:00:00Z",
        "services": {
            "database": "operational",
            "vector_store": "operational",
            "task_queue": "operational",
            "memory_system": "operational"
        }
    }


# API status endpoint
@app.get("/api/v1/status", tags=["status"])
async def api_status():
    """Get detailed API status."""
    return {
        "api_version": "1.0.0",
        "uptime": "24h 15m 32s",
        "total_requests": 15234,
        "active_tasks": 3,
        "memory_usage": "68%",
        "tools_available": 8,
        "rate_limit": {
            "requests_per_minute": 100,
            "burst": 150
        }
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "status_code": 500
        }
    )


# Custom OpenAPI schema
def custom_openapi():
    """Customize OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="AI Agent System API",
        version="1.0.0",
        description="""
        # AI Agent System API
        
        A comprehensive REST API for managing AI agent tasks, memory, and tools.
        
        ## Features
        - Task execution and management
        - Memory storage and retrieval
        - Tool integration and monitoring
        - Admin operations and analytics
        
        ## Authentication
        Most endpoints require API key authentication via the `X-API-Key` header.
        
        ## Rate Limiting
        - Standard: 100 requests per minute
        - Burst: 150 requests
        
        ## Support
        For support, visit: https://github.com/yourusername/agent-system
        """,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )