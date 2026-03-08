const WebSocket = require('ws');
const { handleConnection } = require('./websocket-handler');
const { initHeadlessRenderer } = require('./playwright-renderer');

const PORT = process.env.PORT || 8080;

async function bootstrap() {
    // 1. Initialize our powerful Headless 3D Engine first
    await initHeadlessRenderer();

    // 2. Start WebSocket Server for Thin Clients to connect
    const wss = new WebSocket.Server({ port: PORT });
    
    wss.on('connection', (ws) => {
        console.log('Client connected to WebSocket Viewer Stream');
        handleConnection(ws);
    });
    
    console.log(`WebSocket server started on port ${PORT}`);
}

// Start everything up
bootstrap().catch(err => {
    console.error('Fatal initialization error:', err);
    process.exit(1);
});
