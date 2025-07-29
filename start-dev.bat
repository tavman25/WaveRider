@echo off
echo Starting WaveRider Development Environment...
echo.

echo Setting up environment variables...
if not exist .env.local (
    echo ERROR: .env.local file not found!
    echo Please add your API keys to .env.local file
    pause
    exit /b 1
)

echo Starting Python Backend Server...
start "WaveRider Backend" cmd /k "cd /d %~dp0 && C:/Users/Bill/Documents/Dev2025/WaveRider/.venv/Scripts/python.exe backend/server.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting Next.js Frontend...
start "WaveRider Frontend" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo WaveRider Development Environment Started!
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8002
echo.
echo Press any key to stop all services...
pause >nul

echo Stopping services...
taskkill /f /im node.exe 2>nul
taskkill /f /im python.exe 2>nul
echo Done!
