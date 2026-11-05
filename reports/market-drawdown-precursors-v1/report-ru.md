# Issue19 — Общерыночные коррекции: предвестники и прогностическая сила

**RESEARCH-ONLY. Преимущество нового прогнозного ядра не установлено; NO-GO для
production и заявления о валидации.** Ни одно из 33 первичных сравнений не прошло
заранее заданные критерии. Отсутствие значимости не доказывает отсутствие эффекта.
Основная цель здесь — вероятность **Low на 5% ниже anchor Close в следующих 10
торговых сессиях**, а не доходность/NAV или сравнение с Buy & Hold. Торгового
backtest нет. Общерыночные SPY/QQQ/SOXX и отдельные AMD/NVDA/MU не смешиваются
в одном outcome. SOXX — секторный ETF proxy, не весь рынок и не историческая breadth.

## Пререгистрация и исследовательская база

Протокол опубликован первым: `ee6e4de04a60b969fccb699b8697adf2b3d4d61d`. Аудит данных и
market-only addendum опубликованы до дополнительного сравнения в
`668edd688658819cfd20325a9ada2ea01cc0d6de`.
Первичные 33 теста/пороги/признаки/модели сохранены. Дополнение лишь отдельно
проверяет строго market-only baseline: исходная MINIMAL содержит ownRV20 и потому
честно называется market-conditioned, own-volatility-controlled, а не market-only.
Дополнительная семья из 3 сравнений вторичная, не заменяет первичную.

Прочитаны pinned PR8@c228624158068db64fe7e487a5be59281448fcd9,
PR17@7fe91ab87dcda3607863a19074e6d7b2400503e8,
PR18@43886c0516b35bcfd61afce583b17112ce94bce0. Все open/unmerged;
#17/#18 Draft. Новая ветка основана на #18 ради текущей knowledge base,
не является его внедрением. Предыдущие результаты 0/4,0/27,0/162 не переписаны.
Новый вопрос — dedicated market catalogue, pre-onset anatomy и дополнительная
сила фиксированных факторов, не повтор прежнего ансамблевого теста.

## Квалификация данных:2000–2026 не равно original PIT

| Инструмент | Первый bar | Последний bar | Строк | firstTradeDate metadata (не аттестация IPO) | PIT certified |
|---|---|---|---|---|---|
| SPY | 2000-01-03 | 2026-11-02 | 6749 | 1993-01-29 | нет |
| QQQ | 2000-01-03 | 2026-11-02 | 6749 | 1999-03-10 | нет |
| SOXX | 2001-07-13 | 2026-11-02 | 6364 | 2001-07-13 | нет |
| AMD | 2000-01-03 | 2026-11-02 | 6749 | 1980-03-17 | нет |
| NVDA | 2000-01-03 | 2026-11-02 | 6749 | 1999-01-22 | нет |
| MU | 2000-01-03 | 2026-11-02 | 6749 | 1984-06-01 | нет |
Сохранены бесплатные Yahoo chart responses, URLs, retrievalUTC, SHA256, reported
splits/dividends, normalized split-adjusted OHLC и XNYS4.11.2 calendar с DST и early
closes. Adjclose с dividend adjustment не смешивается с OHLC, второй split-adjustment
не применяется. Внутри фактических диапазонов нет пропущенных сессий/дубликатов/OHLC
ошибок. По каждому инструменту 6872 OHLC-field comparisons с frozen PR11 дают нулевое
расхождение. Это проверка совпадения архивов, не независимая provider verification.
SOXX до 2001-07-13 в сохранённом источнике отсутствует и не достраивался.
firstTradeDate — поле provider, не независимо проверенная IPO/listing date;
отсутствующая история не считается нулевым риском.

Строгий PIT gate **FAIL**: нет original historical vintages/publication timestamps/
независимо подтверждённой adjustment history. Next-midnight UTC availability —
консервативная гипотеза расписания, не свидетельство оригинального release.
Для этих цен разрешён только **AUDITABLE_RETROSPECTIVE_PRICE** causal replay.
Все результаты условны на достоверности provider history; исходная задача не
превращается в independently validated core. См. data-qualification.md,
data/manifest.json, split-quality.csv, source-coverage-era.csv, archive-overlap.csv.
Цены ETF включают ex-dividend price effects, не dividend total return.

