from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import os

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Routes
@app.get("/")
async def root():
    return {
        "message": "WaveRider Backend API",
        "version": "0.1.0",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "docs": "/api/docs",
            "agents": "/api/agents",
            "projects": "/api/projects",
            "websocket": "/ws"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "active",
            "websocket": "active",
            "ai_agents": "ready"
        }
    }

@app.get("/api/agents")
async def get_agents():
    return {
        "agents": [
            {
                "id": "planner-001",
                "name": "Planner Agent",
                "type": "planner",
                "status": "active",
                "description": "Breaks down tasks and creates development plans"
            },
            {
                "id": "coder-001", 
                "name": "Coder Agent",
                "type": "coder",
                "status": "active",
                "description": "Generates and modifies code based on requirements"
            },
            {
                "id": "debugger-001",
                "name": "Debugger Agent", 
                "type": "debugger",
                "status": "active",
                "description": "Identifies and fixes bugs in code"
            },
            {
                "id": "optimizer-001",
                "name": "Optimizer Agent",
                "type": "optimizer", 
                "status": "ready",
                "description": "Optimizes code for performance and efficiency"
            }
        ]
    }

@app.post("/api/agents/execute")
async def execute_agent_task(task_data: Dict[str, Any]):
    task = task_data.get("task", "")
    agent_type = task_data.get("agent", "planner")
    
    # Simulate agent execution
    await asyncio.sleep(1)
    
    result = {
        "task_id": f"task_{datetime.now().timestamp()}",
        "agent": agent_type,
        "task": task,
        "status": "completed",
        "result": f"✅ {agent_type.title()} Agent completed: {task}",
        "timestamp": datetime.now().isoformat()
    }
    
    # Broadcast to all connected WebSocket clients
    await manager.broadcast(json.dumps(result))
    
    return result

@app.get("/api/projects")
async def get_projects():
    return {
        "projects": [
            {
                "id": "demo-project",
                "name": "WaveRider Demo",
                "description": "Demo project showcasing AI-powered development",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "agents_assigned": ["planner-001", "coder-001", "debugger-001"]
            }
        ]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo back the message with agent response
            response = {
                "type": "agent_response",
                "message": f"🤖 AI Agent received: {message_data.get('message', '')}",
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
