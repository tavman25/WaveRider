#!/usr/bin/env python3
"""
WaveRider Production Backend
Real AI agents with file system operations and progress tracking
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json
import asyncio
import uuid
import os
import aiofiles
from typing import Dict, List, Optional, Any
import time
from datetime import datetime
import uvicorn
from pathlib import Path
import httpx
import openai
import anthropic
from pinecone import Pinecone
import redis.asyncio as redis
import psycopg2
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/waverider")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    settings = Column(JSON)
    is_active = Column(Boolean, default=True)

class AgentSession(Base):
    __tablename__ = "agent_sessions"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    task = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)
    result = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

# Initialize services
redis_client = None
pinecone_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_client, pinecone_client
    
    # Initialize Redis
    redis_client = redis.from_url(REDIS_URL)
    
    # Initialize Pinecone
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if pinecone_api_key:
        pinecone_client = Pinecone(api_key=pinecone_api_key)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("WaveRider Backend started successfully")
    yield
    
    # Shutdown
    if redis_client:
        await redis_client.close()
    logger.info("WaveRider Backend shutdown completed")

app = FastAPI(
    title="WaveRider Production Backend",
    description="Agentic AI IDE with real file operations and progress tracking",
    version="1.0.0",
    docs_url="/api/docs",
    lifespan=lifespan
)

# Security
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None
    project_id: Optional[str] = None

class TaskRequest(BaseModel):
    task: str
    type: str  # "code", "debug", "analyze", "optimize"
    context: Optional[str] = None
    project_id: str
    files: Optional[List[str]] = None

class FileOperation(BaseModel):
    operation: str  # "create", "read", "update", "delete"
    path: str
    content: Optional[str] = None
    project_id: str

class AgentProgress(BaseModel):
    session_id: str
    progress: int
    status: str
    message: str
    current_step: Optional[str] = None

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except:
                pass  # Connection might be closed

manager = ConnectionManager()

# AI Service Classes
class AIService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.xai_api_key = os.getenv("XAI_API_KEY")

    async def chat_with_grok(self, message: str, context: str = None) -> str:
        """Chat with xAI Grok (primary AI)"""
        try:
            if not self.xai_api_key:
                raise Exception("xAI API key not configured")
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.xai_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "grok-beta",
                    "messages": [
                        {"role": "system", "content": "You are an expert AI coding assistant."},
                        {"role": "user", "content": f"Context: {context}\n\nMessage: {message}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Grok API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Grok API failed: {e}")
            # Fallback to OpenAI
            return await self.chat_with_openai(message, context)

    async def chat_with_openai(self, message: str, context: str = None) -> str:
        """Fallback to OpenAI GPT-4"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert AI coding assistant."},
                    {"role": "user", "content": f"Context: {context}\n\nMessage: {message}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API failed: {e}")
            return await self.chat_with_claude(message, context)

    async def chat_with_claude(self, message: str, context: str = None) -> str:
        """Final fallback to Anthropic Claude"""
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": f"Context: {context}\n\nMessage: {message}"}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API failed: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later."

ai_service = AIService()

