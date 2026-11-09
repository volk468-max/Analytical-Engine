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
