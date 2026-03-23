"""Circuit breaker implementation for GCP quota protection."""

import logging
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

from backend.utils.quota_manager import QuotaStatus, get_quota_manager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocked due to quota
    HALF_OPEN = "half_open"  # Testing if quota has reset


class CircuitBreaker:
    """Circuit breaker for protecting against quota overages.

    Prevents operations when quota limits are approached or exceeded.
    """

    def __init__(
        self,
        service: str,
        warning_threshold: float = 0.7,
        critical_threshold: float = 0.9,
        emergency_threshold: float = 0.95,
        recovery_timeout: int = 3600,  # 1 hour
    ):
        """Initialize circuit breaker.

        Args:
            service: Service name (e.g., "bigquery", "cloud_storage").
            warning_threshold: Percentage threshold for warning (default: 70%).
            critical_threshold: Percentage threshold for critical (default: 90%).
            emergency_threshold: Percentage threshold for emergency (default: 95%).
            recovery_timeout: Seconds to wait before attempting recovery (default: 3600).
        """
        self.service = service
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.emergency_threshold = emergency_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED
        self.last_failure_time: float | None = None
        self.quota_manager = get_quota_manager()

    def can_proceed(
        self, operation_type: str, estimated_cost: float, limit: float
    ) -> tuple[bool, QuotaStatus, str]:
        """Check if operation can proceed.

        Args:
            operation_type: Type of operation.
            estimated_cost: Estimated cost/usage.
            limit: Quota limit.

        Returns:
            Tuple of (can_proceed, quota_status, reason).
        """
        # Check quota status
        status, percentage = self.quota_manager.check_quota(
            self.service, operation_type, estimated_cost, limit
        )

        # Update circuit breaker state based on quota status
        if status == QuotaStatus.EXCEEDED:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            reason = (
                f"Quota exceeded: {percentage:.1f}% of limit. "
                f"Operation blocked to prevent overage."
            )
            logger.warning(f"Circuit breaker OPEN for {self.service}: {reason}")
            return False, status, reason

        elif status == QuotaStatus.CRITICAL:
            # At critical threshold, open circuit breaker
            if self.state == CircuitState.CLOSED:
                self.state = CircuitState.OPEN
                self.last_failure_time = time.time()
                reason = (
                    f"Quota critical: {percentage:.1f}% of limit. "
                    f"Circuit breaker opened to prevent overage."
                )
                logger.warning(f"Circuit breaker OPEN for {self.service}: {reason}")
                return False, status, reason
            else:
                # Already open
                reason = f"Circuit breaker already OPEN. Quota at {percentage:.1f}%."
                return False, status, reason

        elif status == QuotaStatus.WARNING:
            # At warning threshold, log but allow
            if self.state == CircuitState.OPEN:
                # Try to recover if enough time has passed
                if self._should_attempt_recovery():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(
                        f"Circuit breaker HALF_OPEN for {self.service}. "
                        f"Testing recovery. Quota at {percentage:.1f}%."
                    )
                else:
                    reason = (
                        f"Circuit breaker OPEN. Quota at {percentage:.1f}%. "
                        f"Recovery not yet attempted."
                    )
                    return False, status, reason

            reason = f"Quota warning: {percentage:.1f}% of limit. Proceeding with caution."
            logger.warning(f"Quota warning for {self.service}: {reason}")
            return True, status, reason

        else:  # QuotaStatus.OK
            # Quota is healthy, close circuit breaker if it was open
            if self.state != CircuitState.CLOSED:
                old_state = self.state
                self.state = CircuitState.CLOSED
                self.last_failure_time = None
                logger.info(
                    f"Circuit breaker CLOSED for {self.service} "
                    f"(was {old_state.value}). Quota at {percentage:.1f}%."
                )

            return True, status, "Quota OK"

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery.

        Returns:
            True if recovery should be attempted.
        """
        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout

    def record_failure(self) -> None:
        """Record a failure (quota exceeded).

        Opens the circuit breaker.
        """
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()
        logger.warning(f"Circuit breaker failure recorded for {self.service}")

    def record_success(self) -> None:
        """Record a success.

        If in HALF_OPEN state, transitions to CLOSED.
        """
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.last_failure_time = None
            logger.info(f"Circuit breaker recovery successful for {self.service}")

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state.

        Returns:
            Current state.
        """
        return self.state

    def force_open(self) -> None:
        """Force circuit breaker to open (admin override)."""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()
        logger.warning(f"Circuit breaker force opened for {self.service}")

    def force_close(self) -> None:
        """Force circuit breaker to close (admin override)."""
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        logger.info(f"Circuit breaker force closed for {self.service}")


# Global circuit breakers per service
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service: str) -> CircuitBreaker:
    """Get or create circuit breaker for a service.

    Args:
        service: Service name.

    Returns:
        CircuitBreaker instance.
    """
    if service not in _circuit_breakers:
        _circuit_breakers[service] = CircuitBreaker(service)
    return _circuit_breakers[service]


def circuit_breaker(
    service: str,
    operation_type: str,
    estimated_cost: float | Callable[[], float],
    limit: float | Callable[[], float],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to protect operations with circuit breaker.

    Args:
        service: Service name.
        operation_type: Type of operation.
        estimated_cost: Estimated cost (can be callable for dynamic calculation).
        limit: Quota limit (can be callable for dynamic lookup).

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            cb = get_circuit_breaker(service)

            # Calculate estimated cost and limit
            cost = estimated_cost() if callable(estimated_cost) else estimated_cost
            lim = limit() if callable(limit) else limit

            # Check if operation can proceed
            can_proceed, status, reason = cb.can_proceed(
                operation_type, cost, lim
            )

            if not can_proceed:
                # Raise exception to trigger fallback
                raise QuotaExceededError(
                    f"Operation blocked by circuit breaker: {reason}"
                )

            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                # If it's a quota-related error, record failure
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    cb.record_failure()
                raise

        return wrapper

    return decorator


class QuotaExceededError(Exception):
    """Exception raised when quota is exceeded."""

    pass
