const { getLatestFrame, setCameraMode, setResolution, setOrbit, setPan, setZoom, loadGeometry } = require('./playwright-renderer');

function handleConnection(ws) {
    ws.send(JSON.stringify({ type: 'frame', image: getLatestFrame() }));

    // Update node stream interval from 100ms (10 FPS) to 50ms (20 FPS)
    const interval = setInterval(() => {
        if (ws.readyState === ws.OPEN) {
            const frame = getLatestFrame();
            if (frame) {
                ws.send(JSON.stringify({ type: 'frame', image: frame }));
            }
        }
    }, 50);

    ws.on('message', async (message) => {
        try {
            const command = JSON.parse(message);

            if (command.type === 'view') {
                console.log('Received interaction command:', command.type);
                await setCameraMode(command.mode);
                ws.send(JSON.stringify({ type: 'ack', message: `Camera changed to ${command.mode}` }));
            } else if (command.type === 'resize') {
                console.log(`Received resize command: ${command.width}x${command.height}`);
                const safeW = Math.min(Math.max(command.width, 320), 3840);
                const safeH = Math.min(Math.max(command.height, 240), 2160);
                await setResolution(safeW, safeH);
                ws.send(JSON.stringify({ type: 'ack', message: `Resized to ${safeW}x${safeH}` }));
            } else if (command.type === 'orbit') {
                console.log("Orbit:", command.deltaX, command.deltaY); await setOrbit(command.deltaX, command.deltaY);
            } else if (command.type === 'pan') {
                await setPan(command.deltaX, command.deltaY);
            } else if (command.type === 'zoom') {
                await setZoom(command.deltaY);
            } else if (command.type === 'load') {
                console.log(`Loading geometry ID: ${command.geometryId}`);
                const result = await loadGeometry(command.geometryId);
                if (result) {
                    ws.send(JSON.stringify({ type: 'ack', message: `Loaded geometry ${command.geometryId}` }));
                } else {
                    ws.send(JSON.stringify({ type: 'error', message: 'Failed to load geometry' }));
                }
            }
        } catch (error) {
            console.error('Failed to parse message:', error);
            ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON' }));
        }
    });

    ws.on('close', () => {
        clearInterval(interval);
        console.log('Client disconnected from viewport stream');
    });
}

module.exports = { handleConnection };
