from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'active_users_total',
    'Number of active users'
)

OPENAI_API_CALLS = Counter(
    'openai_api_calls_total',
    'Total OpenAI API calls',
    ['endpoint', 'status']
)

OPENAI_API_LATENCY = Histogram(
    'openai_api_duration_seconds',
    'OpenAI API call latency',
    ['endpoint']
)

def track_request_metrics():
    async def metrics_middleware(request, call_next):
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            return response
        except Exception as e:
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    return metrics_middleware

def track_openai_metrics():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            endpoint = func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                OPENAI_API_CALLS.labels(
                    endpoint=endpoint,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                OPENAI_API_CALLS.labels(
                    endpoint=endpoint,
                    status='error'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                OPENAI_API_LATENCY.labels(
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator