# Ручная подготовка Railway: действия после отдельного разрешения

**Сейчас NOT RUNNING.** Ничего ниже на Railway не выполнялось. Owner comment
6743417658 разрешает code/review/disposable staging, не production migration,
deploy, cron, платные ресурсы или сделки. Исходный v1 runbook сохранён отдельно.

## 1. Согласовать конкретную изоляцию и доступ

- Новый research project/environment/DB, точные одобренные project/environment/
service IDs и domain; не существующий production Postgres/Analytical2.0/collector.
DB `alpha_shadow_research`, schema `alpha_shadow_v1`, PostgreSQL18. При совпадении
имени БД всё равно отдельно проверить изоляцию/ID; имя не доказывает безопасность.
- Отдельный migration owner LOGIN только для ручного bootstrap, отдельные app,
reader и model-registrar LOGIN. Не выдавать app owner/superuser/CREATEDB/CREATEROLE/
pg_signal_backend/schemaCREATE. Никто не наследует registrar автоматически.
- Разные credentials, TLS/private network, секреты только в approved secret store.
Нет reuse production DATABASE_URL, нет вывода DSN/паролей/raw auth headers в логи.
- Согласовать provider-specific licensing, raw archive/backup/retention права,
публикациюUTC, corporate-action source и completeness, coverage всех6symbols.
Текущий collector contract не годится; live adapter отсутствует по конкретному blocker.

## 2. Ручная migration, не startup hook

Только после проверки approved isolated endpoint и отдельной авторизации оператор
задаёт **SHADOW_MIGRATION_DSN** вручную. Он не читается pipeline автоматически.
Проверить `current_database()`, `current_user`, `version()`, утверждённый serviceID.
Не запускать SQL на действующей application DB.

```sh
psql "$SHADOW_MIGRATION_DSN" -v ON_ERROR_STOP=1 -f research/daily_shadow/sql/001_isolated.sql
psql "$SHADOW_MIGRATION_DSN" -v ON_ERROR_STOP=1 -f research/daily_shadow/sql/002_contract_hardening.sql
```

Каждый script — транзакция с guard по имени БД; повторный запуск migration не
маскирует конфликты IF NOT EXISTS. Review hashes/pinned code SHA перед исполнением.
`local_fixture_roles.sql` и пароль synthetic-local-only — **исключительно локальный
тест/CI**, никогда Railway. Реальные LOGIN/пароли создаёт оператор отдельно:

```sql
-- Placeholders: use independently generated credentials through a secure operator channel.
CREATE ROLE shadow_job LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT alpha_shadow_writer TO shadow_job;
CREATE ROLE shadow_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT alpha_shadow_reader TO shadow_reader;
CREATE ROLE shadow_model_operator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT alpha_shadow_model_registrar TO shadow_model_operator;
```

Пароли не заданы этим фрагментом: operator configures them securely; не оставлять
пустую/небезопасную аутентификацию. Registry artifacts из этого PR qualified=false.
Registrar может добавлять только models и не должен просто менять flag ради PASS:
новый reviewed immutable version требует source/code/availability/action evidence.
App может только зарегистрировать unqualified/synthetic manifests или повторить
уже утверждённый manifest; не может самостоятельно создать real qualified model.
Внутренний append_event_v1 закрыт от app; append guards нельзя обойти прямым вызовом.

## 3. Backup / restore / WORM до первого live

