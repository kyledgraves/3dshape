# 3D CAD Visualization Architecture

> **Document Purpose:** Document current architecture, identify gaps, and propose future state based on CAD domain research.

---

## 1. Current Architecture (v0.1 - Proof of Concept)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (HTML5)                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ index.html  │  │ websocket.js│  │ controls.js │  │   CSS Viewer    │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘  └─────────────────┘  │
│         │                 │                                                  │
│         └────────────────┼──────────────────────────────────────────────────  │
│                          ▼                                                   │
│                    WebSocket (ws://localhost:8080)                          │
│                    Base64 JPEG frames @ 20 FPS                              │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RENDER SERVER (Node.js)                             │
│  ┌─────────────────────┐  ┌──────────────────────────────────────────────┐  │
│  │ WebSocket Handler   │  │         Playwright + Three.js Headless     │  │
│  │ (websocket-handler) │  │  ┌─────────────────────────────────────┐   │  │
│  └──────────┬──────────┘  │  │  Chromium --use-gl=swiftshader   │   │  │
│             │              │  │  Three.js WebGL Renderer            │   │  │
│             ▼              │  │  OrbitControls                      │   │  │
│  ┌─────────────────────┐  │  │  Static: /Avocado.glb (hardcoded)  │   │  │
│  │ playwright-renderer │  │  └─────────────────────────────────────┘   │  │
│  └─────────────────────┘  └──────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        REST API (port 8000)                         │   │
│  │  /api/v1/accounts  /api/v1/parts  /api/v1/scenes  /api/v1/convert│   │
│  └────────────────────────────────────┬────────────────────────────────┘   │
│                                       │                                     │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      PostgreSQL Database                            │   │
│  │  accounts, parts, part_revisions, files, geometry, scenes, scene_items│  │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Current Technology Stack

| Layer | Technology | Status |
|-------|------------|--------|
| **Frontend** | HTML5 + Vanilla JS | ✅ Functional |
| **Streaming** | WebSocket + Base64 JPEG | ✅ Basic |
| **Renderer** | Playwright + Three.js (swiftshader) | ✅ Functional |
| **Backend API** | FastAPI + SQLAlchemy | ✅ Functional |
| **Database** | PostgreSQL | ✅ Functional |
| **CAD Translation** | None (placeholder) | ❌ Not Implemented |

### Current Limitations

1. **No real CAD translation** - Uses hardcoded `Avocado.glb` sample model
2. **No database geometry loading** - Renderer loads static file, not PostgreSQL
3. **No assembly tree** - Single model only
4. **Inefficient streaming** - Base64 JSON (~30% overhead)
5. **No raycasting** - Cannot click to select parts
6. **No authentication** - No user auth

---

## 2. Proposed Future Architecture (v1.0 - Production)

### 2.1 Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (HTML5)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    WebGL Canvas (Three.js)                         │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │    │
│  │  │OrbitCtrl │  │Raycaster│  │ViewCube │  │  Selection Highlight│   │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│                    WebRTC or Binary WebSocket Stream                         │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────────────┐
│  SIGNALING SERVER │    │   RENDER SERVER   │    │      BACKEND API          │
│   (Node.js)       │    │   (Node.js)      │    │      (FastAPI)           │
│                   │    │                   │    │                           │
│  WebRTC SDP/ICE  │◄──►│  WebRTC Endpoint  │◄──►│  REST API + WebSocket    │
│  Negotiation     │    │  + Three.js       │    │  + CAD Translation       │
│                   │    │  + Raycaster      │    │  + Celery Workers        │
└───────────────────┘    └─────────┬─────────┘    └────────────┬────────────┘
                                    │                          │
                                    ▼                          ▼
                           ┌────────────────┐         ┌─────────────────────┐
                           │  PostgreSQL    │         │   MESSAGE QUEUE     │
                           │  + Geometry DB │         │   (Redis/Celery)    │
                           └────────────────┘         └─────────────────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────────┐
                                                    │  CAD TRANSLATION    │
                                                    │  WORKER             │
                                                    │  (CAD Exchanger/    │
                                                    │   PythonOCC)        │
                                                    └─────────────────────┘
```

### 2.2 Component Specifications

#### A. CAD Translation Pipeline

| Input Formats | Recommended Solution | Alternative |
|---------------|---------------------|-------------|
| Dassault 3DXML | CAD Exchanger SDK (commercial) | Parse 3DXML ZIP (open source) |
| CATIA V5/V6 | CAD Exchanger SDK | - |
| STEP/IGES | trimesh/cascadio (open source) | PythonOCC |
| SOLIDWORKS | CAD Exchanger SDK | - |
| Inventor | CAD Exchanger SDK | - |

**Translation Worker Architecture:**

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Upload    │───►│   Queue      │───►│   Worker     │
│   (REST)    │    │  (Celery)    │    │  (Python)    │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌───────────────────────────┬┘
                    ▼                           ▼
           ┌──────────────┐           ┌──────────────┐
           │  Geometry DB │           │   Scene Graph│
           │  (PostgreSQL)│           │   (JSON)     │
           └──────────────┘           └──────────────┘
```

#### B. Frame Streaming Options (Ranked)

| Option | Latency | Bandwidth | Complexity | Recommendation |
|--------|---------|----------|-----------|----------------|
| **Base64 JSON** (current) | 50-100ms | High (+30%) | Low | ❌ Remove |
| **Binary WebSocket** | 30-50ms | Medium | Medium | ✅ Phase 3 |
| **H.264 via WebSocket** | 20-40ms | Low | Medium | ✅ Phase 3 |
| **WebRTC** | 10-30ms | Lowest | High | ✅ Phase 3+ |

**Recommendation:** Start with Binary WebSocket (simple upgrade), migrate to WebRTC for production.

#### C. Large Assembly Rendering Strategy

| Approach | Max Primitives | Web Ready | Effort |
|----------|---------------|-----------|--------|
| Three.js (current) | ~10M | ✅ Native | Low |
| Three.js + LOD | ~50M | ✅ Native | Medium |
| OSPRay (CPU raytrace) | ~15B | ❌ Requires encoding | High |
| OSPRay + WebRTC | ~15B | ✅ Via stream | Very High |

**Recommendation:** 
- **Phase 3:** Optimize Three.js with LOD, frustum culling, instancing
- **Phase 4+:** Evaluate OSPRay only if photorealism required for large assemblies (>50M triangles)

---

## 3. Gap Analysis & Refinement

### 3.1 Milestone Refinements

| Milestone | Current | Refined Approach |
|-----------|---------|-----------------|
| **1: CAD Ingestion** | Placeholder (sleeps 1s) | Use CAD Exchanger SDK or trimesh/cascadio for STEP → GLB |
| **2: Rendering** | ✅ Complete | Add database geometry loading |
| **3: Streaming** | Base64 @ 20fps | Binary WebSocket → WebRTC |
| **4: Interactive** | ✅ Complete | Add View Cube |
| **5: Selection** | Not started | Server-side raycasting via Three.js Raycaster |

### 3.2 Technical Debt Items

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| **High** | Remove hardcoded Avocado.glb, load from DB | 2 days | Enables real workflows |
| **High** | Implement real CAD translation | 2-4 weeks | Core value prop |
| **Medium** | Binary frame streaming | 1 week | 30% bandwidth savings |
| **Medium** | Server-side raycasting | 1 week | Part selection |
| **Low** | View cube visualization | 3 days | UX improvement |

---

## 4. External Expertise Requirements

| Expertise | Purpose | Engagement Type |
|-----------|---------|-----------------|
| **CAD Domain Expert** | Validate translation pipeline, recommend formats | Advisory / POC review |
| **Computer Graphics Engineer** | Evaluate streaming architecture, WebRTC | Technical architecture |
| **Backend/Performance Architect** | Binary protocol, latency optimization | Implementation guidance |

---

## 5. Recommended Roadmap (Refined)

### Phase 3.1: Streaming Optimization (2 weeks)
- [ ] Upgrade to Binary WebSocket (remove Base64 overhead)
- [ ] Implement adaptive resolution (50% on move, 100% on still)
- [ ] Add frame delta compression

### Phase 3.2: Real CAD Pipeline (3-4 weeks)
- [ ] Integrate trimesh/cascadio for STEP files
- [ ] Build Celery worker for async translation
- [ ] Add geometry storage to PostgreSQL
- [ ] Load geometry from DB in renderer

### Phase 4: Interactive Features (2 weeks)
- [ ] Add View Cube (visual compass)
- [ ] Implement server-side raycasting
- [ ] Part selection with highlighting

### Phase 5: Scale & Production (Ongoing)
- [ ] Evaluate WebRTC for ultra-low latency
- [ ] Large assembly optimization (LOD, culling)
- [ ] Authentication & multi-user

---

## 6. Appendix: Research Sources

### CAD Translation
- **trimesh/cascadio**: Open source Python module using OpenCASCADE to convert STEP to GLB
- **CAD Exchanger SDK**: Commercial, supports 30+ formats including 3DXML, CATIA, STEP
- **PythonOCC**: Open source, full OpenCASCADE bindings

### Streaming
- **WebRTC**: 250-500ms latency, native browser support, requires signaling
- **H.264 via WebSocket**: 20-40ms, hardware acceleration available
- **Binary WebSocket**: 30-50ms, simplest upgrade path

### Large Assembly Rendering
- **OSPRay**: Intel CPU raytracer, scales to billions of primitives
- **Three.js**: WebGL rasterization, sufficient for <50M with optimization
- **Selkies-GStreamer**: Open source WebRTC streaming framework

---

*Document Version: 1.0*
*Created: March 2026*
*Author: Program Management*
