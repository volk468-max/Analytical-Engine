# Portfolio Risk Probability Engine v1 — Issue21

**RESEARCH ONLY. NO-GO для персональной калиброванной вероятности и торговли.**
Протокол опубликован первым; затем опубликован минимальный Draft PR22 с контрактом
и квалификацией входов, и только после этого реализованы офлайн-прототипы.

Вероятность TOUCH10/60 — падение замороженного no-trade total-return NAV на10%
от NAV момента прогноза в любой момент следующих60 торговых сессий. Дневные Close
дают только отдельный proxy, сумма несинхронных Low активов недопустима.
Допустимая просадка15% от flow-adjusted HWM — отдельный бюджет, не гарантия и
не вероятность TOUCH10/60. Личные позиции, валюта, NAV/HWM и вероятность **NA**.

| Фаза | Статус | Результат |
|---|---|---|
|0 протокол|DONE|Определения, frozen targets, Holm12, gates и сроки|
|1 контракт/registry/audit|DONE|12 кандидатов, все численные вклады unavailable|
|2 baseline/attribution|DONE synthetic / BLOCKED real|Joint-path frequency/ES и logit gate; нет обученной модели|
|3 эмпирическая валидация|BLOCKED|Нет реального портфеля/total-return/PIT истории, все метрики NA|
|4 policy|DONE mechanism / BLOCKED economics|Экспериментальные35/51/60, cumulative targets, confirmation/cooldown; не ledger|
|4 B&H/overlay/Ladder/full policy comparisons|NOT DONE/BLOCKED|Нет исполнений, cash/tax assumptions и portfolio history|
|4 combinations|NOT DONE|Нужна отдельная пререгистрация|
|5 shadow log|DONE offline mock/spec|Hash chain, отдельные labels; live инфраструктура НЕ запущена|

Синтетический пример:1 FAKE share100 + cash20 даёт NAV120, минимум107, proxy
TOUCH10=true (−10.8333%). Это НЕ позиции и НЕ вероятность пользователя.
Четыре вымышленных joint NAV path дают частоту0.5 и terminal ES5%=0.2;
значения проверяют арифметику, не прогнозную точность. Для HWM100/NAV90 остаток
15%-бюджета5 (5.56% текущегоNAV), хотя событие падения ещё10% — другой вопрос.
Реальные P/CI, Brier/logloss/calibration/lift/lead-time/CAGR и иные экономические
метрики не рассчитаны и не заменены нулями.

PR8/17/18/20 остаются unmerged. Их отрицательные результаты0/4,0/27,0/162,0/33
сохранены, simple regime baseline PR20 сильнее сложной MINIMAL. История2021–2026
не untouched holdout. Источники PR20 price-only и не certified PIT: не total-return
история пользовательского портфеля. Нельзя добавлять произвольные новости в процентах.
Реестр разделяет official/opinion/rumour, canonical event/near-duplicate fingerprint,
группы корреляций, release/ingest и revision vintages. Без квалификации вклад NA.

Нужно предоставить/квалифицировать snapshot shares/cash/base currency/FX, action
и dividend ex/pay evidence, синхронные marks, delistings/flows/HWM, assumptions
fees/slippage/tax, архивы revisions/news/market expectations. Исследование rate
surprise требует contemporaneous futures path, а не правила «Fed hikes => risk+».
Все пороги защиты экспериментальные;15% не гарантируется. Norgate/Windows отложен,
покупок, production, брокера, реальных сделок, merge/deploy нет.

[Архитектура и ограничения](architecture.md), [протокол](protocol.md),
[источники](data-qualification.md), [контракт](portfolio-schema.json),
[реестр](factor-registry.json), [синтетическое демо](demo.json).
