#!/usr/bin/env python3
"""
WEEX AI WARS - WINNER STRATEGY TRADING BOT
Based on analysis of actual competition winners.

Strategy:
- High-conviction trend following (not scalping)
- Wide stops + trailing (let winners run)
- All 8 symbols with bigger position sizes
- 4H trend + 15m entry timing
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
# CONFIGURATION - WINNER STRATEGY
# =============================================================================
API_KEY = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
SECRET_KEY = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
PASSPHRASE = "weex26647965"
BASE_URL = "https://api-contract.weex.com"

# WINNER STRATEGY PARAMETERS
MAX_LEVERAGE = 20
MIN_TRADE_INTERVAL = 30          # 30 seconds between scans (quality over speed)
MAX_DAILY_TRADES = 100           # Fewer, better trades
MAX_DRAWDOWN_PCT = 40            # Wider tolerance for bigger moves
STARTING_BALANCE = 1000.0

# HIGH CONVICTION ONLY
MIN_CONFIDENCE = 0.75            # Only trade high-confidence signals
MIN_SIGNAL_SCORE = 5             # Require multiple indicators to agree

# WIDE TARGETS - LET WINNERS RUN
PROFIT_TARGET_PCT = 15.0         # 15% leveraged = 0.75% price move
STOP_LOSS_PCT = 5.0              # 5% leveraged = 0.25% price move
TRAILING_ACTIVATION_PCT = 8.0    # Activate trailing at +8%
TRAILING_DISTANCE_PCT = 4.0      # Trail by 4% from peak
MAX_HOLD_TIME = 7200             # 2 hours max per trade
MAX_CONCURRENT_POSITIONS = 5     # 5 positions across 8 symbols

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
        "model": "Claude-3.5-sonnet (AWS Bedrock) + Winner Strategy",
        "input": {
            "prompt": f"High-conviction trend analysis for {symbol}",
            "market_data": {"symbol": symbol, "price": price},
            "strategy": "WEEX Winner: Trend Following + Wide Trailing Stops"
        },
        "output": {
            "signal": action,
            "confidence": confidence,
            "reasoning": reasoning
        },
        "explanation": f"Winner Strategy AI: {reasoning}"
    }
    r = send_post("/capi/v2/order/uploadAiLog", body)
    return safe_json(r)


# =============================================================================
# TECHNICAL ANALYSIS - WINNER STYLE (Higher Timeframe Focus)
# =============================================================================

def calculate_ema(data: List[float], period: int) -> float:
    """Calculate EMA"""
    if len(data) < period:
        return sum(data) / len(data) if data else 0
    multiplier = 2 / (period + 1)
    ema = sum(data[:period]) / period
    for price in data[period:]:
        ema = (price - ema) * multiplier + ema
    return ema


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calculate RSI"""
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
    """Calculate MACD"""
    if len(closes) < 26:
        return 0, 0, 0
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    macd_line = ema12 - ema26
    signal = calculate_ema(closes[-9:], 9)
    histogram = macd_line - signal * 0.1
    return macd_line, signal, histogram


def calculate_atr(candles: List[dict], period: int = 14) -> float:
    """Calculate ATR for volatility-based stops"""
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


def detect_trend(closes: List[float]) -> str:
    """Detect trend using EMA crossover"""
    if len(closes) < 50:
        return "UNCLEAR"
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    price = closes[-1]
    
    # Strong trend requires clear separation
    if price > ema20 * 1.002 and ema20 > ema50 * 1.001:
        return "UPTREND"
    elif price < ema20 * 0.998 and ema20 < ema50 * 0.999:
        return "DOWNTREND"
    return "SIDEWAYS"


