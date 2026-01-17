#!/usr/bin/env python3
"""Show full order response to debug orderId extraction"""
import time, hmac, hashlib, base64, requests, json

API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASS = "weex26647965"
BASE = "https://api-contract.weex.com"

ts = str(int(time.time() * 1000))
body = {
    "symbol": "cmt_btcusdt",
    "client_oid": ts,
    "size": "0.00015",
    "type": "1",
    "order_type": "0",
    "match_price": "1",
    "price": "80000"
}
body_str = json.dumps(body)
msg = ts + "POST" + "/capi/v2/order/placeOrder" + body_str
sig = base64.b64encode(hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).digest()).decode()
headers = {
    "ACCESS-KEY": API_KEY,
    "ACCESS-SIGN": sig,
    "ACCESS-TIMESTAMP": ts,
    "ACCESS-PASSPHRASE": PASS,
    "Content-Type": "application/json",
    "locale": "en-US"
}

print("Placing test order...")
r = requests.post(BASE + "/capi/v2/order/placeOrder", headers=headers, data=body_str, timeout=30)
print(f"Status: {r.status_code}")
print(f"Raw Response:\n{r.text}")
print()

try:
    data = r.json()
    print(f"Parsed JSON keys: {list(data.keys())}")
    print(f"Full parsed: {json.dumps(data, indent=2)}")
except:
    print("Failed to parse JSON")
