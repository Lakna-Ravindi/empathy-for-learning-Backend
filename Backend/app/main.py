from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth_routes import router as auth_router
from app.routes.chat_routes import router as chat_router
from app.core.config import CORS_ORIGINS
import logging

# ============= Configure Logging =============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Empathy for Learning API",
    description="Backend API for the Empathy for Learning platform",
    version="1.0.0"
)

# ============= CORS Middleware =============
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Error Handlers =============

@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_exception_handler(request: Request, exc: Exception):
    """Handle 401 Unauthorized errors"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": "Unauthorized - Please provide valid credentials",
            "status": "error"
        }
    )


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_exception_handler(request: Request, exc: Exception):
    """Handle 403 Forbidden errors"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": "Forbidden - You don't have permission to access this resource",
            "status": "error"
        }
    )


import traceback

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors with logging"""
    
    print("=" * 60)
    print("UNHANDLED EXCEPTION CAUGHT")
    print(f"Path: {request.url}")
    print(f"Error: {str(exc)}")
    print(traceback.format_exc())
    print("=" * 60)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error - Please try again later",
            "status": "error"
        }
    )

# ============= Route Inclusion =============

app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    chat_router,
    prefix="/api/chat",
    tags=["Chat"]
)


# ============= Root Endpoint =============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Empathy for Learning API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )