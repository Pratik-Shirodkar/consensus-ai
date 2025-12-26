"""
FastAPI REST API routes
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from agents.debate_engine import debate_engine
from execution.order_manager import order_manager
from config.settings import settings


router = APIRouter(prefix="/api", tags=["API"])


# Request/Response Models
class StartSessionRequest(BaseModel):
    symbol: Optional[str] = None
    interval_seconds: Optional[int] = None


class TradeResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# Health & Status
@router.get("/status")
async def get_status():
    """Get system status"""
    debate_stats = debate_engine.get_stats()
    trading_stats = order_manager.get_stats()
    
    return {
        "status": "running" if debate_engine.is_running else "stopped",
        "symbol": settings.default_symbol,
        "debate": debate_stats,
        "trading": trading_stats
    }


@router.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "service": "consensus-ai"}


@router.get("/candles")
async def get_candles(symbol: str = "cmt_btcusdt", interval: str = "5m", limit: int = 100):
    """Get candlestick data for chart"""
    from data.market_data import market_data_service
    
    try:
        market_data = await market_data_service.get_market_data(symbol)
        candles = market_data.candles[-limit:] if market_data.candles else []
        
        return {
            "symbol": symbol,
            "interval": interval,
            "candles": [
                {
                    "time": int(c.timestamp.timestamp()),
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume
                }
                for c in candles
            ],
            "ticker": {
                "last_price": market_data.ticker.last_price if market_data.ticker else 0,
                "change_pct_24h": market_data.ticker.change_pct_24h if market_data.ticker else 0
            } if market_data.ticker else None
        }
    except Exception as e:
        print(f"Error fetching candles: {e}")
        return {"symbol": symbol, "interval": interval, "candles": [], "error": str(e)}


# Trading Session Control
@router.post("/start")
async def start_trading(request: StartSessionRequest):
    """Start the trading session"""
    if debate_engine.is_running:
        raise HTTPException(status_code=400, detail="Session already running")
    
    symbol = request.symbol or settings.default_symbol
    interval = request.interval_seconds or settings.debate_interval_seconds
    
    # Start continuous debate in background
    import asyncio
    asyncio.create_task(debate_engine.run_continuous(symbol, interval))
    
    return {
        "success": True,
        "message": f"Trading session started for {symbol}",
        "interval_seconds": interval
    }


@router.post("/stop")
async def stop_trading():
    """Stop the trading session"""
    if not debate_engine.is_running:
        raise HTTPException(status_code=400, detail="No session running")
    
    debate_engine.stop()
    
    return {
        "success": True,
        "message": "Trading session stopped"
    }


@router.post("/debate/trigger")
async def trigger_single_debate(symbol: Optional[str] = None):
    """Trigger a single debate cycle manually"""
    result = await debate_engine.run_debate_cycle(symbol or settings.default_symbol)
    
    return {
        "success": True,
        "trade_executed": result is not None and result.approved,
        "decision": result.dict() if result else None
    }


# Debate History
@router.get("/debate/history")
async def get_debate_history(limit: int = 50):
    """Get recent debate messages"""
    messages = debate_engine.get_debate_history(limit)
    return {
        "messages": [
            {
                "agent": m.agent,
                "emoji": m.emoji,
                "message": m.message,
                "confidence": m.confidence,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ],
        "total": len(messages)
    }


@router.delete("/debate/history")
async def clear_debate_history():
    """Clear debate history"""
    debate_engine.clear_history()
    return {"success": True, "message": "History cleared"}


# Positions & Trades
@router.get("/positions")
async def get_positions():
    """Get all open positions"""
    await order_manager.update_positions()
    positions = order_manager.get_positions()
    
    return {
        "positions": [p.dict() for p in positions],
        "total_exposure_pct": order_manager.get_total_exposure()
    }


@router.post("/positions/{symbol}/close")
async def close_position(symbol: str, reason: str = "Manual close"):
    """Close a specific position"""
    trade = await order_manager.close_position(symbol, reason)
    
    if not trade:
        raise HTTPException(status_code=404, detail=f"No open position for {symbol}")
    
    return {
        "success": True,
        "trade": trade.dict()
    }


@router.get("/trades")
async def get_trades(limit: int = 50):
    """Get trade history"""
    trades = order_manager.get_trade_history(limit)
    
    return {
        "trades": [t.dict() for t in trades],
        "total": len(trades)
    }


# Agent Stats
@router.get("/agents/stats")
async def get_agent_stats():
    """Get agent performance statistics"""
    from agents.risk_manager import risk_manager
    
    return {
        "violations": risk_manager.violations,
        "debate_count": debate_engine.get_stats()["total_debates"],
        "trade_count": debate_engine.trade_count
    }


@router.post("/agents/reset")
async def reset_agents():
    """Reset agent state (violations, history)"""
    from agents.risk_manager import risk_manager
    
    risk_manager.reset_violations()
    debate_engine.clear_history()
    
    return {"success": True, "message": "Agents reset"}
