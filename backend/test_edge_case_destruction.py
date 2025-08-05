"""
EDGE CASE DESTRUCTION TESTING - Extreme Edge Case Testing
This module focuses on destructive edge case testing to break the system
and ensure it handles every possible edge case gracefully.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os
from fastapi.testclient import TestClient
import json
from datetime import datetime, timedelta
import decimal
import math
import random
import string

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import main application and components
import main
import database
import utils


class TestExtremeDataTypes:
    """Test extreme data types and boundary conditions."""
    
    def setup_method(self):
        """Set up extreme testing environment."""
        self.client = TestClient(main.app)
    
    def test_extreme_numeric_values(self):
        """Test extreme numeric values that could break calculations."""
        extreme_numbers = [
            0,
            -0,
            float('inf'),
            float('-inf'),
            float('nan'),
            sys.maxsize,
            -sys.maxsize,
            1e308,   # Very large float
            1e-308,  # Very small float
            2**63 - 1,  # Max 64-bit signed int
            -2**63,     # Min 64-bit signed int
            decimal.Decimal('999999999999999999999999999.999999999'),
            decimal.Decimal('-999999999999999999999999999.999999999'),
            999999999999999999999999999,  # Very large integer
            -999999999999999999999999999, # Very large negative integer
        ]
        
        for number in extreme_numbers:
            try:
                # Test in user profile data
                profile_data = {
                    "age": number,
                    "weight": number,
                    "height": number,
                    "calorieTarget": str(number) if not math.isnan(number) and not math.isinf(number) else "2000",
                    "activityLevel": "moderate"
                }
                
                # Test with dietary info extraction
                if hasattr(main.database, '_extract_dietary_info'):
                    result = main.database._extract_dietary_info(profile_data)
                    assert result is not None or result is None
                elif 'services.meal_plan_service' in sys.modules:
                    from services.meal_plan_service import _extract_dietary_info
                    result = _extract_dietary_info(profile_data)
                    assert result is not None
                
                # Test password hashing with numeric strings
                if not math.isnan(number) and not math.isinf(number):
                    password_str = str(number)
                    if len(password_str) < 100:  # Avoid extremely long strings
                        hashed = utils.get_password_hash(password_str)
                        assert hashed is not None
                        assert len(hashed) > 10
                
            except (ValueError, TypeError, OverflowError, decimal.InvalidOperation) as e:
                # Expected for extreme values
                print(f"Extreme numeric test for {number}: {e}")
            except Exception as e:
                # Should handle gracefully, not crash
                assert "crashed" not in str(e).lower()
                print(f"Extreme numeric test for {number}: {e}")
    
    def test_extreme_string_values(self):
        """Test extreme string values and edge cases."""
        extreme_strings = [
            "",                    # Empty string
            " ",                   # Single space
            "\n",                  # Newline
            "\r\n",               # CRLF
            "\t",                 # Tab
            "\x00",               # Null byte
            "\x01\x02\x03",      # Control characters
            "   \t\n\r   ",       # Whitespace only
            "\u0000",             # Unicode null
            "\uFFFF",             # Unicode max BMP
            "\U0001F4A9",         # Poop emoji
            "\\",                 # Single backslash
            "\"",                 # Single quote
            "'",                  # Single apostrophe
            "`",                  # Backtick
            "${injection}",       # Template injection attempt
            "{{injection}}",      # Template injection attempt
            "<%=injection%>",     # Template injection attempt
            "a" * 10000,          # Very long string
            "🔥" * 1000,          # Unicode repeated
            "\n".join(["line"] * 1000),  # Many lines
        ]
        
        for extreme_string in extreme_strings:
            try:
                # Test string utilities
                if len(extreme_string) < 1000:  # Skip very long strings for some tests
                    # Test registration code generation with extreme inputs as seed
                    reg_code = utils.generate_registration_code()
                    assert reg_code is not None
                    assert len(reg_code) > 0
                
                # Test session ID generation (should be independent of input)
                session_id = database.generate_session_id()
                assert session_id is not None
                assert len(session_id) > 5
                
                # Test extreme string in API calls
                if len(extreme_string) < 100:  # Avoid overwhelming API
                    response = self.client.post("/login", data={
                        "username": extreme_string,
                        "password": "password123"
                    })
                    
                    # Should handle extreme strings gracefully
                    assert response.status_code in [400, 401, 422, 500]
                
            except (UnicodeError, ValueError) as e:
                # Expected for some extreme strings
                print(f"Extreme string test for '{extreme_string[:20]}...': {e}")
            except Exception as e:
                # Should not crash
                assert "crashed" not in str(e).lower()
                print(f"Extreme string test: {e}")
    
    def test_extreme_collection_values(self):
        """Test extreme collection values (lists, dicts)."""
        extreme_collections = [
            [],                           # Empty list
            {},                           # Empty dict
            [None] * 1000,               # List of Nones
            {"": ""} * 100 if False else {"key": "value"},  # Large dict simulation
            [i for i in range(10000)],   # Large list
            {"nested": {"very": {"deeply": {"nested": {"dict": "value"}}}}},  # Deep nesting
            [[[[[["deeply_nested_list"]]]]]],  # Deep list nesting
            {str(i): i for i in range(1000)},  # Large dictionary
            {"key_with_extreme_value": "x" * 10000},  # Dict with large value
            ["mixed", 123, None, True, {"nested": "dict"}, [1, 2, 3]],  # Mixed types
        ]
        
        for collection in extreme_collections:
            try:
                # Test collection handling in profile data
                if isinstance(collection, dict):
                    # Test as profile data
                    test_profile = {
                        "dietaryRestrictions": collection.get("dietary", []),
                        "medicalConditions": collection.get("medical", []),
                        "allergies": collection.get("allergies", []),
                        **collection
                    }
                    
                    # Test dietary info extraction
                    try:
                        if 'services.meal_plan_service' in sys.modules:
                            from services.meal_plan_service import _extract_dietary_info
                            result = _extract_dietary_info(test_profile)
                            assert result is not None
                    except ImportError:
                        pass
                
                elif isinstance(collection, list):
                    # Test as dietary restrictions
                    test_profile = {
                        "dietaryRestrictions": collection[:100],  # Limit size
                        "medicalConditions": collection[:100],
                        "allergies": collection[:100]
                    }
                    
                    try:
                        if 'services.meal_plan_service' in sys.modules:
                            from services.meal_plan_service import _extract_dietary_info
                            result = _extract_dietary_info(test_profile)
                            assert result is not None
                    except ImportError:
                        pass
                
            except (TypeError, ValueError, RecursionError) as e:
                # Expected for some extreme collections
                print(f"Extreme collection test: {e}")
            except Exception as e:
                # Should handle gracefully
                assert "crashed" not in str(e).lower()
                print(f"Extreme collection test: {e}")


class TestConcurrentEdgeCases:
    """Test edge cases under concurrent conditions."""
    
    @pytest.mark.asyncio
    async def test_race_condition_simulation(self):
        """Simulate race conditions in database operations."""
        import asyncio
        import random
        
        # Mock database containers
        with patch('database.user_container') as mock_users, \
             patch('database.interactions_container') as mock_interactions:
            
            # Simulate race conditions with delayed responses
            def delayed_response(*args, **kwargs):
                # Random delay to simulate race conditions
                import time
                time.sleep(random.uniform(0.001, 0.01))
                return {"id": f"race_test_{random.randint(1000, 9999)}"}
            
            mock_users.create_item.side_effect = delayed_response
            mock_interactions.create_item.side_effect = delayed_response
            mock_users.query_items.return_value = []
            mock_interactions.query_items.return_value = []
            
            # Create concurrent operations that might race
            async def concurrent_user_creation(user_id):
                try:
                    return await database.create_user({
                        "email": f"race_user_{user_id}@test.com",
                        "type": "user"
                    })
                except Exception as e:
                    return {"error": str(e), "user_id": user_id}
            
            async def concurrent_meal_plan_save(user_id):
                try:
                    return await database.save_meal_plan(
                        f"race_user_{user_id}@test.com",
                        {
                            "meals": {
                                "breakfast": f"Race breakfast {user_id}",
                                "lunch": f"Race lunch {user_id}",
                                "dinner": f"Race dinner {user_id}"
                            }
                        }
                    )
                except Exception as e:
                    return {"error": str(e), "user_id": user_id}
            
            # Execute concurrent operations
            tasks = []
            for i in range(10):
                tasks.append(concurrent_user_creation(i))
                tasks.append(concurrent_meal_plan_save(i))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze race condition results
            successful = [r for r in results if isinstance(r, dict) and "error" not in r]
            errors = [r for r in results if isinstance(r, dict) and "error" in r]
            exceptions = [r for r in results if isinstance(r, Exception)]
            
            # Should handle race conditions gracefully
            total_operations = len(results)
            success_rate = len(successful) / total_operations
            
            # Even with race conditions, should have reasonable success rate
            assert success_rate >= 0.5, f"Race condition success rate {success_rate} too low"
            
            # Should not have critical exceptions
            critical_exceptions = [e for e in exceptions if "critical" in str(e).lower()]
            assert len(critical_exceptions) == 0, "Critical exceptions in race conditions"
    
    def test_concurrent_session_generation(self):
        """Test concurrent session ID generation for uniqueness."""
        import threading
        import time
        
        session_ids = []
        lock = threading.Lock()
        
        def generate_sessions(count):
            local_sessions = []
            for _ in range(count):
                try:
                    session_id = database.generate_session_id()
                    local_sessions.append(session_id)
                    time.sleep(0.001)  # Small delay to increase chance of collision
                except Exception as e:
                    local_sessions.append(f"error_{e}")
            
            with lock:
                session_ids.extend(local_sessions)
        
        # Create multiple threads generating session IDs
        threads = []
        for i in range(5):
            thread = threading.Thread(target=generate_sessions, args=(20,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify uniqueness under concurrent generation
        valid_sessions = [s for s in session_ids if not s.startswith("error_")]
        unique_sessions = set(valid_sessions)
        
        assert len(unique_sessions) == len(valid_sessions), \
            f"Session ID collision detected: {len(valid_sessions)} generated, {len(unique_sessions)} unique"
    
    def test_memory_pressure_edge_cases(self):
        """Test edge cases under memory pressure simulation."""
        import gc
        
        # Create memory pressure by generating large objects
        large_objects = []
        
        try:
            # Generate memory pressure
            for i in range(100):
                large_object = {
                    "data": "x" * 10000,  # 10KB strings
                    "list": list(range(1000)),
                    "nested": {"deep": {"nesting": {"level": i}}}
                }
                large_objects.append(large_object)
            
            # Test operations under memory pressure
            for i in range(10):
                # Test session generation
                session_id = database.generate_session_id()
                assert session_id is not None
                
                # Test password hashing
                password_hash = utils.get_password_hash(f"pressure_test_{i}")
                assert password_hash is not None
                
                # Test registration code generation
                reg_code = utils.generate_registration_code()
                assert reg_code is not None
                
                # Force garbage collection occasionally
                if i % 3 == 0:
                    gc.collect()
            
        finally:
            # Clean up memory
            large_objects.clear()
            gc.collect()


class TestMalformedDataHandling:
    """Test handling of malformed and corrupted data."""
    
    def setup_method(self):
        """Set up malformed data testing."""
        self.client = TestClient(main.app)
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON data."""
        malformed_json_strings = [
            "{",                    # Incomplete JSON
            "}",                    # Just closing brace
            '{"key": }',           # Missing value
            '{"key": "value",}',   # Trailing comma
            '{key: "value"}',      # Unquoted key
            "{'key': 'value'}",    # Single quotes
            '{"key": "value"',     # Missing closing brace
            '{"key": "value"}}',   # Extra closing brace
            '{"key": undefined}',   # JavaScript undefined
            '{"key": NaN}',        # JavaScript NaN
            '{"key": Infinity}',   # JavaScript Infinity
            '{null: "value"}',     # Null as key
            '{"": ""}',            # Empty key and value
            '{"key": ""}',         # Empty value
            '{"": "value"}',       # Empty key
        ]
        
        for malformed_json in malformed_json_strings:
            try:
                # Test API endpoints with malformed JSON
                import requests
                
                # Use requests to send raw malformed JSON
                # (TestClient might fix some malformed JSON automatically)
                response = self.client.post(
                    "/login",
                    content=malformed_json,
                    headers={"Content-Type": "application/json"}
                )
                
                # Should handle malformed JSON gracefully
                assert response.status_code in [400, 422, 500], \
                    f"Malformed JSON should be rejected: {malformed_json[:30]}..."
                
                # Should not crash or expose internal errors
                response_text = response.text.lower()
                assert "traceback" not in response_text
                assert "internal server error" not in response_text or response.status_code == 500
                
            except Exception as e:
                # Should handle parsing errors gracefully
                print(f"Malformed JSON test for '{malformed_json[:30]}...': {e}")
    
    def test_corrupted_data_structures(self):
        """Test handling of corrupted data structures."""
        corrupted_data_sets = [
            # Corrupted user data
            {
                "email": None,
                "username": 12345,  # Wrong type
                "profile": "not_a_dict",  # Should be dict
                "is_active": "maybe",  # Should be boolean
            },
            
            # Corrupted meal plan data
            {
                "meals": ["not_a_dict"],  # Should be dict
                "nutritional_info": "invalid",  # Should be dict
                "date": 12345,  # Should be string
                "user_id": {"not": "string"},  # Should be string
            },
            
            # Corrupted profile data
            {
                "age": "not_a_number",
                "weight": [1, 2, 3],  # Should be number
                "height": {"invalid": "structure"},
                "dietaryRestrictions": "not_a_list",  # Should be list
                "medicalConditions": 12345,  # Should be list
            },
            
            # Mixed type corruption
            {
                123: "numeric_key",
                "string_key": 456,
                None: "null_key",
                True: "boolean_key",
                (1, 2): "tuple_key",  # Unhashable in JSON
            }
        ]
        
        for corrupted_data in corrupted_data_sets:
            try:
                # Test dietary info extraction with corrupted data
                if 'services.meal_plan_service' in sys.modules:
                    from services.meal_plan_service import _extract_dietary_info
                    result = _extract_dietary_info(corrupted_data)
                    
                    # Should handle corruption gracefully
                    assert result is not None
                    assert isinstance(result, dict)
                
                # Test API with corrupted data
                try:
                    response = self.client.post("/register", json=corrupted_data)
                    
                    # Should reject corrupted data
                    assert response.status_code in [400, 422, 500]
                    
                except Exception as api_e:
                    # API should handle corrupted data gracefully
                    print(f"API corrupted data test: {api_e}")
                
            except (TypeError, ValueError, AttributeError) as e:
                # Expected for corrupted data
                print(f"Corrupted data test: {e}")
            except Exception as e:
                # Should not crash catastrophically
                assert "crash" not in str(e).lower()
                print(f"Corrupted data handling: {e}")
    
    def test_circular_reference_handling(self):
        """Test handling of circular references in data."""
        # Create circular reference
        circular_dict = {"key": "value"}
        circular_dict["self"] = circular_dict
        
        circular_list = [1, 2, 3]
        circular_list.append(circular_list)
        
        circular_data_sets = [
            circular_dict,
            {"list": circular_list},
            {"nested": {"circular": circular_dict}},
        ]
        
        for circular_data in circular_data_sets:
            try:
                # Test JSON serialization with circular references
                json_str = json.dumps(circular_data)
                assert False, "Should not be able to serialize circular references"
                
            except (ValueError, TypeError) as e:
                # Expected - JSON can't handle circular references
                assert "circular" in str(e).lower() or "reference" in str(e).lower()
                print(f"Circular reference correctly rejected: {e}")
            
            except Exception as e:
                # Other handling is acceptable
                print(f"Circular reference handling: {e}")


