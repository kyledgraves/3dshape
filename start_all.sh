#!/bin/bash
# start_all.sh
set -e

# Change to the root directory
cd "$(dirname "$0")"

echo "Starting backend server..."
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

echo "Starting render server..."
cd render-server
PORT=8080 node src/index.js > render.log 2>&1 &
RENDER_PID=$!
echo $RENDER_PID > ../render-server.pid
cd ..

echo "Starting static viewer server..."
python3 -m http.server 8082 -d viewer > viewer.log 2>&1 &
VIEWER_PID=$!
echo $VIEWER_PID > viewer.pid

echo "Servers started in the background."
echo "Backend PID: $BACKEND_PID"
echo "Render Server PID: $RENDER_PID"
echo "Viewer Server PID: $VIEWER_PID"
