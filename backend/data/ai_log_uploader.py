"""
AI Log Uploader - Uploads AI decision logs to WEEX for hackathon compliance
Based on WEEX API documentation: POST /capi/v2/order/uploadAiLog

AI logs are REQUIRED to verify AI involvement in trading decisions.
Failure to provide valid proof of AI involvement will result in disqualification.
"""
import hmac
import hashlib
import base64
import time
import json
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from config.settings import settings


class AILogUploader:
    """
    Uploads AI decision logs to WEEX for hackathon compliance.
    
    Required fields:
    - stage: The trading stage where AI participated (e.g., "Strategy Generation", "Decision Making")
    - model: The AI model used (e.g., "Claude-3.5-sonnet")
    - input: The prompt/query given to the AI model (JSON)
    - output: The AI model's generated output (JSON)
    - explanation: A concise summary of the AI's reasoning (max 1000 chars)
    - orderId: Optional, the order ID from WEEX order API
    """
    
    def __init__(self):
        self.api_key = settings.weex_api_key
        self.secret_key = settings.weex_api_secret
        self.passphrase = settings.weex_passphrase
        self.base_url = "https://api-contract.weex.com"
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
    
    def _generate_signature(
        self,
        timestamp: str,
        method: str,
        request_path: str,
        body: str
    ) -> str:
        """Generate HMAC-SHA256 signature for POST requests"""
        message = timestamp + method.upper() + request_path + body
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _get_headers(self, request_path: str, body: str) -> dict:
        """Generate authentication headers for API requests"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, "POST", request_path, body)
        
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }
    
    async def upload_ai_log(
        self,
        stage: str,
        model: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        explanation: str,
        order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload AI log to WEEX for compliance verification.
        
        Args:
            stage: Trading stage (e.g., "Strategy Generation", "Decision Making", 
                   "Risk Assessment", "Order Execution")
            model: AI model name/version (e.g., "Claude-3.5-sonnet", "GPT-4-turbo")
            input_data: The prompt/query given to AI (dict)
            output_data: The AI's generated output (dict)
            explanation: Summary of AI reasoning (max 1000 chars)
            order_id: Optional WEEX order ID
            
        Returns:
            API response dict with code, msg, requestTime, and data fields
        """
        # Truncate explanation to 1000 chars if needed
        if len(explanation) > 1000:
            explanation = explanation[:997] + "..."
        
        request_path = "/capi/v2/order/uploadAiLog"
        
        body = {
            "orderId": order_id,
            "stage": stage,
            "model": model,
            "input": input_data,
            "output": output_data,
            "explanation": explanation
        }
        
        body_str = json.dumps(body)
        headers = {**self._default_headers, **self._get_headers(request_path, body_str)}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}{request_path}",
                    headers=headers,
                    content=body_str
                )
                
                result = response.json()
                
                if result.get("code") == "00000":
                    print(f"✅ AI Log uploaded successfully: {result.get('data')}")
                else:
                    print(f"⚠️ AI Log upload warning: {result.get('msg')}")
                
                return result
                
        except Exception as e:
            print(f"❌ Error uploading AI log: {e}")
            return {
                "code": "ERROR",
                "msg": str(e),
                "requestTime": int(time.time() * 1000),
                "data": None
            }
    
    async def log_debate_decision(
        self,
        bull_analysis: Dict[str, Any],
        bear_analysis: Dict[str, Any],
        risk_decision: Dict[str, Any],
        market_data: Dict[str, Any],
        order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload a complete debate cycle as an AI log.
        
        This is a convenience method that formats the multi-agent debate
        into the required AI log structure.
        """
        input_data = {
            "prompt": "Multi-agent debate for trading decision",
            "market_data": market_data,
            "bull_analysis": {
                "action": bull_analysis.get("action"),
                "confidence": bull_analysis.get("confidence"),
                "reasoning": bull_analysis.get("reasoning", "")[:500]
            },
            "bear_analysis": {
                "action": bear_analysis.get("action"), 
                "confidence": bear_analysis.get("confidence"),
                "reasoning": bear_analysis.get("reasoning", "")[:500]
            }
        }
        
        output_data = {
            "decision": risk_decision.get("decision"),
            "action": risk_decision.get("action"),
            "confidence": risk_decision.get("net_score"),
            "size_pct": risk_decision.get("position_size_pct"),
            "stop_loss_pct": risk_decision.get("stop_loss_pct"),
            "take_profit_pct": risk_decision.get("take_profit_pct"),
            "reasoning": risk_decision.get("reasoning", "")[:500]
        }
        
        explanation = (
            f"Consensus AI multi-agent debate system. "
            f"Bull agent proposed {bull_analysis.get('action', 'N/A')} with "
            f"{bull_analysis.get('confidence', 0):.0%} confidence. "
            f"Bear agent countered with {bear_analysis.get('action', 'N/A')} and "
            f"{bear_analysis.get('confidence', 0):.0%} confidence. "
            f"Risk Manager final decision: {risk_decision.get('decision', 'N/A')}. "
            f"{risk_decision.get('reasoning', '')[:400]}"
        )
        
        return await self.upload_ai_log(
            stage="Decision Making",
            model="Claude-3.5-sonnet (AWS Bedrock)",
            input_data=input_data,
            output_data=output_data,
            explanation=explanation,
            order_id=order_id
        )
    
    async def log_strategy_generation(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        signal: str,
        confidence: float,
        reasoning: str,
        order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload a strategy generation AI log.
        
        Use this when logging the initial strategy/signal generation phase.
        """
        input_data = {
            "prompt": f"Generate trading signal for {symbol}",
            "data": indicators
        }
        
        output_data = {
            "signal": signal,
            "confidence": confidence,
            "symbol": symbol,
            "reason": reasoning[:500]
        }
        
        explanation = (
            f"AI strategy generation for {symbol}. "
            f"Technical indicators analyzed: RSI, EMA, MACD, Bollinger Bands. "
            f"Generated signal: {signal} with {confidence:.0%} confidence. "
            f"{reasoning[:500]}"
        )
        
        return await self.upload_ai_log(
            stage="Strategy Generation",
            model="Claude-3.5-sonnet (AWS Bedrock)",
            input_data=input_data,
            output_data=output_data,
            explanation=explanation,
            order_id=order_id
        )
    
    async def log_risk_assessment(
        self,
        symbol: str,
        proposed_action: str,
        risk_factors: Dict[str, Any],
        approved: bool,
        position_size: float,
        reasoning: str,
        order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload a risk assessment AI log.
        
        Use this when logging the risk management evaluation phase.
        """
        input_data = {
            "prompt": f"Evaluate risk for {proposed_action} on {symbol}",
            "risk_factors": risk_factors
        }
        
        output_data = {
            "approved": approved,
            "position_size_pct": position_size,
            "risk_level": risk_factors.get("risk_level", "medium"),
            "reason": reasoning[:500]
        }
        
        explanation = (
            f"AI risk assessment for proposed {proposed_action} on {symbol}. "
            f"Decision: {'APPROVED' if approved else 'REJECTED'}. "
            f"Position size: {position_size:.1f}%. "
            f"{reasoning[:600]}"
        )
        
        return await self.upload_ai_log(
            stage="Risk Assessment",
            model="Claude-3.5-sonnet (AWS Bedrock)",
            input_data=input_data,
            output_data=output_data,
            explanation=explanation,
            order_id=order_id
        )


# Singleton instance
ai_log_uploader = AILogUploader()
