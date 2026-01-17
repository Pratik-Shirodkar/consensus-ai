#!/usr/bin/env python3
"""
WEEX API Test Script - Auto-Run Version
AI Wars: WEEX Alpha Awakens Hackathon
"""

import time
import hmac
import hashlib
import base64
import requests
import json

# Configuration
api_key = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
secret_key = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
access_passphrase = "weex26647965"
BASE_URL = "https://api-contract.weex.com/"
SYMBOL = "cmt_btcusdt"

def generate_signature(secret_key, timestamp, method, request_path, query_string, body):
    message = timestamp + method.upper() + request_path + query_string + str(body)
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def generate_signature_get(secret_key, timestamp, method, request_path, query_string):
    message = timestamp + method.upper() + request_path + query_string
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def send_post(request_path, body):
    timestamp = str(int(time.time() * 1000))
    body_str = json.dumps(body)
    signature = generate_signature(secret_key, timestamp, "POST", request_path, "", body_str)
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    return requests.post(BASE_URL + request_path, headers=headers, data=body_str, timeout=30)

def send_get(request_path, query_string):
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature_get(secret_key, timestamp, "GET", request_path, query_string)
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    return requests.get(BASE_URL + request_path + query_string, headers=headers, timeout=30)

print("=" * 70)
print("WEEX API TEST - AI Wars: WEEX Alpha Awakens Hackathon")
print("=" * 70)
print(f"API Key: {api_key[:15]}...")
print(f"Base URL: {BASE_URL}")
print(f"Symbol: {SYMBOL}")
print()

# Step 3: Get Account Balance
print("\n" + "=" * 60)
print("STEP 3: Checking Account Balance")
print("=" * 60)
try:
    r = send_get("/capi/v2/account/accounts", f"?symbol={SYMBOL}")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Step 4: Set Leverage
print("\n" + "=" * 60)
print("STEP 4: Setting Leverage to 10x")
print("=" * 60)
try:
    body = {"symbol": SYMBOL, "leverage": "10", "side": "1"}
    r = send_post("/capi/v2/account/changeLeverage", body)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Step 5: Get Price
print("\n" + "=" * 60)
print("STEP 5: Getting Asset Price (BTC/USDT)")
print("=" * 60)
try:
    r = requests.get(f"{BASE_URL}capi/v2/market/ticker?symbol={SYMBOL}", timeout=30)
    print(f"Status: {r.status_code}")
    data = r.json()
    if "last" in data:
        print(f"Current BTC Price: ${data['last']}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Step 6-8: Place Order
print("\n" + "=" * 60)
print("STEP 6-8: Placing Order (0.01 BTC Market Buy)")
print("=" * 60)
try:
    client_oid = str(int(time.time() * 1000))
    body = {
        "symbol": SYMBOL,
        "client_oid": client_oid,
        "size": "0.01",
        "type": "1",
        "order_type": "0",
        "match_price": "1",
        "price": "80000"
    }
    r = send_post("/capi/v2/order/placeOrder", body)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\nWaiting 3 seconds for order to process...")
time.sleep(3)

# Step 9: Get Current Orders
print("\n" + "=" * 60)
print("STEP 9: Getting Current Orders")
print("=" * 60)
try:
    r = send_get("/capi/v2/order/currentOrders", f"?symbol={SYMBOL}")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Step 10: Get Order History
print("\n" + "=" * 60)
print("STEP 10: Getting Order History")
print("=" * 60)
try:
    r = send_get("/capi/v2/order/historyOrders", f"?symbol={SYMBOL}&pageSize=20&pageNo=1")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Step 11: Get Trade Details
print("\n" + "=" * 60)
print("STEP 11: Getting Trade Details (Fills)")
print("=" * 60)
try:
    r = send_get("/capi/v2/order/fills", f"?symbol={SYMBOL}&pageSize=20&pageNo=1")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("API TEST COMPLETED!")
print("=" * 70)
