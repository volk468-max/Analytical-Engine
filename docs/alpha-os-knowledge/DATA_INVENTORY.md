# Источники и качество данных

| Набор | Покрытие / источник | Качество и границы |
|---|---|---|
| Initial price/VIX | 11 stocks, 10053 bars / 983 VIX до 2026-10-22; R02 | Limited replay; 44 full comparisons UNAVAILABLE |
| v3/Forecast | AMD/NVDA/MU + QQQ/SOX/VIX, warmup 2020, evaluation 2021–2026-10-22; R05/R07 | Next-midnight publication assumption; не original vintage |
| Anatomy | 18 names + FRED DGS10; R08 | EPS/guidance/P/E/news vintages отсутствуют; yield lag assumed |
| October completion | 11 stocks + market/sector/macros, 44 sessions Sep1–Nov2; R09 | Treasury 42, IG/HY 43 observations; gaps не заполнять |
| Long buyback | 1465 sessions до Nov2, 134 activations; R11 | NBIS с 2024-10-21; split units и dividend receivables; survivor bias |
| Breadth proxy | 22656 HLC, 14 instruments, 2930 rows; R13 | Все historical_backtest_eligible=False; нет PIT index membership |
| Production payloads/holdings/orders | R09/R12/R13 | UNKNOWN; отсутствие записи не HOLD и не нулевая позиция |

Источники каждой строки: соответствующие [карточки и pinned отчёты](RESEARCH_INDEX.md). Dataset hashes/retrieval timestamps находятся в оригинальных manifests отчётов, а не заменены хешем PR. Единой действующей production data version восстановить нельзя.

Рекомендация: до нового backtest фиксировать dataset manifest, provider URL, retrieval/available/effective timestamps, adjustment basis, missing sessions, licence, SHA256. SHA256 данных не является Git commit SHA. Условия поставщиков меняются; исторические цены и licensing candidates в R13 не являются разрешением купить или передать raw данные. В knowledge не копировать credentials, персональные позиции, payloads или лицензионно ограниченные raw exports.

## 2026-11-05: последующие источники

R15 добавил Kaggle survivor-selected2018 archive: acquired candidate coverage около26%, а не verified PIT. Q001 Norgate exports отсутствуют; test bundle synthetic. Ни AssetID rows, ни цены поставщика не копируются в knowledge/public GitHub. Документационные HTTP receipts — sources.json проекта, не real market dataset.
