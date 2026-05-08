"""
Risk management checker — validates if a trade is allowed before execution.
"""
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from ..database.models import RiskSettings, Trade
import logging

logger = logging.getLogger(__name__)


def can_trade(user_id: int, db: Session) -> tuple[bool, str]:
    """
    Check if a user is allowed to place a trade based on risk settings.
    
    Args:
        user_id: The user attempting to trade
        db: Database session
    
    Returns:
        tuple: (allowed: bool, reason: str)
        Example: (False, "Max trades for today reached")
    """
    
    # Get risk settings for user
    settings = db.query(RiskSettings).filter(
        RiskSettings.user_id == user_id
    ).first()
    
    # If no settings, allow trade (default permissive)
    if not settings:
        logger.info(f"✅ User {user_id}: No risk settings configured, allowing trade")
        return True, "ok"
    
    # Check 1: Daily trade count
    today_trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.trade_date == date.today()
    ).count()
    
    if today_trades >= settings.max_trades_per_day:
        reason = f"Max trades ({settings.max_trades_per_day}) reached for today. Done: {today_trades}"
        logger.warning(f"❌ User {user_id}: {reason}")
        return False, reason
    
    # Check 2: Daily loss limit
    today_loss = db.query(func.sum(Trade.pnl)).filter(
        Trade.user_id == user_id,
        Trade.trade_date == date.today(),
        Trade.pnl < 0  # Only count losses
    ).scalar() or 0.0
    
    abs_loss = abs(float(today_loss))
    if abs_loss >= settings.max_loss_per_day:
        reason = f"Daily loss limit (₹{settings.max_loss_per_day}) reached. Loss: ₹{abs_loss:.2f}"
        logger.warning(f"❌ User {user_id}: {reason}")
        return False, reason
    
    logger.info(
        f"✅ User {user_id}: Risk checks passed. "
        f"Trades: {today_trades}/{settings.max_trades_per_day}, "
        f"Loss: ₹{abs_loss:.2f}/{settings.max_loss_per_day}"
    )
    return True, "ok"


def get_risk_settings(user_id: int, db: Session) -> dict:
    """Get user's risk settings or defaults."""
    settings = db.query(RiskSettings).filter(
        RiskSettings.user_id == user_id
    ).first()
    
    if not settings:
        return {
            "user_id": user_id,
            "max_loss_per_day": 5000.0,
            "max_trades_per_day": 10,
            "default_stop_loss_pct": 1.0,
            "default_target_pct": 2.0,
            "trailing_sl_enabled": False,
            "exit_all_at_close": True,
        }
    
    return {
        "user_id": settings.user_id,
        "max_loss_per_day": settings.max_loss_per_day,
        "max_trades_per_day": settings.max_trades_per_day,
        "default_stop_loss_pct": settings.default_stop_loss_pct,
        "default_target_pct": settings.default_target_pct,
        "trailing_sl_enabled": settings.trailing_sl_enabled,
        "exit_all_at_close": settings.exit_all_at_close,
    }


def get_daily_stats(user_id: int, db: Session) -> dict:
    """Get today's trading stats for a user."""
    today_trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.trade_date == date.today()
    ).all()
    
    total_trades = len(today_trades)
    closed_trades = [t for t in today_trades if t.status == "closed"]
    open_trades = [t for t in today_trades if t.status == "open"]
    
    total_pnl = sum([t.pnl or 0 for t in closed_trades])
    win_count = len([t for t in closed_trades if t.pnl and t.pnl > 0])
    loss_count = len([t for t in closed_trades if t.pnl and t.pnl < 0])
    
    return {
        "total_trades": total_trades,
        "open_trades": len(open_trades),
        "closed_trades": len(closed_trades),
        "total_pnl": round(total_pnl, 2),
        "winning_trades": win_count,
        "losing_trades": loss_count,
        "win_rate": f"{(win_count / len(closed_trades) * 100):.1f}%" if closed_trades else "0%",
    }
