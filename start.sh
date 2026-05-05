#!/bin/bash
export PORT=5000

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt || \
    echo "Pip install failed, but continuing..."
fi

echo "Starting application..."
python3 main.py