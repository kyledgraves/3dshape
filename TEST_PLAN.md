# Test Harness Plan - 3D Shape Viewer

## Overview

This document outlines the test-driven development approach for building the 3D Shape Viewer system. Each phase includes test cases that verify functionality similar to Vertex3D's developer guides.

## Test Philosophy

- **Test First**: Write tests before implementation
- **Incremental**: Each phase builds on the previous
- **Automated**: Tests should run automatically via CI/CD
- **Human-readable**: Test names describe the capability

---

## Vertex3D Capability Mapping

| Vertex3D Guide | Our Implementation | Test Phase |
|---------------|-------------------|------------|
| Render your first scene | WebSocket frame streaming | Phase 3-4 |
| Import data (CLI) | CLI commands for import | Phase 2 |
| Import data (API) | REST API file upload | Phase 2 |
| Import metadata | Metadata indexing/retrieval | Phase 1-2 |
| Render static scenes | Scene creation, commit, render | Phase 3 |
| Authentication | OAuth2, stream keys | Phase 5 |
| Customize your scene | Queries & operations | Phase 4 |
| User management | Users, groups, IdP | Phase 5 |

---

## Phase 1: Database Tests

### 1.1 Account Tests

```python
# tests/phase1_database/test_accounts.py
import pytest

def test_create_account(client):
    """Test creating an account - vertex: create account"""
    response = client.post("/api/v1/accounts", json={"name": "Test Corp"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Corp"
    assert "id" in data

def test_list_accounts(client):
    """Test listing accounts - vertex: list accounts"""
    response = client.get("/api/v1/accounts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_account(client):
    """Test retrieving a specific account"""
    create_resp = client.post("/api/v1/accounts", json={"name": "Test"})
    account_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["id"] == account_id

def test_account_not_found(client):
    """Test 404 for non-existent account"""
    response = client.get("/api/v1/accounts/nonexistent-id")
    assert response.status_code == 404
```

### 1.2 Parts Tests

```python
# tests/phase1_database/test_parts.py
import pytest

@pytest.fixture
def account_id(client):
    response = client.post("/api/v1/accounts", json={"name": "Test"})
    return response.json()["id"]

def test_create_part(client, account_id):
    """Test creating a part with metadata - vertex: createPart with suppliedId"""
    payload = {
        "account_id": account_id,
        "supplied_id": "PART-001",
        "name": "Test Part",
        "description": "A test part",
        "category": "mechanical",
        "metadata": {"weight": "2.5kg", "material": "steel"}
    }
    response = client.post("/api/v1/parts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["supplied_id"] == "PART-001"
    assert data["name"] == "Test Part"

def test_create_part_duplicate_supplied_id(client, account_id):
    """Test that duplicate supplied_id is rejected"""
    payload = {
        "account_id": account_id,
        "supplied_id": "DUPLICATE",
        "name": "Part 1"
    }
    client.post("/api/v1/parts", json=payload)
    response = client.post("/api/v1/parts", json=payload)
    assert response.status_code == 400

def test_list_parts(client, account_id):
    """Test listing parts with pagination"""
    for i in range(5):
        client.post("/api/v1/parts", json={
            "account_id": account_id,
            "supplied_id": f"PART-{i}",
            "name": f"Part {i}"
        })
    response = client.get(f"/api/v1/parts?account_id={account_id}")
    assert response.status_code == 200
    assert len(response.json()) == 5

def test_search_parts(client, account_id):
    """Test full-text search on parts - vertex: getParts with search"""
    client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "SEARCH-001",
        "name": "Brass Gear Assembly"
    })
    response = client.get(f"/api/v1/parts?search=brass")
    assert response.status_code == 200
    assert any("Brass" in p["name"] for p in response.json())

def test_get_part_by_id(client, account_id):
    """Test retrieving a specific part"""
    create_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "GET-001",
        "name": "Get Test Part"
    })
    part_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/parts/{part_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test Part"

def test_update_part_metadata(client, account_id):
    """Test updating part metadata"""
    create_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "UPDATE-001",
        "name": "Original Name"
    })
    part_id = create_resp.json()["id"]
    response = client.patch(f"/api/v1/parts/{part_id}", json={
        "name": "Updated Name",
        "metadata": {"new_field": "value"}
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

def test_delete_part(client, account_id):
    """Test deleting a part"""
    create_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "DELETE-001",
        "name": "To Delete"
    })
    part_id = create_resp.json()["id"]
    response = client.delete(f"/api/v1/parts/{part_id}")
    assert response.status_code == 204
```

### 1.3 Part Revisions Tests

```python
# tests/phase1_database/test_part_revisions.py

def test_create_part_revision(client, account_id):
    """Test creating a part revision - vertex: createPart with revision"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "REV-PART-001",
        "name": "Revisable Part"
    })
    part_id = part_resp.json()["id"]
    response = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": "A",
        "supplied_id": "REV-A"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["revision_number"] == "A"
    assert data["status"] == "pending"

def test_list_part_revisions(client, account_id):
    """Test listing revisions for a part"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "REV-LIST-001",
        "name": "Multiple Revisions"
    })
    part_id = part_resp.json()["id"]
    for rev in ["A", "B", "C"]:
        client.post("/api/v1/part-revisions", json={
            "part_id": part_id,
            "revision_number": rev
        })
    response = client.get(f"/api/v1/part-revisions?part_id={part_id}")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_revision_cascade_delete(client, account_id):
    """Test that deleting part deletes revisions"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "CASCADE-001",
        "name": "Cascade Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": "A"
    })
    revision_id = rev_resp.json()["id"]
    client.delete(f"/api/v1/parts/{part_id}")
    response = client.get(f"/api/v1/part-revisions/{revision_id}")
    assert response.status_code == 404
```

