"""
Debate Engine - Orchestrates multi-agent debate workflow
"""
import asyncio
from typing import List, Optional, Callable
from datetime import datetime
from data.data_models import MarketData, DebateMessage, TradeDecision
from data.market_data import market_data_service
from signals.indicators import indicator_analyzer
from agents.bull_agent import bull_agent
from agents.bear_agent import bear_agent
from agents.risk_manager import risk_manager
from config.settings import settings


class DebateEngine:
    """
    Orchestrates the debate between Bull, Bear, and Risk Manager agents.
    Manages the workflow: Proposal → Rebuttal → Resolution
    """
    
    def __init__(self):
        self.bull = bull_agent
        self.bear = bear_agent
        self.risk = risk_manager
        self.debate_history: List[DebateMessage] = []
        self.trade_count = 0
        self.message_callbacks: List[Callable] = []
        self.is_running = False
        self.current_exposure_pct = 0.0
    
    def add_message_callback(self, callback: Callable):
        """Add callback to be called when new debate message is generated"""
        self.message_callbacks.append(callback)
    
    async def _broadcast_message(self, message: DebateMessage):
        """Broadcast message to all registered callbacks"""
        self.debate_history.append(message)
        for callback in self.message_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                print(f"Error in message callback: {e}")
    
    async def run_debate_cycle(self, symbol: str = None) -> Optional[TradeDecision]:
        """
        Run a complete debate cycle:
        1. Bull analyzes and may propose
        2. Bear responds to Bull
        3. Risk Manager makes final decision
        4. Return trade decision (or None if no trade)
        """
        symbol = symbol or settings.default_symbol
        
        try:
            # Fetch market data
            market_data = await market_data_service.get_market_data(symbol)
            
            # Calculate technical signals
            signals = indicator_analyzer.analyze(market_data.candles)
            
            # === PHASE 1: Bull Analysis ===
            bull_analysis = await self.bull.analyze(market_data, signals)
            bull_message = DebateMessage(
                agent="Bull",
                emoji="🐂",
                message=self.bull.format_proposal_message(bull_analysis),
                confidence=bull_analysis.get("confidence"),
                timestamp=datetime.now()
            )
            await self._broadcast_message(bull_message)
            
            # If Bull is just holding, no debate needed
            if bull_analysis.get("action") == "HOLD":
                return None
            
            # === PHASE 2: Bear Response ===
            await asyncio.sleep(0.5)  # Brief pause for realistic feel
            
            bear_analysis = await self.bear.respond_to(bull_message, market_data)
            bear_message = DebateMessage(
                agent="Bear",
                emoji="🐻",
                message=self.bear.format_response_message(bear_analysis),
                confidence=bear_analysis.get("confidence"),
                timestamp=datetime.now()
            )
            await self._broadcast_message(bear_message)
            
            # === PHASE 3: Risk Manager Arbitration ===
            await asyncio.sleep(0.5)
            
            decision = await self.risk.arbitrate(
                bull_analysis,
                bear_analysis,
                market_data,
                self.current_exposure_pct
            )
            risk_message = DebateMessage(
                agent="Risk Manager",
                emoji="⚖️",
                message=self.risk.format_decision_message(decision),
                confidence=None,
                timestamp=datetime.now()
            )
            await self._broadcast_message(risk_message)
            
            # Convert to TradeDecision if approved
            if decision.get("decision") in ["APPROVE", "MODIFY"]:
                self.trade_count += 1
                return self.risk.to_trade_decision(decision, symbol)
            
            return None
            
        except Exception as e:
            error_message = DebateMessage(
                agent="System",
                emoji="⚠️",
                message=f"Debate error: {str(e)}",
                timestamp=datetime.now()
            )
            await self._broadcast_message(error_message)
            return None
    
    async def run_continuous(
        self, 
        symbol: str = None,
        interval_seconds: int = None
    ):
        """
        Run continuous debate cycles
        """
        symbol = symbol or settings.default_symbol
        interval = interval_seconds or settings.debate_interval_seconds
        
        self.is_running = True
        
        while self.is_running:
            try:
                decision = await self.run_debate_cycle(symbol)
                
                if decision and decision.approved:
                    # Here you would execute the trade
                    print(f"Trade #{self.trade_count}: {decision}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"Error in debate cycle: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    def stop(self):
        """Stop continuous debate"""
        self.is_running = False
    
    def get_debate_history(self, limit: int = 50) -> List[DebateMessage]:
        """Get recent debate messages"""
        return self.debate_history[-limit:]
    
    def get_stats(self) -> dict:
        """Get debate statistics"""
        return {
            "total_debates": len([m for m in self.debate_history if m.agent == "Risk Manager"]),
            "total_trades": self.trade_count,
            "messages_count": len(self.debate_history),
            "is_running": self.is_running
        }
    
    def clear_history(self):
        """Clear debate history"""
        self.debate_history = []
        self.bull.clear_history()
        self.bear.clear_history()
        self.risk.clear_history()


# Singleton instance
debate_engine = DebateEngine()
