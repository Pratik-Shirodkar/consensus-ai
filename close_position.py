#!/usr/bin/env python3
"""Close position on WEEX"""
import time, hmac, hashlib, base64, requests, json

api_key = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
secret_key = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
access_passphrase = "weex26647965"
BASE_URL = "https://api-contract.weex.com"
SYMBOL = "cmt_btcusdt"

def send_post(path, body):
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body)
    msg = ts + "POST" + path + body_str
    sig = base64.b64encode(hmac.new(secret_key.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {"ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts, "ACCESS-PASSPHRASE": access_passphrase, "Content-Type": "application/json", "locale": "en-US"}
    return requests.post(BASE_URL + path, headers=headers, data=body_str, timeout=30)

# Close Long position (type=3) with market order (match_price=1)
body = {
    "symbol": SYMBOL,
    "client_oid": str(int(time.time() * 1000)),
    "size": "0.0002",  # Close entire position
    "type": "3",     # 3 = Close Long
    "order_type": "0",
    "match_price": "1",  # Market order
    "price": "80000"
}

print("Closing position...")
print(f"Order: {json.dumps(body, indent=2)}")
r = send_post("/capi/v2/order/placeOrder", body)
print(f"Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2)}")
