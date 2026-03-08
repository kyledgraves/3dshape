# 3D Shape Ingestion & Viewer System - Implementation Plan

## Overview

This document outlines the implementation plan for building a self-hosted 3D CAD visualization system similar to Vertex3D. The system ingests 3D CAD files (3DXML, CATIA, etc.), stores geometry in PostgreSQL, and serves an HTML5 viewer with server-side rendering.

### Key Characteristics

- **Server-side rendering**: All 3D rendering happens on the server; client receives rendered frames (pixels) not geometry
- **Data security**: CAD/IP never leaves the server
- **Thin client**: Minimal HTML5 client that displays streamed frames
- **Self-hosted**: Deployed on Oracle Cloud VPS (Ubuntu 24.04)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Oracle Cloud VPS                              │
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
│  │  Ingestion  │───▶│ PostgreSQL  │◀───│  Render Server      │   │
│  │  (Python)   │    │  + Geometry │    │  (Node.js + xvfb)  │   │
│  └─────────────┘    └─────────────┘    └─────────────────────┘   │
│        │                                    │                      │
│        ▼                                    ▼                      │
│  ┌─────────────┐                   WebSocket                       │
│  │  REST API   │─────────────────────────────▶ HTML5 Thin Client │
│  └─────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Ingestion API | Python FastAPI | Upload CAD files, trigger conversions |
| Database | PostgreSQL | Store metadata + geometry (BYTEA) |
| Render Server | Node.js + xvfb + Three.js | Server-side WebGL rendering |
| Streaming | WebSocket | Push rendered frames to client |
| Client | Minimal HTML5 | Display frames, send camera commands |

---

## Database Schema

### Core Tables

```sql
-- Accounts (multi-tenant support)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Parts Library - Top-level entity
CREATE TABLE parts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    supplied_id VARCHAR(255),
    name VARCHAR(500),
    description TEXT,
    category VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(account_id, supplied_id)
);

-- Part Revisions - Specific version of a part
CREATE TABLE part_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_id UUID REFERENCES parts(id) ON DELETE CASCADE,
    revision_number VARCHAR(50),
    supplied_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Files - Raw CAD files stored in DB
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_revision_id UUID REFERENCES part_revisions(id),
    original_filename VARCHAR(500),
    file_data BYTEA,
    file_size BIGINT,
    status VARCHAR(50) DEFAULT 'pending'
);

-- Geometry - Converted geometry data (glTF/glb)
CREATE TABLE geometry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_revision_id UUID REFERENCES part_revisions(id),
    format VARCHAR(20) DEFAULT 'glb',
    version VARCHAR(20) DEFAULT 'high',
    vertex_count INTEGER,
    face_count INTEGER,
    bounding_box JSONB,
    data BYTEA,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scenes - Collections of parts for visualization
CREATE TABLE scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scene Items - Parts in a scene with transforms
CREATE TABLE scene_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id UUID REFERENCES scenes(id) ON DELETE CASCADE,
    part_revision_id UUID REFERENCES part_revisions(id),
    transform_matrix JSONB,
    visibility BOOLEAN DEFAULT TRUE
);

-- Render Sessions - Active viewer connections
CREATE TABLE render_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id UUID REFERENCES scenes(id),
    user_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_parts_account ON parts(account_id);
CREATE INDEX idx_part_revisions_part ON part_revisions(part_id);
CREATE INDEX idx_geometry_revision ON geometry(part_revision_id);
CREATE INDEX idx_scenes_account ON scenes(account_id);
CREATE INDEX idx_scene_items_scene ON scene_items(scene_id);
```

---

## Phase 1: Setup & Database

### Week 1

#### 1.1 Install PostgreSQL

```bash
# Install PostgreSQL with PostGIS
sudo apt update
sudo apt install -y postgresql postgresql-contrib postgis

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE USER 3dshape WITH PASSWORD 'your_secure_password';
CREATE DATABASE 3dshape OWNER 3dshape;
\c 3dshape
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
\q
```

#### 1.2 Configure Database

```bash
# Update PostgreSQL config for remote access (if needed)
sudo nano /etc/postgresql/*/main/postgresql.conf
# Add: listen_addresses = '*'

# Update pg_hba.conf for authentication
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Add: host 3dshape 3dshape 0.0.0.0/0 md5

sudo systemctl restart postgresql
```

#### 1.3 Install Python Dependencies

