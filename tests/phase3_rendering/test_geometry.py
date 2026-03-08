import pytest

@pytest.fixture
def account_id(client):
    response = client.post("/api/v1/accounts", json={"name": "Test Account"})
    return response.json()["id"]

@pytest.fixture
def part_id(client, account_id):
    response = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "GEOM-PART-001",
        "name": "Geometry Part"
    })
    return response.json()["id"]

@pytest.fixture
def revision_id(client, part_id):
    response = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": 1
    })
    return response.json()["id"]

def test_create_geometry(client, revision_id):
    """Test creating geometry"""
    response = client.post("/api/v1/geometry", json={
        "part_revision_id": revision_id,
        "format": "glb",
        "version": "high",
        "vertex_count": 1000,
        "face_count": 500,
        "data": {"mock": "binary_data"}
    })
    assert response.status_code == 201
    data = response.json()
    assert data["format"] == "glb"
    assert data["version"] == "high"
    assert data["vertex_count"] == 1000

def test_get_geometry(client, revision_id):
    """Test getting geometry metadata"""
    create_resp = client.post("/api/v1/geometry", json={
        "part_revision_id": revision_id,
        "format": "glb",
        "version": "low"
    })
    geom_id = create_resp.json()["id"]
    
    response = client.get(f"/api/v1/geometry/{geom_id}")
    assert response.status_code == 200
    assert response.json()["format"] == "glb"
    assert response.json()["version"] == "low"

def test_get_geometry_data(client, revision_id):
    """Test getting geometry data"""
    create_resp = client.post("/api/v1/geometry", json={
        "part_revision_id": revision_id,
        "format": "step",
        "version": "original",
        "data": {"my": "data"}
    })
    geom_id = create_resp.json()["id"]
    
    response = client.get(f"/api/v1/geometry/{geom_id}/data")
    assert response.status_code == 200
    assert response.json() == {"my": "data"}
