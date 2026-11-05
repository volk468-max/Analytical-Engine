# Risk Forecast v2 — Predictive Validation

**Общее заключение: RESEARCH ONLY. Для текущего fixed estimator преимущество не установлено; GO для использования или усложнения модели на той же истории не обоснован.** Это не доказательство отсутствия любого эффекта: интервалы широкие, независимого нетронутого периода и подтверждённых original PIT vintages нет.

## Что действительно рассчитано

Протокол опубликован первым: commit b1d43275bb10bc69516e868b625377ceea4119b6. В изолированном PR7 checkout366f8cd00e8c228d4796d0abbe9997f717a3b6ad воспроизведён исходный runner без изменения параметров: все13CSV byte-identical, прежние0/18 primary successes подтверждены. Различается только run.json с metadata/absolute paths среды. Original source/artifact hashes проверены. Прежние удалённые исследования не менялись.

Новый benchmark — отдельная exploratory повторная оценка того же estimator architecture/параметров с более строгим обучающим окном, calibration holdout и20-session embargo. Это не утверждение, что новые probabilities равны опубликованным v1: refit deliberately использует меньше/более старых training rows. C/sensitive профиль зафиксирован как earliest source profile; все source annual profiles совпали. Новые baseline choices/thresholds не подбирались по результатам.

Тренировочные anchors2021+, calibration2023/2024/2025, test2024/2025/2026 соответственно. Cal — диагностика вероятностей, без fitted recalibration/подбора/обновления модели. Всего66438forecast rows, включая calibration;34200test task rows, которые не являются34200независимыми событиями. Таблицы по всем3тикерам,3порогам и3горизонтам, TOUCH и TERMINAL отдельно. Synthetic market data для расчётов не использовались.

## Главный числовой срез: TOUCH10 /20

| Model | n | Brier | Log loss |
|---|---:|---:|---:|
| technical_plus_v3 | 1875 | 0.237899 | 0.670022 |
| historical | 1875 | 0.233308 | 0.659593 |
| volatility | 1875 | 0.232776 | 0.658217 |
| regime | 1875 | 0.226822 | 0.645385 |
| technical_combined | 1875 | 0.234458 | 0.661968 |
| v3_state | 1875 | 0.236996 | 0.667175 |
| v3_score | 1875 | 0.235043 | 0.663038 |

Меньше — лучше. На1875коррелированных stock/date anchors primary model имеет delta Brier против unconditional +0.004591,95%block CI[-0.005270,+0.014504]; против volatility +0.005123,CI[-0.002495,+0.013066]; против regime +0.011077,CI[-0.003933,+0.026005]. Интервалы — conditional on fitted models and reused data, не prospective confirmation. Около95.89%primary forecasts в этом срезе LOW_SUPPORT.

0/27primary contrasts (9TOUCH tasks ×3frozen baselines) прошли заранее заданный criterion с Holm, практическим улучшением>=1%, интервалом<0 и устойчивостью по stock/year/block length. 0/9tasks выполнили критерий против всех3baseline. После Holm нет значимых первичных улучшений. Это другой family/benchmark, чем original0/18 UP/DOWN incrementality tests; их нельзя смешивать в общий success rate.

## Экономическая интерпретация отдельно

При fixed p>=.5, delay1, h20/10% средний относительный mark восстановления исходного1share lot составил AMD -5.8553% (21lots),NVDA -4.3458% (15),MU -8.5741% (13), нормировка на sale-open notional. Это НЕ portfolio return, НЕ9задач общей стратегии и НЕ независимые49рыночных испытаний: stocks связаны, окна и разные tasks повторяют пути. При delay2 результаты тоже сохранены; winner не выбирался. Cash-limited restoration не создаёт shares/cash из ничего; fees/slippage5bpкаждый на обе стороны учтены. Неизвестные dividend/tax/liquidity/PIT условия и допущения исполнения не позволяют объявлять инвестиционную эффективность. Полные отдельные ledgers/economic-summary.csv включают все27stock/task и оба delay.

## Решение и пределы

- NO-GO для заявления об установленном статистическом/экономическом преимуществе текущего estimator и для live integration.
- RESEARCH ONLY для дальнейшей разработки: только чёткая новая гипотеза, power/data-quality план и заранее зарезервированная будущая выборка. Не наращивать complexity на многократно просмотренных2021–2026 результатах.
- GO возможен лишь на независимых данных с достаточной поддержкой, PIT evidence и отдельно подтверждённой экономической ценностью. Сейчас эти условия отсутствуют.

Документы: protocol.md, data-audit.md, methodology.md, error-and-power-analysis.md, validation.md. Predictions .csv.gz.b64 декодируются base64→gzip→CSV. История/источники — source-manifest.json и обновлённая knowledge base. Production/engines/signals, paid data, broker, merge/deploy не затрагивались.
