# Marcin Koźliński
# Ostatnia modyfikacja: 2026-04-12

"""TGE RDN Fixing I electricity prices scraped from tge.pl."""

from __future__ import annotations

import asyncio
import logging
import math
import re
from datetime import date, timedelta
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

TGE_RDN_URL = "https://tge.pl/energia-elektryczna-rdn"
# tge.pl blocks aiohttp User-Agent — override with a neutral one
_TGE_HEADERS = {"User-Agent": "python-requests/2.31.0"}


class TgeRdnError(Exception):
    """Error fetching TGE RDN data."""


async def fetch_rdn_fixing(
    session: aiohttp.ClientSession,
    target_date: date,
) -> dict[int, float]:
    """Fetch RDN Fixing I hourly prices for target_date from tge.pl.

    TGE publishes fixing for day D on session date D-1.
    The page dateShow=D-1 contains rows like "YYYY-MM-DD_H01 | 60 | price".

    Returns dict mapping hour (0-23) to price in PLN/kWh.
    Returns empty dict if no data for target_date.
    """
    session_date = target_date - timedelta(days=1)
    params = {"dateShow": session_date.strftime("%d-%m-%Y")}

    try:
        async with session.get(
            TGE_RDN_URL,
            params=params,
            headers=_TGE_HEADERS,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status != 200:
                raise TgeRdnError(f"TGE returned HTTP {response.status}")
            html = await response.text()
    except asyncio.TimeoutError as err:
        raise TgeRdnError(f"Timeout fetching TGE data for {target_date}") from err
    except aiohttp.ClientError as err:
        raise TgeRdnError(f"Connection error: {err}") from err

    return _parse_fixing_prices(html, target_date)


def _parse_fixing_prices(html: str, target_date: date) -> dict[int, float]:
    """Parse hourly Fixing I prices from TGE HTML table.

    Looks for rows: <td>YYYY-MM-DD_HXX</td><td>60</td><td>price</td>
    where duration=60 marks hourly (Fixing I) rows vs 15-min (Fixing II).
    """
    tds = re.findall(r"<td[^>]*>(.*?)</td>", html, re.DOTALL)
    tds_clean = [re.sub(r"<[^>]+>", "", td).strip() for td in tds]

    date_str = target_date.isoformat()
    pattern = re.compile(rf"^{re.escape(date_str)}_H(\d+)$")
    hourly: dict[int, float] = {}

    for i, cell in enumerate(tds_clean):
        m = pattern.match(cell)
        if m and i + 2 < len(tds_clean) and tds_clean[i + 1] == "60":
            hour_num = int(m.group(1))
            hour = hour_num - 1  # H01 = 00:00, H24 = 23:00
            price_raw = (
                tds_clean[i + 2]
                .replace("\xa0", "")
                .replace(" ", "")
                .replace(",", ".")
            )
            try:
                price_mwh = float(price_raw)
                price_net = price_mwh / 1000
                gross = math.floor(price_net * 1.23 * 100) / 100
                hourly[hour] = max(gross, 0.0)
            except ValueError:
                _LOGGER.warning(
                    "Cannot parse TGE price for %s H%02d: %s",
                    date_str, hour_num, price_raw,
                )

    if hourly:
        _LOGGER.debug(
            "Parsed %d hourly TGE RDN Fixing I prices for %s",
            len(hourly), date_str,
        )

    return hourly
