# Twoje-Miasto Sp. z o.o. / Marcin Koźliński
# Ostatnia modyfikacja: 2026-03-28

"""Data update coordinators for Pstryk Energy."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PstrykApiClient, PstrykApiError, PstrykAuthError
from .const import ATTRIBUTION, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PstrykMetricsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for unified metrics data (energy, cost, carbon)."""

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
        """Fetch metrics data from API."""
        try:
            # Get daily and monthly aggregates plus hourly detail
            daily = await self.client.get_daily_metrics(for_tz=self.timezone)
            monthly = await self.client.get_monthly_metrics(for_tz=self.timezone)
            hourly = await self.client.get_hourly_metrics()

            # Find the current "live" frame from hourly data
            current_frame = None
            if hourly.get("frames"):
                for frame in hourly["frames"]:
                    if frame.get("is_live"):
                        current_frame = frame
                        break
                # Fallback to last frame if no live frame found
                if current_frame is None:
                    current_frame = hourly["frames"][-1]

            return {
                "daily": daily,
                "monthly": monthly,
                "hourly": hourly,
                "current_frame": current_frame,
                "daily_summary": daily.get("summary", {}),
                "monthly_summary": monthly.get("summary", {}),
            }
        except PstrykAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except PstrykApiError as err:
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch pricing data from API."""
        try:
            pricing = await self.client.get_current_pricing()

            # Find current live price frame
            current_price = None
            next_prices: list[dict] = []
            cheapest_upcoming = None
            most_expensive_upcoming = None

            if pricing.get("frames"):
                found_live = False
                for frame in pricing["frames"]:
                    if frame.get("is_live"):
                        current_price = frame
                        found_live = True
                        continue
                    if found_live:
                        next_prices.append(frame)

                if not current_price and pricing["frames"]:
                    current_price = pricing["frames"][-1]

                # Find cheapest and most expensive upcoming
                if next_prices:
                    cheapest_upcoming = min(
                        next_prices,
                        key=lambda f: f.get("price_gross") or f.get("price_gross_avg") or 999,
                    )
                    most_expensive_upcoming = max(
                        next_prices,
                        key=lambda f: f.get("price_gross") or f.get("price_gross_avg") or 0,
                    )

            result: dict[str, Any] = {
                "pricing": pricing,
                "current_price": current_price,
                "next_prices": next_prices,
                "cheapest_upcoming": cheapest_upcoming,
                "most_expensive_upcoming": most_expensive_upcoming,
                "price_net_avg": pricing.get("price_net_avg"),
                "price_gross_avg": pricing.get("price_gross_avg"),
            }

            # Prosumer pricing
            if self.is_prosumer:
                prosumer = await self.client.get_current_prosumer_pricing()
                prosumer_current = None
                if prosumer.get("frames"):
                    for frame in prosumer["frames"]:
                        if frame.get("is_live"):
                            prosumer_current = frame
                            break
                    if not prosumer_current:
                        prosumer_current = prosumer["frames"][-1]

                result["prosumer_pricing"] = prosumer
                result["prosumer_current_price"] = prosumer_current
                result["prosumer_price_net_avg"] = prosumer.get("price_net_avg")
                result["prosumer_price_gross_avg"] = prosumer.get("price_gross_avg")

            return result
        except PstrykAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except PstrykApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
