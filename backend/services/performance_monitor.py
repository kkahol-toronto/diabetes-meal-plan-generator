"""
Performance monitoring service to track optimization improvements.
"""
import time
from typing import Dict, List
from datetime import datetime, timedelta
from functools import wraps
import asyncio

class PerformanceMonitor:
    """Monitor API performance and optimization impact"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = datetime.utcnow()
        
    def time_endpoint(self, endpoint_name: str):
        """Decorator to time endpoint execution"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    self._record_metric(endpoint_name, duration, True)
                    
                    # Log slow endpoints
                    if duration > 2.0:  # More than 2 seconds is slow
                        print(f"[PERFORMANCE] SLOW ENDPOINT: {endpoint_name} took {duration:.2f}s")
                    elif duration < 0.5:  # Less than 0.5s is fast
                        print(f"[PERFORMANCE] FAST ENDPOINT: {endpoint_name} took {duration:.3f}s")
                    
                    return result
                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    self._record_metric(endpoint_name, duration, False)
                    raise
            return wrapper
        return decorator
    
    def _record_metric(self, endpoint: str, duration: float, success: bool):
        """Record performance metric"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = {
                'total_calls': 0,
                'total_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'success_count': 0,
                'error_count': 0,
                'recent_durations': []
            }
        
        metric = self.metrics[endpoint]
        metric['total_calls'] += 1
        metric['total_duration'] += duration
        metric['min_duration'] = min(metric['min_duration'], duration)
        metric['max_duration'] = max(metric['max_duration'], duration)
        
        if success:
            metric['success_count'] += 1
        else:
            metric['error_count'] += 1
        
        # Keep only recent 10 durations for trend analysis
        metric['recent_durations'].append(duration)
        if len(metric['recent_durations']) > 10:
            metric['recent_durations'].pop(0)
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        summary = {
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
            'endpoints': {}
        }
        
        for endpoint, metric in self.metrics.items():
            avg_duration = metric['total_duration'] / metric['total_calls'] if metric['total_calls'] > 0 else 0
            recent_avg = sum(metric['recent_durations']) / len(metric['recent_durations']) if metric['recent_durations'] else 0
            success_rate = (metric['success_count'] / metric['total_calls'] * 100) if metric['total_calls'] > 0 else 0
            
            summary['endpoints'][endpoint] = {
                'calls': metric['total_calls'],
                'avg_duration': f"{avg_duration:.3f}s",
                'recent_avg_duration': f"{recent_avg:.3f}s",
                'min_duration': f"{metric['min_duration']:.3f}s",
                'max_duration': f"{metric['max_duration']:.3f}s",
                'success_rate': f"{success_rate:.1f}%",
                'performance_grade': self._get_performance_grade(recent_avg)
            }
        
        return summary
    
    def _get_performance_grade(self, avg_duration: float) -> str:
        """Grade endpoint performance"""
        if avg_duration < 0.2:
            return "A+ (Excellent)"
        elif avg_duration < 0.5:
            return "A (Very Good)"
        elif avg_duration < 1.0:
            return "B (Good)"
        elif avg_duration < 2.0:
            return "C (Fair)"
        else:
            return "D (Needs Optimization)"
    
    def get_optimization_report(self) -> List[str]:
        """Get optimization recommendations"""
        recommendations = []
        
        for endpoint, metric in self.metrics.items():
            avg_duration = metric['total_duration'] / metric['total_calls'] if metric['total_calls'] > 0 else 0
            
            if avg_duration > 2.0:
                recommendations.append(f"🔴 CRITICAL: {endpoint} is very slow ({avg_duration:.2f}s average)")
            elif avg_duration > 1.0:
                recommendations.append(f"🟡 WARNING: {endpoint} is slow ({avg_duration:.2f}s average)")
            elif avg_duration < 0.3:
                recommendations.append(f"🟢 OPTIMIZED: {endpoint} is very fast ({avg_duration:.3f}s average)")
        
        return recommendations

# Global performance monitor instance
perf_monitor = PerformanceMonitor()

# Decorator for easy use
def track_performance(endpoint_name: str):
    """Decorator to track endpoint performance"""
    return perf_monitor.time_endpoint(endpoint_name)