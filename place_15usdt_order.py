#!/usr/bin/env python3
"""Place a 15 USDT order on WEEX"""
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

# First get current BTC price
print("Getting current BTC price...")
r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={SYMBOL}", timeout=30)
price_data = r.json()
btc_price = float(price_data.get("last", 87000))
print(f"Current BTC Price: ${btc_price}")

# Calculate size for 15 USDT
# WEEX contract value is 0.0001 BTC per contract
# So size = (USDT amount / BTC price) / 0.0001
target_usdt = 15
size_btc = target_usdt / btc_price
# Round to 4 decimal places (WEEX minimum precision)
size_btc = round(size_btc, 4)
actual_usdt = size_btc * btc_price

print(f"Target: ${target_usdt} USDT")
print(f"Size: {size_btc} BTC")
print(f"Actual value: ${actual_usdt:.2f} USDT")

# Place market order to open long
body = {
    "symbol": SYMBOL,
    "client_oid": str(int(time.time() * 1000)),
    "size": str(size_btc),
    "type": "1",     # 1 = Open Long
    "order_type": "0",
    "match_price": "1",  # Market order
    "price": "80000"
}

print(f"\nPlacing order...")
print(f"Order: {json.dumps(body, indent=2)}")
r = send_post("/capi/v2/order/placeOrder", body)
print(f"Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2)}")
