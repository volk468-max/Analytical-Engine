# Issue25 / Draft PR26 — предварительная историческая калибровка и continuous NAV

**RESEARCH ONLY. Прогностическое преимущество не обнаружено.** Это реальные расчёты
на frozen исторических ценах, не synthetic-пример и не PIT-certified модель.
Полная квалификация данных остаётся **BLOCKED**. Ниже отдельно раскрыты неизвестные
платёжные даты, неопределённость источников и условность исполнения. Production,
merge, deploy, реальные сделки, live-расписание и платные данные не затронуты.

## Что изменилось по сравнению с v1

Владелец предоставил новые независимые подтверждения MU и отдельно разрешил
предварительное исследование при невозможности полной квалификации. Поэтому
прежний stop condition **не переименован в PASS**: добавлен отдельный v2 протокол,
зафиксированный первым коммитом продолжения до новых расчётов. Старые v1 отчёт,
action-audit, NA-таблицы и negative findings PR24 сохранены неизменными.

База: PR24 `51fb1d34ddb7a28e8bbc7b2361dcfc2107890f0b`; исходный milestone PR26
`82eebbd95579c022040065f67e30c369d0999906`. Оба Draft/unmerged, не production.
Новое исследование находится в том же [Draft PR26](https://github.com/volk468-max/Analytical-Engine/pull/26).
История 2010–2026 ранее изучалась, особенно 2021–2026; untouched holdout отсутствует.

## Независимая сверка и остаточные риски

- [Официальный Micron release 25.09.2024](https://investors.micron.com/news/press-release/2024/Micron-Technology-Inc--Reports-Results-for-the-Fourth-Quarter-and-Full-Year-of-Fiscal-2024-09-25-2024/default.aspx)
подтверждает USD0.115, record07.10.2024 и объявленную payment23.10.2024.
- [Vienna notice 04.10.2024](https://www.wienerborse.at/en/news/vienna-stock-exchange-news/micron-technology-dividends-global-market-10-07-2024/)
для MU/ISIN US5951121038 подтверждает ту же сумму и ex/record07.10, payment23.10.
Это сообщение конкретной площадки; оно не аттестует всю US settlement историю.
Frozen Yahoo MU event совпадает. Прежний MU sample blocker устранён.
- Сохранённый официальный Nasdaq API повторно проверен по SHA256: QQQ ex18.03.2024,
USD0.57345. Frozen Yahoo — USD0.573. Decimal nearest0.001 даёт точно0.573,
разница0.00045 меньше half-unit0.0005. **Округление численно совместимо**, но
спецификация округления Yahoo не получена; причина как vendor policy не доказана.
QQQ не входит в A/B/C, его дивиденды не участвуют в NAV; QQQ close служит regime.

Точные URL, retrieval UTC/status/raw hashes: source-retrievals.json; результаты и
структурированные факты: action-reconciliation.json. Новые полные third-party HTML
не перераспространяются: сохранены hashes/факты, оригинальные ответы были проверены
локально. Для повторного text-аудита нужны те же raw bytes; свежая страница может
измениться и не заменяет оригинал. Права на перераспространение не аттестованы.

Same-provider continuity diagnostic на двух NVDA splits и двух dividend dates
показывает согласованную нормализованную арифметику: остаток adjustment-factor
около0.0010–0.0016bp. Это **не независимый второй источник цен** и не проверка
полноты всех действий. Нельзя повторно умножать normalized shares на split ratio.
Список существенных оставшихся рисков:

1. Нет полной независимой price/action/ex-date history и доказательства отсутствия
пропущенных или двойных корректировок во всём архиве.
2. Yahoo получен ретроспективно: исходные historical vintages, публикация каждого
значения и subsequent revisions неизвестны. Класс RESEARCH_PRICE_REPLAY_NOT_PIT.
3. Почти все dividend payment dates отсутствуют. Только один MU payment независимо
подтверждён как объявленный; фактическое settlement не проверено.
4. Survivor-selected AMD/NVDA/MU, общие semiconductor/market факторы, одна уже
изученная история; результаты нельзя распространить на произвольный портфель.
5. Модель closing execution, комиссии и spread условны. Не доказана возможность
исполнения по указанным ценам; результат NON-EXECUTABLE, не brokerage P&L.

## Калибровка без использования будущих labels в коде

Target — EOD_CLOSE_TOUCH10_60: минимум одного из следующих60 closes frozen no-trade
портфеля <=90% NAV якоря t, не intraday и не continuous drawdown от HWM.
Все 19320 исходных labels, weights и regime/vol features восстановлены и совпали
с PR24; все raw hashes четырёх frozen источников проверены. Никакого refresh цен.

Для test yearY base train заканчивается до Jan1(Y−3), labels полностью зрелые;
банк frozen для cal и test. Cal начинается через60 сессий после train boundary,
последний cal label созревает строго раньше test boundary−60; первые60 сессий
каждого test year исключены. HIST Beta1/1, REGIME/VOL shrink20; intercept-only
logistic с ridge1 и bounds±10 для всех трёх. Нет выбора метода по test-результату.
Climatology — те же цели и даты, trailing5year anchors с maturity строго раньше t.

Итог: **2392 общие даты/портфель**, 2013-04-01…2026-08-13. B2019 имел только4
положительных cal labels при минимуме10; этот год исключён у всех портфелей для
парного сравнения, а не ради улучшения score. Annual60-session test gaps сохранены
в календаре bootstrap. Калибровочные окна обычно574 наблюдения/5 calendar blocks;
это зависимые labels, не574 независимых события.

| Портфель | Модель | Brier | Log loss | Bias, п.п. | AUC |
|---|---|---|---|---|---|
| A | HIST_raw | 0.259581 | 0.712436 | +17.31 | 0.452 |
| A | HIST_cal | 0.264140 | 0.729020 | +5.83 | 0.371 |
| A | REGIME_raw | 0.249182 | 0.691927 | +15.13 | 0.503 |
| A | REGIME_cal | 0.257058 | 0.713398 | +5.32 | 0.427 |
| A | VOL_raw | 0.255554 | 0.704799 | +16.08 | 0.487 |
| A | VOL_cal | 0.260776 | 0.722267 | +5.76 | 0.362 |
| B | HIST_raw | 0.190480 | 0.571140 | +17.16 | 0.511 |
| B | HIST_cal | 0.187668 | 0.572685 | +6.30 | 0.354 |
| B | REGIME_raw | 0.178534 | 0.543645 | +13.80 | 0.574 |
| B | REGIME_cal | 0.179363 | 0.550365 | +5.25 | 0.401 |
| B | VOL_raw | 0.182629 | 0.553479 | +14.96 | 0.563 |
| B | VOL_cal | 0.180404 | 0.557600 | +5.82 | 0.392 |
| C | HIST_raw | 0.258891 | 0.711039 | +17.79 | 0.441 |
| C | HIST_cal | 0.259821 | 0.720463 | +5.80 | 0.384 |
| C | REGIME_raw | 0.247242 | 0.687993 | +15.54 | 0.494 |
| C | REGIME_cal | 0.251892 | 0.702956 | +5.24 | 0.430 |
| C | VOL_raw | 0.251426 | 0.696382 | +16.26 | 0.509 |
| C | VOL_cal | 0.253242 | 0.706462 | +5.64 | 0.401 |

Среднее завышение сократилось, например REGIME A +15.13→+5.32п.п., B +13.80→+5.25,
C +15.54→+5.24. Однако marginal bias reduction не означает лучшую калибровку во
всех bins: ECE и Brier могут ухудшиться. В каждом frozen year intercept сохраняет
ranking; по всей истории annual shifts меняют межгодовой порядок, поэтому global
AUC может снизиться. ranking-by-year.csv содержит проверку annual raw/cal AUC.
Secondary slope/isotonic не выполнялись; slope NA, не доказательство slope=1.

| Портфель | Climatology Brier | Climatology log loss | HAC effective N | Неперекрывающихся окон60 | Hit-окон |
|---|---|---|---|---|---|
| A | 0.239514 | 0.672075 | 55.5 | 50 | 16 |
| B | 0.172969 | 0.533752 | 61.0 | 50 | 10 |
| C | 0.237635 | 0.668418 | 55.5 | 50 | 16 |

Эффективное N — описательная HAC120-оценка с сохранением пропусков календаря.
50 неперекрывающихся окон — не50 независимых рыночных событий; события разных
портфелей зависят от общих активов, число независимых market episodes UNKNOWN.
Наблюдаемых120-session blocks28, а не2392 независимых испытания.

## Статистическая оценка преимущества

9999 синхронных circular calendar-block повторов, seed2509; L120 primary,
60/180 sensitivity. Первичная family9 — calibrated против raw, вторичная family9 —
calibrated против climatology; Holm внутри каждой заранее объявленной family.
CI условны на зафиксированных annual fits: модели не переобучаются внутри bootstrap.
Это ограничение coverage и model uncertainty, не новая независимая валидация.

| Портфель | ΔBrier cal−climatology | CI95% low | CI95% high | Holm p |
|---|---|---|---|---|
| A | +0.017544 | -0.006884 | +0.043588 | 1.000 |
| B | +0.006394 | -0.011316 | +0.024929 | 1.000 |
| C | +0.014258 | -0.010014 | +0.039325 | 1.000 |

Все18 сравнений имеют Holm p=1.000; все primary L120 CI включают0. В primary
family лишь HIST_B и VOL_B дают небольшое point Brier improvement против raw,
но logloss ухудшается и CI включает0. **0/9 проходят первичный критерий** (>=1%
Brier gain, верхняя CI<0, Holm<.05, без ухудшения logloss). Против climatology
все9 calibrated Brier хуже по point estimate. Это отсутствие доказанного
преимущества в данном протоколе, не доказательство невозможности любого прогноза.

Полные Brier/logloss/bias CI — calibration-metrics.csv; paired60/120/180 CI —
comparisons.csv. Reliability10bins и effective support — reliability.csv.
35/51/60% остаются NOT VALIDATED: thresholds.csv содержит support и зависимые
описательные CI; при недостатке positive/negative/block support CI=NA, не ложный
нулевой интервал. Например B REGIME>=51% встретился всего1 раз — этого недостаточно.
A REGIME>=51%:343 зависимых даты, frequency18.95%, mean P58.71%, CI примерно1.0–49.2%;
это не оправдывает51% protective policy. Выборку нельзя трактовать как independent
биномиальную. Decision curve/threshold utility не объявлена подтверждённой.

Отдельные периоды2013–2019/2020–2026 и UP/DOWN/MIXED представлены в
period-regime-metrics.csv для всех моделей. Это descriptive subsets, не новый
поиск победителя. CI широки; формальный prospective power analysis не выполнен,
12 месяцев — минимум data-quality monitoring, не гарантия statistical efficacy.

## Непрерывный self-financing ledger

Общий старт2001-01-03 после252-day warmup, inception$100000, конец2026-11-06,
6500 daily marks/сценарий. A1/3, B20/20/20+40%cash, C inverse252 capped10–50.
Ежемесячное решение в первый close месяца, исполнение **следующим** session close;
веса C используют только историю до решения. StaticA/B не ребалансируются.
Текущая стоимость не сбрасывается в100k при каждом прогнозе. Dividends начисляются
по pre-trade units в ex-date receivable; неизвестная payment date означает
nonspendable receivable навсегда,0%interest. Только MU07.10.2024 переносится в cash
23.10 по подтверждённому объявлению; это исторический replay, не доказательство
фактического поступления. NAV включает требования, но ими нельзя оплатить покупки.
Нормализованные shares эквивалентны split-normalized numeraire; split memo не
изменяет их второй раз. Fractional, no shorts/leverage/flows, sells before buys.

Ниже zero-cost descriptive baseline; **не доходность реального счёта**:

| Рецепт | NAV, USD | CAGR | MaxDD | Пересечений >15% | Сессий >15% | Худшие 60 сессий |
|---|---|---|---|---|---|---|
| A | 30,627,562 | 24.85% | 86.27% | 78 | 4240 | -59.66% |
| B | 6,644,512 | 17.67% | 65.85% | 80 | 2861 | -40.11% |
| C | 22,613,579 | 23.39% | 86.86% | 58 | 4436 | -59.43% |
| A_STATIC | 39,783,475 | 26.12% | 85.25% | 72 | 4218 | -61.11% |
| B_STATIC | 23,910,085 | 23.66% | 66.73% | 71 | 4057 | -51.03% |

15% — строгое превышение continuous HWM drawdown, не hard stop. Пересечения порога
являются длительностями/эпизодами ряда, не независимыми кризисами. A/B/C проводят
4240/2861/4436 сессий ниже−15% HWM; самые длинные такие участки1733/530/1912 сессий.
Максимальная длительность ниже HWM2533/1194/3765 сессий соответственно. C не
гарантирует меньший DD; B снижает exposure, это не alpha.

Сохранено195000 daily rows:5 recipes×6 cost/spread combinations×6500 сессий.
Fees0/10/25bp и assumed spread0/5bp за traded notional, включая inception. В worst
предусмотренном cost case25+5bp NAV A/B/C=28.698/6.344/21.132 млн, CAGR24.53/17.46/
23.07%, MaxDD86.36/66.01/87.12%; суммарные nominal fees≈160734/38995/140811USD.
Это чувствительность к допущениям, не broker-specific quote/tax. 2013–2019 и
2020–2026 subperiod stats с новым локальным HWM и предыдущим close как началом
сохранены отдельно в ledger-economics.csv. Не смешивать их с full-period HWM.

Стоимость денежного резерва описательно: zero-cost monthly B против A даёт
terminal opportunity gap≈$23.983млн и CAGR gap7.18п.п.; staticB против staticA —
≈$15.873млн и2.47п.п. Это цена меньшей экспозиции на выбранной survivor истории,
не стоимость ложных предупреждений и не изолированное model advantage. У staticB
cash доля дрейфует, а monthlyB удерживает её примерно40%. Cash0% не T-bill yield;
потенциальный доход резерва неизвестен без qualified rates. У A/B/C terminal
непогашенные receivables≈$86810/$19186/$81452; неизвестные payment dates и отсутствие
реинвестирования могут существенно менять реальные executable траектории.

## Проверки, статус фаз и следующий этап

44 теста подсистемы (13 прежних+31 новых) и9 knowledge regression PASS локально.
Усилены Decimal/date/security guards, frozen-source hashes, OHLC/calendar gaps,
exact60/maturity/purge boundaries, future-label poisoning, C future-price invariance,
next-close lag, fee conservation, ex/pay receivables, no spending receivables,
continuous DD и offline/no-network. Полный verify_v2 повторно пересчитывает все
выходы с запрещённой сетью, сравнивает числа rtol1e-11/atol1e-8 и фиксирует SHA256;
результат и byte-identity в verification-v2.json. Synthetic tests не evidence efficacy.

| Этап | Статус |
|---|---|
| MU sample | DONE, подтверждён; старый blocker superseded |
| QQQ precision | DONE numeric compatibility; vendor policy NOT VERIFIED |
| Full history/PIT/independent continuity | BLOCKED |
| HIST/REGIME/VOL real historical intercept calibration | DONE, PRELIMINARY only |
| Continuous A/B/C/staticA/B + costs/reserve/DD | DONE, DESCRIPTIVE NON-EXECUTABLE |
| Secondary slope/isotonic, validated thresholds, power | NOT DONE / NOT VALIDATED |
| Trading-policy/model-driven trims, live deployment | NOT AUTHORIZED / NOT DONE |

Решение: **RESEARCH ONLY** для предварительных результатов; **NO-GO** для утверждения
о прогностическом преимуществе, использования порогов35/51/60 и реального риска<=15%.
Следующий этап: независимая полная action/price/settlement reconciliation, frozen
prospective protocol с blinded power/precision review. Не выбирать другой
calibrator/порог на этой же тестовой истории и не называть её нетронутым holdout.
Известный defect ladder PR22 не исправлялся и код ladder не вызывался.
