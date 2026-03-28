# Pstryk Energy - Home Assistant Integration

[![Twoje-Miasto](https://im.twoje-miasto.pl/theme/1/images/logo.png)](https://www.twoje-miasto.pl)

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/twojemiasto/ha-pstryk.svg)](https://github.com/twojemiasto/ha-pstryk/releases)
[![GitHub Downloads](https://img.shields.io/github/downloads/twojemiasto/ha-pstryk/total.svg)](https://github.com/twojemiasto/ha-pstryk/releases)
[![GitHub Stars](https://img.shields.io/github/stars/twojemiasto/ha-pstryk.svg?style=social)](https://github.com/twojemiasto/ha-pstryk)

Integracja Home Assistant dla [Pstryk](https://pstryk.pl) - polskiej platformy zarządzania energią elektryczną z inteligentnym licznikiem. Wykorzystuje nowe Unified Metrics API.

## Funkcje

### Zużycie energii
- Energia pobrana/oddana (godzinowo, dziennie, miesięcznie)
- Bilans energetyczny
- Dane z bieżącej godziny (live)

### Koszty
- Koszt energii (dziś/miesiąc)
- Szczegółowy podział: koszt energii, dystrybucja, VAT, akcyza
- Wartość sprzedanej energii (prosument)

### Ślad węglowy (CO2)
- Emisja CO2 (godzinowo, dziennie, miesięcznie)
- Wartości w gCO2eq

### Ceny TGE (giełda energii)
- Aktualna cena energii (netto/brutto)
- Średnia cena
- Informacja: tania/droga energia teraz
- Najtańsza i najdroższa nadchodząca cena
- Pełna cena z komponentami (dystrybucja, akcyza, VAT)

### Prosument
- Cena prosumencka (netto/brutto)
- Średnia cena prosumencka

## Instalacja przez HACS

1. Otwórz HACS w Home Assistant
2. Kliknij **⋮** (trzy kropki) → **Custom repositories**
3. Dodaj URL: `https://github.com/twojemiasto/ha-pstryk`
4. Kategoria: **Integration**
5. Kliknij **Add** → znajdź "Pstryk Energy" → **Install**
6. Zrestartuj Home Assistant
7. Przejdź do **Ustawienia** → **Urządzenia i usługi** → **Dodaj integrację** → szukaj "Pstryk"

## Konfiguracja

Podczas konfiguracji podaj:

- **Token API** - token z panelu [app.pstryk.pl](https://app.pstryk.pl) (format: `sk-...`)
- **Prosument** - zaznacz jeśli masz fotowoltaikę
- **Strefa czasowa** - domyślnie `Europe/Warsaw`
- **Interwał odświeżania** - domyślnie 15 minut (zakres: 5-120 min)

## Sensory

| Sensor | Jednostka | Opis |
|--------|-----------|------|
| `sensor.pstryk_energy_import_today` | kWh | Energia pobrana dziś |
| `sensor.pstryk_energy_export_today` | kWh | Energia oddana dziś |
| `sensor.pstryk_energy_balance_today` | kWh | Bilans energii dziś |
| `sensor.pstryk_energy_import_month` | kWh | Energia pobrana w miesiącu |
| `sensor.pstryk_energy_export_month` | kWh | Energia oddana w miesiącu |
| `sensor.pstryk_total_cost_today` | PLN | Koszt energii dziś |
| `sensor.pstryk_total_cost_month` | PLN | Koszt energii w miesiącu |
| `sensor.pstryk_carbon_footprint_today` | gCO2eq | Ślad węglowy dziś |
| `sensor.pstryk_current_price_gross` | PLN/kWh | Aktualna cena brutto |
| `sensor.pstryk_is_cheap_now` | bool | Czy teraz tania energia |
| `sensor.pstryk_cheapest_upcoming_price` | PLN/kWh | Najtańsza nadchodząca cena |
| `sensor.pstryk_prosumer_price_gross` | PLN/kWh | Cena prosumencka brutto |

## Automatyzacje

### Przykład: powiadomienie o taniej energii
```yaml
automation:
  - alias: "Tania energia - włącz ładowanie"
    trigger:
      - platform: state
        entity_id: sensor.pstryk_energy_is_cheap_now
        to: "True"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.ev_charger
```

### Przykład: dashboard z kosztami
```yaml
type: entities
title: Pstryk Energy
entities:
  - entity: sensor.pstryk_energy_current_price_gross
  - entity: sensor.pstryk_energy_total_cost_today
  - entity: sensor.pstryk_energy_energy_import_today
  - entity: sensor.pstryk_energy_carbon_footprint_today
```

## Wymagania

- Home Assistant 2024.1.0+
- Konto Pstryk z tokenem API
- Inteligentny licznik podłączony do Pstryk

## Wyłączenie odpowiedzialności

Niniejsze oprogramowanie jest udostępniane w stanie „takim, jakie jest" (_AS IS_), bez jakiejkolwiek gwarancji, wyraźnej ani dorozumianej. Twoje-Miasto Sp. z o.o. nie ponosi odpowiedzialności za jakiekolwiek szkody bezpośrednie, pośrednie, przypadkowe, szczególne ani wynikowe powstałe w związku z korzystaniem z tego oprogramowania. Użytkownik korzysta z integracji na własne ryzyko.

## Licencja

MIT — Copyright (c) 2026 Twoje-Miasto Sp. z o.o.
