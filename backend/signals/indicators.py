"""
Technical indicators for trading signals
"""
import pandas as pd
import numpy as np
from typing import List, Tuple
from data.data_models import Candle, TechnicalSignal, SignalStrength


def candles_to_df(candles: List[Candle]) -> pd.DataFrame:
    """Convert candle list to pandas DataFrame"""
    data = {
        'timestamp': [c.timestamp for c in candles],
        'open': [c.open for c in candles],
        'high': [c.high for c in candles],
        'low': [c.low for c in candles],
        'close': [c.close for c in candles],
        'volume': [c.volume for c in candles]
    }
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(
    df: pd.DataFrame, 
    fast: int = 12, 
    slow: int = 26, 
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD (line, signal, histogram)"""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    df: pd.DataFrame, 
    period: int = 20, 
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands (upper, middle, lower)"""
    middle = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift(1))
    low_close = abs(df['low'] - df['close'].shift(1))
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr


def calculate_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate Volume Simple Moving Average"""
    return df['volume'].rolling(window=period).mean()


def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).mean()


def calculate_stochastic(
    df: pd.DataFrame, 
    k_period: int = 14, 
    d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator (%K and %D)"""
    lowest_low = df['low'].rolling(window=k_period).min()
    highest_high = df['high'].rolling(window=k_period).max()
    
    k = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    
    return k, d


