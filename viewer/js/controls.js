// viewer/js/controls.js

document.addEventListener('DOMContentLoaded', () => {
    const btnConnect = document.getElementById('btn-connect');
    const btnLeft = document.getElementById('btn-left');
    const btnRight = document.getElementById('btn-right');
    const btnFront = document.getElementById('btn-front');
    const btnBack = document.getElementById('btn-back');
    const btnIso = document.getElementById('btn-iso');
    const stream = document.getElementById('stream');

    btnConnect.addEventListener('click', () => {
        if (window.ViewerWebSocket) {
            window.ViewerWebSocket.connect();
        }
    });

    btnLeft.addEventListener('click', () => {
        if (window.ViewerWebSocket) window.ViewerWebSocket.sendCommand('view', 'left');
    });

    btnRight.addEventListener('click', () => {
        if (window.ViewerWebSocket) window.ViewerWebSocket.sendCommand('view', 'right');
    });

    btnFront.addEventListener('click', () => {
        if (window.ViewerWebSocket) window.ViewerWebSocket.sendCommand('view', 'front');
    });

    btnBack.addEventListener('click', () => {
        if (window.ViewerWebSocket) window.ViewerWebSocket.sendCommand('view', 'back');
    });

    btnIso.addEventListener('click', () => {
        if (window.ViewerWebSocket) window.ViewerWebSocket.sendCommand('view', 'iso');
    });

    // Load geometry button
    const btnLoad = document.getElementById('btn-load');
    const geometryIdInput = document.getElementById('geometry-id');

    btnLoad.addEventListener('click', () => {
        const geometryId = geometryIdInput.value;
        if (geometryId && window.ViewerWebSocket) {
            console.log('Loading geometry ID:', geometryId);
            window.ViewerWebSocket.socket.send(JSON.stringify({
                type: 'load',
                geometryId: parseInt(geometryId)
            }));
        }
    });

    // === MOUSE CONTROLS FOR ORBIT / PAN / ZOOM ===
    
    let isDragging = false;
    let dragMode = null; // 'orbit' or 'pan'
    let lastX = 0;
    let lastY = 0;

    // Prevent default context menu when right-clicking the stream so we can use it for panning
    stream.addEventListener('contextmenu', (e) => {
        e.preventDefault();
    });

    stream.addEventListener('mousedown', (e) => {
        if (!window.ViewerWebSocket || !stream.src.startsWith('data:image')) return;
        
        isDragging = true;
        lastX = e.clientX;
        lastY = e.clientY;

        // Left click = 0 (Orbit)
        // Middle click = 1 (Pan)
        // Right click = 2 (Pan)
        if (e.button === 0) {
            dragMode = 'orbit';
        } else {
            dragMode = 'pan';
        }
        
        e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const deltaX = e.clientX - lastX;
        const deltaY = e.clientY - lastY;
        
        if (deltaX === 0 && deltaY === 0) return;

        lastX = e.clientX;
        lastY = e.clientY;

        // Send interaction payload to the server
        window.ViewerWebSocket.sendInteraction({
            type: dragMode,
            deltaX: deltaX,
            deltaY: deltaY
        });
    });

    window.addEventListener('mouseup', () => {
        isDragging = false;
        dragMode = null;
    });

    stream.addEventListener('wheel', (e) => {
        if (!window.ViewerWebSocket || !stream.src.startsWith('data:image')) return;
        
        e.preventDefault();
        
        // Use deltaY to control zoom direction and magnitude
        window.ViewerWebSocket.sendInteraction({
            type: 'zoom',
            deltaY: e.deltaY
        });
    }, { passive: false });
});
