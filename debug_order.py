#!/usr/bin/env python3
"""Debug: Test single order with verbose output"""
import time, hmac, hashlib, base64, requests, json

API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET_KEY = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASSPHRASE = "weex26647965"
BASE_URL = "https://api-contract.weex.com"
SYMBOL = "cmt_btcusdt"

def send_post(path, body):
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body)
    msg = ts + "POST" + path + body_str
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sig,
        "ACCESS-TIMESTAMP": ts,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    print(f"POST {path}")
    print(f"Body: {body_str}")
    r = requests.post(BASE_URL + path, headers=headers, data=body_str, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
    return r

# 1) Set leverage
print("=== Setting Leverage ===")
send_post("/capi/v2/account/changeLeverage", {"symbol": SYMBOL, "leverage": "10", "side": "1"})

# 2) Open Long
print("\n=== Opening Long ===")
r = send_post("/capi/v2/order/placeOrder", {
    "symbol": SYMBOL,
    "client_oid": str(int(time.time() * 1000)),
    "size": "0.00015",
    "type": "1",
    "order_type": "0",
    "match_price": "1",
    "price": "80000"
})

try:
    result = r.json()
    order_id = result.get("order_id") or result.get("orderId")
    print(f"Order ID: {order_id}")
except Exception as e:
    print(f"JSON Error: {e}")
    order_id = None

time.sleep(2)

# 3) Close Long
print("\n=== Closing Long ===")
send_post("/capi/v2/order/placeOrder", {
    "symbol": SYMBOL,
    "client_oid": str(int(time.time() * 1000)),
    "size": "0.00015",
    "type": "3",
    "order_type": "0",
    "match_price": "1",
    "price": "80000"
})

# 4) Upload AI Log
print("\n=== Uploading AI Log ===")
send_post("/capi/v2/order/uploadAiLog", {
    "orderId": int(order_id) if order_id else None,
    "stage": "Decision Making",
    "model": "Claude-3.5-sonnet",
    "input": {"prompt": "Test trade analysis"},
    "output": {"signal": "LONG", "confidence": 0.75},
    "explanation": "Test AI log upload for hackathon compliance"
})

print("\n=== Done ===")
