# Twoje-Miasto Sp. z o.o. / Marcin Koźliński
# Ostatnia modyfikacja: 2026-03-28

"""API client for Pstryk Energy."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from .const import (
    ALL_METRICS,
    API_DATE_FORMAT,
    PRICING_URL,
    PROSUMER_PRICING_URL,
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
                if response.status == 429:
                    _LOGGER.warning("Rate limited (429), skipping until next update cycle")
                    raise PstrykApiError("Rate limited (429) - too many requests")
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
            "resolution": "day",
            "window_start": (now - timedelta(days=1)).strftime(API_DATE_FORMAT),
            "window_end": now.strftime(API_DATE_FORMAT),
        }
        try:
            await self._request(UNIFIED_METRICS_URL, params)
            return True
        except PstrykAuthError:
            return False

    async def _get_metrics(
        self,
        resolution: str,
        window_start: datetime,
        window_end: datetime,
        for_tz: str | None = None,
    ) -> dict[str, Any]:
        """Fetch unified metrics from the API."""
        params: dict[str, str] = {
            "metrics": ALL_METRICS,
            "resolution": resolution,
            "window_start": window_start.strftime(API_DATE_FORMAT),
            "window_end": window_end.strftime(API_DATE_FORMAT),
        }
        if for_tz and resolution != RESOLUTION_HOUR:
            params["for_tz"] = for_tz
        return await self._request(UNIFIED_METRICS_URL, params)

    async def get_hourly_metrics(self) -> dict[str, Any]:
        """Get today's metrics with hourly resolution (includes summary)."""
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return await self._get_metrics(RESOLUTION_HOUR, start_of_day, now)

    async def get_monthly_metrics(self, for_tz: str | None = None) -> dict[str, Any]:
        """Get this month's metrics aggregated by month."""
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return await self._get_metrics(RESOLUTION_MONTH, start_of_month, now, for_tz)

    async def _get_pricing_data(
        self,
        url: str,
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, Any]:
        """Fetch pricing data from the API."""
        params: dict[str, str] = {
            "resolution": RESOLUTION_HOUR,
            "window_start": window_start.strftime(API_DATE_FORMAT),
            "window_end": window_end.strftime(API_DATE_FORMAT),
        }
        return await self._request(url, params)

    async def get_current_pricing(self) -> dict[str, Any]:
        """Get pricing for next 24h (hourly)."""
        now = datetime.now(timezone.utc)
        return await self._get_pricing_data(
            PRICING_URL, now - timedelta(hours=1), now + timedelta(hours=24)
        )

    async def get_current_prosumer_pricing(self) -> dict[str, Any]:
        """Get prosumer pricing for next 24h (hourly)."""
        now = datetime.now(timezone.utc)
        return await self._get_pricing_data(
            PROSUMER_PRICING_URL, now - timedelta(hours=1), now + timedelta(hours=24)
        )
