"""
Strategy evaluation engine — evaluates conditions and returns trading signals.
"""
import pandas as pd
from typing import List, Dict, Any, Literal
import logging

logger = logging.getLogger(__name__)


def evaluate_strategy(df: pd.DataFrame, conditions: List[Dict[str, Any]]) -> Literal["BUY", "SELL", "NONE"]:
    """
    Evaluate strategy conditions against the latest candle.
    
    ALL conditions must pass for a BUY signal. If any condition fails → NONE.
    
    Args:
        df: DataFrame with indicators already calculated
        conditions: List of condition objects
        
    Condition structure:
        {
            "indicator": "EMA_9",              # Column name to check
            "operator": ">",                   # Operator: >, <, >=, <=, ==, !=
            "compare_to": "EMA_21"             # Either another indicator OR "value"
            "value": 60                        # (optional) If compare_to="value", use this
        }
    
    Example conditions:
        [
            {"indicator": "EMA_9", "operator": ">", "compare_to": "EMA_21"},
            {"indicator": "RSI", "operator": ">", "compare_to": "value", "value": 60},
            {"indicator": "close", "operator": ">", "compare_to": "value", "value": 2500}
        ]
        Result: BUY if EMA_9 > EMA_21 AND RSI > 60 AND close > 2500
    
    Returns:
        "BUY": All conditions passed
        "NONE": At least one condition failed
        "SELL": (Future: for sell conditions)
    """
    
    if df.empty:
        logger.warning("⚠️ Empty DataFrame, cannot evaluate strategy")
        return "NONE"
    
    if not conditions:
        logger.warning("⚠️ No conditions provided")
        return "NONE"
    
    try:
        # Get the most recent (latest) candle
        latest = df.iloc[-1]
        
        logger.info(f"📊 Evaluating strategy with {len(conditions)} conditions")
        logger.info(f"   Latest candle: Close={latest.get('close', 'N/A')}")
        
        # Check each condition
        for i, condition in enumerate(conditions):
            try:
                indicator = condition.get("indicator")
                operator = condition.get("operator")
                compare_to = condition.get("compare_to")
                
                # Get left side value (from indicator column)
                if indicator not in latest.index:
                    logger.warning(f"   ❌ Condition {i+1}: Indicator '{indicator}' not found in DataFrame")
                    return "NONE"
                
                left = latest[indicator]
                
                # Get right side value
                if compare_to == "value":
                    right = condition.get("value")
                    if right is None:
                        logger.warning(f"   ❌ Condition {i+1}: 'value' parameter missing")
                        return "NONE"
                else:
                    # compare_to is another indicator
                    if compare_to not in latest.index:
                        logger.warning(f"   ❌ Condition {i+1}: Indicator '{compare_to}' not found")
                        return "NONE"
                    right = latest[compare_to]
                
                # Handle NaN values
                if pd.isna(left) or pd.isna(right):
                    logger.warning(f"   ⚠️ Condition {i+1}: NaN value detected ({indicator}={left}, {compare_to}={right})")
                    return "NONE"
                
                # Evaluate condition
                result = evaluate_condition(left, operator, right)
                
                if result:
                    logger.info(f"   ✅ Condition {i+1}: {indicator} {operator} {right} → PASS")
                else:
                    logger.info(f"   ❌ Condition {i+1}: {indicator} {operator} {right} → FAIL")
                    return "NONE"
            
            except Exception as e:
                logger.error(f"   ❌ Condition {i+1} error: {str(e)}")
                return "NONE"
        
        logger.info("✅ All conditions passed → BUY signal generated")
        return "BUY"
    
    except Exception as e:
        logger.error(f"❌ Error evaluating strategy: {str(e)}")
        return "NONE"


def evaluate_condition(left: float, operator: str, right: float) -> bool:
    """
    Evaluate a single condition.
    
    Args:
        left: Left side value
        operator: One of: >, <, >=, <=, ==, !=
        right: Right side value
    
    Returns:
        bool: True if condition passes, False otherwise
    """
    try:
        if operator == ">":
            return float(left) > float(right)
        elif operator == "<":
            return float(left) < float(right)
        elif operator == ">=":
            return float(left) >= float(right)
        elif operator == "<=":
            return float(left) <= float(right)
        elif operator == "==":
            return float(left) == float(right)
        elif operator == "!=":
            return float(left) != float(right)
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    except (ValueError, TypeError) as e:
        logger.error(f"Error comparing {left} {operator} {right}: {str(e)}")
        return False


def evaluate_multiple_strategies(df: pd.DataFrame, 
                                strategies: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
    """
    Evaluate multiple strategies against the same data.
    
    Args:
        df: DataFrame with all indicators
        strategies: Dict of {strategy_name: [conditions]}
    
    Returns:
        Dict of {strategy_name: signal} where signal is "BUY", "SELL", or "NONE"
    
    Example:
        strategies = {
            "strategy_1": [...conditions...],
            "strategy_2": [...conditions...]
        }
        signals = evaluate_multiple_strategies(df, strategies)
        # signals = {"strategy_1": "BUY", "strategy_2": "NONE"}
    """
    signals = {}
    for name, conditions in strategies.items():
        signal = evaluate_strategy(df, conditions)
        signals[name] = signal
        logger.info(f"Strategy '{name}': {signal}")
    
    return signals
