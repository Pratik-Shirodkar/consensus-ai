"""
Market data service for aggregating and caching data
Includes mock data fallback for demo mode
"""
import asyncio
import random
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from data.weex_client import weex_client
from data.data_models import MarketData, Candle, OrderBook, OrderBookLevel, Ticker
from config.settings import settings


def generate_mock_candles(base_price: float = 98500, count: int = 100) -> List[Candle]:
    """Generate realistic mock candlestick data"""
    candles = []
    price = base_price
    now = datetime.now()
    
    for i in range(count, 0, -1):
        volatility = 0.002
        change = (random.random() - 0.48) * volatility * price
        
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + random.random() * 50
        low_p = min(open_p, close_p) - random.random() * 50
        volume = random.uniform(100, 500)
        
        candles.append(Candle(
            timestamp=now - timedelta(minutes=i * 5),
            open=open_p,
            high=high_p,
            low=low_p,
            close=close_p,
            volume=volume
        ))
        
        price = close_p
    
    return candles


def generate_mock_ticker(symbol: str, last_candle: Candle) -> Ticker:
    """Generate mock ticker from candle data"""
    return Ticker(
        symbol=symbol,
        last_price=last_candle.close,
        bid=last_candle.close - random.uniform(0.5, 2),
        ask=last_candle.close + random.uniform(0.5, 2),
        volume_24h=random.uniform(1000000, 5000000),
        change_24h=random.uniform(-500, 500),
        change_pct_24h=random.uniform(-2, 2),
        high_24h=last_candle.close + random.uniform(100, 300),
        low_24h=last_candle.close - random.uniform(100, 300),
        timestamp=datetime.now()
    )


def generate_mock_orderbook(base_price: float) -> OrderBook:
    """Generate mock order book"""
    bids = []
    asks = []
    
    for i in range(10):
        bid_price = base_price - (i + 1) * random.uniform(1, 5)
        ask_price = base_price + (i + 1) * random.uniform(1, 5)
        
        bids.append(OrderBookLevel(
            price=bid_price,
            quantity=random.uniform(0.1, 2.0)
        ))
        asks.append(OrderBookLevel(
            price=ask_price,
            quantity=random.uniform(0.1, 2.0)
        ))
    
    return OrderBook(
        symbol="cmt_btcusdt",
        timestamp=datetime.now(),
        bids=bids,
        asks=asks
    )


class MarketDataService:
    """
    Aggregates market data from WEEX and provides a unified interface
    Falls back to mock data for demo mode
    """
    
    def __init__(self):
        self._candle_cache: Dict[str, List[Candle]] = {}
        self._orderbook_cache: Dict[str, OrderBook] = {}
        self._ticker_cache: Dict[str, Ticker] = {}
        self._funding_cache: Dict[str, float] = {}
        self._last_update: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(seconds=5)
        # Check if WEEX credentials are properly configured
        self._use_mock = not settings.weex_api_key or settings.weex_api_key == "your_api_key" or len(settings.weex_api_key) < 10
        print(f"📊 MarketDataService initialized - Using {'MOCK' if self._use_mock else 'REAL WEEX'} data")
        if not self._use_mock:
            print(f"   WEEX API Key: {settings.weex_api_key[:10]}...")

    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._last_update:
            return False
        return datetime.now() - self._last_update[key] < self._cache_ttl
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """
        Get aggregated market data for a symbol
        Uses mock data if WEEX credentials aren't configured
        """
        if self._use_mock:
            return await self._get_mock_market_data(symbol)
        
        try:
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
        except Exception as e:
            print(f"Error fetching market data, falling back to mock: {e}")
            return await self._get_mock_market_data(symbol)
    
    async def _get_mock_market_data(self, symbol: str) -> MarketData:
        """Generate mock market data for demo purposes"""
        candles = generate_mock_candles()
        last_candle = candles[-1] if candles else Candle(
            timestamp=datetime.now(),
            open=98500, high=98600, low=98400, close=98550, volume=100
        )
        
        return MarketData(
            symbol=symbol,
            ticker=generate_mock_ticker(symbol, last_candle),
            candles=candles,
            orderbook=generate_mock_orderbook(last_candle.close),
            funding_rate=random.uniform(-0.001, 0.001)
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
