"""Russian investor conclusions; no parameter selection or model fitting."""
import csv,json,statistics
from research.historical_sell_buyback.prepare import R
def rows(n):return list(csv.DictReader((R/n).open()))
def n(x,d=2):return f'{float(x):,.{d}f}' if x not in ('',None) else '—'
def table(h,xs):return '|'+ '|'.join(h)+'|\n|'+'|'.join('---' for _ in h)+'|\n'+''.join('|'+ '|'.join(str(x) for x in r)+'|\n' for r in xs)
def label(x):
    if x['mode']=='PR9_ORIGINAL':return 'E Прежнее восстановление '+str(int(float(x['fraction'])*100))+'%'
    if float(x['fraction'])==0:return 'A Buy & Hold'
    return ('B Только продажи ' if x['mode']=='sale_only' else 'C/D SELL/BUY−5% ')+str(int(float(x['fraction'])*100))+'%'
def main():
    ps=rows('portfolio-comparison.csv');ys=rows('annual-performance.csv');ss=rows('sensitivity.csv');stocks=rows('stock-performance.csv');cov=rows('data-coverage.csv');quality=rows('signal-quality-all-eligible.csv');lots=rows('lots.csv');run=json.loads((R/'run.json').read_text())
    mainkeys=['limit_F0_T0.05_D1_S0_C5','sale_only_F0.05_T0.05_D1_S0_C5','sale_only_F0.1_T0.05_D1_S0_C5','limit_F0.05_T0.05_D1_S0_C5','limit_F0.1_T0.05_D1_S0_C5']
    comp=[]
    for v in ['RESERVED11','COMPARABLE10']:
        comp.append('## '+v+'\n\n'+table(['Стратегия','Конечный капитал USD','Δ к B&H USD','CAGR %','MaxDD %','Vol %','Sharpe rf0','Средний cash/NAV %'],[(label(x),n(x['final_equity']),n(x['excess_vs_buyhold']),n(x['cagr_pct']),n(x['maximum_drawdown_pct']),n(x['volatility_pct']),n(x['sharpe']),n(float(x['average_cash_fraction'])*100)) for x in ps if x['variant']==v]))
    def year_table(v,metric):
        rr=[]
        for year in ['2021','2022','2023','2024','2025','2026','ALL']:
            rr.append([year]+[n(float(next(x for x in ys if x['variant']==v and x['year']==year and x['scenario']==key)[metric])*(100 if metric=='average_cash_fraction' else 1)) for key in mainkeys])
        return table(['Год','B&H','SELL5%','SELL10%','BUY−5%,size5%','BUY−5%,size10%'],rr)
    mature=[q for q in quality if q.get('complete_10')=='True'];false=sum(q['down5_10']=='False' for q in mature);growth=sum(float(q['terminal_10_pct'])>0 for q in mature)
    qsummary=f'{len(mature)} зрелых потенциальных исполнений; {false} ({false/len(mature)*100:.2f}%) без low-падения5% за10 следующих полных сессий; {growth} ({growth/len(mature)*100:.2f}%) с положительным terminal10 return.'
    lotinfo=[]
    for size in [.05,.1]:
        xs=[x for x in lots if x['scenario']==f'limit_F{size}_T0.05_D1_S0_C5'];closed=[x for x in xs if x['status']=='CLOSED'];wait=[int(x['wait_sessions']) for x in closed]
        lotinfo.append([str(int(size*100))+'%',len(xs),len(closed),len(xs)-len(closed),n(len(closed)/len(xs)*100),n(statistics.mean(wait)),n(statistics.median(wait))])
    lots_table=table(['Размер','Продаж','Закрытых','Открытых','Заполнено %','Среднее ожидание','Медиана'],lotinfo)
    decomposition=table(['Стратегия10сопоставимых','Закрытая чистая экономия','Открытый marked benefit','Пропущенные дивиденды','ΔNAV с B&H'],[(label(x),n(x['realized_savings']),n(x['open_marked_benefit']),n(x['missed_dividends']),n(x['excess_vs_buyhold'])) for x in ps if x['variant']=='COMPARABLE10' and x['mode']=='limit' and float(x['fraction'])>0])
    robust=[]
    for v in ['RESERVED11','COMPARABLE10']:
        for f in [.05,.1]:
            xs=[x for x in ss if x['variant']==v and x['mode']=='limit' and float(x['fraction'])==f];robust.append([v,int(f*100),len(xs),n(min(float(x['excess_vs_buyhold']) for x in xs)),n(max(float(x['excess_vs_buyhold']) for x in xs)),sum(float(x['excess_vs_buyhold'])>0 for x in xs)])
    robust_table=table(['Выборка','Размер %','Сочетаний','Мин ΔB&H','Макс ΔB&H','Превосходят B&H'],robust)
    (R/'executive-summary-ru.md').write_text('''# Historical SELL / BUY−5% — итог

**Экономического преимущества по конечному капиталу за весь период не обнаружено.** За2021–2ноября2026 обе фиксированные конфигурации существенно уступили Buy & Hold в обеих заранее описанных выборках. Просадка уменьшилась ценой значительного пропущенного роста. Короткий положительный результат октября из PR10 не обобщился на длинную историю.

Начальный капитал100000USD. Только непрерывный тест: ежегодных сбросов позиций, cash, лотов и лимитов нет. Основная ставка издержек5bp/5bp, original rules без подгонки. Протокол опубликован до вычислений. Контроль PR10:44 sector states,4 даты,15 файлов результатов побайтно и66 адаптированных кейсов совпали до длинного запуска.

'''+ '\n'.join(comp)+'''
RESERVED11:11 одинаковых денежных резервов1/11. Десять доступны4января2021; NBIS-резерв остаётся cash0% до21октября2024. COMPARABLE10:только десять акций, торговавшихся с начала, равные1/10, без новых компаний. Это разные заранее объявленные политики; поздний вход не финансируется продажей старых акций. Обе выборки выбраны из сегодняшних survivors: survivorship/selection bias НЕ устранён и полная исторически нейтральная вселенная не заявляется.

## Ответы на шесть вопросов

1. **Преимущество за весь период? Нет по заданному критерию NAV.** В сопоставимой выборке капитал631370USD у B&H против283299USD у5% и133841USD у10%. CAGR37.20% против19.57%/5.13%. MaxDD53.04% против41.89%/31.45%: защита есть, но не бесплатна.
2. **Когда лучше/хуже?** В COMPARABLE10 обе конфигурации лучше по годовой доходности в2022, хуже в2021/2023/2024/2025/2026YTD. В RESERVED11size5% также чуть лучше в2026YTD33.99% против32.78%, но это не компенсирует предыдущие годы. Годовые доли cash/просадки опубликованы ниже и в CSV.
3. **Продажа или выкуп?** Одни продажи постепенно полностью ликвидируют позиции: нет минимального core-floor в замороженном правиле, а число срабатываний велико. Без новых покупок капитал сопоставимой выборки113709/109110USD. Выкуп возвращает часть участия в росте, добавляя примерно169590/24731USD к sale-only, но не догоняет B&H. Полное превосходство короткого sale-only окна тоже не обобщилось. E из PR9 показана отдельно, с единственным изменением периода, и остаётся близка к B&H; это не полный production/fundamental replay.
4. **Потери от ложных предупреждений?** Главная причина — ранние низкие sale prices и GTC-лимиты, которые не достигаются годами. Открытые лоты сохраняют дефицит акций, хотя закрытые циклы математически дают положительную cash-экономию. Нельзя отбирать только завершённые циклы или считать gross proceeds прибылью.
5. **Издержки/задержки?** Ни один из64 сочетаний размеров,3/5/7/10% target, delay1/2, base/strict fills и5/10bp costs не превзошёл соответствующий по издержкам B&H ни в одной выборке. Это устойчивость отрицательного результата в данной исследованной истории, не универсальная теорема.
6. **Достаточно ли для движения к production? Нет.** Текущая конфигурация не показала требуемого преимущества; original PIT vintages, реальная достижимость лимитов и нейтральная вселенная не подтверждены. Результаты пригодны как отрицательный исследовательский вывод и описание компромисса risk/return, не как основание внедрения. Параметры не изменялись и новая стратегия не создавалась.

## Годовая доходность %, COMPARABLE10

'''+year_table('COMPARABLE10','return_pct')+'''
## Годовая максимальная просадка %, COMPARABLE10

'''+year_table('COMPARABLE10','maximum_drawdown_pct')+'''
## Средняя доля cash/NAV %, COMPARABLE10

'''+year_table('COMPARABLE10','average_cash_fraction')+'''
Все годы связаны непрерывным NAV. Annual MaxDD рассчитывается внутри года от peak, начиная с NAV предыдущего конца года; это не reset позиции. Cash/NAV — средняя доля ликвидного cash, отдельно есть fraction of days cash>0; маленький surplus также даёт день cash>0, поэтому эти показатели не взаимозаменяемы. Dividend receivable учитывается отдельно, не расходуется.

## Закрытые и незавершённые лоты

'''+lots_table+'\n'+decomposition+'''
Лоты в таблице считаются по всем11 акциям, независимо от масштаба capital slots; экономическая декомпозиция — для портфеля100000USD из10. Identity: ΔNAV = realized net savings + open marked benefit −missed dividends. Отрицательный marked benefit — реальная opportunity cost отсутствующих акций относительно удержания по terminal price, но не завершённая торговая прибыль/убыток. Никаких принудительных выкупов в конце нет.

## Качество предупреждений

'''+qsummary+'''
Это диагностическая one-unit когорта всех доступных акций, даже если реальная модель уже продала весь пакет. Она явно отделена от position-selected фактических модельных sales. 11 последних сигналов2ноября не имеют следующей цены исполнения внутри окна и не считаются false/no-loss. Конец окна может цензурировать20-session labels или бессрочное ожидание. 134 общих дат по связанным акциям — не1374 независимых испытания. Отсутствие production-записи не HOLD; все сигналы ретроспективно восстановлены по замороженной формуле.

Regime analysis: QQQclose vsMA200 иR20, label только предыдущего известного close, без влияния на сделки. В этой выборке средняя дневная доходность C/D ниже B&H во всех трёх метках; нельзя просто объявлять любую BEAR-сессию выигрышной. Преимущество годового2022 не равнозначно универсальной regime-protection. Условные disconnected days — не самостоятельная торгуемая стратегия.

## Устойчивость

'''+robust_table+'''
Полный sensitivity.csv не выбирает оптимальный target. Средние времена ожидания приведены только для завершённых выкупов и смещены исключением незавершённых; open-lots.csv обязателен для интерпретации. Внутридневной порядок high/low неизвестен; диапазоны runup не выдаются за установленный путь. Исходные исходы уже неоднократно исследовались, поэтому это не untouched independent holdout.

Источникraw Yahoo, corporate events и SHA256 сохранены. Split-adjusted units используются последовательно; nominal prices/quantities и adjustment factors выводятся отдельно, NAV и causal-return invariance проверены. Сплиты не создают дополнительную экономическую прибыль. Pay dates/удержания ADR/налоги не получены: dividends gross начисляются ex-date как receivable, без reinvestment и процентов. Все расчёты hypothetical, при допущениях о публикации close следующей UTCполуночью и OHLC execution. Реальные торговые рекомендации/production не изменены. Остановка после Draft PR, без merge/deploy/заявок.
''')
    (R/'validation.md').write_text('''# Validation / evidence limits

## Контроль и данные

PR10 snapshots37files с SHA256. До длинного теста control.py подтвердил4 даты (1сентября,14сентября,8октября,2ноября2026),44daily sector states,15generated artifacts byte-for-byte,66 адаптированных engine cases. Новый длинный Yahoo pack также совпал по2730 overlapping bars OHLC и датам. Gate failure прерывает процесс до long economics.

Formula: seven fixed semis AMD/NVDA/MU/TSM/AVGO/AMAT/LRCX; five-session returns;>=4negative AND equal mean<QQQreturn5. Полнота7+QQQобязательна; prev-state хранится через warmup, true transitions, не ежедневные повторы. Контекст SOX/SOXX/SMH/SPY/indices/VIX не входит в сигнал. Future suffix mutation/invariance проверяется.

Provider raw includes OHLCV, actions, source URL, retrieval time, firstTradeDate and hashes; регулярная сессия includePrePost=false. XNYS1465sessions, DST/holidays и eligibility проверены; missing invested-session quote запрещает расчёт, не заполняется forward fabricated price. NBIS только21октября2024, с issuer/exchange reference, без suspended YNDX splice. Прогрев2020; PLTR с30сентября2020, доступна на старте2021.

## Корпоративные действия и единицы

OHLC provider split-adjusted, без использования dividend-adjusted adjclose. Внутренний ledger в одной terminal share unit, с counterpart nominal shares/prices. Для исторического дня factor=product splits AFTER day: nominal price=adjusted price×factor, nominal shares=normalized shares/factor. Это восстановление единиц, не торговый признак. Экономический return5 эквивалентен nominal return с ONLY splits уже effective между двумя датами;35 split-crossing windows проверены. Дополнительная метаморфная проверка пересчёта всех цен/количеств в4раза сохраняет NAV. Для лота черезsplit actual current limit и quantity меняются обратно/прямо пропорционально, стоимости совпадают.

Yahoo dividend events интерпретируются в той же split-normalized unit, gross entitlement наex-date поpre-open shares. Нет выдуманных pay dates, withholding/tax/ADRfees или dividend reinvestment. Нерасходуемый receivable включён в NAV и отдельно в долях портфеля. При разрешённом exact-quantity buyback net proceeds сами покрывают target и комиссию; receipts не нужны для финансирования. Первичные исходные корпоративные vintages не аттестованы независимо.

## Прогоны

Тесты:30 inherited PR10 execution checks направлены на исторический adapter без копирования логики; новые проверки control/raw/calendar/eligibility/splits/nominal value/costs/annual continuity/NAV/production categories/prior-policy adapter. Финальный прогон:54passed (2main+30inherited execution+22historical/data/accounting checks),0failures,1anyio deprecation warning. GitHub read-back — verification.json. Старые203 tests из иной PR-цепочки не заявляются. pytest deprecation warning anyio относится к окружению.

PR9 restoration policy воспроизведена в optional E: source unchanged кроме START2026-09-01→2021-01-01. Проверка source text ровно одна замена; CSV prior-* и original source hashes опубликованы. Это legacy tactical policy, не полный DecisionEngine с придумыванием отсутствующих historical fundamentals. Стоимость риска E почти как B&H, поэтому её похожая доходность не означает хорошую protection.

## Неподтверждённое

Нет original publication feeds/attested timestamp/vintages, production decisions/orders/holdings. Next-midnight availability — сохранённое модельное допущение. Exact real queue/limit fills/volume impact не подтверждены; base touch и strict5bp penetration/gap-cap stress опубликованы. Calendar availability известна на дату, будущие highs/lows — только execution assumptions/outcome labels; не predictors. Gross open proceeds не profit. Весь current-survivor universe biased, no delisted panel. Нельзя считать multi-use2021–2026 независимым holdout. Метрики rf0%, vol sqrt252/sample std, CAGRactual calendar, periods<year CAGRblank.

## Offline reproduction

Python3.12, Node24, pytest9.2.0, exchange-calendars4.13.2. Fetch_data.py только для НОВОГО snapshot, не повторять для идентичности. Все остальные шаги читают замороженные inputs.

~~~bash
python -m research.historical_sell_buyback.control
python -m research.historical_sell_buyback.prepare
python -m research.historical_sell_buyback.run
python -m research.historical_sell_buyback.prior
python -m research.historical_sell_buyback.quality
python -m research.historical_sell_buyback.report
python -m pytest -q -p no:cacheprovider tests research/historical_sell_buyback
~~~

Dependencies устанавливаются в отдельный /tmp target, PYTHONPATH включает root и target; production requirements не изменялись. Никаких production calls/SQL/real orders/merge/deploy/force push.
''')
    (R/'data-coverage.md').write_text('# Data coverage\n\n'+table(['Актив','Первая quote','Eligibility','Последняя','Строк исследования'],[(x['symbol'],x['first_provider_date'],x['study_entry'],x['last'],x['study_rows']) for x in cov])+'''\nNBIS current business eligibility подтверждена Nasdaq announcement18октября2024 (data/eligibility-evidence.json); baseline regular-session purchase21октября, не9am quotation time. Точные actual IPO meta firstTradeDate есть в provider manifest; не подменяет distinct post-restructuring eligibility. CSV no quotes invented. Context series никогда не подменяют фиксированную SEMIS+QQQ формулу.\n''')
if __name__=='__main__':main()
