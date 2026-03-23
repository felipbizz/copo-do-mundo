"""Retry utilities for handling transient errors in GCP operations."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Transient errors that should be retried
TRANSIENT_ERRORS = (
    gcp_exceptions.ServiceUnavailable,
    gcp_exceptions.InternalServerError,
    gcp_exceptions.TooManyRequests,
    gcp_exceptions.DeadlineExceeded,
    ConnectionError,
    TimeoutError,
)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3).
        initial_delay: Initial delay in seconds before first retry (default: 1.0).
        max_delay: Maximum delay in seconds between retries (default: 60.0).
        exponential_base: Base for exponential backoff calculation (default: 2.0).
        retry_on: Tuple of exception types to retry on. If None, uses default transient errors.

    Returns:
        Decorated function that retries on transient errors.
    """
    if retry_on is None:
        retry_on = TRANSIENT_ERRORS

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:  # type: ignore[misc]
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Transient error in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            f"Max retries exceeded for {func.__name__} after {max_retries + 1} attempts"
                        )
                except Exception as e:
                    # Non-transient errors should not be retried
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise

            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected error in {func.__name__}")

        return wrapper

    return decorator
