import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from ..database.database import get_db
from ..database.models import Trade
from ..utils.security import require_admin_token

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/system")
def system_stats(admin: bool = Depends(require_admin_token)):
    """Return basic system statistics using psutil."""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), admin: bool = Depends(require_admin_token)):
    """Return simple analytics for admin dashboard."""
    try:
        total_trades = db.query(Trade).count()
        today_trades = db.query(Trade).filter(Trade.trade_date == date.today()).count()
        total_pnl = db.query(func.sum(Trade.pnl)).scalar() or 0
        return {
            "total_trades": total_trades,
            "today_trades": today_trades,
            "total_pnl": round(float(total_pnl), 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
