#!/bin/bash
# Digital-Candle deployment script
# NOTE: eventlet conflicts with flask debug mode
# Do not use --debug with eventlet

echo "=================================================="
echo "  Digital-Candle Deploy"
echo "=================================================="

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Run WITHOUT debug flag -- eventlet and debug reloader conflict
python web/app.py --port 5000
