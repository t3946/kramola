import os
import redis
from pathlib import Path
from typing import Optional


def get_redis_host():
    """
    Automatically determines Redis host based on execution context.
    Priority:
    1. REDIS_HOST environment variable (if set)
    2. Check if running in Docker (/.dockerenv exists) -> use 'redis'
    3. Otherwise -> use 'localhost'
    """
    # Check environment variable first
    env_host = os.environ.get('REDIS_HOST')
    if env_host:
        return env_host
    
    # Check if running inside Docker container
    if Path('/.dockerenv').exists():
        return 'redis'
    
    # Default to localhost for local execution
    return 'localhost'


def get_redis_config():
    """
    Get Redis connection configuration.
    Returns tuple: (host, port, db)
    """
    host = get_redis_host()
    port = int(os.environ.get('REDIS_PORT', 6379))
    db = int(os.environ.get('REDIS_DB', 0))
    return host, port, db


def get_redis_connection_pool(
    db: Optional[int] = None,
    decode_responses: bool = False,
    **kwargs
) -> redis.ConnectionPool:
    """
    Get Redis connection pool with automatic host detection.
    
    Args:
        db: Database number. If None, uses REDIS_DB env var or 0.
        decode_responses: If True, responses are decoded to strings instead of bytes.
        **kwargs: Additional arguments passed to ConnectionPool.
    
    Returns:
        redis.ConnectionPool instance
    """
    host = get_redis_host()
    port = int(os.environ.get('REDIS_PORT', 6379))
    
    if db is None:
        db = int(os.environ.get('REDIS_DB', 0))
    
    return redis.ConnectionPool(
        host=host,
        port=port,
        db=db,
        decode_responses=decode_responses,
        **kwargs
    )


def get_redis_connection(
    db: Optional[int] = None,
    decode_responses: bool = False,
    use_pool: bool = True,
    **kwargs
) -> redis.Redis:
    """
    Get Redis connection with automatic host detection.
    This is the main utility function - use this everywhere instead of creating Redis connections manually.
    
    Args:
        db: Database number. If None, uses REDIS_DB env var or 0.
        decode_responses: If True, responses are decoded to strings instead of bytes.
        use_pool: If True, uses connection pool for better performance (recommended).
        **kwargs: Additional arguments passed to Redis or ConnectionPool.
    
    Returns:
        redis.Redis instance
    
    Examples:
        # Basic usage (default DB, bytes responses)
        r = get_redis_connection()
        
        # With string decoding
        r = get_redis_connection(decode_responses=True)
        
        # Specific database
        r = get_redis_connection(db=1)
        
        # Custom database with string decoding
        r = get_redis_connection(db=1, decode_responses=True)
    """
    if use_pool:
        pool = get_redis_connection_pool(db=db, decode_responses=decode_responses, **kwargs)
        return redis.Redis(connection_pool=pool)
    else:
        host = get_redis_host()
        port = int(os.environ.get('REDIS_PORT', 6379))
        
        if db is None:
            db = int(os.environ.get('REDIS_DB', 0))
        
        return redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=decode_responses,
            **kwargs
        )


# Get Redis connection parameters (for backward compatibility)
REDIS_HOST, REDIS_PORT, REDIS_DB = get_redis_config()

# Default connection pool (for backward compatibility)
POOL = get_redis_connection_pool()

# Default redis connection (for backward compatibility)
r = get_redis_connection()
