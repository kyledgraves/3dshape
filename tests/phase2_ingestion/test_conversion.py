import pytest
import time

@pytest.fixture
def account_id(client):
    response = client.post("/api/v1/accounts", json={"name": "Test Account for Conversion"})
    return response.json()["id"]

@pytest.fixture
def part_id(client, account_id):
    response = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "PART-CONV-TEST",
        "name": "Part Conv Test"
    })
    return response.json()["id"]

@pytest.fixture
def part_revision_id(client, part_id):
    response = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": 1
    })
    return response.json()["id"]

@pytest.fixture
def file_id(client, part_revision_id):
    file_content = b"fake 3d model content to convert"
    files = {
        "file": ("test_model.obj", file_content, "application/octet-stream")
    }
    data = {
        "part_revision_id": str(part_revision_id)
    }
    response = client.post("/api/v1/files", data=data, files=files)
    return response.json()["id"]

def test_convert_endpoint_and_job_status(client, file_id):
    # test the convert endpoint and job status
    payload = {
        "file_id": str(file_id),
        "quality": "high"
    }
    response = client.post("/api/v1/convert", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"
    
    job_id = data["job_id"]
    
    # check status immediately
    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] in ["processing", "completed"]
    
    # wait a bit for background task to complete (1 second in jobs.py)
    time.sleep(1.2)
    
    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"
    
    # Check if file status is completed
    file_meta_response = client.get(f"/api/v1/files/{file_id}")
    assert file_meta_response.status_code == 200
    assert file_meta_response.json()["status"] == "completed"
