"""
Comprehensive Data Models Module

This module defines all Pydantic models used throughout the diabetes meal plan
generator application. Models provide data validation, serialization, and
type safety for API requests and database operations.

Classes:
    - User: User authentication and profile data
    - UserProfile: Detailed user preferences and health information
    - Token: JWT authentication tokens
    - RegistrationData: User registration and consent information
    - Patient: Medical patient information
    - Meal plan models: Various meal and nutrition related models

Author: Diabetes Meal Plan Generator Team
Version: 2.0.0
Last Updated: 2024
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """
    Token model class.
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    TokenData model class.
    """
    username: Optional[str] = None


class User(BaseModel):
    """
    User model class.
    """
    username: str
    email: EmailStr
    disabled: Optional[bool] = None
    # Privacy & Consent Fields
    consent_given: Optional[bool] = None
    consent_timestamp: Optional[str] = None
    policy_version: Optional[str] = None
    data_retention_preference: Optional[str] = (
        "standard"  # "minimal", "standard", "extended"
    )
    marketing_consent: Optional[bool] = False
    analytics_consent: Optional[bool] = True
    last_consent_update: Optional[str] = None
    # Electronic Signature Fields
    electronic_signature: Optional[str] = None
    signature_timestamp: Optional[str] = None
    signature_ip_address: Optional[str] = None
    research_consent: Optional[bool] = False


class UserInDB(User):
    """
    UserInDB model class.
    """
    hashed_password: str


class Patient(BaseModel):
    """
    Patient model class.
    """
    name: str = Field(..., min_length=1, description="Patient's full name")
    phone: str = Field(..., min_length=10, description="Patient's phone number")
    condition: str = Field(..., min_length=1, description="Primary medical condition")
    medical_conditions: Optional[List[str]] = Field(
        default=[], description="All medical conditions"
    )
    medications: Optional[List[str]] = Field(
        default=[], description="Current medications"
    )
    allergies: Optional[List[str]] = Field(default=[], description="Food allergies")
    dietary_restrictions: Optional[List[str]] = Field(
        default=[], description="Dietary restrictions"
    )
    registration_code: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        """
    Config model class.
    """


class UserProfile(BaseModel):
    """
    UserProfile model class.
    """    # Patient Demographics
    name: Optional[str] = None
    dateOfBirth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    ethnicity: Optional[List[str]] = []

    # Medical History
    medical_conditions: Optional[List[str]] = []
    medicalConditions: Optional[List[str]] = []  # For backward compatibility

    # Current Medications
    currentMedications: Optional[List[str]] = []

    # Lab Values (Optional)
    labValues: Optional[Dict[str, Optional[str]]] = {}

    # Vital Signs
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    waistCircumference: Optional[float] = None
    waist_circumference: Optional[float] = None  # For backward compatibility
    systolicBP: Optional[int] = None
    systolic_bp: Optional[int] = None  # For backward compatibility
    diastolicBP: Optional[int] = None
    diastolic_bp: Optional[int] = None  # For backward compatibility
    heartRate: Optional[int] = None
    heart_rate: Optional[int] = None  # For backward compatibility

    # Dietary Information
    dietType: Optional[List[str]] = []
    diet_type: Optional[str] = None  # For backward compatibility
    dietaryFeatures: Optional[List[str]] = []
    diet_features: Optional[List[str]] = []  # For backward compatibility
    dietaryRestrictions: Optional[List[str]] = []
    foodPreferences: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    strongDislikes: Optional[List[str]] = []

    # Physical Activity
    workActivityLevel: Optional[str] = None
    exerciseFrequency: Optional[str] = None
    exerciseTypes: Optional[List[str]] = []
    mobilityIssues: Optional[bool] = False

    # Lifestyle & Preferences
    mealPrepCapability: Optional[str] = None
    availableAppliances: Optional[List[str]] = []
    eatingSchedule: Optional[str] = None

    # Goals & Readiness
    primaryGoals: Optional[List[str]] = []
    readinessToChange: Optional[str] = None

    # Meal Plan Targeting
    wantsWeightLoss: Optional[bool] = False
    weight_loss_goal: Optional[bool] = False  # For backward compatibility
    calorieTarget: Optional[str] = None
    calories_target: Optional[int] = None  # For backward compatibility
    proteinTarget: Optional[str] = None  # Daily protein goal in grams
    protein_target: Optional[int] = None  # For backward compatibility

    # Comprehensive Macro Goals
    macroGoals: Optional[Dict[str, Optional[int]]] = (
        {}
    )  # {"protein": 100, "carbs": 250, "fat": 66}

    # Timezone for proper date filtering
    timezone: Optional[str] = "UTC"


class MealPlanRequest(BaseModel):
    """
    MealPlanRequest model class.
    """
    user_profile: UserProfile
    family_members: Optional[List[UserProfile]] = None
    additional_requirements: Optional[str] = None


class ChatMessage(BaseModel):
    """
    ChatMessage model class.
    """
    message: str
    session_id: Optional[str] = None


class RegistrationData(BaseModel):
    """
    RegistrationData model class.
    """
    registration_code: str
    email: EmailStr
    password: str
    consent_given: bool
    consent_timestamp: str
    policy_version: str
    data_retention_preference: Optional[str] = "standard"
    marketing_consent: Optional[bool] = False
    analytics_consent: Optional[bool] = True
    # Electronic Signature Fields
    electronic_signature: str
    signature_timestamp: str
    signature_ip_address: Optional[str] = None
    research_consent: Optional[bool] = False
    timezone: Optional[str] = "UTC"


class ImageAnalysisRequest(BaseModel):
    """
    Request model for image analysis containing prompt data.
    """
    prompt: str
