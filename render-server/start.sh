#!/bin/bash
cd "$(dirname "$0")"

# We can optionally use xvfb-run if it's installed and needed for other context creation
# but for now we'll just run node directly.
echo "Starting Render Server..."
node src/index.js
