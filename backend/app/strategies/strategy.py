import yfinance as yf

def check_signal():
    data = yf.download("NIFTYBEES.NS", period="1d", interval="1m")

    if data.empty:
        return "NO DATA"

    try:
        # ✅ FIX: convert to float
        latest_price = float(data["Close"].iloc[-1])

        print("Current Price:", latest_price)

        if latest_price > 242:
            return "BUY"
        elif latest_price < 240:
            return "SELL"
        else:
            return "HOLD"

    except Exception as e:
        print("Error:", e)
        return "ERROR"