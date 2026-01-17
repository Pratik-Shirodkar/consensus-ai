#!/usr/bin/env python3
"""
WEEX API Complete Test - AI Wars Hackathon
"""

import time
import hmac
import hashlib
import base64
import requests
import json

api_key = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
secret_key = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
access_passphrase = "weex26647965"
BASE_URL = "https://api-contract.weex.com"
SYMBOL = "cmt_btcusdt"


def send_get(path, qs):
    ts = str(int(time.time() * 1000))
    msg = ts + "GET" + path + qs
    sig = base64.b64encode(hmac.new(secret_key.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": sig,
        "ACCESS-TIMESTAMP": ts,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    return requests.get(BASE_URL + path + qs, headers=headers, timeout=30)


def send_post(path, body):
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body)
    msg = ts + "POST" + path + body_str
    sig = base64.b64encode(hmac.new(secret_key.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": sig,
        "ACCESS-TIMESTAMP": ts,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    return requests.post(BASE_URL + path, headers=headers, data=body_str, timeout=30)


print("=" * 70)
print("WEEX API TEST - AI Wars: WEEX Alpha Awakens Hackathon")
print("=" * 70)

# STEP 3: Check Account Balance
print("\n" + "=" * 60)
print("STEP 3: Check Account Balance")
print("=" * 60)
try:
    r = send_get("/capi/v2/account/accounts", f"?symbol={SYMBOL}")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if "account" in data:
            print(f"Account ID: {data['account'].get('id')}")
            print(f"Full Response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 4: Set Leverage
print("\n" + "=" * 60)
print("STEP 4: Set Leverage to 10x")
print("=" * 60)
try:
    r = send_post("/capi/v2/account/changeLeverage", {"symbol": SYMBOL, "leverage": "10", "side": "1"})
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 5: Get Price
print("\n" + "=" * 60)
print("STEP 5: Get BTC/USDT Price")
print("=" * 60)
try:
    r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={SYMBOL}", timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"BTC Price: USD {data.get('last', 'N/A')}")
        print(f"Best Bid: {data.get('best_bid')}")
        print(f"Best Ask: {data.get('best_ask')}")
except Exception as e:
    print(f"Error: {e}")

# STEP 6-8: Place Order
print("\n" + "=" * 60)
print("STEP 6-8: Place Order (0.01 BTC Market Buy)")  
print("=" * 60)
try:
    client_oid = str(int(time.time() * 1000))
    body = {
        "symbol": SYMBOL,
        "client_oid": client_oid,
        "size": "0.01",
        "type": "1",  # 1=Open Long
        "order_type": "0",  # Normal
        "match_price": "1",  # Market
        "price": "80000"
    }
    print(f"Order: {json.dumps(body, indent=2)}")
    r = send_post("/capi/v2/order/placeOrder", body)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\nWaiting 3 seconds for order to process...")
time.sleep(3)

# STEP 9: Get Current Orders
print("\n" + "=" * 60)
print("STEP 9: Get Current/Open Orders")
print("=" * 60)
try:
    r = send_get("/capi/v2/order/currentOrders", f"?symbol={SYMBOL}")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 10: Get Order History
print("\n" + "=" * 60)
print("STEP 10: Get Order History")
print("=" * 60)
try:
    r = send_get("/capi/v2/order/historyOrders", f"?symbol={SYMBOL}&pageSize=5&pageNo=1")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 11: Get Trade Details
print("\n" + "=" * 60)
print("STEP 11: Get Trade Details/Fills")
print("=" * 60)
try:
    r = send_get("/capi/v2/order/fills", f"?symbol={SYMBOL}&pageSize=5&pageNo=1")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("API TEST COMPLETED!")
print("=" * 70)
