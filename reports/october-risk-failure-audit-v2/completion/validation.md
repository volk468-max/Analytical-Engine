# Validation

## Новые фактические прогоны

* Original Node CLI test.cjs:29/29 checks на исходном наборе. Original run.cjs повторён, исходные файлы остались byte-identical.
* Тот же неизменённый набор JS проверок повторён на completion inputs:29/29,58 запусков проверок суммарно,29 уникальных логик. Completion run.cjs завершён, prefix market и daily-equity равны оригиналу.
* pytest:20 passed (2 существующих main теста +18 новых completion тестов),0 failures. One environment anyio/pytest10 deprecation warning. Старые203 tests/20 subtests НЕ запускались: они относятся к отдельной research-цепочке, отсутствующей в main-based PR. Первоначальная попытка pytest без deps дала module-not-found; затем установлен в /tmp, финальный прогон успешен.
* XNYS44sessions, DST Nov2 open14:30/close21UTC, next-session timing/delay1/2, prices regular-session request, OHLC overlap10,556, dividends/NAV/no borrowing, future suffix/prefix, макро даты, UNKNOWN production, incomplete Nov2 order проверены.
* Оригинальный Python DecisionEngine исполнялся только на явно синтетических fundamentals для support; это не production replay. Conditional support comparison по историческим OHLC сохраняет только флаг и уровни.

## Не пройдены исторические подтверждения

Original timestamp/vintage attestations, настоящий market-wide breadth, полные исторические fundamentals/revisions/config/deploy input snapshots и реальные production decisions/orders/positions не получены. ФРС прочитана черезweb current official pages; directHTTP403 не трактуется как отсутствие релиза. Отсутствующие2Nov macro observations не заполнены.

Ценовая доступность следующей полуночью и macro2session lag — предположения, не истинный PIT feed. Поэтому диагностические решения не объявляются достоверно доступными production-сигналами и confirmed_trade_signal=false. Новый production engine/прогностическая модель не создавались. Daily lows используются только для future outcome labels, previous highs/lows в решениях только из прошлого; actual recovery rules неизменны. Выборка многократно исследовалась, поэтому она не independent holdout.

## Воспроизведение

Node24.19.0; Python3.12; для audit tests/calendar pytest9.2.0, exchange-calendars4.13.2 с зависимостями. Исходные файлы не перезаписывать. Fetch script только для нового snapshot; для идентичного воспроизведения читать замороженные raw/data файлы, не скачивать новые версии.

~~~bash
python -m pip install --target /tmp/alpha-completion-test-deps pytest==9.2.0 exchange-calendars==4.13.2
export PYTHONPATH="$PWD:/tmp/alpha-completion-test-deps"
python reports/october-risk-failure-audit-v2/completion/prepare.py
node research/october-risk-failure-audit-v2/test.cjs
node reports/october-risk-failure-audit-v2/completion/run.cjs
python reports/october-risk-failure-audit-v2/completion/support_check.py
python reports/october-risk-failure-audit-v2/completion/report.py
python -m pytest -q -p no:cacheprovider tests reports/october-risk-failure-audit-v2/completion/test_completion.py
~~~

baseline.json проверяет SHA256 исходного checkpoint1ee2c09; Git commit content-addressed. Tag audit-v2-baseline-20261103 создан и опубликован как удобная ссылка, без обещания технической блокировки перемещения тега. Контрольная точка — именно полный commit SHA. Нет force push/merge/deploy/productionwrites.
