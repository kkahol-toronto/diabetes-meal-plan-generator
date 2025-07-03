"""
Unit tests for consumption_system module.
"""
import pytest
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Mock environment variables before importing
os.environ.setdefault("AZURE_OPENAI_API_KEY", "test_key")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")

from consumption_system import ConsumptionTracker


class TestConsumptionTracker:
    """Test ConsumptionTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = ConsumptionTracker()
        self.mock_user_id = "test@example.com"
        self.mock_food_name = "Apple"
        self.mock_portion = "1 medium"
    
    @patch("consumption_system.interactions_container")
    @patch("consumption_system.client")
    @pytest.mark.asyncio
    async def test_quick_log_food_success(self, mock_client, mock_container):
        """Test successful quick food logging."""
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "food_name": "Apple",
            "estimated_portion": "1 medium",
            "nutritional_info": {
                "calories": 95,
                "carbohydrates": 25,
                "protein": 0.5,
                "fat": 0.3,
                "fiber": 4,
                "sugar": 19,
                "sodium": 2
            },
            "medical_rating": {
                "diabetes_suitability": "high",
                "glycemic_impact": "low",
                "recommended_frequency": "daily",
                "portion_recommendation": "appropriate"
            },
            "analysis_notes": "Excellent choice for diabetes management"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock database save
        mock_db_response = {"id": "consumption_123"}
        mock_container.upsert_item.return_value = mock_db_response
        
        # Set the tracker's container to use the mock
        self.tracker.container = mock_container
        
        result = await self.tracker.quick_log_food(
            self.mock_user_id, self.mock_food_name, self.mock_portion
        )
        
        assert result["success"] is True
        assert result["food_name"] == "Apple"
        assert result["nutritional_summary"]["calories"] == 95
        assert result["diabetes_rating"] == "high"
        assert result["record_id"] == "consumption_123"
        
        # Verify AI client was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify database was called
        mock_container.upsert_item.assert_called_once()
    
    @patch("consumption_system.interactions_container")
    @patch("consumption_system.client")
    @pytest.mark.asyncio
    async def test_quick_log_food_ai_failure_fallback(self, mock_client, mock_container):
        """Test quick food logging with AI failure using fallback."""
        # Mock AI failure
        mock_client.chat.completions.create.side_effect = Exception("AI API error")
        
        # Mock database save
        mock_db_response = {"id": "consumption_123"}
        mock_container.upsert_item.return_value = mock_db_response
        
        # Set the tracker's container to use the mock
        self.tracker.container = mock_container
        
        result = await self.tracker.quick_log_food(
            self.mock_user_id, self.mock_food_name, self.mock_portion
        )
        
        assert result["success"] is True
        assert result["food_name"] == "Apple"
        # Should use fallback values
        assert result["nutritional_summary"]["calories"] == 200
        assert result["diabetes_rating"] == "medium"
        
        # Verify database was still called
        mock_container.upsert_item.assert_called_once()
    
    @patch("consumption_system.interactions_container")
    @patch("consumption_system.client")
    @pytest.mark.asyncio
    async def test_quick_log_food_invalid_json_fallback(self, mock_client, mock_container):
        """Test quick food logging with invalid JSON response using fallback."""
        # Mock AI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock database save
        mock_container.upsert_item.return_value = {"id": "consumption_123"}
        
        result = await self.tracker.quick_log_food(
            self.mock_user_id, self.mock_food_name, self.mock_portion
        )
        
        assert result["success"] is True
        assert result["food_name"] == "Apple"
        # Should use fallback values
        assert result["nutritional_summary"]["calories"] == 200
        assert result["diabetes_rating"] == "medium"
    
    @patch("consumption_system.interactions_container")
    @patch("consumption_system.client")
    @pytest.mark.asyncio
    async def test_quick_log_food_database_failure(self, mock_client, mock_container):
        """Test quick food logging with database failure."""
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "food_name": "Apple",
            "estimated_portion": "1 medium",
            "nutritional_info": {"calories": 95},
            "medical_rating": {"diabetes_suitability": "high"},
            "analysis_notes": "Test"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock database failure
        mock_container.upsert_item.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            await self.tracker.quick_log_food(
                self.mock_user_id, self.mock_food_name, self.mock_portion
            )
        
        assert "Failed to log food" in str(exc_info.value)
    
    @patch("consumption_system.client")
    @pytest.mark.asyncio
    async def test_get_ai_nutrition_analysis_success(self, mock_client):
        """Test successful AI nutrition analysis."""
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "food_name": "Apple",
            "estimated_portion": "1 medium",
            "nutritional_info": {
                "calories": 95,
                "carbohydrates": 25,
                "protein": 0.5,
                "fat": 0.3,
                "fiber": 4,
                "sugar": 19,
                "sodium": 2
            },
            "medical_rating": {
                "diabetes_suitability": "high",
                "glycemic_impact": "low",
                "recommended_frequency": "daily",
                "portion_recommendation": "appropriate"
            },
            "analysis_notes": "Excellent choice for diabetes management"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await self.tracker._get_ai_nutrition_analysis(
            self.mock_food_name, self.mock_portion
        )
        
        assert result["food_name"] == "Apple"
        assert result["nutritional_info"]["calories"] == 95
        assert result["medical_rating"]["diabetes_suitability"] == "high"
        
        # Verify AI client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert "Apple" in call_args["messages"][1]["content"]
    
    @patch("consumption_system.client")
    @pytest.mark.asyncio
    async def test_get_ai_nutrition_analysis_fallback(self, mock_client):
        """Test AI nutrition analysis with fallback on failure."""
        # Mock AI failure
        mock_client.chat.completions.create.side_effect = Exception("AI API error")
        
        result = await self.tracker._get_ai_nutrition_analysis(
            self.mock_food_name, self.mock_portion
        )
        
        # Should return fallback data
        assert result["food_name"] == "Apple"
        assert result["nutritional_info"]["calories"] == 200
        assert result["medical_rating"]["diabetes_suitability"] == "medium"
        assert "estimate" in result["analysis_notes"]
    
    @patch("consumption_system.interactions_container")
    @pytest.mark.asyncio
    async def test_create_consumption_record_success(self, mock_container):
        """Test successful consumption record creation."""
        mock_analysis = {
            "food_name": "Apple",
            "estimated_portion": "1 medium",
            "nutritional_info": {
                "calories": 95,
                "carbohydrates": 25,
                "protein": 0.5,
                "fat": 0.3,
                "fiber": 4,
                "sugar": 19,
                "sodium": 2
            },
            "medical_rating": {
                "diabetes_suitability": "high",
                "glycemic_impact": "low",
                "recommended_frequency": "daily",
                "portion_recommendation": "appropriate"
            },
            "analysis_notes": "Excellent choice"
        }
        
        mock_db_response = {"id": "consumption_123"}
        mock_container.upsert_item.return_value = mock_db_response
        
        # Set the tracker's container to use the mock
        self.tracker.container = mock_container
        
        result = await self.tracker._create_consumption_record(
            self.mock_user_id, mock_analysis
        )
        
        assert result["id"] == "consumption_123"
        
        # Verify the record was created with correct structure
        call_args = mock_container.upsert_item.call_args[1]["body"]
        assert call_args["type"] == "consumption_record"
        assert call_args["user_id"] == self.mock_user_id
        assert call_args["food_name"] == "Apple"
        assert call_args["nutritional_info"]["calories"] == 95.0
        assert "timestamp" in call_args
        assert "meal_type" in call_args
    
    def test_determine_meal_type_breakfast(self):
        """Test meal type determination for breakfast time."""
        morning_time = datetime(2024, 1, 1, 8, 0, 0)  # 8:00 AM
        meal_type = self.tracker._determine_meal_type(morning_time)
        assert meal_type == "breakfast"
    
    def test_determine_meal_type_lunch(self):
        """Test meal type determination for lunch time."""
        lunch_time = datetime(2024, 1, 1, 13, 0, 0)  # 1:00 PM
        meal_type = self.tracker._determine_meal_type(lunch_time)
        assert meal_type == "lunch"
    
    def test_determine_meal_type_dinner(self):
        """Test meal type determination for dinner time."""
        dinner_time = datetime(2024, 1, 1, 19, 0, 0)  # 7:00 PM
        meal_type = self.tracker._determine_meal_type(dinner_time)
        assert meal_type == "dinner"
    
    def test_determine_meal_type_snack(self):
        """Test meal type determination for snack time."""
        snack_time = datetime(2024, 1, 1, 23, 0, 0)  # 11:00 PM
        meal_type = self.tracker._determine_meal_type(snack_time)
        assert meal_type == "snack"
    
    @patch("consumption_system.interactions_container")
    @pytest.mark.asyncio
    async def test_get_consumption_history_success(self, mock_container):
        """Test successful consumption history retrieval."""
        mock_records = [
            {
                "id": "consumption_123",
                "user_id": self.mock_user_id,
                "food_name": "Apple",
                "timestamp": "2024-01-01T12:00:00"
            },
            {
                "id": "consumption_456",
                "user_id": self.mock_user_id,
                "food_name": "Banana",
                "timestamp": "2024-01-01T14:00:00"
            }
        ]
        mock_container.query_items.return_value = iter(mock_records)
        
        # Set the tracker's container to use the mock
        self.tracker.container = mock_container
        
        result = await self.tracker.get_consumption_history(self.mock_user_id)
        
        assert len(result) == 2
        assert result[0]["food_name"] == "Apple"
        assert result[1]["food_name"] == "Banana"
        
        # Verify query was called correctly
        mock_container.query_items.assert_called_once()
        call_args = mock_container.query_items.call_args[1]
        assert "consumption_record" in call_args["query"]
        assert self.mock_user_id in call_args["query"]
    
    @patch("consumption_system.interactions_container")
    @pytest.mark.asyncio
    async def test_get_consumption_history_with_limit(self, mock_container):
        """Test getting consumption history with limit"""
        # Setup mock data
        mock_records = [
            {
                "id": "consumption_1",
                "user_id": "test@example.com",
                "type": "consumption_record",
                "timestamp": "2023-12-01T10:00:00Z",
                "food_name": "Apple",
                "nutritional_info": {"calories": 95}
            }
        ]
        
        # Mock container query
        mock_container.query_items.return_value = mock_records
        
        # Create tracker instance
        tracker = ConsumptionTracker()
        
        # Call method with limit
        result = await tracker.get_consumption_history("test@example.com", limit=10)
        
        # Verify query was called
        mock_container.query_items.assert_called_once()
        call_args = mock_container.query_items.call_args
        
        # Check the query structure instead of looking for TOP clause
        # The implementation uses Python slicing, not SQL TOP
        query = call_args[1]['query']
        assert "consumption_record" in query
        assert "test@example.com" in query
        assert "ORDER BY c.timestamp DESC" in query
        
        # Verify result
        assert len(result) == 1
        assert result[0]["food_name"] == "Apple"
    
    @patch("consumption_system.interactions_container")
    @pytest.mark.asyncio
    async def test_get_consumption_analytics_success(self, mock_container):
        """Test successful consumption analytics retrieval."""
        mock_records = [
            {
                "id": "consumption_123",
                "user_id": self.mock_user_id,
                "timestamp": "2024-01-01T12:00:00",
                "nutritional_info": {
                    "calories": 95,
                    "carbohydrates": 25,
                    "protein": 0.5,
                    "fat": 0.3
                }
            }
        ]
        mock_container.query_items.return_value = iter(mock_records)
        
        # Set the tracker's container to use the mock
        self.tracker.container = mock_container
        
        result = await self.tracker.get_consumption_analytics(self.mock_user_id, days=7)
        
        assert "total_calories" in result
        assert "average_daily_calories" in result
        assert "macronutrient_breakdown" in result
        assert "daily_breakdown" in result
        assert "period_start" in result
        assert "period_end" in result
        
        # Verify analytics calculations
        assert result["total_calories"] == 95
        assert result["macronutrient_breakdown"]["total_carbs"] == 25
        assert result["macronutrient_breakdown"]["total_protein"] == 0.5
        assert result["macronutrient_breakdown"]["total_fat"] == 0.3
    
    @patch("consumption_system.interactions_container")
    @pytest.mark.asyncio
    async def test_get_consumption_analytics_no_data(self, mock_container):
        """Test consumption analytics with no data."""
        mock_container.query_items.return_value = []
        
        result = await self.tracker.get_consumption_analytics(self.mock_user_id, days=7)
        
        # Should return empty analytics structure
        assert result["total_calories"] == 0
        assert result["average_daily_calories"] == 0
        assert result["macronutrient_breakdown"]["total_carbs"] == 0
        assert len(result["daily_breakdown"]) == 0
    
    def test_empty_analytics_response(self):
        """Test empty analytics response structure."""
        start_date = "2024-01-01"
        result = self.tracker._empty_analytics_response(start_date)
        
        assert result["total_calories"] == 0
        assert result["average_daily_calories"] == 0
        assert result["macronutrient_breakdown"]["total_carbs"] == 0
        assert result["macronutrient_breakdown"]["total_protein"] == 0
        assert result["macronutrient_breakdown"]["total_fat"] == 0
        assert result["period_start"] == start_date
        assert isinstance(result["daily_breakdown"], list)
        assert len(result["daily_breakdown"]) == 0
    
    def test_process_consumption_analytics(self):
        """Test consumption analytics processing."""
        mock_records = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "nutritional_info": {
                    "calories": 95,
                    "carbohydrates": 25,
                    "protein": 0.5,
                    "fat": 0.3
                }
            },
            {
                "timestamp": "2024-01-01T14:00:00",
                "nutritional_info": {
                    "calories": 150,
                    "carbohydrates": 30,
                    "protein": 5,
                    "fat": 8
                }
            }
        ]
        
        result = self.tracker._process_consumption_analytics(
            mock_records, days=7, start_date="2024-01-01"
        )
        
        assert result["total_calories"] == 245
        assert result["macronutrient_breakdown"]["total_carbs"] == 55
        assert result["macronutrient_breakdown"]["total_protein"] == 5.5
        assert result["macronutrient_breakdown"]["total_fat"] == 8.3
        assert result["average_daily_calories"] == 35.0  # 245 / 7 days
        assert len(result["daily_breakdown"]) == 1  # Only one day has data


if __name__ == "__main__":
    pytest.main([__file__])