```bash
# Install Python packages
pip3 install fastapi uvicorn sqlalchemy psycopg2-binary python-multipart

# Install CAD conversion tools (options below)
# Option A: CAD Exchanger SDK (commercial)
# Option B: FreeCAD (open source)
sudo apt install -y freecad python3-freecad
```

#### 1.4 Initialize Database Schema

Run the SQL schema from the Database Schema section above.

---

## Phase 2: Sample Data & Ingestion

### Week 1-2

#### 2.1 Download Sample CAD Files

Download sample 3D files for testing:

```bash
mkdir -p /home/ubuntu/github/3dshape/samples
cd /home/ubuntu/github/3dshape/samples

# Sample glTF models (Three.js examples)
curl -L -o astronaut.glb "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Avocado/glTF-Binary/Avocado.glb"

# More sample models
curl -L -o damselfly.glb "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Damselfly/glTF-Binary/Damselfly.glb"

# Box with materials
curl -L -o box.glb "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Box/glTF-Binary/Box.glb"

# More complex model
curl -L -o lantern.glb "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Lantern/glTF-Binary/Lantern.glb"

# Aircraft model
curl -L -o aircraft.glb "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/CesiumAir/glTF-Binary/CesiumAir.glb"

ls -la
```

#### 2.2 Build Ingestion API

Create `/home/ubuntu/github/3dshape/backend/`:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Database configuration
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── crud.py           # Database operations
│   ├── converter.py      # CAD to glTF conversion
│   └── routes/
│       ├── __init__.py
│       ├── parts.py
│       ├── files.py
│       └── scenes.py
├── requirements.txt
└── run.py
```

#### 2.3 API Endpoints

```python
# REST API Endpoints

# Parts
POST   /api/v1/parts           - Create part with metadata
GET    /api/v1/parts           - List parts (paginated, searchable)
GET    /api/v1/parts/{id}     - Get part details
DELETE /api/v1/parts/{id}     - Delete part
PATCH  /api/v1/parts/{id}     - Update part

# Part Revisions
GET    /api/v1/part-revisions              - List revisions
GET    /api/v1/part-revisions/{id}         - Get revision
PATCH  /api/v1/part-revisions/{id}         - Update revision (metadata)

# Files
POST   /api/v1/files           - Upload CAD file (stores in DB)
GET    /api/v1/files/{id}      - Get file info
DELETE /api/v1/files/{id}      - Delete file
GET    /api/v1/files/{id}/data - Download file

# Conversion/Jobs
POST   /api/v1/convert         - Convert file to geometry (stores in DB)
GET    /api/v1/jobs/{id}       - Check job status

# Geometry
GET    /api/v1/geometry/{id}   - Get geometry metadata
GET    /api/v1/geometry/{id}/data - Download geometry file

# Scenes
POST   /api/v1/scenes          - Create scene
GET    /api/v1/scenes          - List scenes
GET    /api/v1/scenes/{id}     - Get scene details
PATCH  /api/v1/scenes/{id}     - Update scene (state transition)
DELETE /api/v1/scenes/{id}     - Delete scene
POST   /api/v1/scenes/{id}/items - Add part to scene
GET    /api/v1/scenes/{id}/items - List scene items
DELETE /api/v1/scenes/{id}/items/{item_id} - Remove item from scene
GET    /api/v1/scenes/{id}/image - Render scene to image

# Stream Keys
POST   /api/v1/scenes/{id}/stream-keys - Create stream key
GET    /api/v1/stream-keys/{id}   - Get stream key

# Export
POST   /api/v1/exports         - Create export for scene
GET    /api/v1/exports/{id}     - Get export
GET    /api/v1/exports/{id}/download - Download export

# Scene View States
GET    /api/v1/scene-view-states         - List view states
GET    /api/v1/scene-view-states/{id}    - Get view state

# Accounts
POST   /api/v1/accounts        - Create account
GET    /api/v1/accounts        - List accounts
GET    /api/v1/accounts/{id}   - Get account

# Users & Groups
POST   /api/v1/users           - Create user
GET    /api/v1/users           - List users
POST   /api/v1/user-groups     - Create user group
POST   /api/v1/user-groups/{id}/users - Add user to group

