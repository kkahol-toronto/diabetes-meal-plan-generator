"""
Comprehensive tests for database operations in database.py
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from azure.cosmos.exceptions import CosmosResourceNotFoundError

# Import database functions to test
from database import (
    generate_session_id, create_user, get_user_by_email, create_patient,
    get_patient_by_registration_code, get_all_patients, get_patient_by_id,
    save_meal_plan, get_user_meal_plans, get_meal_plan_by_id,
    save_shopping_list, get_user_shopping_lists, save_chat_message,
    save_recipes, get_user_recipes, get_recent_chat_history,
    format_chat_history_for_prompt, clear_chat_history, get_user_sessions,
    save_consumption_record, get_user_consumption_history,
    get_consumption_analytics, get_user_meal_history, log_meal_suggestion,
    get_ai_suggestion, update_consumption_meal_type, view_meal_plans,
    delete_meal_plan_by_id, delete_all_user_meal_plans, get_context_history
)


class TestSessionGeneration:
    """Test session ID generation."""
    
    def test_generate_session_id(self):
        """Test session ID generation."""
        session_id = generate_session_id()
        
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID4 format
        assert session_id.count('-') == 4  # UUID4 has 4 hyphens
        
        # Test uniqueness
        session_ids = [generate_session_id() for _ in range(10)]
        assert len(set(session_ids)) == len(session_ids)  # All unique


class TestUserOperations:
    """Test user-related database operations."""
    
    @pytest.fixture
    def mock_user_container(self):
        """Mock user container for testing."""
        container = Mock()
        container.create_item = Mock()
        container.query_items = Mock()
        container.read_item = Mock()
        container.upsert_item = Mock()
        container.delete_item = Mock()
        return container
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_user_container):
        """Test successful user creation."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password_123"
        }
        
        expected_result = {"id": "test@example.com", "type": "user", **user_data}
        mock_user_container.create_item.return_value = expected_result
        
        with patch('database.user_container', mock_user_container):
            result = await create_user(user_data)
            
            assert result == expected_result
            mock_user_container.create_item.assert_called_once()
            call_args = mock_user_container.create_item.call_args[1]['body']
            assert call_args["type"] == "user"
            assert call_args["id"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_create_user_failure(self, mock_user_container):
        """Test user creation failure."""
        user_data = {"email": "test@example.com"}
        mock_user_container.create_item.side_effect = Exception("Database error")
        
        with patch('database.user_container', mock_user_container):
            with pytest.raises(Exception) as exc_info:
                await create_user(user_data)
            
            assert "Failed to create user" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, mock_user_container):
        """Test getting user by email when user exists."""
        email = "test@example.com"
        expected_user = {
            "id": email,
            "email": email,
            "username": "testuser",
            "type": "user"
        }
        
        mock_user_container.query_items.return_value = [expected_user]
        
        with patch('database.user_container', mock_user_container):
            result = await get_user_by_email(email)
            
            assert result == expected_user
            mock_user_container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, mock_user_container):
        """Test getting user by email when user doesn't exist."""
        mock_user_container.query_items.return_value = []
        
        with patch('database.user_container', mock_user_container):
            result = await get_user_by_email("nonexistent@example.com")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_error(self, mock_user_container):
        """Test getting user by email with database error."""
        mock_user_container.query_items.side_effect = Exception("Database error")
        
        with patch('database.user_container', mock_user_container):
            with pytest.raises(Exception) as exc_info:
                await get_user_by_email("test@example.com")
            
            assert "Failed to get user" in str(exc_info.value)


