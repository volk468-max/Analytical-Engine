# Daily Shadow Worker — диагностика и fix, 15.11.2026

**Исправление подготовлено; новая версия НЕ развёрнута. Полная приёмка UNVERIFIED.**
Никаких изменений Railway configuration, production, текущего cron или истории
прогнозов в этой работе. Новая fix-ветка/PR направляются в research branch, не main.

## Что установлено по фактам

Исследован реально deployed/pinned commit
`f066a5ecc4dc8c1984905b748d5781fe7235bb94`. Worker entrypoint/Dockerfile/predeploy
соответствуют research-коду, зависимости и model artifacts не указывают на root
production app. PostgreSQL service live, public TCP proxy отсутствует. Worker config
cron=`0 2 * * 2-6`, latest deployment1b636903-0f6c-4aa2-9fc8-be27f9c632ff SUCCESS.

[Очищенные наблюдения из Railway](railway-evidence.json) сохраняют источник и время.
Существенные данные находились в **attributes**, а не в пустом message:

| Наблюдение UTC | Подтверждённое содержание |
|---|---|
|11.11 15:37|PREFLIGHT: six-symbol schema/actions passed,4primary samples; actual HTTP codes не логировались|
|12.11 02:03:38.700210717|DAILY ERROR SOURCE_STILL_REVISING после двух collect|
|13.11 02:05:47.809539766|ISSUE RECORDED216numeric+6blocked, session12.11|
|13.11 02:05:47.809568540|ACCEPTANCE_SQL216; first2026-11-13T02:05:45.498639+00:00|
|14.11 02:05:33.499912014|ISSUE RECORDED216numeric+6blocked, session13.11|
|14.11 02:05:33.499927399|ACCEPTANCE_SQL432, тот же first timestamp|

Таким образом, отсутствие прогнозов вообще **не следует** из логов. Существуют
прикладные SQL-count observations двух выпусков. Но это **не независимый свежий
read-only SQL**. Не выдаём432 за проверенный сейчас физический count, не выводим
из него распределения/число полных successful runs/отсутствие дубликатов. SUCCESS
самого deployment также не доказывает завершение job: старый код не имел completion.

## Причина и границы достоверности

Подтверждённая причина остановки12.11: `issue_once` сравнил SHA256 **всего набора
сырых ответов**, включая глобальный exchange-symbol-list/US и JSON formatting,
и при первом несовпадении без повторной проверки выбросил SOURCE_STILL_REVISING.
Сравнение включает данные, не используемые шестью моделируемыми инструментами.
Оба не совпавших snapshot сохранялись только **после** успешного сравнения, поэтому
не сохранились для forensic review. Это излишне широкий criterion и отсутствие
recovery/evidence, а не доказанная ошибка EODHD/auth/cron/database.

**Какое поле изменилось в реальном неудачном запуске — UNVERIFIED.** Исходные
снимки не сохранены; нельзя объявить посторонние metadata или действительную quote revision
установленной первопричиной. Mock regression воспроизводит обе ситуации и проверяет
разное поведение. CRASHED — наблюдение владельца; нынешний deployment history
показывает старые entries как REMOVED и не восстанавливает точный прежний status. Старый код также не проверял legal_reason
второго Snapshot отдельно: blocked second snapshot с revision=NULL мог попасть
в ту же ошибку сравнения. По доступным logs это тоже нельзя исключить. Новый
fetch проверяет legal_reason каждого снимка и сохраняет конкретный error code;
нет утверждения, что в неудачном run обязательно было два успешных HTTP набора.

Второй подтверждённый дефект observability: JSON не имел message, run UUID, полного
lifecycle/traceback; Railway UI показывал пустые строки с данными в attributes.
Старый historical-comparison exception превращался в BLOCKED, но общий exit0,
а batch с недостатком ожидаемых чисел мог считаться RECORDED. DB/lock cleanup мог
скрывать первичное исключение. Исправление различает эти результаты.

## Исправление

- `diagnostics.py`: message+structured fields, UUID каждого run, aware UTC, levels,
  start/error/completion, exception type и очищенная chain/stack без locals/source
  lines. URLs/токены/пароли/auth headers скрываются. DB errors содержат SQLSTATE,
  допустимый constant error code, но не query/row/credential payload.
- `HTTPTransport`: timeout<=20s, <=3attempts только transient timeout/connection/
  429/500/502/503/504;401/403не повторяются. Retry-After до30s соблюдается, более
  долгий не обходится ранним retry. Worker общий network budget900s. Логи содержат
  endpoint без query, actual status/attempt/duration, completion summary counts.
  Успешный DNS не является HTTP RESPONSE, HTTP200не является validation всех данных.
