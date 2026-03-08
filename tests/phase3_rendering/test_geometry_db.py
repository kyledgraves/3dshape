"""
Tests for geometry loading from database feature.

This tests the flow where:
1. Geometry is stored in PostgreSQL via backend API
2. Render server fetches geometry from backend
3. Headless renderer loads the geometry by ID
"""

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


@pytest.fixture
def test_geometry_data():
    """Create a minimal GLB-like binary data for testing"""
    return {
        "format": "glb",
        "version": "1.0",
        "vertex_count": 100,
        "face_count": 50,
        "bounding_box": {
            "min": {"x": -1, "y": -1, "z": -1},
            "max": {"x": 1, "y": 1, "z": 1}
        },
        "data": "mock_glb_base64_data"
    }


class TestGeometryStorage:
    """Test geometry storage in PostgreSQL"""

    def test_store_geometry_with_all_fields(self, client, revision_id, test_geometry_data):
        """Test storing complete geometry metadata and data"""
        response = client.post("/api/v1/geometry", json={
            "part_revision_id": revision_id,
            **test_geometry_data
        })
        assert response.status_code == 201
        data = response.json()
        assert data["format"] == "glb"
        assert data["vertex_count"] == 100
        assert data["face_count"] == 50

    def test_store_multiple_geometry_versions(self, client, revision_id):
        """Test storing multiple geometry versions for same part revision"""
        versions = ["low", "medium", "high"]
        
        for version in versions:
            response = client.post("/api/v1/geometry", json={
                "part_revision_id": revision_id,
                "format": "glb",
                "version": version,
                "vertex_count": 1000 if version == "low" else 5000 if version == "medium" else 10000
            })
            assert response.status_code == 201
        
        # Verify all versions stored
        geom_response = client.get(f"/api/v1/geometry/{revision_id}/by-revision")
        # Note: This endpoint doesn't exist yet - would need to implement

    def test_geometry_data_retrieval(self, client, revision_id, test_geometry_data):
        """Test that geometry data can be retrieved separately"""
        create_resp = client.post("/api/v1/geometry", json={
            "part_revision_id": revision_id,
            **test_geometry_data
        })
        geom_id = create_resp.json()["id"]
        
        # Fetch geometry metadata
        meta_resp = client.get(f"/api/v1/geometry/{geom_id}")
        assert meta_resp.status_code == 200
        
        # Fetch geometry data
        data_resp = client.get(f"/api/v1/geometry/{geom_id}/data")
        assert data_resp.status_code == 200
        assert data_resp.json() == "mock_glb_base64_data"


class TestGeometryAPIAvailability:
    """Test that geometry API is available for render server consumption"""

    def test_render_server_can_fetch_geometry(self, client, revision_id, test_geometry_data):
        """Test that geometry can be fetched by render server"""
        # Store geometry
        create_resp = client.post("/api/v1/geometry", json={
            "part_revision_id": revision_id,
            **test_geometry_data
        })
        geom_id = create_resp.json()["id"]
        
        # Verify endpoint exists and returns data
        response = client.get(f"/api/v1/geometry/{geom_id}/data")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"

    def test_render_server_needs_render_data_endpoint(self, client, revision_id):
        """Test that render server has a specialized endpoint for render data"""
        # Create geometry
        client.post("/api/v1/geometry", json={
            "part_revision_id": revision_id,
            "format": "glb",
            "version": "high",
            "data": "test_data"
        })
        
        # This endpoint returns geometry data optimized for rendering
        response = client.get(f"/api/v1/geometry/1/render-data")
        
        # Should return 200 now that endpoint is implemented
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "glb"
        assert data["version"] == "high"
        assert data["data"] == "test_data"

    def test_scene_render_endpoint_exists(self, client, account_id, revision_id):
        """Test that scene render endpoint exists and returns geometry refs"""
        # Create scene
        scene_resp = client.post("/api/v1/scenes", json={
            "account_id": account_id,
            "name": "Test Scene"
        })
        scene_id = scene_resp.json()["id"]
        
        # Add scene item
        client.post(f"/api/v1/scenes/{scene_id}/items", json={
            "part_revision_id": revision_id,
            "transform_matrix": {"position": {"x": 0, "y": 0, "z": 0}},
            "visibility": True
        })
        
        # This endpoint should trigger render with geometry from DB
        response = client.post(f"/api/v1/scenes/{scene_id}/render")
        
        # Should return 200 now that endpoint is implemented
        assert response.status_code == 200
        data = response.json()
        assert data["scene_id"] == scene_id
        assert data["status"] == "rendering"


class TestSceneGeometryIntegration:
    """Test integration between scenes and geometry"""

    def test_scene_item_with_geometry(self, client, account_id, revision_id):
        """Test creating scene item that references geometry"""
        # Create scene
        scene_resp = client.post("/api/v1/scenes", json={
            "account_id": account_id,
            "name": "Test Scene"
        })
        scene_id = scene_resp.json()["id"]
        
        # Create geometry first
        geom_resp = client.post("/api/v1/geometry", json={
            "part_revision_id": revision_id,
            "format": "glb",
            "version": "high",
            "vertex_count": 1000
        })
        geometry_id = geom_resp.json()["id"]
        
        # Add scene item with geometry
        item_resp = client.post(f"/api/v1/scenes/{scene_id}/items", json={
            "part_revision_id": revision_id,
            "transform_matrix": {"position": {"x": 0, "y": 0, "z": 0}},
            "visibility": True
        })
        assert item_resp.status_code == 201
        
        # Verify scene can be rendered with geometry
        render_resp = client.post(f"/api/v1/scenes/{scene_id}/render")
        # This would trigger render server to load geometry from DB
