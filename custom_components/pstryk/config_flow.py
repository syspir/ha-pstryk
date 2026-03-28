# Twoje-Miasto Sp. z o.o.
# Ostatnia modyfikacja: 2026-03-28

"""Config flow for Pstryk Energy integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PstrykApiClient, PstrykAuthError, PstrykConnectionError
from .const import (
    CONF_API_TOKEN,
    CONF_ENABLE_PANEL,
    CONF_IS_PROSUMER,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_TIMEZONE,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEZONE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class PstrykConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pstryk Energy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            # Validate the token
            session = async_get_clientsession(self.hass)
            client = PstrykApiClient(
                session=session,
                api_token=user_input[CONF_API_TOKEN],
                timezone=user_input.get(CONF_TIMEZONE, DEFAULT_TIMEZONE),
            )

            try:
                valid = await client.validate_token()
                if not valid:
                    errors["base"] = "invalid_auth"
                else:
                    return self.async_create_entry(
                        title=DEFAULT_NAME,
                        data={
                            CONF_API_TOKEN: user_input[CONF_API_TOKEN],
                            CONF_TIMEZONE: user_input.get(CONF_TIMEZONE, DEFAULT_TIMEZONE),
                        },
                        options={
                            CONF_IS_PROSUMER: user_input.get(CONF_IS_PROSUMER, False),
                            CONF_ENABLE_PANEL: user_input.get(CONF_ENABLE_PANEL, True),
                            CONF_SCAN_INTERVAL_MINUTES: user_input.get(
                                CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL
                            ),
                        },
                    )
            except PstrykConnectionError:
                errors["base"] = "cannot_connect"
            except PstrykAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_TOKEN): str,
                    vol.Optional(CONF_IS_PROSUMER, default=False): bool,
                    vol.Optional(CONF_ENABLE_PANEL, default=True): bool,
                    vol.Optional(CONF_TIMEZONE, default=DEFAULT_TIMEZONE): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> PstrykOptionsFlow:
        """Get the options flow."""
        return PstrykOptionsFlow(config_entry)


class PstrykOptionsFlow(OptionsFlow):
    """Handle options for Pstryk Energy."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_IS_PROSUMER,
                        default=self.config_entry.options.get(CONF_IS_PROSUMER, False),
                    ): bool,
                    vol.Optional(
                        CONF_ENABLE_PANEL,
                        default=self.config_entry.options.get(CONF_ENABLE_PANEL, True),
                    ): bool,
                    vol.Optional(
                        CONF_SCAN_INTERVAL_MINUTES,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
                }
            ),
        )
