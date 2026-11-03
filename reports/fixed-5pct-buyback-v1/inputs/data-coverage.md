# Полнота данных

|Ряд|Поставщик|Наблюдений в44 сессиях|Последняя дата|Пропуски|
|---|---|---|---|---|
|AMD|Yahoo chart|44|2026-11-02|нет|
|NVDA|Yahoo chart|44|2026-11-02|нет|
|MU|Yahoo chart|44|2026-11-02|нет|
|TSM|Yahoo chart|44|2026-11-02|нет|
|AVGO|Yahoo chart|44|2026-11-02|нет|
|AMAT|Yahoo chart|44|2026-11-02|нет|
|AMZN|Yahoo chart|44|2026-11-02|нет|
|META|Yahoo chart|44|2026-11-02|нет|
|PLTR|Yahoo chart|44|2026-11-02|нет|
|LRCX|Yahoo chart|44|2026-11-02|нет|
|NBIS|Yahoo chart|44|2026-11-02|нет|
|^GSPC|Yahoo chart|44|2026-11-02|нет|
|^IXIC|Yahoo chart|44|2026-11-02|нет|
|^NDX|Yahoo chart|44|2026-11-02|нет|
|^RUT|Yahoo chart|44|2026-11-02|нет|
|^SOX|Yahoo chart|44|2026-11-02|нет|
|^VIX|Yahoo chart|44|2026-11-02|нет|
|DX-Y.NYB|Yahoo chart|44|2026-11-02|нет|
|QQQ|Yahoo chart|44|2026-11-02|нет|
|SPY|Yahoo chart|44|2026-11-02|нет|
|IWM|Yahoo chart|44|2026-11-02|нет|
|SMH|Yahoo chart|44|2026-11-02|нет|
|SOXX|Yahoo chart|44|2026-11-02|нет|
|DGS2|FRED retrospective daily series|42|2026-10-30|2026-10-12;2026-11-02|
|DGS10|FRED retrospective daily series|42|2026-10-30|2026-10-12;2026-11-02|
|BAMLC0A0CM|FRED retrospective daily series|43|2026-10-30|2026-11-02|
|BAMLH0A0HYM2|FRED retrospective daily series|43|2026-10-30|2026-11-02|

Файлы data/manifest.json содержат URL, retrieval timestampsUTC, SHA256 raw responses, источник, OHLCV, corporate actions и корректировки; inputs.json — фактически применённый набор. Yahoo запрос includePrePost=false, interval1d. Акции/ETF используют regular-session OHLC, индексы и валютный DXY отмечены своими рядами, а не equity quotes. Для DXY17:00NY и VIX16:15NY close — допущение описания дневного ряда, не доказанная лента публикаций. Adjclose не смешивается с OHLC. В окне нет splits; дивиденды сверены с events. NBIS не склеивается с YNDX/приостановленным периодом. Proxy fixed7semis — survivorship sample, не вся ширина.

Все11 акций, QQQ/SPY/IWM, S&P500/NasdaqComposite/Russell2000, SOX/SOXX/SMH, VIX/DXY покрывают44 торговых дня. Индексы и ETF сохранены отдельно, замены индексов ETF нет. 2Y/10Y имеют42 наблюдения:12 октября закрытие Treasury market,2 ноября ещё нет в ответе; IG/HY43,нет2 ноября. Даты не заполняются искусственно. As-of values могут переноситься после lag2sessions с сохранением даты наблюдения; это не котировка за новую дату. Новые values после cutoff не используются. Отсутствие оригинальных релизов/ALFRED vintages не позволяет назвать эту доступность подтверждённой.

Дата индекса в payload может быть временем начала торговли, а не публикацией OHLC; timestamps расчёта задаются явно в prepare/run, источник не считается исходным архивом публикаций. Перед DST regular close20UTC,2 ноября21UTC; open13:30/14:30. session-calendar.csv — exchange_calendars4.13.2 XNYS,44sessions, без7сентября. На3 ноября используется только известный календарь, не будущая цена.

10,556 OHLC comparisons нового Yahoo пакета с исходным audit inputs совпадают; prefix не переписан, только append после22 октября. VIX старого CBOE-пакета сохранён; continuation Yahoo, в audit window расхождения несущественны, вне окна Feb6 различается и не переопределяется. DGS10 prefix также не пересматривается. Точная повторяемость ценовых признаков и daily NAV до22 октября проверена.

ФРС: прямыеHTTP-запросы вернули403 (data/fed-events.json); web connector прочитал официальные страницы16сентября/28октября. Сохранены URL, время чтения, заявленное release time и структурированные факты в data/fed-verified-events.json, без имитации rawHTML. Ссылка календаря: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm . Expectations/futures, транскрипты/полный news feed не получены.

Недоступны original production payloads, orders/positions, исторические точные конфигурации на каждый день, настоящая market-wide breadth/constituents, исходные макровинтажи, полная history EPS/guidance. Текущие значения не подменяют исторические фундаментальные snapshots.