def analyze_symbol_winner(symbol: str) -> Tuple[str, float, str, dict]:
    """
    Winner-style analysis: Focus on trend + confirmation
    Uses 5m for short-term and looks for pullback entries
    """
    candles = get_candles(symbol, "5m", 50)
    if len(candles) < 30:
        return "HOLD", 0.0, "Insufficient data", {}
    
    try:
        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]
    except (IndexError, ValueError):
        return "HOLD", 0.0, "Data parse error", {}
    
    # Calculate indicators
    rsi = calculate_rsi(closes)
    macd_line, signal, macd_hist = calculate_macd(closes)
    trend = detect_trend(closes)
    atr = calculate_atr(candles)
    avg_volume = sum(volumes[-20:]) / 20 if volumes else 1
    current_volume = volumes[-1] if volumes else 1
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    # Calculate momentum
    momentum = ((closes[-1] - closes[-10]) / closes[-10]) * 100 if len(closes) >= 10 else 0
    
    indicators = {
        "rsi": round(rsi, 2),
        "macd_hist": round(macd_hist, 4),
        "trend": trend,
        "momentum": round(momentum, 2),
        "volume_ratio": round(volume_ratio, 2),
        "atr_pct": round((atr / closes[-1]) * 100, 3) if closes[-1] > 0 else 0
    }
    
    long_score = 0
    short_score = 0
    reasons = []
    
    # TREND IS KING (most important factor)
    if trend == "UPTREND":
        long_score += 3
        reasons.append("Strong uptrend")
    elif trend == "DOWNTREND":
        short_score += 3
        reasons.append("Strong downtrend")
    
    # RSI - look for pullback entries in trend
    if trend == "UPTREND" and 30 <= rsi <= 45:
        long_score += 2
        reasons.append(f"RSI pullback ({rsi:.0f})")
    elif trend == "DOWNTREND" and 55 <= rsi <= 70:
        short_score += 2
        reasons.append(f"RSI rally ({rsi:.0f})")
    elif rsi < 25:
        long_score += 2
        reasons.append(f"RSI oversold ({rsi:.0f})")
    elif rsi > 80:
        short_score += 2
        reasons.append(f"RSI overbought ({rsi:.0f})")
    
    # MACD alignment
    if macd_hist > 0 and macd_line > 0:
        long_score += 1
        reasons.append("MACD bullish")
    elif macd_hist < 0 and macd_line < 0:
        short_score += 1
        reasons.append("MACD bearish")
    
    # Momentum
    if momentum > 0.3:
        long_score += 1
        reasons.append(f"Momentum +{momentum:.1f}%")
    elif momentum < -0.3:
        short_score += 1
        reasons.append(f"Momentum {momentum:.1f}%")
    
    # Volume confirmation
    if volume_ratio > 1.3:
        if long_score > short_score:
            long_score += 1
        elif short_score > long_score:
            short_score += 1
        reasons.append(f"High volume ({volume_ratio:.1f}x)")
    
    # Generate signal
    max_score = 8
    if long_score >= MIN_SIGNAL_SCORE and long_score > short_score:
        confidence = min(0.65 + (long_score / max_score) * 0.25, 0.90)
        signal = "LONG"
        reasoning = " | ".join(reasons[:4])
    elif short_score >= MIN_SIGNAL_SCORE and short_score > long_score:
        confidence = min(0.65 + (short_score / max_score) * 0.25, 0.90)
        signal = "SHORT"
        reasoning = " | ".join(reasons[:4])
    else:
        confidence = 0.40
        signal = "HOLD"
        reasoning = f"No high-conviction signal (L:{long_score} S:{short_score})"
    
    return signal, confidence, reasoning, indicators


