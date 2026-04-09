# Marcin Koźliński
# Ostatnia modyfikacja: 2026-04-09 (v0.7.3)

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
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfMass,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_IS_PROSUMER, DOMAIN
from .coordinator import (
    PstrykBleBoxCoordinator,
    PstrykMetricsCoordinator,
    PstrykPricingCoordinator,
    PstrykTgeCoordinator,
)

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


def _round05(value: float | None) -> float | None:
    """Round value to nearest 0.05."""
    if value is None:
        return None
    return round(round(value / 0.05) * 0.05, 4)


def _tge_cena_lt_avg23(data: dict) -> int | None:
    """Return 1 if current price <= avg_today * 2/3, else 0."""
    price = data.get("current_price")
    hours = _safe_get(data, "today", "hours") or {}
    if price is None or not hours:
        return None
    avg = sum(hours.values()) / len(hours)
    return 1 if price <= avg * 2 / 3 else 0


def _tge_cena_lt_avg23_attrs(data: dict) -> dict:
    hours = _safe_get(data, "today", "hours") or {}
    avg = sum(hours.values()) / len(hours) if hours else None
    return {
        "current_price": data.get("current_price"),
        "avg_today": round(avg, 4) if avg is not None else None,
        "threshold_2_3_avg": round(avg * 2 / 3, 4) if avg is not None else None,
    }


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
        state_class=SensorStateClass.TOTAL,
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
        state_class=SensorStateClass.TOTAL,
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
        key="current_full_price",
        translation_key="current_full_price",
        name="Cena energii zakup (brutto)",
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
            "is_cheap": _safe_get(data, "current_price", "is_cheap"),
            "is_expensive": _safe_get(data, "current_price", "is_expensive"),
            "start": _safe_get(data, "current_price", "start"),
            "end": _safe_get(data, "current_price", "end"),
            "cheapest_upcoming_price": _safe_get(data, "cheapest_upcoming", "full_price") or _safe_get(data, "cheapest_upcoming", "price_gross"),
            "cheapest_upcoming_start": _safe_get(data, "cheapest_upcoming", "start"),
            "cheapest_upcoming_end": _safe_get(data, "cheapest_upcoming", "end"),
            "most_expensive_upcoming_price": _safe_get(data, "most_expensive_upcoming", "full_price") or _safe_get(data, "most_expensive_upcoming", "price_gross"),
            "most_expensive_upcoming_start": _safe_get(data, "most_expensive_upcoming", "start"),
            "most_expensive_upcoming_end": _safe_get(data, "most_expensive_upcoming", "end"),
            "price_forecast": [
                {
                    "start": f.get("start"),
                    "end": f.get("end"),
                    "full_price": f.get("full_price"),
                    "price_gross": f.get("price_gross"),
                    "is_cheap": f.get("is_cheap"),
                    "is_expensive": f.get("is_expensive"),
                }
                for f in data.get("all_frames", [])
                if (f.get("full_price") or 0) > 0 or (f.get("price_gross") or 0) > 0
            ],
        },
    ),
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
            _safe_get(data, "cheapest_upcoming", "full_price")
            or _safe_get(data, "cheapest_upcoming", "price_gross")
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
            _safe_get(data, "most_expensive_upcoming", "full_price")
            or _safe_get(data, "most_expensive_upcoming", "price_gross")
        ),
        extra_attrs_fn=lambda data: {
            "start": _safe_get(data, "most_expensive_upcoming", "start"),
            "end": _safe_get(data, "most_expensive_upcoming", "end"),
        },
    ),
)

# ──────────── Unified Metrics Pricing Sensors ────────────

UNIFIED_PRICING_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="unified_price_current_hour",
        translation_key="unified_price_current_hour",
        name="Cena TGE (bieżąca godzina)",
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

# ──────────── Prosumer Pricing Sensors ────────────

