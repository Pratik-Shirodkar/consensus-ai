#!/usr/bin/env python3
"""
Monitor WEEX Account Balance and Positions
For AI Wars Competition Tracking
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

SYMBOLS = [
    "cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt",
    "cmt_xrpusdt", "cmt_adausdt", "cmt_bnbusdt", "cmt_ltcusdt"
]

STARTING_BALANCE = 1000.0  # Competition starting balance

def send_get(path, qs=""):
    ts = str(int(time.time() * 1000))
    msg = ts + "GET" + path + qs
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {"ACCESS-KEY": API_KEY, "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts, "ACCESS-PASSPHRASE": PASSPHRASE, "Content-Type": "application/json", "locale": "en-US"}
    return requests.get(BASE_URL + path + qs, headers=headers, timeout=30)

def safe_json(r):
    try:
        return r.json()
    except:
        return {}

def get_prices():
    """Get current prices for all supported coins"""
    prices = {}
    for symbol in SYMBOLS:
        try:
            r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={symbol}", timeout=5)
            if r.status_code == 200:
                prices[symbol] = float(r.json().get("last", 0))
        except:
            pass
    return prices

def main():
    print("=" * 70)
    print("  🏆 AI WARS COMPETITION MONITOR")
    print("=" * 70)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get account assets
    r = send_get("/capi/v2/account/assets", "")
    assets = safe_json(r)
    
    total_balance = 0
    if isinstance(assets, list):
        for asset in assets:
            if asset.get("coinName") == "USDT":
                total_balance = float(asset.get("equity", 0))
                available = float(asset.get("available", 0))
                frozen = float(asset.get("frozen", 0))
                unrealized = float(asset.get("unrealizePnl", 0))
    
    # Calculate P&L
    pnl = total_balance - STARTING_BALANCE
    pnl_pct = (pnl / STARTING_BALANCE) * 100 if STARTING_BALANCE > 0 else 0
    
    print("  📊 ACCOUNT SUMMARY")
    print("  " + "-" * 50)
    print(f"  Starting Balance:   ${STARTING_BALANCE:,.2f} USDT")
    print(f"  Current Equity:     ${total_balance:,.2f} USDT")
    print(f"  Available:          ${available:,.2f} USDT")
    if frozen > 0:
        print(f"  Frozen:             ${frozen:,.2f} USDT")
    if unrealized != 0:
        print(f"  Unrealized P&L:     ${unrealized:,.2f} USDT")
    print()
    
    # P&L Display
    pnl_emoji = "📈" if pnl >= 0 else "📉"
    pnl_color = "+" if pnl >= 0 else ""
    print(f"  {pnl_emoji} PROFIT/LOSS: {pnl_color}${pnl:,.2f} ({pnl_color}{pnl_pct:.2f}%)")
    print()
    
    # Get current prices
    print("  💰 CURRENT PRICES")
    print("  " + "-" * 50)
    prices = get_prices()
    for symbol, price in prices.items():
        coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
        print(f"  {coin:6s}: ${price:,.2f}")
    print()
    
    # Get open positions
    print("  📍 OPEN POSITIONS")
    print("  " + "-" * 50)
    
    has_positions = False
    for symbol in SYMBOLS:
        r = send_get("/capi/v2/account/accounts", f"?symbol={symbol}")
        data = safe_json(r)
        
        if "position" in data and len(data["position"]) > 0:
            for pos in data["position"]:
                size = float(pos.get("size", 0))
                if size > 0:
                    has_positions = True
                    direction = pos.get("direction", "")
                    entry = float(pos.get("avg_price", 0))
                    unrealized = pos.get("unrealizePnl", "0")
                    leverage = pos.get("leverage", "?")
                    
                    coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
                    current_price = prices.get(symbol, 0)
                    pnl_emoji = "🟢" if float(unrealized) >= 0 else "🔴"
                    
                    print(f"  {coin}:")
                    print(f"    Direction: {'🟢 LONG' if direction == 'long' else '🔴 SHORT'}")
                    print(f"    Size: {size} | Leverage: {leverage}x")
                    print(f"    Entry: ${entry:,.2f} | Current: ${current_price:,.2f}")
                    print(f"    Unrealized P&L: {pnl_emoji} {unrealized} USDT")
                    print()
    
    if not has_positions:
        print("  No open positions")
    
    print()
    print("=" * 70)
    print(f"  🎯 Target: Top 2 in group by Feb 2, 2026")
    print("=" * 70)

if __name__ == "__main__":
    main()
