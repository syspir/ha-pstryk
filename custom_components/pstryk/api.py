"""API client for Pstryk Energy."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from .const import (
    ALL_METRICS,
    API_BASE_URL,
    PRICING_URL,
    PROSUMER_PRICING_URL,
    RESOLUTION_DAY,
    RESOLUTION_HOUR,
    RESOLUTION_MONTH,
    UNIFIED_METRICS_URL,
)

_LOGGER = logging.getLogger(__name__)


class PstrykApiError(Exception):
    """Base exception for Pstryk API errors."""


class PstrykAuthError(PstrykApiError):
    """Authentication error."""


class PstrykConnectionError(PstrykApiError):
    """Connection error."""


class PstrykApiClient:
    """Client for the Pstryk API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_token: str,
        timezone: str = "Europe/Warsaw",
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._api_token = api_token
        self._timezone = timezone
        self._headers = {
            "Authorization": api_token,
            "Accept": "application/json",
        }

    async def _request(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make an authenticated request to the API."""
        try:
            async with self._session.get(
                url, headers=self._headers, params=params, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 401:
                    raise PstrykAuthError("Invalid API token")
                if response.status == 403:
                    raise PstrykAuthError("Access forbidden - check API token permissions")
                if response.status == 404:
                    raise PstrykApiError("Resource not found - meter may not exist")
                if response.status == 400:
                    text = await response.text()
                    raise PstrykApiError(f"Bad request: {text}")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            raise PstrykConnectionError(f"Connection error: {err}") from err

    async def validate_token(self) -> bool:
        """Validate the API token by making a test request."""
        now = datetime.now(timezone.utc)
        params = {
            "metrics": "meter_values",
            "resolution": RESOLUTION_DAY,
            "window_start": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        try:
            await self._request(UNIFIED_METRICS_URL, params)
            return True
        except PstrykAuthError:
            return False

    async def get_unified_metrics(
        self,
        metrics: str = ALL_METRICS,
        resolution: str = RESOLUTION_HOUR,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
        for_tz: str | None = None,
    ) -> dict[str, Any]:
        """Fetch unified metrics from the API.

        Args:
            metrics: Comma-separated list: meter_values,cost,carbon,pricing
            resolution: hour, day, or month
            window_start: Start of time window (UTC)
            window_end: End of time window (UTC, defaults to now)
            for_tz: Timezone for aggregation (cannot combine with hour resolution)
        """
        now = datetime.now(timezone.utc)
        if window_start is None:
            window_start = now - timedelta(hours=24)
        if window_end is None:
            window_end = now

        params: dict[str, str] = {
            "metrics": metrics,
            "resolution": resolution,
            "window_start": window_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_end": window_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # for_tz cannot be combined with hour resolution
        if for_tz and resolution != RESOLUTION_HOUR:
            params["for_tz"] = for_tz

        return await self._request(UNIFIED_METRICS_URL, params)

    async def get_pricing(
        self,
        resolution: str = RESOLUTION_HOUR,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
        for_tz: str | None = None,
    ) -> dict[str, Any]:
        """Fetch TGE pricing data."""
        now = datetime.now(timezone.utc)
        if window_start is None:
            window_start = now - timedelta(hours=24)
        if window_end is None:
            window_end = now + timedelta(days=1)

        params: dict[str, str] = {
            "resolution": resolution,
            "window_start": window_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_end": window_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        if for_tz and resolution != RESOLUTION_HOUR:
            params["for_tz"] = for_tz

        return await self._request(PRICING_URL, params)

    async def get_prosumer_pricing(
        self,
        resolution: str = RESOLUTION_HOUR,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
        for_tz: str | None = None,
    ) -> dict[str, Any]:
        """Fetch prosumer pricing data."""
        now = datetime.now(timezone.utc)
        if window_start is None:
            window_start = now - timedelta(hours=24)
        if window_end is None:
            window_end = now + timedelta(days=1)

        params: dict[str, str] = {
            "resolution": resolution,
            "window_start": window_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_end": window_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        if for_tz and resolution != RESOLUTION_HOUR:
            params["for_tz"] = for_tz

        return await self._request(PROSUMER_PRICING_URL, params)

    async def get_daily_metrics(self, for_tz: str | None = None) -> dict[str, Any]:
        """Get today's metrics aggregated by day."""
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.get_unified_metrics(
            metrics=ALL_METRICS,
            resolution=RESOLUTION_DAY,
            window_start=start_of_day,
            window_end=now,
            for_tz=for_tz,
        )

    async def get_monthly_metrics(self, for_tz: str | None = None) -> dict[str, Any]:
        """Get this month's metrics aggregated by month."""
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return await self.get_unified_metrics(
            metrics=ALL_METRICS,
            resolution=RESOLUTION_MONTH,
            window_start=start_of_month,
            window_end=now,
            for_tz=for_tz,
        )

    async def get_hourly_metrics(self) -> dict[str, Any]:
        """Get last 24h metrics with hourly resolution."""
        now = datetime.now(timezone.utc)
        return await self.get_unified_metrics(
            metrics=ALL_METRICS,
            resolution=RESOLUTION_HOUR,
            window_start=now - timedelta(hours=24),
            window_end=now,
        )

    async def get_current_pricing(self) -> dict[str, Any]:
        """Get pricing for next 24h (hourly)."""
        now = datetime.now(timezone.utc)
        return await self.get_pricing(
            resolution=RESOLUTION_HOUR,
            window_start=now - timedelta(hours=1),
            window_end=now + timedelta(hours=24),
        )

    async def get_current_prosumer_pricing(self) -> dict[str, Any]:
        """Get prosumer pricing for next 24h (hourly)."""
        now = datetime.now(timezone.utc)
        return await self.get_prosumer_pricing(
            resolution=RESOLUTION_HOUR,
            window_start=now - timedelta(hours=1),
            window_end=now + timedelta(hours=24),
        )
