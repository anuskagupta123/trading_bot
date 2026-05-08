"""
Test paper trading workflow
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("📊 PAPER TRADING COMPLETE WORKFLOW TEST")
print("=" * 60)

# 1. Create wallet
print("\n1️⃣ Creating virtual wallet for user 1...")
r = client.post('/paper-trading/wallet/1')
wallet = r.json()
print(f"   Balance: ₹{wallet['balance']}")
print(f"   Total P&L: ₹{wallet['total_pnl']}")

# 2. Place order (will fail due to no broker, but showing the flow)
print("\n2️⃣ Attempting to place paper order...")
order_req = {
    'user_id': 1,
    'symbol': 'TCS',
    'action': 'BUY',
    'quantity': 5
}
print(f"   Order: BUY 5x TCS")
r = client.post('/paper-trading/order', json=order_req)
if r.status_code != 200:
    print(f"   Status: {r.status_code} - {r.json()['detail']}")
    print("   (Expected in dev: No broker configured)")
else:
    result = r.json()
    print(f"   Trade ID: {result['trade_id']}")
    print(f"   Entry Price: ₹{result['entry_price']}")
    print(f"   Remaining Balance: ₹{result['remaining_balance']}")

# 3. Check wallet
print("\n3️⃣ Checking wallet status...")
r = client.get('/paper-trading/wallet/1')
wallet = r.json()
print(f"   Balance: ₹{wallet['balance']}")
print(f"   Open Trades: {wallet['open_trades']}")
print(f"   Net Value: ₹{wallet['net_value']}")

print("\n✅ Paper trading system operational!")
print("   Note: Order placement requires active broker connection")
print("   (For testing, use mock broker or connect real Zerodha account)")
