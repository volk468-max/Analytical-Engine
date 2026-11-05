# Валидация и воспроизведение

Граница исследования: main a14ebf9c268bea5cb01de962edfb98b8df94652a; данные PR11 5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7; контекст PR13 371d7a1135e35f96b5f7583bddc6de1ea007bf82. Knowledge PR14 f9288b42e0d58f521b57c420d79477d5aeb10459 остаётся Draft/unmerged. Remote/runtime version не выводится из main SHA.

Исходные public GitHub файлы загружены по pinned URLs. Source-manifest.json фиксирует 20 входов с Git blob SHA/SHA256/bytes; raw inputs остаются вне PR. Полные файлы, а не excerpts, использованы в расчётах. 4235 reference sessions заморожены с calendar hash. Исходные updater scripts не выполнялись, Wikipedia revision scraping не запускался.

Запуск: python research/free_historical_index_data/audit.py --cache /tmp/free-index-inputs
Полный download/replay: добавить --fetch (только public pinned GitHub). Offline dependencies: stdlib. Новых provider API ключей/аккаунтов/подписок не создаётся. Исходный Stooq probe сохранён с HTTP404; нет retries, обхода challenge или подмены его результата успехом.

10 автоматических тестов: future/effective snapshot boundaries, source duplicates, lawcal created/effective/removal semantics, missing/future MA warmup, malformed OHLCV, complete daily rows/quality flags, annual bounds и разделение issuer/share classes. Primary checks воспроизводятся inspect_primary.py. Outputs повторно сгенерированы в отдельную папку и сравниваются byte-for-byte; финальные результаты этой проверки см. verification.json. Исходные торговые backtests не запускались.

Ограничения: не получены OHLCV всех исторических бумаг; live-provider проверки всех symbols не выполнялись. Нет независимо подтверждённого полного effective membership denominator, security master, оригинальных PIT publication vintages или разрешённого free delisted price archive. Поэтому missing/ambiguous и confirmed=0 — качество доказательств, не оценка количества реально существовавших акций. Нет полного corporate-action validation отсутствующих данных. XNYS reference calendar не аттестует индивидуальные Nasdaq halts.

Для таблиц .gz.b64 сначала base64 decode, затем gzip decompress. CSV encoding UTF-8; даты ISO, интервалы разногласий включительны по first/last trading session, lawcal removal exclusive. Counts относятся к securities/ticker candidates, не безусловно уникальным компаниям. В 2026 YTD tail stale отмечен отдельно; будущие сессии не добавлены.
