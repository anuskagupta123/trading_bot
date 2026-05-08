from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import webhook, brokers, risk, indicators, paper_trading, admin   # 👈 import routers
import app.utils.sentry_init  # initialize Sentry if configured

# Rate limiting
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.utils.limiter import limiter

app = FastAPI(title="Trading Platform")   # 👈 create app FIRST

# Attach shared limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Basic logging configuration
import logging
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