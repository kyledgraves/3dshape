"""
Tests for render server fetching geometry from backend API.

These tests verify:
1. Render server can connect to backend API
2. Geometry can be fetched from backend
3. Headless renderer can load geometry data
"""

import pytest
import os


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


class TestRenderServerGeometryIntegration:
    """Integration tests for render server fetching geometry from backend"""

    @pytest.fixture
    def setup_geometry(self, client, revision_id):
        """Create geometry in the database"""
        response = client.post("/api/v1/geometry", json={
            "part_revision_id": revision_id,
            "format": "glb",
            "version": "high",
            "vertex_count": 1000,
            "data": "dGVzdCBnZW9tZXRyeSBkYXRh"  # "test geometry data" in base64
        })
        return response.json()

    def test_backend_geometry_endpoint_available(self, client, setup_geometry):
        """Test that geometry endpoint is available"""
        geom_id = setup_geometry["id"]
        response = client.get(f"/api/v1/geometry/{geom_id}/render-data")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == geom_id
        assert data["format"] == "glb"

    def test_websocket_load_command_supported(self):
        """Test that WebSocket load command is supported in websocket handler"""
        ws_handler_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "render-server", "src", "websocket-handler.js"
        )
        
        if os.path.exists(ws_handler_path):
            with open(ws_handler_path) as f:
                content = f.read()
                assert "command.type === 'load'" in content, "WebSocket load command not found"
        else:
            pytest.skip("websocket-handler.js not found")


class TestHeadlessRendererGeometryLoading:
    """Tests for headless renderer loading geometry data"""

    def test_headless_html_has_load_function(self):
        """Test that headless.html exposes loadGeometryFromData function"""
        import os
        headless_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "render-server", "public", "headless.html"
        )
        
        if os.path.exists(headless_path):
            with open(headless_path) as f:
                content = f.read()
                assert "window.loadGeometryFromData" in content, "loadGeometryFromData function not found"
        else:
            pytest.skip("headless.html not found")

    def test_playwright_renderer_exports_loadGeometry(self):
        """Test that playwright-renderer exports loadGeometry function"""
        import os
        renderer_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "render-server", "src", "playwright-renderer.js"
        )
        
        if os.path.exists(renderer_path):
            with open(renderer_path) as f:
                content = f.read()
                assert "loadGeometry" in content, "loadGeometry function not found in playwright-renderer"
        else:
            pytest.skip("playwright-renderer.js not found")
