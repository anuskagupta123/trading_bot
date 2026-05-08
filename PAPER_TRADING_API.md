# 📊 Paper Trading API Documentation

## Overview

The Paper Trading system allows users to simulate trading without real capital or broker connections. It's perfect for:
- **Learning**: Practice trading strategies risk-free
- **Testing**: Validate strategy logic before live trading
- **Demo**: Show trading without requiring real credentials

## Features

✅ Virtual wallet with ₹1,00,000 starting capital  
✅ Mock prices for 10 popular NSE stocks  
✅ Works without broker credentials (dev mode)  
✅ Automatic P&L calculation  
✅ Real-time balance tracking  
✅ Trade history and statistics  

## Endpoints

### 1. Create/Get Virtual Wallet

**Create wallet for a user**
```
POST /paper-trading/wallet/{user_id}
```

Response:
```json
{
  "user_id": 1,
  "balance": 100000.0,
  "total_pnl": 0.0,
  "net_value": 100000.0,
  "created_at": "2025-05-08T09:19:21"
}
```

**Get wallet status**
```
GET /paper-trading/wallet/{user_id}
```

Response:
```json
{
  "balance": 51750.0,
  "total_pnl": 0.0,
  "unrealized_pnl": 0.0,
  "net_value": 51750.0,
  "open_trades": 2
}
```

---

### 2. Place Paper Orders

**Place a BUY or SELL order**
```
POST /paper-trading/order
```

Request:
```json
{
  "user_id": 1,
  "symbol": "TCS",
  "action": "BUY",
  "quantity": 5
}
```

Response:
```json
{
  "status": "success",
  "trade_id": 1,
  "symbol": "TCS",
  "action": "BUY",
  "quantity": 5,
  "entry_price": 3950.0,
  "order_value": 19750.0,
  "remaining_balance": 80250.0
}
```

**Available symbols (mock prices):**
- TCS: ₹3,950
- RELIANCE: ₹2,850
- INFY: ₹2,100
- WIPRO: ₹850
- HDFC: ₹2,750
- ITC: ₹450
- LT: ₹2,000
- MARUTI: ₹12,500
- BAJAJ: ₹8,900
- SBIN: ₹750

Other symbols default to ₹2,500.

---

### 3. Close Paper Trades

**Close an open trade**
```
POST /paper-trading/close/{trade_id}
```

Response:
```json
{
  "status": "success",
  "trade_id": 1,
  "symbol": "TCS",
  "action": "BUY",
  "entry_price": 3950.0,
  "exit_price": 4029.0,
  "quantity": 5,
  "pnl": 395.0,
  "pnl_pct": 2.0,
  "wallet_balance": 80645.0,
  "total_pnl": 395.0
}
```

---

### 4. View Paper Trades

**Get all trades for a user**
```
GET /paper-trading/trades/{user_id}?status=open
```

Query params:
- `status`: "open", "closed", or null for all

Response:
```json
{
  "user_id": 1,
  "total_trades": 2,
  "trades": [
    {
      "id": 1,
      "symbol": "TCS",
      "action": "BUY",
      "quantity": 5,
      "entry_price": 3950.0,
      "exit_price": 4029.0,
      "pnl": 395.0,
      "pnl_pct": 2.0,
      "status": "closed",
      "opened_at": "2025-05-08T09:20:00",
      "closed_at": "2025-05-08T09:25:00"
    }
  ]
}
```

---

### 5. Trade Statistics

**Get summary statistics**
```
GET /paper-trading/trades/{user_id}/summary
```

Response:
```json
{
  "total_trades": 2,
  "open_trades": 1,
  "closed_trades": 1,
  "winning_trades": 1,
  "losing_trades": 0,
  "win_rate": "100.0%",
  "realized_pnl": 395.0,
  "unrealized_pnl": 0.0,
  "total_pnl": 395.0
}
```

---

## Example Workflow

```bash
# 1. Create wallet (₹1,00,000 starting capital)
curl -X POST http://localhost:8000/paper-trading/wallet/1

# 2. Place BUY order
curl -X POST http://localhost:8000/paper-trading/order \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "symbol": "RELIANCE",
    "action": "BUY",
    "quantity": 10
  }'

# 3. Check wallet balance
curl http://localhost:8000/paper-trading/wallet/1

# 4. View open trades
curl http://localhost:8000/paper-trading/trades/1?status=open

# 5. Close the trade
curl -X POST http://localhost:8000/paper-trading/close/1

# 6. Get trade statistics
curl http://localhost:8000/paper-trading/trades/1/summary
```

---

## How It Works

### Order Placement
1. **Validate** input (action, quantity, symbol)
2. **Get price** from mock prices (no broker call needed)
3. **Check balance** (for BUY orders, ensure ₹ balance available)
4. **Deduct cost** from wallet balance
5. **Create trade record** with status="open"

### Trade Closing
1. **Get current price** from mock prices
2. **Calculate P&L** based on action (BUY/SELL) and price difference
3. **Update trade** with exit_price, pnl, status="closed"
4. **Add P&L** back to wallet balance and total_pnl

### P&L Calculation
```
For BUY orders:
  P&L = (exit_price - entry_price) × quantity
  
For SELL orders:
  P&L = (entry_price - exit_price) × quantity
  
P&L % = (P&L / order_value) × 100
```

---

## Database Schema

### VirtualWallet
```python
id: Integer (primary key)
user_id: Integer (unique)
balance: Float (₹1,00,000 default)
total_pnl: Float (cumulative realized P&L)
created_at: DateTime
updated_at: DateTime
```

### PaperTrade
```python
id: Integer (primary key)
user_id: Integer
symbol: String
action: String ("BUY" or "SELL")
quantity: Integer
entry_price: Float
exit_price: Float (nullable)
pnl: Float (nullable)
pnl_pct: Float (nullable)
status: String ("open" or "closed")
opened_at: DateTime
closed_at: DateTime (nullable)
```

---

## Integration with Live Trading

To switch from paper to live trading:

1. **Connect broker** via `/brokers/connect` endpoint
2. **Use live broker** for price fetching (automatic fallback to mock if broker unavailable)
3. **Switch to real orders** by calling Zerodha API instead of creating PaperTrade records

The paper trading system gracefully falls back to mock prices if no broker is connected, making it perfect for development and testing.

---

## Testing

Run the test script to verify all features:

```bash
python test_paper_trading_full.py
```

Expected output:
- ✅ Wallet creation
- ✅ Order placement
- ✅ Balance management
- ✅ Trade closing
- ✅ P&L calculation
- ✅ Statistics tracking

---

## Error Handling

| Error | Code | Solution |
|-------|------|----------|
| Action not BUY/SELL | 400 | Use valid action |
| Quantity invalid | 400 | Use 1-10000 |
| Insufficient balance | 400 | Reduce order size |
| Trade not found | 404 | Check trade_id |
| Trade already closed | 400 | Can't close twice |

---

## Next Steps

1. **Connect real broker** for live prices
2. **Integrate with strategy engine** for automated signal testing
3. **Add paper trade → live order** conversion
4. **Build frontend UI** for paper trading dashboard