STOP/NO-GO для VIX без исходных timestamps, credit/yields/liquidity без vintages,
true market/sector breadth и concentration без PIT memberships/holdings,
survivor-peer breadth и **H4 revisions**. Они не импутированы и не заменены текущими
данными. missing-factors.csv сохраняет все исключения. Windows/Norgate acquisition
отложен, trial/account/subscription не запускались; платные данные не приобретались.

## Каталог и чисто pre-onset анатомия

Closing observable-history peak, latest equal high, onset — первая более низкая
сессия; первый closing−5% threshold, lowest closing trough, recovery только после
Close>=старого peak. Nested declines объединяются до recovery. TOUCH Low labels
отдельны от closing-episode labels. Это observable-history high с 2000/IPO, не
доказанный lifetime ATH. Prior lifetime peak UNKNOWN; left-truncated означает лишь
случай peak в первой доступной строке, неизвестная более ранняя история остаётся
ограничением даже при false этом флаге. Незавершённые эпизоды right-censored.
В каталоге также onset-to-threshold/trough и first60-session depth/completeness.

| Proxy | Эпизоды>=5% | Открытые | С доступными pre-onset snapshots |
|---|---|---|---|
| SPY | 22 | 0 | 19 |
| QQQ | 23 | 1 | 19 |
| SOXX | 42 | 1 | 40 |

Всего **87** proxy episodes, объединены по перекрытию
в **25** market interval clusters. Это НЕ 87 независимых рыночных
событий; число статистически независимых событий UNKNOWN. Длинные unrecovered
эпизоды могут объединять несколько известных кризисов в один кластер.
Snapshots onset−60/40/20/10/5 строго до начала падения и только по известным
данным. Сам будущий peak/trough не используется как feature. Warmup252 и общий
SOXX контекст ограничивают earliest full feature panel; snapshots ранних 2000
часто MISSING_WARMUP. Доступные 2008/2020/2022 regimes описаны, но 2008–09 относятся
к train/descriptive, а не к held-out prediction window. Прогнозный test начинается
в 2010 по опубликованному протоколу; нет заявленного OOS-теста 2000–02/2008.

Матчинг до 3 controls: тот же proxy/causal QQQ regime/двухлетний блок, вне всех
квалифицируемых ongoing episodes, >=60 сессий от onset; nearest date, tie earlier.
Повторы и inverse-reuse weights сохранены, NO_MATCH допускается. Это case-enriched
описание, не выборка для probability training. Все population rates рассчитаны
на **всех** пригодных датах, включая no-crash, а не только matched controls.

Pre-onset60 coverage и lead times по всем флагам, без выбора победителя:

| Proxy | Флаг | Полных 60d событий | С предупреждением до onset | Медиана first lead, сессий |
|---|---|---|---|---|
| SPY | market_relative_weakness | 19 | 1 | 45.0 |
| SPY | market_vol_acceleration | 19 | 19 | 51.0 |
| SPY | sector_relative_weakness | 19 | 17 | 48.0 |
| SPY | sector_vol_acceleration | 19 | 16 | 48.0 |
| QQQ | market_relative_weakness | 19 | 4 | 50.0 |
| QQQ | market_vol_acceleration | 19 | 19 | 51.0 |
| QQQ | sector_relative_weakness | 19 | 17 | 53.0 |
| QQQ | sector_vol_acceleration | 19 | 15 | 47.0 |
| SOXX | market_relative_weakness | 40 | 9 | 40.0 |
| SOXX | market_vol_acceleration | 40 | 39 | 49.0 |
| SOXX | sector_relative_weakness | 40 | 32 | 48.0 |
| SOXX | sector_vol_acceleration | 40 | 35 | 47.0 |
Чаще всего до onset встречался market_vol_acceleration: хотя бы раз за 60 сессий
в 19/19 доступных SPY,19/19 QQQ и 39/40 SOXX эпизодов. Это описательное сравнение
фиксированных флагов после просмотра, не validated pattern. Для SPY на всех
пригодных датах precision этого флага 13.72% при base11.11%, false alarms86.28%.

