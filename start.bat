@echo off
echo ==================================================
echo   Starting Royal Album Generator (Local Mode)
echo ==================================================
echo.

echo [1/2] Starting FastAPI Backend on port 8008...
start "Album Backend" cmd /k ".\.venv\Scripts\python -m uvicorn main:app --app-dir backend --port 8008 --host 127.0.0.1"

echo [2/2] Starting React Frontend on port 5173...
cd frontend
start "Album Frontend" cmd /k "npm run dev"

echo.
echo Both servers are booting up in separate windows!
echo Once the frontend is ready, open http://localhost:5173 in your browser.
pause
