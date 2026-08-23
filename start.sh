#!/bin/bash
echo "=================================================="
echo "  Starting Royal Album Generator (Mac/Linux Mode)"
echo "=================================================="
echo ""

echo "[1/2] Starting FastAPI Backend on port 8008..."
.venv/bin/python -m uvicorn main:app --app-dir backend --port 8008 --host 127.0.0.1 &
BACKEND_PID=$!

echo "[2/2] Starting React Frontend on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Both servers are running!"
echo "Once the frontend is ready, open http://localhost:5173 in your browser."
echo "Press Ctrl+C to stop both servers."
echo ""

# Catch Ctrl+C and kill the background servers cleanly
trap "echo 'Shutting down servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Wait indefinitely until Ctrl+C is pressed
wait