Высокая coverage в 60-session окне не означает точный 10-session прогноз: флаг
может сохраняться долго и часто появляться без последующей коррекции. Это не
confusion-метрика и не самостоятельное доказательство предсказательной силы.
Полные offsets/nulls: market-episodes.csv, market-episode-clusters.csv,
pre-onset-snapshots.csv, matched-controls.csv, pre-onset-coverage.csv,
pre-onset-lead-times.csv, matched-factor-prevalence.csv.

## P(feature|crash), P(feature|no crash), P(crash|feature)

TOUCH5/10, все пригодные даты с 252-session warmup (train/descriptive+test),
поэтому эти prevalence estimates НЕ являются OOS результатом. Фиксированные
флаги: QQQ−SPY R20<=−3pp; max marketRV20/RV60>=1.1; SOXX−QQQ R20<=−3pp;
SOXXRV20/RV60>=1.1. Stock flags отдельно: MA50extension>=10% AND R60>=20%,
relative weakness<=−5pp, RV ratio>=1.1. Нет unlimited conjunction search.

| Proxy | Флаг | P(F|crash)% | P(F|no crash)% | P(crash|F)% | Base% | False alarm% | Recall% | Lift [95% CI] |
|---|---|---|---|---|---|---|---|---|
| SPY | market_relative_weakness | 12.09 | 6.25 | 19.48 | 11.11 | 80.52 | 12.09 | 1.75 [0.93;2.59] |
| SPY | market_vol_acceleration | 43.81 | 34.41 | 13.72 | 11.11 | 86.28 | 43.81 | 1.24 [0.97;1.51] |
| SPY | sector_relative_weakness | 32.01 | 20.66 | 16.22 | 11.11 | 83.78 | 32.01 | 1.46 [1.17;1.77] |
| SPY | sector_vol_acceleration | 38.79 | 25.09 | 16.19 | 11.11 | 83.81 | 38.79 | 1.46 [1.11;1.83] |
| QQQ | market_relative_weakness | 11.89 | 5.90 | 28.74 | 16.68 | 71.26 | 11.89 | 1.72 [1.13;2.34] |
| QQQ | market_vol_acceleration | 44.70 | 33.61 | 21.03 | 16.68 | 78.97 | 44.70 | 1.26 [1.05;1.45] |
| QQQ | sector_relative_weakness | 31.24 | 20.06 | 23.77 | 16.68 | 76.23 | 31.24 | 1.42 [1.20;1.65] |
| QQQ | sector_vol_acceleration | 40.18 | 23.89 | 25.18 | 16.68 | 74.82 | 40.18 | 1.51 [1.27;1.77] |
| SOXX | market_relative_weakness | 9.17 | 5.84 | 42.28 | 31.82 | 57.72 | 9.17 | 1.33 [1.04;1.61] |
| SOXX | market_vol_acceleration | 39.60 | 33.53 | 35.54 | 31.82 | 64.46 | 39.60 | 1.12 [1.01;1.24] |
| SOXX | sector_relative_weakness | 25.75 | 20.14 | 37.37 | 31.82 | 62.63 | 25.75 | 1.17 [1.02;1.33] |
| SOXX | sector_vol_acceleration | 30.64 | 24.73 | 36.64 | 31.82 | 63.36 | 30.64 | 1.15 [1.00;1.28] |
Все 4 market/sector flags и 7 stock flags, все 12 target tasks и regime slices,
blockCI399/HAC effectiveN — factor-prevalence.csv. Интервалы здесь pointwise,
exploratory, без отдельного победителя/confirmatory significance search. Высокий
lift может отражать уже начавшееся снижение, поэтому pure pre-onset snapshots
и causal near-high (expanding DD>=−2%) diagnostics показаны отдельно. Near-high
не гарантирует «до будущего onset»: это только известный на дату фильтр.

## Frozen predictive evaluation: основная задача TOUCH5/10