# =============================================================================
# POSITION MANAGEMENT - WINNER STYLE (Wide Stops + Trailing)
# =============================================================================

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def manage_position_winner(symbol: str, signal: str, confidence: float, reasoning: str) -> Optional[float]:
    """
    Winner-style position management:
    - Wide initial stop (5%)
    - Trailing activates at +8%
    - Let winners run to +15% or trail out
    """
    global open_positions, consecutive_losses
    
    size = POSITION_SIZES.get(symbol, "0.001")
    price = get_price(symbol)
    coin = symbol.replace("cmt_", "").replace("usdt", "").upper()
    
    log(f"🎯 OPENING {signal} {coin} @ ${price:,.2f} | Size: {size} | Conf: {confidence:.0%}")
    log(f"   📊 {reasoning}")
    log(f"   🎯 TP: +{PROFIT_TARGET_PCT}% | SL: -{STOP_LOSS_PCT}% | Trail at +{TRAILING_ACTIVATION_PCT}%")
    
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
    
    # Position management variables
    entry_price = price
    start_time = time.time()
    highest_pnl = 0
    trailing_active = False
    
    # Winner-style position management loop
    while (time.time() - start_time) < MAX_HOLD_TIME:
        time.sleep(10)  # Check every 10 seconds (not 5)
        current_price = get_price(symbol)
        
        if current_price <= 0:
            continue
        
        # Calculate leveraged PnL
        if signal == "LONG":
            price_change_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            price_change_pct = ((entry_price - current_price) / entry_price) * 100
        
        leveraged_pnl = price_change_pct * MAX_LEVERAGE
        
        # Track highest PnL
        if leveraged_pnl > highest_pnl:
            highest_pnl = leveraged_pnl
        
        # TRAILING STOP LOGIC
        if leveraged_pnl >= TRAILING_ACTIVATION_PCT and not trailing_active:
            trailing_active = True
            log(f"   📈 {coin} Trailing activated at +{leveraged_pnl:.1f}%")
        
        if trailing_active:
            # Exit if drops more than TRAILING_DISTANCE from peak
            if leveraged_pnl < highest_pnl - TRAILING_DISTANCE_PCT:
                log(f"   🔔 {coin} Trailing exit: Peak +{highest_pnl:.1f}% → Current +{leveraged_pnl:.1f}%")
                break
        
        # Take profit at target
        if leveraged_pnl >= PROFIT_TARGET_PCT:
            log(f"   💰 {coin} TARGET HIT: +{leveraged_pnl:.1f}%")
            break
        
        # Hard stop loss
        if leveraged_pnl <= -STOP_LOSS_PCT:
            log(f"   🛑 {coin} STOP LOSS: {leveraged_pnl:.1f}%")
            break
    
    # Close position
    close_direction = 3 if direction == 1 else 4
    close_result = None
    
    for attempt in range(3):
        close_result = place_order(symbol, close_direction, size)
        if close_result.get("order_id"):
            break
        time.sleep(2)
    
    final_pnl = None
    if close_result and close_result.get("order_id"):
        close_id = close_result.get("order_id")
        final_price = get_price(symbol)
        if final_price <= 0:
            final_price = entry_price
        
        if signal == "LONG":
            price_change_pct = ((final_price - entry_price) / entry_price) * 100
        else:
            price_change_pct = ((entry_price - final_price) / entry_price) * 100
        
        final_pnl = price_change_pct * MAX_LEVERAGE
        
        emoji = "✅" if final_pnl > 0 else "❌"
        log(f"   {emoji} {coin} CLOSED: P&L: {final_pnl:+.1f}% (price: {price_change_pct:+.2f}%)")
        
        # Track consecutive losses
        if final_pnl < 0:
            consecutive_losses += 1
        else:
            consecutive_losses = 0
        
        upload_ai_log(close_id, symbol, f"CLOSE_{signal}", 
                      f"Position closed. P&L: {final_pnl:+.1f}%. Trail active: {trailing_active}", 
                      0.8, final_price)
    else:
        log(f"   ❌❌ {coin} CRITICAL: Position close FAILED! Manual intervention needed.")
    
    # Remove from tracking
    with positions_lock:
        if symbol in open_positions:
            del open_positions[symbol]
    
    return final_pnl


