from prometheus_client import Counter, Histogram, Summary, Gauge
from functools import wraps
import time

MONGO_OPERATIONS = Counter(
    'mongodb_operations_total',
    'Total MongoDB operations',
    ['operation', 'collection', 'status']
)

MONGO_OPERATION_LATENCY = Histogram(
    'mongodb_operation_duration_seconds',
    'MongoDB operation latency',
    ['operation', 'collection']
)

MONGO_CONNECTIONS = Gauge(
    'mongodb_connections',
    'Number of active MongoDB connections'
)

def track_mongo_operation(collection: str, operation: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                MONGO_OPERATIONS.labels(
                    operation=operation,
                    collection=collection,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                MONGO_OPERATIONS.labels(
                    operation=operation,
                    collection=collection,
                    status='error'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                MONGO_OPERATION_LATENCY.labels(
                    operation=operation,
                    collection=collection
                ).observe(duration)
        return wrapper
    return decorator