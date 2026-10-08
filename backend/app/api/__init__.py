from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.transactions import router as transactions_router
from app.api.budgets import router as budgets_router
from app.api.summary import router as summary_router
from app.api.intelligence import router as intelligence_router

api_router = APIRouter()

# Include health endpoints
api_router.include_router(health_router)

# Include business endpoints under /api
api_router.include_router(transactions_router)
api_router.include_router(budgets_router)
api_router.include_router(summary_router)
api_router.include_router(intelligence_router)

__all__ = [
    "api_router",
    "health_router",
    "transactions_router",
    "budgets_router",
    "summary_router",
    "intelligence_router",
]
