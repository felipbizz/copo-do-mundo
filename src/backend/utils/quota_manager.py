"""Quota management service for tracking and enforcing GCP usage limits."""

import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QuotaStatus(Enum):
    """Status of quota check."""

    OK = "ok"
    WARNING = "warning"  # 70% threshold
    CRITICAL = "critical"  # 90% threshold
    EXCEEDED = "exceeded"  # 100% threshold


class QuotaManager:
    """Manages quota tracking and enforcement for GCP services.

    Tracks usage per service and operation type, with configurable limits
    and time windows (daily/monthly).
    """

    def __init__(self, usage_file: str | None = None):
        """Initialize QuotaManager.

        Args:
            usage_file: Path to JSON file for persisting usage data.
                        If None, uses default location in data directory.
        """
        if usage_file is None:
            usage_file = os.path.join(
                os.getenv("DATA_DIR", "data"), "quota_usage.json"
            )
        self.usage_file = Path(usage_file)
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        self._usage_data = self._load_usage_data()

    def _load_usage_data(self) -> dict[str, Any]:
        """Load usage data from file.

        Returns:
            Dictionary containing usage data.
        """
        if not self.usage_file.exists():
            return {}

        try:
            with open(self.usage_file, "r") as f:
                data = json.load(f)
                # Convert date strings back to datetime objects for internal use
                return self._normalize_usage_data(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading usage data: {e}. Starting with empty data.")
            return {}

    def _normalize_usage_data(self, data: dict) -> dict:
        """Normalize usage data, converting date strings to datetime objects.

        Args:
            data: Raw usage data from JSON.

        Returns:
            Normalized usage data.
        """
        normalized = {}
        for service, service_data in data.items():
            normalized[service] = {}
            for period, period_data in service_data.items():
                normalized[service][period] = {}
                for date_str, usage in period_data.items():
                    try:
                        date_obj = datetime.fromisoformat(date_str)
                    except (ValueError, TypeError):
                        # If parsing fails, use current date
                        date_obj = datetime.now().date()
                    normalized[service][period][date_obj.isoformat()] = usage
        return normalized

    def _save_usage_data(self) -> None:
        """Save usage data to file."""
        try:
            with open(self.usage_file, "w") as f:
                json.dump(self._usage_data, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Error saving usage data: {e}")

    def _get_current_period_keys(self) -> tuple[str, str]:
        """Get current date keys for daily and monthly tracking.

        Returns:
            Tuple of (daily_key, monthly_key) as ISO date strings.
        """
        now = datetime.now()
        daily_key = now.date().isoformat()
        monthly_key = now.strftime("%Y-%m")  # YYYY-MM format
        return daily_key, monthly_key

    def track_operation(
        self,
        service: str,
        operation_type: str,
        cost: float,
        unit: str = "bytes",
    ) -> None:
        """Track an operation's usage.

        Args:
            service: Service name (e.g., "bigquery", "cloud_storage").
            operation_type: Type of operation (e.g., "query", "insert", "upload").
            cost: Cost/usage amount (bytes, operations, etc.).
            unit: Unit of measurement (default: "bytes").
        """
        if service not in self._usage_data:
            self._usage_data[service] = {}

        daily_key, monthly_key = self._get_current_period_keys()

        # Track daily usage
        if "daily" not in self._usage_data[service]:
            self._usage_data[service]["daily"] = {}
        if daily_key not in self._usage_data[service]["daily"]:
            self._usage_data[service]["daily"][daily_key] = {}

        if operation_type not in self._usage_data[service]["daily"][daily_key]:
            self._usage_data[service]["daily"][daily_key][operation_type] = {
                "total": 0.0,
                "unit": unit,
            }

        self._usage_data[service]["daily"][daily_key][operation_type]["total"] += cost

        # Track monthly usage
        if "monthly" not in self._usage_data[service]:
            self._usage_data[service]["monthly"] = {}
        if monthly_key not in self._usage_data[service]["monthly"]:
            self._usage_data[service]["monthly"][monthly_key] = {}

        if operation_type not in self._usage_data[service]["monthly"][monthly_key]:
            self._usage_data[service]["monthly"][monthly_key][operation_type] = {
                "total": 0.0,
                "unit": unit,
            }

        self._usage_data[service]["monthly"][monthly_key][operation_type]["total"] += (
            cost
        )

        self._save_usage_data()
        logger.debug(
            f"Tracked {service}.{operation_type}: {cost} {unit} "
            f"(Daily: {self._usage_data[service]['daily'][daily_key][operation_type]['total']}, "
            f"Monthly: {self._usage_data[service]['monthly'][monthly_key][operation_type]['total']})"
        )

    def check_quota(
        self,
        service: str,
        operation_type: str,
        estimated_cost: float,
        limit: float,
        period: str = "monthly",
    ) -> tuple[QuotaStatus, float]:
        """Check if operation would exceed quota.

        Args:
            service: Service name.
            operation_type: Type of operation.
            estimated_cost: Estimated cost/usage for this operation.
            limit: Quota limit for this operation type.
            period: Time period to check ("daily" or "monthly").

        Returns:
            Tuple of (QuotaStatus, current_usage_percentage).
        """
        daily_key, monthly_key = self._get_current_period_keys()
        period_key = daily_key if period == "daily" else monthly_key

        # Get current usage
        current_usage = self.get_usage(service, operation_type, period)

        # Calculate percentage
        usage_percentage = (current_usage / limit) * 100 if limit > 0 else 0

        # Check if adding estimated cost would exceed limit
        projected_usage = current_usage + estimated_cost
        projected_percentage = (projected_usage / limit) * 100 if limit > 0 else 0

        # Determine status
        if projected_percentage >= 100:
            status = QuotaStatus.EXCEEDED
        elif projected_percentage >= 95:
            status = QuotaStatus.EXCEEDED  # Emergency threshold
        elif projected_percentage >= 90:
            status = QuotaStatus.CRITICAL
        elif projected_percentage >= 70:
            status = QuotaStatus.WARNING
        else:
            status = QuotaStatus.OK

        logger.debug(
            f"Quota check for {service}.{operation_type}: "
            f"{current_usage:.2f}/{limit:.2f} ({usage_percentage:.1f}%) "
            f"-> {projected_usage:.2f} ({projected_percentage:.1f}%) - {status.value}"
        )

        return status, projected_percentage

    def get_usage(
        self, service: str, operation_type: str, period: str = "monthly"
    ) -> float:
        """Get current usage for a service and operation type.

        Args:
            service: Service name.
            operation_type: Type of operation.
            period: Time period ("daily" or "monthly").

        Returns:
            Current usage amount.
        """
        daily_key, monthly_key = self._get_current_period_keys()
        period_key = daily_key if period == "daily" else monthly_key

        if service not in self._usage_data:
            return 0.0

        if period not in self._usage_data[service]:
            return 0.0

        if period_key not in self._usage_data[service][period]:
            return 0.0

        if operation_type not in self._usage_data[service][period][period_key]:
            return 0.0

        return float(
            self._usage_data[service][period][period_key][operation_type].get(
                "total", 0.0
            )
        )

    def get_usage_stats(
        self, service: str | None = None, period: str = "monthly"
    ) -> dict[str, Any]:
        """Get usage statistics.

        Args:
            service: Service name. If None, returns stats for all services.
            period: Time period ("daily" or "monthly").

        Returns:
            Dictionary containing usage statistics.
        """
        daily_key, monthly_key = self._get_current_period_keys()
        period_key = daily_key if period == "daily" else monthly_key

        if service:
            services = [service]
        else:
            services = list(self._usage_data.keys())

        stats = {}
        for svc in services:
            if svc not in self._usage_data:
                stats[svc] = {}
                continue

            if period not in self._usage_data[svc]:
                stats[svc] = {}
                continue

            if period_key not in self._usage_data[svc][period]:
                stats[svc] = {}
                continue

            stats[svc] = self._usage_data[svc][period][period_key].copy()

        return stats

    def reset_usage(
        self, service: str | None = None, period: str | None = None
    ) -> bool:
        """Reset usage data (admin only).

        Args:
            service: Service name. If None, resets all services.
            period: Time period. If None, resets all periods.

        Returns:
            True if reset was successful.
        """
        try:
            if service is None:
                self._usage_data = {}
            elif period is None:
                if service in self._usage_data:
                    self._usage_data[service] = {}
            else:
                if service in self._usage_data and period in self._usage_data[service]:
                    self._usage_data[service][period] = {}

            self._save_usage_data()
            logger.info(f"Reset usage data for service={service}, period={period}")
            return True
        except Exception as e:
            logger.error(f"Error resetting usage data: {e}")
            return False

    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old usage data to prevent file from growing too large.

        Args:
            days_to_keep: Number of days of daily data to keep.
        """
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()

        for service in list(self._usage_data.keys()):
            if "daily" in self._usage_data[service]:
                keys_to_remove = [
                    key
                    for key in self._usage_data[service]["daily"].keys()
                    if datetime.fromisoformat(key).date() < cutoff_date
                ]
                for key in keys_to_remove:
                    del self._usage_data[service]["daily"][key]

        self._save_usage_data()
        logger.info(f"Cleaned up usage data older than {days_to_keep} days")


# Global instance
_quota_manager: QuotaManager | None = None


def get_quota_manager() -> QuotaManager:
    """Get or create global QuotaManager instance.

    Returns:
        QuotaManager instance.
    """
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