Train только из fully matured past labels доJan1(Y−1), anchor purge20 (60 дляh60).
CalibrationY−1 отделена: первые max(20,h) сессий удалены, полный future label должен
созреть до final max(20,h) сессий перед testY. TestY первые max(20,h) исключены.
На каждом году модели и calibration frozen; прошлые test years позднее становятся
past training. Никаких random-row splits, отборов flags/thresholds на итоговых тестах.
Годы 2010–2026 chronological, но исторически просмотренные и не untouched holdout.

HIST — annual expanding Beta(1,1), VOL — own logRV20 logistic, REGIME — QQQ causal
UP/DOWN/MIXED frequency shrink20. SIMPLE — own logRV20 + QQQ/SPY trend/R20;
PLUS_M — добавить QQQ−SPY R20 и market volatility ratios; PLUS_S — добавить
SOXX relative weakness/volatility ratio; MINIMAL — SIMPLE+M+S. Для акций PLUS_X
добавляет extension/R60/relative weakness/own volatility ratio к MINIMAL.
L2 C=.1, training-only scaling, intercept-only calibration ridge1 на отдельном
cal year. Raw/calibrated probabilities сохранены; primary metrics используют
calibrated logits, HIST/REGIME без refitted calibration. Пороги alert .20/.50.

| Instrument | n | Base% | HIST Brier | VOL | REGIME | SIMPLE | MINIMAL | PLUS_X |
|---|---|---|---|---|---|---|---|---|
| SPY | 3884 | 9.76 | 0.089247 | 0.087846 | 0.084913 | 0.088304 | 0.089373 | NA |
| QQQ | 3884 | 15.76 | 0.134058 | 0.130597 | 0.127060 | 0.131411 | 0.132410 | NA |
| SOXX | 3884 | 29.89 | 0.213332 | 0.208758 | 0.207483 | 0.208880 | 0.208918 | NA |
| AMD | 3884 | 53.19 | 0.250346 | 0.259523 | 0.249873 | 0.258780 | 0.259203 | 0.259981 |
| NVDA | 3884 | 42.22 | 0.252083 | 0.249256 | 0.246977 | 0.250714 | 0.252780 | 0.249973 |
| MU | 3884 | 51.93 | 0.250648 | 0.263305 | 0.249030 | 0.264369 | 0.264900 | 0.267228 |

Всего 261888 forecast task rows, не независимых событий.
**0/33** primary contrasts прошли criterion, минимальный raw p=0.1393, Holm p=1.0000.
Синхронный calendar-block bootstrap сохраняет все инструменты на одной sampled
дате:9999 primary repetitions, block40, sensitivity20/60, Holm33. Для secondary
999 repeats, blockmax(40,h), metrics/prevalence399. Критерий также требует>=1%
relative Brier gain, CIupper<0 на всех 3 длинах, достаточные классы/блоки, sign stability
по>=2eligible years и неухудшение logloss. Интервалы conditional on fitted models;
training/design uncertainty и regime instability полностью не покрыты.

Все 18 market и 15 stock primary contrasts, включая отрицательные, опубликованы:

