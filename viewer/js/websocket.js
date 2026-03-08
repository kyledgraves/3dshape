// viewer/js/websocket.js

const WS_URL = `ws://${window.location.hostname}:8080`;
let socket = null;
let currentMode = 'iso';

const ViewerWebSocket = {
    connect: function() {
        if (socket && (socket.readyState === WebSocket.CONNECTING || socket.readyState === WebSocket.OPEN)) {
            console.log('Already connected or connecting.');
            return;
        }

        console.log(`Attempting to connect to ${WS_URL}...`);
        socket = new WebSocket(WS_URL);

        const btnConnect = document.getElementById('btn-connect');
        const imgStream = document.getElementById('stream');
        const placeholder = document.getElementById('placeholder');

        socket.onopen = () => {
            console.log('WebSocket connection established.');
            btnConnect.textContent = 'Connected';
            btnConnect.disabled = true;
            btnConnect.classList.add('connected');
            
            // As soon as we connect, let the server know exactly how big our window is
            // so it can render a perfect 1:1 pixel frame without stretching!
            this.sendResize(window.innerWidth, window.innerHeight);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'frame' && data.image) {
                    if (placeholder.style.display !== 'none') {
                        placeholder.style.display = 'none';
                        imgStream.style.display = 'block';
                    }

                    if (data.image.startsWith('data:image')) {
                        imgStream.src = data.image;
                    } else {
                        imgStream.src = `data:image/jpeg;base64,${data.image}`;
                    }
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        socket.onclose = () => {
            console.log('WebSocket connection closed.');
            btnConnect.textContent = 'Connect';
            btnConnect.disabled = false;
            btnConnect.classList.remove('connected');
            socket = null;
            
            placeholder.style.display = 'block';
            imgStream.style.display = 'none';
        };

        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    },

    sendCommand: function(type, mode) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            currentMode = mode;
            const command = { type: type, mode: mode };
            socket.send(JSON.stringify(command));
        } else {
            console.warn('WebSocket not connected. Cannot send command.');
        }
    },
    
    sendResize: function(width, height) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const command = { type: 'resize', width: width, height: height };
            socket.send(JSON.stringify(command));
            console.log('Requested Server Resize:', width, height);
        }
    },

    sendInteraction: function(command) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(command));
        } else {
            console.warn('WebSocket not connected. Cannot send interaction.');
        }
    }
};

window.ViewerWebSocket = ViewerWebSocket;
