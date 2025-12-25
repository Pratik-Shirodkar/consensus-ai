"""
Consensus AI - Multi-Agent Investment Committee
FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.routes import router
from api.websocket import websocket_endpoint
from config.settings import settings


# Create FastAPI app
app = FastAPI(
    title="Consensus AI",
    description="Multi-Agent Investment Committee - AI agents debate before trading",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(router)

# WebSocket endpoint
app.websocket("/ws/debate")(websocket_endpoint)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Consensus AI",
        "description": "Multi-Agent Investment Committee",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws/debate"
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Consensus AI starting up...")
    print(f"📊 Default symbol: {settings.default_symbol}")
    print(f"⚡ Max leverage: {settings.max_leverage}x")
    print(f"📡 API running at http://{settings.host}:{settings.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    from agents.debate_engine import debate_engine
    debate_engine.stop()
    print("👋 Consensus AI shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
