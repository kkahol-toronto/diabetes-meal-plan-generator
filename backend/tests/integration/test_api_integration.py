"""
Integration tests for the diabetes meal plan generator API.
"""
import pytest
import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import json

# Import the main application
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from main import app


class TestApiIntegration(unittest.TestCase):
    """Integration tests for the API."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test the root endpoint is accessible."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Diabetes Diet Manager API" in data["message"]
    
    @patch("main.get_user_by_email")
    @patch("main.verify_password")
    @patch("main.create_access_token")
    def test_full_authentication_flow(self, mock_create_token, mock_verify_password, mock_get_user):
        """Test complete authentication flow."""
        # Mock user exists and credentials are valid
        mock_get_user.return_value = {
            "id": "test@example.com",
            "email": "test@example.com",
            "username": "testuser",
            "hashed_password": "hashed_password",
            "disabled": False,
            "patient_id": "TEST123"
        }
        mock_verify_password.return_value = True
        mock_create_token.return_value = "test_token"
        
        # Test login
        login_response = self.client.post(
            "/login",
            data={
                "username": "test@example.com",
                "password": "testpassword",
                "consent_given": "true",
                "consent_timestamp": "2023-01-01T00:00:00Z",
                "policy_version": "1.0"
            }
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert data["access_token"] == "test_token"
        assert data["token_type"] == "bearer"
    
    @patch("main.get_user_meal_plans")
    def test_meal_plan_workflow(self, mock_get_meal_plans):
        """Test complete meal plan workflow."""
        # Ensure dependency override is active for this test
        from main import app, get_current_user
        
        def mock_get_current_user():
            return {
                "id": "test@example.com",
                "username": "testuser",
                "email": "test@example.com",
                "disabled": False
            }
        app.dependency_overrides[get_current_user] = mock_get_current_user

        # Mock meal plans
        mock_meal_plans = [
            {
                "id": "meal_plan_123",
                "user_id": "test@example.com",
                "breakfast": ["Oatmeal with berries"],
                "lunch": ["Grilled chicken salad"],
                "dinner": ["Baked salmon"],
                "snacks": ["Apple slices"],
                "dailyCalories": 1800,
                "macronutrients": {"protein": 120, "carbs": 180, "fat": 60}
            }
        ]
        mock_get_meal_plans.return_value = mock_meal_plans

        auth_headers = {"Authorization": "Bearer test_token"}

        # Test getting meal plans
        response = self.client.get("/meal_plans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Meal plans response data: {data}")  # Debug output
        print(f"Response type: {type(data)}")  # Debug output
        
        # Check if response has meal_plans key (like other endpoints)
        if "meal_plans" in data:
            meal_plans = data["meal_plans"] 
            assert len(meal_plans) == 1
            assert meal_plans[0]["id"] == "meal_plan_123"
        else:
            # If it's a direct list
            assert len(data) == 1
            assert data[0]["id"] == "meal_plan_123"
    
    @patch("main.get_current_user")
    @patch("main.get_user_consumption_history")
    @patch("main.get_consumption_analytics")
    def test_consumption_tracking_workflow(self, mock_get_analytics, mock_get_history, mock_get_user):
        """Test complete consumption tracking workflow."""
        mock_get_user.return_value = {
            "username": "testuser",
            "email": "test@example.com",
            "disabled": False
        }
        
        # Mock consumption data
        mock_history = [
            {
                "id": "consumption_123",
                "food_name": "Apple",
                "calories": 95,
                "timestamp": "2024-01-01T12:00:00"
            }
        ]
        mock_get_history.return_value = mock_history
        
        mock_analytics = {
            "total_calories": 1800,
            "average_daily_calories": 600,
            "macronutrient_breakdown": {
                "total_carbs": 225,
                "total_protein": 90,
                "total_fat": 60
            }
        }
        mock_get_analytics.return_value = mock_analytics
        
        auth_headers = {"Authorization": "Bearer test_token"}
        
        # Test consumption history
        history_response = self.client.get("/consumption/history", headers=auth_headers)
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data) == 1
        assert history_data[0]["food_name"] == "Apple"
        
        # Test consumption analytics
        analytics_response = self.client.get("/consumption/analytics", headers=auth_headers)
        assert analytics_response.status_code == 200
        analytics_data = analytics_response.json()
        assert analytics_data["total_calories"] == 1800
    
    @patch("main.get_current_user")
    @patch("main.get_recent_chat_history")
    def test_chat_workflow(self, mock_get_history, mock_get_user):
        """Test complete chat workflow."""
        mock_get_user.return_value = {
            "username": "testuser",
            "email": "test@example.com",
            "disabled": False
        }
        
        mock_get_history.return_value = [
            {
                "id": "chat_123",
                "message": "Hello",
                "is_user": True,
                "timestamp": "2024-01-01T12:00:00"
            }
        ]
        
        auth_headers = {"Authorization": "Bearer test_token"}
        
        # Test getting chat history
        response = self.client.get("/chat/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["message"] == "Hello"
    
    def test_error_handling(self):
        """Test API error handling."""
        # Temporarily clear dependency override to test actual auth
        from main import app, get_current_user
        
        # Store original override if it exists
        original_override = None
        if hasattr(app, 'dependency_overrides') and app.dependency_overrides and get_current_user in app.dependency_overrides:
            original_override = app.dependency_overrides[get_current_user]
            del app.dependency_overrides[get_current_user]
        
        # Test unauthenticated access
        response = self.client.get("/users/me")
        assert response.status_code == 401
        
        # Restore dependency override for other tests
        def mock_get_current_user():
            return {
                "id": "test@example.com",
                "username": "testuser",
                "email": "test@example.com",
                "disabled": False,
                "patient_id": "TEST123",
                "is_admin": True
            }
        if hasattr(app, 'dependency_overrides'):
            app.dependency_overrides[get_current_user] = mock_get_current_user
    
    def test_user_profile_workflow(self):
        """Test complete user profile workflow."""
        # Ensure dependency override is active for this test
        from main import app, get_current_user
        
        def mock_get_current_user():
            return {
                "id": "test@example.com",
                "username": "testuser",
                "email": "test@example.com",
                "disabled": False
            }
        app.dependency_overrides[get_current_user] = mock_get_current_user

        auth_headers = {"Authorization": "Bearer test_token"}

        # Test saving user profile
        with patch("main.user_container") as mock_container, \
             patch("main.get_user_by_email") as mock_get_user_by_email:
            
            # Mock the user lookup
            mock_get_user_by_email.return_value = {
                "id": "test@example.com",
                "email": "test@example.com",
                "username": "testuser",
                "profile": {}
            }
            
            mock_container.replace_item.return_value = {"id": "profile_123"}

            profile_data = {
                "profile": {
                    "name": "Test User",
                    "age": 30,
                    "medical_conditions": ["Type 2 Diabetes"],
                    "height": 180,
                    "weight": 75,
                    "calorieTarget": "1800"
                }
            }

            save_response = self.client.post(
                "/user/profile",
                json=profile_data,
                headers=auth_headers
            )
            print(f"Profile save response: {save_response.status_code}")  # Debug
            print(f"Profile save response body: {save_response.json()}")  # Debug
            assert save_response.status_code == 200


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for database operations."""
    
    @patch("database.user_container")
    @patch("database.interactions_container")
    def test_user_creation_and_retrieval_flow(self, mock_interactions, mock_users):
        """Test complete user creation and retrieval flow."""
        from database import create_user, get_user_by_email
        
        # Mock user creation
        mock_users.create_item.return_value = {"id": "test@example.com"}
        
        # Mock user retrieval
        mock_users.query_items.return_value = [
            {
                "id": "test@example.com",
                "email": "test@example.com",
                "username": "testuser"
            }
        ]
        
        # Test user creation
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "hashed_password": "hashed_password"
        }
        
        created_user = asyncio.run(create_user(user_data))
        assert created_user["id"] == "test@example.com"
        
        # Test user retrieval
        retrieved_user = asyncio.run(get_user_by_email("test@example.com"))
        assert retrieved_user["email"] == "test@example.com"
    
    @patch("database.interactions_container")
    def test_meal_plan_crud_operations(self, mock_container):
        """Test complete meal plan CRUD operations."""
        from database import save_meal_plan, get_user_meal_plans, delete_meal_plan_by_id
        
        # Mock save operation
        mock_container.upsert_item.return_value = {"id": "meal_plan_123"}
        
        # Mock get operations
        mock_container.query_items.return_value = [
            {
                "id": "meal_plan_123",
                "user_id": "test@example.com",
                "breakfast": ["Oatmeal"],
                "lunch": ["Salad"],
                "dinner": ["Salmon"],
                "snacks": ["Apple"],
                "dailyCalories": 1800
            }
        ]
        
        # Mock delete operation
        mock_container.delete_item.return_value = None
        
        # Test save
        meal_plan_data = {
            "breakfast": ["Oatmeal"],
            "lunch": ["Salad"],
            "dinner": ["Salmon"],
            "snacks": ["Apple"],
            "dailyCalories": 1800
        }
        
        saved_plan = asyncio.run(save_meal_plan("test@example.com", meal_plan_data))
        assert saved_plan["id"] == "meal_plan_123"
        
        # Test get
        meal_plans = asyncio.run(get_user_meal_plans("test@example.com"))
        assert len(meal_plans) == 1
        assert meal_plans[0]["id"] == "meal_plan_123"
        
        # Test delete
        deleted = asyncio.run(delete_meal_plan_by_id("meal_plan_123", "test@example.com"))
        assert deleted is True


import asyncio

if __name__ == "__main__":
    pytest.main([__file__])
