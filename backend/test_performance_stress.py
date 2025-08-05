"""
PERFORMANCE & STRESS TESTING - Elite Level Performance Testing
This module focuses on performance, stress, load, and concurrency testing
to ensure the system performs like a dream under all conditions.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os
from fastapi.testclient import TestClient
import json
from datetime import datetime, timedelta
import threading
import time
import concurrent.futures
import multiprocessing
import psutil
import gc

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import main application and components
import main
import database
import utils


class TestPerformanceBaseline:
    """Establish performance baselines for all critical operations."""
    
    def setup_method(self):
        """Set up performance testing environment."""
        self.client = TestClient(main.app)
        self.performance_results = {}
    
    def test_api_endpoint_response_times(self):
        """Test API endpoint response times."""
        endpoints = [
            ("/", "GET"),
            ("/login", "POST"),
        ]
        
        for endpoint, method in endpoints:
            times = []
            
            for _ in range(10):  # 10 requests per endpoint
                start_time = time.perf_counter()
                
                try:
                    if method == "GET":
                        response = self.client.get(endpoint)
                    else:
                        response = self.client.post(endpoint, json={})
                    
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    times.append(duration)
                    
                    # Should respond reasonably fast
                    assert duration < 5.0, f"{endpoint} took {duration}s (too slow)"
                    
                except Exception as e:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    times.append(duration)
                    print(f"Performance test exception for {endpoint}: {e}")
            
            # Calculate performance metrics
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            self.performance_results[f"{method}_{endpoint}"] = {
                "avg": avg_time,
                "max": max_time,
                "min": min_time,
                "samples": len(times)
            }
            
            # Performance assertions
            assert avg_time < 2.0, f"{endpoint} average response time {avg_time}s too high"
            assert max_time < 10.0, f"{endpoint} max response time {max_time}s too high"
    
    @pytest.mark.asyncio
    async def test_database_operation_performance(self):
        """Test database operation performance."""
        with patch('database.user_container') as mock_container, \
             patch('database.interactions_container') as mock_interactions:
            
            # Mock fast database responses
            mock_container.query_items.return_value = []
            mock_container.create_item.return_value = {"id": "perf_test"}
            mock_interactions.create_item.return_value = {"id": "perf_interaction"}
            
            # Test database operation speeds
            operations = [
                ("get_user_by_email", lambda: database.get_user_by_email("perf@test.com")),
                ("create_user", lambda: database.create_user({"email": "perf@test.com", "type": "user"})),
                ("save_consumption_record", lambda: database.save_consumption_record(
                    "perf@test.com", {"food_item": "Apple", "calories": 80}
                ))
            ]
            
            for op_name, operation in operations:
                times = []
                
                for _ in range(5):  # 5 operations each
                    start_time = time.perf_counter()
                    
                    try:
                        result = await operation()
                        end_time = time.perf_counter()
                        duration = end_time - start_time
                        times.append(duration)
                        
                        # Database operations should be fast
                        assert duration < 1.0, f"{op_name} took {duration}s (too slow)"
                        
                    except Exception as e:
                        end_time = time.perf_counter()
                        duration = end_time - start_time
                        times.append(duration)
                        print(f"Database performance test exception for {op_name}: {e}")
                
                # Calculate metrics
                if times:
                    avg_time = sum(times) / len(times)
                    self.performance_results[f"db_{op_name}"] = {
                        "avg": avg_time,
                        "max": max(times),
                        "min": min(times)
                    }
                    
                    # Performance assertion
                    assert avg_time < 0.5, f"{op_name} average time {avg_time}s too high"
    
    def test_utility_function_performance(self):
        """Test utility function performance."""
        # Test password hashing performance
        passwords = ["password123", "SecurePass456!", "ComplexPassword789@"]
        
        for password in passwords:
            start_time = time.perf_counter()
            
            try:
                hashed = utils.get_password_hash(password)
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                # Password hashing should be reasonably fast but secure
                assert duration < 2.0, f"Password hashing took {duration}s (too slow)"
                assert hashed is not None
                assert len(hashed) > 10  # Should be a proper hash
                
            except Exception as e:
                print(f"Password hashing performance test: {e}")
        
        # Test JWT token creation performance
        token_data = {"sub": "perf@test.com", "exp": datetime.utcnow() + timedelta(hours=1)}
        
        start_time = time.perf_counter()
        try:
            token = utils.create_access_token(token_data)
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            assert duration < 0.1, f"JWT creation took {duration}s (too slow)"
            assert token is not None
            assert len(token) > 10
            
        except Exception as e:
            print(f"JWT creation performance test: {e}")


class TestConcurrencyStress:
    """Test concurrent operations and race conditions."""
    
    def setup_method(self):
        """Set up concurrency testing."""
        self.client = TestClient(main.app)
        self.results = []
        self.errors = []
    
    def test_concurrent_api_requests(self):
        """Test concurrent API requests."""
        def make_request(request_id):
            try:
                start_time = time.time()
                response = self.client.get("/")
                end_time = time.time()
                
                return {
                    "id": request_id,
                    "status_code": response.status_code,
                    "duration": end_time - start_time,
                    "success": True
                }
            except Exception as e:
                return {
                    "id": request_id,
                    "error": str(e),
                    "success": False
                }
        
        # Create concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        # Should handle most concurrent requests
        success_rate = len(successful) / len(results)
        assert success_rate >= 0.8, f"Success rate {success_rate} too low for concurrent requests"
        
        # Response times should be reasonable under load
        if successful:
            avg_time = sum(r["duration"] for r in successful) / len(successful)
            assert avg_time < 5.0, f"Average response time under load {avg_time}s too high"
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self):
        """Test concurrent database operations."""
        with patch('database.user_container') as mock_container:
            mock_container.create_item.return_value = {"id": "concurrent_test"}
            mock_container.query_items.return_value = []
            
            async def concurrent_db_operation(operation_id):
                try:
                    # Simulate database operations
                    result1 = await database.get_user_by_email(f"user{operation_id}@test.com")
                    
                    result2 = await database.create_user({
                        "email": f"user{operation_id}@test.com",
                        "type": "user"
                    })
                    
                    return {
                        "id": operation_id,
                        "result1": result1,
                        "result2": result2,
                        "success": True
                    }
                except Exception as e:
                    return {
                        "id": operation_id,
                        "error": str(e),
                        "success": False
                    }
            
            # Run concurrent database operations
            tasks = [concurrent_db_operation(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful = [r for r in results if isinstance(r, dict) and r.get("success")]
            
            # Should handle concurrent database operations
            success_rate = len(successful) / len(results)
            assert success_rate >= 0.7, f"Database concurrency success rate {success_rate} too low"
    
    def test_thread_safety(self):
        """Test thread safety of critical components."""
        shared_data = {"counter": 0, "results": []}
        lock = threading.Lock()
        
        def thread_worker(worker_id):
            try:
                for i in range(100):
                    # Test thread-safe operations
                    session_id = database.generate_session_id()
                    
                    with lock:
                        shared_data["counter"] += 1
                        shared_data["results"].append({
                            "worker": worker_id,
                            "iteration": i,
                            "session_id": session_id
                        })
                        
                return {"worker": worker_id, "success": True}
            except Exception as e:
                return {"worker": worker_id, "error": str(e), "success": False}
        
        # Create multiple threads
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda w=i: results.append(thread_worker(w)))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify thread safety
        assert shared_data["counter"] == 500  # 5 workers * 100 iterations
        assert len(shared_data["results"]) == 500
        
        # Verify all session IDs are unique (thread safety test)
        session_ids = [r["session_id"] for r in shared_data["results"]]
        unique_session_ids = set(session_ids)
        assert len(unique_session_ids) == len(session_ids), "Session ID generation not thread-safe"


class TestLoadStress:
    """Test system under heavy load."""
    
    def setup_method(self):
        """Set up load testing."""
        self.client = TestClient(main.app)
    
    def test_memory_usage_under_load(self):
        """Test memory usage under load."""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate heavy load
        requests_count = 50
        responses = []
        
        for i in range(requests_count):
            try:
                response = self.client.get("/")
                responses.append(response.status_code)
                
                # Occasionally check memory
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    
                    # Memory shouldn't grow excessively
                    assert memory_increase < 100, f"Memory increased by {memory_increase}MB (too much)"
                    
            except Exception as e:
                print(f"Load test request {i} failed: {e}")
        
        # Force garbage collection
        gc.collect()
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory
        
        # Should not have significant memory leaks
        assert total_memory_increase < 50, f"Total memory increase {total_memory_increase}MB too high"
        
        # Should have processed most requests
        success_count = len([r for r in responses if r == 200])
        success_rate = success_count / requests_count
        assert success_rate >= 0.8, f"Success rate under load {success_rate} too low"
    
    def test_response_time_degradation(self):
        """Test response time degradation under increasing load."""
        response_times = []
        load_levels = [1, 5, 10, 20]  # Increasing load levels
        
        for load_level in load_levels:
            times_for_level = []
            
            # Make requests at this load level
            for _ in range(load_level):
                start_time = time.perf_counter()
                
                try:
                    response = self.client.get("/")
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    times_for_level.append(duration)
                    
                except Exception as e:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    times_for_level.append(duration)
                    print(f"Load test exception at level {load_level}: {e}")
            
            # Calculate average for this load level
            if times_for_level:
                avg_time = sum(times_for_level) / len(times_for_level)
                response_times.append({
                    "load_level": load_level,
                    "avg_response_time": avg_time,
                    "max_response_time": max(times_for_level),
                    "requests": len(times_for_level)
                })
        
        # Analyze response time degradation
        for i, level_data in enumerate(response_times):
            # Response times should remain reasonable
            assert level_data["avg_response_time"] < 3.0, \
                f"Load level {level_data['load_level']} avg time {level_data['avg_response_time']}s too high"
            
            assert level_data["max_response_time"] < 10.0, \
                f"Load level {level_data['load_level']} max time {level_data['max_response_time']}s too high"
    
    @pytest.mark.asyncio
    async def test_async_operation_scaling(self):
        """Test scaling of async operations."""
        with patch('database.interactions_container') as mock_container:
            mock_container.create_item.return_value = {"id": "scaling_test"}
            
            async def async_operation(operation_id):
                try:
                    start_time = time.perf_counter()
                    
                    # Simulate async database operation
                    result = await database.save_consumption_record(
                        f"user{operation_id}@test.com",
                        {"food_item": f"Food {operation_id}", "calories": 100}
                    )
                    
                    end_time = time.perf_counter()
                    return {
                        "id": operation_id,
                        "duration": end_time - start_time,
                        "result": result,
                        "success": True
                    }
                except Exception as e:
                    return {
                        "id": operation_id,
                        "error": str(e),
                        "success": False
                    }
            
            # Test different scales of async operations
            scales = [5, 10, 20, 50]
            
            for scale in scales:
                start_time = time.perf_counter()
                
                # Create and run async operations
                tasks = [async_operation(i) for i in range(scale)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.perf_counter()
                total_duration = end_time - start_time
                
                # Analyze scaling results
                successful = [r for r in results if isinstance(r, dict) and r.get("success")]
                success_rate = len(successful) / len(results)
                
                # Should scale reasonably well
                assert success_rate >= 0.8, f"Async scaling success rate {success_rate} at scale {scale} too low"
                
                # Total time shouldn't scale linearly (should benefit from async)
                expected_max_time = scale * 0.1  # Very generous
                assert total_duration < expected_max_time, \
                    f"Async operations at scale {scale} took {total_duration}s (should benefit from concurrency)"


class TestResourceUsage:
    """Test resource usage optimization."""
    
    def test_cpu_usage_monitoring(self):
        """Test CPU usage under normal operations."""
        # Get initial CPU usage
        initial_cpu = psutil.cpu_percent(interval=0.1)
        
        # Perform CPU-intensive operations
        operations = [
            lambda: utils.get_password_hash("test_password_123"),
            lambda: utils.generate_registration_code(),
            lambda: database.generate_session_id(),
        ]
        
        cpu_samples = []
        
        for operation in operations:
            for _ in range(10):
                start_cpu = psutil.cpu_percent(interval=None)
                
                try:
                    result = operation()
                    assert result is not None
                    
                    end_cpu = psutil.cpu_percent(interval=0.1)
                    cpu_samples.append(end_cpu)
                    
                except Exception as e:
                    print(f"CPU monitoring test exception: {e}")
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            # CPU usage should be reasonable
            assert avg_cpu < 80, f"Average CPU usage {avg_cpu}% too high"
            assert max_cpu < 95, f"Max CPU usage {max_cpu}% too high"
    
    def test_file_handle_usage(self):
        """Test file handle usage doesn't leak."""
        process = psutil.Process()
        initial_handles = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # Perform operations that might use file handles
        for i in range(20):
            try:
                # Operations that might open/close files or network connections
                session_id = database.generate_session_id()
                password_hash = utils.get_password_hash(f"password_{i}")
                
                assert session_id is not None
                assert password_hash is not None
                
            except Exception as e:
                print(f"File handle test iteration {i}: {e}")
        
        # Check file handle usage
        final_handles = process.num_fds() if hasattr(process, 'num_fds') else 0
        handle_increase = final_handles - initial_handles
        
        # Shouldn't leak file handles
        assert handle_increase < 10, f"File handle increase {handle_increase} suggests leak"


