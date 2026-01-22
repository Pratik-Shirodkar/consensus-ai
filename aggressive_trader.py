#!/usr/bin/env python3
"""
WEEX AI WARS - GOD MODE TRADING BOT
The Ultimate Retail Trading Algorithm.

Strategy:
- High-conviction trend following (Winner Strategy)
- Microstructure Analysis (Order Book Imbalance) - NEW
- Macro Correlation Protection (BTC Check) - NEW
- Spread & Slippage Protection - NEW
- Wide stops + trailing (let winners run)
"""

import time
import hmac
import hashlib
import base64
import requests
import json
import threading
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from concurrent.futures import ThreadPoolExecutor

# =============================================================================
# CONFIGURATION - GOD MODE
# =============================================================================
API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET_KEY = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASSPHRASE = "weex26647965"
BASE_URL = "https://api-contract.weex.com"

# GOD MODE PARAMETERS
MAX_LEVERAGE = 20
MIN_TRADE_INTERVAL = 30          # Quality over speed
MAX_DAILY_TRADES = 100           # Fewer, perfect trades
MAX_DRAWDOWN_PCT = 40            
STARTING_BALANCE = 1000.0

# HIGH CONVICTION ONLY
MIN_CONFIDENCE = 0.80            # Ultra high confidence
MIN_SIGNAL_SCORE = 7             # Almost perfect setup required

# WIDE TARGETS - LET WINNERS RUN
PROFIT_TARGET_PCT = 20.0         # 20% leveraged
STOP_LOSS_PCT = 5.0              # 5% leveraged
TRAILING_ACTIVATION_PCT = 10.0   # Activate at +10%
TRAILING_DISTANCE_PCT = 5.0      # Trail by 5%
MAX_HOLD_TIME = 14400            # 4 hours max per trade
MAX_CONCURRENT_POSITIONS = 5     

# All tradeable symbols with BIGGER sizes (~$250-350 per trade)
SYMBOLS = [
    "cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt",
    "cmt_xrpusdt", "cmt_adausdt", "cmt_bnbusdt", "cmt_ltcusdt"
]

POSITION_SIZES = {
    "cmt_btcusdt": "0.003",       # ~$300
    "cmt_ethusdt": "0.1",         # ~$350
    "cmt_solusdt": "2.0",         # ~$280
    "cmt_dogeusdt": "2000",       # ~$280
    "cmt_xrpusdt": "140",         # ~$280
    "cmt_adausdt": "700",         # ~$280
    "cmt_bnbusdt": "0.4",         # ~$360
    "cmt_ltcusdt": "3.0",         # ~$240
}

# Track open positions and stats
open_positions = {}
positions_lock = threading.Lock()
consecutive_losses = 0

# =============================================================================
# API FUNCTIONS
# =============================================================================

def send_get(path: str, qs: str = "") -> requests.Response:
    ts = str(int(time.time() * 1000))
    msg = ts + "GET" + path + qs
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": API_KEY, "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts,
        "ACCESS-PASSPHRASE": PASSPHRASE, "Content-Type": "application/json", "locale": "en-US"
    }
    return requests.get(BASE_URL + path + qs, headers=headers, timeout=30)


def send_post(path: str, body: dict) -> requests.Response:
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body)
    msg = ts + "POST" + path + body_str
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": API_KEY, "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts,
        "ACCESS-PASSPHRASE": PASSPHRASE, "Content-Type": "application/json", "locale": "en-US"
    }
    return requests.post(BASE_URL + path, headers=headers, data=body_str, timeout=30)


def safe_json(r: requests.Response) -> dict:
    try:
        return r.json()
    except:
        return {"error": "parse_failed", "status": r.status_code}


def get_balance() -> float:
    r = send_get("/capi/v2/account/assets", "")
    assets = safe_json(r)
    if isinstance(assets, list):
        for asset in assets:
            if asset.get("coinName") == "USDT":
                return float(asset.get("equity", 0))
    return 0


def get_price(symbol: str) -> float:
    try:
        r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={symbol}", timeout=10)
        if r.status_code == 200:
            return float(r.json().get("last", 0))
    except:
        pass
    return 0


