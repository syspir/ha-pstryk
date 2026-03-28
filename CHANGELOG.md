# Changelog

## [0.6.2] - 2026-03-29

### Dodane
- Sekcja "Licznik BleBox" w panelu — wyświetlanie danych z lokalnego licznika BleBox (moc, napięcie, prąd, częstotliwość, energia, tg φ) z automatycznym odświeżaniem co 5 sekund

## [0.6.1] - 2026-03-29

### Naprawione
- Błąd 500 w options flow — usunięto ręczne ustawianie config_entry w konstruktorze PstrykOptionsFlow (niezgodne z nowym HA, gdzie OptionsFlow dostarcza config_entry automatycznie)

## [0.6.0] - 2026-03-29

### Dodane
- Obsługa lokalnego licznika BleBox — odczyt danych co 5 sekund przez API lokalne (http://IP/state)
- Sensory BleBox: moc czynna (suma + L1/L2/L3), napięcie (L1/L2/L3), prąd (L1/L2/L3), częstotliwość sieci, energia pobrana/oddana z rejestrów licznika
- Sensory tg φ QI i QIV w 4 okresach: chwilowe (z mocy), miesięczne, roczne i całościowe (z rejestrów energii)
- Konfiguracja adresu IP licznika BleBox w config flow i options flow z walidacją połączenia
- Osobne urządzenie "Pstryk Meter" (manufacturer: BleBox) powiązane z głównym urządzeniem Pstryk Energy
- Trwała pamięć danych sensorów — po restarcie HA sensory mają od razu ostatnie znane wartości (Store dla metrics, pricing i tg φ BleBox)

### Zmienione
- Koordynatory metrics i pricing zapisują dane do .storage/ po każdym udanym pobraniu z API
- Koordynator BleBox zapisuje snapshoty rejestrów energii dla tg φ przy zmianie miesiąca/roku
- Graceful degradation — jeśli licznik BleBox jest niedostępny, integracja działa dalej z API chmurowym

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
