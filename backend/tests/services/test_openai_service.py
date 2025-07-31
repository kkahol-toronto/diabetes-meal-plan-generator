"""
Comprehensive tests for OpenAI service in services/openai_service.py
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from datetime import datetime

from services.openai_service import robust_openai_call, get_openai_client
from constants import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_MAX_RETRIES


class TestGetOpenAIClient:
    """Test OpenAI client initialization."""
    
    @patch('services.openai_service.OpenAI')
    def test_get_openai_client_success(self, mock_openai_class):
        """Test successful OpenAI client creation."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-api-key'}):
            client = get_openai_client()
            
            assert client == mock_client
            mock_openai_class.assert_called_once_with(api_key='test-api-key')
    
    @patch('services.openai_service.OpenAI')
    def test_get_openai_client_no_api_key(self, mock_openai_class):
        """Test OpenAI client creation without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(Exception):
                get_openai_client()


class TestRobustOpenAICall:
    """Test robust OpenAI API call function."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        client = Mock()
        client.chat = Mock()
        client.chat.completions = Mock()
        client.chat.completions.create = AsyncMock()
        return client
    
    @pytest.fixture
    def sample_response(self):
        """Sample OpenAI response."""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = json.dumps({
            "meal_plan": {
                "breakfast": "Oatmeal with berries",
                "lunch": "Quinoa salad",
                "dinner": "Grilled vegetables"
            }
        })
        response.usage = Mock()
        response.usage.total_tokens = 150
        return response
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_success(self, mock_openai_client, sample_response):
        """Test successful OpenAI API call."""
        mock_openai_client.chat.completions.create.return_value = sample_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Generate a meal plan",
                context="meal_planning",
                max_tokens=1000,
                temperature=0.7
            )
            
            assert result["success"] is True
            assert "meal_plan" in result["response"]
            assert result["response"]["meal_plan"]["breakfast"] == "Oatmeal with berries"
            assert result["tokens_used"] == 150
            
            # Verify the call was made with correct parameters
            mock_openai_client.chat.completions.create.assert_called_once()
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args.kwargs["max_tokens"] == 1000
            assert call_args.kwargs["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_with_defaults(self, mock_openai_client, sample_response):
        """Test OpenAI call with default parameters."""
        mock_openai_client.chat.completions.create.return_value = sample_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Simple prompt",
                context="test"
            )
            
            assert result["success"] is True
            
            # Verify default parameters were used
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args.kwargs["max_tokens"] == DEFAULT_MAX_TOKENS
            assert call_args.kwargs["temperature"] == DEFAULT_TEMPERATURE
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_with_system_message(self, mock_openai_client, sample_response):
        """Test OpenAI call with system message."""
        mock_openai_client.chat.completions.create.return_value = sample_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Generate meal plan",
                context="meal_planning",
                system_message="You are a diabetes nutrition expert"
            )
            
            assert result["success"] is True
            
            # Verify system message was included
            call_args = mock_openai_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            assert len(messages) >= 2
            assert messages[0]["role"] == "system"
            assert "diabetes nutrition expert" in messages[0]["content"]
            assert messages[1]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_with_chat_history(self, mock_openai_client, sample_response):
        """Test OpenAI call with chat history."""
        mock_openai_client.chat.completions.create.return_value = sample_response
        
        chat_history = [
            {"role": "user", "content": "What should I eat for breakfast?"},
            {"role": "assistant", "content": "Try oatmeal with berries."},
        ]
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="What about lunch?",
                context="meal_planning",
                chat_history=chat_history
            )
            
            assert result["success"] is True
            
            # Verify chat history was included
            call_args = mock_openai_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            
            # Should include system + history + new prompt
            assert len(messages) >= 4
            assert any("breakfast" in msg["content"] for msg in messages)
            assert any("oatmeal" in msg["content"] for msg in messages)
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_json_mode(self, mock_openai_client):
        """Test OpenAI call with JSON mode."""
        json_response = Mock()
        json_response.choices = [Mock()]
        json_response.choices[0].message = Mock()
        json_response.choices[0].message.content = '{"result": "success", "data": {"meal": "oatmeal"}}'
        json_response.usage = Mock()
        json_response.usage.total_tokens = 100
        
        mock_openai_client.chat.completions.create.return_value = json_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Generate JSON response",
                context="test",
                force_json=True
            )
            
            assert result["success"] is True
            assert result["response"]["result"] == "success"
            assert result["response"]["data"]["meal"] == "oatmeal"
            
            # Verify JSON mode was enabled
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args.kwargs.get("response_format") == {"type": "json_object"}
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_api_error(self, mock_openai_client):
        """Test OpenAI call with API error."""
        from openai import APIError
        
        mock_openai_client.chat.completions.create.side_effect = APIError("Rate limit exceeded")
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Test prompt",
                context="test"
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "Rate limit exceeded" in result["error"]
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_with_retries(self, mock_openai_client, sample_response):
        """Test OpenAI call with retry logic."""
        from openai import APIError
        
        # First call fails, second succeeds
        mock_openai_client.chat.completions.create.side_effect = [
            APIError("Temporary error"),
            sample_response
        ]
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client), \
             patch('asyncio.sleep', new_callable=AsyncMock):  # Mock sleep to speed up test
            
            result = await robust_openai_call(
                prompt="Test prompt",
                context="test",
                max_retries=2
            )
            
            assert result["success"] is True
            assert mock_openai_client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_max_retries_exceeded(self, mock_openai_client):
        """Test OpenAI call when max retries are exceeded."""
        from openai import APIError
        
        mock_openai_client.chat.completions.create.side_effect = APIError("Persistent error")
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client), \
             patch('asyncio.sleep', new_callable=AsyncMock):
            
            result = await robust_openai_call(
                prompt="Test prompt",
                context="test",
                max_retries=2
            )
            
            assert result["success"] is False
            assert "Persistent error" in result["error"]
            assert mock_openai_client.chat.completions.create.call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_timeout(self, mock_openai_client):
        """Test OpenAI call with timeout."""
        mock_openai_client.chat.completions.create.side_effect = asyncio.TimeoutError()
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Test prompt",
                context="test",
                timeout=30
            )
            
            assert result["success"] is False
            assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_invalid_json_response(self, mock_openai_client):
        """Test handling of invalid JSON in response."""
        invalid_response = Mock()
        invalid_response.choices = [Mock()]
        invalid_response.choices[0].message = Mock()
        invalid_response.choices[0].message.content = "This is not valid JSON {invalid}"
        invalid_response.usage = Mock()
        invalid_response.usage.total_tokens = 50
        
        mock_openai_client.chat.completions.create.return_value = invalid_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Generate response",
                context="test"
            )
            
            # Should handle gracefully and try to extract or fallback
            assert "success" in result
            if result["success"]:
                assert "response" in result
            else:
                assert "error" in result
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_empty_response(self, mock_openai_client):
        """Test handling of empty response."""
        empty_response = Mock()
        empty_response.choices = [Mock()]
        empty_response.choices[0].message = Mock()
        empty_response.choices[0].message.content = ""
        empty_response.usage = Mock()
        empty_response.usage.total_tokens = 10
        
        mock_openai_client.chat.completions.create.return_value = empty_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Generate response",
                context="test"
            )
            
            assert result["success"] is False
            assert "empty" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_no_choices(self, mock_openai_client):
        """Test handling response with no choices."""
        no_choices_response = Mock()
        no_choices_response.choices = []
        no_choices_response.usage = Mock()
        no_choices_response.usage.total_tokens = 5
        
        mock_openai_client.chat.completions.create.return_value = no_choices_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Generate response",
                context="test"
            )
            
            assert result["success"] is False
            assert "no choices" in result["error"].lower() or "no response" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_model_parameter(self, mock_openai_client, sample_response):
        """Test OpenAI call with custom model parameter."""
        mock_openai_client.chat.completions.create.return_value = sample_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Test prompt",
                context="test",
                model="gpt-4-turbo"
            )
            
            assert result["success"] is True
            
            # Verify custom model was used
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gpt-4-turbo"
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_context_logging(self, mock_openai_client, sample_response):
        """Test that context is properly logged for debugging."""
        mock_openai_client.chat.completions.create.return_value = sample_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client), \
             patch('builtins.print') as mock_print:
            
            result = await robust_openai_call(
                prompt="Test prompt",
                context="meal_planning_debug"
            )
            
            assert result["success"] is True
            
            # Check that context was included in logging
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            assert any("meal_planning_debug" in str(call) for call in print_calls)
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_performance_tracking(self, mock_openai_client, sample_response):
        """Test that performance metrics are tracked."""
        mock_openai_client.chat.completions.create.return_value = sample_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            start_time = datetime.now()
            result = await robust_openai_call(
                prompt="Test prompt",
                context="performance_test"
            )
            end_time = datetime.now()
            
            assert result["success"] is True
            assert "tokens_used" in result
            assert result["tokens_used"] == 150
            
            # Check that the call completed within reasonable time
            duration = (end_time - start_time).total_seconds()
            assert duration < 30  # Should complete quickly in test
    
    @pytest.mark.asyncio
    async def test_robust_openai_call_large_response_handling(self, mock_openai_client):
        """Test handling of large responses."""
        large_response = Mock()
        large_response.choices = [Mock()]
        large_response.choices[0].message = Mock()
        # Create a large JSON response
        large_data = {"meals": [f"meal_{i}" for i in range(1000)]}
        large_response.choices[0].message.content = json.dumps(large_data)
        large_response.usage = Mock()
        large_response.usage.total_tokens = 5000
        
        mock_openai_client.chat.completions.create.return_value = large_response
        
        with patch('services.openai_service.get_openai_client', return_value=mock_openai_client):
            result = await robust_openai_call(
                prompt="Generate large meal plan",
                context="large_response_test"
            )
            
            assert result["success"] is True
            assert len(result["response"]["meals"]) == 1000
            assert result["tokens_used"] == 5000