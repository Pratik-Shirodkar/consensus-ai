"""
Market data service for aggregating and caching data
"""
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from data.weex_client import weex_client
from data.data_models import MarketData, Candle, OrderBook, Ticker


class MarketDataService:
    """
    Aggregates market data from WEEX and provides a unified interface
    """
    
    def __init__(self):
        self._candle_cache: Dict[str, List[Candle]] = {}
        self._orderbook_cache: Dict[str, OrderBook] = {}
        self._ticker_cache: Dict[str, Ticker] = {}
        self._funding_cache: Dict[str, float] = {}
        self._last_update: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(seconds=5)
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._last_update:
            return False
        return datetime.now() - self._last_update[key] < self._cache_ttl
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """
        Get aggregated market data for a symbol
        Fetches fresh data if cache is expired
        """
        # Fetch all data concurrently
        ticker, candles, orderbook, funding = await asyncio.gather(
            self.get_ticker(symbol),
            self.get_candles(symbol),
            self.get_orderbook(symbol),
            self.get_funding_rate(symbol)
        )
        
        return MarketData(
            symbol=symbol,
            ticker=ticker,
            candles=candles,
            orderbook=orderbook,
            funding_rate=funding
        )
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker with caching"""
        cache_key = f"ticker_{symbol}"
        if self._is_cache_valid(cache_key):
            return self._ticker_cache[symbol]
        
        ticker = await weex_client.get_ticker(symbol)
        self._ticker_cache[symbol] = ticker
        self._last_update[cache_key] = datetime.now()
        return ticker
    
    async def get_candles(
        self, 
        symbol: str, 
        interval: str = "5m", 
        limit: int = 100
    ) -> List[Candle]:
        """Get candles with caching"""
        cache_key = f"candles_{symbol}_{interval}"
        if self._is_cache_valid(cache_key):
            return self._candle_cache.get(cache_key, [])
        
        candles = await weex_client.get_klines(symbol, interval, limit)
        self._candle_cache[cache_key] = candles
        self._last_update[cache_key] = datetime.now()
        return candles
    
    async def get_orderbook(self, symbol: str, depth: int = 20) -> OrderBook:
        """Get orderbook with caching"""
        cache_key = f"orderbook_{symbol}"
        if self._is_cache_valid(cache_key):
            return self._orderbook_cache[symbol]
        
        orderbook = await weex_client.get_orderbook(symbol, depth)
        self._orderbook_cache[symbol] = orderbook
        self._last_update[cache_key] = datetime.now()
        return orderbook
    
    async def get_funding_rate(self, symbol: str) -> float:
        """Get funding rate with caching"""
        cache_key = f"funding_{symbol}"
        if self._is_cache_valid(cache_key):
            return self._funding_cache.get(symbol, 0)
        
        funding = await weex_client.get_funding_rate(symbol)
        self._funding_cache[symbol] = funding
        self._last_update[cache_key] = datetime.now()
        return funding
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cached data"""
        if symbol:
            # Clear specific symbol
            keys_to_remove = [k for k in self._last_update if symbol in k]
            for key in keys_to_remove:
                del self._last_update[key]
        else:
            # Clear all
            self._candle_cache.clear()
            self._orderbook_cache.clear()
            self._ticker_cache.clear()
            self._funding_cache.clear()
            self._last_update.clear()


# Create singleton instance
market_data_service = MarketDataService()
