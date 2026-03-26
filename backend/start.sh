#!/bin/bash
echo "╔══════════════════════════════════════════════╗"
echo "║       NexusAI Productivity Platform          ║"
echo "║            Starting Backend...               ║"
echo "╚══════════════════════════════════════════════╝"

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

#!/bin/bash
echo "╔══════════════════════════════════════════════╗"
echo "║       NexusAI Productivity Platform          ║"
echo "║            Starting Backend...               ║"
echo "╚══════════════════════════════════════════════╝"

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install deps
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Start the server
echo "🚀 Starting server..."
python3 main.py

echo "🚀 Starting FastAPI backend on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo ""
python3 main.py
