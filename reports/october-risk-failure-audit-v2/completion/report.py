"""Deterministic human-readable reports from frozen completion results."""
import csv,json
from pathlib import Path
P=Path(__file__).resolve().parent
def read(n):return json.loads((P/n).read_text())
def rows(n):return list(csv.DictReader((P/n).open()))
def table(head,rs):return '|'+ '|'.join(head)+'|\n|'+'|'.join('---' for _ in head)+'|\n'+''.join('|'+ '|'.join(str(x) if x is not None else '—' for x in r)+'|\n' for r in rs)
def main():
    r=read('results.json');portfolio=r['portfolio'];ss=r['summary'];coverage=rows('data-coverage.csv');dd=rows('drawdown-analysis.csv');imp=rows('support-impact.csv');fixtures=read('support-fixtures.json')
    ptable=table(['Вариант','Конечный капитал USD','Разница с B&H USD','MaxDD %','Cash USD'],[(('Buy & Hold' if x['fraction']==0 else str(int(x['fraction']*100))+'%')+' /delay'+str(x['delay']),f"{x['final_equity']:.2f}",f"{x['excess_vs_buyhold']:.2f}",f"{x['maximum_drawdown_pct']:.4f}",f"{x['cash']:.2f}") for x in portfolio])
    stocktable=table(['Акция','Δ5% USD','Δ10% USD','Продано/возвращено акций (10%)','Дефицит акций %','Дорогой выкуп USD','Блокированные новые переходы'],[(s,f"{next(x for x in ss if x['symbol']==s and x['fraction']==.05 and x['delay']==1)['excess_vs_buyhold']:.2f}",f"{(x:=next(x for x in ss if x['symbol']==s and x['fraction']==.1 and x['delay']==1))['excess_vs_buyhold']:.2f}",f"{x['shares_sold']:.4f}/{x['shares_restored']:.4f}",f"{x['shares_deficit_pct']:.4f}",f"{x['matched_rebuy_cost_minus_sale_proceeds']:.2f}",x['blocked_new_sector_sales']) for s in ['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']])
    dtable=table(['Акция','Пик','−5%','−10%','−15%','−20%'],[(x['symbol'],x['peak_date'],*[x['hit_'+str(n)] or 'не достигнут' for n in (5,10,15,20)]) for x in dd if x['view']=='OCTOBER_NESTED_DIAGNOSTIC'])
    (P/'executive-summary-ru.md').write_text('''# October Risk Failure Audit v2 — Completion

## Ответ на главный вопрос

В ценовых данных существовало воспроизводимое секторное предупреждение 8 октября, ещё при росте широких индексов. При принятой доступности close следующей полуночью UTC оно позволяло гипотетическую продажу 9 октября open. AMD находилась тогда примерно на −3.47% от известного пика, NVDA на −2.26%; закрытие −5% произошло 9 и12 октября соответственно. Это возможность исполнения при допущениях, а не доказанный production-сигнал и не доказательство экономической эффективности.

У MU/TSM −5% close уже достигнут 8 октября, у LRCX/NBIS раньше. Отскок к open9 октября не отменяет прежнее достижение порога. У NBIS исполнение было уже около −11.03%, у LRCX −6.18%. Брать один удачный пример за доказательство универсального раннего предупреждения нельзя.

## Подтверждённая хронология

Секторный флаг: 8 октября (не первый с сентября: были1 и14 сентября). QQQ:14 октября. VIX:16 октября, через рост за5 сессий, абсолютный уровень25 не достигнут. Дополнительно QQQ30 октября; сектор2 ноября, earliest calendar open3 ноября14:30UTC, вне теста и без цены исполнения.

8 октября независимые рыночные ряды подтверждают отставание сектора: SOX −1.60%, SOXX −2.26%, SMH −1.71% за5 сессий против QQQ +0.75% и S&P500 +1.29%. Это связанные секторные измерения, а не статистически независимые факторы. VIX тогда15.41 и снижался; немедленного системного stress-подтверждения не было. При консервативном macro lag известная10Y выросла примерно на31 б.п. за10 сессий, но лишь1 б.п. за5; исходные макровинтажи не аттестованы.

Официальная страница ФРС указывает повышение ставки16 сентября и сохранение28 октября; публикации в18:00UTC учитываются только после этого времени. Сентябрьское решение было доступно до октября; октябрьское не могло предупреждать о падении начала месяца. Текущие страницы не являются независимым архивом всех прежних версий; expectations/futures не получены.

## Экономика непрерывной модели

'''+ptable+'''
Модельный портфель: $100000,11 равных начальных долей капитала1/11, фиксированные исходные количества, без ребалансировки. Это не реальные веса владельца. Комиссия5bp и неблагоприятное проскальзывание5bp на каждую сделку включая начальную, сигнал после close, next-session open, восстановление3 clear closes и close>MA20. Правило полного восстановления перед новой продажей не изменялось. Delay2 означает ещё одну сессию ожидания.

Продажа и дорогой сентябрьский выкуп оставляют дефицит акций, блокирующий последующие сокращения у большинства позиций. Модель не оправдывает себя только наличием предупреждения:5%/10% дают ниже B&H при уменьшении MaxDD лишь примерно0.065/0.130 процентного пункта. Открытые остатки и дефицит оцениваются по2 ноября, завершение цикла не выдумывается. Деньги не добавляются, cash не приносит процента; dividend receivable не расходуется до неизвестной pay-date.

'''+stocktable+'''
`Дорогой выкуп` — расходы на восстановленные количества минус соответствующие чистые поступления продажи, FIFO, включая комиссии; отрицательное значение означает более дешёвый выкуп. Это не то же самое, что полное отклонение NAV: оно включает остаток акций, cash и дивиденды. Доли5% и10% — доля исходного количества, не величина падения. Число блокировок — условия создания ордера на новом переходе, включая2 ноября: это не число пропущенных исполнений внутри периода. Независимый старт октября не заменяет непрерывный сентябрьский тест и здесь не используется для итоговой оценки.

## Просадки

'''+dtable+'''
Это вложенный октябрьский диагностический срез, не независимые события. Для перенесённых META/AVGO первое пересечение могло быть до1 октября: полный сентябрьский каталог есть в drawdown-analysis.csv. Пики/минимумы используются только как ретроспективные labels. Для каждого нового предупреждения lead и предполагаемое исполнение доступны в warning-stock-analysis.csv; уже достигнутые пороги дают отрицательное опережение. Low-hit5% от signal-close внутри10 сессий — отдельная цель warning-outcomes.csv, не peak drawdown и не terminal return. У AMD/NVDA/MU2/3 зрелых секторных предупреждений ложные по этой цели; малые пересекающиеся окна и корреляции запрещают обобщать это как надёжную вероятность. Новое2 ноября предупреждение цензурировано.

## Причины и ограничения

Оригинальных production-пейлоадов/позиций/сделок не получено. Проверены только read-only Railway metadata и bounded filtered logs; пустой ответ при неизвестной retention не доказывает отсутствия предупреждений. Поэтому причина фактического поведения Alpha OS остаётся UNKNOWN. Сохранённые исследовательские HOLD/REDUCE/Forecast — не production-решения.

AUTO-support может скрывать собственный пробой текущей свечой. Но в оригинальном Python fixture включение свечи меняет REVIEW на TRIM через другую ветвь; нельзя утверждать, что этот дефект в целом запрещает сокращение. В окне найдено5 условно маскируемых support-flags у AVGO/AMAT/LRCX/NBIS, ни одного у AMD/NVDA/MU. Реальное влияние на production не подтверждено.

Полнота цен расширена до2 ноября; строгая point-in-time аттестация рыночных публикаций, макровинтажи, market-wide breadth, ожидания ФРС и production-журнал не получены. Доступность котировок next-midnight и макро lag2 сессии остаются предположениями. Поэтому все результаты — диагностические иллюстрации, confirmed_trade_signal=false. Торговая готовность и независимое инвестиционное преимущество не доказаны.

## Контрольная точка

Исходный аудит сохранён в commit1ee2c0958b12c821723c1923ddc69bd23a454a55 и baseline tag; SHA256 всех его файлов проверены. Новые данные/расчёты только в completion/. Новые торговые параметры и Risk Engine v3 не разрабатывались. Merge/deploy/production changes не выполнялись. Для причинной атрибуции нужны original decision payloads, PIT fundamentals/config/deployed-version history и реальные позиции/исполнения. Здесь остановка.
''')
    (P/'data-coverage.md').write_text('''# Полнота данных

'''+table(['Ряд','Поставщик','Наблюдений в44 сессиях','Последняя дата','Пропуски'],[(x['series'],x['provider'],x['rows'],x['last'],x['missing_equity_sessions'] or 'нет') for x in coverage])+'''
Файлы data/manifest.json содержат URL, retrieval timestampsUTC, SHA256 raw responses, источник, OHLCV, corporate actions и корректировки; inputs.json — фактически применённый набор. Yahoo запрос includePrePost=false, interval1d. Акции/ETF используют regular-session OHLC, индексы и валютный DXY отмечены своими рядами, а не equity quotes. Для DXY17:00NY и VIX16:15NY close — допущение описания дневного ряда, не доказанная лента публикаций. Adjclose не смешивается с OHLC. В окне нет splits; дивиденды сверены с events. NBIS не склеивается с YNDX/приостановленным периодом. Proxy fixed7semis — survivorship sample, не вся ширина.

Все11 акций, QQQ/SPY/IWM, S&P500/NasdaqComposite/Russell2000, SOX/SOXX/SMH, VIX/DXY покрывают44 торговых дня. Индексы и ETF сохранены отдельно, замены индексов ETF нет. 2Y/10Y имеют42 наблюдения:12 октября закрытие Treasury market,2 ноября ещё нет в ответе; IG/HY43,нет2 ноября. Даты не заполняются искусственно. As-of values могут переноситься после lag2sessions с сохранением даты наблюдения; это не котировка за новую дату. Новые values после cutoff не используются. Отсутствие оригинальных релизов/ALFRED vintages не позволяет назвать эту доступность подтверждённой.

Дата индекса в payload может быть временем начала торговли, а не публикацией OHLC; timestamps расчёта задаются явно в prepare/run, источник не считается исходным архивом публикаций. Перед DST regular close20UTC,2 ноября21UTC; open13:30/14:30. session-calendar.csv — exchange_calendars4.13.2 XNYS,44sessions, без7сентября. На3 ноября используется только известный календарь, не будущая цена.

10,556 OHLC comparisons нового Yahoo пакета с исходным audit inputs совпадают; prefix не переписан, только append после22 октября. VIX старого CBOE-пакета сохранён; continuation Yahoo, в audit window расхождения несущественны, вне окна Feb6 различается и не переопределяется. DGS10 prefix также не пересматривается. Точная повторяемость ценовых признаков и daily NAV до22 октября проверена.

ФРС: прямыеHTTP-запросы вернули403 (data/fed-events.json); web connector прочитал официальные страницы16сентября/28октября. Сохранены URL, время чтения, заявленное release time и структурированные факты в data/fed-verified-events.json, без имитации rawHTML. Ссылка календаря: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm . Expectations/futures, транскрипты/полный news feed не получены.

Недоступны original production payloads, orders/positions, исторические точные конфигурации на каждый день, настоящая market-wide breadth/constituents, исходные макровинтажи, полная history EPS/guidance. Текущие значения не подменяют исторические фундаментальные snapshots.
''')
    (P/'production-evidence.md').write_text('''# Production evidence — read-only

|Категория|Получено|Интерпретация|
|---|---|---|
|Подтверждённые production-сигналы|0 payloads|UNKNOWN, не HOLD|
|Сохранённые research snapshots|222 Overlay/Forecast строки|Архив PR-цепочки, не production|
|Ретроспективные расчёты|10 новых переходов флагов в44 сессиях|Фиксированные diagnostic rules, не сообщения Alpha OS|
|Недоступные решения/позиции/заявки|Нет read-only SQL/export|UNKNOWN, сделки не реконструируются|

Проверены provider describe-service и get-logs. Service source repo соответствует репозиторию, branchmain, latest deployment SUCCESS создан15 октября. Список variable names включаетDATABASE_URL; значения не запрашивались. У среды нет boundDATABASE_URL/readonlySQLconnection. Детальный sanitized результат в platform-evidence.json. Запрос deploy logs за1сентября–3ноября, filter Investment Memory, limit200 вернул0. Retention/completeness неизвестны: это не доказательство отсутствия сохранённых решений. Пейлоады исторических торговых заявок не доступны.

Текущая main DecisionEngine-v1.1 и investment_memory.py исследованы read-only. Исследовательские Overlay/Forecast находятся в отдельных ветках, а не в main; их прошлые артефакты и версии зафиксированы исходными sources.json. Ни current source main, ни latest deployment metadata не доказывают точную версию/конфигурацию в каждый день сентября. Полный исторический replay с несуществующими fundamentals не выполнялся.

Приложен saved-research-evidence.csv; дата в строке — историческая метка исследования, не подтверждённая дата production-расчёта. Для причинной атрибуции нужен read-only экспорт инвестиционных решений с created_at, полными входами и model/config version, deployment chronology, holdings и execution logs. Без них нельзя утверждать, что Alpha OS выдала HOLD, проигнорировала предупреждение или реально сэкономила/потеряла конкретную сумму. Никакие productionHTTP endpoints, SQL, записи или торговые заявки не выполнялись.
''')
    masked=[x for x in imp if x['masked_break']=='True']
    (P/'auto-support-impact.md').write_text('''# AUTO-support — фактическое выполнение неизменённого Python

Источник: main a14ebf9c268bea5cb01de962edfb98b8df94652a, aae/engines/decision_engine.py, строки177–238 (history сортировка, recent_history[-120:], min(lows)),391–393 (price<support). Ни current-date, ни future-date filter нет. Точный исходник: https://github.com/volk468-max/Analytical-Engine/blob/a14ebf9c268bea5cb01de962edfb98b8df94652a/aae/engines/decision_engine.py#L177 . Локально source неизменён. Ключевые операции: usable_history.sort(key=history_date); recent_history=usable_history[-120:]; auto_support=min(lows) if lows else price; support_broken=price<support. Ниже минимальный исполняемый пример, support_check.py вызывает оригинальный класс.

~~~python
from aae.engines.decision_engine import DecisionEngine
from reports_dummy import snapshot # фактический helper snapshot находится в support_check.py
prior=[dict(date='2026-10-01',close=100,low=99,high=101)]
current=dict(date='2026-10-02',close=90,low=89,high=91)
# Полностью исполняемые вызовы и snapshot: support_check.py
~~~

'''+table(['Сценарий','Support','Support broken','Действие на synthetic fundamentals'],[(x['case'],x['support'],x['support_broken'],x['synthetic_action']) for x in fixtures])+'''
При low_current<=close min(lows)<=close, поэтому price<support невозможно. Это условный input defect, а не доказательство production-ошибки. Отдельная будущая low1 также принимается и маскирует условие. MANUAL/prior-only histories отличаются. В fixture итоговый include-current TRIM остаётся возможным по другой ветви: подавление support condition не эквивалентно подавлению всей рекомендации.

В реальных OHLC проверены prior120 и include-current120 на каждой дате, исключительно для support-флага, не выдуманного fundamental replay. Маскируются5 строк; первая AVGO16октября, AMAT22октября, LRCX22октября, NBIS2ноября. Даты/уровни в support-impact.csv, две строки AVGO относятся к одному продолжающемуся эпизоду. У AMD/NVDA/MU в данном окне0 маскируемых prior120 пробоев. Следовательно этот кодовый дефект не даёт объяснения задержки раннего октябрьского предупреждения именно у них.

Оригинальные history/manual level payloads не получены: production impact UNKNOWN. Никакие изменения DecisionEngine/RiskEngine не сделаны. Пики support row будущие не используются. Вариант prior120 имел полную warmup историю к сентябрю; округлённые уровни исходника не меняют приведённый fixture.
'''.replace('from reports_dummy import snapshot # фактический helper snapshot находится в support_check.py','import importlib.util\nfrom pathlib import Path\np=Path("reports/october-risk-failure-audit-v2/completion/support_check.py")\nspec=importlib.util.spec_from_file_location("support_check",p)\nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\nsnapshot=m.snapshot').replace('# Полностью исполняемые вызовы и snapshot: support_check.py',"for history in [prior,prior+[current]]:\n    r=DecisionEngine().evaluate(snapshot(90),history)\n    print(r['range']['support'],r['conditions']['support_broken'],r['action'])"))
    (P/'validation.md').write_text('''# Validation

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
''')
if __name__=='__main__':main()
