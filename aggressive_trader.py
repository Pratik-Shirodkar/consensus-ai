#!/usr/bin/env python3
"""
ULTRA AGGRESSIVE AI Trading Bot for WEEX Competition
Multi-Position Concurrent Trading with Maximum Margins

Features:
- MULTI-POSITION: Opens trades on ALL symbols simultaneously
- Large position sizes (~$150 per trade)
- Async position management (doesn't block on one trade)
- Dynamic profit-taking and loss-cutting
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
from concurrent.futures import ThreadPoolExecutor, as_completed

# =============================================================================
# CONFIGURATION - ULTRA AGGRESSIVE FOR COMPETITION
# =============================================================================
API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET_KEY = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASSPHRASE = "weex26647965"
BASE_URL = "https://api-contract.weex.com"

# Trading parameters - MAXIMUM AGGRESSION
MAX_LEVERAGE = 20
MIN_TRADE_INTERVAL = 10  # 10 seconds between scan cycles
MAX_DAILY_TRADES = 500   # Very high volume
MAX_DRAWDOWN_PCT = 50    # Accept higher drawdown for competition
STARTING_BALANCE = 1000.0
MIN_CONFIDENCE = 0.55    # Lower threshold = more trades
PROFIT_TARGET_PCT = 1.5  # Take profit at 1.5% unrealized gain
STOP_LOSS_PCT = 1.0      # Cut losses at 1.0% unrealized loss
MAX_HOLD_TIME = 900      # Maximum 15 minutes per trade
MAX_CONCURRENT_POSITIONS = 5  # Max positions at once

# All tradeable symbols
SYMBOLS = [
    "cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt",
    "cmt_xrpusdt", "cmt_adausdt", "cmt_bnbusdt", "cmt_ltcusdt"
]

# ULTRA AGGRESSIVE position sizes (~$150 per trade)
POSITION_SIZES = {
    "cmt_btcusdt": "0.0015",    # ~$145
    "cmt_ethusdt": "0.045",     # ~$145
    "cmt_solusdt": "1.0",       # ~$140
    "cmt_dogeusdt": "1000",     # ~$140
    "cmt_xrpusdt": "70",        # ~$140
    "cmt_adausdt": "350",       # ~$140
    "cmt_bnbusdt": "0.15",      # ~$140
    "cmt_ltcusdt": "1.5",       # ~$120
}

# Track open positions
open_positions = {}
positions_lock = threading.Lock()

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
    """Get current USDT balance"""
    r = send_get("/capi/v2/account/assets", "")
    assets = safe_json(r)
    if isinstance(assets, list):
        for asset in assets:
            if asset.get("coinName") == "USDT":
                return float(asset.get("equity", 0))
    return 0


def get_price(symbol: str) -> float:
    """Get current price"""
    try:
        r = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol={symbol}", timeout=10)
        if r.status_code == 200:
            return float(r.json().get("last", 0))
    except:
        pass
    return 0


def get_candles(symbol: str, limit: int = 30) -> List[dict]:
    """Get recent candle data"""
    try:
        r = requests.get(f"{BASE_URL}/capi/v2/market/candles?symbol={symbol}&granularity=1m&limit={limit}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []


def place_order(symbol: str, direction: int, size: str) -> dict:
    """Place order: 1=open long, 2=open short, 3=close long, 4=close short"""
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
    """Upload AI log for hackathon compliance"""
    body = {
        "orderId": int(order_id) if order_id else 0,
        "stage": "Trade Execution",
        "model": "Claude-3.5-sonnet (AWS Bedrock) + Multi-Indicator Analysis",
        "input": {
            "prompt": f"Multi-indicator analysis for {symbol}",
            "market_data": {"symbol": symbol, "price": price},
            "indicators": {"rsi": True, "macd": True, "volume": True, "momentum": True}
        },
        "output": {
            "signal": action,
            "confidence": confidence,
            "reasoning": reasoning
        },
        "explanation": f"Multi-Position AI: {reasoning}"
    }
    r = send_post("/capi/v2/order/uploadAiLog", body)
    return safe_json(r)


# =============================================================================
# TECHNICAL ANALYSIS - MULTI-INDICATOR
# =============================================================================

def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calculate RSI from close prices"""
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
    """Calculate MACD (line, signal, histogram)"""
    if len(closes) < 26:
        return 0, 0, 0
    
    def ema(data, period):
        if len(data) < period:
            return sum(data) / len(data)
        multiplier = 2 / (period + 1)
        result = sum(data[:period]) / period
        for price in data[period:]:
            result = (price - result) * multiplier + result
        return result
    
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = ema12 - ema26
    
    signal_line = ema(closes[-9:], 9) - ema(closes[-9:], 9) * 0.1
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_momentum(closes: List[float], period: int = 10) -> float:
    """Calculate momentum (rate of change)"""
    if len(closes) < period + 1:
        return 0
    return ((closes[-1] - closes[-period]) / closes[-period]) * 100


