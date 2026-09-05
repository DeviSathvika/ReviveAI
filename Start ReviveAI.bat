@echo off
title ReviveAI Launcher

cd /d "%~dp0"

echo ========================================
echo           REVIVEAI LAUNCHER
echo ========================================
echo.
echo Starting FastAPI backend...
echo.

start "ReviveAI Backend" cmd /k "call .venv\Scripts\activate && uvicorn api.main:app --reload"

timeout /t 3 /nobreak >nul

echo Starting React frontend...
echo.

start "ReviveAI Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 5 /nobreak >nul

echo Opening ReviveAI dashboard...
start "" "http://localhost:5173"

echo.
echo ========================================
echo        REVIVEAI IS RUNNING
echo ========================================
echo.
echo Dashboard: http://localhost:5173
echo API:       http://localhost:8000
echo.
echo Keep the two terminal windows open.
echo Close them when you want to stop ReviveAI.
echo.
pause