#!/usr/bin/env python3
"""Test TGE RDN coordinator + sensor logic end-to-end.

Czyta HTML z plików (pobrane curlem), symuluje _build_day_data i recalculate_current,
a następnie sprawdza wszystkie value_fn sensorów TGE RDN.

Użycie:
  curl -s "https://tge.pl/energia-elektryczna-rdn?dateShow=DD-MM-YYYY" -o /tmp/tge_today.html
  curl -s "https://tge.pl/energia-elektryczna-rdn?dateShow=DD-MM-YYYY" -o /tmp/tge_tomorrow.html
  python3 test_tge.py
"""

import json
import math
import re
import sys
import zoneinfo
from datetime import date, datetime, timedelta


# ── TGE parser (z tge.py) ──

def parse_fixing_prices(html: str, target_date: date) -> dict[int, float]:
    tds = re.findall(r"<td[^>]*>(.*?)</td>", html, re.DOTALL)
    tds_clean = [re.sub(r"<[^>]+>", "", td).strip() for td in tds]
    date_str = target_date.isoformat()
    pattern = re.compile(rf"^{re.escape(date_str)}_H(\d+)$")
    hourly: dict[int, float] = {}
    for i, cell in enumerate(tds_clean):
        m = pattern.match(cell)
        if m and i + 2 < len(tds_clean) and tds_clean[i + 1] == "60":
            hour_num = int(m.group(1))
            hour = hour_num - 1
            price_raw = (
                tds_clean[i + 2]
                .replace("\xa0", "")
                .replace(" ", "")
                .replace(",", ".")
            )
            price_mwh = float(price_raw)
            price_net = price_mwh / 1000
            gross = math.floor(price_net * 1.23 * 100) / 100
            hourly[hour] = max(gross, 0.0)
    return hourly


# ── Coordinator logic (z coordinator.py) ──

def build_day_data(hourly: dict[int, float], target_date: str) -> dict | None:
    if not hourly:
        return None
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


def recalculate_current(data: dict, now: datetime) -> dict:
    """Symuluje recalculate_current z coordinator.py."""
    today_str = now.date().isoformat()
    current_hour = now.hour

    today = data.get("today")
    current_price = None
    if today and today.get("date") == today_str:
        hours = today.get("hours", {})
        current_price = hours.get(current_hour)
        if current_price is None:
            current_price = hours.get(str(current_hour))

    updated = dict(data)
    updated["current_price"] = current_price
    updated["current_hour"] = current_hour
    return updated


# ── Sensor value_fn (z sensor.py) ──

def safe_get(data, *keys, default=None):
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def round_delta(value, delta=0.05):
    if value is None or delta <= 0:
        return None
    return round(round(value / delta) * delta, 4)


SENSOR_FNS = {
    "tge_rdn_current_price": lambda d: d.get("current_price"),
    "tge_rdn_min_price_today": lambda d: safe_get(d, "today", "min_price"),
    "tge_rdn_max_price_today": lambda d: safe_get(d, "today", "max_price"),
    "tge_rdn_min_price_tomorrow": lambda d: safe_get(d, "tomorrow", "min_price"),
    "tge_rdn_max_price_tomorrow": lambda d: safe_get(d, "tomorrow", "max_price"),
    "tge_rdn_cena0": lambda d: (
        None if (p := d.get("current_price")) is None
        else (1 if p <= 0 else 0)
    ),
    "tge_rdn_min_price_today_r05": lambda d: round_delta(
        safe_get(d, "today", "min_price"), d.get("delta_min", 0.05)
    ),
    "tge_rdn_max_price_today_r05": lambda d: round_delta(
        safe_get(d, "today", "max_price"), d.get("delta_max", 0.05)
    ),
    "tge_rdn_cena_lt_avg23": lambda d: (
        None if d.get("current_price") is None or not (safe_get(d, "today", "hours") or {})
        else (1 if d["current_price"] <= sum((safe_get(d, "today", "hours") or {}).values()) / len(safe_get(d, "today", "hours") or {}) * d.get("avg_percent", 67) / 100 else 0)
    ),
    "tge_rdn_cena_lt_min05": lambda d: (
        None if d.get("current_price") is None or safe_get(d, "today", "min_price") is None
        else (1 if d["current_price"] < safe_get(d, "today", "min_price") + d.get("delta_min", 0.05) else 0)
    ),
    "tge_rdn_cena_gt_max05": lambda d: (
        None if d.get("current_price") is None or safe_get(d, "today", "max_price") is None
        else (1 if d["current_price"] > safe_get(d, "today", "max_price") - d.get("delta_max", 0.05) else 0)
    ),
}


# ── JSON storage roundtrip simulation ──

def json_roundtrip(data: dict) -> dict:
    """Symuluje zapis/odczyt z HA storage (int keys -> string keys)."""
    raw = json.loads(json.dumps(data))
    for key in ("today", "tomorrow"):
        day = raw.get(key)
        if day and "hours" in day:
            day["hours"] = {int(k): v for k, v in day["hours"].items()}
    return raw


# ── Main ──

def main():
    now = datetime.now(zoneinfo.ZoneInfo("Europe/Warsaw"))
    today = now.date()
    tomorrow = today + timedelta(days=1)

    print(f"Data: {today}, godzina: {now.hour}:{now.minute:02d}")

    # Czytaj HTML z plików
    try:
        with open("/tmp/tge_today.html") as f:
            html_today = f.read()
        with open("/tmp/tge_tomorrow.html") as f:
            html_tomorrow = f.read()
    except FileNotFoundError as e:
        print(f"Brak pliku HTML: {e}")
        print("Pobierz najpierw:")
        print(f'  curl -s "https://tge.pl/energia-elektryczna-rdn?dateShow={(today - timedelta(days=1)).strftime("%d-%m-%Y")}" -o /tmp/tge_today.html')
        print(f'  curl -s "https://tge.pl/energia-elektryczna-rdn?dateShow={today.strftime("%d-%m-%Y")}" -o /tmp/tge_tomorrow.html')
        sys.exit(1)

    today_hourly = parse_fixing_prices(html_today, today)
    tomorrow_hourly = parse_fixing_prices(html_tomorrow, tomorrow)

    print(f"Sparsowane godziny — dziś: {len(today_hourly)}, jutro: {len(tomorrow_hourly)}")

    if not today_hourly:
        print("BŁĄD: Brak danych na dziś!")
        sys.exit(1)

    # Wypisz ceny godzinowe
    print("\n── Ceny godzinowe (dziś) ──")
    zero_hours = []
    for h in sorted(today_hourly):
        price = today_hourly[h]
        marker = ""
        if price == 0.0:
            marker += " ← ZERO"
            zero_hours.append(h)
        if h == now.hour:
            marker += " ← TERAZ"
        print(f"  H{h:02d}: {price:.4f} PLN/kWh{marker}")

    if zero_hours:
        print(f"\n  Godziny z ceną 0.0: {zero_hours}")

    # Build day data
    today_data = build_day_data(today_hourly, today.isoformat())
    tomorrow_data = build_day_data(tomorrow_hourly, tomorrow.isoformat())

    # Symuluj _async_update_data result
    current_hour = now.hour
    initial_data = {
        "today": today_data,
        "tomorrow": tomorrow_data,
        "current_price": today_hourly.get(current_hour),
        "current_hour": current_hour,
        "delta_min": 0.05,
        "delta_max": 0.05,
        "avg_percent": 67,
    }

    errors = []

    print(f"\n── Po _async_update_data (godzina {current_hour}) ──")
    print(f"  current_price = {initial_data['current_price']!r}")

    # Test recalculate_current na świeżych danych
    recalc_data = recalculate_current(initial_data, now)
    print(f"\n── Po recalculate_current (świeże dane) ──")
    print(f"  current_price = {recalc_data['current_price']!r}")
    if recalc_data["current_price"] is None:
        errors.append("recalculate_current (fresh) -> None")

    # Test po JSON roundtrip (symulacja persistent storage)
    stored = json_roundtrip(initial_data)
    recalc_stored = recalculate_current(stored, now)
    print(f"\n── Po recalculate_current (po JSON roundtrip) ──")
    print(f"  current_price = {recalc_stored['current_price']!r}")
    if recalc_stored["current_price"] is None:
        errors.append("recalculate_current (stored) -> None")

    # Test wszystkich sensorów
    for label, data in [("świeże dane", recalc_data), ("po JSON roundtrip", recalc_stored)]:
        print(f"\n── Wartości sensorów ({label}) ──")
        for name, fn in SENSOR_FNS.items():
            try:
                value = fn(data)
            except Exception as e:
                value = f"EXCEPTION: {e}"
                errors.append(f"{name} ({label})")
                print(f"  {name:40s} = {value}  [ERROR]")
                continue
            is_tomorrow = "tomorrow" in name
            if value is None and not is_tomorrow:
                status = "NONE!"
                errors.append(f"{name} ({label})")
            else:
                status = "OK" if value is not None else "OK (brak danych jutro)"
            print(f"  {name:40s} = {str(value):>12s}  [{status}]")

    # Test dla KAŻDEJ godziny (sprawdź czy recalculate działa poprawnie)
    print(f"\n── Test recalculate_current dla wszystkich 24 godzin ──")
    for h in range(24):
        if h not in today_hourly:
            continue
        fake_now = now.replace(hour=h, minute=30)
        test_fresh = recalculate_current(initial_data, fake_now)
        test_stored = recalculate_current(stored, fake_now)
        expected = today_hourly[h]
        ok1 = test_fresh["current_price"] == expected
        ok2 = test_stored["current_price"] == expected
        is_zero = expected == 0.0
        marker = " (cena 0.0)" if is_zero else ""
        status = "OK" if (ok1 and ok2) else "FAIL"
        if not ok1 or not ok2:
            print(f"  H{h:02d}: oczekiwane={expected!r}, fresh={test_fresh['current_price']!r}, stored={test_stored['current_price']!r}  [{status}]{marker}")
            errors.append(f"hour_{h}")
        else:
            print(f"  H{h:02d}: {expected:.4f}  [{status}]{marker}")

    # Test edge case: godziny z ceną 0.0 -> sensor cena0 powinien być 1
    if zero_hours:
        print(f"\n── Test sensor cena0 dla godzin z ceną 0.0 ──")
        for h in zero_hours:
            fake_now = now.replace(hour=h, minute=30)
            test_data = recalculate_current(initial_data, fake_now)
            cena0 = SENSOR_FNS["tge_rdn_cena0"](test_data)
            ok = cena0 == 1
            print(f"  H{h:02d}: cena0={cena0!r} (oczekiwane: 1) {'OK' if ok else 'FAIL'}")
            if not ok:
                errors.append(f"cena0_hour_{h}")

    # Podsumowanie
    print(f"\n{'='*60}")
    if errors:
        print(f"FAIL — problemy ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("ALL OK — wszystkie sensory zwracają poprawne wartości")


if __name__ == "__main__":
    main()
