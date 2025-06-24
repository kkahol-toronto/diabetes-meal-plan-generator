import unittest
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from io import BytesIO

# Add the parent directory to the path so we can import the main app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

client = TestClient(app)

class TestDataExport(unittest.TestCase):
    """Tests for the data export functionality"""

    @patch('app.routers.users.get_current_user')
    @patch('app.routers.users.user_container')
    @patch('app.routers.users.meal_plan_container')
    @patch('app.routers.users.chat_container')
    @patch('app.routers.users.interactions_container')
    def test_json_export(self, mock_interactions, mock_chat, mock_meal_plans, mock_user, mock_get_user):
        """Test exporting user data in JSON format"""
        # Mock the current user
        mock_user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password_hash": "hashed_password",
            "salt": "salt_value",
            "diabetes_type": "Type 2",
            "dietary_restrictions": ["gluten-free"],
            "created_at": "2023-01-01T00:00:00Z"
        }
        mock_get_user.return_value = mock_user_data
        
        # Mock user container read_item
        mock_user.read_item.return_value = mock_user_data
        
        # Mock meal plans
        mock_meal_plans.query_items.return_value = [
            {
                "id": "mp1",
                "user_id": "test@example.com",
                "date": "2023-06-01",
                "calories": 2000,
                "carbs": 200,
                "protein": 100,
                "fat": 70
            }
        ]
        
        # Mock chat logs
        mock_chat.query_items.return_value = [
            {
                "id": "chat1",
                "user_id": "test@example.com",
                "timestamp": "2023-06-01T12:00:00Z",
                "user_message": "How can I reduce my carb intake?",
                "bot_response": "You can try replacing rice with cauliflower rice..."
            }
        ]
        
        # Mock consumption records
        mock_interactions.query_items.side_effect = [
            # First call for consumption
            [
                {
                    "id": "c1",
                    "user_id": "test@example.com",
                    "type": "consumption",
                    "date": "2023-06-01",
                    "food_name": "Grilled Chicken",
                    "amount": "200g"
                }
            ],
            # Second call for shopping lists
            [
                {
                    "id": "sl1",
                    "user_id": "test@example.com",
                    "type": "shopping_list",
                    "name": "Weekly Groceries",
                    "items": ["Chicken", "Broccoli", "Olive Oil"]
                }
            ],
            # Third call for recipes
            [
                {
                    "id": "r1",
                    "user_id": "test@example.com",
                    "type": "recipe",
                    "name": "Chicken Stir Fry",
                    "ingredients": ["Chicken", "Vegetables", "Soy Sauce"]
                }
            ]
        ]
        
        # Make the request
        response = client.get("/api/users/me/data-export?format=json")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify structure
        self.assertIn("profile", data)
        self.assertIn("meal_plans", data)
        self.assertIn("chat_logs", data)
        self.assertIn("consumption_history", data)
        self.assertIn("shopping_lists", data)
        self.assertIn("recipes", data)
        self.assertIn("export_date", data)
        
        # Verify content
        self.assertEqual(data["profile"]["name"], "Test User")
        self.assertEqual(len(data["meal_plans"]), 1)
        self.assertEqual(data["meal_plans"][0]["calories"], 2000)
        self.assertEqual(len(data["chat_logs"]), 1)
        self.assertEqual(len(data["consumption_history"]), 1)
        self.assertEqual(data["consumption_history"][0]["food_name"], "Grilled Chicken")
        
        # Verify sensitive data is removed
        self.assertNotIn("password_hash", data["profile"])
        self.assertNotIn("salt", data["profile"])

    @patch('app.routers.users.get_current_user')
    @patch('app.routers.users.user_container')
    @patch('app.routers.users.meal_plan_container')
    @patch('app.routers.users.chat_container')
    @patch('app.routers.users.interactions_container')
    def test_pdf_export(self, mock_interactions, mock_chat, mock_meal_plans, mock_user, mock_get_user):
        """Test exporting user data in PDF format"""
        # Set up the same mocks as the JSON test
        mock_user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password_hash": "hashed_password",
            "salt": "salt_value"
        }
        mock_get_user.return_value = mock_user_data
        mock_user.read_item.return_value = mock_user_data
        mock_meal_plans.query_items.return_value = []
        mock_chat.query_items.return_value = []
        mock_interactions.query_items.return_value = []
        
        # Make the request
        response = client.get("/api/users/me/data-export?format=pdf")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertEqual(response.headers["Content-Disposition"], "attachment; filename=my-data.pdf")
        
        # Verify it's a PDF (starts with %PDF-)
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertTrue(len(response.content) > 100)  # Basic size check

if __name__ == "__main__":
    unittest.main() 