# Authentication
POST   /oauth2/token          - OAuth2 token endpoint
POST   /api/v1/stream-keys    - Create stream key
```

#### 2.4 Command-Line Interface (CLI)

Create a CLI tool similar to Vertex's `@vertexvis/cli`:

```
3dshape-cli/
├── bin/
│   └── 3dshape
├── src/
│   ├── commands/
│   │   ├── configure.ts
│   │   ├── parts/
│   │   │   ├── create.ts
│   │   │   ├── list.ts
│   │   │   ├── get.ts
│   │   │   └── delete.ts
│   │   ├── files/
│   │   ├── scenes/
│   │   │   ├── create.ts
│   │   │   ├── list.ts
│   │   │   ├── render.ts
│   │   │   └── delete.ts
│   │   ├── create-parts.ts
│   │   ├── create-scene.ts
│   │   ├── stream-keys/
│   │   │   └── create.ts
│   │   └── exports/
│   │       ├── create.ts
│   │       └── download.ts
│   └── utils/
├── package.json
└── tsconfig.json
```

**CLI Commands:**

| Command | Description |
|---------|-------------|
| `3dshape configure` | Configure API credentials |
| `3dshape parts:list` | List parts |
| `3dshape parts:get` | Get part details |
| `3dshape parts:delete` | Delete part |
| `3dshape files:list` | List files |
| `3dshape files:get` | Get file details |
| `3dshape files:delete` | Delete file |
| `3dshape scenes:list` | List scenes |
| `3dshape scenes:get` | Get scene details |
| `3dshape scenes:create` | Create scene |
| `3dshape scenes:render` | Render scene to image |
| `3dshape scenes:delete` | Delete scene |
| `3dshape stream-keys:create` | Create stream key |
| `3dshape exports:create` | Create export |
| `3dshape exports:download` | Download export |
| `3dshape create-parts` | Upload CAD file and create part |
| `3dshape create-scene` | Create scene from parts |

**CLI Examples:**

```bash
# Configure credentials
3dshape configure --basePath http://localhost:8000

# List parts
3dshape parts:list

# Create scene
3dshape scenes:create --name "My Scene" scene-items.json

# Render scene to image
3dshape scenes:render --output scene.jpg --width 1920 --height 1080

# Create stream key
3dshape stream-keys:create --sceneId <scene-id> --expiry 600

# Upload and create part
3dshape create-parts --directory ./geometry parts.json

# Create scene from JSON
3dshape create-scene --name "Assembly Scene" parts.json
```

#### 2.5 Conversion Pipeline

```python
# converter.py - CAD to glTF conversion

# Using FreeCAD (open source) or CAD Exchanger SDK
# Convert: 3DXML/CATIA/STEP/OBJ → glTF binary (.glb)

def convert_to_glb(input_path: str, output_path: str, quality: str = 'high'):
    """
    Convert CAD file to glTF binary format.
    
    Quality settings:
    - high: ~500k triangles
    - medium: ~100k triangles
    - low: ~20k triangles
    """
    # Implementation using FreeCAD or CAD Exchanger
    pass

def generate_lod_levels(part_revision_id: UUID):
    """Generate high, medium, low LOD versions"""
    # Generate multiple LOD levels for each part
    pass
```

---

## Phase 3: Server-Side Rendering

### Week 2-3

#### 3.1 Install Dependencies

```bash
# Install xvfb for headless rendering
sudo apt install -y xvfb libgl1-mesa-dri libglib2.0-0

# Create render server directory
mkdir -p /home/ubuntu/github/3dshape/render-server
cd /home/ubuntu/github/3dshape/render-server
npm init -y
npm install three ws jpeg-js uuid
```

#### 3.2 Render Server Architecture

```
render-server/
├── src/
│   ├── index.js          # Main entry point
│   ├── scene-manager.js  # Three.js scene management
│   ├── renderer.js      # WebGL rendering
│   ├── frame-encoder.js  # JPEG encoding
│   ├── websocket-handler.js
│   └── geometry-loader.js
├── package.json
└── start.sh
```

#### 3.3 WebSocket Protocol

**Client → Server (Commands)**

```javascript
// Connect to scene
{ type: 'connect', sceneId: 'uuid' }

// Camera control
{ type: 'camera', position: [x, y, z], target: [x, y, z] }
{ type: 'camera', orbit: { theta: 0, phi: 0, distance: 10 } }

// View options
{ type: 'view', mode: 'top' | 'front' | 'iso' }
{ type: 'render' }  // Request static snapshot

// Selection
{ type: 'select', itemId: 'uuid' }

