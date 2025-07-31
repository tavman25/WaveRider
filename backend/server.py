#!/usr/bin/env python3
"""
WaveRider Production Backend
Real AI agents with file system operations and progress tracking
"""

# Load environment variables from .env.local file
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env.local from parent directory
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json
import asyncio
import uuid
import os
# import aiofiles  # Not needed, using regular file operations
import subprocess
import shutil
import string
import re
from typing import Dict, List, Optional, Any
import time
import socket
import httpx
import logging
from datetime import datetime
import uvicorn
from pathlib import Path
import httpx
import openai
import anthropic
# from pinecone import Pinecone
# import redis.asyncio as redis
# import psycopg2
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
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use SQLite fallback for local development
    DATABASE_URL = "sqlite:///./waverider.db"
    logger.info("Using SQLite database for local development")
else:
    logger.info(f"Using database: {DATABASE_URL}")

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
    
    # Initialize Redis (commented out for local development)
    # redis_client = redis.from_url(REDIS_URL)
    redis_client = None
    
    # Initialize Pinecone (commented out for local development)  
    # pinecone_api_key = os.getenv("PINECONE_API_KEY")
    # if pinecone_api_key:
    #     pinecone_client = Pinecone(api_key=pinecone_api_key)
    pinecone_client = None
    
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
                    "model": "grok-2-1212",
                    "messages": [
                        {"role": "system", "content": """You are an expert AI coding assistant in WaveRider IDE. When users request file or directory creation:

1. ALWAYS create actual files and directories immediately - never just provide instructions
2. Use this JSON format for file operations:
{
  "action": "create_files",
  "files": [
    {"path": "file/path.ext", "content": "file content here"},
    {"path": "directory/", "content": null}
  ],
  "message": "Created X files and Y directories for your project"
}

3. For "vibe coding" requests, be proactive and create complete project structures
4. Always follow modern industry standards and best practices
5. Create working, production-ready code - no placeholders
6. Respond with both the JSON structure AND a friendly explanation

Example: If user asks for "React dashboard", create package.json, src/App.js, components/, etc. immediately."""},
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
                model="gpt-3.5-turbo",  # Use gpt-3.5-turbo which is more widely available
                messages=[
                    {"role": "system", "content": """You are an expert AI coding assistant in WaveRider IDE. When users request file or directory creation:

1. ALWAYS create actual files and directories immediately - never just provide instructions
2. Use this JSON format for file operations:
{
  "action": "create_files",
  "files": [
    {"path": "file/path.ext", "content": "file content here"},
    {"path": "directory/", "content": null}
  ],
  "message": "Created X files and Y directories for your project"
}

3. For "vibe coding" requests, be proactive and create complete project structures
4. Always follow modern industry standards and best practices
5. Create working, production-ready code - no placeholders
6. Respond with both the JSON structure AND a friendly explanation

Example: If user asks for "React dashboard", create package.json, src/App.js, components/, etc. immediately."""},
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
                model="claude-3-5-sonnet-20241022",  # Use the latest available Claude model
                max_tokens=2000,
                system="""You are an expert AI coding assistant in WaveRider IDE. When users request file or directory creation:

1. ALWAYS create actual files and directories immediately - never just provide instructions
2. Use this JSON format for file operations:
{
  "action": "create_files",
  "files": [
    {"path": "file/path.ext", "content": "file content here"},
    {"path": "directory/", "content": null}
  ],
  "message": "Created X files and Y directories for your project"
}

3. For "vibe coding" requests, be proactive and create complete project structures
4. Always follow modern industry standards and best practices
5. Create working, production-ready code - no placeholders
6. Respond with both the JSON structure AND a friendly explanation

Example: If user asks for "React dashboard", create package.json, src/App.js, components/, etc. immediately.""",
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
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    async def write_file(self, project_id: str, file_path: str, content: str) -> bool:
        """Write file content"""
        try:
            full_path = self.get_project_path(project_id) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
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
        """List files and directories with proper tree structure"""
        try:
            project_path = self.get_project_path(project_id)
            return await self._build_file_tree(project_path, project_path)
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def _build_file_tree(self, current_path: Path, root_path: Path) -> List[Dict]:
        """Build recursive file tree structure"""
        try:
            files = []
            if current_path.exists() and current_path.is_dir():
                for item in sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                    file_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "path": str(item.relative_to(root_path)),
                        "size": item.stat().st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    }
                    
                    # For directories, add children
                    if item.is_dir():
                        file_info["children"] = await self._build_file_tree(item, root_path)
                    
                    files.append(file_info)
            
            return files
        except Exception as e:
            logger.error(f"Failed to build tree for {current_path}: {e}")
            return []

fs_service = FileSystemService()

# Real Development Server Management
class DevelopmentServerManager:
    def __init__(self):
        self.running_servers = {}  # project_id -> server_info
        self.port_manager = PortManager()
        
    async def start_development_server(self, project_id: str) -> Dict[str, Any]:
        """Start a real development server for the project"""
        try:
            project_path = fs_service.get_project_path(project_id)
            if not project_path.exists():
                return {"success": False, "error": "Project not found"}
            
            # Auto-detect project type and get dev command
            dev_command = await self.detect_and_get_dev_command(project_path)
            if not dev_command:
                return {"success": False, "error": "No development command available - ensure dependencies are installed"}
            
            # Allocate port
            port = await self.port_manager.allocate_port()
            if not port:
                return {"success": False, "error": "No available ports"}
            
            # Install dependencies if needed
            try:
                await self.ensure_dependencies_installed(project_path)
            except Exception as dep_error:
                await self.port_manager.release_port(port)  # Release the port since we failed
                return {"success": False, "error": f"Failed to install dependencies: {str(dep_error)}"}
            
            # Dependencies are now properly installed
            
            # Modify command to use specific port
            dev_command_with_port = self.modify_command_for_port(dev_command, port, project_path)
            logger.info(f"🔧 Original command: {dev_command}")
            logger.info(f"🔧 Modified command: {dev_command_with_port}")
            logger.info(f"🔧 Using port: {port}")
            logger.info(f"🔧 Project path: {project_path}")
            
            # Start the server
            process = await self.start_server_process(project_id, project_path, dev_command_with_port, port)
            
            if process:
                url = f"http://localhost:{port}"
                self.running_servers[project_id] = {
                    "process": process,
                    "port": port,
                    "url": url,
                    "command": dev_command_with_port,
                    "started_at": datetime.now(),
                    "status": "starting"
                }
                
                # Wait a moment and check if server started successfully
                await asyncio.sleep(3)
                if await self.check_server_health(url):
                    self.running_servers[project_id]["status"] = "running"
                    logger.info(f"✅ Development server started successfully: {url}")
                    return {"success": True, "url": url, "port": port, "status": "running"}
                else:
                    self.running_servers[project_id]["status"] = "starting"
                    logger.info(f"🔄 Development server starting: {url}")
                    return {"success": True, "url": url, "port": port, "status": "starting"}
            
            return {"success": False, "error": "Failed to start server process"}
            
        except Exception as e:
            logger.error(f"Development server start error: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_and_get_dev_command(self, project_path: Path) -> Optional[str]:
        """Auto-detect project type and return appropriate development command"""
        
        # Check for Docker setup first
        docker_compose_path = project_path / "docker-compose.yml"
        dockerfile_path = project_path / "Dockerfile"
        
        if docker_compose_path.exists():
            logger.info(f"🐳 Found Docker Compose configuration: {docker_compose_path}")
            return "docker-compose up --build"
        elif dockerfile_path.exists():
            logger.info(f"🐳 Found Dockerfile: {dockerfile_path}")
            # Use Docker with dynamic port mapping
            return "docker build -t temp-project . && docker run --rm -p {port}:{internal_port} temp-project"
        
        # Check for Node.js projects
        package_json_path = project_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                    scripts = package_json.get("scripts", {})
                    
                    # Priority order for dev commands
                    if "dev" in scripts:
                        return "npm run dev"
                    elif "start" in scripts:
                        return "npm start"
                    elif "serve" in scripts:
                        return "npm run serve"
                    else:
                        return "npm start"  # fallback
            except:
                return "npm start"
        
        # Check for Python projects
        if (project_path / "main.py").exists():
            return "python main.py"
        elif (project_path / "app.py").exists():
            return "python app.py"
        elif (project_path / "manage.py").exists():
            return "python manage.py runserver"
        
        # Check for other project types
        if (project_path / "Cargo.toml").exists():
            return "cargo run"
        elif (project_path / "go.mod").exists():
            return "go run ."
        
        return None
    
    async def ensure_dependencies_installed(self, project_path: Path):
        """Ensure project dependencies are installed"""
        try:
            # Node.js dependencies
            if (project_path / "package.json").exists() and not (project_path / "node_modules").exists():
                logger.info("Installing Node.js dependencies...")
                process = await asyncio.create_subprocess_shell(
                    "npm install",
                    cwd=str(project_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    logger.error(f"npm install failed: {stderr.decode()}")
                    raise Exception(f"npm install failed: {stderr.decode()}")
                else:
                    logger.info("✅ Node.js dependencies installed successfully")
            
            # Python dependencies
            if (project_path / "requirements.txt").exists():
                logger.info("Installing Python dependencies...")
                # Use regular subprocess to avoid Windows asyncio issues
                try:
                    import subprocess
                    result = subprocess.run(
                        ["python", "-m", "pip", "install", "-r", "requirements.txt", "--user"],
                        cwd=str(project_path),
                        capture_output=True,
                        text=True,
                        timeout=120  # 2 minute timeout
                    )
                    
                    logger.info(f"pip install return code: {result.returncode}")
                    logger.info(f"pip install stdout: {result.stdout}")
                    if result.stderr:
                        logger.info(f"pip install stderr: {result.stderr}")
                    
                    if result.returncode != 0:
                        error_msg = result.stderr or result.stdout or "Unknown pip installation error"
                        logger.error(f"pip install failed with return code {result.returncode}: {error_msg}")
                        raise Exception(f"pip install failed: {error_msg}")
                    else:
                        logger.info("✅ Python dependencies installed successfully")
                except subprocess.TimeoutExpired:
                    logger.error("pip install timed out")
                    raise Exception("pip install timed out")
                except Exception as pip_error:
                    logger.error(f"pip install process error: {str(pip_error)}")
                    raise Exception(f"pip install process error: {str(pip_error)}")
                
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown dependency installation error"
            logger.warning(f"Failed to install dependencies: {error_msg}")
            raise Exception(error_msg)  # Re-raise with proper error message
    
    def modify_command_for_port(self, command: str, port: int, project_path: Path) -> str:
        """Modify the command to use a specific port based on project type"""
        
        # Handle Docker commands
        if "docker-compose up" in command:
            # For docker-compose, we'll use environment variable for port
            return f"PORT={port} docker-compose up --build"
        elif "docker build" in command and "docker run" in command:
            # Replace the port placeholder in Docker run command
            internal_port = 5000  # Default internal port for Flask
            if "{port}" in command and "{internal_port}" in command:
                return command.format(port=port, internal_port=internal_port)
            else:
                # Fallback: add port mapping
                return command.replace("docker run --rm", f"docker run --rm -p {port}:{internal_port}")
        
        # Check for Next.js
        elif "next dev" in command or (project_path / "next.config.js").exists():
            return f"{command} --port {port}"
        
        # Check for Create React App
        elif "react-scripts start" in command or "npm start" in command:
            package_json_path = project_path / "package.json"
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_json = json.load(f)
                        if "react-scripts" in package_json.get("dependencies", {}):
                            return f"PORT={port} {command}"
                except:
                    pass
        
        # Check for Vue.js
        elif "vue" in command.lower() or (project_path / "vue.config.js").exists():
            return f"{command} --port {port}"
        
        # Check for Vite
        elif "vite" in command or (project_path / "vite.config.js").exists():
            return f"{command} --port {port}"
        
        # Python/FastAPI/Flask projects
        elif "python" in command:
            # Check if it's a Flask app
            if (project_path / "app.py").exists():
                # For Flask apps, we need to set the PORT environment variable
                # and modify the app.py to use it, or use Flask's command-line options
                return f"python -m flask run --host=0.0.0.0 --port={port}"
            else:
                # For other Python apps that might accept --port
                return f"{command} --host 0.0.0.0 --port {port}"
        
        return command
    
    async def start_server_process(self, project_id: str, project_path: Path, command: str, port: int):
        """Start the actual server process"""
        try:
            # Set up environment
            env = os.environ.copy()
            env["PORT"] = str(port)
            env["NODE_ENV"] = "development"
            
            # Flask-specific environment variables
            if "flask run" in command or "docker-compose" in command:
                env["FLASK_APP"] = "app.py"
                env["FLASK_ENV"] = "development"
                env["FLASK_DEBUG"] = "1"
            
            # Docker-specific environment variables
            if "docker" in command:
                env["DOCKER_BUILDKIT"] = "1"  # Enable BuildKit for faster builds
                
            logger.info(f"🚀 Starting process with command: {command}")
            logger.info(f"🚀 Working directory: {project_path}")
            logger.info(f"🚀 Environment PORT: {env.get('PORT')}")
            logger.info(f"🚀 Environment FLASK_APP: {env.get('FLASK_APP', 'Not set')}")
            if "docker" in command:
                logger.info(f"🐳 Using Docker for containerized development")
            
            # Use regular subprocess.Popen for better Windows compatibility
            import subprocess
            import shlex
            
            # Split command properly for Windows
            if os.name == 'nt':  # Windows
                # Use shell=True on Windows for better command parsing
                process = subprocess.Popen(
                    command,
                    cwd=str(project_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    shell=True,
                    text=True,
                    bufsize=1
                )
            else:
                # Unix-like systems
                args = shlex.split(command)
                process = subprocess.Popen(
                    args,
                    cwd=str(project_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    bufsize=1
                )
            
            logger.info(f"✅ Process started successfully with PID: {process.pid}")
            
            # Start output monitoring task
            asyncio.create_task(self.monitor_process_output_sync(project_id, process))
            
            return process
            
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown process start error"
            logger.error(f"Failed to start server process: {error_msg}")
            logger.error(f"Command: {command}")
            logger.error(f"Working directory: {project_path}")
            logger.error(f"Exception type: {type(e).__name__}")
            return None
    
    async def monitor_process_output_sync(self, project_id: str, process):
        """Monitor synchronous process output for logging and health checks"""
        try:
            import threading
            
            def read_stdout():
                try:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            output = line.strip()
                            logger.info(f"[{project_id}] {output}")
                except Exception as e:
                    logger.error(f"Error reading stdout: {e}")
            
            def read_stderr():
                try:
                    for line in iter(process.stderr.readline, ''):
                        if line:
                            output = line.strip()
                            logger.error(f"[{project_id}] ERROR: {output}")
                except Exception as e:
                    logger.error(f"Error reading stderr: {e}")
            
            # Start reading threads
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            
            stdout_thread.start()
            stderr_thread.start()
            
        except Exception as e:
            logger.error(f"Error setting up process monitoring: {e}")
    
    async def monitor_process_output(self, project_id: str, process):
        """Monitor process output for logging and health checks"""
        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                output = line.decode().strip()
                if output:
                    logger.info(f"[{project_id}] {output}")
                    
                    # Check for server ready indicators
                    if any(indicator in output.lower() for indicator in 
                          ["server ready", "compiled successfully", "ready on", "running on", "local:", "development server"]):
                        if project_id in self.running_servers:
                            self.running_servers[project_id]["status"] = "running"
                            
        except Exception as e:
            logger.error(f"Process monitoring error for {project_id}: {e}")
    
    async def check_server_health(self, url: str) -> bool:
        """Check if the server is responding"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                return response.status_code < 500
        except:
            return False
    
    async def stop_server(self, project_id: str) -> bool:
        """Stop the development server for a project"""
        if project_id not in self.running_servers:
            return False
        
        try:
            server_info = self.running_servers[project_id]
            process = server_info["process"]
            port = server_info["port"]
            
            # Terminate process
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            
            # Release port
            await self.port_manager.release_port(port)
            
            # Remove from running servers
            del self.running_servers[project_id]
            
            logger.info(f"🛑 Stopped development server for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop development server: {e}")
            return False
    
    async def get_server_status(self, project_id: str) -> Dict[str, Any]:
        """Get the status of a project's development server"""
        if project_id not in self.running_servers:
            return {"running": False}
        
        server_info = self.running_servers[project_id]
        
        # Check if process is still alive
        if server_info["process"].returncode is not None:
            # Process has died, clean up
            await self.stop_server(project_id)
            return {"running": False}
        
        # Check server health
        is_healthy = await self.check_server_health(server_info["url"])
        
        return {
            "running": True,
            "url": server_info["url"],
            "port": server_info["port"],
            "status": server_info["status"],
            "healthy": is_healthy,
            "started_at": server_info["started_at"].isoformat(),
            "uptime_seconds": (datetime.now() - server_info["started_at"]).total_seconds()
        }
    
    async def list_running_servers(self) -> Dict[str, Any]:
        """List all running development servers"""
        servers = {}
        for project_id, server_info in self.running_servers.items():
            servers[project_id] = await self.get_server_status(project_id)
        return servers

class PortManager:
    def __init__(self, start_port: int = 4000, end_port: int = 4100):
        self.start_port = start_port
        self.end_port = end_port
        self.allocated_ports = set()
        # Reserve ports that are already in use by WaveRider
        self.reserved_ports = {3000, 8002, 8001}  # Frontend, Backend, Agent Server
    
    async def allocate_port(self) -> Optional[int]:
        """Allocate an available port"""
        for port in range(self.start_port, self.end_port + 1):
            if (port not in self.allocated_ports and 
                port not in self.reserved_ports and 
                await self.is_port_free(port)):
                self.allocated_ports.add(port)
                return port
        return None
    
    async def release_port(self, port: int):
        """Release a port back to the pool"""
        self.allocated_ports.discard(port)
    
    async def is_port_free(self, port: int) -> bool:
        """Check if a port is free"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return False

# Global development server manager
dev_server_manager = DevelopmentServerManager()

async def start_project_development_server(project_id: str) -> Dict[str, Any]:
    """Start development server for a project - convenience function"""
    return await dev_server_manager.start_development_server(project_id)

# Helper function for executing commands in projects
async def execute_project_command(project_id: str, command: str) -> Dict[str, Any]:
    """Execute a command in a project directory"""
    try:
        project_path = fs_service.get_project_path(project_id)
        if not project_path.exists():
            return {"success": False, "output": "Project not found"}
        
        # Use the existing terminal execution logic
        result = subprocess.run(
            command,
            cwd=str(project_path),
            shell=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=120  # 2 minute timeout for longer operations
        )
        
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        
        return {
            "success": result.returncode == 0,
            "output": output.strip(),
            "return_code": result.returncode,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"Command '{command}' timed out"}
    except Exception as e:
        return {"success": False, "output": f"Error executing command: {str(e)}"}

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

@app.get("/api/status/ai-services")
async def check_ai_services_status():
    """Check the status and credits of all AI services"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check OpenAI
    try:
        openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Make a minimal test request to check if API key works
        test_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        status["services"]["openai"] = {
            "status": "active",
            "model_tested": "gpt-3.5-turbo",
            "api_key_valid": True,
            "usage_info": "API key working - check OpenAI dashboard for credit details"
        }
    except openai.RateLimitError as e:
        status["services"]["openai"] = {
            "status": "rate_limited",
            "error": str(e),
            "api_key_valid": True,
            "issue": "Rate limit exceeded or insufficient credits"
        }
    except openai.AuthenticationError as e:
        status["services"]["openai"] = {
            "status": "auth_error",
            "error": str(e),
            "api_key_valid": False,
            "issue": "Invalid API key"
        }
    except Exception as e:
        status["services"]["openai"] = {
            "status": "error",
            "error": str(e),
            "api_key_valid": "unknown"
        }
    
    # Check Anthropic
    try:
        anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        test_response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1,
            messages=[{"role": "user", "content": "test"}]
        )
        status["services"]["anthropic"] = {
            "status": "active",
            "model_tested": "claude-3-haiku-20240307",
            "api_key_valid": True,
            "usage_info": "API key working - check Anthropic console for credit details"
        }
    except anthropic.RateLimitError as e:
        status["services"]["anthropic"] = {
            "status": "rate_limited",
            "error": str(e),
            "api_key_valid": True,
            "issue": "Rate limit exceeded or insufficient credits"
        }
    except anthropic.AuthenticationError as e:
        status["services"]["anthropic"] = {
            "status": "auth_error",
            "error": str(e),
            "api_key_valid": False,
            "issue": "Invalid API key"
        }
    except Exception as e:
        status["services"]["anthropic"] = {
            "status": "error",
            "error": str(e),
            "api_key_valid": "unknown"
        }
    
    return status

@app.get("/api/status/environment")
async def check_environment_status():
    """Check environment variables and configuration"""
    return {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic_api_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
            "openai_key_prefix": os.getenv("OPENAI_API_KEY", "")[:7] + "..." if os.getenv("OPENAI_API_KEY") else "Not set",
            "anthropic_key_prefix": os.getenv("ANTHROPIC_API_KEY", "")[:7] + "..." if os.getenv("ANTHROPIC_API_KEY") else "Not set"
        }
    }

@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """Enhanced chat with AI agents that can create files"""
    try:
        # Check if this is a file creation request
        is_file_request = any(keyword in message.message.lower() for keyword in [
            'create', 'generate', 'make', 'build', 'write', 'setup', 'initialize'
        ]) and any(filetype in message.message.lower() for filetype in [
            'file', 'project', 'app', 'component', 'script', 'page', 'webapp', 'react', 'html', 'css', 'js'
        ])
        
        if is_file_request and message.project_id:
            # Enhanced prompt for file creation
            enhanced_prompt = f"""
            CRITICAL: You must create actual files, not just instructions! Return ONLY valid JSON.
            
            User Request: {message.message}
            Context: {message.context or 'No additional context'}
            
            You MUST respond with ONLY a valid JSON object in this EXACT format (no other text):
            {{
                "action": "create_files",
                "message": "Brief explanation of what you created",
                "files": [
                    {{"path": "package.json", "content": "complete file content here"}},
                    {{"path": "src/", "content": null}},
                    {{"path": "src/App.tsx", "content": "complete React component code here"}},
                    {{"path": "public/index.html", "content": "complete HTML code here"}}
                ],
                "instructions": "How to run: npm install && npm start"
            }}
            
            RULES:
            - Return ONLY valid JSON, no markdown formatting, no explanations outside JSON
            - For directories: use "content": null
            - For files: include complete, working content
            - Create real project structures, not examples
            - Use proper file paths relative to project root
            - Include all necessary files for a functional project
            """
            
            response = await ai_service.chat_with_grok(enhanced_prompt)
            
            # Try to parse JSON response and create files
            files_created = []
            try:
                # Try to parse the response as JSON
                parsed_response = json.loads(response)
                if "files" in parsed_response:
                    for file_data in parsed_response["files"]:
                        if "path" in file_data:
                            path = file_data["path"]
                            content = file_data.get("content", "")
                            
                            # Handle directory creation (content is null)
                            if content is None:
                                # Create directory
                                project_path = fs_service.get_project_path(message.project_id)
                                dir_path = project_path / path
                                dir_path.mkdir(parents=True, exist_ok=True)
                                files_created.append(f"{path} (directory)")
                            else:
                                # Create file
                                success = await fs_service.write_file(
                                    message.project_id, 
                                    path, 
                                    content
                                )
                                if success:
                                    files_created.append(path)
                    
                    return {
                        "success": True,
                        "response": parsed_response.get("message", parsed_response.get("response", "Files created successfully!")),
                        "files_created": files_created,
                        "instructions": parsed_response.get("instructions", ""),
                        "timestamp": datetime.now().isoformat()
                    }
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the text response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    try:
                        parsed_response = json.loads(json_match.group())
                        if "files" in parsed_response:
                            for file_data in parsed_response["files"]:
                                if "path" in file_data:
                                    path = file_data["path"]
                                    content = file_data.get("content", "")
                                    
                                    # Handle directory creation (content is null)
                                    if content is None:
                                        # Create directory
                                        project_path = fs_service.get_project_path(message.project_id)
                                        dir_path = project_path / path
                                        dir_path.mkdir(parents=True, exist_ok=True)
                                        files_created.append(f"{path} (directory)")
                                    else:
                                        # Create file
                                        success = await fs_service.write_file(
                                            message.project_id, 
                                            path, 
                                            content
                                        )
                                        if success:
                                            files_created.append(path)
                            
                            return {
                                "success": True,
                                "response": parsed_response.get("message", "Files created successfully!"),
                                "files_created": files_created,
                                "instructions": parsed_response.get("instructions", ""),
                                "timestamp": datetime.now().isoformat()
                            }
                    except Exception as parse_error:
                        logger.error(f"Failed to parse extracted JSON: {parse_error}")
                        pass
                
                # If no JSON found or parsing failed, try to handle as regular text response
                # but check if it contains file creation intent
                if any(keyword in response.lower() for keyword in ['created', 'package.json', 'port', '3001']):
                    # Try to extract and execute any file operations mentioned in the text
                    if 'package.json' in response and 'port' in response:
                        # Create updated package.json with port 3001
                        package_content = """{
  "name": "react-website",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "set PORT=3001&& react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}"""
                        success = await fs_service.write_file(message.project_id, "package.json", package_content)
                        if success:
                            files_created.append("package.json")
                            
                            return {
                                "success": True,
                                "response": "✅ Updated package.json to use port 3001. You can now run 'npm start' to start your React app on port 3001!",
                                "files_created": files_created,
                                "instructions": "Run: npm start (will use port 3001)",
                                "timestamp": datetime.now().isoformat()
                            }
        
        # Regular chat response
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

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a single project by ID"""
    try:
        project = db.query(Project).filter(Project.id == project_id, Project.is_active == True).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/generate")
async def generate_ai_project(project_data: dict, db: Session = Depends(get_db)):
    """Generate a complete, working project with production-ready functionality"""
    try:
        project_id = str(uuid.uuid4())
        template_id = project_data.get("template", "simple-react")  # Changed from template_id to template
        project_name = project_data.get("name", "Generated Project")
        project_description = project_data.get("description", "")
        features = project_data.get("features", [])
        custom_requirements = project_data.get("custom_requirements", "")
        
        logger.info(f"🚀 Creating working project: {project_name}")
        
        # Create project directory first
        await fs_service.create_project(project_id)
        
        # Store in database
        db_project = Project(
            id=project_id,
            name=project_name,
            description=project_description,
            owner_id=project_data.get("owner_id", "anonymous"),
            settings={
                "template": template_id,
                "features": features,
                "custom_requirements": custom_requirements
            }
        )
        db.add(db_project)
        db.commit()
        
        # Generate actual working project files
        files_created = await create_working_project(project_id, template_id, project_name, project_description, features)
        
        if files_created == 0:
            raise HTTPException(status_code=500, detail="Failed to create project files")
        
        # Get the file tree for the generated project
        try:
            file_tree = await fs_service.list_files(project_id)
        except Exception as e:
            logger.error(f"Failed to get file tree: {e}")
            file_tree = []

        return {
            "success": True,
            "project_id": project_id,
            "message": f"Created working project: {project_name}",
            "files_created": files_created,
            "file_tree": file_tree,
            "ready_to_run": True,
            "instructions": f"Project ready! Run 'npm install && npm start' in the project directory to start development."
        }
        
    except Exception as e:
        logger.error(f"Project creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_working_project(project_id: str, template: str, name: str, description: str, features: list) -> int:
    """Generate actual project files using AI based on user requirements"""
    try:
        logger.info(f"🤖 Using AI to generate project: {name}")
        
        # Prepare AI prompt with user requirements
        ai_prompt = f"""Create a complete, production-ready {template} project with the following specifications:

Project Name: {name}
Description: {description}
Features: {', '.join(features) if features else 'Basic functionality'}

Generate COMPLETE, FUNCTIONAL code files for this project. Include:
1. All necessary configuration files (package.json, tsconfig.json, etc.)
2. Core application files with real functionality
3. Proper project structure
4. Working dependencies
5. README with accurate setup instructions

Return the response as a JSON object with this structure:
{{
    "files": {{
        "path/to/file1": "complete file content here",
        "path/to/file2": "complete file content here"
    }}
}}

Make sure all code is production-ready and actually works."""

        # Try OpenAI first, fallback to Anthropic
        files_data = {}
        try:
            # Use OpenAI for project generation with increased token limit
            openai_client = openai.OpenAI()
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",  # Use more efficient model
                messages=[
                    {"role": "system", "content": "You are an expert software architect who creates complete, working project structures. Always return valid JSON with complete file contents."},
                    {"role": "user", "content": ai_prompt}
                ],
                max_tokens=16000,  # Increased from 4000 to 16000
                temperature=0.3
            )
            
            # Parse the AI response
            ai_content = response.choices[0].message.content.strip()
            if ai_content.startswith('```json'):
                ai_content = ai_content[7:-3].strip()
            elif ai_content.startswith('```'):
                ai_content = ai_content[3:-3].strip()
            
            files_data = json.loads(ai_content)
            logger.info(f"✅ OpenAI generated {len(files_data.get('files', {}))} files")
            
        except Exception as openai_error:
            logger.warning(f"OpenAI failed, trying Anthropic: {openai_error}")
            try:
                # Fallback to Anthropic with increased token limit
                anthropic_client = anthropic.Anthropic()
                response = await asyncio.to_thread(
                    anthropic_client.messages.create,
                    model="claude-3-haiku-20240307",  # Use faster, cheaper model
                    max_tokens=8000,  # Increased from 4000 to 8000
                    messages=[
                        {"role": "user", "content": ai_prompt}
                    ]
                )
                
                ai_content = response.content[0].text.strip()
                if ai_content.startswith('```json'):
                    ai_content = ai_content[7:-3].strip()
                elif ai_content.startswith('```'):
                    ai_content = ai_content[3:-3].strip()
                
                files_data = json.loads(ai_content)
                logger.info(f"✅ Anthropic generated {len(files_data.get('files', {}))} files")
                
            except Exception as anthropic_error:
                logger.error(f"Both AI services failed. OpenAI: {openai_error}, Anthropic: {anthropic_error}")
                raise HTTPException(status_code=500, detail="AI project generation failed - please check API keys")

        # Create the actual files
        project_path = fs_service.get_project_path(project_id)
        files_created = 0
        
        for file_path, content in files_data.get('files', {}).items():
            try:
                full_path = project_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle JSON content properly
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2)
                elif not isinstance(content, str):
                    content = str(content)
                
                # Write file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_created += 1
                logger.info(f"📄 Created: {file_path}")
                
            except Exception as file_error:
                logger.error(f"Failed to create {file_path}: {file_error}")
                continue
        
        if files_created == 0:
            raise HTTPException(status_code=500, detail="No files were created - AI response may be invalid")
        
        logger.info(f"✅ AI generated project with {files_created} files")
        return files_created
        
    except Exception as e:
        logger.error(f"AI project generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Project generation failed: {str(e)}")

# Preview Management API Endpoints
@app.post("/api/projects/{project_id}/start")
async def start_project_development_endpoint(project_id: str, db: Session = Depends(get_db)):
    """Start a development server for a project"""
    try:
        # Get project info from database
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        logger.info(f"� Starting development server for project {project_id}")
        
        # Start the development server
        result = await dev_server_manager.start_development_server(project_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Development server started successfully",
                "url": result["url"],
                "port": result["port"],
                "status": result["status"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Development server start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/stop")
async def stop_project_development_endpoint(project_id: str):
    """Stop the development server for a project"""
    try:
        success = await dev_server_manager.stop_server(project_id)
        
        if success:
            return {
                "success": True,
                "message": "Development server stopped successfully"
            }
        else:
            return {
                "success": False,
                "message": "No development server running for this project"
            }
            
    except Exception as e:
        logger.error(f"Development server stop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/status")
async def get_project_development_status(project_id: str):
    """Get the development server status for a project"""
    try:
        status = await dev_server_manager.get_server_status(project_id)
        return {
            "success": True,
            "project_id": project_id,
            **status
        }
        
    except Exception as e:
        logger.error(f"Development server status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/development/servers")
async def list_all_development_servers():
    """List all running development servers"""
    try:
        servers = await dev_server_manager.list_running_servers()
        return {
            "success": True,
            "servers": servers,
            "count": len(servers)
        }
        
    except Exception as e:
        logger.error(f"Development servers list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/install-dependencies")
async def install_project_dependencies(project_id: str):
    """Install dependencies for a project"""
    try:
        project_path = fs_service.get_project_path(project_id)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check for package.json
        package_json_path = project_path / "package.json"
        requirements_path = project_path / "requirements.txt"
        
        if package_json_path.exists():
            # Node.js project
            command = "npm install"
        elif requirements_path.exists():
            # Python project
            command = "pip install -r requirements.txt"
        else:
            raise HTTPException(status_code=400, detail="No package.json or requirements.txt found")
        
        # Execute installation command
        result = await execute_project_command(project_id, command)
        
        return {
            "success": result["success"],
            "output": result["output"],
            "command": command
        }
        
    except Exception as e:
        logger.error(f"Dependency installation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/terminal/execute")
async def execute_terminal_command(command_data: dict):
    """Execute a terminal command in a project"""
    try:
        project_id = command_data.get("project_id")
        command = command_data.get("command")
        
        if not project_id or not command:
            raise HTTPException(status_code=400, detail="project_id and command are required")
        
        # Execute the command
        result = await execute_project_command(project_id, command)
        
        return {
            "success": result["success"],
            "output": result["output"],
            "return_code": result.get("return_code", -1),
            "command": result.get("command", command)
        }
        
    except Exception as e:
        logger.error(f"Terminal execution error: {e}")
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
        log_level="info",
        reload_excludes=[
            "projects/*/node_modules/*",
            "projects/*/build/*", 
            "projects/*/.next/*",
            "projects/*/.git/*",
            "*.pyc",
            "*/__pycache__/*"
        ]
    )
