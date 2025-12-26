"""
WEEX API Client for REST and WebSocket connections
Based on official WEEX API documentation: https://www.weex.com/api-doc/ai/intro
"""
import hmac
import hashlib
import base64
import time
import json
import asyncio
from typing import Optional, Callable, Dict, List, Any
from datetime import datetime
import httpx
import websockets
from config.settings import settings
from data.data_models import (
    Candle, OrderBook, OrderBookLevel, Ticker, OrderSide
)


# Allowed trading pairs in the competition
ALLOWED_SYMBOLS = [
    "cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt",
    "cmt_xrpusdt", "cmt_adausdt", "cmt_bnbusdt", "cmt_ltcusdt"
]


class WEEXClient:
    """
    WEEX Exchange API Client
    Handles both REST API calls and WebSocket subscriptions
    Based on official documentation: https://www.weex.com/api-doc/ai/intro
    """
    
    def __init__(self):
        self.api_key = settings.weex_api_key
        self.secret_key = settings.weex_api_secret
        self.passphrase = settings.weex_passphrase
        self.base_url = "https://api-contract.weex.com"
        self.ws_url = "wss://ws-contract.weex.com/ws"
        self._ws_connection = None
        self._ws_callbacks: Dict[str, List[Callable]] = {}
        # Headers to bypass Cloudflare protection
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
    
    def _generate_signature_get(
        self, 
        timestamp: str, 
        method: str, 
        request_path: str, 
        query_string: str = ""
    ) -> str:
        """Generate HMAC-SHA256 signature for GET requests"""
        message = timestamp + method.upper() + request_path + query_string
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _generate_signature_post(
        self, 
        timestamp: str, 
        method: str, 
        request_path: str, 
        query_string: str,
        body: str
    ) -> str:
        """Generate HMAC-SHA256 signature for POST requests"""
        message = timestamp + method.upper() + request_path + query_string + body
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _get_headers(
        self, 
        method: str, 
        request_path: str, 
        query_string: str = "",
        body: str = ""
    ) -> dict:
        """Generate authentication headers for API requests"""
        timestamp = str(int(time.time() * 1000))
        
        if method.upper() == "GET":
            signature = self._generate_signature_get(
                timestamp, method, request_path, query_string
            )
        else:
            signature = self._generate_signature_post(
                timestamp, method, request_path, query_string, body
            )
        
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }
    
    # ==================== Public API Methods (No Auth) ====================
    
    async def get_ticker(self, symbol: str = "cmt_btcusdt") -> Ticker:
        """Get current ticker for a symbol"""
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self._default_headers) as client:
                response = await client.get(
                    f"{self.base_url}/capi/v2/market/ticker",
                    params={"symbol": symbol}
                )
                print(f"📈 WEEX Ticker Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   Error: {response.text[:200]}")
                    raise Exception(f"API error: {response.status_code}")
                
                data = response.json()
                print(f"   Ticker data keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                
                # Handle different response structures
                if isinstance(data, dict) and "data" in data:
                    data = data["data"]
                
                return Ticker(
                    symbol=symbol,
                    last_price=float(data.get("last", data.get("lastPr", 0))),
                    bid=float(data.get("best_bid", data.get("bidPr", 0))),
                    ask=float(data.get("best_ask", data.get("askPr", 0))),
                    volume_24h=float(data.get("volume_24h", data.get("baseVolume", 0))),
                    change_24h=0,
                    change_pct_24h=float(data.get("priceChangePercent", data.get("change24h", 0))),
                    high_24h=float(data.get("high_24h", data.get("high24h", 0))),
                    low_24h=float(data.get("low_24h", data.get("low24h", 0))),
                    timestamp=datetime.now()
                )
        except Exception as e:
            print(f"❌ Error fetching ticker: {e}")
            raise
    
    async def get_klines(
        self, 
        symbol: str = "cmt_btcusdt", 
        interval: str = "5m", 
        limit: int = 100
    ) -> List[Candle]:
        """Get historical candlestick data"""
        # Map interval to WEEX format
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1H", "4h": "4H", "1d": "1D"
        }
        weex_interval = interval_map.get(interval, "5m")
        
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self._default_headers) as client:
                url = f"{self.base_url}/capi/v2/market/candles"
                params = {
                    "symbol": symbol,
                    "granularity": weex_interval,
                    "limit": limit
                }
                print(f"📊 WEEX Klines Request: {url} with params {params}")
                
                response = await client.get(url, params=params)
                print(f"   Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   Error: {response.text[:200]}")
                    raise Exception(f"API error: {response.status_code}")
                
                raw_data = response.text
                print(f"   Raw response (first 200 chars): {raw_data[:200]}")
                
                data = response.json()
                
                # Handle different response structures
                candle_list = []
                if isinstance(data, list):
                    candle_list = data
                elif isinstance(data, dict):
                    candle_list = data.get("data", [])
                    if not candle_list:
                        print(f"   Response structure: {list(data.keys())}")
                
                print(f"   Found {len(candle_list)} candles")
                
                candles = []
                for item in candle_list:
                    try:
                        candles.append(Candle(
                            timestamp=datetime.fromtimestamp(int(item[0]) / 1000),
                            open=float(item[1]),
                            high=float(item[2]),
                            low=float(item[3]),
                            close=float(item[4]),
                            volume=float(item[5]) if len(item) > 5 else 0
                        ))
                    except (IndexError, ValueError) as e:
                        print(f"   Error parsing candle: {item} - {e}")
                        continue
                
                return candles
        except Exception as e:
            print(f"❌ Error fetching klines: {e}")
            raise
    
    async def get_orderbook(self, symbol: str = "cmt_btcusdt", depth: int = 20) -> OrderBook:
        """Get order book snapshot"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/capi/v2/market/depth",
                params={"symbol": symbol, "limit": depth}
            )
            data = response.json()
            
            bids = [
                OrderBookLevel(price=float(b[0]), quantity=float(b[1]))
                for b in data.get("bids", [])
            ]
            asks = [
                OrderBookLevel(price=float(a[0]), quantity=float(a[1]))
                for a in data.get("asks", [])
            ]
            
            return OrderBook(
                symbol=symbol,
                timestamp=datetime.now(),
                bids=bids,
                asks=asks
            )
    
    async def get_contract_info(self, symbol: str = "cmt_btcusdt") -> dict:
        """Get contract specifications (precision, limits, etc.)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/capi/v2/market/contracts",
                params={"symbol": symbol}
            )
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
    
    async def get_funding_rate(self, symbol: str = "cmt_btcusdt") -> float:
        """Get current funding rate for perpetual contracts"""
        # Funding rate may be included in ticker or separate endpoint
        ticker = await self.get_ticker(symbol)
        # WEEX may include this in the ticker response
        return 0.0  # Default if not available
    
    # ==================== Private API Methods (Auth Required) ====================
    
    async def get_account_balance(self) -> dict:
        """Get account balance (assets)"""
        request_path = "/capi/v2/account/assets"
        query_string = ""
        headers = self._get_headers("GET", request_path, query_string)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{request_path}",
                headers=headers
            )
            return response.json()
    
    async def set_leverage(
        self, 
        symbol: str, 
        leverage: int,
        margin_mode: int = 1  # 1 = cross margin
    ) -> dict:
        """Set leverage for a symbol (max 20x in competition)"""
        # Enforce 20x limit
        leverage = min(leverage, 20)
        
        request_path = "/capi/v2/account/leverage"
        body = {
            "symbol": symbol,
            "marginMode": margin_mode,
            "longLeverage": str(leverage),
            "shortLeverage": str(leverage)
        }
        body_str = json.dumps(body)
        headers = self._get_headers("POST", request_path, "", body_str)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{request_path}",
                headers=headers,
                content=body_str
            )
            return response.json()
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        size: float,
        leverage: int = 1,
        price: Optional[float] = None,
        order_type: str = "limit",  # "limit" or "market"
        client_oid: Optional[str] = None
    ) -> dict:
        """
        Place a new order
        
        Args:
            symbol: Trading pair (e.g., "cmt_btcusdt")
            side: OrderSide.BUY (long) or OrderSide.SELL (short)
            size: Order size in base currency (e.g., 0.0001 BTC)
            leverage: Leverage (max 20x)
            price: Limit price (required for limit orders)
            order_type: "limit" or "market"
            client_oid: Custom order ID
        """
        # Validate symbol
        if symbol not in ALLOWED_SYMBOLS:
            raise ValueError(f"Symbol {symbol} not allowed. Use one of: {ALLOWED_SYMBOLS}")
        
        # Enforce leverage limit
        leverage = min(leverage, 20)
        
        # Set leverage first
        await self.set_leverage(symbol, leverage)
        
        request_path = "/capi/v2/order/placeOrder"
        
        # type: 1=open long, 2=open short, 3=close long, 4=close short
        if side == OrderSide.BUY:
            order_direction = "1"  # Open long
        else:
            order_direction = "2"  # Open short
        
        body = {
            "symbol": symbol,
            "size": str(size),
            "type": order_direction,
            "order_type": "0" if order_type == "limit" else "1",  # 0=limit, 1=market
            "match_price": "1" if order_type == "market" else "0",
        }
        
        if client_oid:
            body["client_oid"] = client_oid
        
        if price and order_type == "limit":
            body["price"] = str(price)
        
        body_str = json.dumps(body)
        headers = self._get_headers("POST", request_path, "", body_str)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{request_path}",
                headers=headers,
                content=body_str
            )
            return response.json()
    
    async def cancel_order(self, symbol: str, order_id: str) -> dict:
        """Cancel an existing order"""
        request_path = "/capi/v2/order/cancelOrder"
        body = {"symbol": symbol, "orderId": order_id}
        body_str = json.dumps(body)
        headers = self._get_headers("POST", request_path, "", body_str)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{request_path}",
                headers=headers,
                content=body_str
            )
            return response.json()
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[dict]:
        """Get open orders"""
        request_path = "/capi/v2/order/openOrders"
        query_string = f"?symbol={symbol}" if symbol else ""
        headers = self._get_headers("GET", request_path, query_string)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{request_path}{query_string}",
                headers=headers
            )
            data = response.json()
            return data.get("list", []) if isinstance(data, dict) else data
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[dict]:
        """Get open positions"""
        request_path = "/capi/v2/position/allPosition"
        query_string = f"?symbol={symbol}" if symbol else ""
        headers = self._get_headers("GET", request_path, query_string)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{request_path}{query_string}",
                headers=headers
            )
            data = response.json()
            return data.get("list", []) if isinstance(data, dict) else data
    
    async def get_trade_history(
        self, 
        symbol: str, 
        order_id: Optional[str] = None
    ) -> List[dict]:
        """Get trade fills/history"""
        request_path = "/capi/v2/order/fills"
        query_string = f"?symbol={symbol}"
        if order_id:
            query_string += f"&orderId={order_id}"
        
        headers = self._get_headers("GET", request_path, query_string)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{request_path}{query_string}",
                headers=headers
            )
            data = response.json()
            return data.get("list", []) if isinstance(data, dict) else data
    
    async def close_position(
        self,
        symbol: str,
        side: OrderSide,
        size: float
    ) -> dict:
        """Close a position"""
        request_path = "/capi/v2/order/placeOrder"
        
        # Close direction is opposite of position
        if side == OrderSide.BUY:
            order_direction = "3"  # Close long
        else:
            order_direction = "4"  # Close short
        
        body = {
            "symbol": symbol,
            "size": str(size),
            "type": order_direction,
            "order_type": "1",  # Market order for closing
            "match_price": "1",
        }
        
        body_str = json.dumps(body)
        headers = self._get_headers("POST", request_path, "", body_str)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{request_path}",
                headers=headers,
                content=body_str
            )
            return response.json()
    
    # ==================== WebSocket Methods ====================
    
    async def connect_websocket(self):
        """Establish WebSocket connection"""
        self._ws_connection = await websockets.connect(self.ws_url)
        asyncio.create_task(self._ws_listener())
    
    async def _ws_listener(self):
        """Listen for WebSocket messages"""
        try:
            async for message in self._ws_connection:
                data = json.loads(message)
                channel = data.get("channel", "")
                
                # Dispatch to registered callbacks
                if channel in self._ws_callbacks:
                    for callback in self._ws_callbacks[channel]:
                        await callback(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
    
    async def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a WebSocket channel"""
        if channel not in self._ws_callbacks:
            self._ws_callbacks[channel] = []
        self._ws_callbacks[channel].append(callback)
        
        if self._ws_connection:
            await self._ws_connection.send(json.dumps({
                "op": "subscribe",
                "args": [channel]
            }))
    
    async def close(self):
        """Close WebSocket connection"""
        if self._ws_connection:
            await self._ws_connection.close()


# Create singleton instance
weex_client = WEEXClient()
