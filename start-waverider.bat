@echo off
echo Starting WaveRider Development Environment...
echo.

echo [1/2] Starting Backend (Port 8002)...
start "WaveRider Backend" cmd /c "cd /d %~dp0 && python -m uvicorn backend.server:app --reload --port 8002"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend (Port 3000)...
start "WaveRider Frontend" cmd /c "cd /d %~dp0 && npm run dev"

echo.
echo ✅ WaveRider is starting up!
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend:  http://localhost:8002
echo 📖 API Docs: http://localhost:8002/api/docs
echo.
echo Press any key to continue...
pause >nul
