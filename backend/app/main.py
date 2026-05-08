from contextlib import asynccontextmanager
from pathlib import Path
import logging
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


app = FastAPI(title="Trading Platform", lifespan=lifespan)   # 👈 create app FIRST

# Attach shared limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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