### 1.4 Metadata Tests (vertex: Import metadata)

```python
# tests/phase1_database/test_metadata.py

def test_update_revision_metadata(client, account_id):
    """Test adding metadata to part revision - vertex: updatePartRevision with metadata"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "META-001",
        "name": "Metadata Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": "A"
    })
    revision_id = rev_resp.json()["id"]
    
    response = client.patch(f"/api/v1/part-revisions/{revision_id}", json={
        "metadata": {
            "PART_NUMBER": {"value": "PN12345", "type": "string"},
            "WEIGHT": {"value": "2.5", "type": "float"},
            "MATERIAL": {"value": "steel", "type": "string"}
        }
    })
    assert response.status_code == 200

def test_get_revision_metadata(client, account_id):
    """Test retrieving metadata - vertex: getPartRevision with fields[part-revision]=metadata"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "META-GET-001",
        "name": "Get Metadata Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": "A"
    })
    revision_id = rev_resp.json()["id"]
    
    client.patch(f"/api/v1/part-revisions/{revision_id}", json={
        "metadata": {"PART_NAME": {"value": "Test Part", "type": "string"}}
    })
    
    response = client.get(f"/api/v1/part-revisions/{revision_id}?fields[part-revision]=metadata")
    assert response.status_code == 200
    assert "metadata" in response.json()

def test_metadata_types(client, account_id):
    """Test different metadata types - vertex: string, long, float, date"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "META-TYPES-001",
        "name": "Types Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": "A"
    })
    revision_id = rev_resp.json()["id"]
    
    response = client.patch(f"/api/v1/part-revisions/{revision_id}", json={
        "metadata": {
            "STRING_VAL": {"value": "text", "type": "string"},
            "LONG_VAL": {"value": "12345", "type": "long"},
            "FLOAT_VAL": {"value": "123.45", "type": "float"},
            "DATE_VAL": {"value": "2024-01-01T00:00:00Z", "type": "date"}
        }
    })
    assert response.status_code == 200
```

### 1.5 Files Tests

```python
# tests/phase1_database/test_files.py
import io

def test_upload_file(client, account_id):
    """Test uploading a CAD file - vertex: createFile + uploadFile"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "FILE-UPLOAD-001",
        "name": "File Upload Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    files = {"file": ("test.glb", io.BytesIO(b"fake glb data"), "model/gltf-binary")}
    data = {"part_revision_id": revision_id}
    response = client.post("/api/v1/files", data=data, files=files)
    assert response.status_code == 201
    file_data = response.json()
    assert file_data["original_filename"] == "test.glb"

def test_upload_3dxml_file(client, account_id):
    """Test uploading 3DXML format - vertex: supported file formats"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "3DXML-001",
        "name": "3DXML Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    files = {"file": ("part.3dxml", io.BytesIO(b"fake 3dxml"), "model/vnd.3ds")}
    response = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    assert response.status_code == 201
```

### 1.6 Geometry Tests

```python
# tests/phase1_database/test_geometry.py

def test_create_geometry(client, account_id):
    """Test creating geometry record"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "GEOM-001",
        "name": "Geometry Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    response = client.post("/api/v1/geometry", json={
        "part_revision_id": revision_id,
        "format": "glb",
        "version": "high",
        "vertex_count": 50000,
        "face_count": 30000,
        "bounding_box": {"min": [0, 0, 0], "max": [10, 10, 10]}
    })
    assert response.status_code == 201

def test_get_geometry_data(client, account_id):
    """Test retrieving geometry binary data"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "GEOM-DATA-001",
        "name": "Geometry Data Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    geom_resp = client.post("/api/v1/geometry", json={
        "part_revision_id": revision_id,
        "format": "glb",
        "version": "high"
    })
    geom_id = geom_resp.json()["id"]
    
    response = client.get(f"/api/v1/geometry/{geom_id}/data")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"

def test_lod_levels(client, account_id):
    """Test multiple LOD levels - vertex: different quality settings"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "LOD-001",
        "name": "LOD Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    for version, verts in [("high", 50000), ("medium", 10000), ("low", 2000)]:
        client.post("/api/v1/geometry", json={
            "part_revision_id": revision_id,
            "format": "glb",
            "version": version,
            "vertex_count": verts
        })
    
    response = client.get(f"/api/v1/geometry?part_revision_id={revision_id}")
    assert len(response.json()) == 3
```

---

## Phase 2: Ingestion Tests

### 2.1 Conversion Tests (vertex: translate CAD to geometry)

```python
# tests/phase2_ingestion/test_conversion.py

def test_trigger_conversion(client, account_id):
    """Test triggering CAD to glTF conversion - vertex: createPart initiates translation"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "CONVERT-001",
        "name": "Convert Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    files = {"file": ("test.glb", io.BytesIO(b"fake"), "model/gltf-binary")}
    file_resp = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    file_id = file_resp.json()["id"]
    
    response = client.post("/api/v1/convert", json={
        "file_id": file_id,
        "quality": "high"
    })
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"

def test_check_conversion_status(client, account_id):
    """Test checking conversion job status - vertex: getQueuedTranslation"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "STATUS-001",
        "name": "Status Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    files = {"file": ("test.glb", io.BytesIO(b"fake"), "model/gltf-binary")}
    file_resp = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    file_id = file_resp.json()["id"]
    
    conv_resp = client.post("/api/v1/convert", json={"file_id": file_id})
    job_id = conv_resp.json()["job_id"]
    
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert "status" in response.json()

def test_conversion_completion(client, account_id):
    """Test conversion completes and creates geometry - vertex: queued translation redirects to part"""
    import time
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "COMPLETE-001",
        "name": "Complete Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    files = {"file": ("test.glb", io.BytesIO(b"glb data"), "model/gltf-binary")}
    file_resp = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    file_id = file_resp.json()["id"]
    
    conv_resp = client.post("/api/v1/convert", json={"file_id": file_id})
    job_id = conv_resp.json()["job_id"]
    
    for _ in range(20):
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        status = status_resp.json()["status"]
        if status in ["completed", "failed"]:
            break
        time.sleep(0.5)
    
    assert status == "completed"
```

### 2.2 CLI Commands Tests

```python
# tests/phase2_ingestion/test_cli.py

def test_cli_configure():
    """Test CLI configure command - vertex: vertex configure"""
    result = run_cli(["configure", "--help"])
    assert result.returncode == 0

def test_cli_parts_list():
    """Test CLI parts:list command - vertex: vertex parts:list"""
    result = run_cli(["parts:list"])
    assert result.returncode == 0

def test_cli_parts_get():
    """Test CLI parts:get command - vertex: vertex parts:get"""
    result = run_cli(["parts:get", "test-part-id"])
    assert result.returncode == 0

def test_cli_parts_delete():
    """Test CLI parts:delete command - vertex: vertex parts:delete"""
    result = run_cli(["parts:delete", "test-part-id"])
    assert result.returncode == 0

def test_cli_files_list():
    """Test CLI files:list command - vertex: vertex files:list"""
    result = run_cli(["files:list"])
    assert result.returncode == 0

def test_cli_files_get():
    """Test CLI files:get command - vertex: vertex files:get"""
    result = run_cli(["files:get", "test-file-id"])
    assert result.returncode == 0

def test_cli_files_delete():
    """Test CLI files:delete command - vertex: vertex files:delete"""
    result = run_cli(["files:delete", "test-file-id"])
    assert result.returncode == 0

def test_cli_scenes_list():
    """Test CLI scenes:list command - vertex: vertex scenes:list"""
    result = run_cli(["scenes:list"])
    assert result.returncode == 0

def test_cli_scenes_get():
    """Test CLI scenes:get command - vertex: vertex scenes:get"""
    result = run_cli(["scenes:get", "test-scene-id"])
    assert result.returncode == 0

def test_cli_scenes_delete():
    """Test CLI scenes:delete command - vertex: vertex scenes:delete"""
    result = run_cli(["scenes:delete", "test-scene-id"])
    assert result.returncode == 0

def test_cli_scenes_create():
    """Test CLI scenes:create command - vertex: vertex create-scene"""
    result = run_cli([
        "create-scene",
        "--name", "Test Scene",
        "items.json"
    ])
    assert result.returncode == 0

def test_cli_scenes_render():
    """Test CLI scenes:render command - vertex: vertex scenes:render"""
    result = run_cli([
        "scenes:render",
        "test-scene-id",
        "--output", "output.jpg",
        "--width", "1920",
        "--height", "1080"
    ])
    assert result.returncode == 0

def test_cli_scenes_render_viewer():
    """Test CLI scenes:render with viewer option"""
    result = run_cli([
        "scenes:render",
        "test-scene-id",
        "--viewer"
    ])
    assert result.returncode == 0

def test_cli_create_parts():
    """Test CLI create-parts command - vertex: vertex create-parts"""
    result = run_cli([
        "create-parts",
        "--directory", "./geometry",
        "parts.json"
    ])
    assert result.returncode == 0

def test_cli_create_parts_parallel():
    """Test CLI create-parts with parallelism"""
    result = run_cli([
        "create-parts",
        "--directory", "./geometry",
        "--parallelism", "10",
        "parts.json"
    ])
    assert result.returncode == 0

def test_cli_create_scene():
    """Test CLI create-scene command - vertex: vertex create-scene"""
    result = run_cli([
        "create-scene",
        "--name", "Test Scene",
        "items.json"
    ])
    assert result.returncode == 0

def test_cli_create_scene_options():
    """Test CLI create-scene with options"""
    result = run_cli([
        "create-scene",
        "--name", "Scene with Options",
        "--supplied-id", "scene-001",
        "--tree-enabled",
        "items.json"
    ])
    assert result.returncode == 0

def test_cli_stream_keys_create():
    """Test CLI stream-keys:create command - vertex: vertex stream-keys:create"""
    result = run_cli([
        "stream-keys:create",
        "--scene-id", "test-scene-id",
        "--expiry", "600"
    ])
    assert result.returncode == 0

def test_cli_exports_create():
    """Test CLI exports:create command - vertex: vertex exports:create"""
    result = run_cli([
        "exports:create",
        "--scene-id", "test-scene-id"
    ])
    assert result.returncode == 0

def test_cli_exports_download():
    """Test CLI exports:download command - vertex: vertex exports:download"""
    result = run_cli([
        "exports:download",
        "export-id",
        "--output", "export.zip"
    ])
    assert result.returncode == 0

def test_cli_create_items():
    """Test CLI create-items command - vertex: vertex create-items"""
    result = run_cli([
        "create-items",
        "--format", "pvs",
        "--output", "items.json",
        "model.pvs"
    ])
    assert result.returncode == 0

def test_cli_scene_view_states_list():
    """Test CLI scene-view-states:list command"""
    result = run_cli(["scene-view-states:list"])
    assert result.returncode == 0

def test_cli_scene_view_states_get():
    """Test CLI scene-view-states:get command"""
    result = run_cli(["scene-view-states:get", "view-state-id"])
    assert result.returncode == 0
```

### 2.3 Full Workflow Test

