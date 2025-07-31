"""
Comprehensive tests for utility functions in utils.py
"""
import pytest
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from freezegun import freeze_time
import pytz

from utils import (
    get_password_hash, verify_password, create_access_token,
    get_today_utc_boundaries, validate_user_timezone, get_user_timezone_boundaries,
    filter_today_records, robust_json_parse, generate_registration_code,
    send_registration_code, validate_and_normalize_profile, calculate_profile_completeness,
    SECRET_KEY, ALGORITHM, pwd_context, oauth2_scheme
)


class TestPasswordFunctions:
    """Test password hashing and verification functions."""
    
    def test_get_password_hash(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password  # Should be hashed
        assert len(hashed) > 10  # Reasonable hash length
        assert hashed.startswith("$2b$")  # bcrypt format
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "secure_password_456"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Different due to salt
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenFunctions:
    """Test JWT token creation and handling."""
    
    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # Reasonable token length
        
        # Decode and verify (without signature verification for testing)
        from jose import jwt
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "test@example.com"
        assert "exp" in decoded
    
    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "test@example.com", "role": "user"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)
        
        from jose import jwt
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "user"
        
        # Check expiry is approximately 2 hours from now
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        assert abs((exp_time - expected_exp).total_seconds()) < 60  # Within 1 minute
    
    def test_create_access_token_empty_data(self):
        """Test creating access token with empty data."""
        token = create_access_token({})
        
        from jose import jwt
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded  # Should have expiry


class TestDateTimeUtilities:
    """Test date and timezone utility functions."""
    
    @freeze_time("2024-01-15 12:30:45")
    def test_get_today_utc_boundaries(self):
        """Test getting today's UTC boundaries."""
        start, end = get_today_utc_boundaries()
        
        assert start.year == 2024
        assert start.month == 1
        assert start.day == 15
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.microsecond == 0
        
        assert end.year == 2024
        assert end.month == 1
        assert end.day == 16  # Next day
        assert end.hour == 0
        assert end.minute == 0
        assert end.second == 0
        assert end.microsecond == 0
    
    def test_validate_user_timezone_valid(self):
        """Test timezone validation with valid timezones."""
        assert validate_user_timezone("UTC") == "UTC"
        assert validate_user_timezone("America/New_York") == "America/New_York"
        assert validate_user_timezone("Europe/London") == "Europe/London"
        assert validate_user_timezone("Asia/Tokyo") == "Asia/Tokyo"
    
    def test_validate_user_timezone_invalid(self):
        """Test timezone validation with invalid timezones."""
        assert validate_user_timezone("Invalid/Timezone") == "UTC"
        assert validate_user_timezone("Not_A_Timezone") == "UTC"
        assert validate_user_timezone("") == "UTC"
        assert validate_user_timezone(None) == "UTC"
        assert validate_user_timezone("   ") == "UTC"
    
    @freeze_time("2024-06-15 18:30:00")  # 6:30 PM UTC
    def test_get_user_timezone_boundaries_utc(self):
        """Test getting timezone boundaries for UTC."""
        start, end = get_user_timezone_boundaries("UTC")
        
        assert start.year == 2024
        assert start.month == 6
        assert start.day == 15
        assert start.hour == 0
        assert start.minute == 0
        
        assert end.year == 2024
        assert end.month == 6
        assert end.day == 16
        assert end.hour == 0
        assert end.minute == 0
    
    @freeze_time("2024-06-15 18:30:00")  # 6:30 PM UTC = 2:30 PM EDT
    def test_get_user_timezone_boundaries_est(self):
        """Test getting timezone boundaries for Eastern timezone."""
        start, end = get_user_timezone_boundaries("America/New_York")
        
        # Should return UTC times for start of day in Eastern timezone
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert end > start
        assert (end - start).days == 1
    
    def test_get_user_timezone_boundaries_invalid_timezone(self):
        """Test timezone boundaries with invalid timezone falls back to UTC."""
        start, end = get_user_timezone_boundaries("Invalid/Timezone")
        
        # Should fall back to UTC boundaries
        utc_start, utc_end = get_today_utc_boundaries()
        assert start == utc_start
        assert end == utc_end


