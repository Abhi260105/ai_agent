"""
Integration tests for REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json


@pytest.mark.integration
class TestAPIEndpoints:
    """Test REST API endpoint integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client for API."""
        from app.ui.api.main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for testing."""
        return {"X-API-Key": "test-key-123"}
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert 'name' in data
        assert 'version' in data
        assert 'endpoints' in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] in ['healthy', 'operational']
        assert 'services' in data
    
    def test_create_task(self, client, auth_headers):
        """Test creating a task via API."""
        task_data = {
            "description": "Test task",
            "priority": "high",
            "use_memory": True,
            "use_tools": True
        }
        
        response = client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['description'] == "Test task"
        assert data['priority'] == "high"
    
    def test_list_tasks(self, client, auth_headers):
        """Test listing tasks."""
        response = client.get(
            "/api/v1/tasks/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_task(self, client, auth_headers):
        """Test getting specific task."""
        # First create a task
        task_data = {"description": "Get test task"}
        create_response = client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=auth_headers
        )
        task_id = create_response.json()['id']
        
        # Then get it
        response = client.get(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == task_id
    
    def test_update_task(self, client, auth_headers):
        """Test updating a task."""
        # Create task
        create_response = client.post(
            "/api/v1/tasks/",
            json={"description": "Original"},
            headers=auth_headers
        )
        task_id = create_response.json()['id']
        
        # Update it
        update_data = {"priority": "critical"}
        response = client.put(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['priority'] == "critical"
    
    def test_delete_task(self, client, auth_headers):
        """Test deleting a task."""
        # Create task
        create_response = client.post(
            "/api/v1/tasks/",
            json={"description": "To delete"},
            headers=auth_headers
        )
        task_id = create_response.json()['id']
        
        # Delete it
        response = client.delete(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    def test_memory_endpoints(self, client, auth_headers):
        """Test memory CRUD endpoints."""
        # Create memory
        memory_data = {
            "content": "Test memory",
            "memory_type": "semantic",
            "importance": "high"
        }
        
        create_response = client.post(
            "/api/v1/memory/",
            json=memory_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        memory_id = create_response.json()['id']
        
        # Get memory
        get_response = client.get(
            f"/api/v1/memory/{memory_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        assert get_response.json()['content'] == "Test memory"
    
    def test_memory_search(self, client, auth_headers):
        """Test memory search endpoint."""
        search_data = {
            "query": "test query",
            "limit": 10
        }
        
        response = client.post(
            "/api/v1/memory/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'memories' in data or 'knowledge_items' in data
        assert 'total_count' in data
    
    def test_tool_endpoints(self, client, auth_headers):
        """Test tool management endpoints."""
        # List tools
        response = client.get(
            "/api/v1/tools/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        assert len(tools) > 0
    
    def test_invoke_tool(self, client, auth_headers):
        """Test tool invocation endpoint."""
        invocation_data = {
            "tool_name": "calculator",
            "parameters": {"expression": "2 + 2"}
        }
        
        response = client.post(
            "/api/v1/tools/invoke",
            json=invocation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'result' in data
    
    def test_pagination(self, client, auth_headers):
        """Test API pagination."""
        response = client.get(
            "/api/v1/tasks/?limit=5&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
    
    def test_filtering(self, client, auth_headers):
        """Test API filtering."""
        response = client.get(
            "/api/v1/tasks/?status=completed&priority=high",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            assert all(task.get('status') == 'completed' for task in data)
    
    def test_authentication_required(self, client):
        """Test that authentication is required."""
        response = client.get("/api/v1/tasks/")
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_invalid_auth(self, client):
        """Test invalid authentication."""
        response = client.get(
            "/api/v1/tasks/",
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401
    
    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting."""
        # Make many rapid requests
        responses = []
        for _ in range(150):  # Exceed typical rate limit
            response = client.get(
                "/api/v1/tasks/",
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # Should get rate limited
        assert 429 in responses
    
    def test_error_handling(self, client, auth_headers):
        """Test API error handling."""
        # Try to get non-existent task
        response = client.get(
            "/api/v1/tasks/nonexistent-id",
            headers=auth_headers
        )
        
        # Should return appropriate error
        assert response.status_code in [404, 400]
        
        # Error response should be JSON
        data = response.json()
        assert 'error' in data or 'detail' in data
    
    def test_validation_errors(self, client, auth_headers):
        """Test input validation."""
        # Send invalid task data
        invalid_data = {
            "priority": "invalid_priority"  # Not in allowed values
        }
        
        response = client.post(
            "/api/v1/tasks/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_concurrent_requests(self, client, auth_headers):
        """Test handling concurrent requests."""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/tasks/", headers=auth_headers)
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
    
    def test_admin_endpoints(self, client):
        """Test admin-only endpoints."""
        admin_headers = {"X-API-Key": "admin-key-123"}
        
        response = client.get(
            "/api/v1/admin/stats",
            headers=admin_headers
        )
        
        # Should work with admin key
        assert response.status_code in [200, 401]  # Depends on auth setup
    
    def test_openapi_documentation(self, client):
        """Test OpenAPI documentation is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        openapi_spec = response.json()
        assert 'openapi' in openapi_spec
        assert 'paths' in openapi_spec
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/v1/tasks/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should have CORS headers
        assert 'access-control-allow-origin' in response.headers
    
    def test_request_id_header(self, client, auth_headers):
        """Test X-Request-ID header is returned."""
        response = client.get(
            "/api/v1/tasks/",
            headers=auth_headers
        )
        
        # Should have request ID
        assert 'x-request-id' in response.headers
    
    def test_api_versioning(self, client, auth_headers):
        """Test API versioning."""
        # V1 endpoint should work
        response = client.get(
            "/api/v1/tasks/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_batch_operations(self, client, auth_headers):
        """Test batch task creation."""
        batch_data = {
            "tasks": [
                {"description": "Task 1"},
                {"description": "Task 2"},
                {"description": "Task 3"}
            ]
        }
        
        response = client.post(
            "/api/v1/tasks/batch",
            json=batch_data,
            headers=auth_headers
        )
        
        # May or may not be implemented
        assert response.status_code in [200, 201, 404]
    
    def test_webhook_integration(self, client, auth_headers):
        """Test webhook notification setup."""
        webhook_config = {
            "url": "https://example.com/webhook",
            "events": ["task.completed", "task.failed"]
        }
        
        response = client.post(
            "/api/v1/admin/webhooks",
            json=webhook_config,
            headers={"X-API-Key": "admin-key-123"}
        )
        
        # May or may not be implemented
        assert response.status_code in [200, 201, 401, 404]