```python
# tests/phase2_ingestion/test_workflow.py

def test_full_ingestion_workflow(client, account_id):
    """Test: create part -> upload file -> convert -> ready - vertex: full import workflow"""
    # 1. Create part
    part_response = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "WORKFLOW-001",
        "name": "Complete Workflow Test"
    })
    assert part_response.status_code == 201
    part_id = part_response.json()["id"]
    
    # 2. Create revision
    rev_response = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": "A"
    })
    assert rev_response.status_code == 201
    revision_id = rev_response.json()["id"]
    
    # 3. Upload file
    files = {"file": ("workflow.glb", io.BytesIO(b"fake glb"), "model/gltf-binary")}
    file_response = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    assert file_response.status_code == 201
    file_id = file_response.json()["id"]
    
    # 4. Trigger conversion
    conv_response = client.post("/api/v1/convert", json={"file_id": file_id})
    assert conv_response.status_code == 202
```

---

## Phase 3: Scene & Rendering Tests

### 3.1 Scene Tests (vertex: Render static scenes)

```python
# tests/phase3_rendering/test_scenes.py

def test_create_scene(client, account_id):
    """Test creating a scene - vertex: createScene"""
    response = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Test Scene"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Scene"
    assert data["state"] == "draft"

def test_list_scenes(client, account_id):
    """Test listing scenes"""
    for i in range(3):
        client.post("/api/v1/scenes", json={
            "account_id": account_id,
            "name": f"Scene {i}"
        })
    response = client.get(f"/api/v1/scenes?account_id={account_id}")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_add_scene_item(client, account_id):
    """Test adding part to scene - vertex: createSceneItem"""
    # Create part with geometry
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "SCENE-PART-001",
        "name": "Scene Part"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    geom_resp = client.post("/api/v1/geometry", json={
        "part_revision_id": revision_id,
        "format": "glb",
        "version": "high"
    })
    
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Scene with Item"
    })
    scene_id = scene_resp.json()["id"]
    
    response = client.post(f"/api/v1/scenes/{scene_id}/items", json={
        "part_revision_id": revision_id,
        "supplied_id": "item-1"
    })
    assert response.status_code == 201

def test_commit_scene(client, account_id):
    """Test committing a scene - vertex: updateScene with state=commit"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Commit Test"
    })
    scene_id = scene_resp.json()["id"]
    
    response = client.patch(f"/api/v1/scenes/{scene_id}", json={
        "state": "commit"
    })
    assert response.status_code == 200
    assert response.json()["state"] == "commit"

def test_scene_transform_matrix(client, account_id):
    """Test scene item with transform - vertex: transform matrix"""
    # Create part
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "TRANSFORM-001",
        "name": "Transform Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Transform Scene"
    })
    scene_id = scene_resp.json()["id"]
    
    transform = {
        "r0": {"x": 1, "y": 0, "z": 0, "w": 0},
        "r1": {"x": 0, "y": 1, "z": 0, "w": 0},
        "r2": {"x": 0, "y": 0, "z": 1, "w": 0},
        "r3": {"x": 10, "y": 5, "z": 0, "w": 1}
    }
    
    response = client.post(f"/api/v1/scenes/{scene_id}/items", json={
        "part_revision_id": revision_id,
        "transform": transform
    })
    assert response.status_code == 201

def test_render_scene_image(client, account_id):
    """Test rendering scene to image - vertex: renderScene"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Render Test"
    })
    scene_id = scene_resp.json()["id"]
    client.patch(f"/api/v1/scenes/{scene_id}", json={"state": "commit"})
    
    response = client.get(f"/api/v1/scenes/{scene_id}/image?width=1000&height=1000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_delete_scene(client, account_id):
    """Test deleting a scene - vertex: DELETE /scenes/{id}"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Delete Test"
    })
    scene_id = scene_resp.json()["id"]
    
    response = client.delete(f"/api/v1/scenes/{scene_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_resp = client.get(f"/api/v1/scenes/{scene_id}")
    assert get_resp.status_code == 404

def test_delete_scene_item(client, account_id):
    """Test deleting a scene item - vertex: DELETE /scenes/{id}/items/{item_id}"""
    # Create part and scene
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "DELETE-ITEM-001",
        "name": "Delete Item Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Scene to Delete Item"
    })
    scene_id = scene_resp.json()["id"]
    
    # Add item
    item_resp = client.post(f"/api/v1/scenes/{scene_id}/items", json={
        "part_revision_id": revision_id
    })
    item_id = item_resp.json()["id"]
    
    # Delete item
    response = client.delete(f"/api/v1/scenes/{scene_id}/items/{item_id}")
    assert response.status_code == 204

def test_scene_state_draft(client, account_id):
    """Test scene starts in draft state"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Draft State Test"
    })
    assert scene_resp.json()["state"] == "draft"

def test_scene_state_transition_draft_to_commit(client, account_id):
    """Test scene state transition from draft to commit - vertex: updateScene state"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "State Transition Test"
    })
    scene_id = scene_resp.json()["id"]
    assert scene_resp.json()["state"] == "draft"
    
    # Transition to committed
    response = client.patch(f"/api/v1/scenes/{scene_id}", json={"state": "commit"})
    assert response.status_code == 200
    assert response.json()["state"] == "commit"

def test_scene_item_visibility_default(client, account_id):
    """Test scene item visibility defaults to true"""
    # Create part
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "VIS-001",
        "name": "Visibility Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Visibility Scene"
    })
    scene_id = scene_resp.json()["id"]
    
    item_resp = client.post(f"/api/v1/scenes/{scene_id}/items", json={
        "part_revision_id": revision_id
    })
    assert item_resp.json()["visibility"] is True

def test_scene_item_set_visibility(client, account_id):
    """Test setting scene item visibility - vertex: scene item visibility"""
    # Create part
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "VIS-SET-001",
        "name": "Set Visibility Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Set Visibility Scene"
    })
    scene_id = scene_resp.json()["id"]
    
    # Add item with visibility=false
    item_resp = client.post(f"/api/v1/scenes/{scene_id}/items", json={
        "part_revision_id": revision_id,
        "visibility": False
    })
    assert item_resp.json()["visibility"] is False

def test_get_scene(client, account_id):
    """Test getting scene details - vertex: GET /scenes/{id}"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Get Scene Test"
    })
    scene_id = scene_resp.json()["id"]
    
    response = client.get(f"/api/v1/scenes/{scene_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Scene Test"

def test_list_scene_items(client, account_id):
    """Test listing scene items in a scene"""
    # Create part
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "LIST-ITEMS-001",
        "name": "List Items Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "List Items Scene"
    })
    scene_id = scene_resp.json()["id"]
    
    # Add multiple items
    for i in range(3):
        client.post(f"/api/v1/scenes/{scene_id}/items", json={
            "part_revision_id": revision_id,
            "supplied_id": f"item-{i}"
        })
    
    response = client.get(f"/api/v1/scenes/{scene_id}/items")
    assert response.status_code == 200
    assert len(response.json()) == 3
```

