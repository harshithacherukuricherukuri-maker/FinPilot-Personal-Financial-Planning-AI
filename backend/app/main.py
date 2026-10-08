import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend directory is in sys.path when running from project root
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safe table creation on application startup
    try:
        create_tables()
    except Exception as e:
        print(f"Notice: Initial table creation attempt encountered: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Personal Financial Planning and Wealth Optimization Platform API",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS configuration for future React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root platform confirmation endpoint."""
    return {"message": "FinPilot API is running"}


@app.get("/health")
def read_health():
    """Root health probe."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }


# Include unified API router with prefix /api
app.include_router(api_router, prefix=settings.API_V1_STR)
