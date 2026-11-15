# Reviewable deployment plan — approval required, NOT APPLIED

Текущая задача прямо запрещает deploy/environment changes без отдельного approval.
Ничего не staged/changed в Railway. Новый fix PR targets research/daily-shadow-postgres-v1.
Использовать проверенный SHA из финального fix PR, не произвольный branch tip.

1. Проверить scope: project73fc59d1-8aaf-480d-bc33-313cbdf428e6,
   environmenteb43b87d-7d51-46a6-829d-cd0c5b68e0f2,
   worker4a395356-42c7-4489-a051-5789bf51e206. Текущий pinned source f066a5ecc4dc8c1984905b748d5781fe7235bb94.
   PostgreSQL5fed870a-5458-4034-8975-9721c186889a running/private. Production не выбирать.
2. После явного approval: stage только worker source на approved fix SHA через
   railway_connect_service_source(repo=volk468-max/Analytical-Engine,
   branch=fix/daily-shadow-worker-diagnostics,commitSha=APPROVED_SHA,staged=true,
   exact project/environment/service IDs). Сохранить существующие переменные, токен
   не читать/не копировать. Сохранить cron0 2 * * 2-6, Dockerfile/entrypoint/predeploy.
3. Read-back source/config и staged scope; после разрешённого accept-deploy ждать
   terminal SUCCESS. Это только deployment criterion, не forecasting acceptance.
   Predeploy применяет неизменённые001–004 и новую005, не переписывает прогнозы.
4. Проверить BOOTSTRAP STARTED/READY/COMPLETED с run UUID. Counter
   forecasts_created_by_bootstrap=0 означает именно created here, не размер БД.
   RUN_STARTED, HTTP actual status, READINESS fingerprint kind, ISSUE, EVALUATION,
   RUN_COMPLETED с exit0/1/2 и одним UUID daily run должны быть видимы в message
   и attributes. SUCCESS без ISSUE RECORDED не означает новый прогноз.
5. Независимый SQL: новый module внутри worker context, без EODHD/DB writes:

```
python -m research.daily_shadow_live.inspect_persistence
```

   Либо выполнить локальный `research/daily_shadow_live/acceptance.sql` через
   authenticated Railway SSH/psql в **research Postgres**, не открывая public proxy.
   Пример psql внутри PostgreSQL container:

```
psql -X -v ON_ERROR_STOP=1 -U "$PGUSER" -d alpha_shadow_research
```

   Подать SQL из файла, выполнить READ ONLY snapshot. Credentials берутся внутри
   Railway, не печатаются/не выгружаются в Codex. Самого нового SQL module сейчас
   нет в старом image до approval. Здесь нет authenticated CLI/query transport;
   нельзя объявить independent SQL PASS по app logs. Полный module также проверяет
   entirely missing sessions начиная2026-11-11, а не только уже записанные даты.
6. При необходимости off-schedule run использовать штатный Railway Cron Run Now
   после approval; CLI из authenticated operator context:

```
railway cron run --service 4a395356-42c7-4489-a051-5789bf51e206 --environment eb43b87d-7d51-46a6-829d-cd0c5b68e0f2 --json
```

   Project context должен быть указан выше. Нельзя обходить same-session/holiday/
   source gates или симулировать новые live записи.15.11.2026 — воскресенье: успешный
   skip не доказывает генерацию. Следующий обычный cron17.11.2026 02:00UTC =
  16.11 21:00NY EST. Дождаться разрешённого окна; не backfill пропуск11.11.
7. Принимать только: parsed six-symbol EODHD responses, stable semantic inputs,
   ISSUE RECORDED216numeric+6diagnostics, original UUID/timestamp unchanged on retry,
   SQL totals/per-date/per-ticker/first/latest/duplicates/missing-grid, завершение
   с exit0 и отсутствие secrets. Утверждение модели validated не допускается.
   Code tests и deployment success не заменяют эту проверку.
8. Rollback после отдельного разрешения: re-pin f066a5ecc4dc8c1984905b748d5781fe7235bb94
   в том же research worker.005 backwards-compatible с old receipt fields; не делать
   destructive down migration, не удалять forecasts/outcomes/receipts. Архивировать
   новые private snapshots по текущему TTL/лицензии, не публиковать raw в Git.

Остаются прежние ограничения: independent retention/legal review, разделение admin/
writer credentials, key rotation/backup recovery и внешние notification адресаты.
Ни одно из них не объявлено выполненным deployment diagnostics fix.