### 3.1.1 Job Status Tests (vertex: Translation job polling)

### 3.1.1 Job Status Tests (vertex: Translation job polling)

```python
# tests/phase3_rendering/test_jobs.py

def test_job_status_pending(client, account_id):
    """Test job starts in pending state"""
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "JOB-PENDING-001",
        "name": "Job Pending Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    files = {"file": ("test.glb", io.BytesIO(b"fake"), "model/gltf-binary")}
    file_resp = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    file_id = file_resp.json()["id"]
    
    conv_resp = client.post("/api/v1/convert", json={"file_id": file_id})
    job_id = conv_resp.json()["job_id"]
    
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "processing", "completed", "failed"]

def test_job_status_completed(client, account_id):
    """Test job completes successfully - vertex: queued translation redirects to part"""
    import time
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "JOB-COMPLETE-001",
        "name": "Job Complete Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    files = {"file": ("test.glb", io.BytesIO(b"GLB_DATA"), "model/gltf-binary")}
    file_resp = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    file_id = file_resp.json()["id"]
    
    conv_resp = client.post("/api/v1/convert", json={"file_id": file_id})
    job_id = conv_resp.json()["job_id"]
    
    # Poll for completion
    for _ in range(30):
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        status_data = status_resp.json()
        if status_data["status"] in ["completed", "failed"]:
            break
        time.sleep(1)
    
    assert status_data["status"] == "completed"

def test_job_status_failed(client, account_id):
    """Test job fails with invalid input"""
    import time
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "JOB-FAIL-001",
        "name": "Job Fail Test"
    })
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": "A"})
    revision_id = rev_resp.json()["id"]
    
    # Upload invalid/corrupt file
    files = {"file": ("invalid.bin", io.BytesIO(b"INVALID_DATA"), "application/octet-stream")}
    file_resp = client.post("/api/v1/files", data={"part_revision_id": revision_id}, files=files)
    file_id = file_resp.json()["id"]
    
    conv_resp = client.post("/api/v1/convert", json={"file_id": file_id})
    job_id = conv_resp.json()["job_id"]
    
    # Poll for failure
    for _ in range(30):
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        status_data = status_resp.json()
        if status_data["status"] in ["completed", "failed"]:
            break
        time.sleep(1)
    
    assert status_data["status"] == "failed"
    assert "error" in status_data
```

### 3.2 Stream Key Tests (vertex: Authentication - Stream Keys)

```python
# tests/phase3_rendering/test_stream_keys.py

def test_create_stream_key(client, account_id):
    """Test creating a stream key - vertex: POST /scenes/{id}/stream-keys"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Stream Key Test"
    })
    scene_id = scene_resp.json()["id"]
    client.patch(f"/api/v1/scenes/{scene_id}", json={"state": "commit"})
    
    response = client.post(f"/api/v1/scenes/{scene_id}/stream-keys", json={
        "expiry": 600
    })
    assert response.status_code == 201
    data = response.json()
    assert "key" in data
    assert data["expiry"] == 600

def test_stream_key_expiry(client, account_id):
    """Test stream key expiry"""
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "Expiry Test"
    })
    scene_id = scene_resp.json()["id"]
    client.patch(f"/api/v1/scenes/{scene_id}", json={"state": "commit"})
    
    response = client.post(f"/api/v1/scenes/{scene_id}/stream-keys", json={
        "expiry": 3600
    })
    assert response.json()["expiry"] == 3600
```

### 3.3 Render Server Tests

```python
# tests/phase3_rendering/test_render_server.py

def test_renderer_initialization(render_server):
    """Test renderer initializes correctly"""
    assert render_server.width == 1920
    assert render_server.height == 1080

def test_load_geometry(render_server):
    """Test loading geometry into scene"""
    render_server.load_geometry(b"fake glb data")
    assert len(render_server.scene.children) > 0

def test_render_to_image(render_server):
    """Test rendering scene to image"""
    image_data = render_server.render()
    assert image_data is not None
    assert len(image_data) > 0

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connects - vertex: viewer connects to stream"""
    async with connect("ws://localhost:8080/ws") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(msg)
        assert data["type"] == "ready"

@pytest.mark.asyncio
async def test_websocket_camera_command():
    """Test camera command via WebSocket"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()  # ready
        await ws.send(json.dumps({
            "type": "camera",
            "position": [5, 5, 5],
            "target": [0, 0, 0]
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(msg)
        assert data["type"] == "frame"

@pytest.mark.asyncio
async def test_frame_streaming_fps():
    """Test frame streaming at reasonable FPS"""
    frames = []
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        import time
        start = time.time()
        for _ in range(10):
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            if data["type"] == "frame":
                frames.append(data)
        elapsed = time.time() - start
        fps = len(frames) / elapsed
        assert fps >= 5  # At least 5 FPS for interactive
```

