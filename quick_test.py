#!/usr/bin/env python3
"""Quick test of WEEX API connectivity and order placement"""
import requests
import time
import hmac
import hashlib
import base64
import json

API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET_KEY = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASSPHRASE = "weex26647965"
BASE_URL = "https://api-contract.weex.com"
SYMBOL = "cmt_btcusdt"

print("Testing WEEX API connectivity...")

# Test public endpoint
r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={SYMBOL}", timeout=10)
print(f"Ticker Status: {r.status_code}")
print(f"Ticker Response: {r.text[:200]}")

# Test authenticated endpoint
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
    return requests.post(BASE_URL + path, headers=headers, data=body_str, timeout=30)

# Try to get account info
def send_get(path, qs):
    ts = str(int(time.time() * 1000))
    msg = ts + "GET" + path + qs
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sig,
        "ACCESS-TIMESTAMP": ts,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    return requests.get(BASE_URL + path + qs, headers=headers, timeout=30)

print("\nTesting authenticated endpoint (account)...")
r = send_get("/capi/v2/account/accounts", f"?symbol={SYMBOL}")
print(f"Account Status: {r.status_code}")
print(f"Account Response: {r.text[:300]}")

# Try placing a small test order
print("\nTrying to place a test order...")
body = {
    "symbol": SYMBOL,
    "client_oid": str(int(time.time() * 1000)),
    "size": "0.0002",  # ~$19 USDT at current BTC price
    "type": "1",  # Open Long
    "order_type": "0",
    "match_price": "1",
    "price": "80000"
}
r = send_post("/capi/v2/order/placeOrder", body)
print(f"Order Status: {r.status_code}")
print(f"Order Response: {r.text}")

if r.status_code == 200:
    result = r.json()
    order_id = result.get("order_id") or result.get("orderId")
    if order_id:
        print(f"\n✅ Order placed successfully! Order ID: {order_id}")
        
        # Now close the position
        print("\nClosing position...")
        body["type"] = "3"  # Close Long
        body["client_oid"] = str(int(time.time() * 1000))
        r = send_post("/capi/v2/order/placeOrder", body)
        print(f"Close Status: {r.status_code}")
        print(f"Close Response: {r.text}")
