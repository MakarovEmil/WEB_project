#!/bin/bash
export PORT=5000
cd WEB_project

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt || \
    echo "Pip install failed, but continuing..."
fi

echo "Starting application..."
python main.py