---

## Phase 4: Viewer & Scene Operations Tests

### 4.1 Viewer Load Tests (vertex: Render your first scene)

```python
# tests/phase4_viewer/test_viewer_load.py

def test_viewer_page_loads(test_client):
    """Test that viewer HTML page loads - vertex: viewer loads scene"""
    response = test_client.get("/viewer/")
    assert response.status_code == 200

def test_viewer_loads_with_stream_key(test_client):
    """Test viewer loads scene via stream key - vertex: viewer.load(urn:vertex:stream-key:xxx)"""
    # Stream key in URL or config
    response = test_client.get("/viewer/?stream_key=test-key")
    assert response.status_code == 200
```

### 4.2 Selection Tests (vertex: Interact with scene - tap to select)

```python
# tests/phase4_viewer/test_selection.py

@pytest.mark.asyncio
async def test_click_to_select():
    """Test clicking item to select - vertex: tap event -> raycaster.hitItems"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "select",
            "position": {"x": 0.5, "y": 0.5}
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(msg)
        assert data["type"] in ["hit", "deselected"]

@pytest.mark.asyncio
async def test_selection_highlight():
    """Test selected item visually highlighted - vertex: select() operation"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "select",
            "position": {"x": 0.5, "y": 0.5}
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"
```

### 4.3 Scene Operations Tests (vertex: Customize your scene)

#### Queries Tests

```python
# tests/phase4_viewer/test_queries.py

@pytest.mark.asyncio
async def test_query_all():
    """Test query all items - vertex: q.all()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "all"},
            "operation": "hide"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_item_id():
    """Test query by item ID - vertex: q.withItemId(id)"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "withItemId", "id": "item-uuid"},
            "operation": "hide"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_supplied_id():
    """Test query by supplied ID - vertex: q.withSuppliedId(id)"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "withSuppliedId", "suppliedId": "part-123"},
            "operation": "show"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_selected():
    """Test query selected items - vertex: q.withSelected()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "withSelected"},
            "operation": "hide"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_metadata():
    """Test query by metadata - vertex: q.withMetadata()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {
                "type": "withMetadata",
                "filter": "Gear",
                "keys": ["PART_NAME"]
            },
            "operation": "hide"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_not():
    """Test NOT query - vertex: q.not()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "not", "query": {"type": "withSelected"}},
            "operation": "show"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"
```

#### Operations Tests

```python
# tests/phase4_viewer/test_operations.py

@pytest.mark.asyncio
async def test_operation_show():
    """Test show operation - vertex: op.show()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "show"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_operation_hide():
    """Test hide operation - vertex: op.hide()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "hide"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_operation_select():
    """Test select operation - vertex: op.select()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "select"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_operation_deselect():
    """Test deselect operation - vertex: op.deselect()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "deselect"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_operation_material_override():
    """Test material override - vertex: op.materialOverride()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "materialOverride",
            "color": {"r": 255, "g": 0, "b": 0, "a": 1.0}
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_operation_clear_material():
    """Test clear material override - vertex: op.clearMaterialOverrides()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "clearMaterialOverrides"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_operation_transform():
    """Test transform operation - vertex: op.transform()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "transform",
            "matrix": [1,0,0,0, 0,1,0,0, 0,0,1,0, 10,0,0,1]
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_operation_phantom():
    """Test phantom operation - vertex: op.setPhantom()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "setPhantom",
            "value": True
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"
```

### 4.4 Camera Controls Tests

```python
# tests/phase4_viewer/test_camera.py

@pytest.mark.asyncio
async def test_orbit_camera():
    """Test orbiting camera - vertex: camera orbit controls"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "camera",
            "orbit": {"theta": 45, "phi": 30, "distance": 10}
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_preset_view_top():
    """Test top view preset - vertex: view cube top"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "view", "mode": "top"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_preset_view_front():
    """Test front view preset"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "view", "mode": "front"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_preset_view_iso():
    """Test isometric view preset - vertex: view cube isometric"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "view", "mode": "iso"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_camera_pan():
    """Test pan camera"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "camera",
            "pan": {"x": 10, "y": 5}
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_camera_zoom():
    """Test zoom camera"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "camera",
            "zoom": 2.0
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_camera_fit_to_bounding_box():
    """Test fit to bounding box - vertex: fitToBoundingBox"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "camera",
            "fitToBoundingBox": {
                "min": [-100, -100, -100],
                "max": [100, 100, 100]
            }
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_camera_view_back():
    """Test back view preset"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "view", "mode": "back"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_camera_view_left():
    """Test left view preset"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "view", "mode": "left"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_camera_view_right():
    """Test right view preset"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "view", "mode": "right"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_camera_view_bottom():
    """Test bottom view preset"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "view", "mode": "bottom"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

### 4.5 Advanced Viewer Tests (Vertex Examples)

```python
# tests/phase4_viewer/test_advanced.py

