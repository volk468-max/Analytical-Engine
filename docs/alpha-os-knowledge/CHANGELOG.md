# Журнал изменений

Формат новой append-only записи: дата UTC | ID | автор/роль | тип fact/hypothesis/recommendation/owner-decision/status/correction | что/почему | PR | source SHA | affected files | supersedes ID (если нужно). Итоговый commit самой записи берётся из Git history, чтобы избежать self-referential SHA.

- 2026-11-04 | K001 | Codex | fact/status/recommendation | Первичный каталог 13 PR, чтение pinned отчётов и main; #14 вернул 404. Приведены ограничения восстановления. PR и source SHA: research.json, sources/PR01-v1.json–PR13-v1.json; affected: knowledge folder, AGENTS.md, validator/workflow/tests. Owner approval только для scope D001; research recommendations не утверждены.

Не редактировать старые записи; correction добавляет новый ID и ссылку на исправляемый. Локальные/CI проверки проверяют append-only сохранность baseline при --base-ref.

- 2026-11-05 | K002 | Codex | fact/status/recommendation | R14/R15 каталогизированы на pinned SHA; Q001 технический проект и synthetic gates, не реальные Norgate результаты. Источники PR13@371d7a1135e35f96b5f7583bddc6de1ea007bf82, PR14@f9288b42e0d58f521b57c420d79477d5aeb10459, PR15@90975c0acdda9c502c7b187c54d8d004b8f514b3, official docs reports/breadth-pit-data-qualification-v1/sources.json. Обновлены catalogue/status/limits/next steps; старые карточки/результаты не изменены. Новая работа — текущий Draft PR/SHA из Git history, без self-reference.

- 2026-11-05 | K003 | Codex | fact/research/recommendation | Q002 exact replay + stricter reused-history validation, R16 indexed. Источники PR7@366f8cd00e8c228d4796d0abbe9997f717a3b6ad, PR8@c228624158068db64fe7e487a5be59281448fcd9, PR11@5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7, PR12@4f8e5615a1c4977b93558735da49c8b424de83ab, protocol@b1d43275bb10bc69516e868b625377ceea4119b6. Old cards/records preserved. New results and economic diagnostics отдельные, not production/strategy change. Final publication SHA via Git history.

## 2026-11-05 / Q003 Ensemble Risk Forecast v1

Изучены frozenPR5–8/11–12/17, добавлен R17 snapshot/card/status и новый ансамблевый
вопросQ003 с протоколом до расчётов.0/162primary contrasts;RESEARCH ONLY.
Метаданные regime исходногоR17 восстановлены в новом исследовании отдельно от
probability. Предыдущие карточки/источники/числовые исследования не изменены.

Численная поправка Q003: bootstrap999→9999 для primary Holm162, без смены моделей
или критериев; отдельный addendum опубликован до corrected computation.

## 2026-11-05 / Q004 Market drawdown precursors / Issue19

Protocol опубликован до outcome analysis, frozen free2000–2026 price snapshot
аудирован; strict original PIT certification отсутствует.87market episodes,
25overlap clusters, causal pre-onset snapshots/controls/full prevalence;0/33primary.
Отдельный пререгистрированный pure-market stock comparator раскрывает ограниченный
secondary NVDA эффект, не validated core. Добавлены R18/status/Q004/shadow-log spec.
Предыдущие исследования/карточки/источники не перезаписаны, production не менялся.

## 2026-11-07 / Q005 Issue21

Первым опубликован протокол, затем минимальный Draft с portfolio contract/audit,
после — isolated synthetic prototypes/registry/tests/log mock. Все реальные metrics
BLOCKED/NA. R20/status/Q005 added append-only; production/research history unchanged.

## 2026-11-08 Q006

Issue23 new EOD target/recipes, free-source audit, baselines and tests; no original PR22 changes.

## 2026-11-08 Q007

Issue25 protocol first, sourceaudit evidence, blocked minimal calibration milestone. No empirical/ledger claims. R24/Q007 added; no earlier source changes.

## 2026-11-09 Q007-v2

Continued existing DraftPR26 after new owner evidence/authorization. MU sample
reconciled; QQQ numeric rounding compatible, not full qualification. Added real
preliminary nested calibration (0/9primary wins;Holm1), continuous descriptive
A/B/C/static ledgers/costs/reserve analysis and46subsystem tests. Old v1
reports/cards/records preserved; full-history/PIT gate remains BLOCKED.

## 2026-11-09 Q008

Issue27 protocol-first daily-shadow infrastructure, append-only SQL design and57local tests. NOT RUNNING, synthetic all222NULL; no production connection/mutation. Added R26/Q008; existing source cards unchanged.

## 2026-11-09 Q008-v2

PR28 rebased to current PR26, conflicts resolved preserving source history. R26-v2
negative evidence catalogued. Collector source-contract audit,222unqualified per-series
frozen artifacts, explicit external live blocker and PostgreSQL18 synthetic staging
with own-backend disconnect/recovery and immutable provenance. NOT RUNNING; no live,
production, deploy, paid provisioning, cron or trades.

## 2026-11-11 Q008-v3

Due diligence/protocol first; current EODHD deletion clause not reproduced, individual
permission absent; Tiingo Power postcancel retention incompatible. Personal-only
operator confirmed. Separate research-mode/legal gates, EODHD fixture adapter,
deletable encrypted payload plane, immutable safe audit, TTL/offboard/restore and
paired full-horizon outcomes. Currentreal0/222, synthetic216+6NULL. New card/report,
old artifacts/source cards/negative PR26 findings retained. NO-GO live/provider.

## 2026-11-11 Q008-v4

Expanded owner authorization and paid personal EODHD acceptance recorded. Added
separate worker/Dockerfile/Railway config, hash migrations, real artifact loader,
session readiness, atomic baseline, outcomes/weekly/private historical comparison.
Railway accept-deploy denied (user did not approve), services remain staged; real0,
firstNULL, croninactive, actual API/comparisonNOT_RUN. Exact handover supplied;
NOT RUNNING and not accepted. No production/trades/merge, old findings retained.

## 2026-11-15 Q008-v5

Read-only actual Railway investigation found structured attributes hidden by blank
message, first SOURCE_STILL_REVISING failure and later application SQL432/firstUTC.
Exact raw changed field/direct SQL unverified. Prepared semantic six-symbol readiness,
private failed-pair retention, bounded network retries, run UUID/UTC/message/safe
traceback and partial-failure diagnostics, additive005 and readonly audit. No deploy
or historical edits. Old cards/data/source/negative research results preserved.


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


### Q009 final code checkpoint
Published Draft PR34; fixed knowledge test-fixture scope and isolated legacy
issuance errors from VOL. One extra runtime regression passes:211distinct pipeline
tests across local runs, plus9knowledge tests; four-schema backup/restore passes.
No VOL live issuance asserted. Deployment/source preflight remain next gate.


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
