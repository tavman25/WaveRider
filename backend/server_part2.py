# Continuation of server.py - API Routes

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

# Additional utility endpoints
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

# Global start time for uptime tracking
start_time = time.time()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
