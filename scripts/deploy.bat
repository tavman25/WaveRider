@echo off
REM WaveRider Production Deployment Script for Windows

echo 🌊 Starting WaveRider Production Deployment...

REM Set production environment
set NODE_ENV=production

REM Install dependencies
echo 📦 Installing dependencies...
call npm ci --only=production

REM Build frontend
echo 🔨 Building frontend...
call npm run build

REM Install backend dependencies
echo 🐍 Installing backend dependencies...
cd backend
call pip install -r requirements.txt

REM Start production services
echo 🚀 Starting production services...
cd ..

REM Start backend
start "WaveRider Backend" cmd /k "python backend/server.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start agents
start "WaveRider Agents" cmd /k "python agents/agent_server.py"

REM Wait a moment for agents to start
timeout /t 3 /nobreak > nul

REM Start frontend
start "WaveRider Frontend" cmd /k "npm start"

echo ✅ WaveRider deployed successfully!
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8002
echo 🤖 Agents: http://localhost:8001
echo 📋 Check the opened command windows for logs
pause