// Transforms
{ type: 'explode', factor: 0.5 }
```

**Server → Client (Frames)**

```javascript
// Rendered frame
{ type: 'frame', image: 'base64_jpeg...', width: 1920, height: 1080 }

// Status
{ type: 'ready' }
{ type: 'error', message: '...' }

// Selection result
{ type: 'hit', itemId: 'uuid', position: [x, y, z] }
```

#### 3.4 Render Server Implementation

```javascript
// renderer.js - Core rendering logic
const THREE = require('three');
const { GLTFLoader } = require('three/examples/jsm/loaders/GLTFLoader.js');

// Initialize with xvfb
const xvfb = require('xvfb');
const xvfbInstance = new xvfb({ 
  xvfbArgs: ['-screen', '0', '1920x1080x24'] 
});
xvfbInstance.start();

// Create Three.js renderer
const renderer = new THREE.WebGLRenderer({ 
  antialias: true,
  preserveDrawingBuffer: true 
});
renderer.setSize(1920, 1080);

// Render frame to JPEG
function renderFrame(scene, camera) {
  renderer.render(scene, camera);
  const canvas = renderer.domElement;
  
  // Encode to JPEG
  const dataURL = canvas.toDataURL('image/jpeg', 0.8);
  return dataURL.replace('data:image/jpeg;base64,', '');
}
```

#### 3.5 Frame Streaming

```javascript
// websocket-handler.js
const WebSocket = require('ws');

class WebSocketHandler {
  constructor(server, sceneManager) {
    this.wss = new WebSocket.Server({ server });
    this.sessions = new Map();  // sessionId -> { ws, sceneId, ... }
    
    this.wss.on('connection', (ws) => this.handleConnection(ws));
  }
  
  handleConnection(ws) {
    ws.on('message', (data) => this.handleMessage(ws, data));
    
    ws.on('close', () => this.handleDisconnect(ws));
  }
  
  async handleMessage(ws, data) {
    const msg = JSON.parse(data);
    
    switch (msg.type) {
      case 'connect':
        // Create session, load scene
        break;
        
      case 'camera':
        // Update camera, render frame
        const frame = await this.sceneManager.render();
        ws.send(JSON.stringify({ type: 'frame', image: frame }));
        break;
        
      case 'render':
        // Generate static snapshot
        break;
    }
  }
  
  startFrameLoop(ws, sceneManager) {
    // Stream frames at ~10 FPS for interactive mode
    setInterval(async () => {
      const frame = await sceneManager.render();
      ws.send(JSON.stringify({ type: 'frame', image: frame }));
    }, 100);
  }
}
```

---

## Phase 4: HTML5 Viewer

### Week 3

#### 4.1 Client Structure

```
viewer/
├── index.html
├── css/
│   └── viewer.css
├── js/
│   ├── viewer.js         # Main viewer logic
│   ├── websocket.js     # WebSocket connection
│   ├── controls.js      # Mouse/touch controls
│   ├── camera.js        # Camera manipulations
│   ├── picking.js       # Selection/raycasting
│   ├── metadata.js       # Metadata operations
│   └── ui.js            # UI interactions
└── assets/
    └── icons/
```

#### 4.2 Core Viewer Features

Based on Vertex Web SDK examples:

| Feature | Description | Example |
|---------|-------------|---------|
| **Load by Stream Key** | Load scene via stream key | `viewer.load('urn:vertex:stream-key:xxx')` |
| **Camera Manipulations** | Standard views, fit to bounding box | top, bottom, front, back, left, right, iso |
| **Picking** | Tap to select, raycasting | Hit testing, ancestor selection |
| **Custom Interactions** | Override default controls | Custom pan, zoom, rotate |
| **Phantom Parts** | Set parts as ghosted | Focus on specific items |
| **End Items** | Mark parts as end items | Highlight leaf nodes |
| **Metadata Operations** | Search by metadata | Filter/highlight by properties |
| **Scene Tree** | Hierarchical part tree | Navigate assembly structure |
| **Transform Widget** | Move parts in 3D | Translate/rotate selections |
| **Walk Mode** | First-person navigation | Teleport, walk through |
| **Align Surfaces** | Align two surfaces | Alignment tools |

#### 4.3 WebSocket Protocol (Extended)

**Client → Server Commands:**

```javascript
// Scene operations
{ type: 'connect', sceneId: 'uuid' }
{ type: 'disconnect' }

