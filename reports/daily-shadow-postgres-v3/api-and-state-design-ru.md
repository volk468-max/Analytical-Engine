# API и состояния — отдельная исследовательская реализация v3

Не импортируется production entrypoint, scheduler или Railway collector. Новая
реализация `research/daily_shadow_v3`; manual SQL003 только в БД
`alpha_shadow_research`. Никакие существующие validated-гейты не ослаблены.
`interfaces.EODProvider`/`Transport` — нейтральные контракты, EODHD первая реализация.
Tiingo адаптер не активирован: контрактное хранение для постоянного audit не прошло.

## Mapping

| Данные | EODHD путь/поле | Внутренняя трактовка |
|---|---|---|
| Инструменты | `/api/exchange-symbol-list/US`, Code/Currency | Только SPY.US, QQQ.US, SOXX.US, AMD.US, NVDA.US, MU.US; currency USD требуется из ответа |
| Бары | `/api/eod/{symbol.US}`, date/open/high/low/close/volume/adjusted_close | date — session, OHLC raw as traded, volume split-adjusted, adjusted_close total-return; не один общий basis |
| Splits | `/api/splits/{symbol.US}`, date/split | new/old, включая reverse; только события <=as-of |
| Dividends | `/api/div/{symbol.US}`, date/value/unadjustedValue/currency/paymentDate | Ex-date, current-share value отдельно от исторической cash amount, paymentDate nullable |
| Метаданные | Fixed source URI без token, SHA256 bytes, фактический retrieval UTC | Первый и исправленный ответ — разные vintages; true publication NULL |

400 календарных дней для SMA200/momentum20; неполная история/дырки/duplicate session/
неUSD/пустой feed/несовпавшая последняя сессия/NaN/неверные OHLC отвергаются. Наличие
endpoint и US mapping ещё не доказывает доступность именно этих шести symbol.
HTTP ограничен фиксированным HTTPS host,20s,8MiB/response,16MiB/bundle, безredirect;
исключения очищаются от URL/token. Автоматических неограниченных retry нет:
после ошибки оператор повторяет идемпотентный one-shot. Credential читается из
`EODHD_API_TOKEN` только после legal gate. Не читаются production DATABASE_URL/ключи.

События price drawdown: от frozen anchor следующего окна из N=10/20/60 US sessions,
без anchor session; отдельно minimum daily close и minimum daily low, thresholds
5/10/15%. Split-only normalization использует события между anchor и observation;
дивиденды не превращаются в total-return correction price event. Prefix features
видят только splits<=decision session. Anchors/actions/raw bytes живут в private
plane, immutable journal содержит только разрешённые reference/hash/forecast fields.
Для A/B/C same-day self-financing NAV ещё не квалифицирован: всё NULL.

## Состояния и полномочия

| Условия | run_mode / status | Вероятность |
|---|---|---|
| Нет применимого права, доступа, as-of input или модели | соответствующий run_mode / STATUS_BLOCKED | NULL |
| Искусственные данные и synthetic-only permit | SYNTHETIC / RESEARCH_FORECAST | Число для проверки кода; не настоящее наблюдение |
| Реальный источник, LIVE permit, reviewed data, frozen model до issue, отдельное разрешение на первый запуск | RESEARCH_FORECAST / RESEARCH_FORECAST | Некалиброванная research probability |
| VALIDATED/TRADING/BACKFILL | Нет маршрута в v3 | Запрещены |

`status` описывает пригодность вычисления, `run_mode` происхождение. SYNTHETIC
всегда отделяется в метриках. Отдельные фиксированные MODEL_NOT_VALIDATED и
TRAINING_REPLAY_NOT_PIT сохраняются даже при реальном forward issue. Старые222
artifacts остаются qualified=false/calibrated=false; training history не получила
новую PIT квалификацию благодаря новому feed. HIST Beta(1,1), REGIME shrinkage20
из frozen count banks; baseline всегда парный. Calibrated probability всегда NULL.

App role не может зарегистрировать LIVE permit: это отдельная роль
`alpha_shadow_legal_reviewer` без LOGIN. App имеет только execute на ограниченные
SECURITY DEFINER функции с фиксированным search_path и reader доступ к safe metadata;
нет direct INSERT/UPDATE/DELETE/DDL, чтения private plane или права объявить purge
backups завершённым. Модель/hash/series/полный calendar horizon/time gating проверяют
и Python, и SQL. Реальная модель должна быть заранее зарегистрирована в DB; модель
созданная после issue недопустима. Real issuance timestamp — фактический UTC после
collection; fixture clock нельзя передать в реальный run. SQL не разрешает backdate
старше10min, future issue, fixture input/model в реальном run.

20:30 America/New_York требует same local session date, exchange calendar, official
close и independently verified provider finalization. Зимний UTC следующий день
корректен; UTC дата не заменяет local session. Без finalization evidence — BLOCKED.
Не обещается SLA публикации или исполнение по тому же close.

## Immutable audit и законное удаление

`alpha_research_v3`: append-only contracts/lifecycle/journal/forecasts/outcomes/calendar;
собственная SHA256 chain/advisory transaction lock. Idempotent retry не переписывает
anchor; исправление источника записывает CORRECTION к тому же forecast и новому
payload; correction outcome с supersedes_id — новая запись того же события.

`alpha_licensed_v3`: отдельный **удаляемый** encrypted payload vault. Fernet key
подаётся оператором отдельно, не хранится в БД/Git. Original bytes/action lineage/
anchors только там. Доступ блокируется по TTL/expiry/offboard. OFFBOARD_REQUESTED
удаляет active payloads, но **не доказывает удаление WAL, snapshots, logs, DR и backups**.
PURGE_CONFIRMED требует отдельной legal-reviewer receipt после проверки всех копий.
Restored backup не является источником актуального права: нужен fresh external
active-contract registry и разрешение, иначе restore/use запрещены. Шифрование или
hash не считаются освобождением от ToS. Реальное backup/storage внедрение не делалось.

В неизменяемой части допускаются только отдельно разрешённые навсегда безопасные
forecast/hash/metadata. Если этого права нет, отказ от источника, а не обход удаления
через hash или derived series. WORM для licensed raw несовместим с требованием
удалить — не включать его без явного подходящего договора. Нынешний staging backup
содержит лишь наши искусственные значения и не доказывает vendor compliance.

Outcomes созревают только после полного N; early touch не ускоряет maturity.
Resolver требует original anchor, полные бары, actions reviewed и фактическую
доступность каждого будущего бара. Метрики объединяют только genuine same-date
HIST/REGIME одного события и одинаковый outcome, исключают synthetic/blocked и
параллельные версии. Brier/logloss сохраняются как descriptive research; независимые
события/CI/мощность не выдумываются при пустом prospective наборе. Перекрывающиеся
окна, 6 коррелированных инструментов и 222серии не независимые испытания.

## Открытые эксплуатационные вопросы

Реальная политика renewal/смены entitlement ещё не принята: manifest immutable,
`access_until` истёк или offboard — дальнейшее чтение/issuance/резолв блокируются.
Нельзя молча продлить срок по ожиданию автопродления. До реального многомесячного
наблюдения нужен проверенный append-only процесс нового review/entitlement и
переноса допустимых payload refs; сейчас такого контрактного renewal доказательства
нет. Это ограничение готовности к запуску, не разрешение оставлять просроченные данные.
Cross-host/PITR/key-loss recovery и реальное выполнение vendor purge не сертифицированы
локальным синтетическим dump/restore. Реальный positive live issuance намеренно не
выполнялся: для него нет ни подтверждённой лицензии, ни разрешения владельца.
