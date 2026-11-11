# Source-license decision memo — 2026-11-11

**NO-GO provider для первого фактического запуска.** EODHD — условный приоритет,
Tiingo — условный резерв, не подтверждённая лицензия. Подписок/аккаунтов не покупали,
trial/demo data API не вызывали. Public legal/docs проверены отдельно от coverage API.
Статус персонального/корпоративного оператора UNKNOWN, ответов провайдеров нет;
письма не отправлялись. Prepared clarification questions ниже, ответ не выдумывался.

## EODHD: конфликт нельзя переносить в отчёт как непроверенный текущий факт

[Storage FAQ](https://eodhd.com/help/storage): короткая цитата: “may be kept and used for your private, non-commercial purposes after cancellation or downgrade”.
[Terms](https://eodhd.com/financial-apis/terms-conditions) — governing document;
короткая цитата из FAQ: “the only governing document”. В прямом HTML полученном
11.11.2026 (HTTP200, UTC/SHA256 в provider-evidence.json) **не найден** прежний
one-month deletion clause. Это не доказательство того, что его никогда не было,
и не реконструкция редакции, указанной владельцем. Дату изменения/преимущество
версий/индивидуальный договор проверить не удалось. FAQ также сообщает, что
персональные отдельные licence letters не выдаются. Исторический конфликт нельзя
объявить разрешённым индивидуальным ответом: такого ответа нет.

[Personal-use FAQ](https://eodhd.com/help/personal-use) ограничивает личный план
одним человеком, не бизнесом; публикацию даже derived outputs следует отдельно
согласовывать. Cloud PostgreSQL/backups, фактический оператор и область доступа
Alpha OS требуют зафиксированной применимой редакции и подтверждения условий.
Публичный Git получает только код/фикстуры/метаданные legal review, не vendor data.

## Tiingo: Power не даёт исключение для постоянного raw audit

[ToS, updated05.11.2026](https://www.tiingo.com/tos/), §1.6(b): “delete all Tiingo Data from every system”; §1.6: “Those plans start at $250 per month”. Starter/trial не разрешают durable storage даже derived outputs. Paid Data нужно удалять при окончании плана, включая backups/logs/DR. Power не получает retention exception. §1.6(c) ограничивает reconstructible derivatives, anchored return series и cross-provider validation; даже hashes не автоматически свободны от ограничений. Нельзя считать encryption или hash заменой удаления. §1.7(c) допускает внутренние non-generative predictive models при активном Power и соблюдении §1.6; это не право сохранять raw навсегда. Для требуемого долгосрочного audit резерв **NO-GO при$50** без отдельного подходящего договора; неизвестную цену exception нельзя записать как$30/$50.

## Сравнение тарифов и обязательств

| Источник | Публичная месячная цена | История/квота по документации | Главный gate |
|---|---:|---|---|
| [EODHD EOD All World](https://eodhd.com/pricing) |$19.99 personal, не annual-equivalent$16.58|30+лет в зависимости от symbol;100000calls/day,1000requests/min; splits/dividends включены|Применимая редакция retention/cloud/use и actual API verification |
| [Tiingo Power](https://www.tiingo.com/about/pricing) |$30 individual; $50 internal commercial|30+лет advertised,10000requests/hour,100000/day,40GB/month|Retaining raw afterexpiry exception не для Power; классификация оператора |
| [Massive Stocks Starter](https://massive.com/stocks) |$29 individual|5лет; unlimited APIcalls, corporate actions; delayed feeds|[Market Data Terms](https://massive.com/legal/market-data-terms-of-service) §8 ограничивает use/delete послеlicense; backup grace<=90days безrestore/use, source-specific rules; ML rights отдельно |
| [Twelve Data Grow](https://twelvedata.com/pricing) |Не подтверждена live quote; pricing fetch timeout|Владельцем отмечен как over-budget|Не квалифицирован и не выбран на основании неподтверждённой цены |

Общий vendor invoice = base + применимые налоги/fees/нужные add-ons. Billing country,
tax/exchange fees и checkout quote UNKNOWN; покупка не открывалась. $50 Tiingo
commercial уже не оставляет места налогам. Infrastructure отдельно: прежняя оценка
$10–30/month не входит в$50vendor cap и также не является согласованной тратой.

Для всех шести SPY,QQQ,SOXX,AMD,NVDA,MU есть строгий planned mapping, **actual licensed
API responses/coverage/recent2026bars не проверены**: authorizedcredentials отсутствуют.
Документация о US equities/ETFs не является результатом6успешных запросов. Нет
утверждения о verified PIT history, actions или raw retention по trial.

## Техническая пригодность и время

[EOD docs](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes): OHLC
raw/as-traded, adjusted_close содержит splits+dividends, volume split-adjusted.
Нельзя домножать low на adjusted_close/close и называть это split-only. История
adjusted_close пересчитывается. US update advertised within15min, broader2–3h;
это не истинное publication timestamp/финальность конкретного ответа.
[Corporate-actions docs](https://eodhd.com/financial-apis/api-splits-dividends): split
new/old, value в современных shares, unadjustedValue историческая выплата. Адаптер
сохраняет basis явно; split-only normalization требует полного action history.

[Tiingo EOD docs](https://www.tiingo.com/documentation/end-of-day): raw и adjusted
OHLC различны, adjustments включают dividend+split; типичное наличие17:30ET,
коррекции до20:00ET. Candidate20:30America/New_York — консервативный gate только
после verification поведения provider; не выдуманное время публикации и не cron.
Дата bar не приравнивается к моменту доступности. Revision сохраняется отдельно.

## Что именно нужно получить до выбора/покупки

EODHD: письменное/официально применимое разъяснение, какая dated Terms редакция
управляет Alpha OS, как согласуется прежний deletion clause с FAQ, разрешены ли
private cloud PostgreSQL, encrypted/offsite backups и indefinite audit послеcancel,
кто может видеть outputs и сколько стоит фактический use case с налогами.
Публичный FAQ полезен, но не выдаётся за индивидуальный ответ.

Tiingo: подтвердить фактическую классификацию и возможность нужного exception в
рамках$50; текущий ToS указывает$250+ и исключает Power. Без него fallback для
постоянного raw audit не подходит. Нельзя сохранить проверенный по Tiingo другой
dataset или reconstructible derived series под видом свободного audit.

Massive: проверить exact dataset/source permissions, postcancel history entitlement,
cloud processor/ML use и retention;5лет не заменяют прежний2000–2026archive.
Приоритет владельца EODHD/Tiingo не изменён выбором третьего источника.

Итог: **conditional EODHD first; Tiingo fallback только при совместимом договоре;
NO-GO provider сегодня**. Подготовлены adapter+RESEARCH_FORECAST и synthetic staging;
это не разрешение купить, собирать реальные данные или выдать реальный прогноз.
