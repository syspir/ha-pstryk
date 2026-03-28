# Twoje-Miasto Sp. z o.o. / Marcin Koźliński
# Ostatnia modyfikacja: 2026-03-28

"""Sensor platform for Pstryk Energy integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfMass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_IS_PROSUMER, DOMAIN
from .coordinator import PstrykMetricsCoordinator, PstrykPricingCoordinator

_LOGGER = logging.getLogger(__name__)

CURRENCY_PLN = "PLN"
UNIT_PLN_KWH = "PLN/kWh"


@dataclass(frozen=True, kw_only=True)
class PstrykSensorEntityDescription(SensorEntityDescription):
    """Describe a Pstryk sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]
    extra_attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    coordinator_type: str = "metrics"  # "metrics" or "pricing"


def _safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested dicts."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


# ──────────── Energy Usage Sensors ────────────

ENERGY_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="energy_import_today",
        translation_key="energy_import_today",
        name="Energia pobrana dziś",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _safe_get(
            data, "daily_summary", "meterValues", "energy_active_import_register_total"
        ),
    ),
    PstrykSensorEntityDescription(
        key="energy_export_today",
        translation_key="energy_export_today",
        name="Energia oddana dziś",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _safe_get(
            data, "daily_summary", "meterValues", "energy_active_export_register_total"
        ),
    ),
    PstrykSensorEntityDescription(
        key="energy_balance_today",
        translation_key="energy_balance_today",
        name="Bilans energii dziś",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:scale-balance",
        value_fn=lambda data: _safe_get(
            data, "daily_summary", "meterValues", "energy_balance_total"
        ),
    ),
    PstrykSensorEntityDescription(
        key="energy_import_month",
        translation_key="energy_import_month",
        name="Energia pobrana w miesiącu",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _safe_get(
            data, "monthly_summary", "meterValues", "energy_active_import_register_total"
        ),
    ),
    PstrykSensorEntityDescription(
        key="energy_export_month",
        translation_key="energy_export_month",
        name="Energia oddana w miesiącu",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _safe_get(
            data, "monthly_summary", "meterValues", "energy_active_export_register_total"
        ),
    ),
    PstrykSensorEntityDescription(
        key="energy_balance_month",
        translation_key="energy_balance_month",
        name="Bilans energii w miesiącu",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:scale-balance",
        value_fn=lambda data: _safe_get(
            data, "monthly_summary", "meterValues", "energy_balance_total"
        ),
    ),
    # Current hour
    PstrykSensorEntityDescription(
        key="energy_import_current_hour",
        translation_key="energy_import_current_hour",
        name="Energia pobrana (bieżąca godzina)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        icon="mdi:flash",
        value_fn=lambda data: _safe_get(
            data, "current_frame", "metrics", "meterValues", "energy_active_import_register"
        ),
    ),
    PstrykSensorEntityDescription(
        key="energy_export_current_hour",
        translation_key="energy_export_current_hour",
        name="Energia oddana (bieżąca godzina)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        icon="mdi:flash-outline",
        value_fn=lambda data: _safe_get(
            data, "current_frame", "metrics", "meterValues", "energy_active_export_register"
        ),
    ),
)

# ──────────── Cost Sensors ────────────

COST_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="total_cost_today",
        translation_key="total_cost_today",
        name="Koszt energii dziś",
        native_unit_of_measurement=CURRENCY_PLN,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:cash",
        value_fn=lambda data: _safe_get(
            data, "daily_summary", "cost", "total_cost_total"
        ),
        extra_attrs_fn=lambda data: {
            "energy_cost_net": _safe_get(data, "daily_summary", "cost", "energy_active_import_register_cost_total"),
            "distribution_cost": _safe_get(data, "daily_summary", "cost", "distribution_cost_total"),
            "vat": _safe_get(data, "daily_summary", "cost", "vat_total"),
        },
    ),
    PstrykSensorEntityDescription(
        key="total_cost_month",
        translation_key="total_cost_month",
        name="Koszt energii w miesiącu",
        native_unit_of_measurement=CURRENCY_PLN,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:cash-multiple",
        value_fn=lambda data: _safe_get(
            data, "monthly_summary", "cost", "total_cost_total"
        ),
        extra_attrs_fn=lambda data: {
            "energy_cost_net": _safe_get(data, "monthly_summary", "cost", "energy_active_import_register_cost_total"),
            "distribution_cost": _safe_get(data, "monthly_summary", "cost", "distribution_cost_total"),
            "vat": _safe_get(data, "monthly_summary", "cost", "vat_total"),
        },
    ),
    PstrykSensorEntityDescription(
        key="cost_current_hour",
        translation_key="cost_current_hour",
        name="Koszt (bieżąca godzina)",
        native_unit_of_measurement=CURRENCY_PLN,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:cash-clock",
        value_fn=lambda data: _safe_get(
            data, "current_frame", "metrics", "cost", "total_cost"
        ),
        extra_attrs_fn=lambda data: {
            "energy_cost": _safe_get(data, "current_frame", "metrics", "cost", "energy_active_import_register_cost"),
            "distribution_cost": _safe_get(data, "current_frame", "metrics", "cost", "distribution_cost"),
            "vat": _safe_get(data, "current_frame", "metrics", "cost", "vat"),
        },
    ),
    PstrykSensorEntityDescription(
        key="energy_sold_value_today",
        translation_key="energy_sold_value_today",
        name="Wartość sprzedanej energii dziś",
        native_unit_of_measurement=CURRENCY_PLN,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:cash-plus",
        value_fn=lambda data: _safe_get(
            data, "daily_summary", "cost", "energy_sold_value_total"
        ),
    ),
    PstrykSensorEntityDescription(
        key="energy_sold_value_month",
        translation_key="energy_sold_value_month",
        name="Wartość sprzedanej energii w miesiącu",
        native_unit_of_measurement=CURRENCY_PLN,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:cash-plus",
        value_fn=lambda data: _safe_get(
            data, "monthly_summary", "cost", "energy_sold_value_total"
        ),
    ),
)