- Утвердить RPO/RTO, encrypted backup и retention сроки, location/access/billing,
права на backup raw payload. Предложение: RPO24h/RTO24h, daily full backup и отдельная
оценка доступного PITR. Это предложения, не обещание Railway backup/PITR capability.
- Ручной `pg_dump -Fc --schema=alpha_shadow_v1` только из isolated DB; хранить
зашифрованно вне той же failure domain. Не отправлять dump/секреты в public Git.
- Restore всегда в НОВУЮ isolated restoreDB/кластер, с отдельно восстановленными
roles/grants. Сравнить counts, ordered audit payloads, hashchain, FK и app-role
отказы UPDATE/DELETE/TRUNCATE; отдельно проверить permission восстановления.
- CI выполняет настоящий pg_dump/pg_restore и read-only hash/content comparison в
fresh `alpha_shadow_restore` на PostgreSQL16/18. Это synthetic same-cluster proof,
не cross-host/PITR certification. Первая локальная попытка была BLOCKED
лимитом диска (checkpoint сохранён). После удаления только собственного test image/
container финальный local PostgreSQL18-alpine restore в новую БД прошёл:992audit
rows и hash chain совпали; чужие ресурсы не изменялись. См.restore-rehearsal-v2.json.
- До stronger immutability claim: отдельный daily chain-head anchor, подписанный
ключом ВНЕ DB/app, offsite WORM/export. Утвердить независимого проверяющего,
rotation/recovery/revocation ключей. Сейчас signer, WORM storage и backup service
не созданы. Superuser/owner может отключить triggers/переписать всю цепочку.
- Текущий audit body содержит raw_b64 и не допускает TTL удаления отдельного raw
payload. Если licence требует более короткий retention, эта схема НЕ совместима:
сначала redesign с versioned external raw object + immutable hash/reference и
согласованным TTL/backup erasure. Нельзя обещать удаление raw, остающегося в audit.

## 4. Бюджет, health и остановка

Плановая оценка $10–30/месяц для малой БД+ephemeral jobs, не текущая котировка;
предлагаемый cap$30 не одобрен. Перед provision проверить реальный Railway тариф,
CPU/RAM/storage/egress/backup и source licensing cost; ничего не покупать сейчас.
222×252≈55944forecast rows/year; при2–10KB это112–560MB только forecasts до индексов.
Mature labels/model manifests/source archives/backups добавляют объём. Нельзя
ежедневно писать IMMATURE для каждого ещё незрелого forecast без бюджета: при
среднем30попыток это≈1.7moutcome attempts/year. Предложение: backlog через read query,
IMMATURE только на существенных audit checkpoints, mature один раз +явные revisions.
Raw bytes/storage измерить на approved supervised source до утверждения cap.

Утвердить recipients/channel и разрешение на отправку уведомлений. Сейчас никому
ничего не отправлялось. Метрики: expected111targets/modelversion/day, blocked/NULL,
publication→ingestion→decision→issued→recorded latency, staleness, retry/DB rollback,
outcome gaps/backlog, hash/export age, backup/restore failure, usage/cost projection.
Пороговые правила operational предлагаются отдельно: любой hash/permission fault
останавливает launcher; source gate =>NULL, без forward-fill. При DB outage процесс
должен завершиться ошибкой; внешний supervisor сохраняет failure и выполняет
bounded retry. Не писать фиктивную успешную health row в недоступную БД.

Rollback: pause будущие jobs/revoke app LOGIN по approved procedure; сохранить
original records и corrections. Не DROP/переписывать forecasts/labels. Патч новой
версией параллельно старой, не менять historical probabilities или model versions.

## 5. Отдельное go-live approval, не часть этого PR

- [ ] Approved isolated serviceIDs/DB/migrations/roles/TLS/secret separation.
- [ ] Verified provider terms/coverage/publication UTC/actions/raw retention;
реализован и independently reviewed actual live ingestion adapter.
- [ ] Training/history qualification +frozen causal manifests; раздельные qualified/
calibrated flags; baseline alongside REGIME. PR26 0/9 не превращается в superiority.
- [ ] Backup/restore cross-host/PITR plan, WORM/signer и проверяющий, retention.
- [ ] Cost cap/billing alerts и failure recipient/channel approved.
- [ ] Go-live date и supervised first session после официального close и release;
реальные UTC rows/source hashes независимо проверены до объявления started.
- [ ] Только отдельное разрешение на конкретный pinned cron service/schedule;
кандидат30 23 * * 1-5 UTC, не установлен. Calendar/DST/holidays/early-close gate
обязателен. Provider contract/latency может потребовать другой schedule.
- [ ] Resolver отдельным job после full10/20/60 maturation; revised evidence через
новые label/correction rows, не backdated issuance; SYNTHETIC/BACKFILL исключены.
- [ ] Мониторинг минимум12months только для data quality; efficacy/power отдельно,
не90day promise. Protective35/51/60 thresholds и торговля не утверждены.

До всех зависимостей и отдельного согласования: **NO-GO LIVE / NOT RUNNING**.
