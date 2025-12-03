"""Main FastAPI application"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import logging
from typing import List

from .config import settings
from .api import api_router
from .models import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced Options Analytics Platform with Universal Broker Integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.now(),
        services={
            "api": "operational",
            "database": "operational",
            "redis": "operational"
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: dict = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Clean up subscriptions
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)
    
    def subscribe(self, websocket: WebSocket, symbols: List[str]):
        if websocket not in self.subscriptions:
            self.subscriptions[websocket] = set()
        self.subscriptions[websocket].update(symbols)
    
    def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket].difference_update(symbols)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time data
    
    Messages:
    - {"type": "subscribe", "symbols": ["SPY", "AAPL"]}
    - {"type": "unsubscribe", "symbols": ["SPY"]}
    - {"type": "ping"}
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "subscribe":
                symbols = data.get("symbols", [])
                manager.subscribe(websocket, symbols)
                await manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "symbols": symbols,
                        "timestamp": datetime.now().isoformat()
                    },
                    websocket
                )
            
            elif msg_type == "unsubscribe":
                symbols = data.get("symbols", [])
                manager.unsubscribe(websocket, symbols)
                await manager.send_personal_message(
                    {
                        "type": "unsubscribed",
                        "symbols": symbols,
                        "timestamp": datetime.now().isoformat()
                    },
                    websocket
                )
            
            elif msg_type == "ping":
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    },
                    websocket
                )
            
            # In a real implementation, we would:
            # 1. Connect to broker's real-time feed
            # 2. Stream quote updates to subscribed clients
            # 3. Handle market data efficiently
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"API docs available at: /docs")
    logger.info(f"Health check at: /health")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
