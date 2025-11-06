import asyncio
from functools import wraps
import logging
from typing import Callable
from openai import APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)

def retry_openai(max_retries: int = 3, initial_delay: float = 1):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (RateLimitError, APIConnectionError) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise
                    
                    wait_time = delay * (2 ** attempt)  # exponential backoff
                    logger.warning(f"OpenAI API call failed. Retrying in {wait_time}s. Error: {str(e)}")
                    await asyncio.sleep(wait_time)
                except APIError as e:
                    logger.error(f"OpenAI API error: {str(e)}")
                    raise
                    
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator