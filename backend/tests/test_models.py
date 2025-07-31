"""
Comprehensive tests for Pydantic models in models.py
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from models import (
    Token, TokenData, User, UserInDB, Patient, UserProfile, 
    MealPlanRequest, ChatMessage, RegistrationData, ImageAnalysisRequest
)


class TestToken:
    """Test Token model."""
    
    def test_token_creation(self):
        """Test creating a valid Token."""
        token = Token(access_token="test_token", token_type="bearer")
        assert token.access_token == "test_token"
        assert token.token_type == "bearer"
    
    def test_token_required_fields(self):
        """Test Token model with missing required fields."""
        with pytest.raises(ValidationError):
            Token(access_token="test_token")  # Missing token_type
        
        with pytest.raises(ValidationError):
            Token(token_type="bearer")  # Missing access_token


class TestTokenData:
    """Test TokenData model."""
    
    def test_token_data_creation(self):
        """Test creating TokenData with username."""
        token_data = TokenData(username="testuser")
        assert token_data.username == "testuser"
    
    def test_token_data_optional_username(self):
        """Test TokenData with no username (optional)."""
        token_data = TokenData()
        assert token_data.username is None


class TestUser:
    """Test User model."""
    
    def test_user_creation(self):
        """Test creating a valid User."""
        user = User(
            username="testuser",
            email="test@example.com",
            consent_given=True,
            consent_timestamp="2024-01-01T00:00:00",
            policy_version="1.0.0",
            electronic_signature="Test User",
            signature_timestamp="2024-01-01T00:00:00"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.consent_given is True
        assert user.disabled is None  # Optional field
        assert user.data_retention_preference == "standard"  # Default value
    
    def test_user_invalid_email(self):
        """Test User model with invalid email."""
        with pytest.raises(ValidationError):
            User(
                username="testuser",
                email="invalid-email",  # Invalid email format
                consent_given=True,
                consent_timestamp="2024-01-01T00:00:00",
                policy_version="1.0.0",
                electronic_signature="Test User",
                signature_timestamp="2024-01-01T00:00:00"
            )
    
    def test_user_default_values(self):
        """Test User model default values."""
        user = User(
            username="testuser",
            email="test@example.com",
            consent_given=True,
            consent_timestamp="2024-01-01T00:00:00",
            policy_version="1.0.0",
            electronic_signature="Test User",
            signature_timestamp="2024-01-01T00:00:00"
        )
        assert user.data_retention_preference == "standard"
        assert user.marketing_consent is False
        assert user.analytics_consent is True
        assert user.research_consent is False


class TestUserInDB:
    """Test UserInDB model."""
    
    def test_user_in_db_creation(self):
        """Test creating UserInDB with hashed password."""
        user_in_db = UserInDB(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            consent_given=True,
            consent_timestamp="2024-01-01T00:00:00",
            policy_version="1.0.0",
            electronic_signature="Test User",
            signature_timestamp="2024-01-01T00:00:00"
        )
        assert user_in_db.hashed_password == "hashed_password_123"
        assert isinstance(user_in_db, User)  # Inherits from User


class TestPatient:
    """Test Patient model."""
    
    def test_patient_creation(self):
        """Test creating a valid Patient."""
        patient = Patient(
            name="John Doe",
            phone="1234567890",
            condition="Type 2 Diabetes"
        )
        assert patient.name == "John Doe"
        assert patient.phone == "1234567890"
        assert patient.condition == "Type 2 Diabetes"
        assert patient.medical_conditions == []  # Default empty list
        assert patient.medications == []
        assert patient.allergies == []
        assert patient.dietary_restrictions == []
    
    def test_patient_with_optional_fields(self):
        """Test Patient with all optional fields."""
        patient = Patient(
            name="Jane Doe",
            phone="0987654321",
            condition="Type 1 Diabetes",
            medical_conditions=["Type 1 Diabetes", "Hypertension"],
            medications=["Insulin", "Lisinopril"],
            allergies=["Peanuts", "Shellfish"],
            dietary_restrictions=["Gluten-free"],
            registration_code="ABC123"
        )
        assert len(patient.medical_conditions) == 2
        assert "Insulin" in patient.medications
        assert patient.registration_code == "ABC123"
    
    def test_patient_validation_errors(self):
        """Test Patient model validation errors."""
        # Missing required fields
        with pytest.raises(ValidationError):
            Patient(name="", phone="123", condition="Diabetes")  # Name too short
        
        with pytest.raises(ValidationError):
            Patient(name="John", phone="123", condition="Diabetes")  # Phone too short
        
        with pytest.raises(ValidationError):
            Patient(name="John", phone="1234567890", condition="")  # Condition too short
    
    def test_patient_schema_example(self):
        """Test that the example in Patient model is valid."""
        example_data = {
            "name": "John Doe",
            "phone": "1234567890",
            "condition": "Type 2 Diabetes"
        }
        patient = Patient(**example_data)
        assert patient.name == "John Doe"


class TestUserProfile:
    """Test UserProfile model."""
    
    def test_user_profile_creation_minimal(self):
        """Test creating UserProfile with minimal data."""
        profile = UserProfile()
        assert profile.name is None
        assert profile.ethnicity == []
        assert profile.medical_conditions == []
        assert profile.timezone == "UTC"  # Default value
    
    def test_user_profile_creation_complete(self):
        """Test creating UserProfile with complete data."""
        profile = UserProfile(
            name="John Doe",
            age=35,
            gender="Male",
            height=175.0,
            weight=70.0,
            medicalConditions=["Type 2 Diabetes"],
            currentMedications=["Metformin"],
            dietType=["Vegetarian"],
            allergies=["Nuts"],
            calorieTarget="2000",
            timezone="America/New_York"
        )
        assert profile.name == "John Doe"
        assert profile.age == 35
        assert profile.height == 175.0
        assert "Type 2 Diabetes" in profile.medicalConditions
        assert profile.calorieTarget == "2000"
        assert profile.timezone == "America/New_York"
    
    def test_user_profile_backward_compatibility(self):
        """Test UserProfile backward compatibility fields."""
        profile = UserProfile(
            medical_conditions=["Diabetes"],  # Old format
            medicalConditions=["Hypertension"],  # New format
            waist_circumference=90.0,  # Old format
            waistCircumference=95.0,  # New format
        )
        # Both should be accessible
        assert profile.medical_conditions == ["Diabetes"]
        assert profile.medicalConditions == ["Hypertension"]
        assert profile.waist_circumference == 90.0
        assert profile.waistCircumference == 95.0
    
    def test_user_profile_optional_fields(self):
        """Test UserProfile optional fields defaults."""
        profile = UserProfile()
        assert profile.mobilityIssues is False
        assert profile.wantsWeightLoss is False
        assert profile.labValues == {}
        assert profile.exerciseTypes == []


class TestMealPlanRequest:
    """Test MealPlanRequest model."""
    
    def test_meal_plan_request_creation(self):
        """Test creating MealPlanRequest."""
        user_profile = UserProfile(name="Test User")
        request = MealPlanRequest(user_profile=user_profile)
        assert request.user_profile.name == "Test User"
        assert request.family_members is None
        assert request.additional_requirements is None
    
    def test_meal_plan_request_with_family(self):
        """Test MealPlanRequest with family members."""
        user_profile = UserProfile(name="Main User")
        family_member = UserProfile(name="Family Member")
        request = MealPlanRequest(
            user_profile=user_profile,
            family_members=[family_member],
            additional_requirements="Low sodium"
        )
        assert len(request.family_members) == 1
        assert request.family_members[0].name == "Family Member"
        assert request.additional_requirements == "Low sodium"


class TestChatMessage:
    """Test ChatMessage model."""
    
    def test_chat_message_creation(self):
        """Test creating ChatMessage."""
        message = ChatMessage(message="Hello, how are you?")
        assert message.message == "Hello, how are you?"
        assert message.session_id is None
    
    def test_chat_message_with_session(self):
        """Test ChatMessage with session ID."""
        message = ChatMessage(
            message="I need help with my diet",
            session_id="session_123"
        )
        assert message.session_id == "session_123"


class TestRegistrationData:
    """Test RegistrationData model."""
    
    def test_registration_data_creation(self):
        """Test creating RegistrationData."""
        reg_data = RegistrationData(
            registration_code="ABC123",
            email="test@example.com",
            password="secure_password",
            consent_given=True,
            consent_timestamp="2024-01-01T00:00:00",
            policy_version="1.0.0",
            electronic_signature="Test User",
            signature_timestamp="2024-01-01T00:00:00"
        )
        assert reg_data.registration_code == "ABC123"
        assert reg_data.email == "test@example.com"
        assert reg_data.consent_given is True
        assert reg_data.data_retention_preference == "standard"  # Default
        assert reg_data.marketing_consent is False  # Default
        assert reg_data.timezone == "UTC"  # Default
    
    def test_registration_data_with_optional_fields(self):
        """Test RegistrationData with optional fields."""
        reg_data = RegistrationData(
            registration_code="XYZ789",
            email="user@example.com",
            password="password123",
            consent_given=True,
            consent_timestamp="2024-01-01T00:00:00",
            policy_version="1.0.0",
            electronic_signature="User Name",
            signature_timestamp="2024-01-01T00:00:00",
            data_retention_preference="extended",
            marketing_consent=True,
            analytics_consent=False,
            research_consent=True,
            timezone="Europe/London"
        )
        assert reg_data.data_retention_preference == "extended"
        assert reg_data.marketing_consent is True
        assert reg_data.analytics_consent is False
        assert reg_data.research_consent is True
        assert reg_data.timezone == "Europe/London"
    
    def test_registration_data_invalid_email(self):
        """Test RegistrationData with invalid email."""
        with pytest.raises(ValidationError):
            RegistrationData(
                registration_code="ABC123",
                email="invalid-email",
                password="password",
                consent_given=True,
                consent_timestamp="2024-01-01T00:00:00",
                policy_version="1.0.0",
                electronic_signature="Test",
                signature_timestamp="2024-01-01T00:00:00"
            )


class TestImageAnalysisRequest:
    """Test ImageAnalysisRequest model."""
    
    def test_image_analysis_request_creation(self):
        """Test creating ImageAnalysisRequest."""
        request = ImageAnalysisRequest(prompt="Analyze this food image")
        assert request.prompt == "Analyze this food image"
    
    def test_image_analysis_request_empty_prompt(self):
        """Test ImageAnalysisRequest with empty prompt."""
        request = ImageAnalysisRequest(prompt="")
        assert request.prompt == ""


class TestModelIntegration:
    """Test model integration and relationships."""
    
    def test_user_profile_in_meal_plan_request(self):
        """Test UserProfile used within MealPlanRequest."""
        profile = UserProfile(
            name="Integration Test User",
            age=30,
            medicalConditions=["Type 2 Diabetes"],
            dietType=["Mediterranean"],
            calorieTarget="1800"
        )
        request = MealPlanRequest(
            user_profile=profile,
            additional_requirements="Focus on whole grains"
        )
        
        # Verify the profile is properly embedded
        assert request.user_profile.name == "Integration Test User"
        assert "Type 2 Diabetes" in request.user_profile.medicalConditions
        assert request.additional_requirements == "Focus on whole grains"
    
    def test_patient_to_user_profile_conversion(self):
        """Test converting Patient data to UserProfile format."""
        patient = Patient(
            name="Patient Test",
            phone="5555555555",
            condition="Type 1 Diabetes",
            medical_conditions=["Type 1 Diabetes", "Celiac Disease"],
            allergies=["Gluten", "Dairy"],
            dietary_restrictions=["Gluten-free", "Dairy-free"]
        )
        
        # Simulate conversion to UserProfile
        profile = UserProfile(
            name=patient.name,
            medicalConditions=patient.medical_conditions,
            allergies=patient.allergies,
            dietaryRestrictions=patient.dietary_restrictions
        )
        
        assert profile.name == patient.name
        assert profile.medicalConditions == patient.medical_conditions
        assert profile.allergies == patient.allergies
        assert profile.dietaryRestrictions == patient.dietary_restrictions