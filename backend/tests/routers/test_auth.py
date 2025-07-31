"""
Tests for authentication router in routers/auth.py
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, status

from routers.auth import router, get_current_user
from utils import create_access_token, get_password_hash


class TestAuthRouter:
    """Test authentication router functionality."""
    
    def test_router_exists(self):
        """Test that the auth router exists and has routes."""
        assert router is not None
        assert hasattr(router, 'routes')
        assert len(router.routes) > 0
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self):
        """Test get_current_user function with valid token."""
        token = create_access_token(data={"sub": "test@example.com"})
        
        mock_user = {
            "email": "test@example.com",
            "username": "testuser",
            "disabled": False
        }
        
        with patch('routers.auth.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = mock_user
            
            result = await get_current_user(token)
            
            assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self):
        """Test get_current_user function with invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(invalid_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestEndpointIntegration:
    """Test basic endpoint integration."""
    
    def test_login_endpoint_exists(self, client):
        """Test that login endpoint exists."""
        response = client.post("/login", data={"username": "test", "password": "test"})
        # Should not get 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_register_endpoint_exists(self, client):
        """Test that register endpoint exists.""" 
        response = client.post("/register", json={"registration_code": "TEST"})
        # Should not get 404 (endpoint exists)
        assert response.status_code != 404

    def test_auth_endpoints_basic(self, client):
        """Test basic auth endpoints exist and respond."""
        # Test various endpoints exist
        endpoints = ["/login", "/register"]
        
        for endpoint in endpoints:
            response = client.post(endpoint, json={})
            # Should not get 404 (endpoint exists)
            assert response.status_code != 404