"""
Unit tests for database module.
"""
import pytest
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from azure.cosmos.exceptions import CosmosResourceNotFoundError

# Add the backend directory to the Python path and set environment variables
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Mock environment variables before importing
os.environ.setdefault("AZURE_OPENAI_KEY", "test_key")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
os.environ.setdefault("COSMO_DB_CONNECTION_STRING", "test_connection")
os.environ.setdefault("INTERACTIONS_CONTAINER", "test_interactions")
os.environ.setdefault("USER_INFORMATION_CONTAINER", "test_users")

from database import (
    create_user,
    get_user_by_email,
    create_patient,
    get_patient_by_registration_code,
    get_all_patients,
    get_patient_by_id,
    save_meal_plan,
    get_user_meal_plans,
    get_meal_plan_by_id,
    delete_meal_plan_by_id,
    delete_all_user_meal_plans,
    save_shopping_list,
    get_user_shopping_lists,
    save_chat_message,
    get_recent_chat_history,
    format_chat_history_for_prompt,
    clear_chat_history,
    get_user_sessions,
    save_recipes,
    get_user_recipes,
    count_tokens,
    get_context_history,
    view_meal_plans,
    save_consumption_record,
    get_user_consumption_history,
    get_consumption_analytics,
    get_user_meal_history,
    log_meal_suggestion,
    get_ai_suggestion,
    update_consumption_meal_type,
    generate_session_id,
)


class TestDatabaseUserOperations:
    """Test user-related database operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "hashed_password": "hashed_password",
            "disabled": False,
        }
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_container):
        """Test successful user creation."""
        mock_container.create_item.return_value = {"id": "test@example.com"}
        
        result = await create_user(self.mock_user_data)
        
        assert result["id"] == "test@example.com"
        mock_container.create_item.assert_called_once()
        
        # Verify the user data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "user"
        assert call_args["id"] == "test@example.com"
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_create_user_failure(self, mock_container):
        """Test user creation failure."""
        mock_container.create_item.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            await create_user(self.mock_user_data)
        
        assert "Failed to create user" in str(exc_info.value)
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, mock_container):
        """Test successful user retrieval by email."""
        mock_user = {"id": "test@example.com", "username": "testuser"}
        mock_container.query_items.return_value = [mock_user]
        
        result = await get_user_by_email("test@example.com")
        
        assert result == mock_user
        mock_container.query_items.assert_called_once()
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, mock_container):
        """Test user retrieval when user doesn't exist."""
        mock_container.query_items.return_value = []
        
        result = await get_user_by_email("nonexistent@example.com")
        
        assert result is None
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_user_by_email_failure(self, mock_container):
        """Test user retrieval failure."""
        mock_container.query_items.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            await get_user_by_email("test@example.com")
        
        assert "Failed to get user" in str(exc_info.value)


class TestDatabasePatientOperations:
    """Test patient-related database operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_patient_data = {
            "name": "Test Patient",
            "phone": "1234567890",
            "condition": "Type 2 Diabetes",
            "registration_code": "TEST123",
        }
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_create_patient_success(self, mock_container):
        """Test successful patient creation."""
        mock_container.create_item.return_value = {"id": "TEST123"}
        
        result = await create_patient(self.mock_patient_data)
        
        assert result["id"] == "TEST123"
        mock_container.create_item.assert_called_once()
        
        # Verify the patient data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "patient"
        assert call_args["id"] == "TEST123"
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_patient_by_registration_code_success(self, mock_container):
        """Test successful patient retrieval by registration code."""
        mock_patient = {"id": "TEST123", "name": "Test Patient"}
        mock_container.query_items.return_value = [mock_patient]
        
        result = await get_patient_by_registration_code("TEST123")
        
        assert result == mock_patient
        mock_container.query_items.assert_called_once()
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_all_patients_success(self, mock_container):
        """Test successful retrieval of all patients."""
        mock_patients = [
            {"id": "TEST123", "name": "Test Patient 1"},
            {"id": "TEST456", "name": "Test Patient 2"},
        ]
        mock_container.query_items.return_value = mock_patients
        
        result = await get_all_patients()
        
        assert result == mock_patients
        mock_container.query_items.assert_called_once()
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_patient_by_id_success(self, mock_container):
        """Test successful patient retrieval by ID."""
        mock_patient = {"id": "TEST123", "name": "Test Patient"}
        mock_container.query_items.return_value = [mock_patient]
        
        result = await get_patient_by_id("TEST123")
        
        assert result == mock_patient
        mock_container.query_items.assert_called_once()


class TestDatabaseMealPlanOperations:
    """Test meal plan-related database operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_meal_plan_data = {
            "id": "meal_plan_123",
            "user_id": "test@example.com",
            "breakfast": ["Oatmeal", "Berries"],
            "lunch": ["Salad", "Chicken"],
            "dinner": ["Salmon", "Vegetables"],
            "snacks": ["Apple", "Nuts"],
            "dailyCalories": 1800,
            "macronutrients": {"protein": 120, "carbs": 180, "fat": 60},
        }
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_save_meal_plan_success(self, mock_container):
        """Test successful meal plan saving."""
        mock_container.upsert_item.return_value = {"id": "meal_plan_123"}
        
        result = await save_meal_plan("test@example.com", self.mock_meal_plan_data)
        
        assert result["id"] == "meal_plan_123"
        mock_container.upsert_item.assert_called_once()
        
        # Verify the meal plan data is correctly formatted
        call_args = mock_container.upsert_item.call_args[1]["body"]
        assert call_args["type"] == "meal_plan"
        assert call_args["user_id"] == "test@example.com"
        assert "_partitionKey" in call_args
        assert "created_at" in call_args
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_meal_plans_success(self, mock_container):
        """Test successful retrieval of user meal plans."""
        mock_meal_plans = [
            {
                "id": "meal_plan_123",
                "user_id": "test@example.com",
                "breakfast": ["Oatmeal"],
                "lunch": ["Salad"],
                "dinner": ["Salmon"],
                "snacks": ["Apple"],
                "dailyCalories": 1800,
                "macronutrients": {"protein": 120, "carbs": 180, "fat": 60},
            }
        ]
        mock_container.query_items.return_value = mock_meal_plans
        
        result = await get_user_meal_plans("test@example.com")
        
        assert result == mock_meal_plans
        mock_container.query_items.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
