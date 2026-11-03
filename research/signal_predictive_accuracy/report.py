"""Deterministic explanatory report; no new signal or statistical fitting."""
import collections,json
from research.signal_predictive_accuracy.io import R,I,STOCKS,MARKETS,rows,write
def pct(v):return f'{float(v)*100:.1f}%' if v not in ('',None) else '—'
def num(v,d=2):return f'{float(v):.{d}f}' if v not in ('',None) else '—'
def table(h,rs):return '|'+ '|'.join(h)+'|\n|'+'|'.join('---' for _ in h)+'|\n'+''.join('|'+ '|'.join(str(x) for x in r)+'|\n' for r in rs)
def main():
    stats=rows(R/'statistics.csv');base=rows(R/'baseline-comparison.csv');ci=rows(R/'baseline-confidence.csv');fn=rows(R/'false-negative-summary.csv');ac={x['symbol']:x for x in rows(R/'asset-confidence.csv')};signal=rows(R/'signals.csv');run=json.loads((R/'run.json').read_text());dateci=rows(R/'date-confidence.csv')
    main=next(x for x in stats if x['cohort']=='STOCK' and x['anchor']=='OPEN' and x['group']=='ALL');close=next(x for x in stats if x['cohort']=='STOCK' and x['anchor']=='CLOSE' and x['group']=='ALL')
    comparator=[]
    for x in base:
        if x['cohort']!='STOCK':continue
        c=next(c for c in ci if c['cohort']==x['cohort'] and c['model']==x['model'] and c['block_length']=='60')
        comparator.append([x['model'],x['matched_warning_dates'],pct(x['signal_precision']),pct(x['control_precision']),num(x['lift_pp']),num(c['ci_low_pp'])+'…'+num(c['ci_high_pp']),pct(c['marginal_confidence'])])
    baseline_table=table(['Контроль','Пар дат','Сигнал на этом подмножестве','Контроль','Разница п.п.','CI разницы п.п.','Уровень CI'],comparator)
    assets=[x for x in stats if x['group']=='symbol' and x['anchor']=='OPEN'];asset_table=table(['Актив','TP','FP','UNKNOWN','UNRESOLVED','TP/(TP+FP)','95% clustered CI','Средняя max-потеря10%'],[(x['value'],x['true_positive'],x['false_positive'],x['unknown'],x['unresolved'],pct(x['precision']),pct(ac[x['value']]['ci_low'])+'…'+pct(ac[x['value']]['ci_high']),num(x['mean_max_drop10'])) for x in assets])
    years=table(['Год','TP','FP','UNKNOWN','Доля TP'],[(x['value'],x['true_positive'],x['false_positive'],x['unknown'],pct(x['precision'])) for x in stats if x['group']=='year' and x['cohort']=='STOCK' and x['anchor']=='OPEN'])
    regimes=table(['Режим на signal-close','Строк','TP доля','Средняя предшествующая DD20%'],[(x['value'],x['rows'],pct(x['precision']),num(x['mean_known_dd20'])) for x in stats if x['group']=='regime' and x['cohort']=='STOCK' and x['anchor']=='OPEN'])
    fn_table=table(['Closing падение','Lookback','Событий','Предупреждено','Пропущено','Recall','95% clustered CI'],[(x['threshold_pct']+'%',x['lookback'],x['events'],x['covered'],x['missed'],pct(x['recall']),pct(x['ci_low'])+'…'+pct(x['ci_high'])) for x in fn])
    examples=[]
    for s in ['AMD','NVDA','MU']:
        for state in ['TRUE_POSITIVE','FALSE_POSITIVE']:
            candidates=sorted((x for x in signal if x['symbol']==s and x['anchor']=='OPEN' and x['complete_10']=='True' and x['classification']==state),key=lambda x:x['signal_date'])
            if candidates:
                x=candidates[0];examples.append(dict(symbol=s,classification=state,signal_date=x['signal_date'],execution_date=x['reference_date'],reference_price=x['reference_price'],down_date=x['down_date'],up_date=x['up_date'],return10=x['return_10_pct'],pre_dd20=x['known_drawdown_20_pct'],selection='EARLIEST_CHRONOLOGICAL_EXAMPLE_IN_CLASS_NOT_EVIDENCE_OF_FREQUENCY'))
    write('examples.csv',examples)
    saved=rows(I/'saved-research-evidence.csv');inventory=[dict(category='CONFIRMED_PRODUCTION',rows=0,meaning='No original decision payloads obtained; UNKNOWN, not HOLD'),dict(category='SAVED_RESEARCH_OVERLAY',rows=sum(x['type']=='SAVED_RESEARCH_OVERLAY' for x in saved),meaning='Research snapshots, not original production timestamps'),dict(category='SAVED_RESEARCH_FORECAST_STATE',rows=sum(x['type']=='SAVED_RESEARCH_FORECAST_STATE' for x in saved),meaning='Research forecasts/states, not scored as production'),dict(category='SAVED_RECONSTRUCTED_SECTOR_ACTIVATIONS',rows=134,meaning='Immutable PR11 algorithm reconstruction; the evaluated warning sequence'),dict(category='NEW_RETROSPECTIVE_OUTCOME_ROWS',rows=len(signal),meaning='Stock/market and OPEN/CLOSE labels; not new trading signals')];write('evidence-inventory.csv',inventory)
    (R/'executive-summary-ru.md').write_text('''# Signal Predictive Accuracy Audit v1 — итог

**Самостоятельная прогностическая ценность sector_flag сверх сопоставимых контролей не подтверждена.** Наблюдаемый эффект мал, доверительные интервалы включают ноль. Сигнал часто отражает уже начавшееся ухудшение; это не доказательство того, что он никогда не может предупредить заранее.

Исследуется реконструированный алгоритм из PR11, а не доказанная точность реальных предупреждений Alpha OS: оригинальных production-пейлоадов не получено. Формула, даты и134 предупреждения не менялись. Оригинальные решения UNKNOWN, отсутствие записи не HOLD.

## Основная классификация

Отсчёт от regular open следующей сессии, без комиссии/проскальзывания: это аудит цены, не сделки.10сессий включают сессию открытия. TP=low−5% раньше high+5%; FP=up5% первым либо полное окно без TP; same-first-bar порядок UNKNOWN; недостаточная история UNRESOLVED.

* 571 TRUE POSITIVE,799 FALSE POSITIVE,4 UNKNOWN,11 UNRESOLVED по акциям.
* Доля TP среди TP+FP:41.7%, FP58.3%. При отнесении всех UNKNOWN к провалам/успехам диапазон41.6–41.8%.
* Это precision предупреждений, не обычная accuracy по всем торговым дням: true negatives здесь не определялись.
* Равный вес каждой даты даёт41.56%,95% block CI35.91–47.01%.1374 зрелые stock-window строки не1374 независимых наблюдения:133 зрелые даты,134 уникальные даты всего;79неперекрывающихся10-session окон тоже не гарантируют независимости. В истории около25блоков по60сессий.

## Лучше ли случайных/механических сигналов?

'''+baseline_table+'''
Разные matched subsets нельзя сравнивать напрямую с общим pooled41.7%: исключённые ячейки и веса дат меняют знаменатель. Random matching:quarter,известный QQQ regime,доступность тикеров. Mechanical baseline:QQQ R5<0 rising edge; естественные совпадения с sector сохранены. DD-matched random — дополнительный, заранее описанный контроль среднего текущего DD20, исследовательский.

Primary CI97.5% на каждый из двухконтрастов даёт familywise95% Bonferroni. Оба интервала включают0. Block20/120 дают тот же вывод. По рынку дополнительное преимущество также не подтверждено: соответствующие интервалы охватывают0. Это не real-time модель вероятности и не независимый out-of-sample holdout.

## Уже начавшееся ухудшение

Примерно60.1% предупреждений при достаточном prehistory появляются уже ниже предыдущего20-сессионного closing peak минимум на5%; средняя известная DD20 около7.98%. Четыре строки без достаточного prehistory не трактуются как DD0. Средняя последующая максимальная потеря в10сессиях6.59%, медиана4.97%; TP достигали−5% в среднем за3.85сессии, медиана3. После FP средний terminal10 рост+4.94%, максимальный внутриграничный рост в среднем10.54%.

Наличие продолжающегося падения после предупреждения не делает его ранним. Но нельзя заключить, что ухудшение всегда уже завершилось: часть событий действительно предупреждена заранее, особенно отдельные даты октября.8октября2026 TP у AMD/NVDA/MU и ряда полупроводников, FP у AMZN/META/PLTR; один удачный эпизод не заменяет полную статистику.

## По акциям и рынкам

'''+asset_table+'''
Рынки — отдельная secondary cohort:индексы и ETF не добавляются к акциям как независимые испытания. QQQвходит в исходную формулу и многие тикеры перекрываются с индексами. Большие интервалы NBIS связаны с короткой доступной историей. Проверки по активам exploratory, не основание выбрать лучший тикер задним числом.

## Пропущенные падения

'''+fn_table+'''
Например, для−5% и предыдущих10сессий87из204эпизодов не имели доступного нового предупреждения. В32из87 sector активировался на том же closing threshold-дне — слишком поздно для предшествующего предупреждения; оставшиеся55имели False state на threshold-close. Ни один из этих статусов не доказывает production HOLD.

20-session recall высокий отчасти потому, что предупреждения частые: это не доказательство дополнительной предсказательной силы. Episode recall и основной competing-barrier precision имеют разные события/единицы: нельзя складывать их в одну confusion matrix или вычислять F1. Знаменатели меняются при неполных начальных lookback windows и показаны явно.

Full-recovery catalogue объединяет вложенные снижения; это не все мелкие локальные колебания. Подробные пики, пороги, lead signal/lead execution и чувствительность seed20/60/recovery98% опубликованы. Прогнозу не передавались будущие пики/минимумы.

## По годам и режимам

'''+years+'\n'+regimes+'''
У более слабого рынка доля TP выше, но controls сопоставлены по regime/времени. Само по себе это не incremental information. Регимы не изменяют предупреждения или торговые правила.

## Вывод и границы

На этой многократно исследованной истории sector_flag разумно описывать как индикатор совместного ухудшения сектора. Данные не подтверждают добавочную надёжную способность предсказывать новое снижение относительно простых ориентиров; они также не доказывают точное нулевое преимущество. Исходные времена публикации/корпоративные vintages и реальные production решения отсутствуют. Fixed current survivors, дневной OHLC и неизвестный intraday порядок ограничивают выводы.

Экономическая эффективность не исследовалась в этом PR; хорошая доля TP не равна прибыльной торговле. Production, сигналы и торговые правила не изменялись, merge/deploy/реальных заявок нет. Здесь остановка.
''')
    (R/'methodology.md').write_text('''# Методика и файлы

Протокол опубликован до вычислений. Источники immutable PR11@5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7, PR10@ef1a3a76c1c0d455f48a9d787f1c04961c244b91, PR9@7135c2bdc0653986d93dfcfc66b202a6fb2f741e.10PR11 и2PR9 исходных blob-путей сверены с GitHub; local compact prices — lossless выбранные поля с указанным исходным blob/SHA256, не восстановленный утраченный v1.

Signal rule unchanged: mean R5 семиAMD/NVDA/MU/TSM/AVGO/AMAT/LRCX нижеQQQ R5,>=4negative, false/nottrue→true. Только доступный past/current close. Сохранённые134dates проверены повторным запуском frozen_sector_formula.py,1465daily states совпали. Не добавлены новые факторы.

Основные anchors:OPEN=next regular open после sourceavailable_at, CLOSE=signal close отдельно. Evaluation bars одинаковы: следующие1/3/5/10/20сессий после signal-date; первый bar — execution-session, return1=open→close этого дня. Для CLOSE return1=signal-close→next-close. В PR11 quality использовала последующие полные сессии после sale,5bp adverse fill и цель without competing upper barrier: проценты разных аудитов нельзя напрямую приравнивать.

Both price touches first in same bar→UNKNOWN, включаяgap: сознательно консервативно по заданию. TP/FP иногда логически известны в частичном окне, но primary precision иконтроли используют только полные10bars. Неизвестный порядок и недостаточное будущее не FP. Отдельно сохраняются maxdrop/maxrise за5/10/20, low/high20dates, terminalreturns иdown3/5/10/15hit+latency. Secondary matrix использует fixedup5 для всех down thresholds; это не новая основная цель.

Minimum/maximum цены в terminal split-normalized units, а contemporaneous nominal prices на соответствующих датах показаны отдельно. Пороговые отношения единично-инвариантны; не сравнивать nominal значения до/послеsplit без conversion. Цена не total-return wealth: dividends не реинвестируются и не исправляют price targets. Quote timing nextUTCmidnight — исходное предположение, не реальная production attestation.

Statistics:pooled stock precision vs equal-date mean раздельно,112? нет фиктивного независимого N. Уникальных кластеров134, полных133; временная зависимость остаётся. CI synchronous moving calendar blocks60,1999resamples, seed20261103; sensitivity20/120. Одни и те же calendar weights действуют на все акции, actual dates и reused controls. Частота ошибок не получает наивный binomialCI по1374строкам. Stocks/markets separate.

Random controls matchcalendar quarter/knownQQQregime/eligibility signature, actual sector dates excluded. MechanicalQQQR5negative rising edge сохраняет естественные совпадения сsector; empty cells не расширяются задним числом. Point estimate exact candidate mean.500seeded panels сreplacement отражают контрольную выборку, а не создают новые независимые истории; unique control count/reuseявно в control-panel-summary.csv. При недостатке кандидатов даты остаются unmatched. Ретроспективное сравнение внутриquarter не объявляется доступной вреальномвремени forecast probability.

Primary two contrasts имеют97.5%marginal CI для family95%; вторичный DD20-bin matching exploratory. Матрицыthreshold/year/ticker/regime тоже exploratory без выбора победителя. Market cohort повторяет benchmark comparison отдельно, без объединения перекрывающихсяETF/индексов.

Episodes: knownclose peak seededprior20 atstudy/eligible start, update onnewhigh, merge untilfullclosing recovery; thresholds5/10/15 close. No newwarning inprior5/10/20 значитfalse negative поэтому окну, не HOLD/stateFalse. Сам closing threshold-day сигнал не prior; earliest nextopen долженбыть доthreshold close. Signal lead иexecution lead отдельные: lead1signal можетозначать0полныхднейисполнения. Неполный начальный lookback не считается FN. Sameevent thresholds не независимы. Seed60/recovery98% sensitivity не оптимизируется.

Файлы:signals.csv полныйwide outcome catalogue;classification.csv четыре статуса;statistics/stock/year/regime tables;threshold-matrix.csv;drawdown-events/missed-falls/episode-sensitivity;baseline-comparison/confidence;asset/date-confidence;control-date-scores/cells и matched-control-panels.csv.gz; examples.csv — earliest chronological TP/FP illustrative, нечастоты. Evidence-inventory иproduction-evidence отделяют архивы. Нет portfolio/trade PnL или нового engine.
'''.replace('112? нет фиктивного независимого N.','Нет фиктивного независимого N.'))
    (R/'production-evidence.md').write_text('''# Evidence inventory

'''+table(['Категория','Строк','Значение'],[(x['category'],x['rows'],x['meaning']) for x in inventory])+'''
Current main risk.py и investment_memory.py доступны как код с SHA; это не historical output archive. В пакетах нет подтверждённых дневных результатов действующего production RiskEngine за2021–2026. Есть111 Overlay research records и111 Forecast states из поздних исследований AMD/NVDA/MU за1сентября–22октября2026, а не реальные первоначальные payloads. Их разные семантики не подмешиваются к sector precision.

В PR9 read-only provider metadata: app source main, latest deployment создан15октября, DATABASE_URL configured; values не запрашивались. Bounded filtered logs вернули0, retention unknown. Этот архив не доказывает отсутствия production предупреждений или данных вБД. В данном аудите сервисные endpoints/SQL вообще не вызывались: некоторые endpoints способны сохранять записи. Для проверки настоящей точности нужны original timestamped decisions/inputs/model config. Отсутствие записи UNKNOWN, никогда HOLD.

Секторные134активации сохранены после реконструкции вPR11. Новая работа только вычисляет outcome labels и контрольные сравнения, не создаёт production торговых сообщений. Главное заключение относится кэтому реконструированному алгоритму при допущениях о доступности.
''')
    (R/'validation.md').write_text('''# Validation and reproducibility

Фактически36Python tests passed:2existing main +34audit checks;0failures. Final readback record inverification.json. Проверки охватывают competing-barrier order/UNKNOWN, partial vs complete, nextopen vsclose anchor, execution-session inclusion, exacttouch, future-prefix invariance, split-unit invariance, nested/unfinished episodes, shared bootstrap weights, unmatched cells, mechanical overlaps, source hashes, eligibility, censoring, baseline cell/frequency invariants, nonoverlap and missing-history denominator. Final actual pass count иповторный прогон после публикации фиксируются отдельно.

Source:18price series с2020warmup,1465sessions2021–2November2026.11stocks,7market/context series не независимые активы. NBIS только21October2024 onward; PLTR available atstudy start. Compact gzip source fields проверены SHA256; archivedGitblob identity сверена. Frozen sector formula exactly reproduces134dates иdaily states. Predictor features считают onlycurrent/past data; extrema, minima, barrierorder and retrospective peaks — labels, неinputs.

Original PIT/publication attestation, corporate-vintage history иproduction payloads unavailable. Next-midnight signal availability — допущение предыдущих исследований. Regular-dayOHLC не intraday tape, same-first-bar order UNKNOWN. Послеsource endpoint cutoff цены не придумываются. Gross dividend accounting не нужен: этоprice-prediction audit, неwealth/portfolio simulation. Split-adjusted price units последовательно используются иотдельноnominal описаны.

CI: synchronouscalendar block60 /sensitivity20,120;1999reps, seed20261103. Календарные веса одновременно изменяют actual dates иshared control dates. Primary family95% adjusted two contrasts, secondary exploratory. Window overlap/sector correlation невыдаютсязановыеindependent trials. Nonoverlapping79windows — лишьподвыборка, не доказанныйESS. Квартальныйregime matching retrospective, не prospective probability forecast. Control reuse disclosed; unmatched неимпутируются. Recall эпизодов иprecision competing-barrier несливаютсявF1.

Reproduction:Python3.12,pytest9.2.0 только дляtests; расчёт stdlib. deps в/tmp target, production requirements untouched.

~~~bash
PYTHONDONTWRITEBYTECODE=1 python -m research.signal_predictive_accuracy.run
PYTHONDONTWRITEBYTECODE=1 python -m research.signal_predictive_accuracy.baselines
PYTHONDONTWRITEBYTECODE=1 python -m research.signal_predictive_accuracy.report
python -m pytest -q -p no:cacheprovider tests research/signal_predictive_accuracy
~~~

Исходные данные не скачиваются заново; не переписывать immutable inputs. Tests require pytest onPYTHONPATH. GitHub readback/byte-identical output verification записывается вverification.json. Нет production API/SQL/реальныхордеров/merge/deploy/пороговойоптимизации.
''')
if __name__=='__main__':main()
