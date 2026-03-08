# Agent Instructions

## Deployment & Testing Protocol
When working on the 3D Shape Viewer system, agents **MUST ALWAYS** use the `./deploy.sh` script to verify changes.

Do **NOT** manually run `start_all.sh`, `stop_all.sh`, or `pytest` individually unless explicitly debugging a specific failure.

### The `./deploy.sh` Pipeline:
1. Automatically scrubs memory for zombie processes and stops all servers cleanly.
2. Starts the FastAPI backend, Node.js Render Server, and HTML5 Viewer server.
3. Waits for the headless WebGL Chromium instance to initialize.
4. Runs the complete automated test suite (Backend API tests + Playwright Visual E2E tests).
5. Exits with a success or failure message, ensuring the environment is perfectly clean for the user.

### Making Changes
After editing Python, Node.js, or HTML/CSS files:
```bash
cd /home/ubuntu/github/3dshape
./deploy.sh
```
If the deployment script fails, immediately read the pytest output, fix the regression, and rerun `./deploy.sh` until you see:
`✅ DEPLOYMENT SUCCESSFUL! All Tests Passed.`
