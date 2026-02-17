#!/bin/bash
# CV Tracker - Startup Script
# Prerequisites: Docker, Python 3.11+, uv (or pip)

set -e

echo "=== CV Tracker & Smart ATS Matcher ==="
echo ""

# Step 1: Start PostgreSQL and Redis
echo "1. Starting PostgreSQL and Redis..."
docker-compose up -d
sleep 3

# Step 2: Create virtual environment and install deps
if [ ! -d ".venv" ]; then
    echo "2. Creating virtual environment..."
    uv venv .venv
fi

echo "2. Installing dependencies..."
source .venv/bin/activate
uv pip install -e ".[dev]"

# Step 3: Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "3. Creating .env from .env.example..."
    cp .env.example .env
    echo "   Please edit .env and add your GROQ_API_KEY"
fi

# Step 4: Run database migrations
echo "4. Running database migrations..."
alembic upgrade head

# Step 5: Start services
echo ""
echo "=== Starting Services ==="
echo ""

# Start Celery worker in background
echo "5. Starting Celery worker..."
celery -A backend.tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

# Start FastAPI backend
echo "6. Starting FastAPI backend on http://localhost:8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend &
FASTAPI_PID=$!

sleep 2

# Start Streamlit frontend
echo "7. Starting Streamlit frontend on http://localhost:8501..."
streamlit run frontend/app.py --server.port 8501 &
STREAMLIT_PID=$!

echo ""
echo "=== All services started! ==="
echo "  Backend API:  http://localhost:8000/docs"
echo "  Frontend UI:  http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"

# Cleanup on exit
cleanup() {
    echo "Stopping services..."
    kill $CELERY_PID $FASTAPI_PID $STREAMLIT_PID 2>/dev/null
    echo "Done."
}
trap cleanup EXIT

wait
