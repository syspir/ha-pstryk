# Marcin Koźliński
# Ostatnia modyfikacja: 2026-03-29

"""The Pstryk Energy integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .api import PstrykApiClient, PstrykApiError
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
)
from .coordinator import (
    PstrykBleBoxCoordinator,
    PstrykMetricsCoordinator,
    PstrykPricingCoordinator,
)

_LOGGER = logging.getLogger(__name__)

SETUP_RETRY_INTERVAL = timedelta(minutes=15)


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
                    "module_url": "/pstryk_panel/pstryk-panel.js?v=10",
                }
            },
            require_admin=False,
        )
        hass.data[DOMAIN]["panel_registered"] = True
    elif not enable_panel and "panel_registered" in hass.data[DOMAIN]:
        async_remove_panel(hass, PANEL_URL)
        hass.data[DOMAIN].pop("panel_registered", None)

    # Throttle: don't retry setup more often than every 15 min
    last_fail = hass.data[DOMAIN].get("last_setup_fail")
    if last_fail and datetime.now(timezone.utc) - last_fail < SETUP_RETRY_INTERVAL:
        remaining = SETUP_RETRY_INTERVAL - (datetime.now(timezone.utc) - last_fail)
        raise ConfigEntryNotReady(
            f"Rate limit cooldown, retry in {int(remaining.total_seconds())}s"
        )

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
        entry_id=entry.entry_id,
    )

    pricing_coordinator = PstrykPricingCoordinator(
        hass=hass,
        client=client,
        update_interval=UPDATE_INTERVAL_PRICING,
        is_prosumer=is_prosumer,
        entry_id=entry.entry_id,
    )

    # Restore last known data from storage (sensors available immediately)
    await metrics_coordinator.async_load_stored_data()
    await pricing_coordinator.async_load_stored_data()

    # Fetch initial data — on failure, retry no sooner than 15 min
    try:
        await metrics_coordinator.async_config_entry_first_refresh()
        await pricing_coordinator.async_config_entry_first_refresh()
    except Exception as err:
        hass.data[DOMAIN]["last_setup_fail"] = datetime.now(timezone.utc)
        raise ConfigEntryNotReady(
            f"Failed to fetch initial data: {err}"
        ) from err

    hass.data[DOMAIN].pop("last_setup_fail", None)

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
        "blebox_coordinator": blebox_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 1-minute tick to recalculate current price frame (no API call)
    async def _tick_recalculate(_now) -> None:
        pricing_coordinator.recalculate_current()

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
        internal_keys = {"panel_registered", "static_path_registered", "last_setup_fail"}
        remaining = {k for k in hass.data[DOMAIN] if k not in internal_keys}
        if not remaining:
            async_remove_panel(hass, PANEL_URL)
            hass.data[DOMAIN].pop("panel_registered", None)
    return unload_ok
