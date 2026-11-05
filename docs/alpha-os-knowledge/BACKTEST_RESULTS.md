# Исторические результаты

Все значения ниже — опубликованные модельные результаты при допущениях соответствующих источников, не реальные сделки.

| Источник / период | Эксперимент | Результат |
|---|---|---|
| R02 / Sep–Oct22 2026 | Limited overlay, 11 names | 403 HOLD, 4 REVIEW, 0 TRIM; full v1/v2 сравнения недоступны |
| R04 / 2021–Oct22 2026 | AMD ladder, $100000 | B&H 550887.46 vs ladder 494460.40 USD; MaxDD -65.45 vs -63.00% |
| R06 / 2023–Oct22 2026 | Independent $100000 stock accounts, HOLD3+CRITICAL | Delta NAV AMD -206016.49, NVDA -485737.42, MU -516095.63 USD |
| R09 / Sep1–Nov2 2026 | Continuous 11-sleeve $100000 | B&H 90888.56, old trim5 90701.12, trim10 90513.69 USD |
| R10 / same short window | Independent buyback lots | fixed5 91568.52, fixed10 92248.48 USD; relative improvement при absolute loss |
| R11 / 2021–Nov2 2026 | COMPARABLE10 $100000 | B&H 631370.19, fixed5 283298.73, fixed10 133841.05 USD |

Источники и SHA: [R02](research/R02-v1.md), [R04](research/R04-v1.md), [R06](research/R06-v1.md), [R09](research/R09-v1.md), [R10](research/R10-v1.md), [R11](research/R11-v1.md). Короткий положительный relative результат R10 не заменяет отрицательный длинный результат R11 и не опровергается им как арифметическая ошибка: отличаются периоды и continuous state. Сохранять оба.

R07 forecasting: 0/18 primary incremental tests; R08 anatomy: 0/4 testable hypotheses; R12 sector precision SOX 42.86% и незначимый any-down5 uplift. Это predictive metrics, не returns. R13 эффективность не тестировал.

Нельзя смешивать reset/inherited accounts, realized/open marks, gross proceeds/profit, stock/portfolio capital, price-only/total return, same-bar ambiguity/confirmed fills. Общие ограничения: retrospective provider vintages, repeated history, survivor bias, отсутствующая реальная execution/PIT evidence. Новые расчёты добавлять с новым ID и sources; старые результаты не переписывать.

## Q002 отдельная диагностическая симуляция

2026-11-05: сохранены все прежние таблицы. Для TOUCH10/20,p>=.5,delay1 mean mark per independently reset1share lot /sale-open notional: AMD-5.8553%(21lots),NVDA-4.3458%(15),MU-8.5741%(13). Это не portfolio return, не независимые market trials и не total return; все9tasks/delays отдельно. [Q002](research/Q002-v1.md).

## Q003 Ensemble (дополнение)

0/162primary contrasts; TOUCH10/20 Brier B0.228306/C0.236401 vs QQQ0.226822.
3+голосов48.37%, same-date baseline44.55%, uplift95%CI[-0.34,+9.35]pp.
RESEARCH ONLY, без подтверждённого экономического превосходства. [Отчёт](../../reports/ensemble-risk-forecast-v1/report-ru.md).

## Q004 / Issue19 — forecast evaluation, не trading backtest

0/33primary TOUCH5/10 contrasts. SPY/QQQ/SOXX MINIMAL Brier0.089373/0.132410/0.208918
противREGIME0.084913/0.127060/0.207483. Дополнительная прогностическая сила не
установлена. NVDA secondary vspuremarket не лучше простойREGIME. No NAV/B&H study.
[Отчёт](../../reports/market-drawdown-precursors-v1/executive-summary-ru.md).
