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
from typing import Optional
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import jwt
import bcrypt
from jose import jwt

# Set environment variables before importing main to avoid Azure credentials issues
os.environ["AZURE_OPENAI_KEY"] = "test_key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4"
os.environ["COSMO_DB_CONNECTION_STRING"] = "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=dGVzdF9rZXk=;"
os.environ["INTERACTIONS_CONTAINER"] = "test_interactions"
os.environ["USER_INFORMATION_CONTAINER"] = "test_users"
os.environ["SECRET_KEY"] = "your-secret-key-here"
os.environ["SMS_API_SID"] = "test_sid"
os.environ["SMS_KEY"] = "test_key"
os.environ["TWILIO_PHONE_NUMBER"] = "+1234567890"
os.environ["COSMOS_DB_CONNECTION_STRING"] = "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key;Database=test_db;"

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

# JWT Configuration matching main.py
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_test_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a proper JWT token for testing using the same method as main.py"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
    """Mock user data with proper bcrypt hash"""
    password = "testpassword"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    return {
        "id": "test@example.com",
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": hashed_password,
        "disabled": False,
        "patient_id": "TEST123",
        "profile": {
            "name": "Test User",
            "medicalConditions": ["Type 2 Diabetes"],
            "currentMedications": ["Metformin"],
            "allergies": ["Nuts"],
            "dietaryRestrictions": ["Vegetarian"]
        }
    }


@pytest.fixture
def mock_patient_data():
    """Mock patient data with proper structure"""
    return {
        "id": "TEST123",
        "name": "Test Patient",
        "registration_code": "TEST123",
        "condition": "Type 2 Diabetes",
        "medical_conditions": ["Type 2 Diabetes"],
        "medications": ["Metformin"],
        "allergies": ["Nuts"],
        "dietary_restrictions": ["Vegetarian"]
    }


@pytest.fixture
def mock_meal_plan_data():
    """Mock meal plan data"""
    return {
        "id": "meal_plan_123",
        "user_id": "test@example.com",
        "breakfast": ["Oatmeal with berries"],
        "lunch": ["Grilled chicken salad"],
        "dinner": ["Baked salmon with vegetables"],
        "snacks": ["Apple with almond butter"],
        "created_at": "2023-12-01T10:00:00Z"
    }


@pytest.fixture
def mock_consumption_data():
    """Mock consumption data"""
    return {
        "id": "consumption_123",
        "user_id": "test@example.com",
        "food_name": "Apple",
        "nutritional_info": {
            "calories": 95,
            "protein": 0.5,
            "carbs": 25,
            "fat": 0.3
        },
        "meal_type": "snack",
        "timestamp": "2023-12-01T15:30:00Z"
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
def valid_jwt_token(mock_user_data):
    """Create a valid JWT token for testing"""
    token_data = {
        "sub": mock_user_data["email"],
        "is_admin": False,
        "name": "Test User",
        "consent_given": True,
        "consent_timestamp": "2023-12-01T10:00:00Z",
        "policy_version": "1.0"
    }
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_test_access_token(data=token_data, expires_delta=expires_delta)


@pytest.fixture
def authenticated_headers(valid_jwt_token):
    """Headers with valid JWT token"""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def mock_auth_user(mock_user_data):
    """Mock the database user lookup for JWT validation"""
    with patch('main.get_user_by_email', return_value=mock_user_data):
        yield mock_user_data


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"test": "response"}'
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client"""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid"
    mock_client.messages.create.return_value = mock_message
    return mock_client


@pytest.fixture
def mock_cosmos_containers():
    """Mock Cosmos DB containers"""
    mock_containers = {
        'user_container': Mock(),
        'patient_container': Mock(),
        'interactions_container': Mock()
    }
    
    # Configure common mock behaviors
    for container in mock_containers.values():
        container.create_item.return_value = {"id": "test_id"}
        container.upsert_item.return_value = {"id": "test_id"}
        container.query_items.return_value = []
        container.read_item.return_value = None
        container.delete_item.return_value = None
    
    return mock_containers


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        "AZURE_OPENAI_KEY": "test_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_VERSION": "2023-05-15",
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


@pytest.fixture
def mock_database_functions():
    """Mock database functions"""
    with patch('main.get_user_by_email', return_value=None), \
         patch('main.create_user', return_value=None), \
         patch('main.get_patient_by_registration_code', return_value=None), \
         patch('main.save_meal_plan', return_value=None), \
         patch('main.get_user_meal_plans', return_value=[]), \
         patch('main.save_chat_message', return_value=None), \
         patch('main.get_recent_chat_history', return_value=[]):
        yield


@pytest.fixture
def sample_analytics_response():
    """Sample analytics response matching expected structure"""
    return {
        "total_calories": 2000,
        "total_protein": 80,
        "total_carbs": 250,
        "total_fat": 67,
        "macronutrient_breakdown": {
            "protein_percent": 16,
            "carbs_percent": 50,
            "fat_percent": 34
        },
        "meal_distribution": {
            "breakfast": 500,
            "lunch": 600,
            "dinner": 700,
            "snacks": 200
        },
        "daily_averages": {
            "calories": 2000,
            "protein": 80,
            "carbs": 250,
            "fat": 67
        }
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


def assert_response_structure(response, expected_keys):
    """Assert response has expected structure"""
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data


def assert_error_response(response, expected_status, expected_detail=None):
    """Assert error response has expected structure"""
    assert response.status_code == expected_status
    if expected_detail:
        assert expected_detail in response.json()["detail"] 