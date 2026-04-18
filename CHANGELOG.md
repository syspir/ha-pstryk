# Changelog

## [0.9.13] - 2026-04-19

### Dodane
- Nowy osobny sensor `tge_rdn_cena_lt_always_buy` („Cena RDN — zawsze kupuj") — `1` gdy aktualna cena jest poniżej progu „Cena zawsze kupuj TGE"

### Zmienione
- Sensor `tge_rdn_cena_lt_min05` wrócił do oryginalnej logiki (tylko `cena ≤ Min+delta`) — próg „zawsze kupuj" wydzielony do osobnego sensora
- Kolorowanie wykresu TGE RDN: zielony zależy tylko od `Min+delta`, czerwony nadal respektuje próg „Minimalna cena sprzedaży"

## [0.9.12] - 2026-04-19

### Zmienione
- Kolorowanie wykresu TGE RDN w panelu uwzględnia progi „Minimalna cena sprzedaży" i „Cena zawsze kupuj" — słupki nie są czerwone, gdy cena jest poniżej progu sprzedaży, i zawsze zielone, gdy cena jest poniżej progu zakupu

## [0.9.11] - 2026-04-19

### Dodane
- Konfigurowalny próg „Minimalna cena sprzedaży TGE" (domyślnie 1.00 PLN/kWh) — sensor `tge_rdn_cena_gt_max05` nie wskazuje sprzedaży, gdy cena jest poniżej tego progu
- Konfigurowalny próg „Cena zawsze kupuj TGE" (domyślnie 0.23 PLN/kWh) — sensor `tge_rdn_cena_lt_min05` zawsze wskazuje zakup, gdy cena jest poniżej tego progu

## [0.9.10] - 2026-04-15

### Zmienione
- Rozdzielenie wykresu cen RDN na dwa osobne boksy: „Prognoza dziś" i „Prognoza jutro" (wyświetlany tylko gdy dane dostępne)

## [0.9.9] - 2026-04-15

### Usunięte
- Sekcja „Dane na żywo" (bieżąca godzina — cena zakupu brutto z rozbiciem na komponenty) z panelu

## [0.9.8] - 2026-04-15

### Usunięte
- Sekcja „Prognoza cen" (wykres słupkowy cen godzinowych zakupu brutto) z panelu
- Sekcja „Nadchodzące ceny" (najtańsza/najdroższa godzina) z panelu

## [0.9.7] - 2026-04-12

### Usunięte
- Wiersze „Min dziś" i „Max dziś" z zaokrągleniem do delty z karty Wskaźniki TGE w panelu — redundantne z kolorowaniem wykresu

## [0.9.6] - 2026-04-12

### Dodane
- Kolorowanie słupków na wykresie TGE RDN według progów — zielone gdy cena < Min + delta, czerwone gdy cena > Max − delta

## [0.9.5] - 2026-04-12

### Dodane
- Encje number do konfiguracji progów TGE (Delta ceny min, Delta ceny max, Próg średniej) — edytowalne bezpośrednio w HA, zmiana działa natychmiast bez reloadu integracji
- Platforma `number` w integracji

### Usunięte
- Pola progów TGE z opcji integracji (config flow) — przeniesione na encje number

## [0.9.4] - 2026-04-12

### Naprawione
- Błąd przy zapisie opcji progów TGE — zamieniono vol.Coerce(int) na NumberSelector z dedykowanym polem liczbowym i jednostkami (gr, %), dodano zabezpieczenie przed nieprawidłowym typem wartości przy odczycie opcji

## [0.9.3] - 2026-04-12

### Naprawione
- Opcje progów TGE nie były zapisywane po zatwierdzeniu — pola zmienione z vol.Optional na vol.Required, dodane wartości domyślne TGE do początkowej konfiguracji

## [0.9.2] - 2026-04-12

### Naprawione
- Etykiety wskaźników TGE w panelu — Min dziś pokazuje „+X gr", Max dziś pokazuje „−X gr" zamiast wspólnego „±" dla obu

## [0.9.1] - 2026-04-12

### Naprawione
- Zmiana progów TGE w opcjach nie była widoczna w panelu do następnego fetcha — wartości delta/avg_percent były zapisywane do persistent storage i po przeładowaniu integracji wczytywane stamtąd zamiast z aktualnej konfiguracji

## [0.9.0] - 2026-04-12

### Dodane
- Konfigurowalne progi wskaźników TGE w opcjach integracji: delta ceny min (grosze), delta ceny max (grosze), próg procentowy średniej dnia
- Panel wyświetla dynamicznie skonfigurowane wartości progów zamiast hardkodowanych

### Zmienione
- Sensory wskaźnikowe TGE (Min±delta, Max±delta, Cena < Min+delta, Cena > Max-delta, Cena ≤ X% średniej) używają wartości z konfiguracji zamiast stałych 0,05 PLN i 2/3
- Koordynator TGE przekazuje parametry konfiguracji w danych do sensorów i panelu

## [0.8.9] - 2026-04-12

### Naprawione
- Wskaźniki TGE w panelu (Min/Max ±0,05, Cena < Min+0,05, Cena > Max−0,05) wyświetlały "---" — przyczyną były błędne hardkodowane entity_id (slugifikacja polskich nazw z przecinkami dawała inne identyfikatory niż zakładane). Wskaźniki są teraz obliczane bezpośrednio w JavaScript z danych działających sensorów

### Usunięte
- Tłumaczenie angielskie (translations/en.json) — integracja obsługuje tylko język polski

## [0.8.8] - 2026-04-12

### Naprawione
- Pobieranie danych z tge.pl — strona TGE blokuje domyślny User-Agent aiohttp, zmieniony na neutralny nagłówek

## [0.8.7] - 2026-04-12

### Naprawione
- Automatyczne odrzucanie nieaktualnego cache TGE RDN przy starcie HA — stare dane z innego dnia nie są już ładowane z persistent storage, koordynator czeka na świeży fetch

## [0.8.6] - 2026-04-12

### Naprawione
- Obsługa timeout przy pobieraniu danych z TGE — `asyncio.TimeoutError` nie był łapany, co powodowało utratę fallbacku na ostatnie znane dane
- Ochrona przed nadpisaniem dobrych danych pustymi — gdy parser TGE zwróci pusty wynik (zmiana HTML, błąd sieci), koordynator zachowuje ostatnie znane dane zamiast je kasować

## [0.8.5] - 2026-04-12

### Naprawione
- Sensory TGE RDN zależne od bieżącej ceny (cena bieżąca, cena0, ≤2/3 średniej, <Min+0,05, >Max-0,05) pokazywały „nieznany" gdy cena godziny wynosiła 0,00 PLN/kWh — operator `or` traktował zero jako brak wartości
- Logika odświeżania danych TGE RDN — wykrywanie nieaktualnych danych dzisiejszych i jutrzejszych z weryfikacją daty

## [0.8.4] - 2026-04-11

### Naprawione
- Retry pobierania danych RDN na jutro — zamiast jednorazowej próby po 13:00, ponawiane co 15 minut aż dane się pojawią (TGE publikuje fixing ok. 13:30)

## [0.8.3] - 2026-04-11

### Zmienione
- Ceny TGE RDN zaokrąglane w dół (floor) zamiast standardowego zaokrąglenia, ujemne ceny ustawiane na 0,00
- Osobny wykres słupkowy cen godzinowych RDN na jutro (widoczny gdy dane dostępne)

### Naprawione
- Brakujące tłumaczenia 6 nowych sensorów TGE RDN (min/max ±0,05, cena0, avg 2/3, wskaźniki progowe) w pl.json i en.json — sensory mogły nie wyświetlać danych w panelu

## [0.8.2] - 2026-04-11

### Zmienione
- Ceny TGE RDN przeliczane na brutto (×1,23 VAT) — wartości zgodne z pstryk.pl/ceny kolumna brutto
- Format walutowy z 2 miejscami po przecinku (0,10 zamiast 0,1)

## [0.8.1] - 2026-04-11

### Naprawione
- Sensory TGE RDN „nieznany" — JSON storage konwertuje klucze int na stringi, co powodowało brak dopasowania bieżącej godziny; naprawione normalizowanie kluczy hours przy wczytywaniu z storage i w recalculate_current

## [0.8.0] - 2026-04-11

### Zmienione
- Panel: etykiety sekcji TGE zaktualizowane — „Ceny RDN Fixing I (TGE — netto)", „Aktualna cena RDN (netto)"

## [0.7.9] - 2026-04-11

### Zmienione
- Źródło cen RDN zmienione z PSE RCE (rynek bilansujący) na TGE RDN Fixing I (aukcja dnia następnego) — ceny teraz zgodne z pstryk.pl/ceny
- Atrybucja zmieniona z PSE S.A. na TGE S.A.

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