| Инструмент | Модель | Baseline | Δ Brier | 95% CI40 | Holm p | Stable years |
|---|---|---|---|---|---|---|
| SPY | PLUS_M | SIMPLE | 0.000650 | [-0.000223;0.001731] | 1.0000 | False |
| SPY | PLUS_S | SIMPLE | 0.000818 | [0.000018;0.001751] | 1.0000 | False |
| SPY | MINIMAL | HIST | 0.000126 | [-0.004687;0.004932] | 1.0000 | False |
| SPY | MINIMAL | VOL | 0.001527 | [-0.000321;0.003847] | 1.0000 | False |
| SPY | MINIMAL | REGIME | 0.004460 | [-0.001136;0.010640] | 1.0000 | False |
| SPY | MINIMAL | SIMPLE | 0.001069 | [-0.000049;0.002354] | 1.0000 | False |
| QQQ | PLUS_M | SIMPLE | 0.000764 | [0.000069;0.001503] | 1.0000 | False |
| QQQ | PLUS_S | SIMPLE | 0.000437 | [-0.000469;0.001364] | 1.0000 | False |
| QQQ | MINIMAL | HIST | -0.001647 | [-0.011086;0.007510] | 1.0000 | False |
| QQQ | MINIMAL | VOL | 0.001813 | [-0.000365;0.004175] | 1.0000 | False |
| QQQ | MINIMAL | REGIME | 0.005351 | [-0.002339;0.013670] | 1.0000 | False |
| QQQ | MINIMAL | SIMPLE | 0.001000 | [-0.000287;0.002320] | 1.0000 | False |
| SOXX | PLUS_M | SIMPLE | 0.001023 | [0.000096;0.002155] | 1.0000 | False |
| SOXX | PLUS_S | SIMPLE | 0.001008 | [-0.001186;0.003333] | 1.0000 | False |
| SOXX | MINIMAL | HIST | -0.004414 | [-0.016511;0.007480] | 1.0000 | False |
| SOXX | MINIMAL | VOL | 0.000160 | [-0.003659;0.004107] | 1.0000 | False |
| SOXX | MINIMAL | REGIME | 0.001436 | [-0.009190;0.012179] | 1.0000 | False |
| SOXX | MINIMAL | SIMPLE | 0.000039 | [-0.002865;0.002923] | 1.0000 | False |
| AMD | PLUS_X | HIST | 0.009635 | [0.000435;0.019048] | 1.0000 | False |
| AMD | PLUS_X | VOL | 0.000457 | [-0.004573;0.005205] | 1.0000 | False |
| AMD | PLUS_X | REGIME | 0.010108 | [0.001306;0.019379] | 1.0000 | False |
| AMD | PLUS_X | SIMPLE | 0.001200 | [-0.002569;0.004847] | 1.0000 | False |
| AMD | PLUS_X | MINIMAL | 0.000778 | [-0.002041;0.003648] | 1.0000 | False |
| NVDA | PLUS_X | HIST | -0.002110 | [-0.014772;0.010982] | 1.0000 | False |
| NVDA | PLUS_X | VOL | 0.000717 | [-0.005493;0.007238] | 1.0000 | False |
| NVDA | PLUS_X | REGIME | 0.002996 | [-0.009261;0.015553] | 1.0000 | False |
| NVDA | PLUS_X | SIMPLE | -0.000741 | [-0.006879;0.005468] | 1.0000 | False |
| NVDA | PLUS_X | MINIMAL | -0.002807 | [-0.007908;0.002418] | 1.0000 | False |
| MU | PLUS_X | HIST | 0.016581 | [0.006051;0.027018] | 1.0000 | False |
| MU | PLUS_X | VOL | 0.003923 | [-0.001193;0.009163] | 1.0000 | False |
| MU | PLUS_X | REGIME | 0.018199 | [0.008203;0.028263] | 1.0000 | False |
| MU | PLUS_X | SIMPLE | 0.002859 | [-0.000148;0.006196] | 1.0000 | False |
| MU | PLUS_X | MINIMAL | 0.002328 | [-0.000064;0.005028] | 1.0000 | False |
predictive-evaluation.csv включает все baseline comparisons по primary/secondary
TOUCH/TERMINAL tasks с интервалами. Brier/logloss, precision/recall/FPR, alert
frequency, calibration bias/ECE, base-rate lift и их CIs — metrics.csv.gz.
Probability bins10 фиксированы и descriptive (reliability.csv.gz), raw Brier
также сохранён. По каждому инструменту/году/QQQ regime/era/near-high отдельно.
HAC effectiveN не определяется при календарных gaps/zero variance; N anchors и
число 40-session blocks не называются independent trials. Terminal/60d результаты
не подменяют основной отрицательный TOUCH5/10 вывод.

## Индивидуальные акции против строго market-only baseline

MARKET_ONLY использует QQQ/SPY/SOXX цены, включая QQQ logRV20; own stock features
отсутствуют. Outcome — по-прежнему отдельное падение акции. PLUS_X отличается
собственной волатильностью и stock X; это другой вопрос, чем X сверх уже
own-volatility-controlled MINIMAL в первичной семье 33.

