"""
Risk Manager Agent - Final authority with veto power
"""
from agents.base_agent import BaseAgent
from data.data_models import MarketData, DebateMessage, TradeDecision, TradeAction
from signals.risk_metrics import risk_metrics
from config.settings import settings


class RiskManager(BaseAgent):
    """
    The Risk Manager has veto power over all trades.
    Enforces hard rules: 20x max leverage, position limits, stop-loss requirements.
    """
    
    def __init__(self):
        super().__init__(
            name="Risk Manager",
            emoji="⚖️",
            prompt_file="risk_prompt.txt"
        )
        self.violations = {"Bull": 0, "Bear": 0}
    
    async def analyze(self, market_data: MarketData, signals: list) -> dict:
        """
        Analyze current portfolio risk state
        Used for general risk assessment, not trade decisions
        """
        market_context = self._format_market_context(market_data)
        
        prompt = f"""
{market_context}

Provide a risk assessment of current market conditions.
Consider:
- Volatility levels
- Market structure
- Whether it's safe to trade at all right now

This is a general assessment, not a trade decision.
"""
        
        response = await self._call_llm(prompt)
        result = self._extract_json(response) or {"assessment": response}
        
        result["raw_message"] = response
        result["agent"] = self.name
        result["emoji"] = self.emoji
        
        return result
    
    async def respond_to(self, message: DebateMessage, market_data: MarketData) -> dict:
        """Not typically used - Risk Manager arbitrates, doesn't respond"""
        return await self.analyze(market_data, [])
    
    async def arbitrate(
        self,
        bull_analysis: dict,
        bear_analysis: dict,
        market_data: MarketData,
        current_exposure_pct: float = 0
    ) -> dict:
        """
        Make final decision on a proposed trade
        This is the main function for the Risk Manager
        """
        # Pre-check: Enforce hard leverage limit
        proposed_leverage = bull_analysis.get("suggested_leverage", 5)
        leverage_adjusted, leverage_warning = risk_metrics.validate_leverage(proposed_leverage)
        
        # Track violations
        if proposed_leverage > settings.max_leverage:
            self.violations["Bull"] += 1
        
        # Build context for LLM
        bull_action = bull_analysis.get("action", "HOLD")
        bull_confidence = bull_analysis.get("confidence", 0.5)
        bear_action = bear_analysis.get("action", "CHALLENGE")
        bear_confidence = bear_analysis.get("confidence", 0.5)
        
        prompt = f"""
DEBATE SUMMARY:

BULL AGENT ({bull_confidence*100:.0f}% confidence):
Action: {bull_action}
{bull_analysis.get('reasoning', '')}
Proposed Leverage: {proposed_leverage}x
Proposed Stop-Loss: {bull_analysis.get('stop_loss_pct', 2.0)}%
Proposed Take-Profit: {bull_analysis.get('take_profit_pct', 4.0)}%

BEAR AGENT ({bear_confidence*100:.0f}% confidence):
Action: {bear_action}
{bear_analysis.get('reasoning', '')}

PORTFOLIO STATUS:
Current Exposure: {current_exposure_pct:.1f}%
Bull Violations Today: {self.violations['Bull']}
Bear Violations Today: {self.violations['Bear']}

{"⚠️ LEVERAGE VIOLATION: " + leverage_warning if leverage_warning else ""}

Make your final decision: APPROVE, REJECT, or MODIFY.
Remember your hard rules and decision framework.
If Bull has violations, be stern in your response.
"""
        
        response = await self._call_llm(prompt)
        result = self._extract_json(response)
        
        if result is None:
            # Default to reject if can't parse
            result = {
                "decision": "REJECT",
                "reasoning": response
            }
        
        # Enforce hard limits regardless of LLM output
        if result.get("decision") in ["APPROVE", "MODIFY"]:
            final_leverage = min(
                result.get("final_leverage", leverage_adjusted),
                settings.max_leverage
            )
            result["final_leverage"] = final_leverage
            
            # Ensure stop-loss exists
            if not result.get("final_stop_loss_pct"):
                result["final_stop_loss_pct"] = bull_analysis.get("stop_loss_pct", 2.0)
            
            # Ensure take-profit exists
            if not result.get("final_take_profit_pct"):
                result["final_take_profit_pct"] = bull_analysis.get("take_profit_pct", 4.0)
            
            # Cap position size
            final_size = min(
                result.get("final_size_pct", 5.0),
                settings.max_position_size_pct
            )
            result["final_size_pct"] = final_size
        
        result["raw_message"] = response
        result["agent"] = self.name
        result["emoji"] = self.emoji
        
        return result
    
    def format_decision_message(self, decision: dict) -> str:
        """Format decision into readable message for UI"""
        decision_type = decision.get("decision", "REJECT")
        reasoning = decision.get("reasoning", "")
        
        if decision_type == "APPROVE":
            leverage = decision.get("final_leverage", 5)
            size = decision.get("final_size_pct", 5)
            sl = decision.get("final_stop_loss_pct", 2.0)
            tp = decision.get("final_take_profit_pct", 4.0)
            
            return (
                f"✅ **APPROVED**\n"
                f"Leverage: {leverage}x | Size: {size}%\n"
                f"Stop-Loss: {sl}% | Take-Profit: {tp}%\n\n"
                f"{reasoning}"
            )
        elif decision_type == "MODIFY":
            orig_lev = decision.get("original_leverage", "?")
            final_lev = decision.get("final_leverage", 5)
            
            return (
                f"⚡ **MODIFIED**\n"
                f"Leverage: {orig_lev}x → {final_lev}x\n"
                f"Size: {decision.get('final_size_pct', 5)}%\n\n"
                f"{reasoning}"
            )
        else:
            return f"🚫 **REJECTED**\n\n{reasoning}"
    
    def to_trade_decision(self, decision: dict, symbol: str) -> TradeDecision:
        """Convert decision dict to TradeDecision model"""
        approved = decision.get("decision") in ["APPROVE", "MODIFY"]
        
        return TradeDecision(
            approved=approved,
            action=TradeAction.LONG if approved else TradeAction.HOLD,
            symbol=symbol,
            leverage=decision.get("final_leverage", 1),
            size_pct=decision.get("final_size_pct", 0),
            stop_loss_pct=decision.get("final_stop_loss_pct", 2.0),
            take_profit_pct=decision.get("final_take_profit_pct", 4.0),
            reasoning=decision.get("reasoning", "")
        )
    
    def reset_violations(self):
        """Reset violation counts (call at start of day)"""
        self.violations = {"Bull": 0, "Bear": 0}


# Singleton instance
risk_manager = RiskManager()
