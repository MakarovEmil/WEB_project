#!/bin/bash
cd Mars_explorer
export PORT=5000

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install --user -r requirements.txt || \
    pip install -r requirements.txt || \
    echo "Pip install failed, but continuing..."
fi

echo "Starting application..."
python main.py