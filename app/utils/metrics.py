from functools import wraps
from typing import Callable, Set
import logging
import time

logger = logging.getLogger(__name__)

# Simple in-memory active users tracking
ACTIVE_USERS: Set[str] = set()

def track_request_metrics():
    async def metrics_middleware(request, call_next):
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            logger.info(f"Request: {method} {endpoint} - Status: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {method} {endpoint} - Error: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            logger.info(f"Request duration: {duration:.3f}s - {method} {endpoint}")
    
    return metrics_middleware

def track_openai_metrics():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            endpoint = func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                logger.info(f"OpenAI API call succeeded: {endpoint}")
                return result
            except Exception as e:
                logger.error(f"OpenAI API call failed: {endpoint} - Error: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                logger.info(f"OpenAI API call duration: {duration:.3f}s - {endpoint}")
        
        return wrapper
    return decorator

def add_active_user(user_id: str):
    """Add a user to the active users set"""
    ACTIVE_USERS.add(user_id)
    logger.info(f"User {user_id} became active. Total active users: {len(ACTIVE_USERS)}")

def remove_active_user(user_id: str):
    """Remove a user from the active users set"""
    ACTIVE_USERS.discard(user_id)
    logger.info(f"User {user_id} became inactive. Total active users: {len(ACTIVE_USERS)}")