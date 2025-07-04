"""
Configuration module for type-safe environment variable handling.
This module centralizes all environment variable access and provides proper type safety.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable with type-safe default."""
    return os.getenv(key) or default

def get_env_var_required(key: str) -> str:
    """Get required environment variable, raise error if not found."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value

# Azure OpenAI Configuration
AZURE_OPENAI_KEY = get_env_var("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = get_env_var("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = get_env_var("AZURE_OPENAI_API_VERSION", "2023-05-15")
AZURE_OPENAI_DEPLOYMENT_NAME = get_env_var("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")

# Alternative naming for compatibility
AZURE_OPENAI_API_KEY = get_env_var("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = get_env_var("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

# Cosmos DB Configuration
COSMOS_CONNECTION_STRING = get_env_var("COSMO_DB_CONNECTION_STRING")
INTERACTIONS_CONTAINER = get_env_var("INTERACTIONS_CONTAINER", "interactions")
USER_INFORMATION_CONTAINER = get_env_var("USER_INFORMATION_CONTAINER", "user_information")

# Twilio Configuration
SMS_API_SID = get_env_var("SMS_API_SID")
SMS_KEY = get_env_var("SMS_KEY")
TWILIO_PHONE_NUMBER = get_env_var("TWILIO_PHONE_NUMBER")

# Security Configuration
SECRET_KEY = get_env_var("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Validation function
def validate_required_env_vars() -> list[str]:
    """Validate that required environment variables are set."""
    required_vars = [
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "COSMO_DB_CONNECTION_STRING",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars

# Export commonly used configurations
__all__ = [
    "AZURE_OPENAI_KEY",
    "AZURE_OPENAI_ENDPOINT", 
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
    "COSMOS_CONNECTION_STRING",
    "INTERACTIONS_CONTAINER",
    "USER_INFORMATION_CONTAINER",
    "SMS_API_SID",
    "SMS_KEY",
    "TWILIO_PHONE_NUMBER",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "get_env_var",
    "get_env_var_required",
    "validate_required_env_vars",
] 