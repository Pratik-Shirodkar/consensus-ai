"""
Bull Agent - Momentum-focused long opportunity finder
"""
from typing import Optional
from agents.base_agent import BaseAgent
from data.data_models import MarketData, DebateMessage, TradeAction


class BullAgent(BaseAgent):
    """
    The Bull Agent looks for LONG opportunities.
    Focuses on momentum indicators and breakout patterns.
    """
    
    def __init__(self):
        super().__init__(
            name="Bull",
            emoji="🐂",
            prompt_file="bull_prompt.txt"
        )
    
    async def analyze(self, market_data: MarketData, signals: list) -> dict:
        """
        Analyze market for long opportunities
        Returns proposal or hold decision
        """
        market_context = self._format_market_context(market_data)
        signals_context = self._format_signals(signals)
        
        prompt = f"""
{market_context}

{signals_context}

Based on this data, analyze whether there's a good LONG opportunity.
If you see a strong setup, propose a trade with your confidence level.
If conditions aren't right, indicate you're holding and explain why.

Respond with the appropriate JSON format as specified in your instructions.
"""
        
        response = await self._call_llm(prompt)
        result = self._extract_json(response)
        
        if result is None:
            result = {
                "action": "HOLD",
                "confidence": 0.5,
                "reasoning": response
            }
        
        # Add the raw message for display
        result["raw_message"] = response
        result["agent"] = self.name
        result["emoji"] = self.emoji
        
        return result
    
    async def respond_to(self, message: DebateMessage, market_data: MarketData) -> dict:
        """
        Respond to Bear's challenge or Risk Manager's questions
        """
        prompt = f"""
The {message.agent} Agent said:
"{message.message}"

Their confidence level: {message.confidence}

Respond to their points. If they challenged your proposal:
- Defend your position with additional evidence
- Or acknowledge valid concerns and adjust your confidence

Keep your response focused and professional.
"""
        
        response = await self._call_llm(prompt)
        result = self._extract_json(response) or {"reasoning": response}
        
        result["raw_message"] = response
        result["agent"] = self.name
        result["emoji"] = self.emoji
        
        return result
    
    def format_proposal_message(self, analysis: dict) -> str:
        """Format analysis into readable message for UI"""
        action = analysis.get("action", "HOLD")
        confidence = analysis.get("confidence", 0.5)
        reasoning = analysis.get("reasoning", "")
        
        if action == "PROPOSE_LONG":
            leverage = analysis.get("suggested_leverage", 5)
            sl = analysis.get("stop_loss_pct", 2.0)
            tp = analysis.get("take_profit_pct", 4.0)
            
            return (
                f"📈 **PROPOSING LONG** on {analysis.get('symbol', 'BTC/USDT')}\n"
                f"Confidence: {confidence*100:.0f}%\n"
                f"Leverage: {leverage}x | SL: {sl}% | TP: {tp}%\n\n"
                f"{reasoning}"
            )
        else:
            return f"⏸️ **HOLDING** - {reasoning}"


# Singleton instance
bull_agent = BullAgent()
