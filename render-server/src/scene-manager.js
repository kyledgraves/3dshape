let currentMode = 'iso';

function updateCamera(mode) {
    currentMode = mode;
    console.log(`Updating camera to mode: ${mode}`);
}

function getMode() {
    return currentMode;
}

function update(data) {
    console.log('Updating scene with data:', data);
}

function getScene() {
    return {};
}

function getCamera() {
    return {};
}

module.exports = { updateCamera, getMode, update, getScene, getCamera };
