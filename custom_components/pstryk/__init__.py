# Twoje-Miasto Sp. z o.o.
# Ostatnia modyfikacja: 2026-03-28

"""The Pstryk Energy integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PstrykApiClient
from .const import (
    CONF_API_TOKEN,
    CONF_IS_PROSUMER,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_TIMEZONE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEZONE,
    DOMAIN,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL,
    PLATFORMS,
    UPDATE_INTERVAL_PRICING,
)
from .coordinator import PstrykMetricsCoordinator, PstrykPricingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pstryk Energy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api_token = entry.data[CONF_API_TOKEN]
    tz = entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)
    is_prosumer = entry.options.get(CONF_IS_PROSUMER, False)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)

    client = PstrykApiClient(
        session=session,
        api_token=api_token,
        timezone=tz,
    )

    metrics_coordinator = PstrykMetricsCoordinator(
        hass=hass,
        client=client,
        update_interval=timedelta(minutes=scan_interval),
        timezone=tz,
    )

    pricing_coordinator = PstrykPricingCoordinator(
        hass=hass,
        client=client,
        update_interval=UPDATE_INTERVAL_PRICING,
        is_prosumer=is_prosumer,
    )

    # Fetch initial data
    await metrics_coordinator.async_config_entry_first_refresh()
    await pricing_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "metrics_coordinator": metrics_coordinator,
        "pricing_coordinator": pricing_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register panel (only once)
    if "panel_registered" not in hass.data[DOMAIN]:
        panel_path = Path(__file__).parent / "frontend"
        hass.http.register_static_path(
            "/pstryk_panel",
            str(panel_path),
            cache_headers=False,
        )
        hass.components.frontend.async_register_panel(
            component_name="custom",
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            frontend_url_path=PANEL_URL,
            config={
                "_panel_custom": {
                    "name": "pstryk-panel",
                    "module_url": "/pstryk_panel/pstryk-panel.js",
                }
            },
            require_admin=False,
        )
        hass.data[DOMAIN]["panel_registered"] = True

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Remove panel if no entries left
        remaining = {k: v for k, v in hass.data[DOMAIN].items() if k != "panel_registered"}
        if not remaining:
            hass.components.frontend.async_remove_panel(PANEL_URL)
            hass.data[DOMAIN].pop("panel_registered", None)
    return unload_ok
