"""
Order Manager - Handles trade execution via WEEX API
With integrated AI log upload for hackathon compliance
"""
import uuid
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from data.data_models import (
    TradeDecision, Trade, Position, OrderSide, TradeAction
)
from data.weex_client import weex_client
from data.ai_log_uploader import ai_log_uploader
from config.settings import settings


class OrderManager:
    """
    Manages order execution, position tracking, and trade logging
    """
    
    def __init__(self):
        self.positions: List[Position] = []
        self.trade_history: List[Trade] = []
        self.account_balance = settings.demo_balance  # Use configured balance
        self.demo_mode = settings.demo_mode  # Track demo mode state
    
    def set_demo_mode(self, enabled: bool):
        """Toggle demo mode"""
        self.demo_mode = enabled
        if enabled:
            # Reset to demo balance when entering demo mode
            self.account_balance = settings.demo_balance
        print(f"📊 Demo mode {'enabled' if enabled else 'disabled'}")
    
    async def execute_trade(
        self, 
        decision: TradeDecision,
        debate_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Trade]:
        """
        Execute a trade based on Risk Manager's decision.
        Automatically uploads AI log to WEEX for hackathon compliance.
        
        Args:
            decision: The approved TradeDecision from Risk Manager
            debate_context: Optional dict with bull_analysis, bear_analysis for AI logging
        """
        if not decision.approved:
            return None
        
        order_id = None
        
        try:
            # Calculate position size
            size_usd = self.account_balance * (decision.size_pct / 100)
            
            # Get current price
            ticker = await weex_client.get_ticker(decision.symbol)
            current_price = ticker.last_price
            
            # Calculate quantity
            quantity = size_usd / current_price
            
            # Determine order side
            side = OrderSide.BUY if decision.action == TradeAction.LONG else OrderSide.SELL
            
            # Calculate stop-loss and take-profit prices
            if decision.action == TradeAction.LONG:
                stop_loss_price = current_price * (1 - decision.stop_loss_pct / 100)
                take_profit_price = current_price * (1 + decision.take_profit_pct / 100)
            else:
                stop_loss_price = current_price * (1 + decision.stop_loss_pct / 100)
                take_profit_price = current_price * (1 - decision.take_profit_pct / 100)
            
            # Place order via WEEX API (only in live mode)
            if not self.demo_mode:
                order_result = await weex_client.place_order(
                    symbol=decision.symbol,
                    side=side,
                    size=quantity,
                    leverage=decision.leverage,
                    stop_loss=stop_loss_price,
                    take_profit=take_profit_price
                )
                # Extract order ID for AI log
                order_id = order_result.get("order_id") or order_result.get("orderId")
            else:
                print(f"📝 [DEMO] Simulated order: {side.value} {quantity:.6f} {decision.symbol} @ ${current_price:.2f}")
            
            # Create trade record
            trade = Trade(
                id=str(uuid.uuid4()),
                symbol=decision.symbol,
                side=side,
                action=decision.action,
                size=quantity,
                price=current_price,
                leverage=decision.leverage,
                reasoning=decision.reasoning,
                executed_at=datetime.now()
            )
            
            # Create position
            position = Position(
                symbol=decision.symbol,
                side=side,
                size=quantity,
                entry_price=current_price,
                current_price=current_price,
                leverage=decision.leverage,
                unrealized_pnl=0,
                unrealized_pnl_pct=0,
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                opened_at=datetime.now()
            )
            
            self.positions.append(position)
            self.trade_history.append(trade)
            
            # Upload AI log for hackathon compliance (non-blocking)
            asyncio.create_task(self._upload_trade_ai_log(
                decision=decision,
                current_price=current_price,
                order_id=order_id,
                debate_context=debate_context
            ))
            
            return trade
            
        except Exception as e:
            print(f"Error executing trade: {e}")
            return None
    
    async def _upload_trade_ai_log(
        self,
        decision: TradeDecision,
        current_price: float,
        order_id: Optional[int] = None,
        debate_context: Optional[Dict[str, Any]] = None
    ):
        """
        Upload AI log to WEEX for hackathon compliance.
        This runs in the background to not block trade execution.
        """
        try:
            input_data = {
                "prompt": f"Evaluate trading opportunity for {decision.symbol}",
                "market_data": {
                    "symbol": decision.symbol,
                    "price": current_price
                }
            }
            
            # Include debate context if provided
            if debate_context:
                if "bull_analysis" in debate_context:
                    input_data["bull_analysis"] = {
                        "action": debate_context["bull_analysis"].get("action"),
                        "confidence": debate_context["bull_analysis"].get("confidence"),
                        "reasoning": str(debate_context["bull_analysis"].get("reasoning", ""))[:300]
                    }
                if "bear_analysis" in debate_context:
                    input_data["bear_analysis"] = {
                        "action": debate_context["bear_analysis"].get("action"),
                        "confidence": debate_context["bear_analysis"].get("confidence"),
                        "reasoning": str(debate_context["bear_analysis"].get("reasoning", ""))[:300]
                    }
            
            output_data = {
                "decision": "APPROVE" if decision.approved else "REJECT",
                "action": decision.action.value if hasattr(decision.action, 'value') else str(decision.action),
                "position_size_pct": decision.size_pct,
                "leverage": decision.leverage,
                "stop_loss_pct": decision.stop_loss_pct,
                "take_profit_pct": decision.take_profit_pct,
                "entry_price": current_price
            }
            
            explanation = (
                f"Consensus AI multi-agent system executed {decision.action} on {decision.symbol} at ${current_price:.2f}. "
                f"Position size: {decision.size_pct:.1f}% with {decision.leverage}x leverage. "
                f"Stop-loss: {decision.stop_loss_pct:.1f}%, Take-profit: {decision.take_profit_pct:.1f}%. "
                f"{decision.reasoning[:500] if decision.reasoning else ''}"
            )
            
            await ai_log_uploader.upload_ai_log(
                stage="Order Execution",
                model="Claude-3.5-sonnet (AWS Bedrock)",
                input_data=input_data,
                output_data=output_data,
                explanation=explanation,
                order_id=int(order_id) if order_id else None
            )
            
        except Exception as e:
            print(f"⚠️ Failed to upload AI log (non-critical): {e}")
    
    async def close_position(
        self, 
        symbol: str, 
        reason: str = "Manual close"
    ) -> Optional[Trade]:
        """
        Close an open position
        """
        position = next(
            (p for p in self.positions if p.symbol == symbol), 
            None
        )
        
        if not position:
            return None
        
        try:
            # Get current price
            ticker = await weex_client.get_ticker(symbol)
            current_price = ticker.last_price
            
            # Calculate P&L
            if position.side == OrderSide.BUY:
                pnl = (current_price - position.entry_price) * position.size
                pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
            else:
                pnl = (position.entry_price - current_price) * position.size
                pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
            
            # Account for leverage
            pnl_pct *= position.leverage
            
            # Close order side is opposite
            close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            
            # Place close order
            await weex_client.place_order(
                symbol=symbol,
                side=close_side,
                size=position.size,
                leverage=position.leverage
            )
            
            # Create close trade record
            trade = Trade(
                id=str(uuid.uuid4()),
                symbol=symbol,
                side=close_side,
                action=TradeAction.CLOSE,
                size=position.size,
                price=current_price,
                leverage=position.leverage,
                pnl=pnl,
                pnl_pct=pnl_pct,
                reasoning=reason,
                executed_at=datetime.now()
            )
            
            # Update account balance
            self.account_balance += pnl
            
            # Remove position
            self.positions = [p for p in self.positions if p.symbol != symbol]
            
            self.trade_history.append(trade)
            
            return trade
            
        except Exception as e:
            print(f"Error closing position: {e}")
            return None
    
    async def update_positions(self):
        """
        Update all position prices and P&L
        """
        for position in self.positions:
            try:
                ticker = await weex_client.get_ticker(position.symbol)
                position.current_price = ticker.last_price
                
                if position.side == OrderSide.BUY:
                    pnl = (position.current_price - position.entry_price) * position.size
                    pnl_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
                else:
                    pnl = (position.entry_price - position.current_price) * position.size
                    pnl_pct = ((position.entry_price - position.current_price) / position.entry_price) * 100
                
                position.unrealized_pnl = pnl
                position.unrealized_pnl_pct = pnl_pct * position.leverage
                
            except Exception as e:
                print(f"Error updating position {position.symbol}: {e}")
    
    def get_total_exposure(self) -> float:
        """
        Calculate total portfolio exposure
        """
        total = sum(
            p.size * p.current_price * p.leverage 
            for p in self.positions
        )
        return (total / self.account_balance) * 100 if self.account_balance > 0 else 0
    
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        return self.positions
    
    def get_trade_history(self, limit: int = 50) -> List[Trade]:
        """Get recent trade history"""
        return self.trade_history[-limit:]
    
    def get_stats(self) -> dict:
        """Get trading statistics"""
        total_trades = len(self.trade_history)
        winning_trades = len([t for t in self.trade_history if t.pnl and t.pnl > 0])
        total_pnl = sum(t.pnl or 0 for t in self.trade_history)
        
        return {
            "account_balance": self.account_balance,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "open_positions": len(self.positions),
            "total_exposure_pct": self.get_total_exposure()
        }


# Singleton instance
order_manager = OrderManager()
