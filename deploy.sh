#!/bin/bash
set -e

# Change to the project directory
cd "$(dirname "$0")"

echo "========================================"
echo "🚀 3D SHAPE VIEWER DEPLOYMENT PIPELINE "
echo "========================================"

echo "🧹 1. Cleaning up previous deployments..."
./stop_all.sh

echo "📦 2. Starting backend, render engine, and viewer servers..."
./start_all.sh

echo "⏳ 3. Waiting 5 seconds for WebGL headless browser to launch and APIs to bind ports..."
sleep 5

echo "🧪 4. Running automated test suite (Backend + Visual UI)..."
if ./run_tests.sh; then
    echo "========================================"
    echo "✅ DEPLOYMENT SUCCESSFUL! All 31 Tests Passed."
    echo "🌐 You can safely connect at: http://100.73.95.42:8082"
    echo "========================================"
else
    echo "========================================"
    echo "❌ DEPLOYMENT FAILED! Tests did not pass."
    echo "📜 Rolling back and shutting down broken servers..."
    ./stop_all.sh
    echo "========================================"
    exit 1
fi
