#!/usr/bin/env python3
"""
WEEX Automated Trading - Non-Interactive Version
Executes 10 trades automatically for AI Wars Hackathon
"""

import time
import hmac
import hashlib
import base64
import requests
import json
from datetime import datetime

# Configuration
API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET_KEY = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASSPHRASE = "weex26647965"
BASE_URL = "https://api-contract.weex.com"
SYMBOL = "cmt_btcusdt"
LEVERAGE = 10
POSITION_SIZE = "0.0002"
NUM_CYCLES = 5
DELAY = 3

def send_post(path, body):
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body)
    msg = ts + "POST" + path + body_str
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {"ACCESS-KEY": API_KEY, "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts, "ACCESS-PASSPHRASE": PASSPHRASE, "Content-Type": "application/json", "locale": "en-US"}
    return requests.post(BASE_URL + path, headers=headers, data=body_str, timeout=30)

def place_order(order_type):
    body = {"symbol": SYMBOL, "client_oid": str(int(time.time()*1000)), "size": POSITION_SIZE, "type": str(order_type), "order_type": "0", "match_price": "1", "price": "80000"}
    r = send_post("/capi/v2/order/placeOrder", body)
    return r.status_code == 200, r.json()

print("=" * 60)
print("WEEX AUTOMATED TRADING - AI Wars Hackathon")
print("=" * 60)
print(f"Start: {datetime.now()}")
print(f"Target: {NUM_CYCLES} cycles = {NUM_CYCLES * 2} trades")

# Get price
r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={SYMBOL}", timeout=30)
btc_price = float(r.json().get("last", 87000))
print(f"BTC Price: ${btc_price:,.2f}")
print(f"Trade Value: ${float(POSITION_SIZE) * btc_price:.2f} USDT")
print()

trades = 0
log = []

for cycle in range(1, NUM_CYCLES + 1):
    print(f"\n--- Cycle {cycle}/{NUM_CYCLES} ---")
    
    # Open Long
    print(f"[{trades+1}] Opening LONG...", end=" ")
    ok, res = place_order(1)
    if ok:
        print(f"OK: {res.get('order_id')}")
        log.append({"n": trades+1, "type": "OPEN_LONG", "order": res.get('order_id')})
        trades += 1
    else:
        print(f"FAIL: {res}")
    time.sleep(DELAY)
    
    # Close Long
    print(f"[{trades+1}] Closing LONG...", end=" ")
    ok, res = place_order(3)
    if ok:
        print(f"OK: {res.get('order_id')}")
        log.append({"n": trades+1, "type": "CLOSE_LONG", "order": res.get('order_id')})
        trades += 1
    else:
        print(f"FAIL: {res}")
    time.sleep(DELAY)

print("\n" + "=" * 60)
print(f"COMPLETE! Total trades: {trades}")
print("=" * 60)

for t in log:
    print(f"  #{t['n']}: {t['type']} -> {t['order']}")

with open("trade_log.json", "w") as f:
    json.dump(log, f, indent=2)
print("\nLog saved to trade_log.json")

if trades >= 10:
    print("\n🎉 Met the 10-trade minimum requirement!")
