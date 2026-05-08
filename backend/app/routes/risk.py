"""
Risk Settings API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database.database import get_db
from ..database.models import RiskSettings
from ..risk_management.checker import can_trade, get_risk_settings, get_daily_stats

router = APIRouter(prefix="/risk", tags=["risk"])


class RiskSettingsUpdate(BaseModel):
    max_loss_per_day: float = 5000.0
    max_trades_per_day: int = 10
    default_stop_loss_pct: float = 1.0
    default_target_pct: float = 2.0
    trailing_sl_enabled: bool = False
    exit_all_at_close: bool = True


@router.post("/{user_id}/settings")
def create_risk_settings(
    user_id: int,
    settings: RiskSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Create or update risk settings for a user."""
    existing = db.query(RiskSettings).filter(
        RiskSettings.user_id == user_id
    ).first()
    
    if existing:
        # Update
        existing.max_loss_per_day = settings.max_loss_per_day
        existing.max_trades_per_day = settings.max_trades_per_day
        existing.default_stop_loss_pct = settings.default_stop_loss_pct
        existing.default_target_pct = settings.default_target_pct
        existing.trailing_sl_enabled = settings.trailing_sl_enabled
        existing.exit_all_at_close = settings.exit_all_at_close
    else:
        # Create
        existing = RiskSettings(
            user_id=user_id,
            max_loss_per_day=settings.max_loss_per_day,
            max_trades_per_day=settings.max_trades_per_day,
            default_stop_loss_pct=settings.default_stop_loss_pct,
            default_target_pct=settings.default_target_pct,
            trailing_sl_enabled=settings.trailing_sl_enabled,
            exit_all_at_close=settings.exit_all_at_close,
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    return {
        "message": "Risk settings saved",
        "user_id": user_id,
        "settings": {
            "max_loss_per_day": existing.max_loss_per_day,
            "max_trades_per_day": existing.max_trades_per_day,
            "default_stop_loss_pct": existing.default_stop_loss_pct,
            "default_target_pct": existing.default_target_pct,
            "trailing_sl_enabled": existing.trailing_sl_enabled,
            "exit_all_at_close": existing.exit_all_at_close,
        }
    }


@router.get("/{user_id}/settings")
def get_user_risk_settings(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get risk settings for a user."""
    return get_risk_settings(user_id, db)


@router.get("/{user_id}/stats")
def get_user_daily_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get today's trading stats for a user."""
    stats = get_daily_stats(user_id, db)
    settings = get_risk_settings(user_id, db)
    allowed, reason = can_trade(user_id, db)
    
    return {
        "stats": stats,
        "limits": {
            "max_trades_per_day": settings["max_trades_per_day"],
            "max_loss_per_day": settings["max_loss_per_day"],
        },
        "can_trade": allowed,
        "trade_blocked_reason": None if allowed else reason,
    }


@router.post("/{user_id}/check")
def check_if_can_trade(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if a user is allowed to place a trade.
    Used before placing any order.
    """
    allowed, reason = can_trade(user_id, db)
    
    if allowed:
        return {
            "can_trade": True,
            "status": "approved",
            "message": "Trade is allowed"
        }
    else:
        return {
            "can_trade": False,
            "status": "blocked",
            "reason": reason
        }