# File System Service
class FileSystemService:
    def __init__(self, base_path: str = "./projects"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def get_project_path(self, project_id: str) -> Path:
        return self.base_path / project_id

    async def create_project(self, project_id: str) -> bool:
        """Create a new project directory"""
        try:
            project_path = self.get_project_path(project_id)
            project_path.mkdir(exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create project {project_id}: {e}")
            return False

    async def read_file(self, project_id: str, file_path: str) -> str:
        """Read file content"""
        try:
            full_path = self.get_project_path(project_id) / file_path
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    async def write_file(self, project_id: str, file_path: str, content: str) -> bool:
        """Write file content"""
        try:
            full_path = self.get_project_path(project_id) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False

    async def delete_file(self, project_id: str, file_path: str) -> bool:
        """Delete file"""
        try:
            full_path = self.get_project_path(project_id) / file_path
            if full_path.exists():
                full_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    async def list_files(self, project_id: str, directory: str = ".") -> List[Dict]:
        """List files and directories"""
        try:
            project_path = self.get_project_path(project_id)
            dir_path = project_path / directory
            
            files = []
            if dir_path.exists():
                for item in dir_path.iterdir():
                    files.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "path": str(item.relative_to(project_path)),
                        "size": item.stat().st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
            
            return sorted(files, key=lambda x: (x["type"] == "file", x["name"]))
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []

fs_service = FileSystemService()

# Agent Classes with Real Implementation
class AgentBase:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type

    async def process_task(
        self, 
        task: str, 
        context: str = None, 
        project_id: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Process task with progress tracking"""
        try:
            # Update progress: Starting
            await self.update_progress(session_id, 10, "starting", "Initializing agent...")
            
            # Analyze task
            await self.update_progress(session_id, 30, "analyzing", "Analyzing task requirements...")
            analysis = await self.analyze_task(task, context)
            
            # Execute task
            await self.update_progress(session_id, 60, "executing", "Executing task...")
            result = await self.execute_task(task, context, project_id, analysis)
            
            # Finalize
            await self.update_progress(session_id, 100, "completed", "Task completed successfully!")
            
            return {
                "success": True,
                "result": result,
                "analysis": analysis,
                "agent_type": self.agent_type
            }
            
        except Exception as e:
            await self.update_progress(session_id, 0, "failed", f"Task failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.agent_type
            }

    async def update_progress(self, session_id: str, progress: int, status: str, message: str):
        """Update task progress"""
        if session_id:
            progress_data = {
                "session_id": session_id,
                "progress": progress,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to WebSocket clients
            await manager.broadcast(json.dumps({
                "type": "agent_progress",
                "data": progress_data
            }))
            
            # Store in Redis
            if redis_client:
                await redis_client.setex(
                    f"agent_progress:{session_id}",
                    3600,  # 1 hour expiry
                    json.dumps(progress_data)
                )

    async def analyze_task(self, task: str, context: str = None) -> Dict[str, Any]:
        """Analyze task requirements"""
        analysis_prompt = f"""
        Analyze this task and provide a structured breakdown:
        Task: {task}
        Context: {context or 'None'}
        
        Provide:
        1. Task type classification
        2. Required steps
        3. Estimated complexity (1-10)
        4. Required files/resources
        5. Potential challenges
        """
        
        response = await ai_service.chat_with_grok(analysis_prompt)
        
        return {
            "raw_analysis": response,
            "complexity": self.extract_complexity(response),
            "steps": self.extract_steps(response)
        }

    def extract_complexity(self, analysis: str) -> int:
        """Extract complexity rating from analysis"""
        # Simple regex to find complexity rating
        import re
        match = re.search(r'complexity[:\s]*(\d+)', analysis.lower())
        return int(match.group(1)) if match else 5

    def extract_steps(self, analysis: str) -> List[str]:
        """Extract steps from analysis"""
        # Simple extraction - could be improved with better parsing
        lines = analysis.split('\n')
        steps = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['step', '1.', '2.', '3.', '-']):
                steps.append(line.strip())
        return steps[:10]  # Limit to 10 steps

    async def execute_task(self, task: str, context: str, project_id: str, analysis: Dict) -> Dict[str, Any]:
        """Execute the actual task - implemented by subclasses"""
        raise NotImplementedError

class CoderAgent(AgentBase):
    def __init__(self):
        super().__init__("coder")

    async def execute_task(self, task: str, context: str, project_id: str, analysis: Dict) -> Dict[str, Any]:
        """Execute coding task with file operations"""
        
        # Generate code based on task
        code_prompt = f"""
        Generate production-ready code for this task:
        Task: {task}
        Context: {context}
        Analysis: {analysis.get('raw_analysis', '')}
        
        Provide:
        1. Complete, working code
        2. File structure if multiple files needed
        3. Comments and documentation
        4. Error handling
        
        Format as JSON with file_path and content for each file.
        """
        
        response = await ai_service.chat_with_grok(code_prompt)
        
        # Parse response and create files
        files_created = []
        
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                code_data = json.loads(response)
                for file_path, content in code_data.items():
                    if await fs_service.write_file(project_id, file_path, content):
                        files_created.append(file_path)
            else:
                # Fallback: create single file
                file_path = f"generated_code_{int(time.time())}.js"
                if await fs_service.write_file(project_id, file_path, response):
                    files_created.append(file_path)
                    
        except json.JSONDecodeError:
            # Create single file with generated content
            file_path = f"generated_code_{int(time.time())}.js"
            if await fs_service.write_file(project_id, file_path, response):
                files_created.append(file_path)
        
        return {
            "code_generated": response,
            "files_created": files_created,
            "file_count": len(files_created)
        }

class DebuggerAgent(AgentBase):
    def __init__(self):
        super().__init__("debugger")

    async def execute_task(self, task: str, context: str, project_id: str, analysis: Dict) -> Dict[str, Any]:
        """Execute debugging task"""
        
        debug_prompt = f"""
        Debug this issue:
        Task: {task}
        Context: {context}
        
        Provide:
        1. Problem identification
        2. Root cause analysis
        3. Step-by-step fix instructions
        4. Fixed code if applicable
        5. Prevention strategies
        """
        
        response = await ai_service.chat_with_grok(debug_prompt)
        
        # If context contains file content, try to fix it
        if context and project_id:
            fixed_code = await self.generate_fix(context, response)
            if fixed_code:
                # Save fixed version
                file_path = f"fixed_code_{int(time.time())}.js"
                await fs_service.write_file(project_id, file_path, fixed_code)
                
                return {
                    "debug_analysis": response,
                    "fixed_code": fixed_code,
                    "fixed_file": file_path
                }
        
        return {
            "debug_analysis": response,
            "suggestions": self.extract_suggestions(response)
        }

    async def generate_fix(self, original_code: str, debug_analysis: str) -> str:
        """Generate fixed code based on debug analysis"""
        fix_prompt = f"""
        Based on this debug analysis, provide the corrected code:
        
        Original Code:
        {original_code}
        
        Debug Analysis:
        {debug_analysis}
        
        Return only the corrected code, properly formatted.
        """
        
        return await ai_service.chat_with_grok(fix_prompt)

    def extract_suggestions(self, analysis: str) -> List[str]:
        """Extract actionable suggestions from debug analysis"""
        lines = analysis.split('\n')
        suggestions = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['fix', 'change', 'update', 'modify', 'add']):
                suggestions.append(line.strip())
        return suggestions[:5]

# Global start time for uptime tracking
start_time = time.time()

# Initialize agents
agents = {
    "coder": CoderAgent(),
    "debugger": DebuggerAgent(),
    # Add more agents as needed
}

# API Routes
@app.get("/")
async def root():
    return {
        "message": "WaveRider Production Backend",
        "version": "1.0.0",
        "status": "active",
        "features": ["Real AI agents", "File operations", "Progress tracking", "WebSocket support"]
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "active",
            "database": "unknown",
            "redis": "unknown",
            "pinecone": "unknown",
            "ai_services": "unknown"
        }
    }
    
    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["services"]["database"] = "active"
    except:
        health_status["services"]["database"] = "error"
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            health_status["services"]["redis"] = "active"
    except:
        health_status["services"]["redis"] = "error"
    
    # Check AI services
    try:
        test_response = await ai_service.chat_with_grok("Hello", "")
        health_status["services"]["ai_services"] = "active"
    except:
        health_status["services"]["ai_services"] = "error"
    
    return health_status

@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """Chat with AI agents"""
    try:
        response = await ai_service.chat_with_grok(
            message.message, 
            message.context
        )
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")

@app.post("/api/tasks")
async def create_task(task_request: TaskRequest, db: Session = Depends(get_db)):
    """Create and execute agent task"""
    try:
        # Create session
        session_id = str(uuid.uuid4())
        
        # Store in database
        db_session = AgentSession(
            id=session_id,
            project_id=task_request.project_id,
            agent_type=task_request.type,
            task=task_request.task,
            status="pending"
        )
        db.add(db_session)
        db.commit()
        
        # Execute task asynchronously
        agent = agents.get(task_request.type)
        if not agent:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {task_request.type}")
        
        # Start background task
        asyncio.create_task(
            agent.process_task(
                task_request.task,
                task_request.context,
                task_request.project_id,
                session_id
            )
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Task started successfully"
        }
        
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{session_id}")
async def get_task_status(session_id: str, db: Session = Depends(get_db)):
    """Get task status and progress"""
    try:
        # Get from database
        db_session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get progress from Redis
        progress_data = None
        if redis_client:
            cached_progress = await redis_client.get(f"agent_progress:{session_id}")
            if cached_progress:
                progress_data = json.loads(cached_progress)
        
        return {
            "session_id": session_id,
            "task": db_session.task,
            "agent_type": db_session.agent_type,
            "status": db_session.status,
            "progress": progress_data,
            "result": db_session.result,
            "created_at": db_session.created_at.isoformat(),
            "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None
        }
        
    except Exception as e:
        logger.error(f"Task status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files")
async def file_operation(operation: FileOperation):
    """Handle file operations"""
    try:
        if operation.operation == "read":
            content = await fs_service.read_file(operation.project_id, operation.path)
            return {"success": True, "content": content}
            
        elif operation.operation == "write":
            if not operation.content:
                raise HTTPException(status_code=400, detail="Content required for write operation")
            success = await fs_service.write_file(operation.project_id, operation.path, operation.content)
            return {"success": success}
            
        elif operation.operation == "delete":
            success = await fs_service.delete_file(operation.project_id, operation.path)
            return {"success": success}
            
        elif operation.operation == "list":
            files = await fs_service.list_files(operation.project_id, operation.path)
            return {"success": True, "files": files}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")
            
    except Exception as e:
        logger.error(f"File operation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/files")
async def list_project_files(project_id: str, directory: str = "."):
    """List files in project directory"""
    try:
        files = await fs_service.list_files(project_id, directory)
        return {
            "success": True,
            "project_id": project_id,
            "directory": directory,
            "files": files
        }
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def create_project(project_data: dict, db: Session = Depends(get_db)):
    """Create new project"""
    try:
        project_id = str(uuid.uuid4())
        
        # Create project directory
        await fs_service.create_project(project_id)
        
        # Store in database
        db_project = Project(
            id=project_id,
            name=project_data.get("name", "Untitled Project"),
            description=project_data.get("description", ""),
            owner_id=project_data.get("owner_id", "anonymous"),
            settings=project_data.get("settings", {})
        )
        db.add(db_project)
        db.commit()
        
        return {
            "success": True,
            "project_id": project_id,
            "message": "Project created successfully"
        }
        
    except Exception as e:
        logger.error(f"Project creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def list_projects(db: Session = Depends(get_db)):
    """List all projects"""
    try:
        projects = db.query(Project).filter(Project.is_active == True).all()
        return {
            "success": True,
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None
                }
                for p in projects
            ]
        }
    except Exception as e:
        logger.error(f"List projects error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": time.time()}))
            elif message.get("type") == "subscribe":
                # Subscribe to project updates
                await websocket.send_text(json.dumps({"type": "subscribed", "project_id": message.get("project_id")}))
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

@app.get("/api/agents")
async def list_agents():
    """List available agents"""
    return {
        "success": True,
        "agents": [
            {
                "type": "coder",
                "name": "Code Generator",
                "description": "Generates production-ready code based on requirements"
            },
            {
                "type": "debugger", 
                "name": "Debug Assistant",
                "description": "Analyzes and fixes code issues"
            },
            {
                "type": "analyzer",
                "name": "Code Analyzer", 
                "description": "Analyzes code quality and suggests improvements"
            },
            {
                "type": "optimizer",
                "name": "Performance Optimizer",
                "description": "Optimizes code for better performance"
            }
        ]
    }

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        total_projects = db.query(Project).count()
        active_sessions = db.query(AgentSession).filter(AgentSession.status.in_(["pending", "running"])).count()
        completed_tasks = db.query(AgentSession).filter(AgentSession.status == "completed").count()
        
        return {
            "success": True,
            "stats": {
                "total_projects": total_projects,
                "active_sessions": active_sessions,
                "completed_tasks": completed_tasks,
                "uptime": time.time() - start_time
            }
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class TaskRequest(BaseModel):
    task: str
    type: str  # "code", "debug", "analyze", "optimize"
    context: Optional[str] = None

class AgentResponse(BaseModel):
    agent_id: str
    agent_type: str
    response: str
    thinking: str
    confidence: float
    next_actions: List[str]

# In-memory storage for active connections
active_connections: Dict[str, WebSocket] = {}

# AI Agent Classes
class BaseAgent:
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = "ready"
    
    async def process(self, task: str, context: str = None) -> AgentResponse:
        raise NotImplementedError

class PlannerAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "planner")
    
    async def process(self, task: str, context: str = None) -> AgentResponse:
        # Simulate thinking time
        await asyncio.sleep(1)
        
        # Analyze the task and break it down
        thinking = f"Analyzing task: '{task}'. Breaking down into actionable steps..."
        
        if "create" in task.lower() or "build" in task.lower():
            response = f"""I'll help you {task}. Here's my plan:

1. **Analysis Phase**: Understand requirements and constraints
2. **Architecture Design**: Define structure and components  
3. **Implementation Strategy**: Break into manageable chunks
4. **Testing Approach**: Define validation criteria

Let me coordinate with the Coder Agent to implement this."""
            next_actions = ["coordinate_with_coder", "define_architecture", "create_implementation_plan"]
            
        elif "debug" in task.lower() or "fix" in task.lower():
            response = f"""I'll analyze the debugging task: {task}

**Debug Strategy**:
1. Identify error patterns and symptoms
2. Trace execution flow 
3. Isolate root cause
4. Propose targeted fixes

Coordinating with Debugger Agent for detailed analysis."""
            next_actions = ["analyze_error_logs", "coordinate_with_debugger", "propose_fixes"]
            
        elif "optimize" in task.lower() or "improve" in task.lower():
            response = f"""Optimization plan for: {task}

**Optimization Strategy**:
1. Performance profiling and bottleneck identification
2. Code quality analysis
3. Resource usage optimization
4. Best practices implementation

I'll work with the Optimizer Agent on this."""
            next_actions = ["profile_performance", "coordinate_with_optimizer", "implement_improvements"]
            
        else:
            response = f"""I'll help you with: {task}

**General Approach**:
1. Requirement analysis
2. Solution design
3. Implementation planning
4. Quality assurance

Let me coordinate with the appropriate agents to execute this plan."""
            next_actions = ["analyze_requirements", "design_solution", "coordinate_execution"]
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response=response,
            thinking=thinking,
            confidence=0.9,
            next_actions=next_actions
        )

class CoderAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "coder")
    
    async def process(self, task: str, context: str = None) -> AgentResponse:
        await asyncio.sleep(1.5)
        
        thinking = f"Analyzing coding task: '{task}'. Determining best implementation approach..."
        
        if "function" in task.lower() or "method" in task.lower():
            response = f"""I'll create the function for: {task}

```javascript
// Generated function based on your request
function processTask(input) {{
    // Implementation logic here
    console.log('Processing:', input);
    
    // Add your specific logic
    const result = {{
        status: 'completed',
        data: input,
        timestamp: new Date().toISOString()
    }};
    
    return result;
}}

// Example usage
const output = processTask('{task}');
console.log(output);
```

This function provides a solid foundation. Would you like me to modify it for your specific use case?"""
            next_actions = ["refine_implementation", "add_error_handling", "write_tests"]
            
        elif "component" in task.lower() or "react" in task.lower():
            response = f"""Creating React component for: {task}

```tsx
import React, {{ useState, useEffect }} from 'react';

interface ComponentProps {{
    data?: any;
    onUpdate?: (value: any) => void;
}}

export const CustomComponent: React.FC<ComponentProps> = ({{ data, onUpdate }}) => {{
    const [state, setState] = useState(null);
    
    useEffect(() => {{
        // Initialize component
        console.log('Component initialized with:', data);
    }}, [data]);
    
    const handleAction = () => {{
        // Handle user interaction
        const newValue = 'Updated value';
        setState(newValue);
        onUpdate?.(newValue);
    }};
    
    return (
        <div className="custom-component">
            <h3>Custom Component</h3>
            <p>Status: {{state || 'Ready'}}</p>
            <button onClick={{handleAction}}>
                Execute Action
            </button>
        </div>
    );
}};
```

This component is ready to be customized for your specific needs."""
            next_actions = ["customize_props", "add_styling", "implement_logic"]
            
        else:
            response = f"""I'm ready to code: {task}

I can help you with:
- Function implementations
- React components  
- API endpoints
- Data processing logic
- Algorithm implementations

Please provide more specific requirements and I'll generate the exact code you need."""
            next_actions = ["clarify_requirements", "choose_technology", "implement_solution"]
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response=response,
            thinking=thinking,
            confidence=0.85,
            next_actions=next_actions
        )

class DebuggerAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "debugger")
    
    async def process(self, task: str, context: str = None) -> AgentResponse:
        await asyncio.sleep(1.2)
        
        thinking = f"Debugging analysis for: '{task}'. Examining potential issues and solutions..."
        
        if "error" in task.lower() or "bug" in task.lower():
            response = f"""🔍 **Debug Analysis for**: {task}

**Common Issues Identified**:
1. **Syntax Errors**: Check for missing brackets, semicolons
2. **Type Mismatches**: Verify variable types and function signatures  
3. **Async/Promise Issues**: Ensure proper await/then handling
4. **Scope Problems**: Check variable accessibility

**Debugging Steps**:
```javascript
// Add console logging for debugging
console.log('Debug checkpoint 1:', variableName);

// Check for null/undefined values
if (data && data.property) {{
    console.log('Data is valid:', data);
}} else {{
    console.error('Data validation failed:', data);
}}

// Try-catch for error handling
try {{
    const result = riskyOperation();
    console.log('Success:', result);
}} catch (error) {{
    console.error('Error caught:', error.message);
}}
```

**Recommended Fixes**:
- Add proper error boundaries
- Implement input validation
- Use TypeScript for better type safety"""
            next_actions = ["add_error_handling", "implement_logging", "validate_inputs"]
            
        else:
            response = f"""🐛 **Debugger Agent Ready**

I can help you debug:
- Runtime errors and exceptions
- Logic errors and unexpected behavior
- Performance issues
- Memory leaks
- API call failures

Share your error messages or describe the unexpected behavior, and I'll provide targeted debugging solutions."""
            next_actions = ["analyze_error_logs", "identify_root_cause", "provide_solution"]
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response=response,
            thinking=thinking,
            confidence=0.88,
            next_actions=next_actions
        )

class OptimizerAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "optimizer")
    
    async def process(self, task: str, context: str = None) -> AgentResponse:
        await asyncio.sleep(1.3)
        
        thinking = f"Performance optimization analysis for: '{task}'. Identifying improvement opportunities..."
        
        if "optimize" in task.lower() or "performance" in task.lower():
            response = f"""⚡ **Performance Optimization for**: {task}

**Optimization Opportunities**:

1. **Code Efficiency**:
```javascript
// Before (inefficient)
const slowFunction = (arr) => {{
    return arr.filter(item => item.active)
             .map(item => item.value)
             .reduce((sum, val) => sum + val, 0);
}}

// After (optimized)
const fastFunction = (arr) => {{
    let sum = 0;
    for (const item of arr) {{
        if (item.active) sum += item.value;
    }}
    return sum;
}}
```

**Performance Gains**: 60-80% improvement expected"""
            next_actions = ["implement_caching", "optimize_algorithms", "profile_performance"]
            
        else:
            response = f"""🚀 **Optimizer Agent Ready**

I can optimize:
- Algorithm efficiency
- Memory usage
- Bundle size
- Database queries
- Network requests
- Rendering performance

What specific performance issue would you like me to address?"""
            next_actions = ["identify_bottlenecks", "measure_performance", "implement_optimizations"]
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response=response,
            thinking=thinking,
            confidence=0.92,
            next_actions=next_actions
        )

