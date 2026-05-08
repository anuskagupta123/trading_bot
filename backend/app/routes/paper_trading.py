"""
Paper Trading API endpoints — simulate trading without real capital or broker API calls.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import logging

from ..database.database import get_db
from ..database.models import VirtualWallet, PaperTrade, Broker
from ..brokers.zerodha import get_kite_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/paper-trading", tags=["paper-trading"])


class PaperOrderRequest(BaseModel):
    user_id: int
    symbol: str
    action: str  # "BUY" or "SELL"
    quantity: int


class PaperTradeResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    action: str
    quantity: int
    entry_price: float
    status: str
    
    class Config:
        from_attributes = True


def get_active_kite(user_id: int, db: Session):
    """Get active Kite connection for a user."""
    broker = db.query(Broker).filter(
        Broker.user_id == user_id,
        Broker.is_active == True
    ).first()
    
    if not broker:
        raise HTTPException(status_code=400, detail="No active broker for this user")
    
    return get_kite_client(broker.api_key, broker.access_token)


def get_or_create_wallet(user_id: int, db: Session) -> VirtualWallet:
    """Get or create a virtual wallet for a user."""
    wallet = db.query(VirtualWallet).filter(
        VirtualWallet.user_id == user_id
    ).first()
    
    if not wallet:
        wallet = VirtualWallet(user_id=user_id, balance=100000.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        logger.info(f"✅ Created virtual wallet for user {user_id} with ₹100,000")
    
    return wallet


def get_current_price(symbol: str, broker: Broker = None) -> float:
    """
    Get current market price for a symbol (read-only, no order placed).
    
    Falls back to mock prices in development mode if broker is unavailable.
    """
    # Mock prices for testing without broker credentials
    MOCK_PRICES = {
        "TCS": 3950.00,
        "RELIANCE": 2850.00,
        "INFY": 2100.00,
        "WIPRO": 850.00,
        "HDFC": 2750.00,
        "ITC": 450.00,
        "LT": 2000.00,
        "MARUTI": 12500.00,
        "BAJAJ": 8900.00,
        "SBIN": 750.00,
    }
    
    # Try to fetch from broker first
    if broker:
        try:
            kite = get_kite_client(broker.api_key, broker.access_token)
            quote = kite.ltp(f"NSE:{symbol}")
            
            if f"NSE:{symbol}" in quote:
                price = quote[f"NSE:{symbol}"]["last_price"]
                logger.info(f"📊 {symbol} LTP: ₹{price}")
                return float(price)
        except Exception as e:
            logger.warning(f"⚠️ Broker LTP fetch failed: {str(e)}, using mock price")
    
    # Use mock price as fallback
    price = MOCK_PRICES.get(symbol.upper(), 2500.0)  # Default to 2500 if symbol not in mock
    logger.info(f"📊 {symbol} (mock): ₹{price}")
    return price


@router.post("/wallet/{user_id}")
def create_wallet(user_id: int, db: Session = Depends(get_db)):
    """
    Create or get virtual wallet for paper trading.
    
    Default balance: ₹1,00,000
    """
    wallet = get_or_create_wallet(user_id, db)
    return {
        "user_id": user_id,
        "balance": wallet.balance,
        "total_pnl": wallet.total_pnl,
        "net_value": wallet.balance + wallet.total_pnl,
        "created_at": wallet.created_at
    }


@router.get("/wallet/{user_id}")
def get_wallet(user_id: int, db: Session = Depends(get_db)):
    """Get wallet balance and P&L."""
    wallet = get_or_create_wallet(user_id, db)
    
    # Calculate total open trade P&L
    open_trades = db.query(PaperTrade).filter(
        PaperTrade.user_id == user_id,
        PaperTrade.status == "open"
    ).all()
    
    unrealized_pnl = sum(t.pnl or 0 for t in open_trades)
    
    return {
        "balance": wallet.balance,
        "total_pnl": wallet.total_pnl,  # Realized P&L
        "unrealized_pnl": unrealized_pnl,  # Open trades P&L
        "net_value": wallet.balance + wallet.total_pnl + unrealized_pnl,
        "open_trades": len(open_trades)
    }


@router.post("/order")
def place_paper_order(
    order: PaperOrderRequest,
    db: Session = Depends(get_db)
):
    """
    Place a simulated paper order (no real broker API call).
    
    Gets current price from broker (read-only) or uses mock prices in dev mode.
    
    Example:
    {
        "user_id": 1,
        "symbol": "RELIANCE",
        "action": "BUY",
        "quantity": 1
    }
    """
    try:
        # Validate inputs
        if order.action.upper() not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="Action must be BUY or SELL")
        
        if order.quantity <= 0 or order.quantity > 10000:
            raise HTTPException(status_code=400, detail="Quantity must be 1-10000")
        
        # Get or create wallet
        wallet = get_or_create_wallet(order.user_id, db)
        
        # Get active broker (optional - will use mock prices if unavailable)
        broker = db.query(Broker).filter(
            Broker.user_id == order.user_id,
            Broker.is_active == True
        ).first()
        
        # Get price (from broker if available, else mock prices)
        entry_price = get_current_price(order.symbol, broker)
        
        # Calculate order cost
        order_cost = entry_price * order.quantity
        
        # Check if wallet has sufficient balance for BUY orders
        if order.action.upper() == "BUY":
            if order_cost > wallet.balance:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Required: ₹{order_cost:.2f}, Available: ₹{wallet.balance:.2f}"
                )
            # Deduct from balance
            wallet.balance -= order_cost
        
        # Create paper trade record
        trade = PaperTrade(
            user_id=order.user_id,
            symbol=order.symbol.upper(),
            action=order.action.upper(),
            quantity=order.quantity,
            entry_price=entry_price,
            status="open"
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        logger.info(
            f"✅ Paper order placed: {order.action} {order.quantity}x {order.symbol} @ ₹{entry_price}"
        )
        
        return {
            "status": "success",
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "action": trade.action,
            "quantity": trade.quantity,
            "entry_price": entry_price,
            "order_value": order_cost,
            "remaining_balance": wallet.balance
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing paper order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close/{trade_id}")
def close_paper_trade(
    trade_id: int,
    db: Session = Depends(get_db)
):
    """
    Close a paper trade at current market price.
    
    Calculates P&L and updates wallet.
    """
    try:
        # Get the trade
        trade = db.query(PaperTrade).filter(
            PaperTrade.id == trade_id
        ).first()
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        if trade.status == "closed":
            raise HTTPException(status_code=400, detail="Trade already closed")
        
        # Get wallet
        wallet = get_or_create_wallet(trade.user_id, db)
        
        # Get broker (optional - will use mock prices if unavailable)
        broker = db.query(Broker).filter(
            Broker.user_id == trade.user_id,
            Broker.is_active == True
        ).first()
        
        # Get current price
        exit_price = get_current_price(trade.symbol, broker)
        
        # Calculate P&L
        # For BUY: profit = (exit - entry) * quantity
        # For SELL: profit = (entry - exit) * quantity
        if trade.action == "BUY":
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:  # SELL
            pnl = (trade.entry_price - exit_price) * trade.quantity
        
        pnl_pct = (pnl / (trade.entry_price * trade.quantity)) * 100
        
        # Update trade
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        trade.status = "closed"
        trade.closed_at = datetime.utcnow()
        
        # Update wallet
        wallet.balance += pnl  # Add P&L back to balance
        wallet.total_pnl += pnl  # Add to cumulative P&L
        
        db.commit()
        
        logger.info(
            f"✅ Paper trade closed: {trade.symbol} P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%)"
        )
        
        return {
            "status": "success",
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "action": trade.action,
            "entry_price": trade.entry_price,
            "exit_price": exit_price,
            "quantity": trade.quantity,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "wallet_balance": wallet.balance,
            "total_pnl": wallet.total_pnl
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing paper trade: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/{user_id}")
def get_paper_trades(
    user_id: int,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all paper trades for a user.
    
    Filter by status: "open", "closed", or None for all
    """
    query = db.query(PaperTrade).filter(PaperTrade.user_id == user_id)
    
    if status:
        query = query.filter(PaperTrade.status == status)
    
    trades = query.all()
    
    return {
        "user_id": user_id,
        "total_trades": len(trades),
        "trades": [
            {
                "id": t.id,
                "symbol": t.symbol,
                "action": t.action,
                "quantity": t.quantity,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "status": t.status,
                "opened_at": t.opened_at,
                "closed_at": t.closed_at
            }
            for t in trades
        ]
    }


@router.get("/trades/{user_id}/summary")
def get_paper_trades_summary(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get summary statistics of all paper trades."""
    trades = db.query(PaperTrade).filter(
        PaperTrade.user_id == user_id
    ).all()
    
    closed_trades = [t for t in trades if t.status == "closed"]
    open_trades = [t for t in trades if t.status == "open"]
    
    if closed_trades:
        total_pnl = sum(t.pnl or 0 for t in closed_trades)
        winning = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing = [t for t in closed_trades if t.pnl and t.pnl < 0]
    else:
        total_pnl = 0
        winning = []
        losing = []
    
    unrealized_pnl = sum(t.pnl or 0 for t in open_trades)
    
    return {
        "total_trades": len(trades),
        "open_trades": len(open_trades),
        "closed_trades": len(closed_trades),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": f"{(len(winning) / len(closed_trades) * 100):.1f}%" if closed_trades else "0%",
        "realized_pnl": round(total_pnl, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "total_pnl": round(total_pnl + unrealized_pnl, 2)
    }
