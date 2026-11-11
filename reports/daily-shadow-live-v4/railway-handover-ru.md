# Передача запуска ChatGPT / Railway — точные действия

**Запуск не выполнен.** Вызов accept-deploy был отклонён контролем согласования:
`Cancelled — the user did not approve this action. No changes were made.` Не обходить
отказ другим deploy-инструментом. Дальнейший apply требует нового подтверждения
в интерфейсе Railway. PR28 остаётся Draft, merge не требуется.

## Точное окружение

- Project `alpha-os-shadow-research`, ID `73fc59d1-8aaf-480d-bc33-313cbdf428e6`.
- Environment `research`, ID `eb43b87d-7d51-46a6-829d-cd0c5b68e0f2`.
- Worker `alpha-shadow-worker`, ID `4a395356-42c7-4489-a051-5789bf51e206`.
- Postgres18, service ID `5fed870a-5458-4034-8975-9721c186889a`.
- Volume `a9f0d0d6-01ac-4dcd-ad7f-c2f35ba5c466`, `/var/lib/postgresql/data`.
- Database **alpha_shadow_research**; private reference
  `ALPHA_SHADOW_DATABASE_URL=${{Postgres.DATABASE_URL}}`.

В staged-патче сохранены PGDATABASE/POSTGRES_DB=alpha_shadow_research,
PGDATA=/var/lib/postgresql/data/pgdata, worker mode=RESEARCH_FORECAST,
ALPHA_LIVE_TRADING=false, лицензия по подтверждению владельца, private DB reference.
Существующий EODHD_API_TOKEN **не читать, не печатать и не копировать**: worker
использует его внутри Railway. Новых подписок/топапов не покупать.

**Текущее временное состояние worker source — официальный python:3.12-slim**,
без кода Alpha OS. Это безопасная промежуточная стадия для создания service instance:
MCP update-service отвечает Service instance not found для staged-create. Само
применение этого патча не запустит прогнозирование. Не выдавать его за готовый worker.

## Через имеющиеся Railway MCP инструменты

После фактического подтверждения apply пользователем:

1. `railway_describe_environment` с указанными project/environment IDs: убедиться,
   что только эти два сервиса и volume, отсутствуют неожиданные изменения.
2. `railway_accept_deploy(environmentId=eb43b87d-7d51-46a6-829d-cd0c5b68e0f2)`
   создаёт изолированную БД и временный пустой worker. Дождаться **SUCCESS Postgres**.
   Python worker может завершиться без действий; это не успешный запуск прогноза.
3. Теперь service instance существует. Вызвать `railway_update_service` для worker,
   `staged=true`, с project/environment/service IDs и параметрами:

```json
{
  "railwayConfigFile": "/research/daily_shadow_live/railway.json",
  "dockerfilePath": "research/daily_shadow_live/Dockerfile",
  "startCommand": "python -m research.daily_shadow_live.runtime",
  "preDeployCommand": ["python -m research.daily_shadow_live.bootstrap"],
  "preDeployTimeoutSeconds": 300,
  "cronSchedule": "0 2 * * 2-6",
  "restartPolicyType": "NEVER",
  "regions": {"sfo":{"numReplicas":1}},
  "limits": {"memoryGB":1,"vCPUs":1},
  "watchPatterns": ["research/daily_shadow*/**","reports/daily-shadow-postgres-v2/**","reports/market-drawdown-precursors-v1/data/**"]
}
```

   Если старый region alias sfo отклонён, оставить существующий worker region,
   не угадывать новый. Разные регионы влияют на задержку, не позволяют менять scope.
   Для Postgres отдельно задать memoryGB1/vCPUs1, если это поддерживается тарифом.
4. `railway_connect_service_source`, `staged=true`, те же IDs, repo
   `volk468-max/Analytical-Engine`, branch `research/daily-shadow-postgres-v1`,
   `commitSha` = **проверенный SHA из итогового PR28/CI**. Pin исключает неожиданный
   redeploy от последующего изменения документации. Image должен стать NULL.
5. Read-back `railway_describe_service`: configFile/Dockerfile/start/predeploy/cron/
   pinned SHA, DB reference, token **name only**; root production railway.json не
   должен управлять worker. Затем согласованный `accept-deploy` для этого environment.
6. Дождаться terminal SUCCESS обоих deployments; не считать QUEUED успешным.
   Predeploy автоматически применяет SQL001/002/003/004, immutable calendar,
   реальные222frozen models и owner-reviewed contract. Ledger проверяет hashes и
   не допускает повторного изменения уже применённой миграции. Test LOGIN роли в
   Railway не создаются. Требуемых CREATE EXTENSION/ALTER SYSTEM нет.
7. Проверить runtime logs без сырых переменных/ответов: PREFLIGHT, ISSUE,
   EVALUATION, HISTORICAL_COMPARISON, ACCEPTANCE_SQL. Ошибка даёт фиксированный
   code и exit1, запись диагностического receipt; внешние email/webhook адресаты
   не настроены, потому что не предоставлены. Настроить Railway уведомления владельца.