| Акция | Δ Brier PLUS_X−market-only | 95% CI40 | Δ logloss | Holm secondary3 |
|---|---|---|---|---|
| AMD | -0.001168 | [-0.005802;0.003355] | -0.001313 | 0.6100 |
| NVDA | -0.011261 | [-0.020541;-0.001878] | -0.030853 | 0.0291 |
| MU | 0.003990 | [-0.001725;0.009657] | 0.008620 | 0.9140 |
У NVDA есть **вторичное exploratory** улучшение против конкретного market-only
logistic comparator: ΔBrier−0.011261,95%CI[−0.020541;−0.001878], Holm3=.0291.
Это не глобальная поправка по всем exploratory analyses и не независимая валидация.
Оно не подтверждает новый core: PLUS_X Brier0.249973 хуже простой REGIME0.246977;
X сверх MINIMAL в первичной семье 33 значимого преимущества не установил. AMD/MU
не подтверждают переносимость эффекта. Не выбирать NVDA или этот comparator
победителем после просмотра. Все 3 secondary tests сохранены отдельно; ни один
из них не заменяет первичный negative результат или PIT/prospective gate.

## Ответ на исследовательский вопрос и ограничения

Повторяющиеся price-relative weakness/volatility conditions действительно можно
описать перед частью market episodes и сопоставить с no-crash controls. Но
присутствие до событий и univariate prevalence не равны дополнительной прогнозной
силе. На фиксированных market/sector feature families **преимущество сверх сильных
baselines не установлено** по пререгистрированной TOUCH5/10 оценке. Нет оснований
называть найденный паттерн validated predictive core.

- Данные 2000–2026 retrospective, original PIT timestamps/adjustments не аттестованы.
  Историческая доступность цен реконструирована; составы breadth/H4 недоступны.
- 2000–02/2008–09 покрыты данными/descriptive catalogue, но не представлены как OOS
  model test. Общий SOXX252 warmup делает earliest full panel2002, early snapshots NA.
- ETF price proxy не neutral market breadth; выбранные AMD/NVDA/MU — survivors,
  секторные/общерыночные shocks связаны. Bootstrap date grouping уменьшает, не
  устраняет все проблемы зависимости.25 overlap clusters не 25 доказанно независимых
  market shocks. Неизвестная pre-2000 история/длинные recovery меняют segmentation.
- История 2021–2026 использована в PR8/17/18; более ранние известные кризисы также
  не становятся исторически слепым holdout от скачивания свежего архива.
- Calibration-window/intercept instability и низкая поддержка редких задач/режимов
  ограничивают precision. NA ratios/intervals остаются NA, не нулём или успехом.
- Pointwise secondary/pattern intervals не доказывают независимый эффект. Глобальный
  поиск сочетаний/порогов/акций не выполнялся; менять specification по этим результатам
  нельзя. Statistical failure не доказывает отсутствие всех возможных предикторов.

**GO: нет для validated core. RESEARCH-ONLY: да для ограниченного causal price-only
исторического исследования. NO-GO: unqualified factors/windows, production,
утверждение о доказанном incremental forecast advantage.** Экономическая полезность
— отдельный будущий gate, в этой задаче не проверялась.

## Дальнейшая независимая проверка

prospective-shadow-log.md и shadow-log-schema.json описывают immutable forecasts:
actual timestamp, frozen code SHA/protocol/input vintage/hash, symbol/population,
TOUCH definition/horizon/probability/quality, отдельно fully matured future label,
append-only records/hash chain и corrections с сохранением истории. Это только
спецификация: live infrastructure не запускалась. Резервировать будущие данные
со следующей сессии после публикации после отдельной авторизации logging setup,
минимум 2 года и 30 market episode clusters плюс blinded power check для 1%Brier gain;
продлить при недостатке мощности. No peeking/model switches, retain33-wayHolm,
original PIT input gate; экономический gate позже. Это рекомендация, не решение
владельца о внедрении или покупке данных.

Весь код/методика/тесты/сводные таблицы/полные forecasts сохранены; knowledge base
дополнена без перезаписи прежних карточек/исследований. Validation evidence —
validation.md/verification.json. No production, trades, merge/deploy or paid data.
