// viewer/js/viewer.js

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing 3D CAD Viewer Phase 4 Client...');
    
    // Initialize the UI controls and event listeners
    if (window.ViewerControls) {
        window.ViewerControls.init();
    } else {
        console.error('ViewerControls module not loaded.');
    }
    
    // Optional: automatically connect on load (uncomment if desired)
    // window.ViewerWebSocket.connect();
});

// Dynamic Resizing - listen to the browser window and send to the server
let resizeTimeout;
window.addEventListener('resize', () => {
    // Debounce the resize to avoid hammering the server
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        if (window.ViewerWebSocket) {
            window.ViewerWebSocket.sendResize(window.innerWidth, window.innerHeight);
        }
    }, 200);
});
