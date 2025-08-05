"""
Comprehensive Utility Functions Module

This module provides essential utility functions for the diabetes meal plan generator
including password management, JWT token operations, date/time utilities, and
data validation functions.

Functions:
    - Password operations: get_password_hash, verify_password
    - JWT operations: create_access_token, get_current_user
    - Validation: validate_email, robust_json_parse
    - Generators: generate_registration_code, generate_session_id
    - Date/time utilities: various timezone and date handling functions

Author: Diabetes Meal Plan Generator Team
Version: 2.0.0
Last Updated: 2024
"""

import json
import os
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from twilio.rest import Client

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# Password context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Explicitly set rounds for bcrypt
)

# Twilio client
twilio_client = Client(os.getenv("SMS_API_SID"), os.getenv("SMS_KEY"))

# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Authentication utilities
def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create Access Token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Date/timezone utilities
def get_today_utc_boundaries():
    """
    Get today's UTC boundaries for proper daily filtering.
    Returns start and end of today in UTC.
    """
    now_utc = datetime.utcnow()

    # Get start of today (00:00:00 UTC)
    start_of_today = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get start of tomorrow (00:00:00 UTC next day)
    start_of_tomorrow = start_of_today + timedelta(days=1)

    return start_of_today, start_of_tomorrow


def validate_user_timezone(user_timezone: str) -> str:
    """
    Validate and sanitize user timezone string.
    Returns a valid timezone string or 'UTC' as fallback.
    """
    if not user_timezone or user_timezone.strip() == "":
        return "UTC"

    try:
        import pytz

        # Try to create timezone object to validate
        pytz.timezone(user_timezone)
        return user_timezone
    except (pytz.exceptions.UnknownTimeZoneError, Exception) as e:
        print(
            f"[TIMEZONE_VALIDATION] Invalid timezone '{user_timezone}': {e}. Falling back to UTC."
        )
        return "UTC"


def get_user_timezone_boundaries(user_timezone: str = "UTC"):
    """
    Get today's boundaries in the user's timezone, converted to UTC.
    This ensures proper daily reset at midnight in the user's local time.
    """
    try:
        from datetime import datetime

        import pytz

        # Validate timezone first
        user_timezone = validate_user_timezone(user_timezone)

        # Get the user's timezone
        user_tz = pytz.timezone(user_timezone)

        # Get current time in user's timezone
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        user_now = utc_now.astimezone(user_tz)

        # Get start of today in user's timezone (midnight)
        start_of_today_user = user_now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Get start of tomorrow in user's timezone
        start_of_tomorrow_user = start_of_today_user + timedelta(days=1)

        # Convert to UTC for database queries
        start_of_today_utc = start_of_today_user.astimezone(pytz.utc).replace(
            tzinfo=None
        )
        start_of_tomorrow_utc = start_of_tomorrow_user.astimezone(pytz.utc).replace(
            tzinfo=None
        )

        print(f"[TIMEZONE] User timezone: {user_timezone}")
        print(f"[TIMEZONE] User local time: {user_now}")
        print(f"[TIMEZONE] Start of today (user timezone): {start_of_today_user}")
        print(f"[TIMEZONE] Start of today (UTC): {start_of_today_utc}")
        print(f"[TIMEZONE] Start of tomorrow (UTC): {start_of_tomorrow_utc}")

        return start_of_today_utc, start_of_tomorrow_utc

    except Exception as e:
        print(f"Error getting timezone boundaries: {e}")
        # Fall back to UTC boundaries
        return get_today_utc_boundaries()


def filter_today_records(
    records: List[Dict[str, Any]], user_timezone: str = "UTC"
) -> List[Dict[str, Any]]:
    """
    Filter consumption records to only include those from today (user's timezone).
    This ensures proper daily reset at midnight.
    """
    if not records:
        return []

    start_of_today_utc, start_of_tomorrow_utc = get_user_timezone_boundaries(
        user_timezone
    )

    print(
        f"[FILTER_DEBUG] Filtering {len(records)} records for timezone: {user_timezone}"
    )
    print(f"[FILTER_DEBUG] Start of today (UTC): {start_of_today_utc}")
    print(f"[FILTER_DEBUG] Start of tomorrow (UTC): {start_of_tomorrow_utc}")

    today_records = []
    for i, record in enumerate(records):
        try:
            timestamp_str = record.get("timestamp", "")
            if not timestamp_str:
                continue

            # Parse the timestamp using the original working method
            record_timestamp = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00")
            )

            # Remove timezone info for comparison (already in UTC)
            record_timestamp_utc = record_timestamp.replace(tzinfo=None)

            # Check if the record is from today
            is_today = (
                start_of_today_utc <= record_timestamp_utc < start_of_tomorrow_utc
            )

            # Debug print for first few records
            if i < 5:  # Only print first 5 records to avoid spam
                food_name = record.get("food_name", "Unknown")
                print(
                    f"[FILTER_DEBUG] Record {i}: {food_name} at {record_timestamp_utc} - Included: {is_today}"
                )

            if is_today:
                today_records.append(record)

        except Exception as e:
            print(f"Error parsing timestamp for record: {e}")
            continue

    print(f"[FILTER_DEBUG] Filtered to {len(today_records)} records for today")
    return today_records


# JSON parsing utility
def robust_json_parse(json_string: str, context: str = "json_parse") -> Dict[str, Any]:
    """
    Parse JSON string with better error handling and fallback mechanisms.

    Args:
        json_string: The JSON string to parse
        context: Context string for logging

    Returns:
        Dict containing parsed JSON or error information
    """
    try:
        # Handle None and invalid inputs
        if json_string is None:
            return {"success": False, "error": "Input is None", "data": None}
        if not isinstance(json_string, str):
            return {"success": False, "error": "Input must be string", "data": None}
        if json_string.strip() == "":
            return {"success": False, "error": "Input is empty", "data": None}

        # First, try to parse as-is
        return {"success": True, "data": json.loads(json_string)}
    except json.JSONDecodeError as e:
        print(f"[{context}] Initial JSON parse failed: {e}")

        # Try to extract JSON from the string (in case there's extra text)
        try:
            # Find the first { and last }
            start_idx = json_string.find("{")
            end_idx = json_string.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                extracted_json = json_string[start_idx:end_idx]
                return {"success": True, "data": json.loads(extracted_json)}
        except:
            pass

        # Try to clean up common JSON issues
        try:
            # Remove common markdown formatting
            cleaned = json_string.replace("```json", "").replace("```", "")
            cleaned = cleaned.strip()

            # Remove trailing commas before closing braces/brackets
            import re

            cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

            return {"success": True, "data": json.loads(cleaned)}
        except:
            pass

    # If all parsing attempts fail, return error
    return {
        "success": False,
        "error": f"Could not parse JSON in {context}",
        "raw_data": (
            json_string[:500] + "..." if len(json_string) > 500 else json_string
        ),
    }


# Registration utilities
def generate_registration_code():
    """
    Generate Registration Code.
    """
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def send_registration_code(phone: str, code: str):
    """Send registration code via SMS using Twilio"""
    try:
        message = twilio_client.messages.create(
            body=f"Your registration code for Diabetes Diet Manager is: {code}",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=phone,
        )
        print(f"Twilio message sent successfully: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return None


# Profile validation utilities
def validate_and_normalize_profile(profile: dict) -> dict:
    """
    Validate and normalize user profile data to ensure proper data types and structure.
    """
    if not isinstance(profile, dict):
        raise ValueError("Profile must be a dictionary")

    # Create a copy to avoid modifying the original
    normalized = profile.copy()

    # Normalize array fields - ensure they are lists
    array_fields = [
        "ethnicity",
        "medicalConditions",
        "currentMedications",
        "dietType",
        "dietaryFeatures",
        "dietaryRestrictions",
        "foodPreferences",
        "allergies",
        "avoids",
        "strongDislikes",
        "exerciseTypes",
        "primaryGoals",
        "availableAppliances",
    ]

    for field in array_fields:
        if field in normalized:
            if isinstance(normalized[field], str):
                # Convert string to single-item array
                normalized[field] = [normalized[field]] if normalized[field] else []
            elif not isinstance(normalized[field], list):
                # Convert other types to empty array
                normalized[field] = []

    # Ensure labValues is a dict
    if "labValues" in normalized and not isinstance(normalized["labValues"], dict):
        normalized["labValues"] = {}

    # Validate numeric fields
    numeric_fields = [
        "age",
        "height",
        "weight",
        "bmi",
        "waistCircumference",
        "systolicBP",
        "diastolicBP",
        "heartRate",
    ]

    for field in numeric_fields:
        if field in normalized and normalized[field] is not None:
            try:
                normalized[field] = float(normalized[field])
            except (ValueError, TypeError):
                normalized[field] = None

    # Validate boolean fields
    boolean_fields = ["mobilityIssues", "wantsWeightLoss"]

    for field in boolean_fields:
        if field in normalized:
            if isinstance(normalized[field], str):
                normalized[field] = normalized[field].lower() in ("true", "1", "yes")
            else:
                normalized[field] = bool(normalized[field])

    print(
        f"[validate_and_normalize_profile] Normalized profile with {len(normalized)} fields"
    )
    return normalized


def calculate_profile_completeness(profile: dict) -> float:
    """
    Calculate the completeness percentage of a user profile.
    """
    if not profile:
        return 0.0

    # Define important fields and their weights
    critical_fields = {
        "name": 2.0,
        "age": 2.0,
        "gender": 2.0,
        "height": 2.0,
        "weight": 2.0,
        "medicalConditions": 3.0,
        "currentMedications": 2.0,
        "dietType": 2.0,
        "dietaryFeatures": 2.0,
        "primaryGoals": 2.0,
        "calorieTarget": 2.0,
    }

    optional_fields = {
        "ethnicity": 1.0,
        "labValues": 1.5,
        "allergies": 1.5,
        "exerciseTypes": 1.0,
        "workActivityLevel": 1.0,
        "exerciseFrequency": 1.0,
        "mealPrepCapability": 1.0,
        "eatingSchedule": 1.0,
        "readinessToChange": 1.0,
    }

    all_fields = {**critical_fields, **optional_fields}

    total_weight = sum(all_fields.values())
    completed_weight = 0.0

    for field, weight in all_fields.items():
        if field in profile:
            value = profile[field]

            # Check if field has meaningful value
            if value is not None and value != "" and value != []:
                # For dict fields, check if they have content
                if isinstance(value, dict) and len(value) > 0:
                    completed_weight += weight
                # For list fields, check if they have items
                elif isinstance(value, list) and len(value) > 0:
                    completed_weight += weight
                # For other fields, check if they have value
                elif not isinstance(value, (dict, list)):
                    completed_weight += weight

    completeness = (completed_weight / total_weight) * 100
    print(f"[calculate_profile_completeness] Completeness: {completeness:.1f}%")
    return round(completeness, 1)
