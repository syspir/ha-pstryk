# Changelog

## [0.7.8] - 2026-04-11

### Naprawione
- Prognoza RDN na kolejny dzień mogła nie pojawiać się w panelu — koordynator TGE wymusza odświeżenie z PSE po 13:00 gdy brak danych jutrzejszych

## [0.7.7] - 2026-04-11

### Naprawione
- Cena bieżąca TGE mogła pokazywać wartość z poprzedniego dnia — `recalculate_current` sprawdza teraz datę danych przed użyciem
- Cena bieżąca Pricing — usunięty ślepy fallback `all_frames[-1]`, `_find_current_frame` zwraca najbliższą przeszłą ramkę zamiast `None`

## [0.7.6] - 2026-04-11

### Dodane
- Wskaźniki TGE: cena ≤ 0, min/max dziś (±0,05), cena ≤ 2/3 średniej, cena < min+0,05, cena > max-0,05
- Karta „Wskaźniki TGE" w panelu z badge'ami Tak/Nie i progami
- Osobne urządzenie „TGE RDN" (PSE S.A.) dla sensorów giełdowych

## [0.7.1] - 2026-04-09

### Zmienione
- Niezależny start źródeł danych — błąd API Pstryk nie blokuje TGE RDN i odwrotnie, integracja zawsze wystartuje
- Możliwość zmiany tokenu API w opcjach integracji (bez konieczności usuwania i ponownej konfiguracji)

### Usunięte
- Throttle `ConfigEntryNotReady` przy starcie — niepotrzebny gdy źródła są niezależne

## [0.7.0] - 2026-04-09

### Dodane
- Ceny RDN z Towarowej Giełdy Energii — pobieranie godzinowych cen sprzedaży energii z API PSE (api.raporty.pse.pl)
- Nowy koordynator TGE z odświeżaniem co 60 min i minutowym przeliczaniem aktualnej godziny
- 5 nowych sensorów: cena RDN bieżąca godzina, najniższa/najwyższa dziś, najniższa/najwyższa jutro
- Atrybuty sensorów z prognozą godzinową na dziś i jutro
- Sekcja „Ceny RDN (TGE — sprzedaż)" w panelu z wykresem słupkowym cen godzinowych
- Karty aktualnej ceny RDN, min/max dziś i jutro (warunkowa — po publikacji danych ~13:00)
- Persistent storage dla danych TGE — sensory dostępne od razu po restarcie

## [0.6.9] - 2026-03-29

### Naprawione
- Wysokość słupków wykresu prognozy cen — kolumny nie rozciągały się na pełną wysokość kontenera, procentowa wysokość słupków nie miała referencji

## [0.6.8] - 2026-03-29

### Zmienione
- Wykres prognozy cen przepisany z SVG na czysty HTML/CSS (flexbox) — eliminuje problem z namespace SVG w Shadow DOM Lit/HA

## [0.6.7] - 2026-03-29

### Naprawione
- Wykres prognozy cen nie renderował słupków — dynamiczne elementy SVG (rect, line, text) tworzone przez Lit `html` tag miały namespace HTML zamiast SVG, użyto `svg` tagged template
- Dodano fallback kolory dla zmiennych CSS w SVG (--divider-color, --secondary-text-color)

## [0.6.6] - 2026-03-29

### Naprawione
- Wykres prognozy cen — filtrowanie ramek z ceną 0 (dane TGE jeszcze niedostępne), eliminuje zniekształcenie skali i puste słupki
- Atrybut price_forecast pomija ramki bez danych cenowych, zmniejszając rozmiar atrybutu

## [0.6.5] - 2026-03-29

### Naprawione
- Sekcja "Prognoza cen" w panelu — zamiast znikać przy braku danych, wyświetla komunikat "Brak danych o prognozach cen"

## [0.6.4] - 2026-03-29

### Dodane
- Przywrócenie sensorów cenowych jako osobne encje: aktualna cena brutto/netto, średnia brutto/netto, tania/droga energia teraz, najtańsza/najdroższa nadchodząca cena, cena TGE z metryki
- Przywrócenie sensorów prosumenckich: cena netto, średnia cena brutto

## [0.6.3] - 2026-03-29

### Naprawione
- Błąd thread safety — recalculate_current() wywoływany z wątku spoza event loop (RuntimeError w nowszym HA), zamieniono sync lambda na async callback

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
