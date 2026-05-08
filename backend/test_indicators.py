"""
Test script for indicators and strategy evaluation
"""
import pandas as pd
from app.indicators.calculator import add_indicators, get_indicator_list
from app.strategies.engine import evaluate_strategy

# Create sample OHLCV data
df = pd.DataFrame({
    'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
    'close': [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
    'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
})

print("📊 Sample candle data:")
print(df.tail(3))
print()

# Add indicators
config = {
    "ema": [{"length": 3}, {"length": 5}],
    "rsi": [{"length": 5}],
    "atr": [{"length": 5}]
}

df = add_indicators(df, config)
print("\n✅ Indicators added. Columns:", list(df.columns))
print(df.tail(2))
print()

# Evaluate strategy
conditions = [
    {"indicator": "EMA_3", "operator": ">", "compare_to": "EMA_5"},
    {"indicator": "RSI", "operator": ">", "compare_to": "value", "value": 30},
    {"indicator": "close", "operator": ">", "compare_to": "value", "value": 105}
]

signal = evaluate_strategy(df, conditions)
print(f"\n🎯 Strategy Signal: {signal}")

# Show available indicators
print("\n📈 Available Indicators for Frontend:")
indicators = get_indicator_list()
for ind_name, ind_info in list(indicators.items())[:3]:
    print(f"  • {ind_name}: {ind_info['name']}")
print("  ... and more")
