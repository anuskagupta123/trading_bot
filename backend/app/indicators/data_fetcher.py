"""
Fetch historical OHLCV candle data from Zerodha.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_instrument_token(kite, symbol: str) -> int:
    """
    Get the instrument token for a symbol from Zerodha.
    
    Args:
        kite: KiteConnect instance
        symbol: Trading symbol (e.g., "RELIANCE")
    
    Returns:
        Instrument token (int)
    
    Raises:
        ValueError: If symbol not found
    """
    try:
        instruments = kite.instruments("NSE")
        for inst in instruments:
            if inst["tradingsymbol"] == symbol:
                logger.info(f"✅ Found {symbol}: token={inst['instrument_token']}")
                return inst["instrument_token"]
        
        raise ValueError(f"Symbol {symbol} not found in NSE")
    
    except Exception as e:
        logger.error(f"❌ Error fetching instrument token for {symbol}: {str(e)}")
        raise


def get_candles(kite, symbol: str, interval: str = "5minute", days: int = 5) -> pd.DataFrame:
    """
    Fetch historical OHLCV candle data from Zerodha.
    
    Args:
        kite: KiteConnect instance
        symbol: Trading symbol (e.g., "RELIANCE")
        interval: Candle interval
                 Options: "minute", "3minute", "5minute", "15minute", 
                         "30minute", "60minute", "day", "week", "month"
        days: Number of days of historical data to fetch (default: 5)
    
    Returns:
        pandas.DataFrame with columns: [open, high, low, close, volume]
        Index: datetime
    
    Example:
        df = get_candles(kite, "RELIANCE", interval="5minute", days=5)
        # df looks like:
        #             open   high    low  close    volume
        # 2026-05-07  2500.0 2550.0 2490.0 2540.0  1000000
        # 2026-05-07  2540.0 2560.0 2535.0 2555.0  950000
    """
    try:
        logger.info(f"📊 Fetching {symbol} candles: {interval}, last {days} days")
        
        # Calculate date range
        from_date = datetime.now() - timedelta(days=days)
        to_date = datetime.now()
        
        # Get instrument token
        token = get_instrument_token(kite, symbol)
        
        # Fetch historical data
        data = kite.historical_data(
            instrument_token=token,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        )
        
        if not data:
            logger.warning(f"⚠️ No candle data returned for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Rename columns to standard format
        df.columns = ["date", "open", "high", "low", "close", "volume"]
        
        # Convert date to datetime and set as index
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        
        # Ensure numeric types
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        logger.info(f"✅ Fetched {len(df)} candles for {symbol}")
        return df
    
    except Exception as e:
        logger.error(f"❌ Error fetching candles: {str(e)}")
        raise


def get_latest_candle(kite, symbol: str, interval: str = "5minute") -> dict:
    """
    Get the latest candle (most recent closed candle).
    
    Returns:
        dict: {"open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}
    """
    try:
        df = get_candles(kite, symbol, interval=interval, days=1)
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        return latest.to_dict()
    
    except Exception as e:
        logger.error(f"❌ Error getting latest candle: {str(e)}")
        return {}
