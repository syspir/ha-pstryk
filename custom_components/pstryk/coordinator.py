# Marcin Koźliński
# Ostatnia modyfikacja: 2026-03-29

"""Data update coordinators for Pstryk Energy."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PstrykApiClient, PstrykApiError, PstrykAuthError
from .const import ATTRIBUTION, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PstrykMetricsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for unified metrics data (energy, cost)."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PstrykApiClient,
        update_interval: timedelta,
        timezone: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_metrics",
            update_interval=update_interval,
        )
        self.client = client
        self.timezone = timezone
        self.attribution = ATTRIBUTION

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch metrics data from API (2 requests: hourly + monthly)."""
        try:
            hourly = await self.client.get_hourly_metrics()
            monthly = await self.client.get_monthly_metrics(for_tz=self.timezone)

            # Find the current "live" frame from hourly data
            current_frame = None
            if hourly.get("frames"):
                for frame in hourly["frames"]:
                    if frame.get("is_live"):
                        current_frame = frame
                        break
                if current_frame is None:
                    current_frame = hourly["frames"][-1]

            return {
                "hourly": hourly,
                "monthly": monthly,
                "current_frame": current_frame,
                "daily_summary": hourly.get("summary", {}),
                "monthly_summary": monthly.get("summary", {}),
            }
        except PstrykAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except PstrykApiError as err:
            if self.data:
                _LOGGER.warning("Metrics API error, keeping last data: %s", err)
                return self.data
            raise UpdateFailed(f"API error: {err}") from err


class PstrykPricingCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for TGE pricing data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PstrykApiClient,
        update_interval: timedelta,
        is_prosumer: bool = False,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_pricing",
            update_interval=update_interval,
        )
        self.client = client
        self.is_prosumer = is_prosumer
        self.attribution = ATTRIBUTION
        self._raw_pricing: dict[str, Any] | None = None
        self._raw_prosumer: dict[str, Any] | None = None

    def _find_current_frame(self, frames: list[dict]) -> dict | None:
        """Find the frame matching current time based on start/end."""
        now = datetime.now(timezone.utc)
        for frame in frames:
            start = frame.get("start")
            end = frame.get("end")
            if start and end:
                try:
                    frame_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    frame_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    if frame_start <= now < frame_end:
                        return frame
                except (ValueError, TypeError):
                    continue
        return None

    def _process_data(self) -> dict[str, Any]:
        """Process stored raw data to determine current prices."""
        pricing = self._raw_pricing or {}

        all_frames = pricing.get("frames", [])
        current_price = self._find_current_frame(all_frames)
        next_prices: list[dict] = []
        cheapest_upcoming = None
        most_expensive_upcoming = None

        if all_frames and current_price:
            now = datetime.now(timezone.utc)
            for frame in all_frames:
                start = frame.get("start")
                if start:
                    try:
                        frame_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                        if frame_start > now:
                            next_prices.append(frame)
                    except (ValueError, TypeError):
                        continue
        elif all_frames:
            current_price = all_frames[-1]

        if next_prices:
            cheapest_upcoming = min(
                next_prices,
                key=lambda f: f.get("full_price") or f.get("price_gross") or 999,
            )
            most_expensive_upcoming = max(
                next_prices,
                key=lambda f: f.get("full_price") or f.get("price_gross") or 0,
            )

        result: dict[str, Any] = {
            "pricing": pricing,
            "all_frames": all_frames,
            "current_price": current_price,
            "next_prices": next_prices,
            "cheapest_upcoming": cheapest_upcoming,
            "most_expensive_upcoming": most_expensive_upcoming,
            "price_net_avg": pricing.get("price_net_avg"),
            "price_gross_avg": pricing.get("price_gross_avg"),
        }

        if self.is_prosumer and self._raw_prosumer:
            prosumer = self._raw_prosumer
            prosumer_frames = prosumer.get("frames", [])
            prosumer_current = self._find_current_frame(prosumer_frames)
            if not prosumer_current and prosumer_frames:
                prosumer_current = prosumer_frames[-1]

            result["prosumer_pricing"] = prosumer
            result["prosumer_current_price"] = prosumer_current
            result["prosumer_price_net_avg"] = prosumer.get("price_net_avg")
            result["prosumer_price_gross_avg"] = prosumer.get("price_gross_avg")

        return result

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch pricing data from API."""
        try:
            self._raw_pricing = await self.client.get_current_pricing()
            if self.is_prosumer:
                self._raw_prosumer = await self.client.get_current_prosumer_pricing()
            return self._process_data()
        except PstrykAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except PstrykApiError as err:
            if self.data:
                _LOGGER.warning("Pricing API error, keeping last data: %s", err)
                return self.data
            raise UpdateFailed(f"API error: {err}") from err

    def recalculate_current(self) -> None:
        """Recalculate current price from stored frames (no API call)."""
        if self._raw_pricing:
            self.async_set_updated_data(self._process_data())
