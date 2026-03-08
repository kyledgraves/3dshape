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
