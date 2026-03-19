#!/bin/bash

echo "🚀 PCM Tenants Configuration Toolkit - Development Mode"
echo ""

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ] || [ ! -d "frontend/node_modules/react" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    echo ""
fi

# Check Python Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing..."
    pip3 install -r web-ui/requirements.txt
fi

echo "✅ Dependencies OK"
echo ""

# Start Flask backend on port 5000
echo "🐍 Starting Flask backend on http://localhost:5000..."
cd web-ui && python3 app.py &
FLASK_PID=$!
cd ..

# Start React frontend on port 3000
echo "⚛️  Starting React frontend on http://localhost:3000..."
cd frontend && npm run dev &
VITE_PID=$!
cd ..

echo ""
echo "📍 Open http://localhost:3000 in your browser"
echo "   (API requests proxy to Flask on port 5000)"
echo ""
echo "Press Ctrl+C to stop both servers"

# Trap Ctrl+C to kill both processes
trap "kill $FLASK_PID $VITE_PID 2>/dev/null; exit" INT TERM
wait
