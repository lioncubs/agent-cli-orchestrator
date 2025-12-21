#!/bin/bash

# Startup script for Agent CLI Orchestrator

echo "🤖 Starting Agent CLI Orchestrator..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
echo "🚀 Starting server on http://localhost:8000"
echo "📱 Web UI available at http://localhost:8000/ui"
echo "📚 API documentation at http://localhost:8000/docs"
echo ""
python main.py
