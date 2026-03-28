# Changelog

## [0.4.7] - 2026-03-28

### Zmienione
- Producent urządzenia zmieniony na Twoje-Miasto Sp. z o.o.
- Link "Odwiedź" kieruje na twoje-miasto.pl

## [0.4.6] - 2026-03-28

### Dodane
- Logo Twoje-Miasto z linkiem w stopce panelu frontendowego

## [0.4.5] - 2026-03-28

### Naprawione
- Panel frontendowy — fallback dla `css` tagged template w nowszych wersjach HA (TypeError: css is not a function)

## [0.4.4] - 2026-03-28

### Naprawione
- Kompatybilność z nowszymi wersjami HA — bezpośredni import funkcji panelu zamiast usuniętego `hass.components`

## [0.4.3] - 2026-03-28

### Naprawione
- Panel w sidebarze rejestruje się natychmiast po instalacji, niezależnie od dostępności API

## [0.4.2] - 2026-03-28

### Naprawione
- Ograniczenie ponownych prób konfiguracji do minimum raz na 15 minut (zapobiega zalewaniu API przy błędach)

## [0.4.1] - 2026-03-28

### Zmienione
- Usunięto retry przy błędzie 429 (rate limit) — czekanie do następnego cyklu odświeżania zamiast dodatkowych zapytań
- Usunięto odniesienia do CO2 z dokumentacji

## [0.4.0] - 2026-03-28

### Zmienione
- Redukcja zapytań API z 3 do 2 na cykl odświeżania (dane dzienne z summary hourly)
- Minimalny interwał odświeżania zmieniony z 5 na 15 minut

### Naprawione
- Obsługa rate limitingu API (429) z automatycznym retry
- Rejestracja ścieżki statycznej panelu (kompatybilność z nowszymi HA)
- Sensory kosztowe: state_class TOTAL zamiast TOTAL_INCREASING (wymagane dla MONETARY)

### Usunięte
- Sensory śladu węglowego (CO2) — redukcja obciążenia API

## [0.3.1] - 2026-03-28

### Naprawione
- Rejestracja ścieżki statycznej panelu — użycie async_register_static_paths z StaticPathConfig (kompatybilność z nowszymi wersjami HA)
- Sensory kosztowe — state_class zmieniony z TOTAL_INCREASING/MEASUREMENT na TOTAL (wymagane dla device_class MONETARY)

## [0.3.0] - 2026-03-28

### Dodane
- Opcja włączenia/wyłączenia panelu w menu bocznym (domyślnie włączony)
- Konfiguracja panelu dostępna podczas instalacji oraz w opcjach integracji

## [0.2.0] - 2026-03-28

### Dodane
- Panel frontendowy w sidebarze Home Assistant z podglądem wszystkich danych
- Sekcje panelu: bieżąca godzina (live), energia, koszty, ceny TGE, prosument
- Responsywny układ (desktop/mobile)
- Badge statusu ceny (tania/droga/normalna)
- Nadchodzące ceny z przedziałami godzinowymi

## [0.1.0] - 2026-03-28

### Dodane
- Pierwsza wersja integracji Pstryk Energy dla Home Assistant
- Sensory zużycia energii (godzinowo, dziennie, miesięcznie)
- Sensory kosztów z podziałem na składniki
- Sensory cen TGE (aktualna, średnia, najtańsza/najdroższa nadchodząca)
- Sensory prosumenckie (warunkowo)
- Config flow z walidacją tokenu API
- Options flow (prosument, interwał odświeżania)
