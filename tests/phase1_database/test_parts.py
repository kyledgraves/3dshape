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