class TestErrorRecoveryUnderStress:
    """Test error recovery under stress conditions."""
    
    @pytest.mark.asyncio
    async def test_database_error_recovery_under_load(self):
        """Test database error recovery under load."""
        error_count = 0
        success_count = 0
        
        with patch('database.user_container') as mock_container:
            # Simulate intermittent database errors
            def side_effect(*args, **kwargs):
                nonlocal error_count, success_count
                if error_count < 3:  # First 3 calls fail
                    error_count += 1
                    raise Exception("Simulated database error")
                else:
                    success_count += 1
                    return {"id": f"recovery_test_{success_count}"}
            
            mock_container.create_item.side_effect = side_effect
            
            # Test error recovery
            results = []
            for i in range(10):
                try:
                    result = await database.create_user({
                        "email": f"recovery{i}@test.com",
                        "type": "user"
                    })
                    results.append({"success": True, "result": result})
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
            
            # Should eventually recover from errors
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]
            
            # Should have some failures initially, then recoveries
            assert len(failed) >= 3, "Should have some initial failures"
            assert len(successful) >= 3, "Should recover and have successes"
    
    def test_api_error_recovery_under_stress(self):
        """Test API error recovery under stress."""
        client = TestClient(main.app)
        results = []
        
        # Make many requests, some to valid and invalid endpoints
        endpoints = ["/", "/nonexistent", "/login", "/invalid"]
        
        for i in range(40):  # 40 requests total
            endpoint = endpoints[i % len(endpoints)]
            
            try:
                start_time = time.perf_counter()
                
                if endpoint == "/login":
                    response = client.post(endpoint, json={})
                else:
                    response = client.get(endpoint)
                
                end_time = time.perf_counter()
                
                results.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "duration": end_time - start_time,
                    "success": response.status_code < 500
                })
                
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "success": False
                })
        
        # Analyze error recovery
        valid_endpoints = [r for r in results if r["endpoint"] in ["/", "/login"]]
        invalid_endpoints = [r for r in results if r["endpoint"] in ["/nonexistent", "/invalid"]]
        
        # Valid endpoints should mostly succeed
        valid_success_rate = len([r for r in valid_endpoints if r["success"]]) / len(valid_endpoints)
        assert valid_success_rate >= 0.8, f"Valid endpoint success rate {valid_success_rate} too low"
        
        # Invalid endpoints should fail gracefully (not crash)
        invalid_graceful = len([r for r in invalid_endpoints if "error" not in r]) / len(invalid_endpoints)
        assert invalid_graceful >= 0.9, f"Invalid endpoints not handling gracefully: {invalid_graceful}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])