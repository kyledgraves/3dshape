#!/bin/bash
# stop_all.sh

cd "$(dirname "$0")"
echo "Stopping all services..."

# Read PIDs gracefully
for pid_file in backend.pid render-server.pid viewer.pid; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        echo "Stopping service from $pid_file (PID $PID)..."
        kill $PID 2>/dev/null || true
        rm "$pid_file"
    fi
done

# Force kill any lingering zombie processes to free up ports and memory
echo "Scrubbing memory for zombie processes..."
pkill -f "uvicorn backend.main" 2>/dev/null || true
pkill -f "node src/index.js" 2>/dev/null || true
pkill -f "python3 -m http.server 808" 2>/dev/null || true
killall -9 chrome 2>/dev/null || true
killall -9 chromium-browser 2>/dev/null || true
killall -9 chrome_crashpad_handler 2>/dev/null || true

echo "All servers stopped securely."
