import pytest

@pytest.fixture
def account_id(client):
    response = client.post("/api/v1/accounts", json={"name": "Test Account"})
    return response.json()["id"]

import pytest

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
        client.post("/api/v1/scenes", json={"account_id": account_id, "name": f"Scene {i}"})
    response = client.get(f"/api/v1/scenes?account_id={account_id}")
    assert response.status_code == 200
    assert len(response.json()) >= 3

def test_add_scene_item(client, account_id):
    """Test adding part to scene - vertex: createSceneItem"""
    part_resp = client.post("/api/v1/parts", json={"account_id": account_id, "supplied_id": "SCENE-PART-001", "name": "Scene Part"})
    part_id = part_resp.json()["id"]
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": 1})
    revision_id = rev_resp.json()["id"]
    geom_resp = client.post("/api/v1/geometry", json={"part_revision_id": revision_id, "format": "glb", "version": "high"})
    scene_resp = client.post("/api/v1/scenes", json={"account_id": account_id, "name": "Scene with Item"})
    scene_id = scene_resp.json()["id"]
    item_resp = client.post(f"/api/v1/scenes/{scene_id}/items", json={"part_revision_id": revision_id})
    assert item_resp.status_code == 201
    assert item_resp.json()["part_revision_id"] == revision_id

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
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": 1})
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
    rev_resp = client.post("/api/v1/part-revisions", json={"part_id": part_id, "revision_number": 1})
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