PROSUMER_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="prosumer_price_gross",
        translation_key="prosumer_price_gross",
        name="Cena sprzedaży energii (brutto)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:solar-power",
        coordinator_type="pricing",
        value_fn=lambda data: (
            _safe_get(data, "prosumer_current_price", "price_gross")
            or _safe_get(data, "prosumer_current_price", "price_gross_avg")
        ),
        extra_attrs_fn=lambda data: {
            "price_net": _safe_get(data, "prosumer_current_price", "price_net") or _safe_get(data, "prosumer_current_price", "price_net_avg"),
            "start": _safe_get(data, "prosumer_current_price", "start"),
            "end": _safe_get(data, "prosumer_current_price", "end"),
        },
    ),
    PstrykSensorEntityDescription(
        key="prosumer_price_net",
        translation_key="prosumer_price_net",
        name="Cena sprzedaży energii (netto)",
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


# ──────────── TGE RDN Sensors ────────────

TGE_RDN_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    PstrykSensorEntityDescription(
        key="tge_rdn_current_price",
        translation_key="tge_rdn_current_price",
        name="Cena RDN (bieżąca godzina)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:currency-usd",
        coordinator_type="tge",
        value_fn=lambda data: data.get("current_price"),
        extra_attrs_fn=lambda data: {
            "hour": data.get("current_hour"),
            "date": _safe_get(data, "today", "date"),
            "price_forecast_today": [
                {"hour": h, "price": p}
                for h, p in sorted((_safe_get(data, "today", "hours") or {}).items())
            ],
            "price_forecast_tomorrow": [
                {"hour": h, "price": p}
                for h, p in sorted((_safe_get(data, "tomorrow", "hours") or {}).items())
            ] if data.get("tomorrow") else [],
            "tomorrow_available": data.get("tomorrow") is not None,
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_min_price_today",
        translation_key="tge_rdn_min_price_today",
        name="Cena RDN najniższa dziś",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-down-bold",
        coordinator_type="tge",
        value_fn=lambda data: _safe_get(data, "today", "min_price"),
        extra_attrs_fn=lambda data: {
            "hour": _safe_get(data, "today", "min_hour"),
            "date": _safe_get(data, "today", "date"),
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_max_price_today",
        translation_key="tge_rdn_max_price_today",
        name="Cena RDN najwyższa dziś",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-up-bold",
        coordinator_type="tge",
        value_fn=lambda data: _safe_get(data, "today", "max_price"),
        extra_attrs_fn=lambda data: {
            "hour": _safe_get(data, "today", "max_hour"),
            "date": _safe_get(data, "today", "date"),
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_min_price_tomorrow",
        translation_key="tge_rdn_min_price_tomorrow",
        name="Cena RDN najniższa jutro",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-down-bold-circle-outline",
        coordinator_type="tge",
        value_fn=lambda data: _safe_get(data, "tomorrow", "min_price"),
        extra_attrs_fn=lambda data: {
            "hour": _safe_get(data, "tomorrow", "min_hour"),
            "date": _safe_get(data, "tomorrow", "date"),
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_max_price_tomorrow",
        translation_key="tge_rdn_max_price_tomorrow",
        name="Cena RDN najwyższa jutro",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-up-bold-circle-outline",
        coordinator_type="tge",
        value_fn=lambda data: _safe_get(data, "tomorrow", "max_price"),
        extra_attrs_fn=lambda data: {
            "hour": _safe_get(data, "tomorrow", "max_hour"),
            "date": _safe_get(data, "tomorrow", "date"),
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_cena0",
        translation_key="tge_rdn_cena0",
        name="Cena RDN ≤ 0 (cena0)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:alert-circle-outline",
        coordinator_type="tge",
        value_fn=lambda data: (
            None if (p := data.get("current_price")) is None
            else (1 if p <= 0 else 0)
        ),
        extra_attrs_fn=lambda data: {
            "current_price": data.get("current_price"),
            "hour": data.get("current_hour"),
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_min_price_today_r05",
        translation_key="tge_rdn_min_price_today_r05",
        name="Cena RDN najniższa dziś (co 0,05)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-down-bold",
        coordinator_type="tge",
        value_fn=lambda data: _round05(_safe_get(data, "today", "min_price")),
        extra_attrs_fn=lambda data: {
            "hour": _safe_get(data, "today", "min_hour"),
            "date": _safe_get(data, "today", "date"),
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_max_price_today_r05",
        translation_key="tge_rdn_max_price_today_r05",
        name="Cena RDN najwyższa dziś (co 0,05)",
        native_unit_of_measurement=UNIT_PLN_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-up-bold",
        coordinator_type="tge",
        value_fn=lambda data: _round05(_safe_get(data, "today", "max_price")),
        extra_attrs_fn=lambda data: {
            "hour": _safe_get(data, "today", "max_hour"),
            "date": _safe_get(data, "today", "date"),
        },
    ),
    PstrykSensorEntityDescription(
        key="tge_rdn_cena_lt_avg23",
        translation_key="tge_rdn_cena_lt_avg23",
        name="Cena RDN ≤ 2/3 średniej dnia",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:approximately-equal-box",
        coordinator_type="tge",
        value_fn=_tge_cena_lt_avg23,
        extra_attrs_fn=_tge_cena_lt_avg23_attrs,
    ),
)


# ──────────── BleBox Local Meter Sensors ────────────


def _blebox_phase(data: dict, phase: int, key: str) -> float | None:
    """Get value from BleBox phase data."""
    if isinstance(data, dict):
        phases = data.get("phases")
        if isinstance(phases, dict):
            phase_data = phases.get(phase)
            if isinstance(phase_data, dict):
                return phase_data.get(key)
    return None


def _blebox_tg_phi(data: dict, key: str) -> float | None:
    """Get tg φ value from BleBox coordinator data."""
    if isinstance(data, dict):
        tg_phi = data.get("tg_phi")
        if isinstance(tg_phi, dict):
            return tg_phi.get(key)
    return None


BLEBOX_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    # Total active power
    PstrykSensorEntityDescription(
        key="blebox_power",
        translation_key="blebox_power",
        name="Moc czynna",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 0, "activePower"),
    ),
    # Per-phase active power
    PstrykSensorEntityDescription(
        key="blebox_power_l1",
        translation_key="blebox_power_l1",
        name="Moc czynna L1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 1, "activePower"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_power_l2",
        translation_key="blebox_power_l2",
        name="Moc czynna L2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 2, "activePower"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_power_l3",
        translation_key="blebox_power_l3",
        name="Moc czynna L3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 3, "activePower"),
    ),
    # Per-phase voltage
    PstrykSensorEntityDescription(
        key="blebox_voltage_l1",
        translation_key="blebox_voltage_l1",
        name="Napięcie L1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:sine-wave",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 1, "voltage"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_voltage_l2",
        translation_key="blebox_voltage_l2",
        name="Napięcie L2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:sine-wave",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 2, "voltage"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_voltage_l3",
        translation_key="blebox_voltage_l3",
        name="Napięcie L3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:sine-wave",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 3, "voltage"),
    ),
    # Per-phase current
    PstrykSensorEntityDescription(
        key="blebox_current_l1",
        translation_key="blebox_current_l1",
        name="Prąd L1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        icon="mdi:current-ac",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 1, "current"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_current_l2",
        translation_key="blebox_current_l2",
        name="Prąd L2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        icon="mdi:current-ac",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 2, "current"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_current_l3",
        translation_key="blebox_current_l3",
        name="Prąd L3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        icon="mdi:current-ac",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 3, "current"),
    ),
    # Frequency
    PstrykSensorEntityDescription(
        key="blebox_frequency",
        translation_key="blebox_frequency",
        name="Częstotliwość sieci",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:waveform",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 0, "frequency"),
    ),
    # Energy counters (total register from meter)
    PstrykSensorEntityDescription(
        key="blebox_energy_import",
        translation_key="blebox_energy_import",
        name="Energia pobrana (licznik)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        icon="mdi:transmission-tower-import",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 0, "forwardActiveEnergy"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_energy_export",
        translation_key="blebox_energy_export",
        name="Energia oddana (licznik)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        icon="mdi:transmission-tower-export",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_phase(data, 0, "reverseActiveEnergy"),
    ),
)


# ──────────── BleBox tg φ Sensors ────────────

BLEBOX_TG_PHI_SENSORS: tuple[PstrykSensorEntityDescription, ...] = (
    # 1 minute (instantaneous from power)
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qi_minute",
        translation_key="blebox_tg_phi_qi_minute",
        name="tg φ QI (chwilowe)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "minute_qi"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qiv_minute",
        translation_key="blebox_tg_phi_qiv_minute",
        name="tg φ QIV (chwilowe)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "minute_qiv"),
    ),
    # Month
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qi_month",
        translation_key="blebox_tg_phi_qi_month",
        name="tg φ QI (miesiąc)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "month_qi"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qiv_month",
        translation_key="blebox_tg_phi_qiv_month",
        name="tg φ QIV (miesiąc)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "month_qiv"),
    ),
    # Year
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qi_year",
        translation_key="blebox_tg_phi_qi_year",
        name="tg φ QI (rok)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "year_qi"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qiv_year",
        translation_key="blebox_tg_phi_qiv_year",
        name="tg φ QIV (rok)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "year_qiv"),
    ),
    # Total (all-time)
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qi_total",
        translation_key="blebox_tg_phi_qi_total",
        name="tg φ QI (całościowe)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "total_qi"),
    ),
    PstrykSensorEntityDescription(
        key="blebox_tg_phi_qiv_total",
        translation_key="blebox_tg_phi_qiv_total",
        name="tg φ QIV (całościowe)",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        icon="mdi:angle-acute",
        coordinator_type="blebox",
        value_fn=lambda data: _blebox_tg_phi(data, "total_qiv"),
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
    tge_coordinator: PstrykTgeCoordinator | None = data.get("tge_coordinator")
    blebox_coordinator: PstrykBleBoxCoordinator | None = data.get("blebox_coordinator")
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

    # Add TGE RDN sensors (osobne urządzenie TGE)
    if tge_coordinator:
        tge_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_tge")},
            name="TGE RDN",
            manufacturer="PSE S.A.",
            model="Rynek Dnia Następnego (RDN)",
            configuration_url="https://api.raporty.pse.pl",
        )
        for description in TGE_RDN_SENSORS:
            entities.append(
                PstrykSensorEntity(tge_coordinator, description, entry, device_info=tge_device_info)
            )

    # Add BleBox local meter sensors
    if blebox_coordinator:
        blebox_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_blebox")},
            name="Pstryk Meter",
            manufacturer="BleBox",
            model="Smart Meter",
            via_device=(DOMAIN, entry.entry_id),
        )
        for description in (*BLEBOX_SENSORS, *BLEBOX_TG_PHI_SENSORS):
            entities.append(
                PstrykSensorEntity(
                    blebox_coordinator, description, entry,
                    device_info=blebox_device_info,
                )
            )

    async_add_entities(entities)


class PstrykSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a Pstryk sensor."""

    entity_description: PstrykSensorEntityDescription

    def __init__(
        self,
        coordinator: PstrykMetricsCoordinator | PstrykPricingCoordinator | PstrykTgeCoordinator | PstrykBleBoxCoordinator,
        description: PstrykSensorEntityDescription,
        entry: ConfigEntry,
        device_info: DeviceInfo | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = device_info or DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Pstryk Energy",
            manufacturer="Marcin Koźliński",
            model="Smart Meter Integration",
            entry_type=None,
            configuration_url="https://github.com/syspir/ha-pstryk",
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
