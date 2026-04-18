# Marcin Koźliński
# Ostatnia modyfikacja: 2026-04-19

"""Number entities for Pstryk Energy TGE thresholds."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DEFAULT_TGE_ALWAYS_BUY_PRICE,
    DEFAULT_TGE_AVG_PERCENT,
    DEFAULT_TGE_DELTA_MAX,
    DEFAULT_TGE_DELTA_MIN,
    DEFAULT_TGE_MIN_SELL_PRICE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pstryk number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    tge_coordinator = data.get("tge_coordinator")
    if not tge_coordinator:
        return

    tge_device_info = DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_tge")},
    )

    async_add_entities([
        PstrykTgeNumber(
            coordinator=tge_coordinator,
            entry=entry,
            device_info=tge_device_info,
            key="tge_delta_min",
            translation_key="tge_delta_min",
            name="Delta ceny min TGE",
            icon="mdi:arrow-down-circle-outline",
            native_min=0.00,
            native_max=0.50,
            native_step=0.01,
            native_unit="PLN/kWh",
            default=DEFAULT_TGE_DELTA_MIN,
            attr="delta_min",
            divisor=1,
            migrate_from_groszy=True,
        ),
        PstrykTgeNumber(
            coordinator=tge_coordinator,
            entry=entry,
            device_info=tge_device_info,
            key="tge_delta_max",
            translation_key="tge_delta_max",
            name="Delta ceny max TGE",
            icon="mdi:arrow-up-circle-outline",
            native_min=0.00,
            native_max=0.50,
            native_step=0.01,
            native_unit="PLN/kWh",
            default=DEFAULT_TGE_DELTA_MAX,
            attr="delta_max",
            divisor=1,
            migrate_from_groszy=True,
        ),
        PstrykTgeNumber(
            coordinator=tge_coordinator,
            entry=entry,
            device_info=tge_device_info,
            key="tge_avg_percent",
            translation_key="tge_avg_percent",
            name="Próg średniej TGE",
            icon="mdi:approximately-equal-box",
            native_min=1,
            native_max=100,
            native_step=1,
            native_unit="%",
            default=DEFAULT_TGE_AVG_PERCENT,
            attr="avg_percent",
            divisor=1,
        ),
        PstrykTgeNumber(
            coordinator=tge_coordinator,
            entry=entry,
            device_info=tge_device_info,
            key="tge_min_sell_price",
            translation_key="tge_min_sell_price",
            name="Minimalna cena sprzedaży TGE",
            icon="mdi:cash-lock",
            native_min=0.00,
            native_max=5.00,
            native_step=0.01,
            native_unit="PLN/kWh",
            default=DEFAULT_TGE_MIN_SELL_PRICE,
            attr="min_sell_price",
            divisor=1,
            migrate_from_groszy=True,
        ),
        PstrykTgeNumber(
            coordinator=tge_coordinator,
            entry=entry,
            device_info=tge_device_info,
            key="tge_always_buy_price",
            translation_key="tge_always_buy_price",
            name="Cena zawsze kupuj TGE",
            icon="mdi:cash-check",
            native_min=-1.00,
            native_max=5.00,
            native_step=0.01,
            native_unit="PLN/kWh",
            default=DEFAULT_TGE_ALWAYS_BUY_PRICE,
            attr="always_buy_price",
            divisor=1,
            migrate_from_groszy=True,
        ),
    ])


class PstrykTgeNumber(RestoreEntity, NumberEntity):
    """Number entity for TGE threshold configuration."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
        key: str,
        translation_key: str,
        name: str,
        icon: str,
        native_min: float,
        native_max: float,
        native_unit: str,
        default: float,
        attr: str,
        divisor: float,
        native_step: float = 1.0,
        migrate_from_groszy: bool = False,
    ) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = translation_key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_min_value = native_min
        self._attr_native_max_value = native_max
        self._attr_native_step = native_step
        self._attr_native_unit_of_measurement = native_unit
        self._attr_device_info = device_info
        self._default = default
        self._attr = attr
        self._divisor = divisor
        self._migrate_from_groszy = migrate_from_groszy
        self._attr_native_value = default

    async def async_added_to_hass(self) -> None:
        """Restore last state on startup."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                value = float(last_state.state)
                # Migracja z poprzedniej wersji, gdy wartość była w groszach
                if self._migrate_from_groszy and value > self._attr_native_max_value:
                    value = value / 100
                self._attr_native_value = value
            except (ValueError, TypeError):
                self._attr_native_value = self._default
        self._apply_to_coordinator()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        self._attr_native_value = value
        self._apply_to_coordinator()
        self.async_write_ha_state()

    def _apply_to_coordinator(self) -> None:
        """Push current value to coordinator and trigger recalculation."""
        val = self._attr_native_value / self._divisor if self._divisor != 1 else self._attr_native_value
        setattr(self._coordinator, self._attr, val)
        if self._coordinator.data:
            self._coordinator.recalculate_current()
