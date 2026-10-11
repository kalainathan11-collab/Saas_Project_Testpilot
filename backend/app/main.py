"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions import register_exception_handlers
from app.routers import auth, dashboard, defects, projects, requirements, testcases, testruns

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Credentialed CORS is required for the HttpOnly refresh cookie. Safe only because
    # origins are an explicit allowlist (config rejects '*').
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(requirements.router)
app.include_router(testcases.router)
app.include_router(testruns.router)
app.include_router(defects.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
