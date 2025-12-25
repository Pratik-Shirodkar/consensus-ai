"""
WebSocket endpoint for real-time debate streaming
"""
import asyncio
import json
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from data.data_models import DebateMessage
from agents.debate_engine import debate_engine


class ConnectionManager:
    """
    Manages WebSocket connections for real-time debate streaming
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and track new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send recent history to new connection
        history = debate_engine.get_debate_history(20)
        for message in history:
            await self.send_message(websocket, message)
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_message(self, websocket: WebSocket, message: DebateMessage):
        """Send a message to a specific client"""
        try:
            await websocket.send_json({
                "type": "debate_message",
                "agent": message.agent,
                "emoji": message.emoji,
                "message": message.message,
                "confidence": message.confidence,
                "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error sending to websocket: {e}")
    
    async def broadcast(self, message: DebateMessage):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for websocket in self.active_connections:
            try:
                await self.send_message(websocket, message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_status(self, status: dict):
        """Broadcast status update to all clients"""
        disconnected = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json({
                    "type": "status_update",
                    **status
                })
            except Exception:
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)


# Global connection manager
connection_manager = ConnectionManager()


# Register broadcast callback with debate engine
async def broadcast_callback(message: DebateMessage):
    """Callback to broadcast debate messages"""
    await connection_manager.broadcast(message)

debate_engine.add_message_callback(broadcast_callback)


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time debate streaming
    """
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif msg_type == "trigger_debate":
                    # Allow client to trigger a debate cycle
                    symbol = message.get("symbol")
                    asyncio.create_task(
                        debate_engine.run_debate_cycle(symbol)
                    )
                
                elif msg_type == "get_history":
                    limit = message.get("limit", 20)
                    history = debate_engine.get_debate_history(limit)
                    for msg in history:
                        await connection_manager.send_message(websocket, msg)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)
