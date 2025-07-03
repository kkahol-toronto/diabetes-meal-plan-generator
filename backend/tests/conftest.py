"""
Pytest configuration and fixtures for the diabetes meal plan generator tests.
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import jwt

# Set environment variables before importing main to avoid Azure credentials issues
os.environ["AZURE_OPENAI_KEY"] = "test_key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-12-01-preview"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4"
os.environ["COSMO_DB_CONNECTION_STRING"] = "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=dGVzdF9rZXk=;"
os.environ["INTERACTIONS_CONTAINER"] = "test_interactions"
os.environ["USER_INFORMATION_CONTAINER"] = "test_users"
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["SMS_API_SID"] = "test_sms_sid"
os.environ["SMS_KEY"] = "test_sms_key"

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock azure.cosmos module before any imports
mock_cosmos_client = MagicMock()
mock_client_instance = MagicMock()
mock_cosmos_client.from_connection_string.return_value = mock_client_instance

# Mock containers
mock_interactions_container = MagicMock()
mock_user_container = MagicMock()
mock_database = MagicMock()
mock_database.get_container_client.side_effect = lambda x: mock_interactions_container if x == "test_interactions" else mock_user_container
mock_client_instance.get_database_client.return_value = mock_database

# Create a mock azure.cosmos module
mock_azure_cosmos = MagicMock()
mock_azure_cosmos.CosmosClient = mock_cosmos_client
mock_azure_cosmos.exceptions = MagicMock()
mock_azure_cosmos.exceptions.CosmosResourceNotFoundError = Exception

# Patch the module before import
sys.modules['azure.cosmos'] = mock_azure_cosmos

from main import app
from database import interactions_container, user_container


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "id": "test@example.com",
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": "$2b$12$Pk.9ehLaB/CTuiyO0nWBjeuDcDecMRNdvMZx9KXxtPFGgaAs/2AeC",
        "disabled": False,
        "type": "user",
        "consent_given": True,
        "consent_timestamp": datetime.utcnow().isoformat(),
        "policy_version": "1.0",
        "data_retention_preference": "standard",
        "marketing_consent": False,
        "analytics_consent": True,
        "last_consent_update": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def mock_patient_data():
    """Mock patient data for testing."""
    return {
        "id": "TEST123",
        "name": "Test Patient",
        "phone": "1234567890",
        "condition": "Type 2 Diabetes",
        "medical_conditions": ["Type 2 Diabetes"],
        "medications": ["Metformin"],
        "allergies": ["Nuts"],
        "dietary_restrictions": ["Vegetarian"],
        "registration_code": "TEST123",
        "created_at": datetime.utcnow().isoformat(),
        "type": "patient",
    }


@pytest.fixture
def mock_meal_plan_data():
    """Mock meal plan data for testing."""
    return {
        "id": "meal_plan_123",
        "user_id": "test@example.com",
        "type": "meal_plan",
        "created_at": datetime.utcnow().isoformat(),
        "breakfast": ["Oatmeal with berries", "Greek yogurt"],
        "lunch": ["Grilled chicken salad", "Quinoa bowl"],
        "dinner": ["Baked salmon", "Steamed vegetables"],
        "snacks": ["Apple slices", "Almonds"],
        "dailyCalories": 1800,
        "macronutrients": {
            "protein": 120,
            "carbs": 180,
            "fat": 60,
        },
        "week": 1,
        "day": 1,
    }


@pytest.fixture
def mock_consumption_data():
    """Mock consumption data for testing."""
    return {
        "id": "consumption_123",
        "user_id": "test@example.com",
        "session_id": "session_123",
        "type": "consumption_record",
        "timestamp": datetime.utcnow().isoformat(),
        "logged_at": datetime.utcnow(),
        "food_name": "Apple",
        "estimated_portion": "1 medium",
        "nutritional_info": {
            "calories": 95,
            "carbohydrates": 25,
            "protein": 0.5,
            "fat": 0.3,
            "fiber": 4,
            "sugar": 19,
            "sodium": 2,
        },
        "medical_rating": {
            "diabetes_suitability": "high",
            "glycemic_impact": "low",
            "recommended_frequency": "daily",
            "portion_recommendation": "appropriate",
        },
        "analysis_notes": "Excellent choice for diabetes management",
        "meal_type": "snack",
    }


@pytest.fixture
def mock_chat_message_data():
    """Mock chat message data for testing."""
    return {
        "id": "chat_123",
        "user_id": "test@example.com",
        "session_id": "session_123",
        "type": "chat_message",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Hello, how are you?",
        "is_user": True,
        "image_url": None,
    }


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing - creates a valid token that can be decoded."""
    # Use the same SECRET_KEY and algorithm as the main application
    secret_key = "test_secret_key"
    algorithm = "HS256"
    
    # Create token payload with proper structure
    payload = {
        "sub": "test@example.com",
        "exp": datetime.utcnow() + timedelta(minutes=60),
        "iat": datetime.utcnow(),
        "is_admin": False,
        "name": "Test User",
        "consent_given": True,
        "consent_timestamp": datetime.utcnow().isoformat(),
        "policy_version": "1.0"
    }
    
    # Create actual JWT token
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


@pytest.fixture
def authenticated_headers(mock_jwt_token):
    """Headers with authentication token."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Test AI response"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing."""
    mock_client = Mock()
    mock_client.messages.create.return_value = Mock(sid="test_sid")
    return mock_client


@pytest.fixture
def mock_cosmos_containers():
    """Mock Cosmos DB containers for testing."""
    mock_interactions = Mock()
    mock_users = Mock()
    
    # Mock common methods
    mock_interactions.create_item = Mock(return_value={"id": "test_id"})
    mock_interactions.upsert_item = Mock(return_value={"id": "test_id"})
    mock_interactions.query_items = Mock(return_value=[])
    mock_interactions.delete_item = Mock()
    
    mock_users.create_item = Mock(return_value={"id": "test_id"})
    mock_users.upsert_item = Mock(return_value={"id": "test_id"})
    mock_users.query_items = Mock(return_value=[])
    mock_users.delete_item = Mock()
    
    return mock_interactions, mock_users


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        "AZURE_OPENAI_KEY": "test_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_VERSION": "2023-12-01-preview",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
        "COSMO_DB_CONNECTION_STRING": "test_connection",
        "INTERACTIONS_CONTAINER": "test_interactions",
        "USER_INFORMATION_CONTAINER": "test_users",
        "SECRET_KEY": "test_secret_key",
        "SMS_API_SID": "test_sms_sid",
        "SMS_KEY": "test_sms_key",
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_file_upload():
    """Mock file upload for testing."""
    mock_file = Mock()
    mock_file.filename = "test_image.jpg"
    mock_file.content_type = "image/jpeg"
    mock_file.file.read.return_value = b"fake_image_data"
    return mock_file


@pytest.fixture
def mock_user_profile_data():
    """Mock user profile data for testing."""
    return {
        "name": "Test User",
        "dateOfBirth": "1990-01-01",
        "age": 34,
        "gender": "Male",
        "ethnicity": ["Caucasian"],
        "medical_conditions": ["Type 2 Diabetes"],
        "currentMedications": ["Metformin"],
        "height": 180,
        "weight": 75,
        "bmi": 23.1,
        "dietType": ["Mediterranean"],
        "allergies": ["Nuts"],
        "dietaryRestrictions": ["Vegetarian"],
        "calorieTarget": "1800",
        "wantsWeightLoss": False,
    }


@pytest.fixture(autouse=True)
def mock_database_operations():
    """Auto-use fixture to mock database operations."""
    with patch("database.interactions_container") as mock_interactions, \
         patch("database.user_container") as mock_users, \
         patch("database.openai_client") as mock_openai:
        
        # Configure default mock behavior
        mock_interactions.create_item.return_value = {"id": "test_id"}
        mock_interactions.upsert_item.return_value = {"id": "test_id"}
        mock_interactions.query_items.return_value = []
        mock_interactions.delete_item.return_value = None
        
        mock_users.create_item.return_value = {"id": "test_id"}
        mock_users.upsert_item.return_value = {"id": "test_id"}
        mock_users.query_items.return_value = []
        mock_users.delete_item.return_value = None
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test AI response"
        mock_openai.chat.completions.create.return_value = mock_response
        
        yield mock_interactions, mock_users, mock_openai


@pytest.fixture
def mock_current_user():
    """Mock current user for dependency injection."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "disabled": False,
    }


# Helper functions for tests
def assert_response_success(response, expected_status=200):
    """Assert that a response is successful."""
    assert response.status_code == expected_status
    assert response.json() is not None


def assert_response_error(response, expected_status=400):
    """Assert that a response contains an error."""
    assert response.status_code == expected_status
    response_data = response.json()
    assert "detail" in response_data or "error" in response_data 