// Camera
{ type: 'camera', position: [x, y, z], target: [x, y, z] }
{ type: 'camera', orbit: { theta: 0, phi: 0, distance: 10 } }
{ type: 'camera', fitToBoundingBox: { min: [x,y,z], max: [x,y,z] } }
{ type: 'view', mode: 'top' | 'bottom' | 'front' | 'back' | 'left' | 'right' | 'iso' }

// Selection
{ type: 'select', position: { x: 0.5, y: 0.5 } }  // Pick at screen position
{ type: 'select', itemId: 'uuid' }
{ type: 'deselect' }
{ type: 'deselect', itemId: 'uuid' }

// Operations
{ type: 'operation', operation: 'show' }
{ type: 'operation', operation: 'hide' }
{ type: 'operation', operation: 'select' }
{ type: 'operation', operation: 'deselect' }
{ type: 'operation', operation: 'setPhantom', value: true }
{ type: 'operation', operation: 'clearPhantom' }
{ type: 'operation', operation: 'setEndItem', value: true }
{ type: 'operation', operation: 'clearEndItem' }
{ type: 'operation', operation: 'materialOverride', color: { r: 255, g: 0, b: 0 } }
{ type: 'operation', operation: 'clearMaterialOverrides' }
{ type: 'operation', operation: 'transform', matrix: [...] }
{ type: 'operation', operation: 'clearTransforms' }

// Queries (combine with operations)
{ type: 'operation', query: { type: 'all' }, operation: 'hide' }
{ type: 'operation', query: { type: 'withItemId', id: 'uuid' }, operation: 'show' }
{ type: 'operation', query: { type: 'withSuppliedId', suppliedId: 'xxx' }, operation: 'select' }
{ type: 'operation', query: { type: 'withSelected' }, operation: 'hide' }
{ type: 'operation', query: { type: 'withMetadata', filter: 'value', keys: ['PART_NAME'] }, operation: 'setPhantom' }
{ type: 'operation', query: { type: 'not', query: { type: 'withSelected' } }, operation: 'show' }

// Walk Mode
{ type: 'walkMode', enabled: true }
{ type: 'walkMode', teleport: { position: [x, y, z] } }
{ type: 'walkMode', speed: 5 }

// Scene Tree
{ type: 'sceneTree', expandAll: true }
{ type: 'sceneTree', collapseAll: true }
{ type: 'sceneTree', expandNode: 'nodeId' }
{ type: 'sceneTree', collapseNode: 'nodeId' }

// Render options
{ type: 'render' }  // Single frame
{ type: 'stream', fps: 10 }  // Continuous streaming
```

**Server → Client Responses:**

```javascript
// Frame
{ type: 'frame', image: 'base64_jpeg...', width: 1920, height: 1080 }

// Status
{ type: 'ready' }
{ type: 'error', message: '...' }

// Selection
{ type: 'hit', itemId: 'uuid', position: [x, y, z], normal: [x, y, z], ancestors: [...] }
{ type: 'miss' }  // No hit

// Scene Tree
{ type: 'sceneTree', data: [...] }

// Metadata
{ type: 'metadata', itemId: 'uuid', metadata: {...} }
```

#### 4.4 Viewer UI Components

Based on Vertex examples:

```html
<!-- Main Viewer -->
<vertex-viewer id="viewer"></vertex-viewer>

<!-- Scene Tree -->
<vertex-scene-tree id="scene-tree"></vertex-scene-tree>

<!-- View Cube -->
<vertex-viewer-view-cube></vertex-viewer-view-cube>

<!-- Transform Widget -->
-widget id="transform<vertex-viewer-transform"></vertex-viewer-transform-widget>

<!-- Walk Mode -->
<vertex-viewer-walk-mode-tool id="walk-mode"></vertex-viewer-walk-mode-tool>

<!-- Toolbar -->
<vertex-viewer-toolbar>
  <!-- Tools here -->
