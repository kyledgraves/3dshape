const THREE = require('three');
const sceneManager = require('./scene-manager');
const jpeg = require('jpeg-js');

const width = 800;
const height = 600;

let time = 0;

function generateMockFrame() {
    time += 0.2; // Move wave animation
    const mode = sceneManager.getMode();
    let rMulti = 1, gMulti = 1, bMulti = 1;

    // Pick colors based on the camera angle being requested
    switch(mode) {
        case 'left': rMulti = 1.0; gMulti = 0.2; bMulti = 0.2; break;   // Red
        case 'right': rMulti = 0.2; gMulti = 1.0; bMulti = 0.2; break;  // Green
        case 'front': rMulti = 0.2; gMulti = 0.2; bMulti = 1.0; break;  // Blue
        case 'back': rMulti = 1.0; gMulti = 1.0; bMulti = 0.2; break;   // Yellow
        case 'iso': rMulti = 1.0; gMulti = 0.5; bMulti = 1.0; break;    // Purple
        default: rMulti = 0.8; gMulti = 0.8; bMulti = 0.8; break;       // Gray
    }

    const frameData = Buffer.alloc(width * height * 4);
    
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const i = (y * width + x) * 4;
            
            // Background gradient
            let bgFactor = (y / height) * 0.5;
            
            // Simulated 3D object mask (a circle in the center)
            const cx = width / 2;
            const cy = height / 2;
            const radius = 200;
            const dist = Math.sqrt(Math.pow(x - cx, 2) + Math.pow(y - cy, 2));
            
            if (dist < radius) {
                // Inside the "3D object"
                // Add some fake shading based on distance and time
                let shade = Math.cos(dist * 0.05 - time) * 100 + 155;
                
                // Color the object based on the mode
                frameData[i] = Math.min(255, shade * rMulti);       // R
                frameData[i+1] = Math.min(255, shade * gMulti);     // G
                frameData[i+2] = Math.min(255, shade * bMulti);     // B
            } else {
                // Background
                frameData[i] = 40 + bgFactor * 100;
                frameData[i+1] = 40 + bgFactor * 100;
                frameData[i+2] = 50 + bgFactor * 120;
            }
            
            frameData[i+3] = 255; // A
        }
    }
    
    const rawImageData = { data: frameData, width, height };
    const jpegImageData = jpeg.encode(rawImageData, 40); // 40% quality for fast streaming
    return "data:image/jpeg;base64," + jpegImageData.data.toString('base64');
}

function renderFrame() {
    return generateMockFrame();
}

module.exports = { renderFrame };
