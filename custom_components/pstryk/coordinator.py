# Marcin Koźliński
# Ostatnia modyfikacja: 2026-04-19

"""Data update coordinators for Pstryk Energy."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PstrykApiClient, PstrykApiError, PstrykAuthError
from .blebox import PstrykBleBoxClient, PstrykBleBoxError
from .const import ATTRIBUTION, DOMAIN
from .tge import TgeRdnError, fetch_rdn_fixing

_LOGGER = logging.getLogger(__name__)


_STORE_VERSION = 1


class PstrykMetricsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for unified metrics data (energy, cost)."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PstrykApiClient,
        update_interval: timedelta,
        timezone: str,
        entry_id: str,
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
        self._store = Store(hass, _STORE_VERSION, f"{DOMAIN}_metrics_{entry_id}")

    async def async_load_stored_data(self) -> None:
        """Load last known data from persistent storage."""
        stored = await self._store.async_load()
        if stored:
            self.async_set_updated_data(stored)
            _LOGGER.debug("Restored metrics data from storage")

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

            result = {
                "hourly": hourly,
                "monthly": monthly,
                "current_frame": current_frame,
                "daily_summary": hourly.get("summary", {}),
                "monthly_summary": monthly.get("summary", {}),
            }
            await self._store.async_save(result)
            return result
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
        entry_id: str = "",
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
        self._store = Store(hass, _STORE_VERSION, f"{DOMAIN}_pricing_{entry_id}")

    async def async_load_stored_data(self) -> None:
        """Load last known raw pricing data from persistent storage."""
        stored = await self._store.async_load()
        if stored:
            self._raw_pricing = stored.get("raw_pricing")
            self._raw_prosumer = stored.get("raw_prosumer")
            if self._raw_pricing:
                self.async_set_updated_data(self._process_data())
                _LOGGER.debug("Restored pricing data from storage")

    def _find_current_frame(self, frames: list[dict]) -> dict | None:
        """Find the frame matching current time based on start/end.

        If no exact match, return the most recent past frame as fallback.
        """
        now = datetime.now(timezone.utc)
        best_past: dict | None = None
        best_past_start: datetime | None = None
        for frame in frames:
            start = frame.get("start")
            end = frame.get("end")
            if start and end:
                try:
                    frame_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    frame_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    if frame_start <= now < frame_end:
                        return frame
                    if frame_start <= now and (best_past_start is None or frame_start > best_past_start):
                        best_past = frame
                        best_past_start = frame_start
                except (ValueError, TypeError):
                    continue
        return best_past

    def _process_data(self) -> dict[str, Any]:
        """Process stored raw data to determine current prices."""
        pricing = self._raw_pricing or {}

        all_frames = pricing.get("frames", [])
        current_price = self._find_current_frame(all_frames)
        next_prices: list[dict] = []
        cheapest_upcoming = None
        most_expensive_upcoming = None

        if all_frames:
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
            result = self._process_data()
            await self._store.async_save({
                "raw_pricing": self._raw_pricing,
                "raw_prosumer": self._raw_prosumer,
            })
            return result
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


class PstrykTgeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for TGE RDN prices via PSE API (api.raporty.pse.pl)."""

    def __init__(
        self,
        hass: HomeAssistant,
        session,
        update_interval: timedelta,
        entry_id: str,
        delta_min: float = 0.05,
        delta_max: float = 0.05,
        avg_percent: int = 67,
        min_sell_price: float = 1.00,
        always_buy_price: float = 0.23,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_tge",
            update_interval=update_interval,
        )
        self._session = session
        self.attribution = "Dane z TGE S.A. (tge.pl) — RDN Fixing I"
        self._store = Store(hass, _STORE_VERSION, f"{DOMAIN}_tge_{entry_id}")
        self._tomorrow_last_retry = None
        self.delta_min = delta_min
        self.delta_max = delta_max
        self.avg_percent = avg_percent
        self.min_sell_price = min_sell_price
        self.always_buy_price = always_buy_price

    async def async_load_stored_data(self) -> None:
        """Load last known data from persistent storage."""
        stored = await self._store.async_load()
        if stored:
            # Discard stale cache — if today's date doesn't match, start fresh
            import zoneinfo
            today_str = datetime.now(
                zoneinfo.ZoneInfo("Europe/Warsaw"),
            ).date().isoformat()
            today_data = stored.get("today")
            if not today_data or today_data.get("date") != today_str:
                _LOGGER.info(
                    "TGE RDN stored data is stale (date=%s, today=%s), discarding",
                    today_data.get("date") if today_data else None,
                    today_str,
                )
                return
            # JSON storage converts int keys to strings — normalize hours dicts
            for key in ("today", "tomorrow"):
                day = stored.get(key)
                if day and "hours" in day:
                    day["hours"] = {int(k): v for k, v in day["hours"].items()}
            # Config values always from coordinator instance, not storage
            stored["delta_min"] = self.delta_min
            stored["delta_max"] = self.delta_max
            stored["avg_percent"] = self.avg_percent
            stored["min_sell_price"] = self.min_sell_price
            stored["always_buy_price"] = self.always_buy_price
            self.async_set_updated_data(stored)
            _LOGGER.debug("Restored TGE RDN data from storage")

    @staticmethod
    def _build_day_data(
        hourly: dict[int, float], target_date: str,
    ) -> dict[str, Any] | None:
        """Build structured day data from hourly prices."""
        if not hourly:
            return None
        # Normalize keys to int (JSON storage converts int keys to strings)
        hourly = {int(k): v for k, v in hourly.items()}
        min_hour = min(hourly, key=hourly.get)
        max_hour = max(hourly, key=hourly.get)
        return {
            "date": target_date,
            "hours": hourly,
            "min_price": hourly[min_hour],
            "min_hour": min_hour,
            "max_price": hourly[max_hour],
            "max_hour": max_hour,
        }

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch RDN Fixing I prices for today and tomorrow from tge.pl."""
        import zoneinfo
        now = datetime.now(zoneinfo.ZoneInfo("Europe/Warsaw"))
        today = now.date()
        tomorrow = today + timedelta(days=1)

        try:
            today_hourly = await fetch_rdn_fixing(self._session, today)
            tomorrow_hourly = await fetch_rdn_fixing(self._session, tomorrow)
        except TgeRdnError as err:
            if self.data:
                _LOGGER.warning("TGE RDN error, keeping last data: %s", err)
                return self.data
            raise UpdateFailed(f"TGE RDN error: {err}") from err

        # If parser returned empty data for today, keep existing data
        if not today_hourly:
            if self.data:
                _LOGGER.warning(
                    "TGE RDN: no hourly data parsed for %s, keeping last data", today,
                )
                return self.data
            raise UpdateFailed(f"TGE RDN: no data for {today}")

        today_data = self._build_day_data(today_hourly, today.isoformat())
        tomorrow_data = self._build_day_data(tomorrow_hourly, tomorrow.isoformat())

        current_hour = now.hour
        current_price = today_hourly.get(current_hour)

        result = {
            "today": today_data,
            "tomorrow": tomorrow_data,
            "current_price": current_price,
            "current_hour": current_hour,
        }
        if tomorrow_data:
            self._tomorrow_last_retry = None
        await self._store.async_save(result)
        result["delta_min"] = self.delta_min
        result["delta_max"] = self.delta_max
        result["avg_percent"] = self.avg_percent
        result["min_sell_price"] = self.min_sell_price
        result["always_buy_price"] = self.always_buy_price
        return result

    def recalculate_current(self) -> None:
        """Recalculate current hour price from stored data (no fetch)."""
        if not self.data:
            return
        import zoneinfo
        now = datetime.now(zoneinfo.ZoneInfo("Europe/Warsaw"))
        today_str = now.date().isoformat()
        tomorrow_str = (now.date() + timedelta(days=1)).isoformat()
        current_hour = now.hour

        today = self.data.get("today")
        current_price = None
        if today and today.get("date") == today_str:
            hours = today.get("hours", {})
            current_price = hours.get(current_hour)
            if current_price is None:
                current_price = hours.get(str(current_hour))

        updated = dict(self.data)
        updated["current_price"] = current_price
        updated["current_hour"] = current_hour
        updated["delta_min"] = self.delta_min
        updated["delta_max"] = self.delta_max
        updated["avg_percent"] = self.avg_percent
        updated["min_sell_price"] = self.min_sell_price
        updated["always_buy_price"] = self.always_buy_price
        self.async_set_updated_data(updated)

        # Refresh needed: today data stale/missing, or tomorrow missing after 13:00
        need_refresh = False
        if not today or today.get("date") != today_str:
            need_refresh = True
        elif current_hour >= 13:
            tom = self.data.get("tomorrow")
            if not tom or tom.get("date") != tomorrow_str:
                need_refresh = True

        if need_refresh:
            last = getattr(self, "_tomorrow_last_retry", None)
            if last is None or (now - last).total_seconds() >= 900:
                self._tomorrow_last_retry = now
                _LOGGER.debug("TGE RDN data stale/missing, requesting refresh")
                self.hass.async_create_task(self.async_request_refresh())


class PstrykBleBoxCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for local BleBox meter data (every 5s)."""

    # Energy register keys used for tg φ calculation
    _ENERGY_KEYS = ("forwardActiveEnergy", "forwardReactiveEnergy", "reverseReactiveEnergy")

    def __init__(
        self,
        hass: HomeAssistant,
        client: PstrykBleBoxClient,
        update_interval: timedelta,
        entry_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_blebox",
            update_interval=update_interval,
        )
        self.client = client
        self.attribution = ATTRIBUTION
        self._store = Store(hass, _STORE_VERSION, f"{DOMAIN}_blebox_{entry_id}")
        # Period start register snapshots for tg φ
        self._month_start: dict[str, float] | None = None
        self._month_start_month: int | None = None
        self._year_start: dict[str, float] | None = None
        self._year_start_year: int | None = None

    async def async_load_periods(self) -> None:
        """Load period start snapshots from persistent storage."""
        data = await self._store.async_load()
        if not data:
            return
        self._month_start = data.get("month_start")
        self._month_start_month = data.get("month_start_month")
        self._year_start = data.get("year_start")
        self._year_start_year = data.get("year_start_year")
        _LOGGER.debug("Loaded BleBox tg φ period data from storage")

    async def _async_save_periods(self) -> None:
        """Save period start snapshots to persistent storage."""
        await self._store.async_save({
            "month_start": self._month_start,
            "month_start_month": self._month_start_month,
            "year_start": self._year_start,
            "year_start_year": self._year_start_year,
        })

    @staticmethod
    def _calc_tg_phi(
        start: dict[str, float], end: dict[str, float],
    ) -> tuple[float | None, float | None]:
        """Calculate tg φ QI and QIV from energy register deltas.

        tg φ QI  = ΔEb_indukcyjna / ΔEa_pobrana
        tg φ QIV = ΔEb_pojemnościowa / ΔEa_pobrana
        """
        delta_active = (
            end.get("forwardActiveEnergy", 0)
            - start.get("forwardActiveEnergy", 0)
        )
        if delta_active < 0.001:
            return None, None
        delta_qi = (
            end.get("forwardReactiveEnergy", 0)
            - start.get("forwardReactiveEnergy", 0)
        )
        delta_qiv = (
            end.get("reverseReactiveEnergy", 0)
            - start.get("reverseReactiveEnergy", 0)
        )
        return delta_qi / delta_active, delta_qiv / delta_active

    def _snapshot(self, total: dict[str, float]) -> dict[str, float]:
        """Take a snapshot of energy registers for period tracking."""
        return {k: total.get(k, 0) for k in self._ENERGY_KEYS}

    async def _build_tg_phi(self, total: dict[str, float]) -> dict[str, float | None]:
        """Calculate tg φ for all periods."""
        now = datetime.now()
        tg_phi: dict[str, float | None] = {}
        save_needed = False

        # 1 minute — instantaneous from power (reactivePower / activePower)
        active_p = total.get("activePower", 0)
        if active_p > 0:
            reactive_p = total.get("reactivePower", 0)
            tg_phi["minute_qi"] = max(0.0, reactive_p) / active_p
            tg_phi["minute_qiv"] = max(0.0, -reactive_p) / active_p
        else:
            tg_phi["minute_qi"] = None
            tg_phi["minute_qiv"] = None

        # Month — energy delta from start of month
        if self._month_start_month != now.month:
            self._month_start = self._snapshot(total)
            self._month_start_month = now.month
            save_needed = True
        if self._month_start:
            qi, qiv = self._calc_tg_phi(self._month_start, total)
            tg_phi["month_qi"] = qi
            tg_phi["month_qiv"] = qiv
        else:
            tg_phi["month_qi"] = None
            tg_phi["month_qiv"] = None

        # Year — energy delta from start of year
        if self._year_start_year != now.year:
            self._year_start = self._snapshot(total)
            self._year_start_year = now.year
            save_needed = True
        if self._year_start:
            qi, qiv = self._calc_tg_phi(self._year_start, total)
            tg_phi["year_qi"] = qi
            tg_phi["year_qiv"] = qiv
        else:
            tg_phi["year_qi"] = None
            tg_phi["year_qiv"] = None

        # Total — all-time from meter registers
        fae = total.get("forwardActiveEnergy", 0)
        if fae > 0:
            tg_phi["total_qi"] = total.get("forwardReactiveEnergy", 0) / fae
            tg_phi["total_qiv"] = total.get("reverseReactiveEnergy", 0) / fae
        else:
            tg_phi["total_qi"] = None
            tg_phi["total_qiv"] = None

        if save_needed:
            await self._async_save_periods()

        return tg_phi

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch meter data from local BleBox API."""
        try:
            raw = await self.client.get_state()
            phases = PstrykBleBoxClient.parse_sensors(raw)
            total = phases.get(0, {})
            return {
                "phases": phases,
                "tg_phi": await self._build_tg_phi(total),
            }
        except PstrykBleBoxError as err:
            if self.data:
                _LOGGER.warning("BleBox meter error, keeping last data: %s", err)
                return self.data
            raise UpdateFailed(f"BleBox meter error: {err}") from err
