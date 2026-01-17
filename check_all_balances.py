#!/usr/bin/env python3
"""Check ALL account balances on WEEX - comprehensive check"""
import time, hmac, hashlib, base64, requests, json

api_key = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
secret_key = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
access_passphrase = "weex26647965"
BASE_URL = "https://api-contract.weex.com"

# All supported symbols in the competition
SYMBOLS = [
    "cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt",
    "cmt_xrpusdt", "cmt_adausdt", "cmt_bnbusdt", "cmt_ltcusdt"
]

def send_get(path, qs=""):
    ts = str(int(time.time() * 1000))
    msg = ts + "GET" + path + qs
    sig = base64.b64encode(hmac.new(secret_key.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {"ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts, "ACCESS-PASSPHRASE": access_passphrase, "Content-Type": "application/json", "locale": "en-US"}
    return requests.get(BASE_URL + path + qs, headers=headers, timeout=30)

print("=" * 60)
print("COMPREHENSIVE WEEX BALANCE CHECK")
print("=" * 60)

# 1. Check assets endpoint (general account)
print("\n[1] Checking /capi/v2/account/assets ...")
r = send_get("/capi/v2/account/assets", "")
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

# 2. Check account info for each symbol
print("\n[2] Checking account info per symbol...")
for symbol in SYMBOLS:
    r = send_get("/capi/v2/account/accounts", f"?symbol={symbol}")
    data = r.json()
    
    if "collateral" in data and len(data["collateral"]) > 0:
        col = data["collateral"][0]
        available = float(col.get("available", 0))
        equity = float(col.get("equity", 0))
        if available > 0 or equity > 0:
            print(f"  {symbol}: Available=${available:.2f}, Equity=${equity:.2f}")
    
    if "account" in data and r.status_code == 200:
        acc = data.get("account", {})
        user_id = acc.get("user_id")
        if user_id:
            print(f"  {symbol}: user_id={user_id}")
            break  # Only need to show user_id once

# 3. Check if there's a separate account balance endpoint
print("\n[3] Checking /capi/v2/account/account (singular) ...")
r = send_get("/capi/v2/account/account", "")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"Response: {r.text[:500]}")
else:
    print("Endpoint not available")

# 4. Check positions across all symbols
print("\n[4] Checking all positions...")
r = send_get("/capi/v2/position/allPosition", "")
print(f"Status: {r.status_code}")
data = r.json()
if isinstance(data, dict) and "data" in data:
    positions = data.get("data", [])
    if positions:
        print(f"Found {len(positions)} positions")
        for pos in positions:
            print(f"  {pos}")
    else:
        print("No open positions")
elif isinstance(data, list) and len(data) > 0:
    print(f"Found {len(data)} positions")
else:
    print(f"Response: {data}")

# 5. Summary
print("\n" + "=" * 60)
print("KEY INFO FOR WEEX SUPPORT")
print("=" * 60)
r = send_get("/capi/v2/account/accounts", "?symbol=cmt_btcusdt")
data = r.json()
if "account" in data:
    acc = data["account"]
    print(f"API Account user_id: {acc.get('user_id')}")
    print(f"API Account id: {acc.get('id')}")
    print(f"client_account_id: {acc.get('client_account_id')}")
print(f"Competition UID (from WEEX support): 8937798547")
print("\nIf these don't match, the API key needs to be regenerated for the correct account.")