class TestPatientOperations:
    """Test patient-related database operations."""
    
    @pytest.fixture
    def sample_patient_data(self):
        """Sample patient data for testing."""
        return {
            "name": "John Doe",
            "phone": "1234567890",
            "condition": "Type 2 Diabetes",
            "registration_code": "ABC123"
        }
    
    @pytest.mark.asyncio
    async def test_create_patient_success(self, mock_cosmos_client, sample_patient_data):
        """Test successful patient creation."""
        container = mock_cosmos_client['container']
        expected_result = {"id": "ABC123", "type": "patient", **sample_patient_data}
        container.create_item.return_value = expected_result
        
        with patch('database.user_container', container):
            result = await create_patient(sample_patient_data)
            
            assert result == expected_result
            container.create_item.assert_called_once()
            call_args = container.create_item.call_args[1]['body']
            assert call_args["type"] == "patient"
            assert call_args["id"] == "ABC123"
    
    @pytest.mark.asyncio
    async def test_get_patient_by_registration_code_found(self, mock_cosmos_client):
        """Test getting patient by registration code when patient exists."""
        container = mock_cosmos_client['container']
        expected_patient = {
            "id": "ABC123",
            "registration_code": "ABC123",
            "name": "John Doe",
            "type": "patient"
        }
        container.query_items.return_value = [expected_patient]
        
        with patch('database.user_container', container):
            result = await get_patient_by_registration_code("ABC123")
            
            assert result == expected_patient
    
    @pytest.mark.asyncio
    async def test_get_all_patients(self, mock_cosmos_client):
        """Test getting all patients."""
        container = mock_cosmos_client['container']
        expected_patients = [
            {"id": "ABC123", "name": "John Doe", "type": "patient"},
            {"id": "DEF456", "name": "Jane Smith", "type": "patient"}
        ]
        container.query_items.return_value = expected_patients
        
        with patch('database.user_container', container):
            result = await get_all_patients()
            
            assert result == expected_patients
            container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_patient_by_id(self, mock_cosmos_client):
        """Test getting patient by ID."""
        container = mock_cosmos_client['container']
        expected_patient = {"id": "ABC123", "name": "John Doe", "type": "patient"}
        container.query_items.return_value = [expected_patient]
        
        with patch('database.user_container', container):
            result = await get_patient_by_id("ABC123")
            
            assert result == expected_patient


