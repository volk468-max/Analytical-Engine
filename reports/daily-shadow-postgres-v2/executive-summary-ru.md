# PR28: PostgreSQL18 rehearsal и готовность к supervised запуску

**NOT RUNNING. GO для review/disposable staging; NO-GO для live issuance.**
Pipeline не запущен, actual prospective rows отсутствуют. Ни production DB, ни
Railway services/cron не изменялись; merge, deploy, provisioning и сделки не выполнялись.
Это выполнение [последнего owner задания](https://github.com/volk468-max/Analytical-Engine/pull/28#issuecomment-6743417658),
сохранённого в task-comment.json. Оно разрешает code/review/staging, не live rollout.

## Зависимость и сохранность исследований

Ветка PR28 обновлена rebase поверх актуального DraftPR26
`291762bb951ce806f7e289bd261e6797664e9dd7`, без объединения с main. Конфликты
append-only базы знаний разрешены сохранением обеих историй. PR26 исходные code/
reports/cards/records не менялись; добавлены отдельные R26-v2/Q008-v2 записи.
Старые отчёты daily-shadow-v1 сохранены как checkpoints, этот v2 их дополняет.

PR26 v2: **0/9 calibrated primary wins**, Holm1 для всех18 comparisons; преимущества
над rolling climatology не обнаружено. MU sample подтверждён, QQQ rounding numeric
compatibility не означает full source qualification. Thresholds35/51/60 NOT VALIDATED.
Ни rehearsal, ни новые HIST/REGIME count artifacts не меняют эти отрицательные выводы.

## Источник: точный внешний blocker

Прочитан код Data-collector-1.0 на commit
`ef80df85b5faead5068854afbf9517f97cf9ba00`, paths/blob hashes зафиксированы.
**Не импортировался collector и не вызывался hosted API:** repository construction
даже в GET handler запускает schema init/DDL; app lifespan включает scheduler.
Main не считается доказательством deployed SHA. Production SQL не выполнялся.

[Полная source qualification matrix](source-qualification-ru.md) показывает:
OHLCV/trade_date доступны в кодовом контракте, но source publicationUTC, исходные
raw vintages, action lineage и licence/retention rights не подтверждены. History
записывается INSERT OR REPLACE; metadata.timestamp — naive UTC generation time,
не время публикации. SOXX не входит в configured universe. auto_adjust=False не
аттестует split/dividend units; actions из yfinance не входят в MarketRecord.
Library Apache license не является data licence; owner-specific usage/archiving
rights и retention не установлены. Реальное API coverage/freshness/SLA неизвестны.

Поэтому legal/reliable live contract не квалифицирован, **network live adapter не
реализован и не подключён** — это допустимый заданием конкретный external blocker.
UnavailableLiveProvider работает fail-closed: source_present=false, publication/
ingestion=NULL, причина сохранена; empty bytes означают missing response, не якобы
полученные market data. Fixture adapters — только SYNTHETIC infrastructure tests.

## Frozen HIST/REGIME по каждой серии

| Группа | HIST | REGIME | Артефактов | Genuine live P |
|---|---:|---:|---:|---:|
| SPY/QQQ/SOXX/AMD/NVDA/MU × LOW_INTRADAY/EOD_CLOSE ×5/10/15 ×10/20/60 |108|108|216|0|
| A/B/C × PORTFOLIO_EOD_CLOSE10/60 |3|3|6|0|
| Всего |111|111|222|0|

Code-supported математические labels построены из frozen PR20 OHLC и PR24 portfolio
labels; это новая подготовка frequency artifacts, не восстановленные якобы прошлые
операционные прогнозы. LOW и EOD не смешиваются, nextN excludesanchor, fullwindow
обязателен даже приearly hit; portfolio targets не расширялись. HIST Beta1/1,
REGIME shrink20 по причинному QQQ200SMA/20momentum. Никакого подбора модели/порогов.

Каждый artifact имеет symbol/label/threshold/horizon, immutable content-addressed
version, per-regime n/hits, n/events, first/lastanchor/lastmaturity, digest всех
использованных labels, hashes исходников и builder+engine code. Fit cutoff
2026-11-09T00:00UTC; label maturity строго раньше cutoff. Midnight после последней
сессии — **REPLAY ASSUMPTION**, не истинное historical publication evidence.
Actual preparation timestamp записан отдельно, версия не может быть выдана раньше
её создания: это проверяется и в коде, и в SQL. Повторный build reproduces versions;
поменять body под тем же immutable filename нельзя. Source prices не обновлялись.

У всех222: qualified=false, training_source_qualified=false, calibrated=false;
causal numerical code verification не означает PIT/forecast validation. Count bank
не выдаётся за независимо validated model. Для каждой серии базовый HIST сохраняется
рядом с REGIME, никакой winner-selection. Frozen models загружаются без daily refit;
новая версия должна идти отдельной параллельной серией, не переписывать прежнюю.

Registry routing/writer исправлены для множества версий с общим именем HIST/REGIME:
выбор строго по четырём полям цели, reference по name+version, неоднозначность —
ошибка. Model artifact из другого symbol/target отвергается также SQL guard.
Real-qualified model может добавить только отдельный registrar; app не может
квалифицировать себя. Synthetic-only model/source никогда не проходят в PROSPECTIVE.

## Dry-run и supervised PostgreSQL18 rehearsal

Registry/data-gate assessment: **222 requested, 222NULL, 0genuine live eligible**.
series-coverage.csv содержит каждую серию/версию/историческую поддержку и причины:
NO_VERIFIED_LIVE_PUBLICATION_ACTION_LICENSE_CONTRACT; TRAINING_HISTORY_NOT_PIT;
MODEL_UNQUALIFIED. Calibrated P=NULL для всех. Это assessment, не actual issuance.

Отдельный воспроизводимый SYNTHETIC rehearsal в disposable local PostgreSQL18
проверяет инфраструктуру; его собственный least-privilege LOGIN не superuser,
не DB/schema owner, не registrar и не pg_signal_backend. Проверено:

- Atomic222blocked rows и уникальные immutable model references; повторные запуски
возвращают те же original IDs, source revision не маскируется как retry.
- Пара HIST/REGIME с синтетическим known contract даёт raw0.5 только в режиме
SYNTHETIC; это **2fixture scores**, не2real forecasts и не data/model qualification.
- Исправленный raw response отдельно архивируется, correction связан с исходным
forecast; original probability/anchor/record не меняются.
- Provider timeout имеет bounded3 attempts; отдельная health и UNRESOLVED outcome,
без выдуманного успешного source timestamp. Следующий вызов восстанавливается.
- Принудительно разорван собственный backend после первого forecast INSERT:
транзакция полностью откатывается, новый connection+retry сохраняет весь batch.
Другие connections не останавливались и права на signal чужих процессов не выдавались.
- Early hit =>IMMATURE, затем exactfull10session window =>MATURED; labels append,
retry зрелого исхода идемпотентен. Core tests отдельно проверяют10/20/60 границы,
late publication, calendar/DST/holidays/earlyclose, source/basis/action failures.
- UPDATE/DELETE/TRUNCATE запрещены, внутренний append_event_v1 недоступен app,
hash chain проверяется. Corrections и новые label rows сохраняют provenance.
- Все записи rehearsal SYNTHETIC; проверено отсутствие созданных PROSPECTIVE runs.
Model quality report по-прежнему исключает fixtures/backfills/blocked/null rows.

Migration001 сохранена; новые contract/role guards — отдельная
002_contract_hardening.sql. Обе применялись только к disposable local test DB.
Local_fixture_roles.sql содержит явно synthetic credentials, не Railway секреты.

## Проверки и воспроизводимость

Команды и контракты: research/daily_shadow/README-v2.md. Локально прошли78
unit/integration cases на PostgreSQL18 (25integration,53unit,0skips); CI matrix
дополнительно проверяет PostgreSQL16 и18. Отдельно
выполнены все7parent research suites:180тестов,9knowledge tests и2root engine tests.
Финальные SHA и CI run links фиксируются в описании существующего DraftPR28.
Считать PASS только по фактическому завершению CI на этом head, не по наличию YAML.

Frozen222 artifacts воспроизводятся с запрещённым socket; registry coverageNULL
проверяется программно. Полный parent PR26 replay повторно воспроизвёл12таблиц;
его код/результаты не изменены. Test fixtures подтверждают arithmetic/contracts,
а не predictive advantage. Исходные raw SHA и model hashes сохранены в manifests.

Backup/restore: actual pg_dump/restore в свежую локальную PostgreSQL18 DB прошёл,
все992audit rows и hash chain совпали; PROSPECTIVE0. Итог restore-rehearsal-v2.json
сохраняет ссылку на первоначальный disk-capacity BLOCKED checkpoint
restore-rehearsal.json. Удалены только собственные test resources, не чужие данные. CI дополнительно выполняет pg_dump/restore в НОВУЮ
alpha_shadow_restore и read-only exact payload/hash-chain comparison для16/18.
Это same-cluster synthetic proof, не cloud cross-host/PITR/WORM certification.

## GO / NO-GO и точные оставшиеся условия

**GO:** review изолированной архитектуры, frozen artifacts и supervised disposable
staging. **NO-GO LIVE / NOT RUNNING:** квалифицированных live inputs и training
lineage нет; реальных prospective records нет; superiority/threshold policies не
подтверждены. Задание не даёт разрешения включать cron ради получения этих records.

[Ручной Railway runbook](railway-manual-runbook-ru.md) содержит SQL order/guards,
отдельные LOGIN/roles/secrets, backup/restore/WORM, бюджет и rollback. До firstlive:

1. External source dependency: legal/retention/coverage/publication/action contract,
read-only-safe boundary и reviewed actual ingestion adapter с raw archive.
2. Training/source qualification и independently reviewed frozen versions; раздельные
qualification/calibration flags. Нельзя просто изменить false на true ради score.
3. Separate owner approval конкретных isolated serviceIDs/DB/migration/roles/TLS,
cost cap, backup/retention/WORM/signer, alerting recipients/channel и go-live date.
Существующий production Postgres не выбран для reuse.
4. Cross-host restore/permissions/PITR и независимый chain-head export review. В
текущем schema raw_b64 находится в immutable audit body: ограниченный licence TTL
требует redesign с external raw object+immutable hash reference до live ingestion.
5. Supervised session после official close И реальной release, независимый просмотр
фактических UTC rows/hashes; только после этого можно сообщать started. Конкретный
cron service/schedule требует отдельного разрешения, сейчас не создан/не установлен.

Бюджет$10–30/month и cap$30 — proposals, не quote/утверждённая трата. Прогнозируемые
55944forecastrows/year не включают raw archives/labels/backups; ежедневные IMMATURE
attempts могут существенно увеличить объём, поэтому budget их явно учитывает.
Notifications никому не отправлялись. Rollback = pause/revoke futurejobs, сохранить
историю; не переписывать прогнозы/labels. Мониторинг12months — dataquality, power и
эффективность отдельно; source/model blocks не снимаются по истечении90days.
