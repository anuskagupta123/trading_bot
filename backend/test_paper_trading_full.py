"""
Complete paper trading workflow test with mock prices
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 70)
print("📊 PAPER TRADING COMPLETE WORKFLOW TEST (with mock prices)")
print("=" * 70)

# 1. Create wallet
print("\n1️⃣ Creating virtual wallet for user 1...")
r = client.post('/paper-trading/wallet/1')
assert r.status_code == 200
wallet = r.json()
print(f"   ✅ Balance: ₹{wallet['balance']:,.0f}")
print(f"   ✅ Total P&L: ₹{wallet['total_pnl']:,.0f}")

# 2. Place BUY order
print("\n2️⃣ Placing BUY order: 5x TCS @ ₹3,950...")
order_req = {
    'user_id': 1,
    'symbol': 'TCS',
    'action': 'BUY',
    'quantity': 5
}
r = client.post('/paper-trading/order', json=order_req)
assert r.status_code == 200
result = r.json()
trade1_id = result['trade_id']
print(f"   ✅ Trade ID: {trade1_id}")
print(f"   ✅ Entry Price: ₹{result['entry_price']:,.2f}")
print(f"   ✅ Order Value: ₹{result['order_value']:,.2f}")
print(f"   ✅ Remaining Balance: ₹{result['remaining_balance']:,.2f}")

# 3. Place another BUY order
print("\n3️⃣ Placing BUY order: 10x RELIANCE @ ₹2,850...")
order_req = {
    'user_id': 1,
    'symbol': 'RELIANCE',
    'action': 'BUY',
    'quantity': 10
}
r = client.post('/paper-trading/order', json=order_req)
assert r.status_code == 200
result = r.json()
trade2_id = result['trade_id']
print(f"   ✅ Trade ID: {trade2_id}")
print(f"   ✅ Entry Price: ₹{result['entry_price']:,.2f}")
print(f"   ✅ Order Value: ₹{result['order_value']:,.2f}")
print(f"   ✅ Remaining Balance: ₹{result['remaining_balance']:,.2f}")

# 4. Check wallet
print("\n4️⃣ Checking wallet status...")
r = client.get('/paper-trading/wallet/1')
assert r.status_code == 200
wallet = r.json()
print(f"   ✅ Available Balance: ₹{wallet['balance']:,.2f}")
print(f"   ✅ Unrealized P&L: ₹{wallet['unrealized_pnl']:,.2f}")
print(f"   ✅ Open Trades: {wallet['open_trades']}")
print(f"   ✅ Net Value: ₹{wallet['net_value']:,.2f}")

# 5. Close first trade (TCS) with profit
print("\n5️⃣ Closing TCS trade (simulating +2% profit)...")
# Mock: TCS at 4029 (3950 * 1.02)
r = client.post(f'/paper-trading/close/{trade1_id}')
assert r.status_code == 200
result = r.json()
print(f"   ✅ Entry Price: ₹{result['entry_price']:,.2f}")
print(f"   ✅ Exit Price: ₹{result['exit_price']:,.2f}")
print(f"   ✅ P&L: ₹{result['pnl']:,.2f} ({result['pnl_pct']:.2f}%)")
print(f"   ✅ Wallet Balance: ₹{result['wallet_balance']:,.2f}")
print(f"   ✅ Total P&L: ₹{result['total_pnl']:,.2f}")

# 6. Get all trades
print("\n6️⃣ Fetching all trades for user 1...")
r = client.get('/paper-trading/trades/1')
assert r.status_code == 200
result = r.json()
print(f"   ✅ Total Trades: {result['total_trades']}")
for i, trade in enumerate(result['trades'], 1):
    status = "✅ CLOSED" if trade['status'] == 'closed' else "⏳ OPEN"
    if trade['pnl']:
        print(f"      {i}. {trade['symbol']:10} {trade['action']:4} x{trade['quantity']:5} {status} P&L: ₹{trade['pnl']:.2f}")
    else:
        print(f"      {i}. {trade['symbol']:10} {trade['action']:4} x{trade['quantity']:5} {status}")

# 7. Get summary
print("\n7️⃣ Getting trade summary...")
r = client.get('/paper-trading/trades/1/summary')
assert r.status_code == 200
result = r.json()
print(f"   ✅ Total Trades: {result['total_trades']}")
print(f"   ✅ Open Trades: {result['open_trades']}")
print(f"   ✅ Closed Trades: {result['closed_trades']}")
print(f"   ✅ Winning Trades: {result['winning_trades']}")
print(f"   ✅ Losing Trades: {result['losing_trades']}")
print(f"   ✅ Win Rate: {result['win_rate']}")
print(f"   ✅ Realized P&L: ₹{result['realized_pnl']:,.2f}")
print(f"   ✅ Unrealized P&L: ₹{result['unrealized_pnl']:,.2f}")
print(f"   ✅ Total P&L: ₹{result['total_pnl']:,.2f}")

print("\n" + "=" * 70)
print("✅ ALL PAPER TRADING TESTS PASSED!")
print("=" * 70)
print("\nPaper trading system features:")
print("  • Virtual wallet with ₹1,00,000 starting capital")
print("  • Mock prices for 10 popular stocks (works without broker)")
print("  • Place BUY/SELL orders")
print("  • Close trades with automatic P&L calculation")
print("  • Track open/closed trades and statistics")
print("  • Real-time wallet balance and P&L tracking")
print("\nNext: Connect a real broker to use live prices!")
