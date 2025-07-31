"""
Pytest configuration and shared fixtures for the diabetes meal plan generator backend tests.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import json

# Import FastAPI testing utilities
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import application modules
from main import app
from models import User, UserInDB, UserProfile, Patient, MealPlanRequest
from utils import get_password_hash, create_access_token
from constants import DEFAULT_PATIENT_PROFILE

# Set test environment
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["COSMO_DB_CONNECTION_STRING"] = "test-connection-string"
os.environ["INTERACTIONS_CONTAINER"] = "test-interactions"
os.environ["USER_INFORMATION_CONTAINER"] = "test-users"


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
async def async_client():
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_cosmos_client():
    """Mock Azure Cosmos DB client."""
    with patch('database.client') as mock_client:
        mock_database = Mock()
        mock_container = Mock()
        
        # Configure the mock
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        
        # Mock container methods
        mock_container.create_item = Mock()
        mock_container.query_items = Mock(return_value=[])
        mock_container.read_item = Mock()
        mock_container.upsert_item = Mock()
        mock_container.delete_item = Mock()
        
        yield {
            'client': mock_client,
            'database': mock_database,
            'container': mock_container
        }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing AI-related functionality."""
    with patch('services.openai_service.get_openai_client') as mock_client:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "meal_plan": {
                "day_1": {
                    "breakfast": "Oatmeal with berries",
                    "lunch": "Quinoa salad",
                    "dinner": "Grilled vegetables"
                }
            }
        })
        
        mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        yield mock_client


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for SMS testing."""
    with patch('utils.twilio_client') as mock_twilio:
        mock_message = Mock()
        mock_message.sid = "test-message-sid"
        mock_twilio.messages.create.return_value = mock_message
        yield mock_twilio


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": get_password_hash("testpassword123"),
        "disabled": False,
        "consent_given": True,
        "consent_timestamp": datetime.utcnow().isoformat(),
        "policy_version": "1.0.0",
        "electronic_signature": "Test User",
        "signature_timestamp": datetime.utcnow().isoformat(),
        "timezone": "UTC"
    }


@pytest.fixture
def test_user(test_user_data):
    """Create a test user instance."""
    return UserInDB(**test_user_data)


@pytest.fixture
def test_patient_data():
    """Sample patient data for testing."""
    return {
        "name": "Test Patient",
        "phone": "1234567890",
        "condition": "Type 2 Diabetes",
        "medical_conditions": ["Type 2 Diabetes"],
        "medications": ["Metformin"],
        "allergies": ["Nuts"],
        "dietary_restrictions": ["Vegetarian"],
        "registration_code": "TEST1234",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def test_patient(test_patient_data):
    """Create a test patient instance."""
    return Patient(**test_patient_data)


@pytest.fixture
def test_user_profile():
    """Sample user profile for testing."""
    return UserProfile(
        name="Test User",
        age=35,
        gender="Male",
        height=175.0,
        weight=70.0,
        medicalConditions=["Type 2 Diabetes"],
        currentMedications=["Metformin"],
        dietType=["Vegetarian"],
        allergies=["Nuts"],
        calorieTarget="2000",
        timezone="UTC"
    )


@pytest.fixture
def test_meal_plan_request(test_user_profile):
    """Sample meal plan request for testing."""
    return MealPlanRequest(
        user_profile=test_user_profile,
        additional_requirements="Low sodium, high fiber"
    )


@pytest.fixture
def mock_consumption_data():
    """Sample consumption data for testing."""
    return [
        {
            "id": "consumption_1",
            "user_email": "test@example.com",
            "food_name": "Oatmeal with berries",
            "meal_type": "breakfast",
            "calories": 300,
            "protein": 10,
            "carbs": 45,
            "fat": 8,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.95
        },
        {
            "id": "consumption_2", 
            "user_email": "test@example.com",
            "food_name": "Quinoa salad",
            "meal_type": "lunch",
            "calories": 400,
            "protein": 15,
            "carbs": 60,
            "fat": 12,
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "confidence": 0.90
        }
    ]


@pytest.fixture
def mock_meal_plan_data():
    """Sample meal plan data for testing."""
    return {
        "id": "meal_plan_1",
        "user_email": "test@example.com",
        "created_date": datetime.utcnow().date().isoformat(),
        "days": 7,
        "target_calories": 2000,
        "meal_plan": {
            "day_1": {
                "breakfast": "Oatmeal with berries and nuts",
                "lunch": "Quinoa salad with vegetables",
                "dinner": "Grilled vegetables with tofu",
                "snack": "Apple with almond butter"
            },
            "day_2": {
                "breakfast": "Greek yogurt with seeds",
                "lunch": "Lentil soup with bread",
                "dinner": "Stuffed bell peppers",
                "snack": "Mixed nuts"
            }
        },
        "nutrition_summary": {
            "avg_calories": 2000,
            "avg_protein": 80,
            "avg_carbs": 250,
            "avg_fat": 70
        }
    }


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers for authenticated requests."""
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_database_operations(mock_cosmos_client):
    """Mock common database operations."""
    container = mock_cosmos_client['container']
    
    async def mock_create_user(user_data):
        return {"id": user_data["email"], **user_data}
    
    async def mock_get_user_by_email(email):
        if email == "test@example.com":
            return {
                "id": email,
                "email": email,
                "username": "testuser",
                "hashed_password": get_password_hash("testpassword123"),
                "disabled": False
            }
        return None
    
    async def mock_save_meal_plan(user_email, meal_plan_data):
        return {"id": "meal_plan_1", "user_email": user_email, **meal_plan_data}
    
    # Patch database functions
    with patch('database.create_user', side_effect=mock_create_user), \
         patch('database.get_user_by_email', side_effect=mock_get_user_by_email), \
         patch('database.save_meal_plan', side_effect=mock_save_meal_plan):
        yield


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset any caches before each test."""
    # Clear any module-level caches
    try:
        from services.cache_service import cache_service
        cache_service.clear()
    except ImportError:
        pass  # Cache service may not be available
    yield
    try:
        from services.cache_service import cache_service
        cache_service.clear()
    except ImportError:
        pass


# Utility functions for testing
def assert_valid_response(response, expected_status=200, expected_keys=None):
    """Assert that a response has the expected status and structure."""
    assert response.status_code == expected_status
    if expected_keys:
        data = response.json()
        for key in expected_keys:
            assert key in data


def create_test_meal_plan(user_email="test@example.com", days=7):
    """Create a test meal plan for testing purposes."""
    return {
        "user_email": user_email,
        "days": days,
        "created_date": datetime.utcnow().date().isoformat(),
        "meal_plan": {
            f"day_{i}": {
                "breakfast": f"Test breakfast {i}",
                "lunch": f"Test lunch {i}",
                "dinner": f"Test dinner {i}",
                "snack": f"Test snack {i}"
            } for i in range(1, days + 1)
        }
    }


def create_test_consumption_record(user_email="test@example.com", meal_type="breakfast"):
    """Create a test consumption record."""
    return {
        "user_email": user_email,
        "food_name": f"Test {meal_type} food",
        "meal_type": meal_type,
        "calories": 300,
        "protein": 15,
        "carbs": 45,
        "fat": 10,
        "timestamp": datetime.utcnow().isoformat(),
        "confidence": 0.9
    }