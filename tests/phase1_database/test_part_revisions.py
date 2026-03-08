import pytest

@pytest.fixture
def account_id(client):
    response = client.post("/api/v1/accounts", json={"name": "Test Account"})
    return response.json()["id"]

@pytest.fixture
def part_id(client, account_id):
    response = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "PART-REV-TEST",
        "name": "Part Rev Test"
    })
    return response.json()["id"]

def test_create_part_revision(client, part_id):
    payload = {
        "part_id": part_id,
        "revision_number": 1,
        "supplied_id": "REV-001",
        "status": "draft",
        "metadata": {"designer": "Alice"}
    }
    response = client.post("/api/v1/part-revisions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["revision_number"] == 1
    assert data["status"] == "draft"
    assert data["metadata"]["designer"] == "Alice"

def test_list_part_revisions(client, part_id):
    for i in range(3):
        client.post("/api/v1/part-revisions", json={
            "part_id": part_id,
            "revision_number": i + 1
        })
    response = client.get(f"/api/v1/part-revisions?part_id={part_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["part_id"] == part_id

def test_revision_cascade_delete(client, part_id):
    rev_resp = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": 1
    })
    rev_id = rev_resp.json()["id"]
    
    # Delete the part
    client.delete(f"/api/v1/parts/{part_id}")
    
    # Check if revision is also deleted
    get_resp = client.get(f"/api/v1/part-revisions/{rev_id}")
    assert get_resp.status_code == 404
