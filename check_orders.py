#!/usr/bin/env python3
"""Check orders on WEEX"""
import time, hmac, hashlib, base64, requests, json

api_key = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
secret_key = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
access_passphrase = "weex26647965"
BASE_URL = "https://api-contract.weex.com"
SYMBOL = "cmt_btcusdt"

def send_get(path, qs):
    ts = str(int(time.time() * 1000))
    msg = ts + "GET" + path + qs
    sig = base64.b64encode(hmac.new(secret_key.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {"ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts, "ACCESS-PASSPHRASE": access_passphrase, "Content-Type": "application/json", "locale": "en-US"}
    return requests.get(BASE_URL + path + qs, headers=headers, timeout=30)

print("=" * 60)
print("Current Open Orders")
print("=" * 60)
r = send_get("/capi/v2/order/currentOrders", f"?symbol={SYMBOL}")
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))

print("\n" + "=" * 60)
print("Order History (Last 10)")
print("=" * 60)
r = send_get("/capi/v2/order/historyOrders", f"?symbol={SYMBOL}&pageSize=10&pageNo=1")
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))

print("\n" + "=" * 60)
print("Trade Fills (Last 10)")
print("=" * 60)
r = send_get("/capi/v2/order/fills", f"?symbol={SYMBOL}&pageSize=10&pageNo=1")
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))
