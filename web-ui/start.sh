#!/bin/bash

echo "🚀 Starting PCM Tenants Configuration Toolkit Web UI"
echo ""
echo "📦 Checking dependencies..."

if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing..."
    pip3 install -r requirements.txt
fi

echo "✅ Dependencies OK"
echo ""
echo "🌐 Starting server..."
echo "📍 Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
