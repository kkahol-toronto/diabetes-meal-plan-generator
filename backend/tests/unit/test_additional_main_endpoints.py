"""
Comprehensive test suite for additional main.py endpoints
Designed to push test coverage to 95%+
"""

import unittest
import json
import base64
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from main import app, get_current_user

class TestAuthenticationEndpoints(unittest.TestCase):
    """Test authentication and registration endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.mock_user = {
            "id": "test@example.com",
            "username": "testuser",
            "email": "test@example.com",
            "disabled": False,
            "patient_id": "TEST123"
        }
    
    def tearDown(self):
        """Clean up after tests."""
        app.dependency_overrides.clear()

    @patch("main.get_user_by_email")
    @patch("main.verify_password")
    @patch("main.create_access_token")
    @patch("main.user_container")
    def test_login_success(self, mock_container, mock_create_token, mock_verify, mock_get_user):
        """Test successful user login."""
        mock_get_user.return_value = {
            "id": "test@example.com",
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password",
            "disabled": False
        }
        mock_verify.return_value = True
        mock_create_token.return_value = "jwt_token_123"
        
        login_data = {
            "username": "test@example.com",
            "password": "password123",
            "consent_given": "true",
            "consent_timestamp": "2023-01-01T00:00:00Z",
            "policy_version": "1.0"
        }
        
        response = self.client.post("/token", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt_token_123"
        assert data["token_type"] == "bearer"

    @patch("main.get_user_by_email")
    def test_login_invalid_credentials(self, mock_get_user):
        """Test login with invalid credentials."""
        mock_get_user.return_value = None
        
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = self.client.post("/token", data=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Incorrect username or password"

class TestUtilityEndpoints(unittest.TestCase):
    """Test utility and validation endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.mock_user = {
            "id": "test@example.com",
            "username": "testuser",
            "email": "test@example.com",
            "disabled": False,
            "patient_id": "TEST123"
        }
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
    
    def tearDown(self):
        """Clean up after tests."""
        app.dependency_overrides.clear()

    def test_echo_endpoint(self):
        """Test echo utility endpoint."""
        test_message = {"message": "Hello, world!"}
        
        response = self.client.post("/test/echo", json=test_message)
        
        assert response.status_code == 200
        data = response.json()
        assert data["echo"]["message"] == "Hello, world!"

    def test_validate_email_endpoint(self):
        """Test email validation endpoint."""
        response = self.client.post("/utils/validate-email", json={
            "email": "valid@example.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True

class TestHealthCheckEndpoints(unittest.TestCase):
    """Test health check and monitoring endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to Diabetes Diet Manager API"

    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

if __name__ == "__main__":
    unittest.main()