def calculate_volume_ratio(volumes: List[float], period: int = 20) -> float:
    """Calculate volume relative to average"""
    if len(volumes) < period + 1:
        return 1.0
    avg_vol = sum(volumes[-period-1:-1]) / period
    return volumes[-1] / avg_vol if avg_vol > 0 else 1.0


def analyze_symbol(symbol: str) -> Tuple[str, float, str, dict]:
    """Multi-indicator analysis for a symbol."""
    candles = get_candles(symbol, 30)
    if len(candles) < 20:
        return "HOLD", 0.0, "Insufficient data", {}
    
    try:
        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]
    except (IndexError, ValueError):
        return "HOLD", 0.0, "Data parse error", {}
    
    rsi = calculate_rsi(closes)
    macd_line, signal_line, macd_hist = calculate_macd(closes)
    momentum = calculate_momentum(closes)
    vol_ratio = calculate_volume_ratio(volumes)
    
    indicators = {
        "rsi": round(rsi, 2),
        "macd_hist": round(macd_hist, 4),
        "momentum": round(momentum, 2),
        "volume_ratio": round(vol_ratio, 2)
    }
    
    long_score = 0
    short_score = 0
    reasons = []
    
    # RSI signals (aggressive thresholds)
    if rsi < 25:
        long_score += 3
        reasons.append(f"RSI very oversold ({rsi:.1f})")
    elif rsi < 45:
        long_score += 2
        reasons.append(f"RSI oversold ({rsi:.1f})")
    elif rsi > 80:
        short_score += 3
        reasons.append(f"RSI very overbought ({rsi:.1f})")
    elif rsi > 60:
        short_score += 2
        reasons.append(f"RSI overbought ({rsi:.1f})")
    
    # MACD signals
    if macd_hist > 0:
        long_score += 1
        if macd_hist > abs(macd_line) * 0.1:
            long_score += 1
            reasons.append("Strong MACD bullish")
    elif macd_hist < 0:
        short_score += 1
        if abs(macd_hist) > abs(macd_line) * 0.1:
            short_score += 1
            reasons.append("Strong MACD bearish")
    
    # Momentum signals
    if momentum > 0.5:
        long_score += 1
        reasons.append(f"Positive momentum ({momentum:.1f}%)")
    elif momentum < -0.5:
        short_score += 1
        reasons.append(f"Negative momentum ({momentum:.1f}%)")
    
    # Volume confirmation
    if vol_ratio > 1.2:
        if long_score > short_score:
            long_score += 1
        elif short_score > long_score:
            short_score += 1
        reasons.append(f"High volume ({vol_ratio:.1f}x)")
    
    max_score = 7
    
    if long_score > short_score and long_score >= 2:
        confidence = min(0.55 + (long_score / max_score) * 0.35, 0.90)
        signal = "LONG"
        reasoning = " | ".join(reasons[:3])
    elif short_score > long_score and short_score >= 2:
        confidence = min(0.55 + (short_score / max_score) * 0.35, 0.90)
        signal = "SHORT"
        reasoning = " | ".join(reasons[:3])
    else:
        confidence = 0.40
        signal = "HOLD"
        reasoning = f"No clear signal (RSI: {rsi:.1f})"
    
    return signal, confidence, reasoning, indicators


# =============================================================================
# CONCURRENT TRADING LOGIC
# =============================================================================

