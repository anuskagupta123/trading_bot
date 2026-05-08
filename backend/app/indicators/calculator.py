"""
Calculate technical indicators using pandas-ta.
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def add_indicators(df: pd.DataFrame, config: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Add technical indicators to a pandas DataFrame.
    
    Args:
        df: DataFrame with columns: [open, high, low, close, volume]
        config: Dictionary specifying which indicators to calculate
        
    Example config:
        {
            "ema": [{"length": 9}, {"length": 21}],
            "rsi": [{"length": 14}],
            "macd": [{}],
            "supertrend": [{"length": 10, "multiplier": 3}],
            "bollinger": [{"length": 20}]
        }
    
    Returns:
        DataFrame with added indicator columns
    
    Example:
        df = get_candles(kite, "RELIANCE", "5minute", days=5)
        config = {
            "ema": [{"length": 9}, {"length": 21}],
            "rsi": [{"length": 14}]
        }
        df = add_indicators(df, config)
        # df now has columns: EMA_9, EMA_21, RSI
    """
    
    if df.empty:
        logger.warning("⚠️ Empty DataFrame, skipping indicator calculation")
        return df
    
    try:
        # Ensure required columns exist
        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        logger.info(f"📈 Calculating indicators: {list(config.keys())}")
        
        # EMA (Exponential Moving Average)
        if "ema" in config:
            for ema_cfg in config["ema"]:
                length = ema_cfg.get("length", 12)
                col_name = f"EMA_{length}"
                df[col_name] = ta.ema(df["close"], length=length)
                logger.info(f"  ✅ EMA_{length}")
        
        # RSI (Relative Strength Index)
        if "rsi" in config:
            length = config["rsi"][0].get("length", 14)
            df["RSI"] = ta.rsi(df["close"], length=length)
            logger.info(f"  ✅ RSI")
        
        # MACD (Moving Average Convergence Divergence)
        if "macd" in config:
            macd_data = ta.macd(df["close"])
            if macd_data is not None:
                df = pd.concat([df, macd_data], axis=1)
                logger.info(f"  ✅ MACD")
        
        # Supertrend
        if "supertrend" in config:
            length = config["supertrend"][0].get("length", 10)
            multiplier = config["supertrend"][0].get("multiplier", 3)
            st_data = ta.supertrend(df["high"], df["low"], df["close"], 
                                   length=length, multiplier=multiplier)
            if st_data is not None:
                df = pd.concat([df, st_data], axis=1)
                logger.info(f"  ✅ Supertrend")
        
        # Bollinger Bands
        if "bollinger" in config:
            length = config["bollinger"][0].get("length", 20)
            bb_data = ta.bbands(df["close"], length=length)
            if bb_data is not None:
                df = pd.concat([df, bb_data], axis=1)
                logger.info(f"  ✅ Bollinger Bands")
        
        # SMA (Simple Moving Average)
        if "sma" in config:
            for sma_cfg in config["sma"]:
                length = sma_cfg.get("length", 20)
                col_name = f"SMA_{length}"
                df[col_name] = ta.sma(df["close"], length=length)
                logger.info(f"  ✅ SMA_{length}")
        
        # ATR (Average True Range)
        if "atr" in config:
            length = config["atr"][0].get("length", 14)
            df["ATR"] = ta.atr(df["high"], df["low"], df["close"], length=length)
            logger.info(f"  ✅ ATR")
        
        # STOCH (Stochastic Oscillator)
        if "stoch" in config:
            k = config["stoch"][0].get("k", 14)
            d = config["stoch"][0].get("d", 3)
            stoch_data = ta.stoch(df["high"], df["low"], df["close"], k=k, d=d)
            if stoch_data is not None:
                df = pd.concat([df, stoch_data], axis=1)
                logger.info(f"  ✅ Stochastic")
        
        logger.info(f"✅ Indicators calculated. Total columns: {len(df.columns)}")
        return df
    
    except Exception as e:
        logger.error(f"❌ Error calculating indicators: {str(e)}")
        raise


def get_indicator_list() -> Dict[str, Dict[str, Any]]:
    """
    Get list of available indicators with their parameters.
    Useful for frontend to build indicator selection UI.
    """
    return {
        "ema": {
            "name": "Exponential Moving Average",
            "params": [{"name": "length", "type": "integer", "default": 12, "min": 2, "max": 500}]
        },
        "sma": {
            "name": "Simple Moving Average",
            "params": [{"name": "length", "type": "integer", "default": 20, "min": 2, "max": 500}]
        },
        "rsi": {
            "name": "Relative Strength Index",
            "params": [{"name": "length", "type": "integer", "default": 14, "min": 2, "max": 100}]
        },
        "macd": {
            "name": "Moving Average Convergence Divergence",
            "params": []
        },
        "bollinger": {
            "name": "Bollinger Bands",
            "params": [{"name": "length", "type": "integer", "default": 20, "min": 5, "max": 100}]
        },
        "supertrend": {
            "name": "Supertrend",
            "params": [
                {"name": "length", "type": "integer", "default": 10, "min": 2, "max": 50},
                {"name": "multiplier", "type": "float", "default": 3, "min": 0.5, "max": 10}
            ]
        },
        "atr": {
            "name": "Average True Range",
            "params": [{"name": "length", "type": "integer", "default": 14, "min": 2, "max": 100}]
        },
        "stoch": {
            "name": "Stochastic Oscillator",
            "params": [
                {"name": "k", "type": "integer", "default": 14, "min": 2, "max": 50},
                {"name": "d", "type": "integer", "default": 3, "min": 1, "max": 20}
            ]
        }
    }
