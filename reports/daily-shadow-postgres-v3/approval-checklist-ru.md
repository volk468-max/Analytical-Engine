# Отдельные согласования и ручной runbook — НЕ выполнены

Основание: комментарий владельца 6788172712 разрешает код и disposable staging,
прямо исключает purchase, реальные forecasts, платный provisioning и production.
Ниже условия будущего согласования, а не новые согласованные решения.

## Перед покупкой (отдельное решение владельца)

- Фактический оператор уточнён владельцем11.11.2026: только личное исследование.
  Повторно проверить классификацию при изменении use case. Public repo не должен содержать provider-derived цены/реконструируемые ряды.
- Сохранить датированную применимую редакцию Terms и письменный/официально применимый
  ответ EODHD на прежнее противоречие FAQ/deletion, личную cloud PostgreSQL установку,
  encrypted/offsite backups, сроки raw/hash/derived retention и права на publication.
  Подготовленные вопросы в provider memo. Ответов пока нет, письма не отправлены.
- Для Tiingo: отдельное retention exception с ценой и областью; Power текущим ToS
  исключён из exception, планы с такой возможностью от$250. Не закупать неподходящий
  план с надеждой решить это позже. Trial не используется как бесплатный durable feed.
- Подтвердить final invoice EODHD$19.99 + taxes/fees/addons <=$50/month именно для
  данного оператора. Для Tiingo$30personal/$50internalCommercial — не полная quote.
- Отдельно согласовать инфраструктуру: ориентир$10–30/month (исследовательская БД,
  worker, backup storage), не гарантированная Railway quote, не часть vendor$50cap.
  Потребуются фактический расчет billing/egress/storage и верхний лимит расходов.
- Выбрать источник и условия отмены/удаления. Текущий итог NO-GO provider; код не
  заменяет этих проверок. Никакой подписки/аккаунта не создано.

## Перед первым реальным one-shot (ещё одно отдельное решение)

1. Указать новый изолированный проект/БД и region, точные роли и доступ к private
   plane; не действующая production DB. Разрешение на ручную миграцию отдельно.
   SQL001,002,003 последовательно применяются admin; immutable exchange calendar
   грузится из pinned exchange_calendars4.11.2. CLI setup_fixture_db **только local
   disposable** с искусственными ролями, не инструкция переносить test password в cloud.
2. Разделить секреты admin/legal-reviewer/writer/reader/provider/Fernet; least privilege,
   rotation/key recovery вне БД/Git; не использовать production credentials.
3. Reviewer регистрирует LIVE contract capability manifest только после проверки
   прав. Явно разрешены raw, hash metadata, nonreconstructible forecast history,
   cloud и backups; TTL должен покрывать самое длинное60-session окно+availability.
   Fixture-only permit не даёт реальных прав. Реальные frozen models заранее записать
   в registry; qualified/calibrated=false не менять.
4. С лицензированным доступом проверить фактические6symbol/US/currency/actions,
   корпоративные события NVDA/MU/QQQ по primary references, recent2026same-basis bars
   с допусками из protocol; каждый результат и receipt проверяются человеком.
   Сейчас эти сравнения BLOCKED, не пройдены на основании фикстур.
5. В нескольких будущих сессиях измерить реальную доступность/исправления после20:30
   NY (включая DST/early close), обосновать finalization_verified. Истинное publication
   сохранять NULL, если поставщик не предоставляет подтверждённую метку.
6. Создать backup/WAL/log/storage inventory с точным TTL по договору; immutable raw
   WORM только если совместим с удалением. Провести восстановление сначала на
   синтетике, затем по отдельно разрешённым данным. Fresh external license authority
   обязательна до восстановления/доступа к licensed backup. Storage receipt включает
   все active/DR/offsite copies; crypto deletion сама по себе не считается исполнением.
7. Зафиксировать адресатов мониторинга без отправки сейчас: source late/stale/gap,
   unknown currency/basis/action, license expiry, missing credential, DB/chain failure,
   unexpected NULL, missing HIST/REGIME pair, duplicate issue, legal deletion pending.
   Проектный operational SLO — проверка до21:30NY; это не SLA поставщика. При ошибке
   блокировать выпуск, сохранять безопасный HEALTH, не backdate. Не повторять процесс
   бесконечно: ограниченный retry вручную, идемпотентный anchor.
8. После отдельного разрешения сделать ОДИН supervised real run с реальными UTC после
   collection и current local session. Независимо проверить UUID, raw/calibrated,
   model hash/creation, source retrieval/publication, mode=RESEARCH_FORECAST,
   MODEL_NOT_VALIDATED, TRAINING_REPLAY_NOT_PIT, оба HIST/REGIME, A/B/C=NULL.
   До inspection не заявлять live launch. Никакого trading action/production consumer.
9. Любой scheduler, deployment или production integration требует ещё одного
   согласования. Rollback: остановить будущие вызовы/revoke access; immutable forecasts
   не менять; source offboard, purge active/licensed backups, независимая receipt,
   восстановление запрещено до актуальной лицензии. Не сливать Draft автоматически.

## Воспроизведение сейчас (только disposable loopback)

Создать собственный локальный PostgreSQL16 либо18, БД alpha_shadow_research и
синтетический admin password. Явно задать ALPHA_SHADOW_TEST_DSN (admin loopback) и
ALPHA_SHADOW_STAGE_DSN (local alpha_shadow_test_app) как в CI. Затем:

```
pip install -r research/daily_shadow_v3/requirements.txt
python -m research.daily_shadow_v3.setup_fixture_db
python -m unittest research.daily_shadow.test_core research.daily_shadow.test_postgres research.daily_shadow.test_reporting research.daily_shadow.test_preparation research.daily_shadow_v3.test_unit research.daily_shadow_v3.test_postgres -v
python -m research.daily_shadow.verify_preparation
python -m research.daily_shadow_v3.rehearsal
```

Далее full-schema synthetic pg_dump/pg_restore и два verifier согласно
`.github/workflows/daily-shadow.yml`; parent seven suites, root tests, PR26verify_v2
и knowledge validator. Никакой paid API или реальные forecast строки не нужны.