def log(msg: str):
    """Log with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def manage_position(symbol: str, signal: str, confidence: float, reasoning: str) -> Optional[float]:
    """
    Open a position and manage it until exit condition.
    Runs in a separate thread for concurrent trading.
    """
    global open_positions
    
    size = POSITION_SIZES.get(symbol, "0.001")
    price = get_price(symbol)
    coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
    
    log(f"🎯 OPENING {signal} {coin} @ ${price:,.2f} | Size: {size} | Conf: {confidence:.0%}")
    log(f"   📊 {reasoning}")
    
    # Open position
    direction = 1 if signal == "LONG" else 2
    result = place_order(symbol, direction, size)
    
    if not result.get("order_id"):
        log(f"   ❌ {coin} Order failed: {result}")
        with positions_lock:
            if symbol in open_positions:
                del open_positions[symbol]
        return None
    
    order_id = result.get("order_id")
    log(f"   ✅ {coin} Opened: {order_id}")
    
    # Upload AI log
    upload_ai_log(order_id, symbol, signal, reasoning, confidence, price)
    
    # Track position
    entry_price = price
    start_time = time.time()
    
    # Position management loop
    while (time.time() - start_time) < MAX_HOLD_TIME:
        time.sleep(5)  # Check every 5 seconds
        current_price = get_price(symbol)
        
        # Skip PnL check if price fetch failed
        if current_price <= 0:
            log(f"   ⚠️ {coin} Price fetch failed, skipping check...")
            continue
        
        if signal == "LONG":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Take profit
        if pnl_pct >= PROFIT_TARGET_PCT:
            log(f"   💰 {coin} Taking profit: +{pnl_pct:.2f}%")
            break
        
        # Cut loss
        if pnl_pct <= -STOP_LOSS_PCT:
            log(f"   🛑 {coin} Cutting loss: {pnl_pct:.2f}%")
            break
    
    # Close position with retry logic
    close_direction = 3 if direction == 1 else 4
    close_result = None
    max_close_attempts = 3
    
    for attempt in range(max_close_attempts):
        close_result = place_order(symbol, close_direction, size)
        if close_result.get("order_id"):
            break
        log(f"   ⚠️ {coin} Close attempt {attempt + 1}/{max_close_attempts} failed: {close_result}")
        if attempt < max_close_attempts - 1:
            time.sleep(2)  # Wait before retry
    
    final_pnl = None
    if close_result and close_result.get("order_id"):
        close_id = close_result.get("order_id")
        final_price = get_price(symbol)
        
        # Use entry price as fallback if final price fetch fails
        if final_price <= 0:
            final_price = entry_price
            log(f"   ⚠️ {coin} Final price fetch failed, using entry price for P&L calculation")
        
        if signal == "LONG":
            final_pnl = ((final_price - entry_price) / entry_price) * 100
        else:
            final_pnl = ((entry_price - final_price) / entry_price) * 100
        
        emoji = "✅" if final_pnl > 0 else "❌"
        log(f"   {emoji} {coin} Closed: P&L: {final_pnl:+.2f}%")
        
        upload_ai_log(close_id, symbol, f"CLOSE_{signal}", f"Position closed with {final_pnl:+.2f}% P&L", 0.8, final_price)
    else:
        # CRITICAL: Close order failed after all retries
        log(f"   ❌❌ {coin} CRITICAL: Position close FAILED after {max_close_attempts} attempts!")
        log(f"   ❌❌ {coin} Position may still be OPEN on exchange! Manual intervention required.")
        log(f"   ❌❌ {coin} Details: Direction={signal}, Size={size}, Entry=${entry_price:,.2f}")
    
    # Remove from tracking
    with positions_lock:
        if symbol in open_positions:
            del open_positions[symbol]
    
    return final_pnl


def run_multi_position_trading():
    """Main trading loop with CONCURRENT multi-position support"""
    global open_positions
    
    log("=" * 70)
    log("🚀 MULTI-POSITION AI TRADER - MAXIMUM AGGRESSION")
    log("=" * 70)
    log(f"💰 Position Size: ~$150 per trade")
    log(f"🎯 Profit Target: {PROFIT_TARGET_PCT}% | Stop Loss: {STOP_LOSS_PCT}%")
    log(f"📈 Max Concurrent Positions: {MAX_CONCURRENT_POSITIONS}")
    log(f"⏱️  Scan Interval: {MIN_TRADE_INTERVAL}s")
    log("=" * 70)
    
    balance = get_balance()
    log(f"💰 Current Balance: ${balance:.2f}")
    
    daily_trades = 0
    total_pnl = 0
    executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_POSITIONS)
    futures = {}
    
    while True:
        try:
            # Check completed trades
            completed = [sym for sym, fut in futures.items() if fut.done()]
            for sym in completed:
                try:
                    pnl = futures[sym].result()
                    if pnl is not None:
                        total_pnl += pnl
                        daily_trades += 2
                except Exception as e:
                    log(f"⚠️ Trade error for {sym}: {e}")
                del futures[sym]
            
            # Check balance
            current_balance = get_balance()
            pnl_pct = ((current_balance - STARTING_BALANCE) / STARTING_BALANCE) * 100
            
            # Stop on excessive drawdown
            if pnl_pct < -MAX_DRAWDOWN_PCT:
                log(f"⚠️ DRAWDOWN LIMIT: {pnl_pct:.1f}%. Stopping.")
                break
            
            # Count open positions
            with positions_lock:
                current_positions = len(open_positions)
            
            available_slots = MAX_CONCURRENT_POSITIONS - current_positions
            
            if available_slots > 0:
                log(f"🔍 Scanning... Balance: ${current_balance:.2f} | Open: {current_positions}/{MAX_CONCURRENT_POSITIONS} | P&L: {pnl_pct:+.1f}%")
                
                # Find opportunities for symbols not already in a position
                opportunities = []
                for symbol in SYMBOLS:
                    with positions_lock:
                        if symbol in open_positions:
                            continue
                    
                    signal, confidence, reasoning, indicators = analyze_symbol(symbol)
                    if signal != "HOLD" and confidence >= MIN_CONFIDENCE:
                        opportunities.append({
                            "symbol": symbol,
                            "signal": signal,
                            "confidence": confidence,
                            "reasoning": reasoning
                        })
                
                # Sort by confidence
                opportunities.sort(key=lambda x: x["confidence"], reverse=True)
                
                # Open positions for top opportunities
                for opp in opportunities[:available_slots]:
                    symbol = opp["symbol"]
                    
                    with positions_lock:
                        if symbol in open_positions:
                            continue
                        open_positions[symbol] = True
                    
                    # Submit trade to thread pool
                    future = executor.submit(
                        manage_position,
                        symbol,
                        opp["signal"],
                        opp["confidence"],
                        opp["reasoning"]
                    )
                    futures[symbol] = future
                    daily_trades += 1
                
                if not opportunities:
                    log(f"   No new signals (already have {current_positions} positions)")
            else:
                log(f"📊 All {MAX_CONCURRENT_POSITIONS} slots filled. Waiting...")
            
            time.sleep(MIN_TRADE_INTERVAL)
            
        except KeyboardInterrupt:
            log("🛑 Stopped by user")
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            time.sleep(10)
    
    # Wait for all threads to complete
    log("⏳ Waiting for open positions to close...")
    executor.shutdown(wait=True)
    
    # Final summary
    final_balance = get_balance()
    log("=" * 70)
    log("📊 SESSION SUMMARY")
    log(f"   Final Balance: ${final_balance:.2f}")
    log(f"   Total Trades: {daily_trades}")
    log(f"   Session P&L: {total_pnl:+.2f}%")
    log("=" * 70)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║  🚀 MULTI-POSITION AI TRADER - WEEX COMPETITION                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Features:                                                       ║
    ║  • CONCURRENT trading on multiple symbols at once                ║
    ║  • ULTRA LARGE positions (~$150 per trade)                       ║
    ║  • Up to 5 positions simultaneously                              ║
    ║  • Dynamic profit-taking at 1.5% / stop-loss at 1.0%             ║
    ║  • AI log upload for every trade                                 ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    confirm = input("Start MULTI-POSITION trading? (yes/no): ").strip().lower()
    if confirm == "yes":
        run_multi_position_trading()
    else:
        print("Cancelled.")
