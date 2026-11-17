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

## Q006

[R22](research/R22-v1.md); [EOD portfolios Q006](research/Q006-v1.md). Prior research preserved.

## Q007

[R24](research/R24-v1.md); [Q007 calibration gate](research/Q007-v1.md). Prior cards preserved.

## Q007-v2

[Preliminary real calibration and continuous ledger](research/Q007-v2.md), supersedes
limited Q007-v1 milestone; original card/source/results preserved. Same Draft PR26,
not a new PR. New owner evidence/authorization is the reason for further research.

## Q008

[R26 source qualification](research/R26-v1.md); [Q008 daily shadow infrastructure](research/Q008-v1.md). Earlier research preserved.

## Q008-v2

[R26-v2 preliminary negative findings](research/R26-v2.md); [Q008-v2 PostgreSQL18
preparation](research/Q008-v2.md). Old source cards and PR26 parent outputs preserved.

## Q008-v3

[Separate research forecast/source-licence milestone](research/Q008-v3.md). Existing
Draft PR28, EODHD conditional primary, no qualified provider or real launch. Historical
Q008/R26 records and negative results preserved.

## Q008-v4

[Daily EODHD worker / blocked Railway launch](research/Q008-v4.md). New owner scope
allows isolated deployment; tool approval rejected, NOT RUNNING. Old cards retained.

## Q008-v5

[Daily worker diagnostics/readiness fix](research/Q008-v5.md): new dependent fix PR,
actual old application log observations, direct SQL/new execution UNVERIFIED.


## 2026-11-17 — Q009 / daily VOL10 stocks

