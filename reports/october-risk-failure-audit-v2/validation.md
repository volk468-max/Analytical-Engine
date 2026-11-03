# Validation and reproducibility

**29/29 pure-JavaScript проверок исполнены в V8 functions.exec, 0 failures.** test.cjs содержит тот же проверенный текст. Проверены costs, next-open, delay, gap, no-repeat, restoration, no borrowing, NAV, ex-date entitlement, prefix invariance, prior support, conditional self-inclusion, nested/censored events, missing outcomes, duplicate dates, VIX availability, unknown production statuses. Имена и результат — test-results.json.

**НЕ выполнены:** Node CLI/fs integration и существующий Python suite (shell environment FAILED); независимый provider refresh; полный период до 2 ноября; исходные публикации/макровинтажи; original production replay/реальные позиции/сделки. Старые 203 tests/20 subtests не повторялись и не входят в 29. Неаттестованная PIT-доступность не считается пройденной исторической проверкой.

Данные: 2639 warmup+audit price rows /13series; 407 stock-days,37 market-days до22 октября;7 weekday-placeholder без цен. 222 saved research rows,8 новых transitions. 370 перекрывающихся stock closes совпадают в двух архивах (не независимые поставщики). Empty/null означает unknown/censored, не ноль.

Воспроизведение после восстановления shell (Node18+, без зависимостей/сети/credentials):

~~~bash
node research/october-risk-failure-audit-v2/test.cjs
node research/october-risk-failure-audit-v2/run.cjs
~~~

run.cjs читает только опубликованные inputs/sources/saved-research-signals и пишет только каталог аудита. Pure code не импортирует приложение, не обращается к production. Общий split engine не заявляется: проверено отсутствие splits в доступном окне. Dividend pay dates неизвестны, receivable не расходуется. Для полной проверки требуются поставщик и дополнительная история.

Гипотезы известны по прежним исследованиям: даже новый протокол не превращает эту выборку в untouched holdout. Воспроизводимость архивной ассоциации не равна инвестиционной эффективности. Полный аудит не завершён; этапы2–5 не выполнялись. No merge/deploy/SQL/live orders.
