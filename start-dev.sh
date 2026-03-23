#!/bin/bash

echo "🚀 Solutions Toolkit - Development Mode"
echo ""

BASEDIR="$(cd "$(dirname "$0")" && pwd)"

# Install frontend dependencies if needed
if [ ! -d "$BASEDIR/frontend/node_modules" ] || [ ! -d "$BASEDIR/frontend/node_modules/react" ]; then
    echo "📦 Installing frontend dependencies..."
    (cd "$BASEDIR/frontend" && npm install)
    echo ""
fi

# Check Python Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing..."
    pip3 install -r "$BASEDIR/web-ui/requirements.txt"
fi

echo "✅ Dependencies OK"
echo ""

# Start Flask backend on port 5000
echo "🐍 Starting Flask backend on http://localhost:5000..."
(cd "$BASEDIR/web-ui" && python3 app.py) &
FLASK_PID=$!

# Start React frontend on port 3000
echo "⚛️  Starting React frontend on http://localhost:3000..."
(cd "$BASEDIR/frontend" && npm run dev) &
VITE_PID=$!

echo ""
echo "📍 Open http://localhost:3000 in your browser"
echo "   (API requests proxy to Flask on port 5000)"
echo ""
echo "Press Ctrl+C to stop both servers"

# Trap Ctrl+C to kill both processes
trap "kill $FLASK_PID $VITE_PID 2>/dev/null; exit" INT TERM
wait
