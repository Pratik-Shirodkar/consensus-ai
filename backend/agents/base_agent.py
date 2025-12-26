"""
Base agent class for all AI agents
Uses AWS Bedrock for LLM inference
"""
import json
import re
import boto3
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from config.settings import settings
from data.data_models import MarketData, DebateMessage


class BaseAgent(ABC):
    """Abstract base class for all trading agents"""
    
    def __init__(self, name: str, emoji: str, prompt_file: str):
        self.name = name
        self.emoji = emoji
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.model_id = settings.bedrock_model_id
        self.system_prompt = self._load_prompt(prompt_file)
        self.message_history = []
        
    def _load_prompt(self, filename: str) -> str:
        """Load system prompt from file"""
        try:
            with open(f"agents/prompts/{filename}", "r") as f:
                return f.read()
        except FileNotFoundError:
            return f"You are the {self.name} agent."
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response"""
        # Try to find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to parse entire response as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find any JSON-like structure
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _format_market_context(self, market_data: MarketData) -> str:
        """Format market data for LLM context"""
        ticker = market_data.ticker
        orderbook = market_data.orderbook
        
        context = f"""
CURRENT MARKET DATA for {market_data.symbol}:
- Current Price: ${ticker.last_price:,.2f}
- 24h Change: {ticker.change_pct_24h:+.2f}%
- 24h High: ${ticker.high_24h:,.2f}
- 24h Low: ${ticker.low_24h:,.2f}
- 24h Volume: ${ticker.volume_24h:,.0f}
- Bid: ${ticker.bid:,.2f} | Ask: ${ticker.ask:,.2f}
- Spread: {orderbook.spread_pct:.4f}%
- Funding Rate: {market_data.funding_rate * 100:.4f}%

ORDER BOOK DEPTH:
- Top 3 Bids: {', '.join([f'${b.price:,.0f} ({b.quantity:.2f})' for b in orderbook.bids[:3]])}
- Top 3 Asks: {', '.join([f'${a.price:,.0f} ({a.quantity:.2f})' for a in orderbook.asks[:3]])}
"""
        return context
    
    def _format_signals(self, signals: list) -> str:
        """Format technical signals for LLM context"""
        if not signals:
            return "No signals available."
        
        lines = ["TECHNICAL SIGNALS:"]
        for signal in signals:
            lines.append(f"- {signal.name}: {signal.value:.2f} ({signal.signal.value}) - {signal.description}")
        return "\n".join(lines)
    
    async def _call_llm(self, user_message: str) -> str:
        """Make LLM API call via AWS Bedrock"""
        
        try:
            # Build messages array
            messages = [
                *self.message_history,
                {"role": "user", "content": user_message}
            ]
            
            # Prepare the request body for Claude
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": self.system_prompt,
                "messages": messages,
                "temperature": 0.7
            })
            
            print(f"[{self.name}] Calling Bedrock model: {self.model_id}")
            
            # Invoke Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            assistant_message = response_body['content'][0]['text']
            
            # Add to history for context
            self.message_history.append({"role": "user", "content": user_message})
            self.message_history.append({"role": "assistant", "content": assistant_message})
            
            # Keep history manageable
            if len(self.message_history) > 10:
                self.message_history = self.message_history[-10:]
            
            return assistant_message
            
        except Exception as e:
            error_msg = str(e)
            print(f"[{self.name}] Bedrock API Error: {error_msg}")
            
            # Check for common issues
            if "AccessDeniedException" in error_msg:
                raise Exception(
                    f"AWS Bedrock Access Denied. You need to request access to {self.model_id} "
                    f"in the AWS Console: https://console.aws.amazon.com/bedrock/home?region={settings.aws_region}#/modelaccess"
                )
            elif "ValidationException" in error_msg:
                raise Exception(f"Invalid model ID or request format: {error_msg}")
            elif "ResourceNotFoundException" in error_msg:
                raise Exception(
                    f"Model {self.model_id} not found. Check if it's available in region {settings.aws_region}"
                )
            else:
                raise Exception(f"Bedrock API Error: {error_msg}")
    
    def create_message(self, content: str, confidence: float = None) -> DebateMessage:
        """Create a debate message from this agent"""
        return DebateMessage(
            agent=self.name,
            emoji=self.emoji,
            message=content,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    @abstractmethod
    async def analyze(self, market_data: MarketData, signals: list) -> dict:
        """Analyze market data and return opinion"""
        pass
    
    @abstractmethod
    async def respond_to(self, message: DebateMessage, market_data: MarketData) -> dict:
        """Respond to another agent's message"""
        pass
    
    def clear_history(self):
        """Clear conversation history"""
        self.message_history = []
