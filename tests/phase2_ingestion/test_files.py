import pytest
import io

@pytest.fixture
def account_id(client):
    response = client.post("/api/v1/accounts", json={"name": "Test Account for Files"})
    return response.json()["id"]

@pytest.fixture
def part_id(client, account_id):
    response = client.post("/api/v1/parts", json={
        "account_id": account_id,
        "supplied_id": "PART-FILE-TEST",
        "name": "Part File Test"
    })
    return response.json()["id"]

@pytest.fixture
def part_revision_id(client, part_id):
    response = client.post("/api/v1/part-revisions", json={
        "part_id": part_id,
        "revision_number": 1
    })
    return response.json()["id"]

def test_file_upload(client, part_revision_id):
    # test file upload (multipart/form-data)
    file_content = b"fake 3d model content"
    files = {
        "file": ("test_model.obj", file_content, "application/octet-stream")
    }
    data = {
        "part_revision_id": str(part_revision_id)
    }
    
    response = client.post("/api/v1/files", data=data, files=files)
    assert response.status_code == 200
    
    resp_data = response.json()
    assert resp_data["original_filename"] == "test_model.obj"
    assert resp_data["file_size"] == len(file_content)
    assert resp_data["status"] == "uploaded"
    assert resp_data["part_revision_id"] == part_revision_id

def test_file_download(client, part_revision_id):
    file_content = b"fake 3d model content"
    files = {
        "file": ("test_model.obj", file_content, "application/octet-stream")
    }
    data = {
        "part_revision_id": str(part_revision_id)
    }
    response = client.post("/api/v1/files", data=data, files=files)
    file_id = response.json()["id"]
    
    # test get file metadata
    meta_response = client.get(f"/api/v1/files/{file_id}")
    assert meta_response.status_code == 200
    assert meta_response.json()["original_filename"] == "test_model.obj"
    
    # test file download
    dl_response = client.get(f"/api/v1/files/{file_id}/download")
    assert dl_response.status_code == 200
    assert dl_response.content == file_content
    assert "attachment" in dl_response.headers.get("Content-Disposition", "")
