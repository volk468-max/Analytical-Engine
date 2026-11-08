# Три модельных портфеля — EOD CLOSE TOUCH10/60

RESEARCH ONLY, не портфель пользователя и не exact intraday probability.
Протокол опубликован первым: f02708c4c646c1c1c198b86db123dcb104459033.
Зависимая ветка от DraftPR22@9b68d2a9cd5f70d1f50ad430e5f3242bf03ff659, без merge.

A:1/3 каждого AMD/NVDA/MU; B:.2 каждого+.4 USD cash0%; C:inverseRV252,
не менее200returns (фактически252), clip(lambda/sigma,.1,.5), bisection sum1.
Каждый anchor создаёт отдельный no-trade book100000USD; shares/cash фиксированы
на60будущих closes. Внутри окна нет ребалансировки. Это не continuous account.

## Данные

|Symbol|First|Last|Rows|
|---|---|---|---|
|AMD|2000-01-03|2026-11-06|6753|
|NVDA|2000-01-03|2026-11-06|6753|
|MU|2000-01-03|2026-11-06|6753|
|QQQ|2000-01-03|2026-11-06|6753|

Raw responses, retrievalUTC/URL/SHA256 сохранены; XNYS и OHLC проверены до метрик.
RESEARCH_PRICE_REPLAY_NOT_PIT: original vintages, original publication timestamps,
actions/adjustment completeness и redistribution rights не аттестованы независимо.
Delisting evidence для survivor basket не устанавливает исторически нейтральную
вселенную. Отдельный EOD adapter использует provider split-normalised Close и
split-normalised dividends; ex-date gross receivable, no reinvestment, zerointerest.
Нет второго split/dividend adjustment; PR22 RAW_UNADJUSTED engine не используется.
Payment dates неизвестны: при gross zero-interest NAV receivable->cash не меняет
стоимость; налог/доходность cash/спендируемость dividend cash здесь не оцениваются.
Историческая доступность close на EOD assumed, не доказанные release/ingest logs.

## Результаты
Частоты на всех eligible anchors после252warmup, включая train и ранее изученную
историю, описательные; тестовые частоты отдельно ниже. Окна зависимы.

|Recipe|Anchors|Frequency%|Mean within-anchor DD60%|Continuous MaxDD|
|---|---|---|---|---|
|A|6440|45.25|19.10|NA|
|B|6440|30.51|11.96|NA|
|C|6440|44.46|18.79|NA|

Годовые frozen expanding fits2010–2026, mature labels и60session train purge;
REGIME shrink20 knownQQQ regime, VOL fixed RVbins(.2,.4,.6), HIST Beta1/1.
Никаких randomsplits, news scores или test-dependent calibration mappings.

|Recipe|Model|TestN|Test frequency%|Brier [CI120]|Logloss|HAC N_eff|
|---|---|---|---|---|---|---|
|A|HIST|4178|39.85|0.252828 [0.242090;0.263009]|0.698880|91.7|
|A|REGIME|4178|39.85|0.248474 [0.236519;0.259420]|0.690412|91.7|
|A|VOL|4178|39.85|0.252336 [0.240468;0.263276]|0.698392|91.7|
|B|HIST|4178|24.96|0.199413 [0.173817;0.225378]|0.589439|92.2|
|B|REGIME|4178|24.96|0.194041 [0.162582;0.225580]|0.576286|92.2|
|B|VOL|4178|24.96|0.198470 [0.169223;0.226921]|0.587264|92.2|
|C|HIST|4178|38.77|0.251529 [0.240838;0.262386]|0.696274|90.4|
|C|REGIME|4178|38.77|0.246525 [0.233691;0.258560]|0.686470|90.4|
|C|VOL|4178|38.77|0.248184 [0.235741;0.259926]|0.690353|90.4|

Все6парных CI разницыBrier REGIME/VOL−HIST включают0 при120blocks;
Holm p=.954. Прогностическое преимущество не установлено. Bias положителен:
оценки в среднем завышают риск примерно8–11pp. Reliability10bins в reliability.csv;
это диагностика некалиброванного estimator, не заявление готовой калибровки.
CI synchronous date-block999rep,120основной/60/180sensitivity, Holm6;
HAC effectiveN — приближение, не число независимых crash events. 4178test anchors
не независимы, лишь34полных120blocks. 2021–2026 уже многократно изучалась.

B уменьшает exposure: при unchanged stock shocks cash снижает event rate,
это не alpha. C лишь немного отличается отA в этой истории, победитель не выбран.
ScenarioDD60 — peak-to-trough внутри каждого отдельного anchor-window, включая
начальныйNAV; НЕ HWM непрерывного портфеля, не actual15%budget. Continuous ledger
не реализован, MaxDD/CAGR/trading costs NA. Ни одна recipe не гарантирует15%limit.

## Точность реализации и ограничения
Веса C используют только returns до anchor включительно; будущие returns не
участвуют. Все training maturity раньше annualcutoff и anchors60сессий до него.
Labels.csv.gz сохраняет weights/units/cash/min/terminal NAV/maturity, forecasts —
training support и lastmaturity. Future gap/незрелые60сессий отклоняются, раннийhit
не допускает незрелый label. Cash/дивиденды не переносятся между anchorbooks.
Unit tests — только software evidence, не empirical predictive evidence.

DONE: protocol/data retrieval/audit/EODadapter/A-B-C labels/baselines/reliability/tests.
BLOCKED: certified PIT/action reconciliation and independently validated probability.
NOT DONE: continuous ledger, Tbill sensitivity, covariance weights, policy comparisons.

PR22 ladder_target — BLOCKING DEFECT: sell onrise/fixedanchor противоположен
agreed sell5%initial per−2%from last execution, buy5%per+2%,floor50/cap100.
Функция здесь НЕ вызывается и НЕ исправляется; нужен отдельный reviewed PR22patch.
Original intraday contracts/functions и предыдущие исследования не изменены.

Следующий этап: независимая action/unit reconciliation и rights review, затем
future frozen EOD log и калибровка на отделённом прошлом; blinded power calculation.
Позже — preregistered Fed expectations surprise/credit/dated AI sentiment vs strongest
simple EODbaseline. Missing sources UNAVAILABLE, никаких произвольных+pp.
NO-GO trading/deployment/calibratedpersonalforecast; RESEARCH ONLY price replay.
No production/merge/deploy/broker/orders/data purchases. CI success не заявлен.
