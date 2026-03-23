"""Rate limiting utilities for GCP operations."""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from threading import Lock
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(self, capacity: float, refill_rate: float):
        """Initialize token bucket.

        Args:
            capacity: Maximum number of tokens (burst capacity).
            refill_rate: Tokens added per second.
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()

    def consume(self, tokens: float = 1.0) -> bool:
        """Try to consume tokens.

        Args:
            tokens: Number of tokens to consume.

        Returns:
            True if tokens were consumed, False if insufficient tokens.
        """
        with self.lock:
            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
            self.last_refill = now

            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> float:
        """Get current number of available tokens.

        Returns:
            Number of available tokens.
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
            self.last_refill = now
            return self.tokens


# Global rate limiters per service and operation
_rate_limiters: dict[str, dict[str, TokenBucket]] = defaultdict(dict)
_rate_limiter_lock = Lock()


def get_rate_limiter(service: str, operation_type: str, max_ops: float, window_seconds: float) -> TokenBucket:
    """Get or create rate limiter for a service and operation.

    Args:
        service: Service name.
        operation_type: Operation type.
        max_ops: Maximum operations per window.
        window_seconds: Time window in seconds.

    Returns:
        TokenBucket instance.
    """
    key = f"{service}:{operation_type}"
    with _rate_limiter_lock:
        if key not in _rate_limiters[service]:
            # Calculate refill rate (tokens per second)
            refill_rate = max_ops / window_seconds
            _rate_limiters[service][operation_type] = TokenBucket(capacity=max_ops, refill_rate=refill_rate)
        return _rate_limiters[service][operation_type]


def rate_limit(
    service: str,
    operation_type: str,
    max_ops: float,
    window_seconds: float = 60.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to rate limit operations.

    Args:
        service: Service name.
        operation_type: Operation type.
        max_ops: Maximum operations per window.
        window_seconds: Time window in seconds (default: 60).

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        limiter = get_rate_limiter(service, operation_type, max_ops, window_seconds)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not limiter.consume():
                available = limiter.get_available_tokens()
                wait_time = (1.0 - available) / limiter.refill_rate
                error_msg = (
                    f"Rate limit exceeded for {service}.{operation_type}. "
                    f"Max {max_ops} operations per {window_seconds}s. "
                    f"Retry after {wait_time:.1f}s."
                )
                logger.warning(error_msg)
                raise RateLimitExceededError(error_msg)

            return func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""

    pass