# ──────────── TGE Pricing Sensors ────────────

PRICING_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="current_price_gross",
        translation_key="current_price_gross",
        name="Aktualna cena energii (brutto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:currency-usd",
        coordinator_type="pricing",
        value_fn=lambda data: (
            _safe_get(data, "current_price", "price_gross")
            or _safe_get(data, "current_price", "price_gross_avg")
        ),
        extra_attrs_fn=lambda data: {
            "price_net": _safe_get(data, "current_price", "price_net") or _safe_get(data, "current_price", "price_net_avg"),
            "is_cheap": _safe_get(data, "current_price", "is_cheap"),
            "is_expensive": _safe_get(data, "current_price", "is_expensive"),
            "is_live": _safe_get(data, "current_price", "is_live"),
            "start": _safe_get(data, "current_price", "start"),
            "end": _safe_get(data, "current_price", "end"),
        },
    ),
    PstrykSensorEntityDescription(
        key="current_price_net",
        translation_key="current_price_net",
        name="Aktualna cena energii (netto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:currency-usd-off",
        coordinator_type="pricing",
        value_fn=lambda data: (
            _safe_get(data, "current_price", "price_net")
            or _safe_get(data, "current_price", "price_net_avg")
        ),
    ),
    PstrykSensorEntityDescription(
        key="avg_price_gross",
        translation_key="avg_price_gross",
        name="Średnia cena energii (brutto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:chart-line",
        coordinator_type="pricing",
        value_fn=lambda data: data.get("price_gross_avg"),
    ),
    PstrykSensorEntityDescription(
        key="avg_price_net",
        translation_key="avg_price_net",
        name="Średnia cena energii (netto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:chart-line-variant",
        coordinator_type="pricing",
        value_fn=lambda data: data.get("price_net_avg"),
    ),
    PstrykSensorEntityDescription(
        key="is_cheap_now",
        translation_key="is_cheap_now",
        name="Tania energia teraz",
        icon="mdi:thumb-up",
        coordinator_type="pricing",
        value_fn=lambda data: _safe_get(data, "current_price", "is_cheap"),
    ),
    PstrykSensorEntityDescription(
        key="is_expensive_now",
        translation_key="is_expensive_now",
        name="Droga energia teraz",
        icon="mdi:thumb-down",
        coordinator_type="pricing",
        value_fn=lambda data: _safe_get(data, "current_price", "is_expensive"),
    ),
    PstrykSensorEntityDescription(
        key="cheapest_upcoming_price",
        translation_key="cheapest_upcoming_price",
        name="Najtańsza nadchodząca cena",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-down-bold",
        coordinator_type="pricing",
        value_fn=lambda data: (
            _safe_get(data, "cheapest_upcoming", "price_gross")
            or _safe_get(data, "cheapest_upcoming", "price_gross_avg")
        ),
        extra_attrs_fn=lambda data: {
            "start": _safe_get(data, "cheapest_upcoming", "start"),
            "end": _safe_get(data, "cheapest_upcoming", "end"),
        },
    ),
    PstrykSensorEntityDescription(
        key="most_expensive_upcoming_price",
        translation_key="most_expensive_upcoming_price",
        name="Najdroższa nadchodząca cena",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-up-bold",
        coordinator_type="pricing",
        value_fn=lambda data: (
            _safe_get(data, "most_expensive_upcoming", "price_gross")
            or _safe_get(data, "most_expensive_upcoming", "price_gross_avg")
        ),
        extra_attrs_fn=lambda data: {
            "start": _safe_get(data, "most_expensive_upcoming", "start"),
            "end": _safe_get(data, "most_expensive_upcoming", "end"),
        },
    ),
    # Full price components for current hour
    PstrykSensorEntityDescription(
        key="current_full_price",
        translation_key="current_full_price",
        name="Pełna cena energii (z dystrybucją)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:cash-register",
        coordinator_type="pricing",
        value_fn=lambda data: _safe_get(data, "current_price", "full_price"),
        extra_attrs_fn=lambda data: {
            "base_price": _safe_get(data, "current_price", "base_price"),
            "dist_price": _safe_get(data, "current_price", "dist_price"),
            "service_price": _safe_get(data, "current_price", "service_price"),
            "vat_component": _safe_get(data, "current_price", "vat_component"),
            "excise_component": _safe_get(data, "current_price", "excise_component"),
        },
    ),
)