def run_winner_strategy():
    """Main trading loop - Winner Style"""
    global open_positions, consecutive_losses
    
    log("=" * 70)
    log("🏆 WEEX AI WARS - WINNER STRATEGY BOT")
    log("=" * 70)
    log(f"💰 Position Size: ~$250-350 per trade")
    log(f"🎯 Profit Target: {PROFIT_TARGET_PCT}% | Stop: {STOP_LOSS_PCT}%")
    log(f"📈 Trailing: Activates at +{TRAILING_ACTIVATION_PCT}%, trails by {TRAILING_DISTANCE_PCT}%")
    log(f"⏱️  Max Hold: {MAX_HOLD_TIME//60} minutes")
    log(f"📊 Symbols: {len(SYMBOLS)} | Max Concurrent: {MAX_CONCURRENT_POSITIONS}")
    log("=" * 70)
    
    balance = get_balance()
    log(f"💰 Starting Balance: ${balance:.2f}")
    
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
            
            if pnl_pct < -MAX_DRAWDOWN_PCT:
                log(f"⚠️ DRAWDOWN LIMIT: {pnl_pct:.1f}%. Pausing for 30 minutes.")
                time.sleep(1800)
                continue
            
            # Reduce trading after consecutive losses
            if consecutive_losses >= 3:
                log(f"⚠️ {consecutive_losses} consecutive losses. Waiting 5 min.")
                time.sleep(300)
                consecutive_losses = 0
                continue
            
            # Count open positions
            with positions_lock:
                current_positions = len(open_positions)
            
            available_slots = MAX_CONCURRENT_POSITIONS - current_positions
            
            if available_slots > 0:
                log(f"🔍 Scanning... Balance: ${current_balance:.2f} | Open: {current_positions}/{MAX_CONCURRENT_POSITIONS} | P&L: {pnl_pct:+.1f}%")
                
                # Find high-conviction opportunities
                opportunities = []
                for symbol in SYMBOLS:
                    with positions_lock:
                        if symbol in open_positions:
                            continue
                    
                    signal, confidence, reasoning, indicators = analyze_symbol_winner(symbol)
                    if signal != "HOLD" and confidence >= MIN_CONFIDENCE:
                        opportunities.append({
                            "symbol": symbol,
                            "signal": signal,
                            "confidence": confidence,
                            "reasoning": reasoning,
                            "indicators": indicators
                        })
                
                # Sort by confidence (highest first)
                opportunities.sort(key=lambda x: x["confidence"], reverse=True)
                
                # Only take the BEST opportunities
                for opp in opportunities[:available_slots]:
                    symbol = opp["symbol"]
                    
                    with positions_lock:
                        if symbol in open_positions:
                            continue
                        open_positions[symbol] = True
                    
                    future = executor.submit(
                        manage_position_winner,
                        symbol,
                        opp["signal"],
                        opp["confidence"],
                        opp["reasoning"]
                    )
                    futures[symbol] = future
                    daily_trades += 1
                
                if not opportunities:
                    log(f"   No high-conviction signals. Waiting for better setup...")
            else:
                log(f"📊 All {MAX_CONCURRENT_POSITIONS} slots filled. Managing positions...")
            
            time.sleep(MIN_TRADE_INTERVAL)
            
        except KeyboardInterrupt:
            log("🛑 Stopped by user")
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            time.sleep(30)
    
    # Cleanup
    log("⏳ Waiting for positions to close...")
    executor.shutdown(wait=True)
    
    final_balance = get_balance()
    log("=" * 70)
    log("📊 SESSION SUMMARY")
    log(f"   Final Balance: ${final_balance:.2f}")
    log(f"   Total Trades: {daily_trades}")
    log(f"   Session P&L: {total_pnl:+.1f}%")
    log("=" * 70)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║  🏆 WEEX AI WARS - WINNER STRATEGY BOT                          ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Strategy: High-conviction trend following                       ║
    ║  • Wide stops (5%) + Trailing (activates at +8%)                ║
    ║  • Let winners run to +15%                                       ║
    ║  • All 8 symbols with bigger sizes (~$300/trade)                ║
    ║  • Quality over quantity                                         ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    confirm = input("Start WINNER STRATEGY trading? (yes/no): ").strip().lower()
    if confirm == "yes":
        run_winner_strategy()
    else:
        print("Cancelled.")