- `readiness.py`: canonical validated six-symbol OHLCV/currency/split/dividend inputs
  вместо всей глобальной raw-directory/formatting; unused adjusted_close исключён
  из price-risk fingerprint. Source basis/threshold/model ничего не меняют. Все
  исходные raw snapshots сохраняются отдельно encrypted до сравнения. До3пар с
  gap>=60s, повторно проверяется local session. Значимые изменения продолжают
  блокировать выпуск; raw-only drift даёт отдельный evidence classification.
- SQL005 только расширяет безопасный receipt schema. Уже применённые SQL001–004,
  модели, forecasts/outcomes не изменены. Run UUID, HTTP summary и readiness refs/
  hashes/changed component names сохраняются в receipts; никаких raw цен в audit.
- Transaction-scoped advisory lock + прежняя уникальность/session guard: retries
  читают original batch, не upsert его значений. Atomic HIST/REGIME+baseline прежние.
  222записи/216numeric+6intentionallyblocked A/B/C — полный batch; меньшее число
  не SUCCESS. Idempotent attempt не выдаётся за новый выпуск.
- exit0 complete/expected calendar skip, exit1 hard failure, exit2 partial. Optional
  historical/evaluation failures видны и не дают overall success. DB audit/retention
  failure тоже не скрывается. Source/model/clock errors не подменяются cache/provider.
- `inspect_persistence.py`/acceptance.sql: repeatable-read READ ONLY audit actual
  tables/columns: totals, UTC min/max, per date/ticker, complete issuance groups,
  duplicate logical series, expected grid/missing days, fixture alarms, run IDs.
  Expected sessions начинаются11.11 и включают отсутствующие дни с grace02:30UTC
  next day. Legacy jobs без run IDs не интерпретируются как0successful jobs.

## Расписание и причинность

Cron **не меняется**.02:00UTC Tue–Sat =21:00NY EST/22:00NY EDT в предыдущую local
дату, после20:30gate и regular/early close. Две реальные удачные записи подтверждают
пригодность этого окна по этим дням; один raw mismatch не обосновывает перенос.
Readiness не гарантирует отсутствия будущих vendor corrections. Истинное publication
по-прежнему NULL. При stale/unstable/holiday нет backdate/alternate provider.
Новая пара сравнивается последовательно, используется последний stable snapshot,
issue UTC только после collection/readiness, модели должны существовать раньше.
Старые model qualified/calibrated=false и отрицательные PR26 результаты сохранены.

## Проверки и приёмка

[Verification manifest](verification.json) и head-specific CI в описании fix PR.
Mocked successful generation, auth, timeout/429/retry bounds, stale/missing data,
holiday/DST, DB failure, duplicate/partial batch, UTC/as-of, secret redaction; также
реальные disposable PostgreSQL permission/rollback/readonly/migration/restore checks.
Только synthetic в тестах; они не доказывают новое Railway execution.

| Критерий | Статус этой работы |
|---|---|
|Failure branch/observability cause|VERIFIED code+structured logs; changed historical field UNVERIFIED|
|Repeatable automated tests|См. verification/CI, не deployment proof|
|Новая real research execution без unhandled errors|UNVERIFIED, approval/deployment pending|
|Новый actual EODHD HTTP response/auth/data check|UNVERIFIED; historical parsed-input success наблюдался в старых logs|
|Actual forecast generation старой версии|APP-LOG OBSERVED216+216; новая версия UNVERIFIED|
|Независимый PostgreSQL SQL count/distribution/duplicates|UNVERIFIED: private DB, no TCP proxy/query/CLI access здесь|
|Count/first UTC|Last application SQL log432 /2026-11-13T02:05:45.498639+00:00; fresh SQL UNVERIFIED|
|Secret logging|Mock redaction tests + no secret-bearing fields in captured log sample; new live logs UNVERIFIED|
|Production/trading/history modification|NONE; no Railway mutation/deploy in this task|

Следующий шаг — отдельное подтверждение deployment **fix SHA** только в указанном
research worker с additive005, затем read-only SQL-аудит и наблюдение допустимого
cron. [Инструкция и точные команды](deployment-approval-ru.md). Нет merge в main.

Локально **379unique tests PASS**:188pipeline на disposable PostgreSQL18
(164прежних+24новых),180всех7parent suites,9knowledge,2root,0skips. Полный12table
PR26 replay/222frozen artifact reproduction PASS. Synthetic4schema dump/restore,
обе journal chains и operation content hashes совпали. Никакой Railway execution
не выполнялось. Финальные PG16/18 и online knowledge CI проверяются на fix head;
ссылки на конкретный SHA/runs находятся в описании fix PR.