class TestMealPlanOperations:
    """Test meal plan database operations."""
    
    @pytest.fixture
    def sample_meal_plan(self):
        """Sample meal plan data for testing."""
        return {
            "user_email": "test@example.com",
            "days": 7,
            "created_date": "2024-01-15",
            "meal_plan": {
                "day_1": {
                    "breakfast": "Oatmeal with berries",
                    "lunch": "Quinoa salad",
                    "dinner": "Grilled vegetables"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_save_meal_plan_success(self, mock_cosmos_client, sample_meal_plan):
        """Test successful meal plan saving."""
        container = mock_cosmos_client['container']
        expected_result = {"id": "meal_plan_1", **sample_meal_plan}
        container.create_item.return_value = expected_result
        
        with patch('database.interactions_container', container):
            with patch('services.cache_service.invalidate_meal_plan_cache'):
                result = await save_meal_plan("test@example.com", sample_meal_plan)
                
                assert result == expected_result
                container.create_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_meal_plans(self, mock_cosmos_client):
        """Test getting user meal plans."""
        container = mock_cosmos_client['container']
        expected_plans = [
            {"id": "plan1", "user_email": "test@example.com", "type": "meal_plan"},
            {"id": "plan2", "user_email": "test@example.com", "type": "meal_plan"}
        ]
        container.query_items.return_value = expected_plans
        
        with patch('database.interactions_container', container):
            result = await get_user_meal_plans("test@example.com")
            
            assert result == expected_plans
            container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_meal_plan_by_id_found(self, mock_cosmos_client):
        """Test getting meal plan by ID when it exists."""
        container = mock_cosmos_client['container']
        expected_plan = {"id": "plan1", "user_email": "test@example.com"}
        container.read_item.return_value = expected_plan
        
        with patch('database.interactions_container', container):
            result = await get_meal_plan_by_id("plan1", "test@example.com")
            
            assert result == expected_plan
            container.read_item.assert_called_once_with(
                item="plan1", partition_key="test@example.com"
            )
    
    @pytest.mark.asyncio
    async def test_get_meal_plan_by_id_not_found(self, mock_cosmos_client):
        """Test getting meal plan by ID when it doesn't exist."""
        container = mock_cosmos_client['container']
        container.read_item.side_effect = CosmosResourceNotFoundError(message="Not found")
        
        with patch('database.interactions_container', container):
            result = await get_meal_plan_by_id("nonexistent", "test@example.com")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_meal_plan_by_id(self, mock_cosmos_client):
        """Test deleting meal plan by ID."""
        container = mock_cosmos_client['container']
        container.delete_item.return_value = {"deleted": True}
        
        with patch('database.interactions_container', container):
            with patch('services.cache_service.invalidate_meal_plan_cache'):
                result = await delete_meal_plan_by_id("plan1", "test@example.com")
                
                assert result["deleted"] is True
                container.delete_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_all_user_meal_plans(self, mock_cosmos_client):
        """Test deleting all meal plans for a user."""
        container = mock_cosmos_client['container']
        existing_plans = [
            {"id": "plan1", "user_email": "test@example.com"},
            {"id": "plan2", "user_email": "test@example.com"}
        ]
        container.query_items.return_value = existing_plans
        container.delete_item.return_value = {"deleted": True}
        
        with patch('database.interactions_container', container):
            with patch('services.cache_service.invalidate_all_meal_plan_caches'):
                result = await delete_all_user_meal_plans("test@example.com")
                
                assert result["deleted_count"] == 2
                assert container.delete_item.call_count == 2


class TestConsumptionOperations:
    """Test consumption tracking database operations."""
    
    @pytest.fixture
    def sample_consumption_record(self):
        """Sample consumption record for testing."""
        return {
            "user_email": "test@example.com",
            "food_name": "Apple",
            "meal_type": "snack",
            "calories": 80,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_save_consumption_record(self, mock_cosmos_client, sample_consumption_record):
        """Test saving consumption record."""
        container = mock_cosmos_client['container']
        expected_result = {"id": "consumption_1", **sample_consumption_record}
        container.create_item.return_value = expected_result
        
        with patch('database.interactions_container', container):
            result = await save_consumption_record(sample_consumption_record)
            
            assert result == expected_result
            container.create_item.assert_called_once()
            call_args = container.create_item.call_args[1]['body']
            assert call_args["type"] == "consumption"
    
    @pytest.mark.asyncio
    async def test_get_user_consumption_history(self, mock_cosmos_client):
        """Test getting user consumption history."""
        container = mock_cosmos_client['container']
        expected_records = [
            {"id": "c1", "user_email": "test@example.com", "food_name": "Apple"},
            {"id": "c2", "user_email": "test@example.com", "food_name": "Banana"}
        ]
        container.query_items.return_value = expected_records
        
        with patch('database.interactions_container', container):
            result = await get_user_consumption_history("test@example.com", limit=50)
            
            assert result == expected_records
            container.query_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_consumption_analytics(self, mock_cosmos_client):
        """Test getting consumption analytics."""
        container = mock_cosmos_client['container']
        mock_records = [
            {
                "calories": 300, "protein": 15, "carbs": 45, "fat": 10,
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            {
                "calories": 400, "protein": 20, "carbs": 50, "fat": 15,
                "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat()
            }
        ]
        container.query_items.return_value = mock_records
        
        with patch('database.interactions_container', container):
            result = await get_consumption_analytics("test@example.com", days=7)
            
            assert "total_calories" in result
            assert "avg_calories" in result
            assert "total_protein" in result
            assert result["total_calories"] == 700
            assert result["avg_calories"] == 350
    
    @pytest.mark.asyncio
    async def test_update_consumption_meal_type(self, mock_cosmos_client):
        """Test updating consumption meal type."""
        container = mock_cosmos_client['container']
        existing_record = {
            "id": "consumption_1",
            "user_email": "test@example.com",
            "meal_type": "snack"
        }
        container.read_item.return_value = existing_record
        container.upsert_item.return_value = {**existing_record, "meal_type": "breakfast"}
        
        with patch('database.interactions_container', container):
            result = await update_consumption_meal_type(
                "consumption_1", "test@example.com", "breakfast"
            )
            
            assert result["meal_type"] == "breakfast"
            container.upsert_item.assert_called_once()


class TestChatOperations:
    """Test chat-related database operations."""
    
    @pytest.mark.asyncio
    async def test_save_chat_message(self, mock_cosmos_client):
        """Test saving chat message."""
        container = mock_cosmos_client['container']
        message_data = {
            "user_email": "test@example.com",
            "message": "Hello",
            "session_id": "session_123"
        }
        expected_result = {"id": "chat_1", **message_data}
        container.create_item.return_value = expected_result
        
        with patch('database.interactions_container', container):
            result = await save_chat_message(message_data)
            
            assert result == expected_result
            container.create_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_chat_history(self, mock_cosmos_client):
        """Test getting recent chat history."""
        container = mock_cosmos_client['container']
        expected_messages = [
            {
                "id": "chat_1",
                "user_email": "test@example.com",
                "message": "Hello",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        container.query_items.return_value = expected_messages
        
        with patch('database.interactions_container', container):
            result = await get_recent_chat_history("test@example.com", limit=10)
            
            assert result == expected_messages
    
    def test_format_chat_history_for_prompt(self):
        """Test formatting chat history for AI prompt."""
        chat_history = [
            {"message": "Hello", "role": "user", "timestamp": "2024-01-01T12:00:00"},
            {"message": "Hi there!", "role": "assistant", "timestamp": "2024-01-01T12:01:00"}
        ]
        
        result = format_chat_history_for_prompt(chat_history)
        
        assert isinstance(result, str)
        assert "Hello" in result
        assert "Hi there!" in result
    
    @pytest.mark.asyncio
    async def test_clear_chat_history(self, mock_cosmos_client):
        """Test clearing chat history."""
        container = mock_cosmos_client['container']
        existing_messages = [
            {"id": "chat_1", "user_email": "test@example.com"},
            {"id": "chat_2", "user_email": "test@example.com"}
        ]
        container.query_items.return_value = existing_messages
        container.delete_item.return_value = {"deleted": True}
        
        with patch('database.interactions_container', container):
            result = await clear_chat_history("test@example.com")
            
            assert result["deleted_count"] == 2
            assert container.delete_item.call_count == 2


class TestShoppingListOperations:
    """Test shopping list database operations."""
    
    @pytest.mark.asyncio
    async def test_save_shopping_list(self, mock_cosmos_client):
        """Test saving shopping list."""
        container = mock_cosmos_client['container']
        shopping_list_data = {
            "user_email": "test@example.com",
            "items": ["Apples", "Quinoa", "Spinach"]
        }
        expected_result = {"id": "shopping_1", **shopping_list_data}
        container.create_item.return_value = expected_result
        
        with patch('database.interactions_container', container):
            result = await save_shopping_list(shopping_list_data)
            
            assert result == expected_result
            container.create_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_shopping_lists(self, mock_cosmos_client):
        """Test getting user shopping lists."""
        container = mock_cosmos_client['container']
        expected_lists = [
            {"id": "list1", "user_email": "test@example.com", "items": ["Apple"]},
            {"id": "list2", "user_email": "test@example.com", "items": ["Banana"]}
        ]
        container.query_items.return_value = expected_lists
        
        with patch('database.interactions_container', container):
            result = await get_user_shopping_lists("test@example.com")
            
            assert result == expected_lists


class TestRecipeOperations:
    """Test recipe database operations."""
    
    @pytest.mark.asyncio
    async def test_save_recipes(self, mock_cosmos_client):
        """Test saving recipes."""
        container = mock_cosmos_client['container']
        recipes_data = {
            "user_email": "test@example.com",
            "recipes": [
                {"name": "Oatmeal", "ingredients": ["oats", "milk"]},
                {"name": "Salad", "ingredients": ["lettuce", "tomato"]}
            ]
        }
        expected_result = {"id": "recipes_1", **recipes_data}
        container.create_item.return_value = expected_result
        
        with patch('database.interactions_container', container):
            result = await save_recipes(recipes_data)
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_user_recipes(self, mock_cosmos_client):
        """Test getting user recipes."""
        container = mock_cosmos_client['container']
        expected_recipes = [
            {"id": "recipe1", "user_email": "test@example.com", "name": "Oatmeal"}
        ]
        container.query_items.return_value = expected_recipes
        
        with patch('database.interactions_container', container):
            result = await get_user_recipes("test@example.com")
            
            assert result == expected_recipes


class TestUtilityOperations:
    """Test utility database operations."""
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, mock_cosmos_client):
        """Test getting user sessions."""
        container = mock_cosmos_client['container']
        expected_sessions = [
            {"id": "session1", "user_email": "test@example.com", "created_at": "2024-01-01"}
        ]
        container.query_items.return_value = expected_sessions
        
        with patch('database.interactions_container', container):
            result = await get_user_sessions("test@example.com")
            
            assert result == expected_sessions
    
    @pytest.mark.asyncio
    async def test_get_context_history(self, mock_cosmos_client):
        """Test getting context history."""
        container = mock_cosmos_client['container']
        expected_context = [
            {"id": "context1", "user_email": "test@example.com", "context": "meal planning"}
        ]
        container.query_items.return_value = expected_context
        
        with patch('database.interactions_container', container):
            result = await get_context_history("test@example.com", limit=10)
            
            assert result == expected_context
    
    @pytest.mark.asyncio
    async def test_log_meal_suggestion(self, mock_cosmos_client):
        """Test logging meal suggestion."""
        container = mock_cosmos_client['container']
        suggestion_data = {
            "user_email": "test@example.com",
            "suggestion": "Try quinoa salad",
            "context": "lunch recommendation"
        }
        expected_result = {"id": "suggestion_1", **suggestion_data}
        container.create_item.return_value = expected_result
        
        with patch('database.interactions_container', container):
            result = await log_meal_suggestion(suggestion_data)
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_ai_suggestion(self, mock_cosmos_client):
        """Test getting AI suggestion."""
        container = mock_cosmos_client['container']
        expected_suggestion = {
            "id": "suggestion_1",
            "user_email": "test@example.com",
            "suggestion": "Try quinoa salad"
        }
        container.query_items.return_value = [expected_suggestion]
        
        with patch('database.interactions_container', container):
            result = await get_ai_suggestion("test@example.com", "lunch")
            
            assert result == expected_suggestion
    
    @pytest.mark.asyncio
    async def test_view_meal_plans(self, mock_cosmos_client):
        """Test viewing meal plans with pagination."""
        container = mock_cosmos_client['container']
        expected_plans = [
            {"id": "plan1", "user_email": "test@example.com"},
            {"id": "plan2", "user_email": "test@example.com"}
        ]
        container.query_items.return_value = expected_plans
        
        with patch('database.interactions_container', container):
            result = await view_meal_plans("test@example.com", limit=10, offset=0)
            
            assert result == expected_plans
    
    @pytest.mark.asyncio
    async def test_get_user_meal_history(self, mock_cosmos_client):
        """Test getting user meal history."""
        container = mock_cosmos_client['container']
        expected_history = [
            {"id": "meal1", "user_email": "test@example.com", "meal": "Breakfast"}
        ]
        container.query_items.return_value = expected_history
        
        with patch('database.interactions_container', container):
            result = await get_user_meal_history("test@example.com", limit=50)
            
            assert result == expected_history


class TestErrorHandling:
    """Test database error handling."""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, mock_cosmos_client):
        """Test handling database connection errors."""
        container = mock_cosmos_client['container']
        container.query_items.side_effect = Exception("Connection failed")
        
        with patch('database.interactions_container', container):
            with pytest.raises(Exception):
                await get_user_meal_plans("test@example.com")
    
    @pytest.mark.asyncio
    async def test_resource_not_found_handling(self, mock_cosmos_client):
        """Test handling of resource not found errors."""
        container = mock_cosmos_client['container']
        container.read_item.side_effect = CosmosResourceNotFoundError(message="Not found")
        
        with patch('database.interactions_container', container):
            result = await get_meal_plan_by_id("nonexistent", "test@example.com")
            assert result is None


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_user_complete_workflow(self, mock_cosmos_client):
        """Test complete user workflow from creation to meal planning."""
        container = mock_cosmos_client['container']
        
        # Mock responses for different operations
        user_data = {"email": "test@example.com", "username": "testuser"}
        meal_plan_data = {"user_email": "test@example.com", "days": 7}
        
        container.create_item.side_effect = [
            {"id": "test@example.com", **user_data},  # User creation
            {"id": "plan_1", **meal_plan_data}       # Meal plan creation
        ]
        container.query_items.return_value = [{"id": "test@example.com", **user_data}]
        
        with patch('database.user_container', container), \
             patch('database.interactions_container', container), \
             patch('services.cache_service.invalidate_meal_plan_cache'):
            
            # Create user
            user_result = await create_user(user_data)
            assert user_result["email"] == "test@example.com"
            
            # Get user
            get_result = await get_user_by_email("test@example.com")
            assert get_result["email"] == "test@example.com"
            
            # Save meal plan
            plan_result = await save_meal_plan("test@example.com", meal_plan_data)
            assert plan_result["user_email"] == "test@example.com"