</vertex-viewer-toolbar>
```

#### 4.5 Implementation Examples

**Camera Standard Views:**
```javascript
// Standard views (from camera-manipulations example)
const views = {
  top: { position: [0, 1, 0], lookAt: [0, 0, 0], up: [0, 0, -1] },
  bottom: { position: [0, -1, 0], lookAt: [0, 0, 0], up: [0, 0, 1] },
  front: { position: [0, 0, -1], lookAt: [0, 0, 0], up: [0, 1, 0] },
  back: { position: [0, 0, 1], lookAt: [0, 0, 0], up: [0, 1, 0] },
  left: { position: [-1, 0, 0], lookAt: [0, 0, 0], up: [0, 1, 0] },
  right: { position: [1, 0, 0], lookAt: [0, 0, 0], up: [0, 1, 0] },
  iso: { position: [1, 1, -1], lookAt: [0, 0, 0], up: [0, 1, 0] }
};
```

**Selection (Picking):**
```javascript
// Tap to select (from picking example)
viewer.addEventListener('tap', async (event) => {
  const { position } = event.detail;
  const raycaster = await scene.raycaster();
  const result = await raycaster.hitItems(position);
  
  if (result.hits.length > 0) {
    const hit = result.hits[0];
    // Select item
    await scene.items((op) => [
      op.where((q) => q.all()).deselect(),
      op.where((q) => q.withItemId(hit.itemId.hex)).select()
    ]).execute();
  } else {
    // Deselect all
    await scene.items((op) => [
      op.where((q) => q.all()).deselect()
    ]).execute();
  }
});
```

**Metadata Search:**
```javascript
// Search by metadata (from metadata-operations example)
await scene.items((op) => [
  op.where((q) => q.all()).setPhantom(true),
  op.where((q) => q.withMetadata('PartName', ['PART_NAME_KEY'], false)).setPhantom(false)
]).execute();
```

**Walk Mode:**
```javascript
// Walk mode navigation (from walk-mode example)
walkModeTool.teleportMode = 'teleport';  // or 'teleport-toward', 'teleport-and-align'
walkModeTool.controller.updateConfiguration({ keyboardWalkSpeed: 5 });
```

#### 4.6 Minimal Client Implementation

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>3D Shape Viewer</title>
  <link rel="stylesheet" href="css/viewer.css">
</head>
<body>
  <div id="viewer">
    <img id="frame" alt="3D View">
    <canvas id="overlay"></canvas>
  </div>
  
  <div id="controls">
    <button id="capture">Capture</button>
    <button id="interact">Interact</button>
    <select id="scene-select">
      <option value="">Select Scene</option>
    </select>
  </div>
  
  <div id="info">
    <h3 id="part-name"></h3>
    <p id="part-desc"></p>
  </div>
  
  <script src="js/websocket.js"></script>
  <script src="js/controls.js"></script>
  <script src="js/ui.js"></script>
  <script src="js/viewer.js"></script>
</body>
</html>
```

```javascript
// js/viewer.js
class Viewer {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.interactive = false;
    
    this.initElements();
    this.connect();
    this.setupControls();
  }
  
  initElements() {
    this.frameEl = document.getElementById('frame');
    this.overlayEl = document.getElementById('overlay');
    this.sceneSelect = document.getElementById('scene-select');
  }
  
  connect() {
    this.ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    this.ws.onopen = () => {
      console.log('Connected to render server');
      this.loadScenes();
    };
    
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      this.handleMessage(msg);
    };
  }
  
  handleMessage(msg) {
    switch (msg.type) {
      case 'frame':
        this.frameEl.src = `data:image/jpeg;base64,${msg.image}`;
        break;
        
      case 'scenes':
        this.updateSceneList(msg.scenes);
        break;
        
      case 'error':
        console.error(msg.message);
        break;
    }
  }
  
  loadScenes() {
    // Fetch scenes from API
    fetch('/api/v1/scenes')
      .then(res => res.json())
      .then(data => this.updateSceneList(data.scenes));
  }
  
  selectScene(sceneId) {
    this.ws.send(JSON.stringify({
      type: 'connect',
      sceneId: sceneId
    }));
  }
  
  capture() {
    this.ws.send(JSON.stringify({ type: 'render' }));
  }
  
  setupControls() {
    let isDragging = false;
    let lastX, lastY;
    
    this.frameEl.addEventListener('mousedown', (e) => {
      if (!this.interactive) return;
      isDragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
    });
    
    window.addEventListener('mousemove', (e) => {
      if (!isDragging || !this.interactive) return;
      
      const deltaX = e.clientX - lastX;
      const deltaY = e.clientY - lastY;
      
      this.ws.send(JSON.stringify({
        type: 'camera',
        orbit: { deltaX, deltaY }
      }));
      
      lastX = e.clientX;
      lastY = e.clientY;
    });
    
    window.addEventListener('mouseup', () => {
      isDragging = false;
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.viewer = new Viewer();
});
```

