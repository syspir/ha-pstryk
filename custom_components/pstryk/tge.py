# Marcin Koźliński
# Ostatnia modyfikacja: 2026-04-09

"""TGE RDN electricity prices via PSE (api.raporty.pse.pl) JSON API."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

PSE_RCE_URL = "https://api.raporty.pse.pl/api/rce-pln"


class TgeRdnError(Exception):
    """Error fetching TGE RDN data."""


async def fetch_rce_prices(
    session: aiohttp.ClientSession,
    target_date: date,
) -> list[dict[str, Any]]:
    """Fetch RCE prices for a given date from PSE API.

    Returns list of dicts with keys: period, rce_pln, dtime, business_date.
    Each entry is a 15-minute interval. Returns empty list if no data.
    """
    params = {
        "$filter": f"business_date eq '{target_date.isoformat()}'",
    }
    try:
        async with session.get(
            PSE_RCE_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status != 200:
                raise TgeRdnError(f"PSE API returned HTTP {response.status}")
            data = await response.json()
    except aiohttp.ClientError as err:
        raise TgeRdnError(f"Connection error: {err}") from err

    return data.get("value", [])


def aggregate_hourly(records: list[dict[str, Any]]) -> dict[int, float]:
    """Aggregate 15-min RCE records into hourly averages.

    Returns dict mapping hour (0-23) to average price in PLN/MWh.
    """
    hourly_sums: dict[int, list[float]] = {}
    for rec in records:
        price = rec.get("rce_pln")
        if price is None:
            continue
        period = rec.get("period", "")
        # period format: "HH:MM - HH:MM", first part is start
        try:
            hour = int(period.split(":")[0])
        except (ValueError, IndexError):
            continue
        hourly_sums.setdefault(hour, []).append(price)

    return {
        hour: round(sum(prices) / len(prices) / 1000, 4)
        for hour, prices in hourly_sums.items()
        if prices
    }
