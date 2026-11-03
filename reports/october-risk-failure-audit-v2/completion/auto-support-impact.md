# AUTO-support — фактическое выполнение неизменённого Python

Источник: main a14ebf9c268bea5cb01de962edfb98b8df94652a, aae/engines/decision_engine.py, строки177–238 (history сортировка, recent_history[-120:], min(lows)),391–393 (price<support). Ни current-date, ни future-date filter нет. Точный исходник: https://github.com/volk468-max/Analytical-Engine/blob/a14ebf9c268bea5cb01de962edfb98b8df94652a/aae/engines/decision_engine.py#L177 . Локально source неизменён. Ключевые операции: usable_history.sort(key=history_date); recent_history=usable_history[-120:]; auto_support=min(lows) if lows else price; support_broken=price<support. Ниже минимальный исполняемый пример, support_check.py вызывает оригинальный класс.

~~~python
from aae.engines.decision_engine import DecisionEngine
from reports_dummy import snapshot # фактический helper snapshot находится в support_check.py
prior=[dict(date='2026-10-01',close=100,low=99,high=101)]
current=dict(date='2026-10-02',close=90,low=89,high=91)
# Полностью исполняемые вызовы и snapshot: support_check.py
~~~

|Сценарий|Support|Support broken|Действие на synthetic fundamentals|
|---|---|---|---|
|strict_prior|99.0|True|REVIEW|
|include_current|89.0|False|TRIM|
|include_future|1.0|False|TRIM|

При low_current<=close min(lows)<=close, поэтому price<support невозможно. Это условный input defect, а не доказательство production-ошибки. Отдельная будущая low1 также принимается и маскирует условие. MANUAL/prior-only histories отличаются. В fixture итоговый include-current TRIM остаётся возможным по другой ветви: подавление support condition не эквивалентно подавлению всей рекомендации.

В реальных OHLC проверены prior120 и include-current120 на каждой дате, исключительно для support-флага, не выдуманного fundamental replay. Маскируются5 строк; первая AVGO16октября, AMAT22октября, LRCX22октября, NBIS2ноября. Даты/уровни в support-impact.csv, две строки AVGO относятся к одному продолжающемуся эпизоду. У AMD/NVDA/MU в данном окне0 маскируемых prior120 пробоев. Следовательно этот кодовый дефект не даёт объяснения задержки раннего октябрьского предупреждения именно у них.

Оригинальные history/manual level payloads не получены: production impact UNKNOWN. Никакие изменения DecisionEngine/RiskEngine не сделаны. Пики support row будущие не используются. Вариант prior120 имел полную warmup историю к сентябрю; округлённые уровни исходника не меняют приведённый fixture.
