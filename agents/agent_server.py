from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import os

from core.agent_manager import AgentManager
from core.langgraph_orchestrator import LangGraphOrchestrator
from agents.planner_agent import PlannerAgent
from agents.coder_agent import CoderAgent
from agents.debugger_agent import DebuggerAgent
from agents.optimizer_agent import OptimizerAgent
from agents.reviewer_agent import ReviewerAgent
from services.context_manager import ContextManager
from services.tool_registry import ToolRegistry
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(__name__)

# Create FastAPI app for agents
app = FastAPI(
    title="WaveRider Agent Server",
    description="Autonomous AI Agents for Code Generation, Planning, and Optimization",
    version="0.1.0",
    docs_url="/agents/docs",
    redoc_url="/agents/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
agent_manager: Optional[AgentManager] = None
orchestrator: Optional[LangGraphOrchestrator] = None
context_manager: Optional[ContextManager] = None
tool_registry: Optional[ToolRegistry] = None

@app.on_event("startup")
async def startup_event():
    """Initialize all agents and services on startup"""
    global agent_manager, orchestrator, context_manager, tool_registry
    
    try:
        # Initialize core services
        context_manager = ContextManager()
        tool_registry = ToolRegistry()
        
        # Initialize agents
        planner = PlannerAgent(context_manager, tool_registry)
        coder = CoderAgent(context_manager, tool_registry)
        debugger = DebuggerAgent(context_manager, tool_registry)
        optimizer = OptimizerAgent(context_manager, tool_registry)
        reviewer = ReviewerAgent(context_manager, tool_registry)
        
        # Register agents
        agent_manager = AgentManager()
        await agent_manager.register_agent("planner", planner)
        await agent_manager.register_agent("coder", coder)
        await agent_manager.register_agent("debugger", debugger)
        await agent_manager.register_agent("optimizer", optimizer)
        await agent_manager.register_agent("reviewer", reviewer)
        
        # Initialize LangGraph orchestrator
        orchestrator = LangGraphOrchestrator(agent_manager, context_manager)
        await orchestrator.initialize()
        
        logger.info("Agent server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start agent server: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent_manager, orchestrator, context_manager
    
    if orchestrator:
        await orchestrator.cleanup()
    if agent_manager:
        await agent_manager.cleanup()
    if context_manager:
        await context_manager.cleanup()
        
    logger.info("Agent server shutdown completed")

@app.get("/agents/health")
async def health_check():
    """Health check for agent server"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_agents": await agent_manager.get_active_agents() if agent_manager else [],
        "version": "0.1.0"
    }

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    if not agent_manager:
        return {"error": "Agent manager not initialized"}
    
    return await agent_manager.get_agents_status()

@app.post("/agents/execute")
async def execute_task(task_data: dict):
    """Execute a task using the agent orchestrator"""
    if not orchestrator:
        return {"error": "Orchestrator not initialized"}
    
    try:
        result = await orchestrator.execute_workflow(task_data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Task execution failed: {str(e)}")
        return {"error": str(e), "success": False}

@app.websocket("/agents/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time agent communication"""
    await websocket.accept()
    
    if not orchestrator:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Orchestrator not initialized"
        }))
        await websocket.close()
        return
    
    # Register client with orchestrator
    await orchestrator.register_client(client_id, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            elif message_type == "task_request":
                # Execute task via orchestrator
                task_id = await orchestrator.execute_task_async(
                    message.get("task", {}),
                    client_id
                )
                await websocket.send_text(json.dumps({
                    "type": "task_started",
                    "task_id": task_id
                }))
            
            elif message_type == "agent_message":
                # Direct agent communication
                agent_id = message.get("agent_id")
                if agent_manager and await agent_manager.has_agent(agent_id):
                    response = await agent_manager.send_message(
                        agent_id,
                        message.get("message", {})
                    )
                    await websocket.send_text(json.dumps({
                        "type": "agent_response",
                        "agent_id": agent_id,
                        "response": response
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Agent {agent_id} not found"
                    }))
            
            elif message_type == "context_update":
                # Update context
                if context_manager:
                    await context_manager.update_context(
                        client_id,
                        message.get("context", {})
                    )
                    await websocket.send_text(json.dumps({
                        "type": "context_updated"
                    }))
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
                
    except WebSocketDisconnect:
        if orchestrator:
            await orchestrator.unregister_client(client_id)
        logger.info(f"Agent client {client_id} disconnected")
        
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        if orchestrator:
            await orchestrator.unregister_client(client_id)

# Agent-specific endpoints
@app.post("/agents/{agent_id}/invoke")
async def invoke_agent(agent_id: str, request_data: dict):
    """Invoke a specific agent directly"""
    if not agent_manager:
        return {"error": "Agent manager not initialized"}
    
    try:
        if not await agent_manager.has_agent(agent_id):
            return {"error": f"Agent {agent_id} not found"}
        
        result = await agent_manager.invoke_agent(agent_id, request_data)
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Agent invocation failed for {agent_id}: {str(e)}")
        return {"error": str(e), "success": False}

@app.get("/agents/{agent_id}/capabilities")
async def get_agent_capabilities(agent_id: str):
    """Get capabilities of a specific agent"""
    if not agent_manager:
        return {"error": "Agent manager not initialized"}
    
    if not await agent_manager.has_agent(agent_id):
        return {"error": f"Agent {agent_id} not found"}
    
    capabilities = await agent_manager.get_agent_capabilities(agent_id)
    return {"agent_id": agent_id, "capabilities": capabilities}

@app.post("/agents/workflow/create")
async def create_workflow(workflow_data: dict):
    """Create a new workflow using LangGraph"""
    if not orchestrator:
        return {"error": "Orchestrator not initialized"}
    
    try:
        workflow_id = await orchestrator.create_workflow(workflow_data)
        return {"success": True, "workflow_id": workflow_id}
    except Exception as e:
        logger.error(f"Workflow creation failed: {str(e)}")
        return {"error": str(e), "success": False}

@app.post("/agents/workflow/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, execution_data: dict):
    """Execute a specific workflow"""
    if not orchestrator:
        return {"error": "Orchestrator not initialized"}
    
    try:
        result = await orchestrator.execute_workflow_by_id(workflow_id, execution_data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    uvicorn.run(
        "agent_server:app",
        host=os.getenv("AGENT_HOST", "localhost"),
        port=int(os.getenv("AGENT_PORT", 8001)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="info"
    )
