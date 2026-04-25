#!/bin/bash
# TalentScout — Start both backend and frontend

echo "🚀 Starting TalentScout AI..."

# Start FastAPI backend
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ Backend started on http://localhost:8000 (PID: $BACKEND_PID)"

# Start Next.js frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started on http://localhost:3000 (PID: $FRONTEND_PID)"

echo ""
echo "─────────────────────────────────────────"
echo "  TalentScout is running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "─────────────────────────────────────────"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" INT
wait