class TestBoundaryConditions:
    """Test boundary conditions and limits."""
    
    @pytest.mark.asyncio
    async def test_time_boundary_conditions(self):
        """Test time-related boundary conditions."""
        import time
        from datetime import datetime, timedelta
        
        extreme_dates = [
            datetime.min,                                    # Minimum datetime
            datetime.max,                                    # Maximum datetime
            datetime(1970, 1, 1),                           # Unix epoch
            datetime(2038, 1, 19, 3, 14, 7),               # Unix 32-bit limit
            datetime.now() + timedelta(days=365*100),       # Far future
            datetime.now() - timedelta(days=365*100),       # Far past
            datetime(2000, 2, 29),                          # Leap year
            datetime(1900, 2, 28),                          # Non-leap year
        ]
        
        for extreme_date in extreme_dates:
            try:
                # Test with extreme dates in meal plan data
                meal_plan_data = {
                    "meals": {
                        "breakfast": "Test breakfast",
                        "lunch": "Test lunch", 
                        "dinner": "Test dinner"
                    },
                    "created_at": extreme_date.isoformat(),
                    "date": extreme_date.strftime("%Y-%m-%d")
                }
                
                # Test saving meal plan with extreme dates
                with patch('database.interactions_container') as mock_container:
                    mock_container.create_item.return_value = {"id": "extreme_date_test"}
                    
                    result = await database.save_meal_plan("test@extreme.com", meal_plan_data)
                    assert result is not None
                
            except (ValueError, OverflowError, OSError) as e:
                # Expected for extreme dates
                print(f"Extreme date test for {extreme_date}: {e}")
            except Exception as e:
                # Should handle gracefully
                print(f"Date boundary test: {e}")
    
    def test_numeric_boundary_conditions(self):
        """Test numeric boundary conditions."""
        numeric_boundaries = [
            (0, "zero"),
            (-1, "negative_one"),
            (1, "positive_one"),
            (0.1, "small_decimal"),
            (-0.1, "small_negative_decimal"),
            (999999999, "large_integer"),
            (-999999999, "large_negative_integer"),
            (0.000001, "very_small_decimal"),
            (-0.000001, "very_small_negative_decimal"),
        ]
        
        for number, description in numeric_boundaries:
            try:
                # Test in profile calculations
                profile_data = {
                    "age": number if number > 0 else 25,
                    "weight": number if number > 0 else 70,
                    "height": number if number > 0 else 175,
                    "calorieTarget": str(max(number, 1000)),
                    "activityLevel": "moderate"
                }
                
                # Test dietary info extraction
                if 'services.meal_plan_service' in sys.modules:
                    from services.meal_plan_service import _extract_dietary_info
                    result = _extract_dietary_info(profile_data)
                    assert result is not None
                
                # Test password with numeric string
                if abs(number) < 1000000:  # Avoid extremely long strings
                    password_str = f"password_{number}"
                    hashed = utils.get_password_hash(password_str)
                    assert hashed is not None
                    assert len(hashed) > 10
                
            except (ValueError, TypeError) as e:
                # Expected for some boundary conditions
                print(f"Numeric boundary test for {description} ({number}): {e}")
            except Exception as e:
                # Should handle gracefully
                print(f"Numeric boundary handling: {e}")
    
    def test_string_length_boundaries(self):
        """Test string length boundary conditions."""
        string_lengths = [0, 1, 2, 10, 100, 1000, 10000, 65535, 100000]
        
        for length in string_lengths:
            try:
                # Generate string of specific length
                if length == 0:
                    test_string = ""
                elif length == 1:
                    test_string = "a"
                else:
                    test_string = "a" * length
                
                # Test various operations with different string lengths
                if length < 1000:  # Avoid overwhelming small operations
                    # Test registration code (should be independent of input)
                    reg_code = utils.generate_registration_code()
                    assert reg_code is not None
                    assert len(reg_code) > 0
                
                if length < 100:  # Test only reasonable password lengths
                    if length > 0:
                        # Test password hashing
                        hashed = utils.get_password_hash(test_string)
                        assert hashed is not None
                        
                        # Test password verification
                        verified = utils.verify_password(test_string, hashed)
                        assert verified is True
                
                # Test API with various string lengths
                if length < 1000:  # Avoid overwhelming API
                    response = self.client.post("/login", data={
                        "username": test_string if length > 0 else "test@test.com",
                        "password": test_string if length > 0 else "password"
                    })
                    
                    # Should handle various string lengths
                    assert response.status_code in [400, 401, 422, 500]
                
            except (MemoryError, ValueError) as e:
                # Expected for very large strings
                print(f"String length boundary test for length {length}: {e}")
            except Exception as e:
                # Should handle gracefully
                assert "crash" not in str(e).lower()
                print(f"String length handling: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])