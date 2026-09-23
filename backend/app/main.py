"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

This currently exposes only a health-check route. Real feature routers
(auth, schools, students, ...) get added under app/api/ in later phases
and included here with app.include_router(...).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="School Results Management System API",
    version="0.1.0",
    description="Multi-tenant school CA / examination / results / report card API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
def health_check():
    """Simple liveness check used to confirm the backend is up and reachable."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}
