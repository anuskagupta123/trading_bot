from kiteconnect import KiteConnect
from typing import Optional

def get_kite_client(api_key: str, access_token: str):
    """Create and return authenticated Kite client."""
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite

def place_order(kite, symbol: str, action: str, quantity: int, 
                price: Optional[float] = None, order_type: str = "MARKET"):
    """
    Place an order on Zerodha.
    
    Args:
        kite: KiteConnect instance
        symbol: Trading symbol (e.g., "RELIANCE")
        action: "BUY" or "SELL"
        quantity: Number of shares
        price: Limit price (optional, for limit orders)
        order_type: "MARKET" or "LIMIT"
    
    Returns:
        Order ID
    """
    order_id = kite.place_order(
        variety=kite.VARIETY_REGULAR,
        exchange=kite.EXCHANGE_NSE,
        tradingsymbol=symbol,
        transaction_type=kite.TRANSACTION_TYPE_BUY if action.upper() == "BUY" else kite.TRANSACTION_TYPE_SELL,
        quantity=quantity,
        price=price if order_type == "LIMIT" else None,
        product=kite.PRODUCT_MIS,  # Intraday (auto square-off at 3:15 PM)
        order_type=kite.ORDER_TYPE_MARKET if order_type == "MARKET" else kite.ORDER_TYPE_LIMIT
    )
    return order_id

def get_portfolio(kite):
    """Get user's holdings."""
    return kite.holdings()

def get_positions(kite):
    """Get today's open positions."""
    return kite.positions()

def cancel_order(kite, order_id: str):
    """Cancel an order."""
    return kite.cancel_order(
        variety=kite.VARIETY_REGULAR,
        order_id=order_id
    )

def place_bracket_order(kite, symbol: str, action: str, quantity: int, 
                       sl_price: float, target_price: float):
    """
    Place a bracket order (BO) with stop loss and target built in.
    
    Zerodha automatically places SL and target orders when the entry order fills.
    If either SL or target hits, the other is automatically cancelled.
    
    Args:
        kite: KiteConnect instance
        symbol: Trading symbol (e.g., "RELIANCE")
        action: "BUY" or "SELL"
        quantity: Number of shares
        sl_price: Stop loss price
        target_price: Target/profit price (squareoff)
    
    Returns:
        Order ID
    
    Example:
        place_bracket_order(kite, "RELIANCE", "BUY", 1, 
                           sl_price=2500, target_price=2600)
    """
    try:
        # Get current LTP for limit order price
        ltp_data = kite.quote([f"NSE:{symbol}"])
        current_price = ltp_data[f"NSE:{symbol}"]["last_price"]
        
        # Place bracket order
        order_id = kite.place_order(
            variety=kite.VARIETY_BO,  # Bracket Order
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol=symbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY if action.upper() == "BUY" else kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            product=kite.PRODUCT_MIS,  # Intraday (auto square-off at 3:15 PM)
            order_type=kite.ORDER_TYPE_LIMIT,
            price=current_price,
            stoploss=sl_price,
            squareoff=target_price
        )
        return order_id
    
    except Exception as e:
        raise Exception(f"Bracket order failed: {str(e)}")

def place_oco_order(kite, symbol: str, action: str, quantity: int, 
                   entry_price: float, sl_price: float, target_price: float):
    """
    Place a regular order with OCO (One Cancels Other) exit conditions.
    
    Note: This requires manual SL/target setup or using bracket orders.
    For simplicity, use place_bracket_order instead.
    """
    # Zerodha doesn't have native OCO, so bracket orders are recommended
    return place_bracket_order(kite, symbol, action, quantity, sl_price, target_price)