---

## Phase 5: Refinement

### Week 4

#### 5.1 Error Handling

- Graceful handling of failed conversions
- Connection loss recovery
- Invalid file format handling

#### 5.2 Authentication

```python
# Simple API key auth (can upgrade to OAuth2 later)
# Add to FastAPI
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    # Validate against stored keys
    pass

@app.post("/api/v1/parts", dependencies=[Depends(verify_api_key)])
async def create_part(...):
    pass
```

#### 5.3 Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| OS | Ubuntu | 24.04 |
| Database | PostgreSQL | 15+ |
| Database Extension | PostGIS | 3.x |
| Backend | Python | 3.12 |
| Framework | FastAPI | 0.100+ |
| Render Server | Node.js | 20+ |
| 3D Library | Three.js | 0.160+ |
| Rendering | xvfb | Latest |
| Streaming | ws (WebSocket) | 8.x |
| Client | Vanilla JS | ES6 |

---

## API Endpoints Summary

### Parts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/parts | Create part |
| GET | /api/v1/parts | List parts (paginated) |
| GET | /api/v1/parts/{id} | Get part details |
| DELETE | /api/v1/parts/{id} | Delete part |

### Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/files | Upload CAD file |
| GET | /api/v1/files/{id} | Get file info |

### Geometry

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/convert | Convert to geometry |
| GET | /api/v1/geometry/{id} | Get geometry data |
| GET | /api/v1/geometry/{id}/data | Download geometry file |

### Scenes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/scenes | Create scene |
| GET | /api/v1/scenes | List scenes |
| GET | /api/v1/scenes/{id} | Get scene details |
| POST | /api/v1/scenes/{id}/items | Add part to scene |
| DELETE | /api/v1/scenes/{id}/items/{item_id} | Remove part from scene |

---

## Comparison to Vertex3D

| Aspect | Vertex3D | This Implementation |
|--------|-----------|---------------------|
| Rendering | Server-side (cloud) | Server-side (self-hosted) |
| Protocol | WebSocket | WebSocket |
| Data Security | CAD on vendor cloud | CAD on your server |
| Infrastructure | AWS (multi-node) | Single VPS |
| Cost | SaaS subscription | Infrastructure only |
| Support | Vendor managed | Self-managed |
| Scale | Unlimited | Limited by server |

### CLI Comparison

| Vertex CLI Command | Our CLI Command | Status |
|-------------------|-----------------|--------|
| `vertex configure` | `3dshape configure` | ✅ |
| `vertex parts:list` | `3dshape parts:list` | ✅ |
| `vertex parts:get` | `3dshape parts:get` | ✅ |
| `vertex parts:delete` | `3dshape parts:delete` | ✅ |
| `vertex files:list` | `3dshape files:list` | ✅ |
| `vertex files:get` | `3dshape files:get` | ✅ |
| `vertex files:delete` | `3dshape files:delete` | ✅ |
| `vertex scenes:list` | `3dshape scenes:list` | ✅ |
| `vertex scenes:get` | `3dshape scenes:get` | ✅ |
| `vertex scenes:create` | `3dshape scenes:create` | ✅ |
| `vertex scenes:render` | `3dshape scenes:render` | ✅ |
| `vertex scenes:delete` | `3dshape scenes:delete` | ✅ |
| `vertex create-parts` | `3dshape create-parts` | ✅ |
| `vertex create-scene` | `3dshape create-scene` | ✅ |
| `vertex stream-keys:create` | `3dshape stream-keys:create` | ✅ |
| `vertex exports:create` | `3dshape exports:create` | ✅ |
| `vertex exports:download` | `3dshape exports:download` | ✅ |
| `vertex create-items` | `3dshape create-items` | ✅ |
| `vertex scene-view-states:*` | `3dshape scene-view-states:*` | ✅ |

---

## Future Enhancements

### Phase 6: Scalability

- Add render farm for multiple concurrent users
- Implement CDN for frame caching
- Add GPU rendering support

### Phase 7: Features

- Multi-user collaboration
- Annotation/markup tools
- Measurement tools
- Section planes/cutaways

### Phase 8: Enterprise

- OAuth2 authentication
- Role-based access control
- Audit logging
- API rate limiting

---

## Implementation Checklist

### Phase 1: Setup
- [ ] Install PostgreSQL
- [ ] Configure database
- [ ] Create database schema
- [ ] Install Python dependencies

