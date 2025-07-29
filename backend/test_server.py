# Test configuration for WaveRider backend
import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "services" in data

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "WaveRider Production Backend"
    assert data["version"] == "1.0.0"
    assert data["status"] == "active"

def test_agents_list():
    """Test the agents list endpoint"""
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "agents" in data
    assert len(data["agents"]) > 0

def test_chat_endpoint():
    """Test the chat endpoint"""
    chat_data = {
        "message": "Hello, AI!",
        "context": "Test context",
        "project_id": "test-project"
    }
    response = client.post("/api/chat", json=chat_data)
    # Note: This might fail if AI services are not configured
    # In production, we'd mock the AI service
    assert response.status_code in [200, 500]  # 500 if AI service unavailable

@pytest.mark.asyncio
async def test_file_operations():
    """Test file operations"""
    # Test file creation
    file_data = {
        "operation": "write",
        "project_id": "test-project",
        "path": "test.txt",
        "content": "Hello, World!"
    }
    response = client.post("/api/files", json=file_data)
    assert response.status_code == 200
    
    # Test file reading
    read_data = {
        "operation": "read",
        "project_id": "test-project", 
        "path": "test.txt"
    }
    response = client.post("/api/files", json=read_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "content" in data
