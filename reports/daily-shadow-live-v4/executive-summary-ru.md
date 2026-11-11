# Alpha OS — daily EODHD worker v4

**NO-GO операционная приёмка: запуск не выполнен.** Код подготовлен в существующем
Draft PR28, но в Railway нет подтверждённого реального прогноза или действующего
расписания. Тесты и backtest не заменяют эти условия.

## Фактический результат

| Требование | Статус |
|---|---|
| Paid EODHD personal / принятие текущих условий | Подтверждено владельцем в этом задании; не независимый invoice audit |
| EODHD_API_TOKEN | Имя переменной присутствует в staged worker; значение не читалось/не выводилось |
| Реальный EODHD data API /6symbols/actions | **NOT RUN**: Railway deployment не разрешён контролем согласования |
| PostgreSQL18 Railway | Только staged-create, latestDeployment=NULL |
| Настоящие прогнозы, записанные этой работой в Railway | **0; независимая SQL-приёмка NOT RUN** |
| Первый настоящий выпуск | **Отсутствует, UTC NULL** |
| Ежедневное расписание | Код0 2 * * 2-6 подготовлен; **не активно** |
| Историческое сравнение нового EODHD с прежним источником | Код/causality tests готовы; реальный licensed comparison **NOT RUN** |
| Торговые операции / production / merge | Не выполнялись |

Причина: `railway_accept_deploy` для environment
`eb43b87d-7d51-46a6-829d-cd0c5b68e0f2` вернул:
`Cancelled — the user did not approve this action. No changes were made.`
Это результат контроля согласования, а не вывод об отсутствии воли владельца:
само задание явно разрешает изолированный запуск. Обход отказа не предпринимался.
Staged изменения сохранены для review/продолжения. Полные действия:
[передача запуска ChatGPT/Railway](railway-handover-ru.md).

## Что реализовано

- Отдельные Railway Dockerfile/config и worker для точных project/environment/service
  IDs. Root production railway.json и торговые точки входа не менялись.
- SQL001–004 с hash-ledger и idempotent bootstrap, pinned exchange calendar,
  genuine222frozen HIST/REGIME artifacts, ни одной искусственной модели в runtime.
- Paid account metadata по документированной схеме subscriptionType monthly/yearly,
  dailyRateLimit>=100000 в сочетании с подтверждением владельца и full data fetch.
  User API не подтверждает product/инвойс/paid-through: это не выдумывается.
- Личное существующее платное использование явно отделено от точного invoice total:
  total=NULL, owner-authorized cap50. Новых подписок/топапов нет. Это не утверждение
  о проверенной сумме налогов. Legal basis — current Terms/Storage FAQ плюс owner
  acceptance; individual provider letter/независимой юридической экспертизы нет.
- Raw/split-only/total-return basis, metadata USD,6last same-session bars, полные
  календарные ряды,4primary corporate-action samples, два одинаковых snapshot
  с gap>=60s после20:30NY. SQL сохраняет per-session readiness evidence. Publication
  NULL; стабильность не обещает отсутствия последующих vendor corrections.
- Реальный clock после collection, server UTC issue, no backdate, weekend/holiday/
  early-close/DST gates; один ежедневный запуск02:00UTC Tue–Sat. Идемпотентный retry
  читает исходный batch, не создаёт новые forecast IDs.
- Численные HIST/REGIME и отдельный prequential baseline пишутся атомарно. Для
 6tickers потенциально216numeric series +6blocked A/B/C. Это два метода на111
  event definitions, а не222независимых подтверждения. Calibrated probability=NULL,
  MODEL_NOT_VALIDATED/TRAINING_REPLAY_NOT_PIT и старые qualified=false сохранены.
- Полные10/20/60-session outcomes из original private anchor, append-only corrections,
  weekly private reports Brier/logloss/event frequency/calibration, отдельный
  Beta1/1 prequential baseline с cold-start0.5/support0. Только genuine records;
  synthetic/replay исключены. CI/independent event count при отсутствии данных NA.
- TTL purge выполняется также при ошибке источника. Данные в deletable encrypted
  private vault, safe forecast journal отдельно. Bounded paid-status continuity
  renewal не даёт новых юридических прав. Secrets не записываются в Git/логи.
- Private historical comparison одинаковыми annual expanding fits: same common
  anchors, >=252mature training labels, horizon purge,200QQQfeature sessions,
  beta1/1/shrink20. Прежняя frozen история проверяется hashes; EODHD today revised
  vintage, **не original PIT**. Ни raw history, ни individual EODHD forecasts/новые
  derived test results не публикуются в Git.

## Ограничения готовности

Не выполнены реальные API/coverage/price/action checks, Docker deployment, миграции
Railway, SQL-приёмка, запуск cron, реальная историческая оценка или уведомление
внешнего адресата. Нет empirical results, оценок преимущества или даты первого
выпуска. Подписка подтверждена владельцем; актуальность конкретного токена не проверена.

Admin bootstrap/legal continuity credential пока в private worker environment,
writer применяется через SET ROLE; дальнейшее разделение credentials необходимо
для усиления безопасности. Vault key может задаваться независимо, иначе derived
from DB password: перед rotation нужен rekey/recovery. Cross-host/PITR/WORM и
реальный purge всех backups/WAL/DR не сертифицированы. Native backup schedule и
внешние email/webhook адресаты не настроены. Уже MATURED outcomes поздней vendor
revision автоматически отдельным job не переоцениваются: explicit corrections
поддержаны, отдельный revision-review остаётся следующим этапом.

PR26 негативные0/9 primary wins и отсутствие validated35/51/60thresholds сохранены.
Нового predictive advantage нет оснований заявлять. Следующий критерий приёмки —
после разрешённого deploy **actual SQL count>0, actual first_issue_utc и active cron**.
Переданное расписание/ожидаемые216строк не являются фактом запуска.

## Проверки кода (не операционная приёмка)

Локально355уникальных tests PASS:164pipeline на disposable PostgreSQL18
(142прежних+22новых),180семи parent suites,9knowledge,2root, без skips. Новый
bootstrap выполнен повторно с неизменными hash-ledger; четыре schema восстановлены
из synthetic dump, journal chain и operation content hashes совпали.222реальных
frozen artifacts воспроизведены, полный12table replay PR26 PASS. Online knowledge
validator с base291762bb951ce806f7e289bd261e6797664e9dd7 PASS.
[Verification manifest](verification.json). CI также выполняет PostgreSQL16/18 matrix;
окончательные head-specific ссылки приводятся в описании PR. Эти проверки ничего
не доказывают о доступности действительного EODHD токена или работе Railway cron.