## Ручные команды внутри того же изолированного сервиса

Точные команды контейнера, уже заданные в predeploy/start:

```
python -m research.daily_shadow_live.bootstrap
python -m research.daily_shadow_live.runtime
```

Они требуют автоматических Railway identity variables, private DB reference,
ALPHA_LICENSE_MANIFEST и существующего EODHD_API_TOKEN. Нельзя запускать с
production DATABASE_URL, подставлять фиктивные модели или обходить clock/session gates.
Для команды cron из пользовательской CLI с нужным authenticated context:

```
railway link --project 73fc59d1-8aaf-480d-bc33-313cbdf428e6 --environment eb43b87d-7d51-46a6-829d-cd0c5b68e0f2 --service 4a395356-42c7-4489-a051-5789bf51e206
railway status --json
railway cron run --service 4a395356-42c7-4489-a051-5789bf51e206 --environment eb43b87d-7d51-46a6-829d-cd0c5b68e0f2 --json
railway cron list --service 4a395356-42c7-4489-a051-5789bf51e206 --environment eb43b87d-7d51-46a6-829d-cd0c5b68e0f2 --json
```

Проверить help установленной версии при несовпадении flags; не использовать
`railway run` для выгрузки Railway secrets в локальную среду Codex. В Dashboard
допустим штатный Run Now cron. Прямой независимый SQL внутри Postgres: выполнить
`research/daily_shadow_live/acceptance.sql` через psql/SSH с текущим PGUSER,
`-d alpha_shadow_research`. Этот файл не содержит credential или лицензированных цен.
В runtime уже есть отдельный SQL-count, но ручная read-only сверка предпочтительна.

## Приёмка, время и ограничения

Cron02:00UTC Tue–Sat =21:00NY зимой/22:00NY летом в предыдущую local дату. Он
проверяет exchange holiday/early close/current session и реальную готовность всех
шести рядов. Два одинаковых snapshot с интервалом>=60s и4primary action samples
обязательны. Это наблюдаемая стабильность, **не гарантия отсутствия дальнейших
коррекций**. True publication=NULL. Повторный run не повторяет222series; численные
HIST/REGIME и baseline фиксируются атомарно. A/B/C6NULL не считаются выпущенными.

До закрытия/20:30NY first deployment делает только реальный preflight; не выпускает
forecast за предыдущий день. При текущей дате11.11.2026 первый штатный запуск был бы
12.11.2026 02:00UTC **при своевременном развёртывании**. Это план, не факт.
Нужны actual SQL count>0 (ожидаемо216численных рядов, не независимых событий),
first_issue_utc, source_fixture=false, реальные model hashes, active cron и его
actual execution result. Пока этого нет — задача **не принята / NOT RUNNING**.

Weekly report в private alpha_operations_v4.reports: daily immutable snapshots с
week/asof/issued/checked/pending, per-series Brier/logloss/frequency/calibration,
paired HIST/REGIME и prequential baseline (Beta1/1 cold-start0.5 с support0).
Outcomes только после полных10/20/60 будущих sessions. Нет независимых CI/power
до необходимой будущей истории, overlapping series не независимы. Original forecast
не перезаписывается; есть append-only outcome/source corrections. Автоматическая
переоценка уже MATURED при более поздней vendor revision пока не планируется
отдельным job: доступны explicit resolve_once/append correction; это открытая задача.

ALPHA_COMPARE_HISTORY_ONCE=true запускает только private revised-history comparison,
сырьё в encrypted deletable vault, aggregates в reports key2000-01-01. BLOCKED не
считать выполненным тестом; API quota/corporate-action/coverage failures не угадывать.
Никаких рядов/индивидуальных прогнозов EODHD из БД в public Git.

Bootstrap использует admin DSN только из **этой новой БД**; runtime connections
SET ROLE ограниченного writer. Для автоматического continuity-review секрет ещё
остаётся у worker — усиление разделения bootstrap/legal-review/runtime credentials
следующий security milestone. Vault key допускает отдельный ALPHA_VAULT_KEY;
если он не задан, derived from private DB password. До password rotation нужна
rekey/recovery процедура. DB dump сам по себе не содержит этого environment secret.
Это не доказательство cross-host/PITR/WORM или compliance backup retention.

Оператор должен отдельно включить private backup schedule/restore drill в Railway
и inventory WAL/logs/DR/offsite. Сейчас platform backups не настроены/не проверены.
Offboard: остановить cron, выставить ALPHA_RUN_MODE=DISABLED вне backup, revoke
contract/offboard active vault, проверить все копии и receipt. До restore сверить
current external approval/manifest/paid status, а не использовать старую таблицу
contract из restored backup как актуальное право. Никакого trading consumer.