# ──────────── Prosumer Pricing Sensors ────────────

PROSUMER_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="prosumer_price_gross",
        translation_key="prosumer_price_gross",
        name="Cena prosumencka (brutto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:solar-power",
        coordinator_type="pricing",
        value_fn=lambda data: (
            _safe_get(data, "prosumer_current_price", "price_gross")
            or _safe_get(data, "prosumer_current_price", "price_gross_avg")
        ),
    ),
    PstrykSensorEntityDescription(
        key="prosumer_price_net",
        translation_key="prosumer_price_net",
        name="Cena prosumencka (netto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:solar-power-variant",
        coordinator_type="pricing",
        value_fn=lambda data: (
            _safe_get(data, "prosumer_current_price", "price_net")
            or _safe_get(data, "prosumer_current_price", "price_net_avg")
        ),
    ),
    PstrykSensorEntityDescription(
        key="prosumer_avg_price_gross",
        translation_key="prosumer_avg_price_gross",
        name="Średnia cena prosumencka (brutto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:chart-line",
        coordinator_type="pricing",
        value_fn=lambda data: data.get("prosumer_price_gross_avg"),
    ),
)

# ──────────── Unified Metrics Pricing Sensors ────────────

UNIFIED_PRICING_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="unified_price_current_hour",
        translation_key="unified_price_current_hour",
        name="Cena TGE (bieżąca godzina, z metryki)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:lightning-bolt",
        value_fn=lambda data: _safe_get(
            data, "current_frame", "metrics", "pricing", "price_gross"
        ),
        extra_attrs_fn=lambda data: {
            "price_net": _safe_get(data, "current_frame", "metrics", "pricing", "price_net"),
            "is_cheap": _safe_get(data, "current_frame", "metrics", "pricing", "is_cheap"),
            "is_expensive": _safe_get(data, "current_frame", "metrics", "pricing", "is_expensive"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pstryk sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    metrics_coordinator: PstrykMetricsCoordinator = data["metrics_coordinator"]
    pricing_coordinator: PstrykPricingCoordinator = data["pricing_coordinator"]
    is_prosumer = entry.options.get(CONF_IS_PROSUMER, False)

    entities: list[PstrykSensorEntity] = []

    # Add energy sensors
    for description in ENERGY_SENSORS:
        entities.append(
            PstrykSensorEntity(metrics_coordinator, description, entry)
        )

    # Add cost sensors
    for description in COST_SENSORS:
        entities.append(
            PstrykSensorEntity(metrics_coordinator, description, entry)
        )

    # Add TGE pricing sensors
    for description in PRICING_SENSORS:
        entities.append(
            PstrykSensorEntity(pricing_coordinator, description, entry)
        )

    # Add unified metrics pricing sensors
    for description in UNIFIED_PRICING_SENSORS:
        entities.append(
            PstrykSensorEntity(metrics_coordinator, description, entry)
        )

    # Add prosumer sensors if enabled
    if is_prosumer:
        for description in PROSUMER_SENSORS:
            entities.append(
                PstrykSensorEntity(pricing_coordinator, description, entry)
            )

    async_add_entities(entities)


class PstrykSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a Pstryk sensor."""

    entity_description: PstrykSensorEntityDescription

    def __init__(
        self,
        coordinator: PstrykMetricsCoordinator | PstrykPricingCoordinator,
        description: PstrykSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Pstryk Energy",
            manufacturer="Twoje-Miasto Sp. z o.o.",
            model="Smart Meter Integration",
            entry_type=None,
            configuration_url="https://www.twoje-miasto.pl",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        try:
            value = self.entity_description.value_fn(self.coordinator.data)
            if value is not None and isinstance(value, (int, float)):
                precision = self.entity_description.suggested_display_precision
                return round(value, precision if precision is not None else 4)
            return value
        except (KeyError, TypeError, IndexError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if (
            self.coordinator.data is None
            or self.entity_description.extra_attrs_fn is None
        ):
            return None
        try:
            return self.entity_description.extra_attrs_fn(self.coordinator.data)
        except (KeyError, TypeError, IndexError):
            return None
