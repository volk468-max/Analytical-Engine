# Alpha OS: ежедневный prospective shadow pipeline — Issue #27

**NOT RUNNING. RESEARCH ONLY.** Подготовлены код, локальные интеграционные проверки
и план запуска. Реальных prospective-прогнозов нет. Railway, действующие сервисы,
production PostgreSQL и расписания не изменялись. Реальных сделок нет.
Прогностическое преимущество этой работой не установлено: задача инфраструктурная.

## Зафиксированная база и новый вопрос

Вопрос: можно ли сохранять прогноз до результата, воспроизводимо и без изменения
истории, с последующей проверкой? Протокол сначала зафиксирован в architecture.md
первым коммитом ветки, до реализации. Зависимость — открытый Draft PR #26,
не main; его код и результаты не считаются внедрёнными.

| Источник | Зафиксированный head | Ограничение |
|---|---|---|
| [PR20](https://github.com/volk468-max/Analytical-Engine/pull/20) | `8e9aec99c7eee8b384e35a3bc1aa734f2d55800d` | Исторические зависимые наблюдения; не prospective доказательство |
| [PR24](https://github.com/volk468-max/Analytical-Engine/pull/24) | `51fb1d34ddb7a28e8bbc7b2361dcfc2107890f0b` | A/B/C EOD; Yahoo replay, PIT не подтверждён |
| [PR26](https://github.com/volk468-max/Analytical-Engine/pull/26) | `82eebbd95579c022040065f67e30c369d0999906` | Corporate-action qualification BLOCKED, validated calibrated P нет |

Существующие архивы не обновлялись и не переименовывались в live feed. Новая
независимая подсистема research/daily_shadow не подключена к production imports,
startup, ORM или scheduler. Старые датасеты и результаты сохранены.

## Определения и объём

После официального закрытия сессии t, реальной публикации и ingestion фиксируются
issued_at, decision_at, server recorded_at UTC, raw response/SHA256 и версия модели.
Прогноз относится к следующим N торговым сессиям t+1…t+N; t исключён. Порог равен
5/10/15% от **замороженного** close t, не от будущего локального максимума.
LOW_INTRADAY использует минимум low, EOD_CLOSE минимум close; это touch внутри
окна, не return на последней дате. Одна split-normalized price basis для low/anchor;
неподтверждённые действия или missing values блокируют результат. Dividends не
подмешиваются в price labels. Портфели используют только total-return EOD NAV,
с учётом dividend/cash и согласованной базы; intraday portfolio labels отсутствуют.

| Серии | Модели | Число в день | Dry-run |
|---|---|---:|---|
| SPY/QQQ/SOXX/AMD/NVDA/MU × 2 labels × 3 thresholds × 3 horizons | HIST, REGIME | 216 | BLOCKED, P=NULL |
| A/B/C × PORTFOLIO_EOD_CLOSE 10% / 60 sessions | HIST, REGIME | 6 | BLOCKED, P=NULL |
| Всего | 2 версии-заготовки, не qualified fits | 222 | 222 NULL, 0 live |

A: 1/3 каждой AMD/NVDA/MU. B: .20 каждой + .40 cash. C: inverse-vol по последним
252 total-return дням, минимум 200 валидных, границы 10–50%, сумма 1. Снимок —
гипотетические $100000, fractional units, фиксированные weights/units/cash, не
реальные позиции; в окне нет ребалансировки. Снимок должен иметь доступные на t
данные и замороженную lineage. Без квалифицированного NAV прогноз заблокирован.

HIST — Beta(1,1) historical frequency; REGIME — заранее фиксированный shrinkage20
к общей частоте для данной **акции, label и горизонта**, без смешивания целей.
Это интерфейс для будущих causal frozen artifacts, не новые validated модели:
default manifests qualified=false, supported_tasks=[]; calibrated P всегда NULL.
Обучающие labels обязаны полностью созреть к fit_cutoff <= issued_at. Новая версия
параллельна старой, одинаковый version с другими параметрами отвергается.

## Что реализовано и проверено

SQL 001 создаёт только alpha_shadow_v1 в специально названной отдельной БД
alpha_shadow_research. На Railway SQL **не выполнялся**. Локальный disposable
PostgreSQL16 использован для реальных транзакционных тестов. Runtime role не имеет
INSERT напрямую, UPDATE/DELETE/TRUNCATE; SECURITY DEFINER append-функция с закрытым
search_path атомарно пишет hash chain и typed projections. Конкурентные повторы
сериализуются, уникальный target/model/session не дублируется. Изменение payload
под тем же ключом — ошибка, не overwrite. Revision — отдельная correction.

Resolver — отдельная вызываемая функция, не активный job. Требует полного окна,
точного календаря, опубликованных значений, source hashes, action/basis gate;
сохраняет MAE и time-to-hit. Early hit не делает окно зрелым. SQL дополнительно
отвергает maturity до конца горизонта и публикацию раньше конца. Original anchor,
basis, expected horizon end и snapshot находятся в неизменяемом forecast payload.
IMMATURE/UNRESOLVED и новые outcome versions добавляются, не заменяют forecast.

| Проверка | Результат |
|---|---|
| Calendar/DST/holiday/early-close, availability/no-lookahead, labels, model/data gates, fixtures | 36 тестов PASS |
| Реальный PostgreSQL16: атомарность, 222-row batch, concurrent retry, privileges, corrections, versions, maturity | 17 тестов PASS |
| Раздельные серии/метрики, исключение synthetic, недостаточная мощность | 4 теста PASS |
| Всего subsystem | **57 PASS**, integration skips: 0 |
| Offline dry-run два раза | 222 records, одинаковые IDs, все P=NULL; без сети/БД |

Daily SQL-report показывает issuance, latency, diagnostics, backlog и health.
Single-series Python report отделяет data quality от model quality: только реальные
PROSPECTIVE FORECAST + mature outcomes допускаются к Brier/logloss/calibration.
Серии с разными targets/model versions не объединяются. Пока поддержка меньше
10 наблюдаемых 120-session blocks, model metrics NA. Этот консервативный operational
порог не доказывает power и не гарантирует независимость блоков. Есть circular
calendar-block bootstrap999 с L=60/120/180 и HAC support; CI условны на fitted model.
Калибровочные bins описательные; cross-version comparison пока ручная по отдельным
сериям, superiority testing и поправки на множественность требуют нового протокола.
Нельзя обещать efficacy через 90 дней. Минимум 12 месяцев — data-quality monitoring,
а объём для predictive power рассчитывается отдельно.

## Read-only обследование, ограничения и следующий этап

Platform inventory подтверждает наличие Data-collector-1.0, Analytical2.0 и Postgres
в skillful-reflection. Проверены только metadata и имена переменных, без значений
секретов. API collector, licensing, SQL permissions, connectivity к DB не проверены;
никакого запроса в production DB не было. Автоматически reuse не предлагается.
План: новая отдельная researchDB, минимальные права, staging/restore checks,
manual migration и live provider только после отдельного согласования.

Live adapter **не реализован без подтверждённого источника**: есть Provider contract
и synthetic fixture adapter. Daily runner вызываемый, нет активного entrypoint/cron.
Malformed provider payload может завершить job ошибкой; внешний supervision должен
это регистрировать. Строгую неизменяемость от superuser одна hash chain не даёт:
подпись/WORM/offsite anchor, backup/PITR и restore drill — обязательные launch gates,
в этой работе не развёрнуты. PostgreSQL18 Railway отдельно проверить на staging.
Роли и manifests сами по себе не заменяют независимый audit источников и моделей.

False Signal Anatomy выделено в следующий PR, как допускает Issue27. Сохранены
оригинальные SPY 2164 flags / 297 hits / 1867 nonhits; UP 55/864, DOWN 136/492,
MIXED 106/808 — перекрывающиеся дневные наблюдения, не независимые события.
Группы 0–2/2–5% loss, latehit11–20/21–60, rebound/rally и alert episodes сначала
preregister, затем out-of-time validation. Поздний hit не исправляет исходный FP10.

[Railway runbook](railway-runbook-ru.md) содержит конкретный checklist: isolated DB,
доступ, provider terms, cost cap, отдельный cron, notifications, retention/backups,
backfills, go-live. Плановый бюджет $10–30/месяц — оценка, не актуальная котировка
и не согласованная трата. Следующий этап — review и отдельное согласование этих
пунктов; до него статус **NOT RUNNING**, prospective rows отсутствуют.
