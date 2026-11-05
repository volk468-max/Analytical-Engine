# Проверка реализации

Реализован standard-library offline validator, не Windows extractor. Формат и обязательные поля описаны в data-contract.md. Реальные Norgate bundles не загружались. Fixtures имеют data_kind=synthetic, ID namespace SYNTH и вымышленные цены.

Запуск: `python -m unittest discover -s research/breadth_pit_qualification -v`.
CLI: `python research/breadth_pit_qualification/validator.py <private-bundle.json> --policy <policy.json> --private-report <private-report.json>`.
CLI по умолчанию печатает только статус, не IDs/цены; file report содержит restricted metrics и требует того же private storage/expiry. Код не удаляет files и не пишет в production. Не указывать public Git checkout как private-report path.

Настройки overall/departed coverage, index count ranges, required action sample types и MA windows configurable. Количественные пороги не отключают жёсткие identity/timing/licence/reference gates. Отсутствие departed/action samples блокирует strict acceptance; для engineering можно изменить sampling policy, но это не заполняет NOT_EVALUATED evidence.

Проверяются finite/valid OHLCV, duplicate keys, clock timezone/order, future price/membership/action availability, source refs/hash syntax и payload integrity, active security/ticker intervals и reuse, полнота reference index/calendar, missing constituents/prices, departed subgroup и MA gap/warmup. Schema/malformed input fail-closed. Границы: не проверяется подлинность external review/хешируемого исходного документа, полнота universe при ложном reference, истинность лицензии, полная adjustment reconciliation и содержимое оригинальных historical archives. Эти поля требуют независимого evidence и human attestation.

Ни один результат функции не выставляет real_data_qualified=true. Чистый synthetic bundle → SYNTHETIC_TEST_ONLY; реальные rows без блокеров → REQUIRES_HUMAN_ATTESTATION, не GO. PASS структурных проверок не равен покупке, безусловной PIT-корректности или готовности к стратегии.

Результаты test runs, hashes и точная граница проверки — verification.json. Прежние карточки/результаты базы знаний сохранены; источник PR15 добавлен с pinned head и отчётом, текущий проект каталогизирован как работа этого PR без self-referential SHA (он определяется Git history).
