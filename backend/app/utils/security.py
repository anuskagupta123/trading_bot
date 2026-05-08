import os
from fastapi import Header, HTTPException


def require_admin_token(x_admin_token: str = Header(None)):
    """Dependency to require an admin token header.
    Header name: `X-Admin-Token`.
    The expected token is read from `ADMIN_TOKEN` env var.
    """
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(status_code=500, detail="Admin token not configured")
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True


def verify_webhook_secret(payload_secret: str):
    expected = os.getenv("WEBHOOK_SECRET")
    if not expected:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    if payload_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    return True
