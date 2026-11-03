"""Generate a deterministic Russian report without selecting parameters."""
import csv,json,statistics
from pathlib import Path
from research.fixed_5pct_buyback.run import REPORT as R,write
def rows(n):return list(csv.DictReader((R/n).open()))
def number(v):return f'{float(v):,.2f}' if v not in ('',None) else '—'
def table(head,rs):return '|'+ '|'.join(head)+'|\n|'+'|'.join('---' for _ in head)+'|\n'+''.join('|'+ '|'.join(str(x) for x in r)+'|\n' for r in rs)
def main():
    comp=rows('comparison.csv');sens=rows('sensitivity.csv');lots=rows('cycles.csv');stocks=rows('stock-results.csv');canonical='LIMIT_0.1_T0.05_D1_S0';cl=[l for l in lots if l['scenario']==canonical]
    labels={'A_BUY_HOLD':'A Buy & Hold','B_SALE_ONLY_0.05_D1':'B Только продажа5%','B_SALE_ONLY_0.1_D1':'B Только продажа10%','LIMIT_0.05_T0.05_D1_S0':'C Продажа5% /выкуп−5%','LIMIT_0.1_T0.05_D1_S0':'D Продажа10% /выкуп−5%','E_PRIOR_0.05_D1':'E Прежний возврат5%','E_PRIOR_0.1_D1':'E Прежний возврат10%'}
    comparison=table(['Стратегия','Итог NAV USD','Δ к B&H USD','Макс.просадка %','Cash USD'],[(labels[x['scenario']],number(x['final_equity']),number(x['excess_vs_buyhold']),number(x['maximum_drawdown_pct']),number(x['cash'])) for x in comp])
    stocktable=table(['Акция','Δ5% USD','Δ10% USD','Дефицит акций10%','Cash10% USD','Выкуплено/продано лотов'],[(s,number(next(x for x in stocks if x['symbol']==s and x['scenario']=='LIMIT_0.05_T0.05_D1_S0')['excess_vs_buyhold']),number((x:=next(x for x in stocks if x['symbol']==s and x['scenario']==canonical))['excess_vs_buyhold']),number(x['shares_deficit']),number(x['cash']),str(x['closed_cycles'])+'/'+str(x['sales'])) for s in ['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']])
    st=table(['Порог выкупа','Исполнение','Итог NAV10%','Δ к B&H','Заполнено','Среднее/медиана сессий'],[(str(int(float(x['threshold'])*100))+'%', 'строгое' if x['stress']=='True' else 'базовое',number(x['final_equity']),number(x['excess_vs_buyhold']),str(x['closed_cycles'])+'/'+str(x['sales']),number(x['mean_wait'])+'/'+number(x['median_wait'])) for x in sens if x['mode']=='limit' and x['fraction']=='0.1' and x['delay']=='1'])
    delayed=table(['Сценарий','Итог NAV','Δ к B&H'],[(x['scenario'],number(x['final_equity']),number(x['excess_vs_buyhold'])) for x in sens if x['scenario'] in ['LIMIT_0.05_T0.05_D2_S0','LIMIT_0.1_T0.05_D2_S0']])
    opened=table(['Акция','Сигнал','Продажа','Лимит','Marked benefit USD'],[(x['symbol'],x['signal_date'],number(x['sale_price']),number(x['limit_price']),number(x['unrealized_missing_shares_benefit'])) for x in cl if x['status']=='OPEN'])
    q=[{k:v for k,v in l.items() if k not in ['quantity','budget','sale_fee','buy_fee','sale_slippage','buy_slippage']} for l in cl];write('sale-quality.csv',q)
    waiting=[]
    for x in sens:
        if x['mode']!='limit':continue
        for symbol in ['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']:
            ls=[l for l in lots if l['scenario']==x['scenario'] and l['symbol']==symbol];wait=[int(l['wait_sessions']) for l in ls if l['status']=='CLOSED'];mature=[l for l in ls if l['horizon_10_complete']=='True']
            waiting.append(dict(scenario=x['scenario'],symbol=symbol,closed=len(wait),sales=len(ls),filled_fraction=len(wait)/len(ls) if ls else None,mean_wait=statistics.mean(wait) if wait else None,median_wait=statistics.median(wait) if wait else None,mature_10=len(mature),no_down5_within10=sum(l['false_sale_10']=='True' for l in mature),right_censored_open=sum(l['status']=='OPEN' for l in ls)))
    write('waiting-summary.csv',waiting)
    (R/'executive-summary-ru.md').write_text('''# Fixed5% Buyback — Executive Summary

В данном коротком тесте ответ по капиталу — **да относительно Buy & Hold и прежнего восстановления**, но **нет относительно варианта только продажи**. Это ретроспективное исследование опубликованных секторных предупреждений, а не подтверждённые реальные сделки Alpha OS и не доказательство инвестиционной эффективности вне выборки.

Период1сентября–2ноября2026,11 акций,100000USD,11 равных начальных денежных долей, без ребалансировки. Продажи по тем же sector_flag activations PR9; определения/даты не менялись. Полное восстановление перед новой продажей больше не требуется; каждый лот отдельный. Покупка — только95% фактической sale fill price, с последующей сессии, без условий риска/МА/тренда.

'''+comparison+'''
Основная модель10%:33 продажи,29 полных выкупов,4 незавершённых лота; заполнение87.88%. Среднее ожидание завершённого выкупа16.45сессии, медиана14. 11 сигналов2ноября не исполнены до конца окна: для них лоты/прибыль не создавались. Cash включает суммы незавершённых продаж и не называется прибылью.

10%: реализованный чистый денежный surplus завершённых циклов1430.68USD, mark-to-end benefit незавершённых−70.75USD; итоговое преимущество к B&H1359.92USD. Для5% эти величины вдвое меньше:715.34,−35.38 и679.96USD. Издержки уже учтены; slippage, встроенное в цены, повторно не вычитается. Денежный остаток не приносит процента. Упущенные дивиденды посчитаны отдельно (для этой основной конфигурации0).

**Больше акций, чем Buy & Hold, не получилось и по этим правилам невозможно:** выкупается ровно проданное количество, cash surplus не реинвестируется. После полных циклов исходное количество восстанавливается, в4 открытых лотах остаётся дефицит. Больше капитала не означает больше акций.

## Качество продажи и покупки — разные вопросы

19/33 продаж не дали low-падения5% от фактической sale fill price за следующие10 полных сессий (57.58%).29/33 всё же достигли выбранного лимита до конца теста благодаря бессрочному ожиданию. Позднее исполнение нельзя выдавать за своевременное10-дневное предупреждение. Положительная экономия завершённого цикла во многом следует из самого условия покупки дешевле; пропущенные и незавершённые случаи обязательны для оценки.

Продажи сентябрьских предупреждений в ряде случаев предшествовали продолжению роста. Примеры/максимальные runups, terminal10 return и статусы в sale-quality.csv и opportunity-cost.csv. В открытых лотах ниже минус означает потери от отсутствующих акций против удержания; плюс означает marked защиту. Это ещё не завершённая прибыль.

'''+opened+'''
Цифры этой таблицы и stock-results.csv относятся к независимому100000USD на одну акцию; вклад в модельный100000USD портфель равен1/11. Например отрицательный открытый лот AMD не означает отрицательный итог всех циклов AMD.

## Что изменилось относительно PR9

Новая политика позволяет продавать другие свободные акции, пока старые лоты не выкуплены, и исключает дорогой выкуп по подтверждению тренда. Прежняя политика воспроизведена неизменённым архивным JS и совпала с PR9. Новая политика меняет одновременно gate следующих продаж и правило выкупа: всю разницу с E нельзя приписывать только качеству покупки. Sale-only помогает отделить цену раннего возврата: в падающем конце периода он удерживал меньше акций и дал больший NAV. Это не основание выбрать его для иных режимов.

## Ограничения

44 сессии, коррелированные акции и3 фактически исполненных общих дат сигнала — малая зависимая выборка.33 строки не33 независимых рыночных эксперимента. Исходные publication times/макровинтажи не аттестованы; это исследовательские сигналы. Daily low-touch не доказывает достижимое полное исполнение лимита/очередь. Внутридневной порядок high/low на дне limit fill неизвестен: показаны границы runup. Сильный гэп даёт price improvement по open только как модельное допущение.

Соседние пороги и задержки опубликованы полностью; основной−5% не переопределялся. Длинный тест2021–2026 не выполнен: для этой замороженной последовательности секторных предупреждений за весь период нет входов в аудите. Нельзя выдавать другие v3 сигналы за продолжение этого же ряда. Вывод не является готовой рекомендацией для реальной торговли. Merge/deploy/production изменений и реальных заявок нет. Остановка после исследования.
''')
    (R/'report.md').write_text('''# Методика, полные результаты и чувствительность

Источник: PR9 commit7135c2bdc0653986d93dfcfc66b202a6fb2f741e. Исходные inputs/сигналы/календарь/benchmark сохранены byte-for-byte с SHA256 в inputs/provenance.json. Ветка основана на main, не на PR9. Протокол commit37065b2 опубликован до расчётов и Draft PR создан заранее. Применяются только sector_flag новые активации1сентября,14сентября,8октября,2ноября. Последняя не имеет fill в тесте. QQQ/VIX не объединяются с ними. Ни параметры, ни даты не подбирались.

## Исполнение и учёт

Начальная покупка одинаковая:5bp fee и5bp adverse slippage; оригинальные количества net of costs. Sell5%/10% ORIGINAL shares по next regular open,5bp fee/5bp slip. Delay2 — одна дополнительная сессия. Нет продажи по сигнальному close. Акции дробные. Один pending sell, количество ограничено фактически удерживаемыми свободными акциями; проданные лоты не могут продаваться повторно. FIFO применяется к независимым lot budgets.

Каждой фактической продаже соответствует один GTC лимит actual_sale*.95, активный с последующей сессии. Gap open<=limit →open; иначе low<=limit →limit. Без RSI/MA/risk/trend условий и без full-restoration gate. Net sale proceeds зарезервированы за своим лотом; одно и то же cash не расходуется дважды. Количество покупки строго равно продаже (all-or-none); если средств с комиссией недостаточно, заявка не исполняется. В реальных сценариях cash rejections0. Дополнительных денег/плеча/short нет, полученная экономия остаётся cash, не покупает дополнительные акции.

Комиссия buy5bp; base limit touch не получает цену выше лимита. В отличие от рыночного buy в прежней E, произвольные +5bp к limit недопустимы. Поэтому стресс: intraday low должен пройти ещё5bp ниже лимита; gap price ухудшается на5bp, но не выше limit. Это чувствительность к цене/касанию, не полная модель queue/market impact. Сравнение стоимости market и limit buy потому имеет разный вид исполнения по самой природе ордеров, что может делать base touch оптимистичным.

At-open порядок: pending sale, затем старые gap-buy lots FIFO, затем intraday touches. Новый lot нельзя купить в тот же бар; акции, приобретённые позже в баре, не финансируют уже прошедшую продажу. Дивиденды ex-date по pre-open holdings; receivable не расходуется, pay dates неизвестны. Splits в окне отсутствуют; general split engine не заявляется. NAV=cash+held shares*close+dividend receivable. Незавершённый лот: net proceeds−missing shares*terminal close, не gross proceeds прибыль. Полный ledger identity: ΔNAV к B&H=sum(closed net surplus)+sum(open marked benefit)−missed dividends; проверено для всех новых сценариев.

## Основные результаты

'''+comparison+'''
## По акциям

'''+stocktable+'''
Здесь100000USD на каждую отдельную акцию; чтобы получить вклад в общий модельный портфель100000USD, делить на11. Количество также делится на11. Малые floating-point дефициты порядка1e−14 не являются реальной недостачей. Больше первоначального количества не покупается.

## Пороги и неблагоприятное исполнение

'''+st+'''
Более глубокие лимиты в этом окне меняют заполнение и удерживаемую долю cash. Это exploratory sensitivity, не оптимизация и не выбор лучшей конфигурации. Для3/7/10% основная конфигурация всё равно−5%. Fill fraction считается для фактических sales, не для неисполненных сигналов. Открытые ожидания right-censored; среднее/медиана ожидания — только completed, не unconditional lifetime expectation.

## Дополнительная сессия задержки

'''+delayed+'''
Все сочетания размеров/порогов/delay/stress, включая оба размера sale-only/E, находятся в sensitivity.csv. На каждый сценарий остаётся одинаковый44-session период, без перезапуска октября.

## Качество сигнала и временные определения

Цель качества: low-падение от actual sale fill за5/10/20 полных ПОСЛЕДУЮЩИХ сессий; sale session исключена из этих сопоставимых горизонтов. Её low и факт hit5 записаны отдельно, поскольку лимит всё равно ещё не активен. Для неполного горизонта есть observed extrema, но complete=false и итоговая метка пустая. Down5 latency и бессрочное достижение лимита — отдельные колонки. Terminal10 return не смешивается с intrahorizon hit.

Высокая цена дня фактической продажи учитывается в runup после sale-open. Для intraday buy неизвестно, был ли high до или после low: runup_before_fill_day — нижняя информация до buy-day, runup_possible_including_fill_day — возможная верхняя оценка с buy-day high. Для gap open buy дневной high после исполнения не учитывается. Future maxima/minima только outcome labels, никогда в signals, sale prices или limit creation.

## Файлы

sales.csv — полный журнал продаж; limit-orders.csv — лимиты/активность/статусы; buybacks.csv и trades.csv — исполнения; cycles.csv — все realized/censored lots; sale-quality.csv — одна каноническая выборка продаж без дублирования по чувствительности; waiting-summary.csv — доли/ожидания по акциям и сценариям; opportunity-cost.csv — ожидание/упущенный рост; daily-stock-equity.csv и daily-portfolio-equity.csv — NAV; comparison.csv /stock-results.csv /sensitivity.csv — результаты.

E не переизобретена: архивный inputs/pr9-audit.cjs заново исполняется в Node, summary сверяется с inputs/strategy-economics.csv. Исходные E trades/daily equity тоже сохранены read-only в inputs/. Здесь количество completed E cycles не подменяется числом частичных cash-limited buybacks.

Результаты зависят от короткого падающего окна и уже изучавшихся сигналов. Независимая out-of-sample эффективность не доказана; фундаментальные/production snapshots не создавались. Длинная история не заявляется. Код изолирован от application/RiskEngine, сеть для расчёта не нужна.
''')
    (R/'validation.md').write_text('''# Validation / воспроизводимость

43 Python checks passed:2 существующих main теста +30 тестов исполнения +11 межреестровых проверок.0 failures;1 deprecation warning окружения anyio/pytest10. Проверены next-open/extra delay, независимые лоты/free shares, no same-bar rebuy, actual-sale limit, touch/gap/stress, no borrowing/extra shares, segregated cash, fees, GTC, censored horizons, ex-dividend entitlement, future-prefix invariance, complete NAV identities, input hashes и E replay.

Node replay исходной E сверил55 stock/config summaries с PR9 и B&H с новым движком. Original production signals неизвестны, не HOLD; inputs read-only snapshots не менялись. Сигналы используются как опубликованные строки, не вычисляются заново. Биржевой календарь сохранён из PR9,44session с verified DST1/2Nov; signal available_at после close — исходное непроверенное допущение, а не аттестованный price feed.

Node24.19.0, Python3.12; runtime calculations толькоstdlib+Node. Для тестов pytest9.2.0 установлен отдельно в /tmp, production requirements не менялись. Воспроизведение из корня:

~~~bash
PYTHONDONTWRITEBYTECODE=1 python -m research.fixed_5pct_buyback.run
PYTHONDONTWRITEBYTECODE=1 python -m research.fixed_5pct_buyback.report
python -m pytest -q -p no:cacheprovider tests research/fixed_5pct_buyback
~~~

Не скачать новые prices вместо входов: frozen source commit7135c2bdc0653986d93dfcfc66b202a6fb2f741e. Повторяемость после GitHub-публикации фиксируется отдельным verification.json. SHA manifest исключает самого себя. Контроль исходных source hashes выполняется каждым run.

НЕ доказаны: original PIT publication/vintages, реальная достижимость лимитных исполнений/очередь/частичные объёмы, production сигналы/позиции/заявки, историческая полнота2021–2026 для этой же последовательности сигналов. Рыночная стоимость cash открытого лота не считается realized profit; низкая доля ожидания по закрытым циклам не оценивает незавершённые. Никаких merge/deploy/production/order действий.
''')
if __name__=='__main__':main()