### Phase 2: Ingestion
- [ ] Download sample CAD files
- [ ] Build FastAPI application
- [ ] Implement file upload
- [ ] Build conversion pipeline

### Phase 3: Rendering
- [ ] Install xvfb
- [ ] Set up Node.js render server
- [ ] Implement WebSocket streaming
- [ ] Connect to database

### Phase 4: Client
- [ ] Build HTML5 viewer
- [ ] Implement frame display
- [ ] Add capture functionality
- [ ] Implement interactive controls

### Phase 5: Polish
- [ ] Error handling
- [ ] Basic authentication
- [ ] Logging

---

## Notes

- This implementation uses **CPU-based rendering** which limits frame rate (~5-10 FPS)
- For better performance, consider adding GPU support via headless-gl or NVIDIA GPU
- All CAD geometry stays on the server for data security
- The client only receives rendered images (pixels), not geometry data

## Phase 6+: Vertex3D Parity Roadmap

To achieve full feature parity with Vertex3D, the following capabilities must be built to replace our foundational mocks and scale the system for enterprise CAD assemblies (e.g., Dassault 3DX, Siemens NX).

### 1. True CAD Ingestion & Conversion Pipeline
- **Integrate Real Translation Engine**: Replace the mocked conversion endpoint with a headless CAD engine (e.g., FreeCAD via Python, or a commercial SDK like Datakit/CAD Exchanger) to natively parse `.3dxml`, `.CATPart`, `.STEP`, and `.JT` files.
- **Assembly Hierarchy Extraction**: Parse the B-Rep (Boundary Representation) solids into triangulated meshes (`.glb`) while preserving the exact scene graph, parent/child relationships, and part metadata.
- **Asynchronous Worker Queues**: Implement Celery and Redis to handle long-running CAD translation jobs without blocking the API, updating the PostgreSQL `jobs` table with progress percentages.

### 2. High-Performance Server-Side Rendering
- **Real WebGL Context / CPU Raytracing**: Replace the 2D pixel generator with a true headless 3D engine. Options include running Three.js via Puppeteer/headless Chrome, or compiling a pure CPU raytracer like Intel OSPRay (which aligns closely with Vertex3D's CPU rendering claims).
- **Level of Detail (LOD) Generation**: Automatically generate low, medium, and high polygon count versions of parts during conversion to maintain render speeds on massive assemblies.
- **Spatial Partitioning (BVH)**: Implement Bounding Volume Hierarchies so the server only loads parts into memory that are currently visible to the camera.

### 3. Advanced Frame Streaming & Latency
- **Binary WebSockets or WebRTC**: Transition from sending Base64 encoded JSON payloads to streaming raw binary frames (H.264 video or raw JPEG bytes) to drastically reduce network bandwidth and latency.
- **Delta-Pixel Streaming**: Implement algorithms that only transmit pixels that have changed between frames, saving massive amounts of bandwidth when only small parts of the screen are animating.
- **Adaptive Resolution**: Render the scene at a lower resolution (e.g., 50% scale) while the user is actively dragging the mouse (Orbit/Pan), and snap to a high-resolution, anti-aliased frame the moment they stop moving.

### 4. Interactive Viewer & Camera Math
- **Mouse/Touch Controls**: Implement full Orbit, Pan, and Zoom controls in the HTML5 viewer capturing `mousemove` and `wheel` events.
- **Camera Matrix Sync**: Translate 2D screen coordinates into 3D camera transformation matrices that are sent to the server over the WebSocket to perfectly update the server's virtual camera.

### 5. Scene Graph, Selection, and Analysis Tools
- **Server-Side Raycasting**: When a user clicks the HTML5 canvas, send the `(X, Y)` screen coordinates to the server. The server casts a 3D ray into the scene, detects which part was hit, and returns the `part_revision_id` to the client.
- **Phantom & Exploded Views**: Implement operations to apply translucent "ghost" materials to parts, hide/show specific assemblies, or mathematically translate parts outwards from their center of mass for exploded views.
- **Cross-Sectioning & Measurements**: Allow users to place arbitrary clipping planes on the server to look inside solid objects, and select vertices to measure exact real-world distances.

---

## Agent Protocol
> **Critical:** All AI agents working on this repository must read `agents.md` before making architectural changes. Code modifications must be validated by successfully executing `./deploy.sh` to ensure the E2E Visual and API tests pass.
