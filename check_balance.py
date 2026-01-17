#!/usr/bin/env python3
"""Check detailed account balance on WEEX"""
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

# Get current BTC price
r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={SYMBOL}", timeout=30)
btc_price = float(r.json().get("last", 0))
print(f"Current BTC Price: ${btc_price:,.2f}")
print()

# Get account info
r = send_get("/capi/v2/account/accounts", f"?symbol={SYMBOL}")
data = r.json()

if "account" in data:
    acc = data["account"]
    print("=" * 50)
    print("ACCOUNT SUMMARY")
    print("=" * 50)
    print(f"Account ID: {acc.get('id')}")
    
if "collateral" in data and len(data["collateral"]) > 0:
    col = data["collateral"][0]
    available = float(col.get("available", 0))
    equity = float(col.get("equity", 0))
    margin = float(col.get("margin", 0))
    frozen = float(col.get("frozen", 0))
    
    print()
    print("=" * 50)
    print("BALANCE DETAILS")
    print("=" * 50)
    print(f"Available Balance: ${available:,.2f} USDT")
    print(f"Equity: ${equity:,.2f} USDT")
    print(f"Used Margin: ${margin:,.2f} USDT")
    print(f"Frozen: ${frozen:,.2f} USDT")

if "position" in data and len(data["position"]) > 0:
    pos = data["position"][0]
    size = float(pos.get("size", 0))
    entry = float(pos.get("avg_price", 0))
    direction = pos.get("direction", "N/A")
    unrealized = pos.get("unrealizePnl", "0")
    
    position_value = size * btc_price
    
    print()
    print("=" * 50)
    print("OPEN POSITION")
    print("=" * 50)
    print(f"Direction: {direction}")
    print(f"Size: {size} BTC")
    print(f"Entry Price: ${entry:,.2f}")
    print(f"Current Value: ${position_value:,.2f} USDT")
    print(f"Unrealized P&L: {unrealized}")
else:
    print()
    print("No open positions")
