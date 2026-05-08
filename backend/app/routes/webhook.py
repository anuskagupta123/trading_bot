import os
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..brokers.zerodha import get_kite_client, place_order
from ..database.database import get_db
from ..database.models import Broker, WebhookLog
from ..risk_management.checker import can_trade
from ..utils.security import verify_webhook_secret
from ..utils.limiter import limiter

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()


def is_mock_broker_credentials(broker: Broker) -> bool:
    """Return True when the broker still has placeholder credentials."""
    placeholder_values = {
        "your_api_key",
        "your_api_secret",
        "your_real_access_token",
        "your-access-token",
        "your_api_key_here",
        "your_api_secret_here",
        "",
        None,
    }
    return broker.api_key in placeholder_values or broker.access_token in placeholder_values

class AlertPayload(BaseModel):
    symbol: str
    action: str   # "BUY" or "SELL"
    quantity: int = 1
    secret: str

@router.post("")
@limiter.limit("60/minute")
def receive_alert(
    request: Request,
    payload: AlertPayload, 
    db: Session = Depends(get_db),
    x_forwarded_for: str = Header(None)  # To log client IP
):
    """
    Webhook endpoint for TradingView alerts.
    
    TradingView will POST a JSON with:
    {
        "symbol": "NIFTY",
        "action": "BUY",
        "quantity": 1,
        "secret": "my-secret-token-123"
    }
    """
    
    # Get client IP for logging
    client_ip = x_forwarded_for.split(",")[0] if x_forwarded_for else "unknown"
    
    # Log receipt
    logger.info(f"📩 Webhook from {client_ip}: {payload.symbol} {payload.action} x{payload.quantity}")
    
    # Create log entry
    log = WebhookLog(
        symbol=payload.symbol,
        action=payload.action,
        quantity=payload.quantity,
        status="pending"
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    try:
        # 1. Validate secret token (must match env `WEBHOOK_SECRET`)
        verify_webhook_secret(payload.secret)
        
        # 2. Validate action
        if payload.action.upper() not in ["BUY", "SELL"]:
            log.status = "failed"
            log.error_message = f"Invalid action: {payload.action}"
            db.commit()
            raise HTTPException(status_code=400, detail="Action must be BUY or SELL")
        
        # 3. Validate quantity
        if payload.quantity <= 0 or payload.quantity > 1000:
            log.status = "failed"
            log.error_message = f"Invalid quantity: {payload.quantity}"
            db.commit()
            raise HTTPException(status_code=400, detail="Quantity must be between 1 and 1000")
        
        # 4. Get active broker
        broker = db.query(Broker).filter(Broker.is_active == True).first()
        if not broker:
            log.status = "failed"
            log.error_message = "No active broker configured"
            db.commit()
            logger.error("❌ No active broker found")
            raise HTTPException(status_code=400, detail="No active broker configured")
        
        log.broker_id = broker.id
        
        # 5. Check risk settings
        # Extract user_id from broker (or use a default for alerts without user context)
        user_id = broker.user_id if broker.user_id else 1
        
        allowed, risk_reason = can_trade(user_id, db)
        if not allowed:
            log.status = "failed"
            log.error_message = f"Risk check blocked: {risk_reason}"
            db.commit()
            logger.warning(f"🚫 Trade blocked by risk checker: {risk_reason}")
            raise HTTPException(status_code=403, detail=f"Trade blocked: {risk_reason}")
        
        # 6. Place order with Zerodha or simulate it in development.
        try:
            logger.info(f"🔄 Placing order: {payload.symbol} {payload.action} x{payload.quantity}")

            if ENVIRONMENT != "production" and is_mock_broker_credentials(broker):
                order_id = f"MOCK-{log.id}"
                logger.info("🧪 Development mode: skipping real Zerodha order placement")
            else:
                kite = get_kite_client(broker.api_key, broker.access_token)
                order_id = place_order(
                    kite,
                    payload.symbol.upper(),
                    payload.action.upper(),
                    payload.quantity
                )
            
            # 7. Update log with success
            log.order_id = str(order_id)
            log.status = "success"
            log.executed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"✅ Order placed! ID: {order_id}")
            
            return {
                "status": "success",
                "order_id": order_id,
                "symbol": payload.symbol,
                "action": payload.action,
                "quantity": payload.quantity,
                "broker": broker.broker_name,
                "mode": "mock" if str(order_id).startswith("MOCK-") else "live",
                "log_id": log.id
            }
        
        except Exception as e:
            # Order placement failed
            error_msg = str(e)
            log.status = "failed"
            log.error_message = error_msg[:500]  # Truncate long errors
            db.commit()
            logger.error(f"❌ Order placement failed: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Order failed: {error_msg}")
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    
    except Exception as e:
        # Unexpected error
        log.status = "failed"
        log.error_message = f"Unexpected error: {str(e)}"
        db.commit()
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/logs")
def get_webhook_logs(db: Session = Depends(get_db), limit: int = 100):
    """
    Get recent webhook logs for debugging.
    """
    logs = db.query(WebhookLog).order_by(WebhookLog.received_at.desc()).limit(limit).all()
    return logs

@router.get("/logs/stats")
def get_webhook_stats(db: Session = Depends(get_db)):
    """
    Get webhook statistics.
    """
    total = db.query(WebhookLog).count()
    success = db.query(WebhookLog).filter(WebhookLog.status == "success").count()
    failed = db.query(WebhookLog).filter(WebhookLog.status == "failed").count()
    pending = db.query(WebhookLog).filter(WebhookLog.status == "pending").count()
    
    return {
        "total_alerts": total,
        "successful_orders": success,
        "failed_orders": failed,
        "pending": pending,
        "success_rate": f"{(success/total*100):.1f}%" if total > 0 else "0%"
    }