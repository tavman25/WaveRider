#!/bin/bash
# WaveRider Production Deployment Script

echo "🌊 Starting WaveRider Production Deployment..."

# Set production environment
export NODE_ENV=production

# Install dependencies
echo "📦 Installing dependencies..."
npm ci --only=production

# Build frontend
echo "🔨 Building frontend..."
npm run build

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
python -c "
from server import Base, engine
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

# Start production services
echo "🚀 Starting production services..."
cd ..

# Start backend
nohup python backend/server.py > backend.log 2>&1 &
echo $! > backend.pid

# Start agents
nohup python agents/agent_server.py > agents.log 2>&1 &
echo $! > agents.pid

# Start frontend
npm start > frontend.log 2>&1 &
echo $! > frontend.pid

echo "✅ WaveRider deployed successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8002" 
echo "🤖 Agents: http://localhost:8001"
echo "📋 Logs: backend.log, agents.log, frontend.log"
echo "🛑 Stop with: npm run stop"
