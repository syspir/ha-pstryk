# Marcin Koźliński
# Ostatnia modyfikacja: 2026-04-09

"""The Pstryk Energy integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .api import PstrykApiClient
from .blebox import PstrykBleBoxClient
from .const import (
    CONF_API_TOKEN,
    CONF_BLEBOX_IP,
    CONF_ENABLE_PANEL,
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
    UPDATE_INTERVAL_BLEBOX,
    UPDATE_INTERVAL_PRICING,
    UPDATE_INTERVAL_TGE,
)
from .coordinator import (
    PstrykBleBoxCoordinator,
    PstrykMetricsCoordinator,
    PstrykPricingCoordinator,
    PstrykTgeCoordinator,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pstryk Energy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Register panel early (before API calls) so it's available even if API fails
    enable_panel = entry.options.get(CONF_ENABLE_PANEL, True)

    if enable_panel and "panel_registered" not in hass.data[DOMAIN]:
        if "static_path_registered" not in hass.data[DOMAIN]:
            panel_path = Path(__file__).parent / "frontend"
            await hass.http.async_register_static_paths([
                StaticPathConfig("/pstryk_panel", str(panel_path), cache_headers=True)
            ])
            hass.data[DOMAIN]["static_path_registered"] = True
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            frontend_url_path=PANEL_URL,
            config={
                "_panel_custom": {
                    "name": "pstryk-panel",
                    "module_url": "/pstryk_panel/pstryk-panel.js?v=17",
                }
            },
            require_admin=False,
        )
        hass.data[DOMAIN]["panel_registered"] = True
    elif not enable_panel and "panel_registered" in hass.data[DOMAIN]:
        async_remove_panel(hass, PANEL_URL)
        hass.data[DOMAIN].pop("panel_registered", None)

    session = async_get_clientsession(hass)
    api_token = entry.options.get(CONF_API_TOKEN) or entry.data[CONF_API_TOKEN]
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
        entry_id=entry.entry_id,
    )

    pricing_coordinator = PstrykPricingCoordinator(
        hass=hass,
        client=client,
        update_interval=UPDATE_INTERVAL_PRICING,
        is_prosumer=is_prosumer,
        entry_id=entry.entry_id,
    )

    tge_coordinator = PstrykTgeCoordinator(
        hass=hass,
        session=session,
        update_interval=UPDATE_INTERVAL_TGE,
        entry_id=entry.entry_id,
    )

    # Restore last known data from storage (sensors available immediately)
    await metrics_coordinator.async_load_stored_data()
    await pricing_coordinator.async_load_stored_data()
    await tge_coordinator.async_load_stored_data()

    # Fetch initial data — each source is independent, none blocks the others
    for coord_name, coord in [
        ("Pstryk Metrics", metrics_coordinator),
        ("Pstryk Pricing", pricing_coordinator),
        ("TGE RDN", tge_coordinator),
    ]:
        try:
            await coord.async_config_entry_first_refresh()
        except Exception:
            _LOGGER.warning(
                "%s data is not available, continuing without it", coord_name,
            )

    # BleBox local meter (optional)
    blebox_ip = entry.options.get(CONF_BLEBOX_IP) or entry.data.get(CONF_BLEBOX_IP)
    blebox_coordinator = None

    if blebox_ip:
        blebox_client = PstrykBleBoxClient(session=session, host=blebox_ip)
        blebox_coordinator = PstrykBleBoxCoordinator(
            hass=hass,
            client=blebox_client,
            update_interval=UPDATE_INTERVAL_BLEBOX,
            entry_id=entry.entry_id,
        )
        try:
            await blebox_coordinator.async_load_periods()
            await blebox_coordinator.async_config_entry_first_refresh()
        except Exception:
            _LOGGER.warning(
                "BleBox meter at %s is not available, continuing without local data",
                blebox_ip,
            )
            blebox_coordinator = None

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "metrics_coordinator": metrics_coordinator,
        "pricing_coordinator": pricing_coordinator,
        "tge_coordinator": tge_coordinator,
        "blebox_coordinator": blebox_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 1-minute tick to recalculate current price frame (no API call)
    async def _tick_recalculate(_now) -> None:
        pricing_coordinator.recalculate_current()
        tge_coordinator.recalculate_current()

    cancel_tick = async_track_time_interval(
        hass,
        _tick_recalculate,
        timedelta(minutes=1),
    )
    entry.async_on_unload(cancel_tick)

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
        # Remove panel if no config entries left
        internal_keys = {"panel_registered", "static_path_registered"}
        remaining = {k for k in hass.data[DOMAIN] if k not in internal_keys}
        if not remaining:
            async_remove_panel(hass, PANEL_URL)
            hass.data[DOMAIN].pop("panel_registered", None)
    return unload_ok
