# Каталог исследований

Проверено 13 существующих PR; каталог включает 12 исследований/аудитов (#2–13) и 1 инженерное предложение (#1). Проверка #14: 404 на 2026-11-04; номер может быть использован позднее.

| ID | PR / название | Исходная база | Карточка |
|---|---|---|---|
| R01-v1 | [#1: Fix causal support/resistance and add independent tactical risk overlay](https://github.com/volk468-max/Analytical-Engine/pull/1) | `main` | [читать](research/R01-v1.md) |
| R02-v1 | [#2: Add historical simulator with explicit point-in-time data limits](https://github.com/volk468-max/Analytical-Engine/pull/2) | `fix/risk-engine-v2` | [читать](research/R02-v1.md) |
| R03-v1 | [#3: Diagnose missing TRIM signals and restoration opportunity costs](https://github.com/volk468-max/Analytical-Engine/pull/3) | `feature/risk-backtest-v1` | [читать](research/R03-v1.md) |
| R04-v1 | [#4: Research AMD Core + Tactical Ladder over 2021–2026](https://github.com/volk468-max/Analytical-Engine/pull/4) | `feature/risk-backtest-v1` | [читать](research/R04-v1.md) |
| R05-v1 | [#5: Research: Risk Signal Engine v3 with explainable signals and walk-forward evaluation](https://github.com/volk468-max/Analytical-Engine/pull/5) | `research/risk-signal-diagnostics` | [читать](research/R05-v1.md) |
| R06-v1 | [#6: Research: economic backtest of frozen Risk Signal v3 with cash-limited recovery](https://github.com/volk468-max/Analytical-Engine/pull/6) | `research/risk-signal-engine-v3` | [читать](research/R06-v1.md) |
| R07-v1 | [#7: Research: Risk Forecast v1 with purged walk-forward probabilities and dependent-window validation](https://github.com/volk468-max/Analytical-Engine/pull/7) | `research/risk-signal-v3-economic-backtest` | [читать](research/R07-v1.md) |
| R08-v1 | [#8: Research: Historical Drawdown Anatomy v1 with nested-free events and causal hypothesis validation](https://github.com/volk468-max/Analytical-Engine/pull/8) | `research/risk-forecast-v1` | [читать](research/R08-v1.md) |
| R09-v1 | [#9: October 2026 Risk Failure Audit v2](https://github.com/volk468-max/Analytical-Engine/pull/9) | `main` | [читать](research/R09-v1.md) |
| R10-v1 | [#10: Research: Fixed 5% Buyback Experiment v1](https://github.com/volk468-max/Analytical-Engine/pull/10) | `main` | [читать](research/R10-v1.md) |
| R11-v1 | [#11: Research: Historical SELL / BUY −5% Backtest v1](https://github.com/volk468-max/Analytical-Engine/pull/11) | `main` | [читать](research/R11-v1.md) |
| R12-v1 | [#12: Research: Signal Predictive Accuracy Audit v1](https://github.com/volk468-max/Analytical-Engine/pull/12) | `main` | [читать](research/R12-v1.md) |
| R13-v1 | [#13: Research: Breadth Data Audit & Prototype v1](https://github.com/volk468-max/Analytical-Engine/pull/13) | `main` | [читать](research/R13-v1.md) |

Канонические поля: [research.json](research.json). Исходные PR descriptions сохранены без пользовательских профилей в sources/. Report links закреплены на commit SHA; branch names не задают версию. Нельзя считать PR1–8 внедрёнными только потому, что они не Draft.

Новый результат = новая запись Rxx-v2 и новая карточка; старые карточки, записи и source snapshots append-only. Изменения статуса ведутся отдельно в status.json. Исправление старой ошибки публикуется новой версией с объяснением и ссылкой на прежнюю.

## Дополнение 2026-11-05

R14/R15 добавлены отдельно; предыдущие 13 карточек и записи неизменны.

| ID | Источник | Карточка |
|---|---|---|
| R14-v1 | [PR14](https://github.com/volk468-max/Analytical-Engine/pull/14) | [карточка](research/R14-v1.md) |
| R15-v1 | [PR15](https://github.com/volk468-max/Analytical-Engine/pull/15) | [карточка](research/R15-v1.md) |
| Q001-v1 | Текущий отдельный Draft PR, SHA из Git history | [проект](research/Q001-v1.md) |

Начальный блок каталога выше — сохранённый checkpoint 2026-11-04; актуальные статусы в PROJECT_STATUS. Q001 зарегистрирован в research.json/draft_work до публикации, чтобы не изобретать self-referential SHA.

## Q002 и R16,2026-11-05

| ID | Источник | Карточка |
|---|---|---|
| R16-v1 | [PR16](https://github.com/volk468-max/Analytical-Engine/pull/16) | [карточка](research/R16-v1.md) |
| Q002-v1 | Текущий отдельный Draft PR; protocol b1d43275bb10bc69516e868b625377ceea4119b6 | [Risk Forecast validation](research/Q002-v1.md) |

Q001 остаётся в истории как технический проект, не completed real vendor qualification. Q002 новая independent implementation evaluation на reused history, не переписывает результаты R07/R08/R11/R12.

## Ensemble Risk Forecast v1 / Q003

| ID | Источник | Карточка |
|---|---|---|
| R17-v1 | [PR17](https://github.com/volk468-max/Analytical-Engine/pull/17) | [карточка](research/R17-v1.md) |
| Q003-v1 | Отдельный текущий Draft PR; source SHA из Git history | [ансамбли](research/Q003-v1.md) |

Новый вопрос об ансамблях; прежние записи/карточки сохранены. Q002 теперь опубликован
как PR17, его старый draft_work checkpoint оставлен в истории.

## Issue19 / Q004 — dedicated market precursor research

| ID | Источник | Карточка |
|---|---|---|
| R18-v1 | [PR18](https://github.com/volk468-max/Analytical-Engine/pull/18) | [карточка](research/R18-v1.md) |
| Q004-v1 | [Issue19](https://github.com/volk468-max/Analytical-Engine/issues/19), текущий отдельный Draft PR | [market precursors](research/Q004-v1.md) |

Новый dedicated market catalogue/forecast вопрос; R08/R17/R18 сохранены.

## Q005 / Issue21

R20-v1 [PR20](https://github.com/volk468-max/Analytical-Engine/pull/20): [карточка](research/R20-v1.md).
Q005-v1: [Portfolio probability research](research/Q005-v1.md). Предыдущие карточки
сохранены; новый portfolio target не заменяет market/stock negative findings.
