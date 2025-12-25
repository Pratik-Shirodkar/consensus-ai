"""
Bear Agent - Risk-focused skeptic and short opportunity finder
"""
from agents.base_agent import BaseAgent
from data.data_models import MarketData, DebateMessage


class BearAgent(BaseAgent):
    """
    The Bear Agent challenges bullish proposals and identifies risks.
    Focuses on mean reversion, overbought conditions, and market structure.
    """
    
    def __init__(self):
        super().__init__(
            name="Bear",
            emoji="🐻",
            prompt_file="bear_prompt.txt"
        )
    
    async def analyze(self, market_data: MarketData, signals: list) -> dict:
        """
        Analyze market for risks or short opportunities
        Used when Bear initiates (no Bull proposal to respond to)
        """
        market_context = self._format_market_context(market_data)
        signals_context = self._format_signals(signals)
        
        prompt = f"""
{market_context}

{signals_context}

Analyze the current market conditions for risks or SHORT opportunities.
Look for:
- Overbought conditions
- Weak order book support
- Bearish divergences
- Reasons to be cautious

Provide your analysis with confidence level.
"""
        
        response = await self._call_llm(prompt)
        result = self._extract_json(response)
        
        if result is None:
            result = {
                "action": "NEUTRAL",
                "confidence": 0.5,
                "reasoning": response
            }
        
        result["raw_message"] = response
        result["agent"] = self.name
        result["emoji"] = self.emoji
        
        return result
    
    async def respond_to(self, message: DebateMessage, market_data: MarketData) -> dict:
        """
        Respond to Bull's proposal with challenge, agreement, or counter-proposal
        """
        market_context = self._format_market_context(market_data)
        
        prompt = f"""
The Bull Agent has made this proposal:
"{message.message}"

Bull's confidence: {message.confidence}

{market_context}

Analyze the Bull's proposal critically:
1. Is this a good trade? What are the risks?
2. Is the order book supportive or thin?
3. Are there warning signs Bull is ignoring?

Respond with CHALLENGE, AGREE, or COUNTER_PROPOSE as appropriate.
Be specific about your concerns or support.
"""
        
        response = await self._call_llm(prompt)
        result = self._extract_json(response)
        
        if result is None:
            result = {
                "action": "CHALLENGE",
                "confidence": 0.6,
                "reasoning": response
            }
        
        result["raw_message"] = response
        result["agent"] = self.name
        result["emoji"] = self.emoji
        
        return result
    
    def format_response_message(self, analysis: dict) -> str:
        """Format response into readable message for UI"""
        action = analysis.get("action", "CHALLENGE")
        confidence = analysis.get("confidence", 0.5)
        reasoning = analysis.get("reasoning", "")
        
        if action == "CHALLENGE":
            concerns = analysis.get("key_concerns", [])
            concerns_text = ", ".join(concerns) if concerns else ""
            return (
                f"⚠️ **CHALLENGE** (Confidence: {confidence*100:.0f}%)\n"
                f"{reasoning}\n"
                f"{'Key concerns: ' + concerns_text if concerns_text else ''}"
            )
        elif action == "AGREE":
            return f"✅ **AGREE** (Confidence: {confidence*100:.0f}%) - {reasoning}"
        elif action == "COUNTER_PROPOSE":
            proposal = analysis.get("proposal", {})
            return (
                f"🔄 **COUNTER-PROPOSAL: SHORT**\n"
                f"Confidence: {confidence*100:.0f}%\n"
                f"{reasoning}"
            )
        else:
            return f"🤔 {reasoning}"


# Singleton instance
bear_agent = BearAgent()
