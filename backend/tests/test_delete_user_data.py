import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
import sys
import os
import json

# Add the backend directory to the path to import from the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

client = TestClient(app)

class TestDeleteUserData:
    
    @patch("main.get_current_user")
    @patch("main.delete_all_user_meal_plans")
    @patch("main.clear_chat_history")
    @patch("main.interactions_container")
    @patch("main.user_container")
    def test_delete_user_data_success(self, mock_user_container, mock_interactions_container, 
                                     mock_clear_chat_history, mock_delete_meal_plans, mock_get_current_user):
        """Test successful deletion of all user data"""
        
        # Mock user response
        test_user = {
            "id": "test@example.com",
            "email": "test@example.com",
            "username": "test@example.com"
        }
        mock_get_current_user.return_value = test_user
        
        # Mock query responses for different data types
        mock_query_results = [{"id": "item1", "user_id": "test@example.com"}, 
                             {"id": "item2", "user_id": "test@example.com"}]
        
        # Setup mock for interactions_container query_items
        mock_interactions_container.query_items.return_value = mock_query_results
        
        # Call the endpoint
        response = client.delete("/api/users/me/data")
        
        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["detail"] == "Account and all data deleted."
        
        # Verify all necessary methods were called
        mock_delete_meal_plans.assert_called_once_with("test@example.com")
        mock_clear_chat_history.assert_called_once_with("test@example.com")
        assert mock_interactions_container.query_items.call_count == 3  # Called for consumption, shopping, recipes
        assert mock_interactions_container.delete_item.call_count == 6  # 2 items for each of 3 types
        mock_user_container.delete_item.assert_called_once_with(item="test@example.com", partition_key="test@example.com")
    
    @patch("main.get_current_user")
    def test_delete_user_data_unauthorized(self, mock_get_current_user):
        """Test that unauthorized access is rejected"""
        
        # Mock unauthorized scenario
        mock_get_current_user.side_effect = Exception("Not authenticated")
        
        # Call the endpoint
        response = client.delete("/api/users/me/data")
        
        # Verify endpoint returns unauthorized error
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch("main.get_current_user")
    @patch("main.delete_all_user_meal_plans")
    def test_delete_user_data_error(self, mock_delete_meal_plans, mock_get_current_user):
        """Test error handling during deletion process"""
        
        # Mock user response
        test_user = {
            "id": "test@example.com",
            "email": "test@example.com",
            "username": "test@example.com"
        }
        mock_get_current_user.return_value = test_user
        
        # Mock an error during deletion process
        mock_delete_meal_plans.side_effect = Exception("Database error")
        
        # Call the endpoint
        response = client.delete("/api/users/me/data")
        
        # Verify error is handled correctly
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to delete account" in response.json()["detail"] 