class IndicatorAnalyzer:
    """Analyzes technical indicators and generates signals"""
    
    def __init__(self):
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.atr_period = 14
        self.vol_period = 20
    
    def analyze(self, candles: List[Candle]) -> List[TechnicalSignal]:
        """Generate all technical signals from candles"""
        if len(candles) < 30:  # Need enough data
            return []
        
        df = candles_to_df(candles)
        signals = []
        
        # RSI Analysis
        rsi = calculate_rsi(df, self.rsi_period)
        current_rsi = rsi.iloc[-1]
        signals.append(self._analyze_rsi(current_rsi))
        
        # MACD Analysis
        macd_line, signal_line, histogram = calculate_macd(
            df, self.macd_fast, self.macd_slow, self.macd_signal
        )
        signals.append(self._analyze_macd(
            macd_line.iloc[-1], 
            signal_line.iloc[-1], 
            histogram.iloc[-1],
            histogram.iloc[-2] if len(histogram) > 1 else 0
        ))
        
        # Bollinger Bands Analysis
        upper, middle, lower = calculate_bollinger_bands(df, self.bb_period)
        signals.append(self._analyze_bollinger(
            df['close'].iloc[-1],
            upper.iloc[-1],
            middle.iloc[-1],
            lower.iloc[-1]
        ))
        
        # Volume Analysis
        vol_sma = calculate_volume_sma(df, self.vol_period)
        signals.append(self._analyze_volume(
            df['volume'].iloc[-1],
            vol_sma.iloc[-1]
        ))
        
        # ATR (for volatility context)
        atr = calculate_atr(df, self.atr_period)
        signals.append(self._analyze_volatility(
            atr.iloc[-1],
            df['close'].iloc[-1]
        ))
        
        return signals
    
    def _analyze_rsi(self, rsi: float) -> TechnicalSignal:
        """Analyze RSI signal"""
        if rsi >= 70:
            return TechnicalSignal(
                name="RSI",
                value=rsi,
                signal=SignalStrength.STRONG,
                description=f"Overbought at {rsi:.1f} - potential reversal down"
            )
        elif rsi >= 60:
            return TechnicalSignal(
                name="RSI",
                value=rsi,
                signal=SignalStrength.MODERATE,
                description=f"Bullish momentum at {rsi:.1f}"
            )
        elif rsi <= 30:
            return TechnicalSignal(
                name="RSI",
                value=rsi,
                signal=SignalStrength.STRONG,
                description=f"Oversold at {rsi:.1f} - potential reversal up"
            )
        elif rsi <= 40:
            return TechnicalSignal(
                name="RSI",
                value=rsi,
                signal=SignalStrength.MODERATE,
                description=f"Bearish momentum at {rsi:.1f}"
            )
        else:
            return TechnicalSignal(
                name="RSI",
                value=rsi,
                signal=SignalStrength.NEUTRAL,
                description=f"Neutral at {rsi:.1f}"
            )
    
    def _analyze_macd(
        self, 
        macd: float, 
        signal: float, 
        hist: float,
        prev_hist: float
    ) -> TechnicalSignal:
        """Analyze MACD signal"""
        # Bullish crossover
        if hist > 0 and prev_hist <= 0:
            return TechnicalSignal(
                name="MACD",
                value=hist,
                signal=SignalStrength.STRONG,
                description="Bullish crossover - MACD crossed above signal"
            )
        # Bearish crossover
        elif hist < 0 and prev_hist >= 0:
            return TechnicalSignal(
                name="MACD",
                value=hist,
                signal=SignalStrength.STRONG,
                description="Bearish crossover - MACD crossed below signal"
            )
        # Bullish momentum
        elif hist > 0 and hist > prev_hist:
            return TechnicalSignal(
                name="MACD",
                value=hist,
                signal=SignalStrength.MODERATE,
                description="Bullish momentum increasing"
            )
        # Bearish momentum
        elif hist < 0 and hist < prev_hist:
            return TechnicalSignal(
                name="MACD",
                value=hist,
                signal=SignalStrength.MODERATE,
                description="Bearish momentum increasing"
            )
        else:
            return TechnicalSignal(
                name="MACD",
                value=hist,
                signal=SignalStrength.NEUTRAL,
                description="No clear MACD signal"
            )
    
    def _analyze_bollinger(
        self, 
        price: float, 
        upper: float, 
        middle: float, 
        lower: float
    ) -> TechnicalSignal:
        """Analyze Bollinger Bands signal"""
        band_width = upper - lower
        position = (price - lower) / band_width if band_width > 0 else 0.5
        
        if price >= upper:
            return TechnicalSignal(
                name="Bollinger",
                value=position,
                signal=SignalStrength.STRONG,
                description="Price at upper band - overbought"
            )
        elif price <= lower:
            return TechnicalSignal(
                name="Bollinger",
                value=position,
                signal=SignalStrength.STRONG,
                description="Price at lower band - oversold"
            )
        elif position > 0.7:
            return TechnicalSignal(
                name="Bollinger",
                value=position,
                signal=SignalStrength.MODERATE,
                description="Price in upper zone"
            )
        elif position < 0.3:
            return TechnicalSignal(
                name="Bollinger",
                value=position,
                signal=SignalStrength.MODERATE,
                description="Price in lower zone"
            )
        else:
            return TechnicalSignal(
                name="Bollinger",
                value=position,
                signal=SignalStrength.NEUTRAL,
                description="Price near middle band"
            )
    
    def _analyze_volume(self, volume: float, vol_avg: float) -> TechnicalSignal:
        """Analyze volume relative to average"""
        ratio = volume / vol_avg if vol_avg > 0 else 1.0
        
        if ratio >= 2.0:
            return TechnicalSignal(
                name="Volume",
                value=ratio,
                signal=SignalStrength.STRONG,
                description=f"Volume {ratio:.1f}x above average - strong interest"
            )
        elif ratio >= 1.3:
            return TechnicalSignal(
                name="Volume",
                value=ratio,
                signal=SignalStrength.MODERATE,
                description=f"Volume {ratio:.1f}x above average"
            )
        elif ratio <= 0.5:
            return TechnicalSignal(
                name="Volume",
                value=ratio,
                signal=SignalStrength.WEAK,
                description=f"Low volume - weak conviction"
            )
        else:
            return TechnicalSignal(
                name="Volume",
                value=ratio,
                signal=SignalStrength.NEUTRAL,
                description="Normal volume"
            )
    
    def _analyze_volatility(self, atr: float, price: float) -> TechnicalSignal:
        """Analyze volatility via ATR"""
        atr_pct = (atr / price) * 100 if price > 0 else 0
        
        if atr_pct >= 5.0:
            return TechnicalSignal(
                name="Volatility",
                value=atr_pct,
                signal=SignalStrength.STRONG,
                description=f"High volatility at {atr_pct:.2f}% - increased risk"
            )
        elif atr_pct >= 3.0:
            return TechnicalSignal(
                name="Volatility",
                value=atr_pct,
                signal=SignalStrength.MODERATE,
                description=f"Moderate volatility at {atr_pct:.2f}%"
            )
        else:
            return TechnicalSignal(
                name="Volatility",
                value=atr_pct,
                signal=SignalStrength.WEAK,
                description=f"Low volatility at {atr_pct:.2f}%"
            )


# Singleton instance
indicator_analyzer = IndicatorAnalyzer()
