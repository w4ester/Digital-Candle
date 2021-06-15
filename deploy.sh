#!/bin/bash
# Digital-Candle deployment script
# Deploys the vigil candle server with redis backend

echo "=================================================="
echo "  Digital-Candle Deploy"
echo "=================================================="

# Check for redis
if ! command -v redis-cli &> /dev/null; then
    echo "ERROR: redis-cli not found"
    echo "Install redis: sudo apt-get install redis-server"
    exit 1
fi

# Check redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: redis is not running"
    echo "Start redis: sudo systemctl start redis"
    exit 1
fi

echo "Redis is running"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run with redis backend on port 5000
echo ""
echo "=================================================="
echo "  Starting Digital-Candle"
echo "  Store: redis"
echo "  Port: 5000"
echo "=================================================="

python web/app.py --store redis --port 5000
