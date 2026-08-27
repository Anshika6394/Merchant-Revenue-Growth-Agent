from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import evidence, analytics, auth, health
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

app.include_router(evidence.router)

from app.api.routes import strategy
app.include_router(strategy.router)

from app.api.routes import rag
app.include_router(rag.router)

from app.api.routes import actions
app.include_router(actions.router)

from app.api.routes import opportunities
app.include_router(opportunities.router)
