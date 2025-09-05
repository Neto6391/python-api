from fastapi import APIRouter
from app.presentation.v1.endpoints.health.endpoints import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
