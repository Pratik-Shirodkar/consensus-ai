"""
Risk metrics for portfolio and position management
"""
import numpy as np
from typing import List, Optional
from data.data_models import Candle, Position
from config.settings import settings


class RiskMetrics:
    """Calculates risk metrics for the Risk Manager agent"""
    
    def __init__(self):
        self.max_leverage = settings.max_leverage  # Hard limit: 20x
        self.max_position_size_pct = settings.max_position_size_pct
        self.max_drawdown_pct = 5.0  # Maximum acceptable drawdown
        self.var_confidence = 0.95  # 95% VaR
    
    def validate_leverage(self, proposed_leverage: int) -> tuple[int, str]:
        """
        Validate and cap leverage at maximum allowed
        Returns (adjusted_leverage, message)
        """
        if proposed_leverage > self.max_leverage:
            return (
                self.max_leverage,
                f"⚠️ Leverage {proposed_leverage}x exceeds maximum. Capped to {self.max_leverage}x."
            )
        elif proposed_leverage > 10:
            return (
                proposed_leverage,
                f"⚡ High leverage at {proposed_leverage}x. Use with caution."
            )
        else:
            return (proposed_leverage, "")
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_pct: float,
        risk_per_trade_pct: float = 2.0
    ) -> float:
        """
        Calculate position size based on risk management
        Uses the 2% rule by default
        """
        risk_amount = account_balance * (risk_per_trade_pct / 100)
        price_risk = entry_price * (stop_loss_pct / 100)
        
        if price_risk > 0:
            position_size = risk_amount / price_risk
        else:
            position_size = 0
        
        # Cap at maximum position size
        max_size = account_balance * (self.max_position_size_pct / 100) / entry_price
        return min(position_size, max_size)
    
    def calculate_var(
        self,
        returns: List[float],
        confidence: float = 0.95,
        time_horizon: int = 1
    ) -> float:
        """
        Calculate Value at Risk using historical method
        Returns the maximum expected loss at given confidence level
        """
        if len(returns) < 10:
            return 0.0
        
        returns_array = np.array(returns)
        var_percentile = (1 - confidence) * 100
        var = np.percentile(returns_array, var_percentile)
        
        # Scale to time horizon (assuming daily returns)
        var_scaled = var * np.sqrt(time_horizon)
        
        return abs(var_scaled)
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """
        Calculate maximum drawdown from equity curve
        Returns percentage of maximum decline from peak
        """
        if len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        max_drawdown = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe Ratio
        Measures risk-adjusted returns
        """
        if len(returns) < 10:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate
        
        mean_return = np.mean(excess_returns)
        std_return = np.std(excess_returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming daily returns)
        sharpe = (mean_return / std_return) * np.sqrt(365)
        return sharpe
    
    def calculate_portfolio_risk(
        self,
        positions: List[Position],
        account_balance: float
    ) -> dict:
        """
        Calculate overall portfolio risk metrics
        """
        if not positions:
            return {
                "total_exposure": 0,
                "exposure_pct": 0,
                "weighted_leverage": 0,
                "risk_level": "low"
            }
        
        total_exposure = sum(
            p.size * p.current_price * p.leverage 
            for p in positions
        )
        exposure_pct = (total_exposure / account_balance) * 100 if account_balance > 0 else 0
        
        # Weighted average leverage
        total_notional = sum(p.size * p.current_price for p in positions)
        weighted_leverage = sum(
            (p.size * p.current_price / total_notional) * p.leverage 
            for p in positions
        ) if total_notional > 0 else 0
        
        # Determine risk level
        if exposure_pct > 80 or weighted_leverage > 15:
            risk_level = "critical"
        elif exposure_pct > 50 or weighted_leverage > 10:
            risk_level = "high"
        elif exposure_pct > 30 or weighted_leverage > 5:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "total_exposure": total_exposure,
            "exposure_pct": exposure_pct,
            "weighted_leverage": weighted_leverage,
            "risk_level": risk_level
        }
    
    def check_trade_safety(
        self,
        proposed_leverage: int,
        proposed_size_pct: float,
        current_exposure_pct: float,
        volatility_pct: float
    ) -> tuple[bool, str]:
        """
        Safety check for a proposed trade
        Returns (is_safe, reason)
        """
        warnings = []
        is_safe = True
        
        # Leverage check
        if proposed_leverage > self.max_leverage:
            is_safe = False
            warnings.append(f"Leverage {proposed_leverage}x exceeds limit of {self.max_leverage}x")
        
        # Position size check
        if proposed_size_pct > self.max_position_size_pct:
            is_safe = False
            warnings.append(f"Position size {proposed_size_pct}% exceeds limit of {self.max_position_size_pct}%")
        
        # Combined exposure check
        new_exposure = current_exposure_pct + proposed_size_pct
        if new_exposure > 80:
            is_safe = False
            warnings.append(f"Total exposure would reach {new_exposure}% - too high")
        
        # High volatility warning
        if volatility_pct > 5.0 and proposed_leverage > 5:
            warnings.append(f"High volatility ({volatility_pct}%) with leverage - risky")
        
        reason = " | ".join(warnings) if warnings else "Trade passes safety checks"
        return is_safe, reason


# Singleton instance
risk_metrics = RiskMetrics()
