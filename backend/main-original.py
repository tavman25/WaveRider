from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import os
from dotenv import load_dotenv

from api.routes import auth, projects, files, ai, collaboration, agents
from core.config import settings
from core.database import engine, Base
from core.auth import verify_token
from services.websocket_manager import ConnectionManager
from services.ai_service import AIService
from services.agent_orchestrator import AgentOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="WaveRider Backend API",
    description="Agentic AI IDE Backend with autonomous coding agents",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
connection_manager = ConnectionManager()

# AI services
ai_service = AIService()
agent_orchestrator = AgentOrchestrator()

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize AI services
    await ai_service.initialize()
    await agent_orchestrator.initialize()
    
    logger.info("WaveRider Backend started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await ai_service.cleanup()
    await agent_orchestrator.cleanup()
    logger.info("WaveRider Backend shutdown completed")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["collaboration"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await connection_manager.connect(websocket, client_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "ping":
                await connection_manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                    client_id
                )
            
            elif message_type == "agent_request":
                # Forward to agent orchestrator
                await agent_orchestrator.handle_request(message, client_id)
            
            elif message_type == "collaboration":
                # Handle collaboration events
                await connection_manager.broadcast_to_room(
                    message.get("room_id", ""),
                    json.dumps(message)
                )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        connection_manager.disconnect(client_id)

# Agent communication endpoint
@app.websocket("/ws/agents/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for agent communication"""
    await agent_orchestrator.connect_agent(websocket, agent_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await agent_orchestrator.handle_agent_message(agent_id, message)
    except WebSocketDisconnect:
        await agent_orchestrator.disconnect_agent(agent_id)
    except Exception as e:
        logger.error(f"Agent WebSocket error for {agent_id}: {str(e)}")
        await agent_orchestrator.disconnect_agent(agent_id)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests"""
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