# Initialize agents
agents = {
    "planner": PlannerAgent("planner-001"),
    "coder": CoderAgent("coder-001"), 
    "debugger": DebuggerAgent("debugger-001"),
    "optimizer": OptimizerAgent("optimizer-001")
}

@app.get("/")
async def root():
    return {"message": "WaveRider AI Backend is running!", "status": "active", "agents": len(agents)}

@app.get("/health")
async def health():
    return {"status": "healthy", "agents": len(agents)}

@app.post("/chat")
async def chat_with_ai(message: ChatMessage):
    """Process chat message with AI agents"""
    try:
        # Determine which agent to use based on message content
        message_lower = message.message.lower()
        
        if any(word in message_lower for word in ["plan", "strategy", "approach", "organize"]):
            agent = agents["planner"]
        elif any(word in message_lower for word in ["code", "function", "implement", "create", "build"]):
            agent = agents["coder"]
        elif any(word in message_lower for word in ["debug", "error", "bug", "fix", "problem"]):
            agent = agents["debugger"]
        elif any(word in message_lower for word in ["optimize", "performance", "improve", "faster"]):
            agent = agents["optimizer"]
        else:
            # Default to planner for general questions
            agent = agents["planner"]
        
        # Process with selected agent
        response = await agent.process(message.message, message.context)
        
        return {
            "success": True,
            "agent_used": agent.agent_type,
            "response": response.response,
            "thinking": response.thinking,
            "confidence": response.confidence,
            "next_actions": response.next_actions,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@app.get("/api/agents")
async def get_agents():
    return {
        "agents": [
            {"id": agent.agent_id, "name": f"{agent.agent_type.title()} Agent", "status": agent.status, "type": agent.agent_type}
            for agent in agents.values()
        ]
    }

if __name__ == "__main__":
    print("Starting WaveRider AI Backend...")
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
