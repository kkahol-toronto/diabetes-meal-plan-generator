"""
Comprehensive tests for database.py to maximize code coverage.
Focusing on the 356 missing statements (67% gap) in database operations.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import pytest
from datetime import datetime
import json
import os

# Set up test environment
os.environ.setdefault("USER_INFORMATION_CONTAINER", "test_users")

from database import (
    create_user, get_user_by_email, create_patient, get_patient_by_registration_code,
    get_all_patients, save_meal_plan, get_user_meal_plans, get_meal_plan_by_id,
    save_shopping_list, get_user_shopping_lists, save_chat_message, save_recipes,
    get_user_recipes, get_recent_chat_history, format_chat_history_for_prompt,
    clear_chat_history, get_user_sessions, get_patient_by_id, get_context_history,
    generate_session_id, view_meal_plans, delete_meal_plan_by_id, delete_all_user_meal_plans,
    save_consumption_record, get_user_consumption_history, get_consumption_analytics,
    get_user_meal_history, log_meal_suggestion, get_ai_suggestion, update_consumption_meal_type,
    user_container, interactions_container
)


class TestUserOperations(unittest.TestCase):
    """Test user-related database operations."""
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_container):
        """Test successful user creation."""
        mock_container.create_item.return_value = {"id": "test@example.com"}
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password",
            "disabled": False
        }
        
        result = await create_user(user_data)
        
        assert result["id"] == "test@example.com"
        mock_container.create_item.assert_called_once()
        
        # Verify the user data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "user"
        assert call_args["email"] == "test@example.com"
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_create_user_error(self, mock_container):
        """Test user creation with error."""
        mock_container.create_item.side_effect = Exception("Database error")
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password"
        }
        
        with pytest.raises(Exception) as exc_info:
            await create_user(user_data)
        
        assert "Failed to create user" in str(exc_info.value)
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, mock_container):
        """Test successful user retrieval by email."""
        mock_user = {
            "id": "test@example.com",
            "email": "test@example.com",
            "username": "testuser"
        }
        mock_container.query_items.return_value = [mock_user]
        
        result = await get_user_by_email("test@example.com")
        
        assert result == mock_user
        mock_container.query_items.assert_called_once()
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, mock_container):
        """Test user retrieval when user not found."""
        mock_container.query_items.return_value = []
        
        result = await get_user_by_email("nonexistent@example.com")
        
        assert result is None
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_user_by_email_error(self, mock_container):
        """Test user retrieval with database error."""
        mock_container.query_items.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            await get_user_by_email("test@example.com")
        
        assert "Failed to get user" in str(exc_info.value)


class TestPatientOperations(unittest.TestCase):
    """Test patient-related database operations."""
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_create_patient_success(self, mock_container):
        """Test successful patient creation."""
        mock_container.create_item.return_value = {"id": "TEST123"}
        
        patient_data = {
            "name": "Test Patient",
            "phone": "1234567890",
            "condition": "Type 2 Diabetes",
            "registration_code": "TEST123"
        }
        
        result = await create_patient(patient_data)
        
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
        mock_patient = {
            "id": "TEST123",
            "name": "Test Patient",
            "registration_code": "TEST123"
        }
        mock_container.query_items.return_value = [mock_patient]
        
        result = await get_patient_by_registration_code("TEST123")
        
        assert result == mock_patient
        mock_container.query_items.assert_called_once()
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_patient_by_registration_code_not_found(self, mock_container):
        """Test patient retrieval when patient not found."""
        mock_container.query_items.return_value = []
        
        result = await get_patient_by_registration_code("INVALID")
        
        assert result is None
    
    @patch("database.user_container")
    @pytest.mark.asyncio
    async def test_get_all_patients_success(self, mock_container):
        """Test successful retrieval of all patients."""
        mock_patients = [
            {"id": "TEST123", "name": "Patient 1"},
            {"id": "TEST456", "name": "Patient 2"}
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


class TestMealPlanOperations(unittest.TestCase):
    """Test meal plan database operations."""
    
    @patch("database.interactions_container")
    @patch("database.generate_session_id")
    @pytest.mark.asyncio
    async def test_save_meal_plan_success(self, mock_session_id, mock_container):
        """Test successful meal plan saving."""
        mock_session_id.return_value = "session_123"
        mock_container.create_item.return_value = {"id": "meal_plan_session_123"}
        
        meal_plan_data = {
            "breakfast": ["Oatmeal"],
            "lunch": ["Salad"],
            "dinner": ["Chicken"],
            "snacks": ["Apple"],
            "dailyCalories": 1800
        }
        
        result = await save_meal_plan("test@example.com", meal_plan_data)
        
        assert result["id"] == "meal_plan_session_123"
        mock_container.create_item.assert_called_once()
        
        # Verify the meal plan data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "meal_plan"
        assert call_args["user_id"] == "test@example.com"
        assert call_args["breakfast"] == ["Oatmeal"]
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_meal_plans_success(self, mock_container):
        """Test successful meal plans retrieval."""
        mock_meal_plans = [
            {
                "id": "meal_plan_1",
                "user_id": "test@example.com",
                "breakfast": ["Oatmeal"]
            }
        ]
        mock_container.query_items.return_value = mock_meal_plans
        
        result = await get_user_meal_plans("test@example.com")
        
        assert result == mock_meal_plans
        mock_container.query_items.assert_called_once()
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_meal_plans_with_limit(self, mock_container):
        """Test meal plans retrieval with limit."""
        mock_meal_plans = [{"id": "meal_plan_1"}]
        mock_container.query_items.return_value = mock_meal_plans
        
        result = await get_user_meal_plans("test@example.com", limit=5)
        
        assert result == mock_meal_plans
        mock_container.query_items.assert_called_once()
        
        # Check that TOP clause is used in query
        call_args = mock_container.query_items.call_args
        query = call_args[1]["query"]
        assert "TOP 5" in query
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_meal_plan_by_id_success(self, mock_container):
        """Test successful meal plan retrieval by ID."""
        mock_meal_plan = {
            "id": "meal_plan_123",
            "breakfast": ["Oatmeal"]
        }
        mock_container.query_items.return_value = [mock_meal_plan]
        
        result = await get_meal_plan_by_id("meal_plan_123")
        
        assert result == mock_meal_plan
        mock_container.query_items.assert_called_once()
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_delete_meal_plan_by_id_success(self, mock_container):
        """Test successful meal plan deletion."""
        mock_container.delete_item.return_value = True
        
        result = await delete_meal_plan_by_id("test@example.com", "meal_plan_123")
        
        assert result is True
        mock_container.delete_item.assert_called_once()
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_delete_all_user_meal_plans_success(self, mock_container):
        """Test successful deletion of all user meal plans."""
        mock_meal_plans = [
            {"id": "meal_plan_1", "user_id": "test@example.com"},
            {"id": "meal_plan_2", "user_id": "test@example.com"}
        ]
        mock_container.query_items.return_value = mock_meal_plans
        
        result = await delete_all_user_meal_plans("test@example.com")
        
        assert result is True
        # Verify delete was called for each meal plan
        assert mock_container.delete_item.call_count == 2
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_view_meal_plans_success(self, mock_container):
        """Test successful meal plans view."""
        mock_meal_plans = [
            {
                "id": "meal_plan_1",
                "created_at": "2023-12-01T10:00:00Z",
                "dailyCalories": 1800
            }
        ]
        mock_container.query_items.return_value = mock_meal_plans
        
        result = await view_meal_plans("test@example.com")
        
        assert result == mock_meal_plans
        mock_container.query_items.assert_called_once()


class TestChatOperations(unittest.TestCase):
    """Test chat-related database operations."""
    
    @patch("database.interactions_container")
    @patch("database.generate_session_id")
    @pytest.mark.asyncio
    async def test_save_chat_message_success(self, mock_session_id, mock_container):
        """Test successful chat message saving."""
        mock_session_id.return_value = "session_123"
        mock_container.create_item.return_value = {"id": "message_123"}
        
        result = await save_chat_message(
            "test@example.com",
            "Hello, I need help",
            is_user=True,
            session_id="session_123"
        )
        
        assert result["id"] == "message_123"
        mock_container.create_item.assert_called_once()
        
        # Verify the message data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "chat_message"
        assert call_args["user_id"] == "test@example.com"
        assert call_args["message"] == "Hello, I need help"
        assert call_args["is_user"] is True
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_recent_chat_history_success(self, mock_container):
        """Test successful chat history retrieval."""
        mock_messages = [
            {
                "id": "message_1",
                "message": "Hello",
                "is_user": True,
                "timestamp": "2023-12-01T10:00:00Z"
            },
            {
                "id": "message_2",
                "message": "Hi there!",
                "is_user": False,
                "timestamp": "2023-12-01T10:01:00Z"
            }
        ]
        mock_container.query_items.return_value = mock_messages
        
        result = await get_recent_chat_history("test@example.com")
        
        assert len(result) == 2
        assert result[0] == ("Hello", True)
        assert result[1] == ("Hi there!", False)
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_format_chat_history_for_prompt(self, mock_container):
        """Test chat history formatting for AI prompts."""
        mock_messages = [
            ("Hello", True),
            ("Hi there!", False),
            ("How are you?", True)
        ]
        
        result = format_chat_history_for_prompt(mock_messages)
        
        expected = "User: Hello\nAssistant: Hi there!\nUser: How are you?"
        assert result == expected
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_clear_chat_history_success(self, mock_container):
        """Test successful chat history clearing."""
        mock_messages = [
            {"id": "message_1", "user_id": "test@example.com"},
            {"id": "message_2", "user_id": "test@example.com"}
        ]
        mock_container.query_items.return_value = mock_messages
        
        result = await clear_chat_history("test@example.com")
        
        assert result is True
        # Verify delete was called for each message
        assert mock_container.delete_item.call_count == 2
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_sessions_success(self, mock_container):
        """Test successful user sessions retrieval."""
        mock_sessions = [
            {
                "session_id": "session_123",
                "created_at": "2023-12-01T10:00:00Z",
                "last_message": "Hello"
            }
        ]
        mock_container.query_items.return_value = mock_sessions
        
        result = await get_user_sessions("test@example.com")
        
        assert result == mock_sessions
        mock_container.query_items.assert_called_once()


class TestShoppingListOperations(unittest.TestCase):
    """Test shopping list database operations."""
    
    @patch("database.interactions_container")
    @patch("database.generate_session_id")
    @pytest.mark.asyncio
    async def test_save_shopping_list_success(self, mock_session_id, mock_container):
        """Test successful shopping list saving."""
        mock_session_id.return_value = "session_123"
        mock_container.create_item.return_value = {"id": "shopping_list_session_123"}
        
        shopping_list = {
            "items": ["Apples", "Chicken", "Rice"]
        }
        
        result = await save_shopping_list("test@example.com", shopping_list)
        
        assert result["id"] == "shopping_list_session_123"
        mock_container.create_item.assert_called_once()
        
        # Verify the shopping list data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "shopping_list"
        assert call_args["user_id"] == "test@example.com"
        assert call_args["items"] == ["Apples", "Chicken", "Rice"]
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_shopping_lists_success(self, mock_container):
        """Test successful shopping lists retrieval."""
        mock_lists = [
            {
                "id": "shopping_list_1",
                "user_id": "test@example.com",
                "items": ["Apples", "Chicken"]
            }
        ]
        mock_container.query_items.return_value = mock_lists
        
        result = await get_user_shopping_lists("test@example.com")
        
        assert result == mock_lists
        mock_container.query_items.assert_called_once()


class TestRecipeOperations(unittest.TestCase):
    """Test recipe database operations."""
    
    @patch("database.interactions_container")
    @patch("database.generate_session_id")
    @pytest.mark.asyncio
    async def test_save_recipes_success(self, mock_session_id, mock_container):
        """Test successful recipes saving."""
        mock_session_id.return_value = "session_123"
        mock_container.create_item.return_value = {"id": "recipes_session_123"}
        
        recipes = [
            {
                "name": "Healthy Salad",
                "ingredients": ["Lettuce", "Tomatoes"],
                "instructions": ["Mix ingredients"]
            }
        ]
        
        result = await save_recipes("test@example.com", recipes)
        
        assert result["id"] == "recipes_session_123"
        mock_container.create_item.assert_called_once()
        
        # Verify the recipes data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "recipes"
        assert call_args["user_id"] == "test@example.com"
        assert call_args["recipes"] == recipes
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_recipes_success(self, mock_container):
        """Test successful recipes retrieval."""
        mock_recipes = [
            {
                "id": "recipes_1",
                "user_id": "test@example.com",
                "recipes": [{"name": "Healthy Salad"}]
            }
        ]
        mock_container.query_items.return_value = mock_recipes
        
        result = await get_user_recipes("test@example.com")
        
        assert result == mock_recipes
        mock_container.query_items.assert_called_once()


class TestConsumptionOperations(unittest.TestCase):
    """Test consumption tracking database operations."""
    
    @patch("database.interactions_container")
    @patch("database.generate_session_id")
    @pytest.mark.asyncio
    async def test_save_consumption_record_success(self, mock_session_id, mock_container):
        """Test successful consumption record saving."""
        mock_session_id.return_value = "session_123"
        mock_container.create_item.return_value = {"id": "consumption_session_123"}
        
        consumption_data = {
            "food_name": "Apple",
            "quantity": "1 medium",
            "calories": 80,
            "meal_type": "snack"
        }
        
        result = await save_consumption_record("test@example.com", consumption_data)
        
        assert result["id"] == "consumption_session_123"
        mock_container.create_item.assert_called_once()
        
        # Verify the consumption data is correctly formatted
        call_args = mock_container.create_item.call_args[1]["body"]
        assert call_args["type"] == "consumption_record"
        assert call_args["user_id"] == "test@example.com"
        assert call_args["food_name"] == "Apple"
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_consumption_history_success(self, mock_container):
        """Test successful consumption history retrieval."""
        mock_records = [
            {
                "id": "consumption_1",
                "user_id": "test@example.com",
                "food_name": "Apple",
                "calories": 80
            }
        ]
        mock_container.query_items.return_value = mock_records
        
        result = await get_user_consumption_history("test@example.com")
        
        assert result == mock_records
        mock_container.query_items.assert_called_once()
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_consumption_analytics_success(self, mock_container):
        """Test successful consumption analytics retrieval."""
        mock_records = [
            {
                "nutritional_info": {"calories": 80, "protein": 0, "carbs": 21, "fat": 0},
                "timestamp": "2023-12-01T10:00:00Z"
            },
            {
                "nutritional_info": {"calories": 300, "protein": 25, "carbs": 30, "fat": 10},
                "timestamp": "2023-12-01T12:00:00Z"
            }
        ]
        mock_container.query_items.return_value = mock_records
        
        result = await get_consumption_analytics("test@example.com")
        
        assert "total_calories" in result
        assert "average_daily_calories" in result
        assert "total_protein" in result
        assert result["total_calories"] == 380
        assert result["total_protein"] == 25
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_update_consumption_meal_type_success(self, mock_container):
        """Test successful consumption meal type update."""
        mock_container.read_item.return_value = {
            "id": "consumption_123",
            "meal_type": "breakfast"
        }
        mock_container.upsert_item.return_value = {"id": "consumption_123"}
        
        result = await update_consumption_meal_type("consumption_123", "lunch")
        
        assert result["id"] == "consumption_123"
        mock_container.read_item.assert_called_once()
        mock_container.upsert_item.assert_called_once()


class TestUtilityFunctions(unittest.TestCase):
    """Test utility database functions."""
    
    def test_generate_session_id(self):
        """Test session ID generation."""
        session_id = generate_session_id()
        
        assert isinstance(session_id, str)
        assert len(session_id) > 10  # Should be a reasonable length
        
        # Generate multiple IDs to ensure they're unique
        session_id_2 = generate_session_id()
        assert session_id != session_id_2
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_context_history_success(self, mock_container):
        """Test successful context history retrieval."""
        mock_records = [
            {
                "id": "context_1",
                "user_id": "test@example.com",
                "context": "Meal planning"
            }
        ]
        mock_container.query_items.return_value = mock_records
        
        result = await get_context_history("test@example.com")
        
        assert result == mock_records
        mock_container.query_items.assert_called_once()
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_log_meal_suggestion_success(self, mock_container):
        """Test successful meal suggestion logging."""
        mock_container.create_item.return_value = {"id": "suggestion_123"}
        
        suggestion_data = {
            "suggestion": "Try a balanced breakfast",
            "user_query": "What should I eat for breakfast?",
            "context": "User has diabetes"
        }
        
        result = await log_meal_suggestion("test@example.com", suggestion_data)
        
        assert result["id"] == "suggestion_123"
        mock_container.create_item.assert_called_once()
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_ai_suggestion_success(self, mock_container):
        """Test successful AI suggestion retrieval."""
        mock_suggestions = [
            {
                "id": "suggestion_1",
                "suggestion": "Try oatmeal for breakfast",
                "timestamp": "2023-12-01T08:00:00Z"
            }
        ]
        mock_container.query_items.return_value = mock_suggestions
        
        result = await get_ai_suggestion("test@example.com")
        
        assert result == mock_suggestions
        mock_container.query_items.assert_called_once()
    
    @patch("database.interactions_container")
    @pytest.mark.asyncio
    async def test_get_user_meal_history_success(self, mock_container):
        """Test successful user meal history retrieval."""
        mock_history = [
            {
                "id": "meal_1",
                "meal_name": "Breakfast Bowl",
                "timestamp": "2023-12-01T08:00:00Z"
            }
        ]
        mock_container.query_items.return_value = mock_history
        
        result = await get_user_meal_history("test@example.com")
        
        assert result == mock_history
        mock_container.query_items.assert_called_once()


if __name__ == "__main__":
    unittest.main() 