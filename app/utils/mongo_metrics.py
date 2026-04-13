from functools import wraps
import time
import threading
from loguru import logger

_connection_count = 0
_connection_lock = threading.Lock()

def track_mongo_operation(collection: str, operation: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                logger.info(f"MongoDB operation success: {operation} on {collection}")
                return result
            except Exception as e:
                logger.error(f"MongoDB operation failed: {operation} on {collection} - Error: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                logger.info(f"MongoDB operation duration: {duration:.3f}s - {operation} on {collection}")
        return wrapper
    return decorator

def increment_connections():
    global _connection_count
    with _connection_lock:
        _connection_count += 1
        logger.info(f"MongoDB connections: {_connection_count}")

def decrement_connections():
    global _connection_count
    with _connection_lock:
        _connection_count = max(0, _connection_count - 1)
        logger.info(f"MongoDB connections: {_connection_count}")

def get_connection_count():
    with _connection_lock:
        return _connection_count