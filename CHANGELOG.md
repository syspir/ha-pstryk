# Changelog

## [0.5.3] - 2026-03-29

### Zmienione
- Uproszczenie sensorów cenowych — zostały tylko 2: cena zakupu brutto (full_price z dystrybucją, VAT, akcyzą) i cena sprzedaży brutto (prosument)
- Panel Live — duża cena zakupu z rozbiciem na składowe (TGE, dystrybucja, serwisowa, akcyza, VAT) z ikonkami
- Wykres godzinowych cen (dziś + jutro) w panelu z kolorowaniem tania/droga/normalna i oznaczeniem bieżącej godziny
- Rozszerzenie okna API cenowego na dziś + jutro (do +48h)
- Koordynator cenowy odświeża bieżącą godzinę co 1 minutę bez zapytania API
- Minimalny interwał odpytywania API zmieniony z 15 na 30 minut
- Ikonki przy wszystkich metrykach w panelu

### Usunięte
- Sensory: aktualna cena brutto/netto, średnia brutto/netto, tania/droga teraz, najtańsza/najdroższa nadchodząca, cena TGE z metryki, cena prosumencka netto, średnia prosumencka
- Dane przeniesione do atrybutów sensora zakupu i wyświetlane w panelu

## [0.5.2] - 2026-03-28

### Dodane
- Pierwsza publiczna wersja integracji Pstryk Energy dla Home Assistant
- Sensory zużycia energii (godzinowo, dziennie, miesięcznie)
- Sensory kosztów z podziałem na składniki
- Sensory cen TGE (aktualna, średnia, najtańsza/najdroższa nadchodząca)
- Sensory prosumenckie (warunkowo)
- Panel frontendowy w sidebarze Home Assistant z podglądem wszystkich danych
- Config flow z walidacją tokenu API
- Options flow (prosument, interwał odświeżania, panel)
