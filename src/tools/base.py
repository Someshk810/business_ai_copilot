"""
Base tool interface and common functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""
    pass


class BaseTool(ABC):
    """
    Base class for all tools.
    
    Provides common functionality like:
    - Retry logic
    - Timeout handling
    - Error handling
    - Logging
    - Result caching
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes default
    
    @abstractmethod
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's core functionality.
        Must be implemented by subclasses.
        """
        pass
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with error handling and retry logic.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        start_time = time.time()
        
        try:
            logger.info(f"Executing tool: {self.name}")
            logger.debug(f"Tool parameters: {kwargs}")
            
            # Check cache
            cache_key = self._get_cache_key(**kwargs)
            if cache_key and cache_key in self.cache:
                cached_result, cached_time = self.cache[cache_key]
                age = time.time() - cached_time
                
                if age < self.cache_ttl:
                    logger.info(f"Cache hit for {self.name} (age: {age:.1f}s)")
                    cached_result['cached'] = True
                    cached_result['cache_age_seconds'] = age
                    return cached_result
            
            # Execute tool
            result = self._execute(**kwargs)
            
            # Add metadata
            execution_time = time.time() - start_time
            result['success'] = True
            result['tool_name'] = self.name
            result['execution_time_ms'] = int(execution_time * 1000)
            result['timestamp'] = datetime.now().isoformat()
            
            # Cache result
            if cache_key:
                self.cache[cache_key] = (result, time.time())
            
            logger.info(f"Tool {self.name} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool {self.name} failed: {str(e)}", exc_info=True)
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'tool_name': self.name,
                'execution_time_ms': int(execution_time * 1000),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_cache_key(self, **kwargs) -> Optional[str]:
        """
        Generate a cache key from parameters.
        Override for custom caching logic.
        """
        import hashlib
        import json
        
        try:
            # Sort kwargs for consistent hashing
            sorted_kwargs = json.dumps(kwargs, sort_keys=True)
            return hashlib.md5(sorted_kwargs.encode()).hexdigest()
        except (TypeError, ValueError):
            return None
    
    def clear_cache(self):
        """Clear the tool's cache."""
        self.cache.clear()
        logger.info(f"Cache cleared for {self.name}")


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            
            raise last_exception
        
        return wrapper
    return decorator