class TestFilterTodayRecords:
    """Test filtering consumption records by timezone."""
    
    def create_test_records(self):
        """Helper to create test consumption records."""
        base_time = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
        return [
            {
                "food_name": "Breakfast",
                "timestamp": (base_time - timedelta(hours=6)).isoformat() + "Z",
                "meal_type": "breakfast"
            },
            {
                "food_name": "Lunch",
                "timestamp": base_time.isoformat() + "Z",
                "meal_type": "lunch"
            },
            {
                "food_name": "Yesterday Dinner",
                "timestamp": (base_time - timedelta(days=1)).isoformat() + "Z",
                "meal_type": "dinner"
            },
            {
                "food_name": "Future Snack",
                "timestamp": (base_time + timedelta(days=1)).isoformat() + "Z",
                "meal_type": "snack"
            }
        ]
    
    def test_filter_today_records_utc(self):
        """Test filtering records for UTC timezone."""
        records = self.create_test_records()
        today_records = filter_today_records(records, "UTC")
        
        # Should include breakfast and lunch (today), exclude yesterday and future
        food_names = [r["food_name"] for r in today_records]
        assert "Breakfast" in food_names
        assert "Lunch" in food_names
        assert "Yesterday Dinner" not in food_names
        assert "Future Snack" not in food_names
    
    def test_filter_today_records_empty_list(self):
        """Test filtering empty records list."""
        result = filter_today_records([], "UTC")
        assert result == []
    
    def test_filter_today_records_invalid_timestamps(self):
        """Test filtering records with invalid timestamps."""
        records = [
            {"food_name": "Valid", "timestamp": datetime.utcnow().isoformat() + "Z"},
            {"food_name": "Invalid", "timestamp": "invalid-timestamp"},
            {"food_name": "Missing", "timestamp": None},
            {"food_name": "Empty", "timestamp": ""}
        ]
        
        result = filter_today_records(records, "UTC")
        food_names = [r["food_name"] for r in result]
        assert "Valid" in food_names
        assert "Invalid" not in food_names
        assert "Missing" not in food_names
        assert "Empty" not in food_names


class TestJSONParsing:
    """Test robust JSON parsing utility."""
    
    def test_robust_json_parse_valid_json(self):
        """Test parsing valid JSON."""
        json_str = '{"key": "value", "number": 42}'
        result = robust_json_parse(json_str)
        
        assert result["success"] is True
        assert result["data"]["key"] == "value"
        assert result["data"]["number"] == 42
    
    def test_robust_json_parse_with_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        json_str = '```json\n{"meal": "oatmeal", "calories": 300}\n```'
        result = robust_json_parse(json_str)
        
        assert result["success"] is True
        assert result["data"]["meal"] == "oatmeal"
        assert result["data"]["calories"] == 300
    
    def test_robust_json_parse_with_extra_text(self):
        """Test extracting JSON from text with extra content."""
        json_str = 'Here is the meal plan: {"breakfast": "eggs", "lunch": "salad"} for today.'
        result = robust_json_parse(json_str)
        
        assert result["success"] is True
        assert result["data"]["breakfast"] == "eggs"
        assert result["data"]["lunch"] == "salad"
    
    def test_robust_json_parse_trailing_commas(self):
        """Test parsing JSON with trailing commas."""
        json_str = '{"meal": "soup", "calories": 250,}'
        result = robust_json_parse(json_str)
        
        assert result["success"] is True
        assert result["data"]["meal"] == "soup"
        assert result["data"]["calories"] == 250
    
    def test_robust_json_parse_invalid_json(self):
        """Test parsing completely invalid JSON."""
        json_str = 'This is not JSON at all!'
        result = robust_json_parse(json_str, "test_context")
        
        assert result["success"] is False
        assert "error" in result
        assert "test_context" in result["error"]
        assert "raw_data" in result
    
    def test_robust_json_parse_empty_string(self):
        """Test parsing empty string."""
        result = robust_json_parse("")
        
        assert result["success"] is False
        assert "error" in result


class TestRegistrationUtilities:
    """Test registration code generation and SMS functions."""
    
    def test_generate_registration_code(self):
        """Test registration code generation."""
        code = generate_registration_code()
        
        assert len(code) == 8
        assert code.isalnum()
        assert code.isupper()
        
        # Test uniqueness (high probability)
        codes = [generate_registration_code() for _ in range(10)]
        assert len(set(codes)) == len(codes)  # All unique
    
    @patch('utils.twilio_client')
    def test_send_registration_code_success(self, mock_twilio):
        """Test successful SMS sending."""
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        mock_twilio.messages.create.return_value = mock_message
        
        result = send_registration_code("+1234567890", "ABC123")
        
        assert result == "test_message_sid"
        mock_twilio.messages.create.assert_called_once()
        call_args = mock_twilio.messages.create.call_args
        assert "ABC123" in call_args.kwargs["body"]
        assert call_args.kwargs["to"] == "+1234567890"
    
    @patch('utils.twilio_client')
    def test_send_registration_code_failure(self, mock_twilio):
        """Test SMS sending failure."""
        mock_twilio.messages.create.side_effect = Exception("SMS failed")
        
        result = send_registration_code("+1234567890", "ABC123")
        
        assert result is None


class TestProfileValidation:
    """Test profile validation and normalization functions."""
    
    def test_validate_and_normalize_profile_basic(self):
        """Test basic profile validation and normalization."""
        profile = {
            "name": "John Doe",
            "age": "35",  # String that should be converted to float
            "ethnicity": "Asian",  # String that should become list
            "medicalConditions": ["Diabetes"],
            "wantsWeightLoss": "true"  # String that should become boolean
        }
        
        normalized = validate_and_normalize_profile(profile)
        
        assert normalized["name"] == "John Doe"
        assert normalized["age"] == 35.0  # Converted to float
        assert normalized["ethnicity"] == ["Asian"]  # Converted to list
        assert normalized["medicalConditions"] == ["Diabetes"]  # Already list
        assert normalized["wantsWeightLoss"] is True  # Converted to boolean
    
    def test_validate_and_normalize_profile_array_fields(self):
        """Test normalization of array fields."""
        profile = {
            "dietType": "Vegetarian",  # String to list
            "allergies": ["Nuts", "Dairy"],  # Already list
            "exerciseTypes": None,  # None to empty list
            "primaryGoals": ""  # Empty string to empty list
        }
        
        normalized = validate_and_normalize_profile(profile)
        
        assert normalized["dietType"] == ["Vegetarian"]
        assert normalized["allergies"] == ["Nuts", "Dairy"]
        assert normalized["exerciseTypes"] == []
        assert normalized["primaryGoals"] == []
    
    def test_validate_and_normalize_profile_numeric_fields(self):
        """Test normalization of numeric fields."""
        profile = {
            "height": "175.5",
            "weight": "70",
            "age": "invalid",  # Should become None
            "bmi": 25.5,  # Already float
            "systolicBP": None  # Should remain None
        }
        
        normalized = validate_and_normalize_profile(profile)
        
        assert normalized["height"] == 175.5
        assert normalized["weight"] == 70.0
        assert normalized["age"] is None  # Invalid conversion
        assert normalized["bmi"] == 25.5
        assert normalized["systolicBP"] is None
    
    def test_validate_and_normalize_profile_boolean_fields(self):
        """Test normalization of boolean fields."""
        profile = {
            "mobilityIssues": "true",
            "wantsWeightLoss": "false",
            "anotherBoolean": "yes",
            "numberBoolean": 1,
            "zeroBoolean": 0
        }
        
        normalized = validate_and_normalize_profile(profile)
        
        assert normalized["mobilityIssues"] is True
        assert normalized["wantsWeightLoss"] is False
        assert normalized.get("anotherBoolean") is True  # 'yes' converts to True
        assert normalized.get("numberBoolean") is True  # 1 converts to True
        assert normalized.get("zeroBoolean") is False  # 0 converts to False
    
    def test_validate_and_normalize_profile_invalid_input(self):
        """Test validation with invalid input."""
        with pytest.raises(ValueError):
            validate_and_normalize_profile("not a dict")
        
        with pytest.raises(ValueError):
            validate_and_normalize_profile(None)


