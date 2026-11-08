# Issue25 — калибровка EOD и continuous ledger: первый milestone

**RESEARCH ONLY. Обязательная независимая сверка действий не завершена.**
По stop condition Issue25 выполнен ограниченный milestone: phase0 + phase1 +
минимальная gated-реализация калибровки. Реальные новые Brier/P/CI и ledger-экономика
**NA**, а не выдуманные результаты. Это не выполнение всех фаз и не новая валидация.

Протокол опубликован первым до исследования результатов. База — DraftPR24
51fb1d34ddb7a28e8bbc7b2361dcfc2107890f0b, без merge. Frozen Yahoo bytes/hash сохранены,
цены НЕ обновлялись. EOD_CLOSE_TOUCH10_60 отделён от intraday;15%HWM — отдельный бюджет.

| Проверка | Результат |
|---|---|
|PR24 raw hashes|Совпадают для AMD/NVDA/MU/QQQ|
|NVDA2024-06-10 split10:1|Issuer release содержит дату/ratio, соответствует provider event|
|NVDA2021-07-20 split4:1|Issuer announcement+provider совпадают; announcement был conditional|
|MU2024-10-07 .115 dividend|Получены index/soft-release страницы, нужной dated записи нет:BLOCKED|
|QQQ2024-03-18 dividend|HTML без данных; API доступен:Nasdaq .57345 против Yahoo .573|

Разница QQQ =0.00045USD/share. QQQ не является held asset вA/B/C: это НЕ доказательство
материальной ошибки NAV этих портфелей. Но точная сверка пререгистрированного sample
не прошла, tolerance нельзя выбирать ради удобного pass. Полнота действий, исходные
исторические vintages и права не аттестованы; RESEARCH_PRICE_REPLAY_NOT_PIT.
Независимый второй источник цены/полного total-return continuity также не установлен.
Получение HTTP200 не означает квалификации; raw evidence/URLs/times/hashes сохранены.

| Фаза | Статус |
|---|---|
|0 протокол|DONE: frozen methods/windows/gates/costs|
|1 action audit|DONE attempts/partial reconciliation; gate BLOCKED|
|2 минимальный calibrator|DONE code+synthetic fixtures, реальные fits/metrics BLOCKED|
|2 raw/cal/climatology comparisons, reliability,thresholdCIs|NOT DONE/BLOCKED,NA|
|2 slope/isotonic|NOT DONE; effective-support gate|
|3 continuous ledger/economics/sensitivities|NEXT MILESTONE,NOT DONE/BLOCKED|
|4 shadow log|DONE offline schema/mock only; live не запущен|

Минимальный модуль: замороженный base bank; chronological train/cal/test с60-session
purge/maturity, первичный intercept-only logit correction ridge1 и bounded scalar
solver. HIST также подлежит калибровке по будущему протоколу. Синтетическое демо
проверяет арифметику bias correction, не оценивает реальный риск. Пороговые35/51/60
**NOT VALIDATED**, trim simulation НЕ выполнялась. Intercept correction не создаёт
ranking information и не доказывает timing-предсказание. У PR24 отрицательная
история доказательств сохранена:6CI включали0, Holm=.954, bias+8–11pp.

Следующий milestone после data/ledger review: сначала получить original MU record,
согласовать точность dividend units и independently сверить continuity насплитах,
затем genuine as-of cal forecasts и paired120/60/180blocks/Holm9. Для continuous
ledger — monthly decision от previousclose/executionfollowingclose (NON-EXECUTABLE
до квалификации), A/B/C+staticA/B, segregated nonspendable receivables, fees0/10/25bp,
assumed spread5bp sensitivity, no inventedtax. Пока NAV/CAGR/DD15breaches/turnover/
missedupside —NA. CashB lower risk не alpha.15%не guarantee.

LadderPR22 — BLOCKING defect, не вызывается/не исправляется. Политики35/51/60 здесь
не разрешены. Будущий shadow log должен фиксировать actual UTC/source/model/code/
snapshot hashes и отдельный mature label. Pilot минимум12months только длякачества;
power/precision зависит от variance/arrival rate и может требовать лет, не90days.
2021–2026 не untouchedholdout. No news/Fed/credit features, no arbitrary+pp.

NO-GO: калиброванный прогноз/торговля/экономический вывод до устранения gate.
GO: review ограниченного milestone. No production/merge/deploy/broker/purchases.
Подробные gates: protocol-calibration-ledger.md, action-audit.json, source-followups.json,
evaluation-status.csv, synthetic-calibration-demo.json. Недостающие фазы названы явно.
