#!/usr/bin/env python3
"""Close ALL open positions on ALL symbols on WEEX"""
import time, hmac, hashlib, base64, requests, json

api_key = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
secret_key = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
access_passphrase = "weex26647965"
BASE_URL = "https://api-contract.weex.com"

# All tradeable symbols
SYMBOLS = [
    "cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt",
    "cmt_xrpusdt", "cmt_adausdt", "cmt_bnbusdt", "cmt_ltcusdt"
]

def generate_signature_get(timestamp, method, request_path, query_string):
    message = timestamp + method.upper() + request_path + query_string
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def send_get(path, query_string=""):
    ts = str(int(time.time() * 1000))
    sig = generate_signature_get(ts, "GET", path, query_string)
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": sig,
        "ACCESS-TIMESTAMP": ts,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    return requests.get(BASE_URL + path + query_string, headers=headers, timeout=30)

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

def get_all_positions():
    """Get ALL positions across all symbols"""
    print("=" * 60)
    print("📊 Getting ALL Positions...")
    print("=" * 60)
    
    all_positions = []
    
    for symbol in SYMBOLS:
        try:
            response = send_get("/capi/v2/account/position/singlePosition", f"?symbol={symbol}")
            data = response.json()
            
            # Handle list response
            if isinstance(data, list):
                for pos in data:
                    if float(pos.get("size", "0")) > 0:
                        pos["_symbol"] = symbol
                        all_positions.append(pos)
                        coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
                        print(f"  Found: {pos.get('side')} {coin} size={pos.get('size')}")
            
            # Handle dict response with data field
            elif isinstance(data, dict) and "data" in data:
                pos_data = data.get("data", {})
                if pos_data:
                    long_avail = float(pos_data.get("long_available", "0"))
                    short_avail = float(pos_data.get("short_available", "0"))
                    if long_avail > 0 or short_avail > 0:
                        pos_data["_symbol"] = symbol
                        all_positions.append(pos_data)
                        coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
                        print(f"  Found: {coin} long={long_avail} short={short_avail}")
                        
        except Exception as e:
            print(f"  Error checking {symbol}: {e}")
    
    return all_positions

def close_position(symbol, size, position_side):
    """
    Close a position
    type: 3 = Close Long, 4 = Close Short
    """
    close_type = "4" if position_side.upper() == "SHORT" else "3"
    coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
    
    body = {
        "symbol": symbol,
        "client_oid": str(int(time.time() * 1000)),
        "size": size,
        "type": close_type,
        "order_type": "0",
        "match_price": "1",
        "price": "100000"
    }
    
    print(f"\n🔄 Closing {position_side.upper()} {coin} position of size {size}...")
    
    response = send_post("/capi/v2/order/placeOrder", body)
    result = response.json()
    
    if result.get("order_id"):
        print(f"  ✅ Closed successfully: {result.get('order_id')}")
    else:
        print(f"  ❌ Failed: {result}")
    
    return response

def main():
    print("\n" + "=" * 70)
    print("🚨 CLOSING ALL POSITIONS ON ALL SYMBOLS")
    print("=" * 70 + "\n")
    
    # Get all positions
    positions = get_all_positions()
    
    if not positions:
        print("\n✅ No open positions found on any symbol!")
        return
    
    print(f"\n📈 Found {len(positions)} position(s) to close")
    print("=" * 60)
    
    positions_closed = 0
    
    for pos in positions:
        symbol = pos.get("_symbol", pos.get("symbol", ""))
        side = pos.get("side", "")
        size = pos.get("size", "0")
        
        # Handle different response formats
        if side:
            # Direct position format
            if float(size) > 0:
                close_position(symbol, size, side)
                positions_closed += 1
                time.sleep(0.5)
        else:
            # Long/short available format
            long_avail = pos.get("long_available", "0")
            short_avail = pos.get("short_available", "0")
            
            if float(long_avail) > 0:
                close_position(symbol, long_avail, "LONG")
                positions_closed += 1
                time.sleep(0.5)
            
            if float(short_avail) > 0:
                close_position(symbol, short_avail, "SHORT")
                positions_closed += 1
                time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"✅ Closed {positions_closed} position(s)!")
    print("=" * 60)
    
    # Verify
    print("\n🔍 Verifying all positions are closed...")
    time.sleep(2)
    remaining = get_all_positions()
    if not remaining:
        print("\n✅ All positions successfully closed!")
    else:
        print(f"\n⚠️ {len(remaining)} position(s) may still be open")

if __name__ == "__main__":
    main()
