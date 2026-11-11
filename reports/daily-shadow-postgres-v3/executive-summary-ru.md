# Alpha OS — PR28 v3: EODHD adapter и RESEARCH_FORECAST

**GO для review и синтетического disposable staging. NO-GO provider и первый
реальный запуск. NOT RUNNING.** Личное исследование подтверждено владельцем;
письменных разрешений нет. Подписок, реальных API data запросов, production DB
изменений, live cron, merge, deploy и сделок не было.

Задание: [комментарий владельца11.11.2026](https://github.com/volk468-max/Analytical-Engine/pull/28#issuecomment-6788172712).
Обновляется тот же [Draft PR28](https://github.com/volk468-max/Analytical-Engine/pull/28),
база остаётся unmerged Draft PR26@291762bb951ce806f7e289bd261e6797664e9dd7.
Предыдущий PR28 milestone@947037413cb5386d5b48a4391ff264371653f822 сохранён.
Протокол/сверка поставщиков зафиксированы первыми, до реализации нового режима.
PR26 код/данные/отчёты не переписаны: **0/9 primary wins**, 35/51/60 не валидированы.

## Решение об источнике

[Source-license memo](provider-comparison-ru.md), [dated HTTP/SHA256 evidence](provider-evidence.json).
EODHD personal EOD$19.99/month — **условный приоритет**, Tiingo personal Power$30 —
резерв только при совместимом договоре. Taxes/fees final quote неизвестны;
получение письменного разъяснения не завершено. Личный use case не автоматически
подтверждает все необходимые права cloud/retention/публикации.

Новое наблюдение: в прямом HTML действующей EODHD Terms не найден прежний one-month
termination deletion clause; FAQ допускает private retention и называет Terms
единственным governing document. **Нельзя повторять прежнее противоречие как
подтверждённый текущий факт**, но нельзя и считать его индивидуально разрешённым:
редакция из комментария не восстановлена, ответа провайдера нет. FAQ сообщает об
отсутствии отдельных personal license letters. Нужна применимая датированная
позиция по фактической cloud PostgreSQL/backups установке и данным после отмены.

Tiingo ToS05.11.2026 требует удаления raw/derived data со всех систем/backups/logs,
ограничивает reconstructible derivatives и cross-source validation. Power исключён
из retention exception; подходящие планы от$250/month, выше$50. Hash/encryption —
не автоматический обход. Massive$29/5лет тоже не квалифицирован: retention/ML и
история требуют проверки; приоритет EODHD/Tiingo не подменён третьим поставщиком.
Twelve Data live quote не получена, выбор по неподтверждённой цене не делался.

## Что реализовано и проверяется

Новый provider-neutral contract, strict6symbol EODHD adapter, отдельный
RESEARCH_FORECAST с model_status/data_status. Доступ к сети/секрету после legal
capability gate; publication timestamp NULL, retrieval UTC отдельно. Корректные
raw/split-only/total-return границы, currency/session/as-of/calendar/DST20:30NY,
отдельные revisions и immutable anchor. Новая модель/источник не объявляют старую
историю PIT. Все222старые artifacts по-прежнему qualified=false/calibrated=false.

Старый immutable raw audit не используется для новых licensed payloads. Добавлен
отдельный encrypted **удаляемый** plane с TTL/offboarding, самостоятельная безопасная
append-only research chain. Право хранить hashes и nonreconstructible forecasts
проверяется отдельно. App не выдаёт себе LIVE licence и не подтверждает удаление
backups. Actual offsite/WAL purge/WORM и независимая приемка ещё не выполнялись.

| Сценарий | Requested series | Численные значения | NULL | Реальные prospective observations |
|---|---:|---:|---:|---:|
| Текущая правовая/эмпирическая доступность |222|0|222|0|
| Наши искусственные6symbol fixture inputs и fake count banks |222|216|6 A/B/C|0|

222 — **два HIST/REGIME на111event definitions**, не222 независимые валидированные
модели. Числа из фикстур не являются вероятностями реальных падений. Портфели A/B/C
остаются заблокированы до поддержки same-day self-financing NAV. В отсутствие
законного источника код не выдаёт несуществующую реальную probability.

Outcomes требуют полного10/20/60-session окна даже при раннем touch. Original
anchor берётся из отдельного vault, correction outcome/источника добавляется,
а не перезаписывает forecast. Paired Brier/logloss вычисляются по одинаковым
событиям HIST/REGIME с последними append-only outcomes; synthetic исключается.
**Реальных пар0; Brier/logloss/CI NA; независимые события и мощность UNKNOWN**.
Нового вывода о predictive advantage нет; историческое отрицательное свидетельство
PR26 сохранено. Никакая защитная торговая политика не запускается.

## Проверки и воспроизведение

[API/security/state design](api-and-state-design-ru.md), [manual approval/runbook](approval-checklist-ru.md),
[protocol](protocol.md). **333 уникальных теста PASS локально:**142pipeline (78старых+64новых) на каждом
PostgreSQL16/18, без skips;180всех7parent suites,9knowledge,2root. Полный PR26
replay PASS:7176forecast rows,2392common dates,195000ledger rows,41supported years;
222frozen artifacts воспроизведены без изменения flags. Online knowledge validator
с базой291762bb951ce806f7e289bd261e6797664e9dd7 PASS.
[Verification manifest](verification.json), [synthetic PG18 demo](staging-pg18.json),
[PG16 demo](staging-pg16.json), [PG18 restore](restore-pg18.json),
[PG16 restore](restore-pg16.json). На момент backup18 research journal18901rows и
legacy20766, backup16 research7338 и legacy8624 — содержимое точно совпало после
restore, обе chain валидны, real research/PROSPECTIVE0. Разные размеры — число
локальных повторных синтетических тестов, не количество независимых событий.

При первом запуске тяжёлого local PG16 image закончился filesystem capacity;
освобождён только неиспользуемый тестовый image, затем использован alpine. Повторные
финальные142tests на каждой версии прошли. Также исправлена изоляция теста missing
model при повторном запуске: immutable per-session uniqueness сохранена, тест берёт
свободную synthetic session. Backup не утверждает cross-host/PITR/vendor compliance.
CI запускает те же проверки на head; окончательные head-specific ссылки в описании PR.

Сравнения реальных vendor6symbol coverage, NVDA splits, MU/QQQ dividends и recent2026
bars с первичными источниками **BLOCKED: authorized credentials/contract отсутствуют**.
Допуски объявлены в протоколе заранее, тесты сравнения проверяют только код.
0.573 и0.57345 численно совместимы при округлении до3знаков; это не подтверждение
правил округления EODHD/Tiingo и не эмпирическая квалификация их данных.

Контрактное renewal/смена entitlement пока fail-closed на expiry; многомесячный
процесс обновления прав, cross-host/PITR/key recovery требуют отдельной проверки.

Для next stage: применимая лицензия+finalinvoice<=50, authorized API проверка,
измерение финальности/коррекций, separate owner approvals на покупку/новую isolated
БД/first one-shot, backup deletion inventory и human inspection реальных UUID/UTC.
Расписание и production требуют собственного согласования. Ожидаемая инфраструктура
$10–30/month отдельно от$50vendor cap, пока оценка, не quote и не согласованная трата.
