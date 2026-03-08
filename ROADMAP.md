# Vertex3D Parity Roadmap
> **Goal:** Extend the foundational architecture of the 3D Shape Viewer to match the enterprise scale, performance, and features of Vertex3D.

## Milestone 1: True CAD Ingestion & Translation
*   **Action:** Integrate a real CAD translation engine (FreeCAD, CAD Exchanger, or Datakit) into the Python FastAPI backend.
*   **Result:** The `POST /api/v1/convert` endpoint will accept native Dassault `.3dxml`, `.CATPart`, and `.STEP` files. It will run an asynchronous worker (via Celery/Redis) to extract the Assembly Tree (scene graph), metadata (PMIs, materials), and triangulate the B-Rep solids into web-optimized `.glb` (glTF) binaries.
*   **Vertex Feature:** *Import Data (API), Translation Job Polling, Import Metadata*

## Milestone 2: High-Performance Server-Side Rendering
*   **Action:** Replace the mock 2D pixel generator in the Node.js Render Server with a true headless 3D engine. 
*   **Result:** Utilize headless Three.js (via Puppeteer or `gl` bindings) or a pure CPU raytracer (like Intel OSPRay) to load the `.glb` files from PostgreSQL into a virtual 3D scene.
*   **Vertex Feature:** *Server-Side WebGL / CPU Rendering, Data Security (IP never leaves server)*

## Milestone 3: Advanced Frame Streaming & Latency Optimization
*   **Action:** Refactor the WebSocket protocol to prioritize raw bandwidth and latency.
*   **Result:** 
    *   Transition from sending Base64 JSON payloads to streaming raw binary frames (e.g., H.264 video streams or raw JPEG bytes via WebRTC/Binary WebSockets).
    *   **Delta-Pixel Streaming:** Only send pixels that changed between frames.
    *   **Adaptive Resolution:** Render the scene at 50% resolution during active camera movement (Orbit/Pan), instantly snapping to a high-resolution, anti-aliased frame when movement stops.
*   **Vertex Feature:** *Context-Aware Pixel Streaming, Massive Assembly Support*

## Milestone 4: Interactive Viewer & Camera Math
*   **Action:** Upgrade the HTML5 Thin Client from basic directional buttons to full 3D viewport controls.
*   **Result:** 
    *   Implement Orbit, Pan, and Zoom logic that captures `mousemove`, `touch`, and `wheel` events. These 2D screen interactions will be mathematically translated into 3D camera transformation matrices and synced to the server in real-time.
    *   **Visual Compass (View Cube):** Render a 3D compass/view cube in the top-right corner of the viewer that perfectly tracks the server's camera orientation, allowing users to understand their current XYZ orientation in space and click faces to snap to standard views.
*   **Vertex Feature:** *Camera Manipulations, Transform Widget, View Cube*

## Milestone 5: Scene Graph, Selection, and Analysis Tools
*   **Action:** Build the bi-directional communication required for deep CAD interaction.
*   **Result:**
    *   **Server-Side Raycasting:** When a user clicks the HTML5 canvas, the `(X, Y)` screen coordinates are sent to the server. The server casts a 3D ray, detects the hit part, and returns its `part_revision_id`.
    *   **Phantom & Exploded Views:** Operations to apply translucent "ghost" materials, hide/show assemblies, or mathematically translate parts outwards for exploded views.
    *   **Cross-Sectioning & PMIs:** Allow users to place arbitrary clipping planes on the server to look inside solid objects and view embedded manufacturing information.
*   **Vertex Feature:** *Interact with Scene (Tap to Select), Phantom Parts, Scene Tree Columns*
