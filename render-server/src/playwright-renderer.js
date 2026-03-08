const { chromium } = require('playwright');
const path = require('path');
const express = require('express');
const http = require('http');

let browser;
let page;
let latestFrameBase64 = null;
let app;
let server;

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

function fetchGeometryFromBackend(geometryId) {
    return new Promise((resolve, reject) => {
        const url = `${BACKEND_URL}/api/v1/geometry/${geometryId}/render-data`;
        console.log(`Fetching geometry from: ${url}`);
        
        http.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const geometry = JSON.parse(data);
                    console.log(`Loaded geometry: ${geometry.format} v${geometry.version}, ${geometry.vertex_count} vertices`);
                    resolve(geometry);
                } catch (e) {
                    reject(new Error(`Failed to parse geometry response: ${e.message}`));
                }
            });
        }).on('error', (e) => {
            reject(new Error(`Failed to fetch geometry: ${e.message}`));
        });
    });
}

async function loadGeometry(geometryId) {
    if (!page) {
        console.log('Page not ready, cannot load geometry');
        return null;
    }
    
    try {
        const geometry = await fetchGeometryFromBackend(geometryId);
        
        if (geometry && geometry.data) {
            await page.evaluate((geomData) => {
                if (window.loadGeometryFromData) {
                    window.loadGeometryFromData(geomData);
                } else {
                    console.log('loadGeometryFromData not available, using fallback');
                    window.pendingGeometryData = geomData;
                }
            }, geometry.data);
            return geometry;
        }
        return null;
    } catch (e) {
        console.error('Failed to load geometry:', e.message);
        return null;
    }
}

async function initHeadlessRenderer() {
    console.log('Starting local HTTP server to host headless WebGL renderer...');
    app = express();
    app.use(express.static(path.join(__dirname, '../public')));
    
    server = app.listen(8083, async () => {
        console.log('Internal HTTP server running on port 8083');
        
        console.log('Launching headless Chromium via Playwright...');
        browser = await chromium.launch({
            args: [
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--use-gl=swiftshader',     // Use software rasterizer (CPU WebGL)
                '--disable-gpu',
                '--hide-scrollbars',
                '--mute-audio'
            ]
        });
        
        // Boot at 1920x1080 resolution initially
        page = await browser.newPage({
            viewport: { width: 1920, height: 1080 }
        });

        await page.exposeFunction('sendFrameToServer', (dataUrl) => {
            latestFrameBase64 = dataUrl;
        });

        page.on('console', msg => console.log('Headless Console:', msg.text()));
        page.on('pageerror', err => console.log('Headless Page Error:', err.message));

        await page.goto('http://localhost:8083/headless.html');
        console.log('Headless 3D context loaded and rendering!');
    });
}

function getLatestFrame() {
    if (!latestFrameBase64) {
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";
    }
    return latestFrameBase64;
}

async function setCameraMode(mode) {
    if (page) {
        await page.evaluate(`window.updateCameraMode('${mode}')`);
    }
}

async function setResolution(width, height) {
    if (page) {
        console.log(`Resizing headless renderer to ${width}x${height}`);
        await page.setViewportSize({ width, height });
        // Optional safety: evaluate JS explicitly if resize events are swallowed
        await page.evaluate(`if(window.resizeRenderer) window.resizeRenderer(${width}, ${height})`).catch(e => console.log(e));
    }
}

async function setOrbit(dx, dy) {
    if (page) {
        await page.evaluate(`if(window.applyOrbit) window.applyOrbit(${dx}, ${dy})`).catch(e => console.log(e));
    }
}

async function setPan(dx, dy) {
    if (page) {
        await page.evaluate(`if(window.applyPan) window.applyPan(${dx}, ${dy})`).catch(e => console.log(e));
    }
}

async function setZoom(dy) {
    if (page) {
        await page.evaluate(`if(window.applyZoom) window.applyZoom(${dy})`).catch(e => console.log(e));
    }
}

async function closeRenderer() {
    if (browser) await browser.close();
    if (server) server.close();
}

module.exports = { initHeadlessRenderer, getLatestFrame, setCameraMode, setResolution, setOrbit, setPan, setZoom, closeRenderer, loadGeometry };
