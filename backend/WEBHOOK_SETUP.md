# Webhook Setup & Testing Guide

## 🚀 Quick Start

### 1. Initialize Database
```bash
cd backend
python init_db.py
```

### 2. Start the Server
```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### 3. Test Webhook Endpoint
Go to: `http://localhost:8000/docs`
- Find `/webhook` endpoint
- Click "Try it out"
- Paste this JSON:
```json
{
  "symbol": "RELIANCE",
  "action": "BUY",
  "quantity": 1,
  "secret": "my-secret-token-123"
}
```
- Click Execute

### 4. View Webhook Logs
```
GET http://localhost:8000/webhook/logs
GET http://localhost:8000/webhook/stats
```

---

## 🌐 Testing with TradingView (Local Setup)

### Step 1: Install ngrok
Download from: https://ngrok.com/download

```bash
# On Windows
ngrok.exe http 8000

# On Mac/Linux
ngrok http 8000
```

You'll see:
```
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Step 2: Create Alert in TradingView

1. Go to TradingView chart
2. Right-click → **Add Alert**
3. Set up your condition (e.g., price > 100)
4. Scroll down to **Notifications**
5. Check "Webhook URL"
6. Enter your webhook URL:
   ```
   https://abc123.ngrok.io/webhook
   ```

7. Paste this in **Alert message**:
   ```json
   {
     "symbol": "RELIANCE",
     "action": "BUY",
     "quantity": 1,
     "secret": "my-secret-token-123"
   }
```

8. Click Create

---

## 🔐 Production Security Checklist

Before deploying to production:

- [ ] Change `WEBHOOK_SECRET` to a strong random token
- [ ] Move secret to `.env` file: `WEBHOOK_SECRET=your-secret-here`
- [ ] Update `.env` in `app/routes/webhook.py`:
  ```python
  import os
  WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default-secret")
  ```
- [ ] Enable HTTPS only (use Render/Railway/AWS)
- [ ] Add IP whitelist for TradingView servers (optional)
- [ ] Implement rate limiting (max alerts per minute)
- [ ] Add authentication for `/webhook/logs` endpoint

---

## 🐛 Debugging

### Check Recent Logs
```bash
curl http://localhost:8000/webhook/logs
```

### Check Statistics
```bash
curl http://localhost:8000/webhook/stats
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Invalid secret | Wrong secret token | Match it exactly in TradingView alert |
| 400 No active broker | Broker not connected | Register broker via `/brokers/connect` |
| 500 Order failed | API issue | Check broker credentials & access token |

---

## 📝 API Response Examples

### Success (200)
```json
{
  "status": "success",
  "order_id": "123456789",
  "symbol": "RELIANCE",
  "action": "BUY",
  "quantity": 1,
  "broker": "zerodha",
  "log_id": 1
}
```

### Failed Secret (401)
```json
{
  "detail": "Invalid secret token"
}
```

### No Broker (400)
```json
{
  "detail": "No active broker configured"
}
```

---

## 🔄 Next: Broker Setup

Before placing real trades, register your broker:

### 1. Get Zerodha API Keys
- Go to: https://kite.trade/
- Create account
- Generate API key & secret

### 2. Register Broker
```bash
curl -X POST http://localhost:8000/brokers/connect \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "broker_name": "zerodha",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret"
  }'
```

### 3. Complete OAuth Login
Get your `access_token` from Zerodha and update:
```bash
curl -X PUT http://localhost:8000/brokers/1 \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your-access-token",
    "is_active": true
  }'
```

---

## ⚠️ Warning: Paper Trading First

**Always test with paper trading before real capital!**
- Enable paper trading in Zerodha
- Verify orders show up in your account
- Check webhook logs for errors
- Monitor live for 1-2 days