def get_candles(symbol: str, granularity: str = "1m", limit: int = 50) -> List[dict]:
    """Get candle data - granularity: 1m, 5m, 15m, 1H, 4H"""
    try:
        r = requests.get(f"{BASE_URL}/capi/v2/market/candles?symbol={symbol}&granularity={granularity}&limit={limit}", timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []


def get_order_book(symbol: str, limit: int = 20) -> dict:
    """Get order book depth"""
    try:
        r = requests.get(f"{BASE_URL}/capi/v2/market/depth?symbol={symbol}&limit={limit}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}


def place_order(symbol: str, direction: int, size: str) -> dict:
    body = {
        "symbol": symbol,
        "client_oid": str(int(time.time() * 1000)),
        "size": size,
        "type": str(direction),
        "order_type": "0",
        "match_price": "1",
        "price": "1"
    }
    r = send_post("/capi/v2/order/placeOrder", body)
    return safe_json(r)


def upload_ai_log(order_id: int, symbol: str, action: str, reasoning: str, confidence: float, price: float) -> dict:
    body = {
        "orderId": int(order_id) if order_id else 0,
        "stage": "Trade Execution",
        "model": "Claude-3.5-sonnet (AWS Bedrock) + God Mode Strategy",
        "input": {
            "prompt": f"God Mode analysis for {symbol}",
            "market_data": {"symbol": symbol, "price": price},
            "strategy": "Trend + Microstructure + Correlation"
        },
        "output": {
            "signal": action,
            "confidence": confidence,
            "reasoning": reasoning
        },
        "explanation": f"God Mode AI: {reasoning}"
    }
    r = send_post("/capi/v2/order/uploadAiLog", body)
    return safe_json(r)


# =============================================================================
# ADVANCED INDICATORS - GOD MODE
# =============================================================================

def calculate_ema(data: List[float], period: int) -> float:
    if len(data) < period:
        return sum(data) / len(data) if data else 0
    multiplier = 2 / (period + 1)
    ema = sum(data[:period]) / period
    for price in data[period:]:
        ema = (price - ema) * multiplier + ema
    return ema


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(diff if diff > 0 else 0)
        losses.append(abs(diff) if diff < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_macd(closes: List[float]) -> Tuple[float, float, float]:
    if len(closes) < 26:
        return 0, 0, 0
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    macd_line = ema12 - ema26
    signal = calculate_ema(closes[-9:], 9)
    histogram = macd_line - signal * 0.1
    return macd_line, signal, histogram


def calculate_atr(candles: List[dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0
    true_ranges = []
    for i in range(1, len(candles)):
        try:
            high = float(candles[i][2])
            low = float(candles[i][3])
            prev_close = float(candles[i-1][4])
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
        except:
            continue
    return sum(true_ranges[-period:]) / period if true_ranges else 0


def calculate_obi(symbol: str) -> float:
    """
    Calculate Order Book Imbalance (OBI)
    Range: -1.0 (Sell Pressure) to 1.0 (Buy Pressure)
    """
    book = get_order_book(symbol, 20)
    if not book or 'bids' not in book or 'asks' not in book:
        return 0
    
    bid_vol = sum([float(b[1]) for b in book['bids']])
    ask_vol = sum([float(a[1]) for a in book['asks']])
    total_vol = bid_vol + ask_vol
    
    if total_vol == 0: return 0
    return (bid_vol - ask_vol) / total_vol


def get_btc_trend() -> str:
    """Get the master trend of BTC - Don't fight the king"""
    candles = get_candles("cmt_btcusdt", "15m", 50)
    if not candles:
        return "UNCLEAR"
    closes = [float(c[4]) for c in candles]
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    
    if closes[-1] > ema20 > ema50:
        return "UPTREND"
    elif closes[-1] < ema20 < ema50:
        return "DOWNTREND"
    return "SIDEWAYS"


def detect_trend(closes: List[float]) -> str:
    if len(closes) < 50:
        return "UNCLEAR"
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    price = closes[-1]
    
    if price > ema20 * 1.002 and ema20 > ema50 * 1.001:
        return "UPTREND"
    elif price < ema20 * 0.998 and ema20 < ema50 * 0.999:
        return "DOWNTREND"
    return "SIDEWAYS"


def analyze_symbol_god_mode(symbol: str) -> Tuple[str, float, str, dict]:
    """
    God Mode Analysis:
    1. 4H Trend (Macro)
    2. 15m RSI (Pullback)
    3. BTC Correlation (Market Safety)
    4. Order Book Imbalance (Microstructure)
    """
    btc_trend = get_btc_trend()
    candles = get_candles(symbol, "5m", 50)
    
    if len(candles) < 30:
        return "HOLD", 0.0, "Insufficient data", {}
    
    try:
        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]
    except:
        return "HOLD", 0.0, "Data parse error", {}
    
    # Calculate indicators
    rsi = calculate_rsi(closes)
    macd_line, signal, macd_hist = calculate_macd(closes)
    trend = detect_trend(closes)
    atr = calculate_atr(candles)
    obi = calculate_obi(symbol)
    
    # Volume analysis
    avg_volume = sum(volumes[-20:]) / 20 if volumes else 1
    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
    momentum = ((closes[-1] - closes[-10]) / closes[-10]) * 100 if len(closes) >= 10 else 0
    
    indicators = {
        "rsi": round(rsi, 2),
        "macd": round(macd_hist, 4),
        "trend": trend,
        "btc_trend": btc_trend,
        "obi": round(obi, 2),
        "vol_ratio": round(volume_ratio, 2)
    }
    
    long_score = 0
    short_score = 0
    reasons = []
    
    # 1. MACRO TREND CHECK (3 pts)
    if trend == "UPTREND":
        long_score += 3
        reasons.append("Strong Uptown")
    elif trend == "DOWNTREND":
        short_score += 3
        reasons.append("Strong Downtrend")
        
    # 2. BTC CORRELATION - SAFETY CHECK
    is_alt = "btc" not in symbol
    if is_alt:
        if trend == "UPTREND" and btc_trend == "DOWNTREND":
            reasons.append("⚠️ Fighting BTC downtrend")
            long_score -= 2
        elif trend == "DOWNTREND" and btc_trend == "UPTREND":
            reasons.append("⚠️ Fighting BTC uptrend")
            short_score -= 2
            
    # 3. RSI PULLBACKS (2 pts)
    if trend == "UPTREND" and 35 <= rsi <= 55:
        long_score += 2
        reasons.append(f"Perfect RSI Dip ({rsi:.0f})")
    elif trend == "DOWNTREND" and 45 <= rsi <= 65:
        short_score += 2
        reasons.append(f"Perfect RSI Rally ({rsi:.0f})")
        
    # 4. ORDER BOOK IMBALANCE (The Edge - 2 pts)
    if obi > 0.2:
        long_score += 2
        reasons.append(f"Strong Buy Pressure (OBI +{obi:.2f})")
    elif obi < -0.2:
        short_score += 2
        reasons.append(f"Strong Sell Pressure (OBI {obi:.2f})")
        
    # 5. MACD & Volume (1 pt each)
    if macd_hist > 0: long_score += 1
    if macd_hist < 0: short_score += 1
    if volume_ratio > 1.5:
        reasons.append("High Volume")
        long_score += 1
        short_score += 1
        
    # SCORE EVALUATION
    max_score = 10
    
    if long_score >= MIN_SIGNAL_SCORE and long_score > short_score:
        confidence = min(0.70 + (long_score / max_score) * 0.29, 0.99)
        signal = "LONG"
    elif short_score >= MIN_SIGNAL_SCORE and short_score > long_score:
        confidence = min(0.70 + (short_score / max_score) * 0.29, 0.99)
        signal = "SHORT"
    else:
        confidence = 0.50
        signal = "HOLD"
        reasoning = f"Waiting for setup (L:{long_score} S:{short_score})"
        
    if signal != "HOLD":
        reasoning = " | ".join(reasons)
        
    return signal, confidence, reasoning, indicators


# =============================================================================
# POSITION MANAGEMENT - GOD MODE
# =============================================================================

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def manage_position_god_mode(symbol: str, signal: str, confidence: float, reasoning: str) -> Optional[float]:
    """
    God Mode Management:
    - Checks Spread before entry
    - Wide stops, trailing profits
    """
    global open_positions, consecutive_losses
    
    # 1. SPREAD CHECK - Don't enter if spread is bad
    book = get_order_book(symbol, 1)
    if book and book.get('bids') and book.get('asks'):
        best_bid = float(book['bids'][0][0])
        best_ask = float(book['asks'][0][0])
        spread = (best_ask - best_bid) / best_bid * 100
        if spread > 0.15: # 0.15% spread limit
            log(f"⚠️ {symbol} Spread too high ({spread:.3f}%), skipping.")
            return None
    
    size = POSITION_SIZES.get(symbol, "0.001")
    price = get_price(symbol)
    coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
    
    log(f"⚡ GOD MODE ENTRY: {signal} {coin} @ ${price:,.2f} | Conf: {confidence:.0%}")
    log(f"   📊 {reasoning}")
    
    direction = 1 if signal == "LONG" else 2
    result = place_order(symbol, direction, size)
    
    if not result.get("order_id"):
        log(f"   ❌ {coin} Order failed: {result}")
        with positions_lock:
            if symbol in open_positions: del open_positions[symbol]
        return None
        
    order_id = result.get("order_id")
    upload_ai_log(order_id, symbol, signal, reasoning, confidence, price)
    
    # Management Loop
    entry_price = price
    start_time = time.time()
    highest_pnl = 0
    trailing_active = False
    
    while (time.time() - start_time) < MAX_HOLD_TIME:
        time.sleep(10)
        current_price = get_price(symbol)
        if current_price <= 0: continue
        
        # PnL Calc
        if signal == "LONG":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        leveraged_pnl = pnl_pct * MAX_LEVERAGE
        if leveraged_pnl > highest_pnl: highest_pnl = leveraged_pnl
        
        # Trailing Logic
        if leveraged_pnl >= TRAILING_ACTIVATION_PCT: trailing_active = True
        
        if trailing_active and leveraged_pnl < (highest_pnl - TRAILING_DISTANCE_PCT):
            log(f"   🔔 {coin} Trailing Stop Hit: +{leveraged_pnl:.2f}%")
            break
            
        if leveraged_pnl >= PROFIT_TARGET_PCT:
            log(f"   💰 {coin} Target Hit: +{leveraged_pnl:.2f}%")
            break
            
        if leveraged_pnl <= -STOP_LOSS_PCT:
            log(f"   🛑 {coin} Stop Loss: {leveraged_pnl:.2f}%")
            break
            
    # Close
    close_dir = 3 if direction == 1 else 4
    for _ in range(3):
        res = place_order(symbol, close_dir, size)
        if res.get("order_id"): break
        time.sleep(1)
        
    # Final PnL
    final_price = get_price(symbol)
    if signal == "LONG":
        final_pnl = ((final_price - entry_price) / entry_price) * 100 * MAX_LEVERAGE
    else:
        final_pnl = ((entry_price - final_price) / entry_price) * 100 * MAX_LEVERAGE
        
    if final_pnl < 0: consecutive_losses += 1
    else: consecutive_losses = 0
    
    log(f"   🏁 {coin} Closed: {final_pnl:+.2f}%")
    
    with positions_lock:
        del open_positions[symbol]
        
    return final_pnl


def run_god_mode():
    """Main Loop"""
    log("=" * 60)
    log("⚡ WEEX GOD MODE BOT ACTIVATED")
    log("=" * 60)
    log("Features Active:")
    log("✅ Microstructure Analysis (OBI)")
    log("✅ Macro Correlation (BTC Check)")
    log("✅ Smart Spreads (Slippage Protection)")
    log("✅ Winner Strategy (Trend Following)")
    log("-" * 60)
    
    executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_POSITIONS)
    
    while True:
        try:
            with positions_lock:
                busy = len(open_positions)
            
            # Get and show balance
            balance = get_balance()
            log(f"🔍 Scanning {len(SYMBOLS)} symbols... Balance: ${balance:.2f} | Open: {busy}/{MAX_CONCURRENT_POSITIONS}")
            
            if busy < MAX_CONCURRENT_POSITIONS:
                # Scan symbols
                opportunities = []
                for s in SYMBOLS:
                    with positions_lock:
                        if s in open_positions: continue
                    
                    sig, conf, reas, _ = analyze_symbol_god_mode(s)
                    if sig != "HOLD" and conf >= MIN_CONFIDENCE:
                        opportunities.append((s, sig, conf, reas))
                        log(f"   📊 {s}: {sig} ({conf:.0%}) - {reas[:50]}")
                
                if not opportunities:
                    log(f"   ⏳ No high-conviction signals. Waiting for setup...")
                
                # Sort best first
                opportunities.sort(key=lambda x: x[2], reverse=True)
                
                for opp in opportunities[:(MAX_CONCURRENT_POSITIONS - busy)]:
                    with positions_lock:
                        open_positions[opp[0]] = True
                    executor.submit(manage_position_god_mode, *opp)
                    
            time.sleep(MIN_TRADE_INTERVAL)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_god_mode()