Owner explicitly requests implementation/connection and preservation in Notion.
Universe ANET/NVDA/AMD/CRWD/NBIS/GOOG/GS/META/MU/LRCX; horizons10/30.
New daily-refit raw VOL,120series; not calibrated annual historical estimator.
Pinned research base [PR29](https://github.com/volk468-max/Analytical-Engine/pull/29)
@ fe834c77cbadf4baa3eab68135cbdee1ecdad1f0; isolated Railway configuration read
confirmed this deployed source2026-11-17, deploymentad829a06-9089-40b5-99f0-bd8056561c74 SUCCESS.
Implementation prepared with additive006, independent manifest, strict complete
training labels/support/asof, same-session publishing, NBIS only since2024-10-21.
Local PostgreSQL17.11:210tests PASS,0skips (includes22new VOL tests). This is
code/SQL evidence, not real VOL issuance. Final integration/live acceptance still
pending deployment and actual source/SQL checks. Old research records untouched.
[Q009](research/Q009-v1.md).


## 2026-11-17 — Q009-v2 / code verified, platform deployment rejected

[PR34](https://github.com/volk468-max/Analytical-Engine/pull/34) calculation SHA
`84fcc8dff22d08ce186eaf0d8753a9700b428e15`: final GitHub
[daily pipeline](https://github.com/volk468-max/Analytical-Engine/actions/runs/44060183233)
and [online knowledge](https://github.com/volk468-max/Analytical-Engine/actions/runs/44060183208)
completed SUCCESS, including PostgreSQL16/18, full parent regression/replay and restore.
Local211distinct pipeline tests+9knowledge, four-schema synthetic restore pass.

Owner repeated connection request after platform rejection. Both accept-deploy
attempts returned: Cancelled — the user did not approve this action. No changes
were made. This is a platform result, not an assertion owner intentionally refused.
No bypass attempted. Patch0bc08fd0-33af-4f97-b3ee-03ca1c0a73ea remains STAGED,
worker-only. Current live source stays fe834c77cbadf4baa3eab68135cbdee1ecdad1f0.
VOL not enabled; migration006/live10-symbol preflight/realVOL issuance NOT RUN.
Notion Alpha OS received decisions, exact universe, implementation and this
blocked operational checkpoint. No production/trading/merge/purchases.

Next: approve/apply existing research patch, observe terminal deploy SUCCESS,
bootstrap/migration006 and actual10-symbol preflight, direct read-only SQL, cron.
Do not call code/CI/staging a completed connection; no historical backfill.


## 2026-11-17 — Q009-v3 / deployment and actual preflight

Owner applied the research patch manually. Source84fcc8dff22d08ce186eaf0d8753a9700b428e15
deployment8b87b0b1-8d8a-484e-97f3-b96963756390 reached SUCCESS. Bootstrap READY/exit0
run d4a3036b-175b-49b6-9974-bc3c80846e4a confirms migration/setup completed; no
independent migration-catalog SQL yet. Existing cron unchanged, no staged changes.

An authorised worker-only restart ran real preflight89344101-1cdd-4ce5-b7f7-e3676fcdd0c8:
63HTTP200/0failures,10stock checks completed108ready/12blocked. All12NBIS targets
blocked INSUFFICIENT_MATURE_TRAINING_SUPPORT; other9names12/12ready each. No
actual VOL forecast published: daytime gate BEFORE_OFFICIAL_CLOSE. This is not
prospective forecast acceptance/model validation. Old forecast total648 is old
HIST/REGIME application SQL-log evidence, not VOL.

Run ended PARTIAL_FAILURE/exit2 because inspect_vol selected repeatable-read after
Store.connect had already queried database identity in the same transaction. New
three-line fix commits the setup transaction before the read-only snapshot,
retaining the restricted session role. Real disposable PostgreSQL17 regression
plus6runtime tests PASS7/7. No estimator/targets/threshold/model changes.

[PR34](https://github.com/volk468-max/Analytical-Engine/pull/34) continues; isolated
research fix deployment and repeat audit/preflight are next, already within owner
authorisation. No production/trading/merge/purchases. Project list-services read
confirms only one environment, research; no other environment could receive a
service source update. After acceptance verify first real next valid cron issue.


## 2026-11-17 — Q009-v4 / operational preflight accepted, first issue pending

Actual deployed/pinned source `a2855b5107eb02946cb6e7e1dc41ab69db61ecfb`,
deploymentd20392cf-7044-4ac5-8264-d050168bbefd SUCCESS. No pending patch.
After minimal audit-transaction fix, actual run8688b6b2-7b50-465b-93d6-b04f67ff93a7
ended SUCCESS/exit0 at2026-11-17T10:19:12UTC:108/120targets ready,12NBIS blocked
INSUFFICIENT_MATURE_TRAINING_SUPPORT; other9stocks12/12ready.63HTTP200/0failures.
Read-only SQL audit inside worker reports0VOLrecords/0numeric/NULLfirst/lastissue,
DUPLICATES=0. These are SQL results read from application logs, not an independent
SQL session. BEFORE_OFFICIAL_CLOSE prevented a daytime/backdated forecast.
[Sanitised evidence](../../reports/vol-daily-v1/operational-acceptance.json).

Cron0 2 * * 2-6 remains05:00Moscow Tue–Sat. First real VOL issue expected2026-11-18
05:00Moscow (USsession2026-11-17); pending, not claimed as issued. One-time
automation for05:30Moscow will audit actual manifest/timestamps/duplicates/blocks
and save in Notion; IDAutomation_a3be3fb079a881918909c1cd592c1d7c.
Notion Alpha OS history saved including old failures and successful resolution.
Next: first prospective issuance acceptance, then mature10/30session scoring;
NBIS remains explicitly blocked until protocol support is sufficient.
No production/trading/broker/merge/new purchases. PR34 remains Draft/unmerged.


## 2026-11-17 — Q010 / daily Risk Forecast

Owner requests daily Risk Forecast for same10stocks/10&30sessions as VOL. Chosen
existing technical_combined from source366f8cd00e8c228d4796d0abbe9997f717a3b6ad:
exact empirical Beta1/1+shrink20 cell model, drawdown20/RV20/belowSMA50/WilderRSI14.
Not technical_plus_v3; no fabricated v3/VIX/SOX. Dailyrefit/30session/CloseTOUCH
adaptation explicitly versioned. LOW_SUPPORT numerical backoff is labelled, not
validated/calibrated. NBIS since2024-10-21 only; global support may block.

[Issue35](https://github.com/volk468-max/Analytical-Engine/issues/35), newbranch
feature/risk-forecast-daily-ten-stocks from VOL metadata headf4042bf070c9d8ef1640d82bf72b5117a25484f1;
actual research deployed source remainsa2855b5107eb02946cb6e7e1dc41ab69db61ecfb.
Protocol frozen before real source fits.122local tests on PostgreSQL17 PASS,0skips,
including newRF/SQL007 and VOL/runtime regression; original formula/cells parity
confirmed against archived exact source. Production/trading/merge/purchases absent.
Implementation prepared; NOT YET DEPLOYED. Actual10-stock preflight/SQLaudit and
first future valid-window issuance remain to verify. [Q010](research/Q010-v1.md).
