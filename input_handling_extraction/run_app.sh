#!/bin/bash

echo "✈️ Starting Flight Booking Chat App..."

# tart FastAPI backend in background
echo "🚀 Starting FastAPI backend..."
poetry run uvicorn fastapi_app.main:app --reload --port 8000 &
FASTAPI_PID=$!

# wait 2 seconds
sleep 2

# start Streamlit frontend in background
echo "🚀 Starting Streamlit frontend..."
poetry run streamlit run streamlit_app/home.py --server.port 8501 &
STREAMLIT_PID=$!

# Wait 3 seconds for both services to start
sleep 3

# Open browsers
echo "🌐 Opening browsers..."
# open http://localhost:8501  # streamlit frontend
open http://localhost:8000/docs  # FastAPI docs

echo ""
echo "🎉 Both services are running!"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for user to press Ctrl+C
wait 