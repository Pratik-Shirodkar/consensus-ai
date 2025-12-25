"""
Pydantic models for market data
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class TradeAction(str, Enum):
    LONG = "long"
    SHORT = "short"
    CLOSE = "close"
    HOLD = "hold"


class Candle(BaseModel):
    """OHLCV candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class OrderBookLevel(BaseModel):
    """Single level in order book"""
    price: float
    quantity: float


class OrderBook(BaseModel):
    """Order book snapshot"""
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel]  # Buy orders (descending by price)
    asks: List[OrderBookLevel]  # Sell orders (ascending by price)
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread"""
        if self.bids and self.asks:
            return self.asks[0].price - self.bids[0].price
        return 0.0
    
    @property
    def spread_pct(self) -> float:
        """Calculate spread as percentage"""
        if self.bids and self.asks:
            mid = (self.asks[0].price + self.bids[0].price) / 2
            return (self.spread / mid) * 100
        return 0.0


class Ticker(BaseModel):
    """Current ticker data"""
    symbol: str
    last_price: float
    bid: float
    ask: float
    volume_24h: float
    change_24h: float
    change_pct_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime


class MarketData(BaseModel):
    """Aggregated market data for analysis"""
    symbol: str
    ticker: Ticker
    candles: List[Candle]
    orderbook: OrderBook
    funding_rate: Optional[float] = None
    
    @property
    def current_price(self) -> float:
        return self.ticker.last_price


class SignalStrength(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEUTRAL = "neutral"


class TechnicalSignal(BaseModel):
    """Technical indicator signal"""
    name: str
    value: float
    signal: SignalStrength
    description: str


class TradeProposal(BaseModel):
    """Proposed trade from an agent"""
    action: TradeAction
    symbol: str
    confidence: float
    suggested_leverage: int
    stop_loss_pct: float
    take_profit_pct: float
    reasoning: str
    signals: List[TechnicalSignal] = []


class DebateMessage(BaseModel):
    """Message in the debate"""
    agent: str
    emoji: str
    message: str
    confidence: Optional[float] = None
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


class TradeDecision(BaseModel):
    """Final decision from Risk Manager"""
    approved: bool
    action: TradeAction
    symbol: str
    leverage: int
    size_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    reasoning: str


class Position(BaseModel):
    """Open position"""
    symbol: str
    side: OrderSide
    size: float
    entry_price: float
    current_price: float
    leverage: int
    unrealized_pnl: float
    unrealized_pnl_pct: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime


class Trade(BaseModel):
    """Executed trade record"""
    id: str
    symbol: str
    side: OrderSide
    action: TradeAction
    size: float
    price: float
    leverage: int
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    fee: float = 0.0
    reasoning: str
    executed_at: datetime
    closed_at: Optional[datetime] = None
