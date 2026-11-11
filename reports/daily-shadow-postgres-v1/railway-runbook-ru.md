# Railway: план, а не выполненный запуск

Статус **NOT RUNNING**. Issue27 разрешает code/design/Draft, не deploy/provision/cron.
Read-only inventory: skillful-reflection содержит production Data-collector-1.0,
Analytical2.0,Alpha-5,Postgres,Redis и другие сервисы. Проверены platform metadata,
source/variable NAMES, не значения. Data collector имеет ADC_DB_PATH; API contract,
права источников и реальная freshness семантика неизвестны. Analytical2.0 связан
с DATABASE_URL, это не разрешение использовать базу. Postgres image18, доступные
SQL roles/схемы/права НЕ проверялись. Ни одного подключения к Railway DB, SELECT,
DDL/DML, secret read или изменения existing services не было. Local integration
uses disposable PostgreSQL16; PostgreSQL18 qualification отдельный staging gate.

Рекомендуется НОВАЯ отдельная researchDB, не existing production Postgres. Schema
alpha_shadow_v1, DB alpha_shadow_research; owner migration role отдельно от NOLOGIN
writer/reader group roles, dedicated LOGIN secrets только в Railway settings.
Application не superuser, не table owner, no schema CREATE/UPDATE/DELETE/TRUNCATE.
Migration 001 — review artifact; не выполнялась на Railway. Приложение не получает
админский DATABASE_URL и не имеет migration-on-start. Rawresponses в изолированной
DB с hashes, source licence/retention metadata; не в public Git для будущих paid/
restricted feeds. В репозитории только synthetic fixtures/исследовательский код.

## Checklist отдельного явного согласования

- [ ] Separate project/environment/DB choice, точные IDs, запрет production reuse.
- [ ] Одобрены SQL namespace, migration role, LOGIN app/reader grants; TLS/private network.
- [ ] Provider terms, redistributions/retention, licence/cost, exact release/ingest,
corporate actions и live raw archive independently verified; исторический архивне feed.
- [ ] Freeze modelcode/parameters/source/protocol hashes, targetmanifest и период
минимум12months data-quality monitoring; новые версии только parallel series.
- [ ] Принят monthly cost cap и billing alerts (никаких paidresources сейчас).
- [ ] Отдельный одобренный Railway cron service, pinned SHA; candidate schedule
30 23 * * 1-5 UTC, НЕ установлен. Обязательны calendar/close/publication gates.
Provider retries max3, no infinite sleep, one-shot exits; duplicate jobs DB serialised.
- [ ] Outcome resolver отдельный one-shot service после daily ingestion, own app role;
full10/20/60 maturity evenearly hit, independent source lineage.
- [ ] Согласованы failure notifications: канал/получатель/разрешение отправлять.
Сейчас уведомления никому не отправляются. Failure health durable; failed DB commit
must fail process, external scheduler failure signal/approved notifications needed.
- [ ] Retention: forecasts/labels/corrections keep весь утверждённый research period;
rawresponse срок зависит от licence; delete only approved owner retention process
после immutable export, не через application. Нельзя молча удалить часть цепочки.
- [ ] Backup/PITR/snapshot plan, encrypted offsite exports, restore drill, retention
и ежедневный signed/WORM anchor; hashchain alone не защищает отDBsuperuser.
- [ ] Backfills только BACKFILL/newseries, no historical claim prospective; corrected
sources appendlinked corrections. No retroactive replacement of blocked day.
- [ ] Go-live date, timezone, supervisedfirstsession, verify actual UTCrows BEFORE
announcing started; current status remains NOT RUNNING. Нет обещания modelpower90days.

Оценка бюджета (плановая, НЕ quote):222series/day*252≈55944forecastrows/year плюс
2rawmodel versions, runs/vintages/outcomes/corrections/health. 2–10KBforecastpayload
даёт112–560MB/year до индексов/backup, raw archives могут доминировать. Оценка
малого DB+ephemeralcron $10–30/month требует проверки текущих тарифов/плана,CPU/RAM,
storage/egress/backups; предлагаемый cap$30 только к обсуждению, не одобренная трата.
Railway docs search подтверждает UTCcron и минимум5minutes spacing. Full-page
fetch инструментом вернул pageFound=false, поэтому overlap/backup semantics нужно
сверить повторно перед запуском; собственная идемпотентность не полагается на cron.

## После одобрения, не сейчас
1. Изолированная stagingDB, manualmigration, grants/security/restore smoke checks.
2. Supervised synthetic run с отдельным режимом, verify counts/unique/hash chain,
source health и отказ UPDATE/DELETE; synthetic никогда не performance evidence.
3. Qualified live adapter+model manifest review, first actual session manually,
check real timestamps/raw hashes/222completeness; приblocker Pnull, не fakePASS.
4. Только затем separatelyapproved cron. Pause launcher onfailure, preserve records;
rollback = остановить новые jobs, не переписывать/удалять историю.

No merge/deploy/services/DB/schedule/realtrade/purchases were performed for this PR.