@pytest.mark.asyncio
async def test_tap_to_select():
    """Test tap/click to select - vertex: picking example"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "select",
            "position": {"x": 0.5, "y": 0.5}
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        # Either hit or miss
        assert msg["type"] in ["hit", "miss"]

@pytest.mark.asyncio
async def test_select_by_item_id():
    """Test selection by item ID"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "select",
            "itemId": "test-item-uuid"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_deselect_all():
    """Test deselect all items"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "deselect"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_phantom_mode():
    """Test phantom mode - vertex: phantom-parts example"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "withItemId", "id": "test-item"},
            "operation": "setPhantom",
            "value": True
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_clear_phantom():
    """Test clear phantom mode"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "all"},
            "operation": "clearPhantom"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_end_item():
    """Test end item state - vertex: end-items example"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "withSelected"},
            "operation": "setEndItem",
            "value": True
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_clear_end_item():
    """Test clear end item"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {"type": "all"},
            "operation": "clearEndItem"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_item_ids():
    """Test query multiple item IDs - vertex: q.withItemIds"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {
                "type": "withItemIds",
                "ids": ["id1", "id2", "id3"]
            },
            "operation": "hide"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_supplied_ids():
    """Test query by supplied IDs"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {
                "type": "withSuppliedIds",
                "suppliedIds": ["part-1", "part-2"]
            },
            "operation": "show"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_volume_intersection():
    """Test query by volume/rectangle - vertex: q.withVolumeIntersection"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {
                "type": "withVolumeIntersection",
                "rectangle": {"x": 100, "y": 100, "width": 100, "height": 100},
                "exclusive": False
            },
            "operation": "hide"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_with_point():
    """Test query by point - vertex: q.withPoint"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {
                "type": "withPoint",
                "point": {"x": 100, "y": 100}
            },
            "operation": "select"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_query_not_with_selected():
    """Test NOT query - vertex: q.not().withSelected()"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "operation",
            "query": {
                "type": "not",
                "query": {"type": "withSelected"}
            },
            "operation": "show"
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_scene_tree_expand_all():
    """Test scene tree expand all - vertex: scene-tree example"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "sceneTree",
            "expandAll": True
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "sceneTree"

@pytest.mark.asyncio
async def test_scene_tree_collapse_all():
    """Test scene tree collapse all"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "sceneTree",
            "collapseAll": True
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "sceneTree"

@pytest.mark.asyncio
async def test_walk_mode_enable():
    """Test walk mode enable - vertex: walk-mode example"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "walkMode",
            "enabled": True
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        # Walk mode doesn't necessarily return a frame

@pytest.mark.asyncio
async def test_walk_mode_teleport():
    """Test walk mode teleport"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "walkMode",
            "teleport": {"position": [10, 0, 10]}
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"

@pytest.mark.asyncio
async def test_walk_mode_speed():
    """Test walk mode speed setting"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "walkMode",
            "speed": 5
        }))
        # Should not error

@pytest.mark.asyncio
async def test_stream_fps_control():
    """Test streaming at different FPS"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        # Request 5 FPS
        await ws.send(json.dumps({
            "type": "stream",
            "fps": 5
        }))
        # Should start streaming at 5 FPS

