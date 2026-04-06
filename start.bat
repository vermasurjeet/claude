@echo off
echo ========================================
echo   Indian Stock Market Analyzer
echo ========================================
echo.
echo Starting Backend (port 8000)...
start "Stock Analyzer - Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --reload"

echo Starting Frontend (port 5173)...
start "Stock Analyzer - Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo Both servers starting...
echo.
echo Open http://localhost:5173 in your browser
echo.
echo To stop: close both command prompt windows
pause
