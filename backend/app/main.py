from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os
import subprocess
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database.database import engine
from app.routes import webhook, brokers, risk, indicators, paper_trading, admin   # 👈 import routers
import app.utils.sentry_init  # initialize Sentry if configured

# Rate limiting
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.utils.limiter import limiter


def run_database_migrations() -> None:
    """Apply Alembic migrations before serving requests."""
    backend_root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "alembic", "upgrade", "head"]

    result = subprocess.run(
        command,
        cwd=backend_root,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return

    output = f"{result.stdout}\n{result.stderr}"
    if "Can't locate revision identified by" in output:
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
        subprocess.run(command, cwd=backend_root, check=True)
        return

    raise RuntimeError(
        "Database migration failed during startup:\n"
        f"{output.strip()}"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_database_migrations()
    yield


def get_allowed_origins() -> list[str]:
    """Build the CORS allowlist from environment variables and local defaults."""
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    frontend_urls = os.getenv("FRONTEND_URLS", "")
    if frontend_urls:
        origins.extend(
            origin.strip() for origin in frontend_urls.split(",") if origin.strip()
        )

    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url:
        origins.append(frontend_url)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(origins))


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')


def create_app() -> FastAPI:
    app = FastAPI(title="Trading Platform", lifespan=lifespan)

    # Attach shared limiter to app state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 👇 THEN include routers
    app.include_router(webhook.router)
    app.include_router(brokers.router)
    app.include_router(risk.router)
    app.include_router(indicators.router)
    app.include_router(paper_trading.router)
    app.include_router(admin.router)

    @app.get("/")
    def root():
        return {"message": "Trading API is running"}

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()