"""
Indicators API endpoints — calculate and retrieve technical indicators
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from ..database.database import get_db
from ..indicators.data_fetcher import get_candles, get_latest_candle
from ..indicators.calculator import add_indicators, get_indicator_list
from ..strategies.engine import evaluate_strategy

router = APIRouter(prefix="/indicators", tags=["indicators"])


class IndicatorConfig(BaseModel):
    """Configuration for which indicators to calculate"""
    ema: Optional[List[Dict[str, Any]]] = None
    sma: Optional[List[Dict[str, Any]]] = None
    rsi: Optional[List[Dict[str, Any]]] = None
    macd: Optional[List[Dict[str, Any]]] = None
    bollinger: Optional[List[Dict[str, Any]]] = None
    supertrend: Optional[List[Dict[str, Any]]] = None
    atr: Optional[List[Dict[str, Any]]] = None
    stoch: Optional[List[Dict[str, Any]]] = None


@router.get("/available")
def get_available_indicators():
    """
    Get list of all available indicators with their parameters.
    Useful for building frontend dropdown UI.
    """
    return {
        "indicators": get_indicator_list(),
        "total": len(get_indicator_list())
    }


@router.post("/calculate/{symbol}")
def calculate_indicators(
    symbol: str,
    config: IndicatorConfig,
    interval: str = "5minute",
    days: int = 5,
    db: Session = Depends(get_db)
):
    """
    Calculate technical indicators for a symbol.
    
    Note: This requires a live Kite connection (broker configured).
    For demo, use the /mock endpoint.
    
    Example request:
    {
        "ema": [{"length": 9}, {"length": 21}],
        "rsi": [{"length": 14}],
        "macd": [{}]
    }
    """
    try:
        from ..brokers.zerodha import get_kite_client
        from ..database.models import Broker
        
        # Get active broker
        broker = db.query(Broker).filter(Broker.is_active == True).first()
        if not broker:
            raise HTTPException(status_code=400, detail="No active broker configured")
        
        # Get kite connection
        kite = get_kite_client(broker.api_key, broker.access_token)
        
        # Fetch candles
        df = get_candles(kite, symbol, interval=interval, days=days)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        
        # Convert config to dict, filtering out None values
        indicator_config = {
            k: v for k, v in config.dict().items() 
            if v is not None
        }
        
        # Calculate indicators
        df = add_indicators(df, indicator_config)
        
        # Return latest candle with indicators
        latest = df.iloc[-1]
        return {
            "symbol": symbol,
            "interval": interval,
            "data": {
                "datetime": str(df.index[-1]),
                **latest.to_dict()
            },
            "total_candles": len(df),
            "indicators_calculated": list(indicator_config.keys())
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating indicators: {str(e)}")


@router.post("/mock/calculate")
def calculate_indicators_mock(
    config: IndicatorConfig,
):
    """
    Calculate indicators on mock/sample data (no broker needed).
    Useful for testing strategies without live connection.
    """
    import pandas as pd
    
    try:
        # Create sample data
        df = pd.DataFrame({
            'open': [100 + i*0.5 for i in range(50)],
            'high': [101 + i*0.5 for i in range(50)],
            'low': [99 + i*0.5 for i in range(50)],
            'close': [100.5 + i*0.5 for i in range(50)],
            'volume': [1000 * (i+1) for i in range(50)]
        })
        
        # Convert config to dict, filtering out None values
        indicator_config = {
            k: v for k, v in config.dict().items() 
            if v is not None
        }
        
        # Calculate indicators
        df = add_indicators(df, indicator_config)
        
        # Return latest candle with indicators
        latest = df.iloc[-1]
        return {
            "mode": "mock",
            "symbol": "SAMPLE",
            "data": {
                "close": float(latest['close']),
                **{k: float(v) if not pd.isna(v) else None 
                   for k, v in latest.items() if k != 'close'}
            },
            "total_candles": len(df),
            "indicators_calculated": list(indicator_config.keys())
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