@pytest.mark.asyncio
async def test_stream_stop():
    """Test stopping stream"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        await ws.send(json.dumps({
            "type": "stream",
            "fps": 0
        }))
        # Should stop streaming
```

---

## Phase 5: Integration & Authentication Tests

### 5.1 Authentication Tests (vertex: OAuth2)

```python
# tests/phase5_integration/test_authentication.py

def test_oauth2_client_credentials():
    """Test OAuth2 client credentials flow - vertex: grant_type=client_credentials"""
    response = client.post("/oauth2/token", data={
        "grant_type": "client_credentials"
    }, auth=(client_id, client_secret))
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_oauth2_token_expiry():
    """Test token expires after configured time"""
    response = client.post("/oauth2/token", data={
        "grant_type": "client_credentials"
    }, auth=(client_id, client_secret))
    assert response.json()["expires_in"] == 3600

def test_invalid_credentials():
    """Test invalid credentials are rejected"""
    response = client.post("/oauth2/token", data={
        "grant_type": "client_credentials"
    }, auth=("invalid", "invalid"))
    assert response.status_code == 401

def test_api_key_auth():
    """Test API key authentication"""
    response = client.get("/api/v1/parts", headers={
        "X-API-Key": "test-key"
    })
    assert response.status_code in [200, 401]
```

### 5.2 User Management Tests (vertex: User management)

```python
# tests/phase5_integration/test_users.py

def test_create_user(client):
    """Test creating a user - vertex: POST /users"""
    response = client.post("/api/v1/users", json={
        "email": "user@example.com",
        "name": "Test User"
    })
    assert response.status_code == 201

def test_list_users(client):
    """Test listing users - vertex: GET /users"""
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user_group(client):
    """Test creating user group - vertex: POST /user-groups"""
    response = client.post("/api/v1/user-groups", json={
        "name": "Engineers",
        "supplied_id": "engineers-group"
    })
    assert response.status_code == 201

def test_add_user_to_group(client):
    """Test adding user to group - vertex: POST /users-groups/{id}/users"""
    user_resp = client.post("/api/v1/users", json={
        "email": "user@example.com",
        "name": "Test User"
    })
    user_id = user_resp.json()["id"]
    
    group_resp = client.post("/api/v1/user-groups", json={
        "name": "Test Group"
    })
    group_id = group_resp.json()["id"]
    
    response = client.post(f"/api/v1/user-groups/{group_id}/users", json={
        "user_id": user_id
    })
    assert response.status_code == 200
```

### 5.3 End-to-End Tests

```python
# tests/phase5_integration/test_end_to_end.py

def test_complete_workflow():
    """Test: Create account -> Upload CAD -> Convert -> Create Scene -> Render"""
    # 1. Create account
    account_resp = client.post("/api/v1/accounts", json={"name": "E2E"})
    account_id = account_resp.json()["id"]
    
    # 2. Create part
    part_resp = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "E2E-001",
        "name": "End to End Test"
    })
    part_id = part_resp.json()["id"]
    
    # 3. Create revision
    rev_resp = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": "A"
    })
    revision_id = rev_resp.json()["id"]
    
    # 4. Upload and convert (simulated)
    geom_resp = client.post("/api/v1/geometry", json={
        "part_revision_id": revision_id,
        "format": "glb",
        "version": "high"
    })
    
    # 5. Create scene
    scene_resp = client.post("/api/v1/scenes", json={
        "account_id": account_id,
        "name": "E2E Scene"
    })
    scene_id = scene_resp.json()["id"]
    
    # 6. Add item
    client.post(f"/api/v1/scenes/{scene_id}/items", json={
        "part_revision_id": revision_id
    })
    
    # 7. Commit
    client.patch(f"/api/v1/scenes/{scene_id}", json={"state": "commit"})
    
    # 8. Render image
    img_resp = client.get(f"/api/v1/scenes/{scene_id}/image?width=1000&height=1000")
    assert img_resp.status_code == 200

def test_viewer_interaction_workflow():
    """Test: Connect viewer -> Load scene -> Select item -> Change material"""
    # WebSocket flow test
    async with connect("ws://localhost:8080/ws") as ws:
        # Connect
        await ws.recv()
        
        # Load scene
        await ws.send(json.dumps({"type": "connect", "sceneId": "test-scene"}))
        await ws.recv()
        
        # Select item
        await ws.send(json.dumps({
            "type": "select",
            "position": {"x": 0.5, "y": 0.5}
        }))
        
        # Change material
        await ws.send(json.dumps({
            "type": "operation",
            "operation": "materialOverride",
            "color": {"r": 255, "g": 0, "b": 0}
        }))
        
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        assert msg["type"] == "frame"
```

### 5.4 Performance Tests

```python
# tests/phase5_integration/test_performance.py

def test_api_response_time():
    """Test API responds within acceptable time"""
    import time
    start = time.time()
    client.post("/api/v1/parts", json={
        "account_id": str(uuid4()),
        "supplied_id": f"PERF-{uuid4()}",
        "name": "Performance Test"
    })
    elapsed = time.time() - start
    assert elapsed < 1.0

@pytest.mark.asyncio
async def test_websocket_latency():
    """Test WebSocket frame delivery latency"""
    async with connect("ws://localhost:8080/ws") as ws:
        await ws.recv()
        import time
        start = time.time()
        await ws.send(json.dumps({"type": "render"}))
        await asyncio.wait_for(ws.recv(), timeout=30)
        elapsed = time.time() - start
        assert elapsed < 5.0

def test_concurrent_requests():
    """Test system handles concurrent requests"""
    import concurrent.futures
    def make_request():
        return client.get("/api/v1/parts")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    assert all(r.status_code == 200 for r in results)
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific phase
pytest tests/phase1_database/ -v
pytest tests/phase2_ingestion/ -v
pytest tests/phase3_rendering/ -v
pytest tests/phase4_viewer/ -v
pytest tests/phase5_integration/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

---

## Test Coverage Goals

| Phase | Minimum Coverage |
|-------|------------------|
| Phase 1 (Database) | 90% |
| Phase 2 (Ingestion) | 85% |
| Phase 3 (Rendering) | 80% |
| Phase 4 (Viewer) | 80% |
| Phase 5 (Integration) | 75% |

---

## Vertex3D Guide to Test Mapping

| Vertex3D Guide | Test Coverage |
|---------------|---------------|
| **Render your first scene** | `test_viewer_page_loads`, `test_websocket_connection`, `test_click_to_select`, `test_selection_highlight` |
| **Import data (CLI)** | `test_cli_configure`, `test_cli_parts_list`, `test_cli_parts_get`, `test_cli_parts_delete`, `test_cli_files_list`, `test_cli_files_get`, `test_cli_files_delete`, `test_cli_scenes_list`, `test_cli_scenes_get`, `test_cli_scenes_delete`, `test_cli_scenes_create`, `test_cli_scenes_render`, `test_cli_create_parts`, `test_cli_create_scene`, `test_cli_stream_keys_create`, `test_cli_exports_create`, `test_cli_exports_download`, `test_cli_create_items`, `test_cli_scene_view_states_list`, `test_cli_scene_view_states_get` |
| **Import data (API)** | `test_upload_file`, `test_trigger_conversion`, `test_check_conversion_status`, `test_full_ingestion_workflow` |
| **Import metadata** | `test_update_revision_metadata`, `test_get_revision_metadata`, `test_metadata_types` |
| **Render static scenes** | `test_create_scene`, `test_add_scene_item`, `test_commit_scene`, `test_render_scene_image`, `test_scene_transform_matrix`, `test_delete_scene`, `test_delete_scene_item`, `test_scene_state_draft`, `test_scene_state_transition_draft_to_commit`, `test_scene_item_visibility_default`, `test_scene_item_set_visibility`, `test_get_scene`, `test_list_scene_items`, `test_job_status_pending`, `test_job_status_completed`, `test_job_status_failed` |
| **Authentication** | `test_oauth2_client_credentials`, `test_create_stream_key` |
| **Customize your scene** | All `test_query_*`, `test_operation_*`, `test_camera_*`, `test_phantom_*`, `test_end_item_*`, `test_walk_mode_*`, `test_scene_tree_*` tests |
| **User management** | `test_create_user`, `test_list_users`, `test_create_user_group`, `test_add_user_to_group` |

---

## Notes

- Tests use `pytest` with `pytest-asyncio` for async tests
- Database tests use test PostgreSQL or in-memory SQLite
- WebSocket tests use `websockets` library
- Browser tests use Playwright for E2E testing
- All tests should be idempotent and clean up after themselves
