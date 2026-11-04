# Alpha OS — Free Historical Index Data Audit v1

**Бесплатные источники позволяют построить исследовательские реконструкции, но достоверная полная PIT-база S&P 500/Nasdaq 100 за 2010–2026 в этой работе не получена. Полноценное тестирование раннего предупреждения Breadth начинать на этих входах пока нельзя.** Это результат аудита конкретных источников и доступных цен, не доказательство невозможности любого бесплатного решения.

Проверены исходные файлы трёх репозиториев, а не только README. Восстановлены 16940 source/date строк: четыре отдельных ряда по 4235 сессий с 2010-01-04 до 2026-11-03. 2026 — YTD, не полный год. Устаревшие хвосты явно помечены. Никакой источник не объявлен правильным по умолчанию.

## Ответы на семь вопросов

1. **Составы бесплатно?** Кандидатные ряды доступны. S&P-ряд thuning наследует fja: это не независимое подтверждение. Lawcal даёт другую реконструкцию, но с приблизительными датами и revision-time gates. Для Nasdaq есть только один из заданных источников, с backward reconstruction и ошибками исторических тикеров.
2. **Какие годы достоверны?** Ни один полный год 2010–2026 не получил квалификацию complete verified PIT history. Есть подтверждённые отдельные события и проверенная структура файлов; это не аттестация всего года. 2017+ у Nasdaq нельзя объявить чистым только по README: NLOK/QRTEA перенесены назад, а хвост после июня 2026 устарел.
3. **Котировки?** Повторно использован PR11: 31248 OHLCV строк по 19 инструментам, преимущественно 2020–2026. В индексы попадает лишь часть бумаг; сводка ниже. Это доля реально полученных exact-ticker member-day observations, не оценка максимума бесплатного покрытия. Для 2010–2019 в этом архиве котировок нет. Будущий/переименованный ticker не подставляется автоматически.
4. **Выбывшие компании?** По источникам найдено 338–386 выбывших S&P ticker histories и 140 Nasdaq. Их exact-ticker quote coverage в полученном архиве — 0%. Index exit не означает exchange delisting; банкротства/поглощения нельзя выводить из одного удаления. Для всех кандидатных тикеров опубликован реестр статуса, но live-запросы ко всем символам не выполнялись: доступ к разрешённому полному бесплатному провайдеру не установлен.
5. **Начинать backtest?** Можно отлаживать загрузку/контроль качества, отдельно маркируя approximate inputs. Делать полноценные выводы об эффективности Breadth нельзя; historical_backtest_eligible=False для всего набора. Сигналы и стратегию здесь не рассчитывали.
6. **Что докупить при необходимости?** Исторические effective memberships, стабильные security IDs и issuer links, delisted/acquired/bankrupt security OHLCV, ticker-validity intervals, corporate actions, корректировки, delisting outcomes и разрешённое хранение. До покупки проверить образец спорных случаев, права и доступность обоих индексов.
7. **Оправдан ли Norgate $630/год?** Для личного некоммерческого исследования — обоснованный кандидат, закрывающий нужные классы пробелов по документации; экономия времени вероятна, но точность не проверена на купленном наборе. Для коммерческого/общего публичного Alpha OS — не автоматическое решение: действующий FAQ ограничивает personal use, коммерческой лицензии не предлагает, raw/metadata после окончания entitlement нужно удалить. Оплачивать без согласования не следует. Подписка не приобреталась.

| Source | Candidate ticker histories | Observed departed tickers | Archived OHLCV member-days / candidate member-days | Coverage |
|---|---:|---:|---:|---:|
| fja_sp500 | 848 | 345 | 13660 / 2126329 | 0.6424% |
| thuning_sp500 | 841 | 338 | 13660 / 2126328 | 0.6424% |
| thuning_ndx | 241 | 140 | 13596 / 435613 | 3.1211% |
| lawcal_sp500 | 889 | 386 | 13661 / 2116199 | 0.6455% |

S&P источники расходятся хотя бы в одной паре в 3408/4235 сессий (включая старые хвосты); 847 интервальных расхождений сохранены в source-disagreements.csv. Это частота разногласий, не процент ошибочных составов. У lawcal 257 approximate additions, 131 approximate removals; CIK — issuer ID, не security ID.

Источники: [fja](https://github.com/fja05680/sp500/blob/a2430f2af0c79ddf0748e91de11bdeb1616ab5a7/S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv), [thuning SP](https://github.com/thuningxu/sp500nq100/blob/1cc1de2770874293597a418b41b079e5337b260c/sp500_components_history.csv), [thuning Nasdaq](https://github.com/thuningxu/sp500nq100/blob/1cc1de2770874293597a418b41b079e5337b260c/nasdaq100_components_history.csv), [lawcal](https://github.com/lawcal/sp500-components-history/blob/bb43682b4078a6266bc1ad157f3e1ec8b12af31f/data/components_history.csv); pinned Alpha OS PR11 SHA/хеши — source-manifest.json. Тариф и ограничения: [Norgate pricing](https://norgatedata.com/stockmarketpackages.php), [content](https://norgatedata.com/data-content-tables.php), [FAQ](https://norgatedata.com/faq.php). Подробности и границы проверки — source-audit.md, data-quality-report.md, validation.md.
