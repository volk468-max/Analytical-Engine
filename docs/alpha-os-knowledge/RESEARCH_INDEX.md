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


## 2026-11-17 — Q010-v2 / Risk Forecast operational preflight PASS

Actual pinned source261cf92ef3466934a2c3a9f4a56603f5fa00c925, deployment
4381f0a4-3236-4161-a8f3-7d716c9b132b SUCCESS. Bootstrap READY/exit0 includes007.
Real runc78f6dbd-e55d-40c6-8d0e-a78c44ffad9a completedSUCCESS/exit0 at10:40:44UTC,
63HTTP200/0failures, partial_phases empty. Same10stock universe:9stocks12targets
ready each,12NBIS blocked INSUFFICIENT_MATURE_TRAINING_SUPPORT. RF read-only SQL
audit inside worker:0records/firstNULL/latestNULL/duplicates0; VOL audit also
passed. These are application-log SQL observations, not an independent SQL session.
No real RF forecast before close; gate BEFORE_OFFICIAL_CLOSE. No backfill.

[PR36](https://github.com/volk468-max/Analytical-Engine/pull/36) Draft/unmerged.
Raw technical_combined daily v1, explicit LOW_SUPPORT for sparse cells; not
technical_plus_v3, not calibrated, no proven forecast advantage. Local122tests
PostgreSQL17+9knowledge PASS;4schema backup/restore hashes match. Online knowledge
CI passed; full repeated pipeline still pending at this checkpoint.

Cron05:00Moscow Tue–Sat unchanged; first real RF issue2026-11-18 for USsession
2026-11-17 is pending, not claimed as issued. Active-task limit prevented a new
separate05:40audit; existing firstVOL audit Automation_a3be3fb079a881918909c1cd592c1d7c
was extended to BOTH models at existing05:30Moscow, preserving original VOL scope
and schedule. Notion history updated/corrected. Next real first-manifest audit,
then mature10/30session scoring. No production/trades/broker/merge/purchases.


## 2026-11-17 — Q011 / daily Ensemble Risk Forecast B

Owner requested Ensemble Risk Forecast on the same ten stocks and 10/30-session
grid. [Issue37](https://github.com/volk468-max/Analytical-Engine/issues/37).
Protocol frozen at12afba72735363868dae7b0f7c6c3a6809974420 before actual fits;
branch feature/ensemble-daily-ten-stocks based on RF metadata
f2e17ec10d90326edaf7baf0328d345c40a08c71. Actual worker still pins
261cf92ef3466934a2c3a9f4a56603f5fa00c925 at this implementation checkpoint.

Ensemble B is the mean of FIVE original same-target probabilities:
technical_combined, v3_state, technical_plus_v3, empirical volatility, QQQ regime.
Original RiskForecast/v3 source366f8cd00e8c228d4796d0abbe9997f717a3b6ad preserved,
v3 C/sensitive evaluator exact except UTC import. Required QQQ causal features;
optional VIX/SOX/support unavailable explicitly, no zero fill. Daily refit,
new30 horizon and CloseTOUCH form a NEW daily variant. Original PR18 result
0/162 primary advantages remains unchanged; no superiority claim.

120 immutable atomic series, DOWN5/10/15%, Low/Close TOUCH, warmup252/min252
mature labels/min10 each global class, LOW_SUPPORT if any sparse component.
NBIS starts2024-10-21. SQL008 additive,001–007 unchanged. No price forecast or
terminal return; no calibrated probabilities. NOT YET DEPLOYED. Next local SQL
acceptance, GitHub CI, authorised research-only update and actual preflight,
then first prospective manifest audit. Production/trades/merge unchanged.

[Q011](research/Q011-v1.md).


## 2026-11-17 — Q011-v2 / Ensemble B connected; real preflight and SQL audit PASS

[PR38](https://github.com/volk468-max/Analytical-Engine/pull/38) Draft/unmerged,
actual pinned sourcee581a0af10467ebc7720af8a3fdeac126199a6a3, deployment
79c1aabd-1c00-4914-8280-095c1b3b36c4 SUCCESS. Bootstrap READY/exit0 at11:10:14UTC
(run6ea2c412-a0ef-4b0f-9a04-4e240e92e29e); this source applies SQL001–008.
Existing001–007 unchanged. Research remains the sole environment, no staged
changes. Cron unchanged0 2 * * 2-6 =05:00Moscow Tue–Sat.

Actual run8c90266a-9d15-4b5f-890e-8c0841e10a55 completedSUCCESS/exit0
11:11:30UTC,93HTTP200/0failures/partial_phases empty. All10stocks checked:
ANET/NVDA/AMD/CRWD/GOOG/GS/META/MU/LRCX ready12targets each,
NBIS12BLOCKED INSUFFICIENT_MATURE_TRAINING_SUPPORT;108ready/12blocked.
Ensemble read-only SQL inside worker:0records/firstNULL/latestNULL/duplicates0.
VOL/RF audits also passed. These are application-log SQL observations, not an
independent SQL connection. BEFORE_OFFICIAL_CLOSE correctly prevented a daytime
backdated forecast. Original HIST/REGIME648 numerical forecasts still present.

133local tests on disposable PostgreSQL17 passed with0skips,9knowledge tests
and offline validator PASS;4-schema backup/restore exact content hashes match.
Online knowledge CI44070680112 SUCCESS, full CI44070680070 still running at
this checkpoint. Same five-component B raw uncalibrated daily variant, explicit
missing optional VIX/SOX/support, sparse components LOW_SUPPORT; no accuracy
advantage claimed. Original PR18 negative result preserved.

First actual daily Ensemble issue is pending2026-11-18 around05:00Moscow,
for USsession2026-11-17; not claimed as issued. Existing05:30Moscow first-issue
audit extended to Ensemble as well as VOL/RF, preserving original scopes/time;
Automation_a3be3fb079a881918909c1cd592c1d7c. Next verify actual immutable120row
manifest, blocks/reasons/LOW_SUPPORT/issuedUTC/duplicates, then mature10/30
session scoring. Operational status DEPLOYED_SCHEDULED_PREFLIGHT_AUDIT_PASS,
FIRST_PROSPECTIVE_ENSEMBLE_ISSUANCE_PENDING. Production/trades/merge unchanged.

[Q011-v2](research/Q011-v2.md).


### Q011 final deployed-source CI acceptance

On actual deployed sourcee581a0af10467ebc7720af8a3fdeac126199a6a3, full
[CI44070680070](https://github.com/volk468-max/Analytical-Engine/actions/runs/44070680070)
completedSUCCESS: PostgreSQL16/18, all parent research regression/replay and
backup/restore drills. Online knowledge CI44070680112 also SUCCESS. Previous
running status is historical. Prospective first issuance still pending.


## 2026-11-17 — Q012 / Market Drawdown Precursors daily deployment preparation

Owner explicitly requests daily deployment in existing isolated research Railway.
[Issue39](https://github.com/volk468-max/Analytical-Engine/issues/39); base
5ded52b0f309874e3ca08016be9bb87cd8fdffd3 (PR38 metadata), actual deployed source
e581a0af10467ebc7720af8a3fdeac126199a6a3. Source [PR20](https://github.com/volk468-max/Analytical-Engine/pull/20)
head8e9aec99c7eee8b384e35a3bc1aa734f2d54800d remains Draft/unmerged; original
0/33primary contrasts and unqualified PIT/missing factors findings preserved.

New daily RAW variant preserves exact original price feature_frame and ridge raw
fit mean/scale/coef/intercept C0.1. MINIMAL for SPY/QQQ/SOXX, PLUS_X for owner
ANET/NVDA/AMD/CRWD/NBIS/GOOG/GS/META/MU/LRCX.156series/session:13instruments,
10/30sessions,DOWN5/10/15 Low/Close TOUCH. Labels never pooled across instruments.
Daily expanding refit/no original annual intercept calibration/new30/CloseTOUCH
are EXPLICIT adaptations, not identical original annual calibrated forecasts.
Required SPY/QQQ/SOXX prices; no Breadth/VIX/macro/H4 or missing-value imputation.
Warmup252 and min252fullymature trainingrows/min10eachglobalclass; NBIS only
since2024-10-21. Raw unvalidated/uncalibrated/NOT_PIT probabilities.

Protocol702d8edffd198809b1635786b48874ea97684b79 committed before real fits.
Separate MARKET_PRECURSORS model/MDP_V1 manifest/lock280009, additiveSQL009;
001–008 and all previous models/history unchanged. SQL156atomic/idempotency/
rollback/fixturelive/readonly/oldVOLmanifest guards passed in disposablePG17.
Remaining local regression/CI and actual research deployment/preflight/SQLaudit
are pending at this checkpoint. First future issue must not be backdated.
[Q012](research/Q012-v1.md). No production/trades/merge/new purchases.


## 2026-11-17 — Q012-v2 / Market Drawdown Precursors operational acceptance

[PR40](https://github.com/volk468-max/Analytical-Engine/pull/40), Draft/unmerged.
Actual pinned sourceda216e5ab9025d0df1881cfcdcd14901b4e2e09a, deployment
74f84b49-d296-4736-b39f-47b025d3090f SUCCESS. Bootstrap READY/exit0
13:39:29UTC, run2e7cae06-f5e4-4c61-9078-447914e92317, applies additive009;
001–008 unchanged. Sole environment research, no staged changes.

Actual run046162ce-2d00-459b-a9e0-07ba3b5dc627 completedSUCCESS/exit0
13:41:01UTC,183HTTP200/0failures/partial_phases empty.156targets checked:
9ownerstocks plusSPY/QQQ/SOXX12ready each=144ready; NBIS12blocked
INSUFFICIENT_MATURE_TRAINING_SUPPORT. Worker read-onlySQL:MDP0records,
first/latestNULL,DUPLICATES=0; priorVOL/RF/Ensemble audits pass. Original
HIST/REGIME648numerical forecasts preserved. SQL from application logs is not
an independent SQL session. BEFORE_OFFICIAL_CLOSE prevented backdated issue.

Original MINIMAL market/PLUS_X stock features and rawridgeC0.1 preserved. NEW
expanding dailyrefit/noannualinterceptcalibration/10&30/Low&CloseTOUCH variant,
not identical original calibrated backtest. Raw/uncalibrated/unvalidated/NOT_PIT;
original PR20 result0/33 primary advantages remains negative. No missingfactor
imputation or pooledstock/market labels.

62local tests on disposablePG17 with0skips+9knowledge/offline validation PASS;
4-schema backuprestore exact hashes match. OnlineknowledgeCI44094734299 SUCCESS;
fullCI44094734515 running at this checkpoint. Notion Alpha OS saved and panel
requested. Cron0 2 * * 2-6 unchanged05:00MoscowTue–Sat; first issuePENDING
2026-11-18 around05:00Moscow,USsession2026-11-17. Existing05:30Moscow audit
Automation_a3be3fb079a881918909c1cd592c1d7c extended to MDP156manifest alongside
VOL/RF/Ensemble with scopes/time preserved. Next actual156manifest/timestamps/
blocks/duplicates then mature10/30session scoring. No production/trades/merge.

[Q012-v2](research/Q012-v2.md).


### Q012 final deployed-source CI acceptance

Actual deployed sourceda216e5ab9025d0df1881cfcdcd14901b4e2e09a passed full
[CI44094734515](https://github.com/volk468-max/Analytical-Engine/actions/runs/44094734515):
PostgreSQL16/18, old and new model suites, all parent research regressions/replay
and backup/restore drills SUCCESS. Authenticated onlineknowledge44094734299
also SUCCESS. Earlier running status is historical. Source stays SHA-pinned;
subsequent commits are evidence/knowledge only. First prospective issue remains
pending2026-11-18 around05:00Moscow; common acceptance05:30Moscow.


## 2026-11-17 — Q013 / owner replaces NBIS with AVGO

Owner explicitly requests AVGO instead of NBIS in current chat. New active order:
ANET,NVDA,AMD,CRWD,AVGO,GOOG,GS,META,MU,LRCX. Applies to four new daily models
VOL/RISK_FORECAST/ENSEMBLE_RISK/MARKET_PRECURSORS. HIST/REGIME unchanged; market
SPY/QQQ/SOXX retained. [Issue41](https://github.com/volk468-max/Analytical-Engine/issues/41).
BasePR40 metadatafef6da030befa977ed352473482f8eec040e835a; actual worker still
pinsda216e5ab9025d0df1881cfcdcd14901b4e2e09a at implementation checkpoint.

Shared active portfolio and universe-revision hash added to all four manifests.
Original estimator protocols/reports/oldNBIS records preserved; only current
universe superseded by reports/portfolio-avgo-v1/protocol.txt. AdditiveSQL010
updates the two future target guards, no existing rows modified.001–009
unchanged. Counts120/120/120/156,10/30sessions,labels/thresholds/estimators/gates
and cron unchanged. NBIS retrospective numerical cutoff retained; no backfill.

Replacement implementation prepared, not yet deployed. Local numerical tests
and actualSQL010 guard validation/CI are pending; AVGO real data/support must
be checked in all four models before claiming ready. Notion and first-issue
audit must supersede old NBIS universe prospectively. Research only, no trades/
production/mainmerge/new purchases. [Q013](research/Q013-v1.md).


## 2026-11-17 — Q013-v2 / AVGO deployed and ready in all four models

[PR42](https://github.com/volk468-max/Analytical-Engine/pull/42) Draft/unmerged.
Actual pinned source9e93e9a4914db95bc41d127afa19e2b3b96ca436, deployment
34e22c16-c498-412a-ae66-780eb5859aca SUCCESS. Bootstrap READY/exit0
14:37:04UTC run139f07a5-235a-404d-91b6-efb75b2db46d applies010.001–009 unchanged.
Active order ANET,NVDA,AMD,CRWD,AVGO,GOOG,GS,META,MU,LRCX. HIST/REGIME and
SPY/QQQ/SOXX unchanged. OldNBIS history/protocols retained, not relabelled/deleted.

Actual run59dc1994-fc1b-4553-99e3-ef3dee24d21a SUCCESS/exit0 at14:41:07UTC,
333HTTP200/0failures,partial_phases empty. VOL120ready,RF120ready,Ensemble120ready,
MDP156ready,0blocked. AVGO12/12targets ready in EACH model. All four worker
read-onlySQLaudits0records/firstNULL/duplicates0; oldHIST/REGIME648numbers intact.
These are application-log SQL observations, not independent SQL acceptance.
BEFORE_OFFICIAL_CLOSE prevents daytime/backdated issue. Readiness is not a real
forecast or predictive accuracy validation.

31local tests on disposablePG17 passed0skips+9knowledge/offlinevalidatorPASS.
Four-schema backuprestore exact hashes match. Onlineknowledge44104725436 SUCCESS;
fullCI44104725516 running at checkpoint. Local --online timed out at90seconds;
no localonline success claimed. Notion Alpha OS history saved.

First-issue05:30Moscow audit Automation_a3be3fb079a881918909c1cd592c1d7c updated
with explicit prospectiveAVGOoverride and historicalNBISnotes retained. Regular
five-day ForecastLab audit Automation_cc9778a7a54081918db93b4da1726ce0 updated
only its scope/currentcoverage/universe; schedule retained. After real success
all four *_PREFLIGHT_ONCE flags disabled, daily enabled flags remain true.
Cron05:00MoscowTue–Sat unchanged, first AVGOissuePENDING2026-11-18 around05:00,
USsessionNov17. Next actual120/120/120/156manifest/time/no duplicates/AVGO checks,
then mature scoring. Modelformulas/support thresholds/10&30/labels unchanged.
No trading/production/mainmerge/new purchases.

[Q013-v2](research/Q013-v2.md).


### Q013 final deployed-source CI acceptance
Actual deployed source9e93e9a4914db95bc41d127afa19e2b3b96ca436 passed full
[CI44104725516](https://github.com/volk468-max/Analytical-Engine/actions/runs/44104725516):
PostgreSQL16/18, prior and new model suites, parent regressions/replay/restore
SUCCESS. Authenticated onlineknowledge44104725436 also SUCCESS. Earlier running
status is historical. AVGO universe deployed, all four real preflights passed
516ready0blocked; first prospective issue still pending2026-11-18.


## 2026-11-20 — Q014-v1 / context integration and redundancy audit

Actual Railway source fd37ef2d347663aaf24b086c6db8d41928a6ea12, deployment
e244eb8e-4dfa-4754-a037-66a07ee1221b SUCCESS observed read-only. This supersedes
the Q013 deployed-source snapshot as a new observation only; no new cron/SQL
acceptance is inferred. New opt-in, separate contextual research adapter and
learned L2 logit-offset path prepared. NOT DEPLOYED, baseline unchanged.
No model removed: RF is one Ensemble component, complete models not identical.
MDP nesting violations require investigation before enhanced promotion. Current
coefficient/SA/archive/delivery readiness is insufficient: BASELINE_ONLY; no
trained live context weights. 10-session coefficient never reused for30.
See [Q014](research/Q014-v1.md) and [implementation report](../../reports/context-factors-v1/README.md).
