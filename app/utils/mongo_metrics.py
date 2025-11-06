from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

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

_connection_count = 0

def increment_connections():
    global _connection_count
    _connection_count += 1
    logger.info(f"MongoDB connections: {_connection_count}")

def decrement_connections():
    global _connection_count
    _connection_count = max(0, _connection_count - 1)
    logger.info(f"MongoDB connections: {_connection_count}")

def get_connection_count():
    return _connection_count