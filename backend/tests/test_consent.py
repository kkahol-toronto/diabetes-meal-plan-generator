import pytest
from fastapi.testclient import TestClient
from fastapi import status
import sys
import os
from datetime import datetime
import json

# Add the parent directory to the Python path to import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from unittest.mock import patch, MagicMock

# Create a test client
client = TestClient(app)

class TestConsent:
    @pytest.fixture
    def mock_get_user_by_email(self):
        """Mock the get_user_by_email function"""
        with patch('main.get_user_by_email') as mock:
            yield mock

    @pytest.fixture
    def mock_create_user(self):
        """Mock the create_user function"""
        with patch('main.create_user') as mock:
            yield mock

    @pytest.fixture
    def mock_get_patient_by_registration_code(self):
        """Mock the get_patient_by_registration_code function"""
        with patch('main.get_patient_by_registration_code') as mock:
            yield mock

    def test_register_without_consent(self, mock_get_patient_by_registration_code, mock_get_user_by_email):
        """Test that registration without consent fails"""
        # Setup mock returns
        mock_get_patient_by_registration_code.return_value = {
            "id": "123", 
            "name": "Test Patient",
            "condition": "Type 2 Diabetes"
        }
        mock_get_user_by_email.return_value = None

        # Attempt to register without consent
        response = client.post(
            "/register",
            json={
                "registration_code": "TEST123",
                "email": "test@example.com",
                "password": "securepassword",
                "consent_given": False
            }
        )

        # Verify the response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Consent required" in response.json()["detail"]

    def test_register_with_consent(self, mock_get_patient_by_registration_code, mock_get_user_by_email, mock_create_user):
        """Test that registration with consent succeeds"""
        # Setup mock returns
        mock_get_patient_by_registration_code.return_value = {
            "id": "123", 
            "name": "Test Patient",
            "condition": "Type 2 Diabetes"
        }
        mock_get_user_by_email.return_value = None
        mock_create_user.return_value = {"id": "test@example.com"}

        # Register with consent
        response = client.post(
            "/register",
            json={
                "registration_code": "TEST123",
                "email": "test@example.com",
                "password": "securepassword",
                "consent_given": True
            }
        )

        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Registration successful"

        # Verify user data includes consent fields
        called_user_data = mock_create_user.call_args[0][0]
        assert called_user_data["consent_given"] == True
        assert "consent_timestamp" in called_user_data
        assert called_user_data["policy_version"] == "1.0"

    def test_login_without_consent(self, mock_get_user_by_email):
        """Test that login without consent fails"""
        # Setup mock return
        mock_get_user_by_email.return_value = {
            "id": "test@example.com", 
            "email": "test@example.com",
            "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "securepassword"
            "consent_given": False
        }

        # Attempt to login
        response = client.post(
            "/login",
            data={
                "username": "test@example.com",
                "password": "securepassword"
            }
        )

        # Verify the response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Consent required" in response.json()["detail"]

    def test_update_consent(self, mock_get_user_by_email):
        """Test updating user consent"""
        # Setup mock user without consent
        user_without_consent = {
            "id": "test@example.com", 
            "email": "test@example.com",
            "consent_given": False
        }
        mock_get_user_by_email.return_value = user_without_consent

        # Mock the replace_item method
        with patch('main.user_container.replace_item') as mock_replace:
            # Replace item returns the updated item
            mock_replace.return_value = {**user_without_consent, "consent_given": True}

            # Mock the authentication dependency
            with patch('main.get_current_user', return_value={"email": "test@example.com"}):
                # Update consent
                response = client.post(
                    "/user/update-consent",
                    json={"consent_given": True},
                    headers={"Authorization": "Bearer test-token"}
                )

                # Verify the response
                assert response.status_code == status.HTTP_200_OK
                assert response.json()["message"] == "Consent updated successfully"

                # Verify user data was updated
                updated_user = mock_replace.call_args[1]["body"]
                assert updated_user["consent_given"] == True
                assert "consent_timestamp" in updated_user
                assert updated_user["policy_version"] == "1.0" 