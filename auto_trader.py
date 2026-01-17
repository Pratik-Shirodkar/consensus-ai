#!/usr/bin/env python3
"""
WEEX Automated Trading Script for AI Wars Hackathon
Executes the required minimum 10 trades with safe parameters.

Features:
- Small position sizes (~$15-20 USDT each)
- Safe leverage (10x)
- Automated open/close cycles
- Trade logging
"""

import time
import hmac
import hashlib
import base64
import requests
import json
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET_KEY = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASSPHRASE = "weex26647965"
BASE_URL = "https://api-contract.weex.com"
SYMBOL = "cmt_btcusdt"

# Trading parameters
LEVERAGE = 10  # Safe leverage (max allowed is 20)
POSITION_SIZE = "0.0002"  # ~$17 USDT per trade at current prices
NUM_TRADE_CYCLES = 5  # Each cycle = 1 open + 1 close = 2 trades, so 5 cycles = 10 trades
DELAY_BETWEEN_TRADES = 5  # Seconds between trades

# =============================================================================
# API FUNCTIONS
# =============================================================================

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


def get_btc_price():
    """Get current BTC price"""
    r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={SYMBOL}", timeout=30)
    if r.status_code == 200:
        return float(r.json().get("last", 0))
    return 0


def set_leverage(leverage):
    """Set account leverage"""
    body = {"symbol": SYMBOL, "leverage": str(leverage), "side": "1"}
    r = send_post("/capi/v2/account/changeLeverage", body)
    return r.status_code == 200


def open_long(size):
    """Open a long position"""
    body = {
        "symbol": SYMBOL,
        "client_oid": str(int(time.time() * 1000)),
        "size": size,
        "type": "1",  # 1 = Open Long
        "order_type": "0",
        "match_price": "1",  # Market order
        "price": "80000"
    }
    r = send_post("/capi/v2/order/placeOrder", body)
    return r.status_code == 200, r.json()


def close_long(size):
    """Close a long position"""
    body = {
        "symbol": SYMBOL,
        "client_oid": str(int(time.time() * 1000)),
        "size": size,
        "type": "3",  # 3 = Close Long
        "order_type": "0",
        "match_price": "1",  # Market order
        "price": "80000"
    }
    r = send_post("/capi/v2/order/placeOrder", body)
    return r.status_code == 200, r.json()


def open_short(size):
    """Open a short position"""
    body = {
        "symbol": SYMBOL,
        "client_oid": str(int(time.time() * 1000)),
        "size": size,
        "type": "2",  # 2 = Open Short
        "order_type": "0",
        "match_price": "1",  # Market order
        "price": "80000"
    }
    r = send_post("/capi/v2/order/placeOrder", body)
    return r.status_code == 200, r.json()


def close_short(size):
    """Close a short position"""
    body = {
        "symbol": SYMBOL,
        "client_oid": str(int(time.time() * 1000)),
        "size": size,
        "type": "4",  # 4 = Close Short
        "order_type": "0",
        "match_price": "1",  # Market order
        "price": "80000"
    }
    r = send_post("/capi/v2/order/placeOrder", body)
    return r.status_code == 200, r.json()


def get_trade_history():
    """Get trade history"""
    r = send_get("/capi/v2/order/historyOrders", f"?symbol={SYMBOL}&pageSize=20&pageNo=1")
    return r.json() if r.status_code == 200 else {}


# =============================================================================
# MAIN TRADING LOGIC
# =============================================================================

def run_automated_trading():
    print("=" * 70)
    print("WEEX AUTOMATED TRADING - AI Wars Hackathon")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {NUM_TRADE_CYCLES} cycles = {NUM_TRADE_CYCLES * 2} trades")
    print(f"Position Size: {POSITION_SIZE} BTC per trade")
    print(f"Leverage: {LEVERAGE}x")
    print()
    
    # Get initial price
    btc_price = get_btc_price()
    print(f"Current BTC Price: ${btc_price:,.2f}")
    trade_value = float(POSITION_SIZE) * btc_price
    print(f"Estimated Trade Value: ${trade_value:.2f} USDT per trade")
    print()
    
    # Set leverage
    print("Setting leverage to 10x...")
    set_leverage(LEVERAGE)
    print()
    
    trade_log = []
    total_trades = 0
    
    for cycle in range(1, NUM_TRADE_CYCLES + 1):
        print(f"\n{'='*50}")
        print(f"CYCLE {cycle}/{NUM_TRADE_CYCLES}")
        print(f"{'='*50}")
        
        # --- Trade 1: Open Long ---
        print(f"\n[Trade {total_trades + 1}] Opening LONG position...")
        success, result = open_long(POSITION_SIZE)
        if success:
            order_id = result.get("order_id", "N/A")
            print(f"  ✅ Order placed: {order_id}")
            trade_log.append({
                "trade_num": total_trades + 1,
                "type": "OPEN_LONG",
                "size": POSITION_SIZE,
                "order_id": order_id,
                "timestamp": datetime.now().isoformat()
            })
            total_trades += 1
        else:
            print(f"  ❌ Failed: {result}")
        
        time.sleep(DELAY_BETWEEN_TRADES)
        
        # --- Trade 2: Close Long ---
        print(f"\n[Trade {total_trades + 1}] Closing LONG position...")
        success, result = close_long(POSITION_SIZE)
        if success:
            order_id = result.get("order_id", "N/A")
            print(f"  ✅ Order placed: {order_id}")
            trade_log.append({
                "trade_num": total_trades + 1,
                "type": "CLOSE_LONG",
                "size": POSITION_SIZE,
                "order_id": order_id,
                "timestamp": datetime.now().isoformat()
            })
            total_trades += 1
        else:
            print(f"  ❌ Failed: {result}")
        
        time.sleep(DELAY_BETWEEN_TRADES)
        
        print(f"\n  Cycle {cycle} complete. Total trades: {total_trades}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TRADING COMPLETE!")
    print("=" * 70)
    print(f"Total Trades Executed: {total_trades}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("Trade Log:")
    print("-" * 50)
    for trade in trade_log:
        print(f"  #{trade['trade_num']}: {trade['type']} | {trade['size']} BTC | Order: {trade['order_id']}")
    
    # Save trade log to file
    with open("trade_log.json", "w") as f:
        json.dump(trade_log, f, indent=2)
    print("\nTrade log saved to: trade_log.json")
    
    return total_trades


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║       AI Wars: WEEX Alpha Awakens - Automated Trading           ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  This script will execute 10 trades to meet hackathon rules.    ║
    ║  - 5 Long positions opened and closed                           ║
    ║  - Safe leverage (10x)                                          ║
    ║  - Small position sizes (~$17 USDT each)                        ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    confirm = input("Start automated trading? (yes/no): ").strip().lower()
    if confirm == "yes":
        trades = run_automated_trading()
        print(f"\n✅ Successfully executed {trades} trades!")
        if trades >= 10:
            print("🎉 You have met the minimum 10-trade requirement!")
    else:
        print("Cancelled.")