class TestProfileCompleteness:
    """Test profile completeness calculation."""
    
    def test_calculate_profile_completeness_empty(self):
        """Test completeness of empty profile."""
        completeness = calculate_profile_completeness({})
        assert completeness == 0.0
    
    def test_calculate_profile_completeness_minimal(self):
        """Test completeness of minimal profile."""
        profile = {
            "name": "John Doe",
            "age": 35
        }
        completeness = calculate_profile_completeness(profile)
        assert 0 < completeness < 100  # Some progress but not complete
    
    def test_calculate_profile_completeness_comprehensive(self):
        """Test completeness of comprehensive profile."""
        profile = {
            "name": "John Doe",
            "age": 35,
            "gender": "Male",
            "height": 175.0,
            "weight": 70.0,
            "medicalConditions": ["Type 2 Diabetes"],
            "currentMedications": ["Metformin"],
            "dietType": ["Mediterranean"],
            "dietaryFeatures": ["Low sodium"],
            "primaryGoals": ["Weight loss"],
            "calorieTarget": "2000",
            "ethnicity": ["Caucasian"],
            "labValues": {"A1C": "6.5"},
            "allergies": ["None"],
            "exerciseTypes": ["Walking"],
            "workActivityLevel": "Moderate",
            "exerciseFrequency": "3 times per week",
            "mealPrepCapability": "Advanced",
            "eatingSchedule": "Regular",
            "readinessToChange": "High"
        }
        completeness = calculate_profile_completeness(profile)
        assert completeness > 90.0  # Should be very complete
    
    def test_calculate_profile_completeness_empty_values(self):
        """Test that empty values don't count toward completeness."""
        profile = {
            "name": "",  # Empty string
            "age": None,  # None value
            "medicalConditions": [],  # Empty list
            "labValues": {}  # Empty dict
        }
        completeness = calculate_profile_completeness(profile)
        assert completeness == 0.0
    
    def test_calculate_profile_completeness_partial_values(self):
        """Test completeness with some meaningful values."""
        profile = {
            "name": "Jane Doe",  # Valid
            "age": 28,  # Valid
            "medicalConditions": ["Hypertension"],  # Valid list
            "currentMedications": [],  # Empty list (doesn't count)
            "labValues": {"cholesterol": "200"},  # Valid dict
            "allergies": ""  # Empty string (doesn't count)
        }
        completeness = calculate_profile_completeness(profile)
        assert 0 < completeness < 50  # Partial completion


class TestSecurityConfiguration:
    """Test security-related configurations."""
    
    def test_secret_key_exists(self):
        """Test that SECRET_KEY is configured."""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 10  # Reasonable length
    
    def test_algorithm_configuration(self):
        """Test JWT algorithm configuration."""
        assert ALGORITHM == "HS256"
    
    def test_password_context_configuration(self):
        """Test password context is properly configured."""
        assert pwd_context is not None
        # Test that it can hash and verify
        password = "test_password"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed)
    
    def test_oauth2_scheme_configuration(self):
        """Test OAuth2 scheme configuration."""
        assert oauth2_scheme is not None
        assert oauth2_scheme.tokenUrl == "login"