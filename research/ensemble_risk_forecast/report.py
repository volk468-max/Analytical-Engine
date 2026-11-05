"""Render Russian report from saved result tables; no model selection."""
import csv,json
from study import OUT,VOTES,MODELS

def read(name):
    with (OUT/(name+'.csv')).open() as f:return list(csv.DictReader(f))
def num(x,d=4):return f'{float(x):.{d}f}' if x not in ('',None) else 'NA'
def pct(x):return num(float(x)*100,2) if x not in ('',None) else 'NA'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'
def main():
    ms=read('metrics');ag=read('agreement');co=read('comparisons');ec=read('economic-summary');ad=read('added-value');cc=read('error-correlation')
    ref=lambda r:r['target']=='touch' and r['horizon']=='20' and r['threshold_pct']=='10.0'
    m=[r for r in ms if ref(r) and r['dimension']=='ALL'];a=[r for r in ag if ref(r) and r['dimension']=='ALL' and r['kind']=='count']
    text='''# Alpha OS — Ensemble Risk Forecast v1

**RESEARCH ONLY. NO-GO для внедрения и заявления о подтверждённом преимуществе.**
Ни одно из 162 первичных сравнений ансамблей с тремя baseline не прошло
заранее заданный критерий. Это не доказательство отсутствия любого эффекта.
Новый вопрос — полезно ли согласие/усреднение/stacking уже существующих моделей;
новых рыночных данных нет. История 2021–2026 многократно использовалась, поэтому
все выводы exploratory, даже при малом точечном p-value.

Протокол опубликован первым в commit `5ddbe68` до ансамблевых расчётов.
Ветка основана на Draft #17 @ `7fe91ab87dcda3607863a19074e6d7b2400503e8`,
чтобы использовать frozen strict benchmark и актуальную knowledge base.
Это зависимость исследования, а не утверждение о внедрении #17. #5–8/#11–12/#17
проверены live: все open/unmerged, #11/#12/#17 Draft. Production SHA UNKNOWN.
Полные SHA и описания — [source-pr-snapshots.json](source-pr-snapshots.json).

## Данные, модели и временная достоверность

Реальные архивные provider OHLCV/actions, 2020 warmup, 2021+ base training,
строгий test 2024–2026, источник заканчивается 22 октября 2026. В test 34 200
stock/date/task rows по 18 задачам: 9 TOUCH и 9 TERMINAL. Это не независимые
испытания. Для TOUCH10/20 — 1875 anchors, 625 наблюдаемых дат, 16 полных
40-session календарных блоков с учётом промежутков. Все 66 438 исходных
calibration+test labels повторно проверены по исходным Low/Close и availability.

| Название в задании | Реально оценённый estimator | Ограничение |
|---|---|---|
| Technical Risk Signal | technical_combined: фиксированные technical cells PR7 | proxy; оригинальные production payloads не получены |
| Risk Signal Engine v3 | v3_state: probability mapping C/sensitive | вероятность состояния, не сам categorical REDUCE |
| Risk Forecast | technical_plus_v3 | joint technical/v3; частично повторяет два предыдущих входа |
| Volatility-based Risk | volatility: RV20 bins/shrinkage20 | эмпирическая вероятность того же target/horizon |
| QQQ Market Regime | regime: causal close/MA200/R20 | price-only market regime, не breadth |
| Дополнительно | v3_score; historical Beta frequency | v3_score отдельно, не шестой голос |
| Breadth | EXCLUDED | подтверждённой PIT-истории нет |

У всех базовых вероятностей версия PR17 strict refit unchanged PR7 ProbabilityBank,
исходный код PR7 @ `366f8cd00e8c228d4796d0abbe9997f717a3b6ad`.
В исходном #17 имя режима было перезаписано числовой probability в поле regime.
Здесь probability сохранена, а категория восстановлена отдельно как market_regime
по known QQQ bars; это исправление metadata, не исходных forecasts/labels.
См. corrections.md.

Дата доступности каждого прогноза — decision_at в predictions.csv.gz:
реконструированная следующая полночь UTC, не документированная историческая
публикация модели. Оригинальные provider vintages/adjustments не аттестованы;
проверка префиксов не устраняет retrospective research bias. Прогнозы, сигналы,
котировки и synthetic unit fixtures не смешиваются. Все новые числовые результаты
получены из реальных frozen prices, synthetic применяется только для тестов.
[model-inventory.csv](model-inventory.csv), [source-manifest.json](source-manifest.json),
[label-audit.csv](label-audit.csv); source pack и hashes также закреплены в #17.

Base train cutoff Jan1(Y−1), maturity/purge20 унаследованы из #17. Первый полугодовой
блок calibration-role прогнозов Y−1 используется как meta-train, второй — отдельная
калибровка, после исключения первых20 сессий и очистки label maturity на границе.
C: L2 logistic C=.1 на пяти logits; калибровка меняет только intercept с ridge1.
Ни base estimators, ни stacking slopes не обучаются на test. Никаких random stock
splits; AMD/NVDA/MU остаются на общих календарных границах. [fit-audit.csv](fit-audit.csv)
и [weights.csv](weights.csv) показывают все 54 fold/task fits и ablations.
Короткий meta/cal период ограничивает устойчивость обучаемых весов.

A2/A3/A4/A5 предупреждают при >=2/3/4/5 голосах p>=.5. Для вероятностных scores
A использует заранее обученную на meta-train conditional frequency binary warning
с shrink20; это не число голосов, делённое на5. При p<.5 mapping предупреждение
A всё равно определяется count, как задано протоколом; поэтому confusion и Brier
оценивают разные аспекты одного consensus rule. B — среднее пяти вероятностей,
C — trained/calibrated stack; B/C alert p>=.5. Пороги не менялись после результатов.

## Точность: основной иллюстративный срез TOUCH10/20

TOUCH — достижение Low порога от anchor Close внутри следующих h сессий,
TERMINAL — только Close последней сессии. Anchor исключён, незрелый horizon
не допускается даже при раннем hit. Все задачи опубликованы отдельно в CSV,
этот срез не выбран как победитель (он заранее основной для экономики).
Здесь точечные метрики; 95% block интервалы всех перечисленных метрик — в metrics.csv.
Precision=TP/(TP+FP), recall=TP/(TP+FN), FPR=FP/(FP+TN); NA означает пустой знаменатель.

'''
    text+=table(['Модель','Brier [95% CI]','Log loss','Precision %','Recall %','FPR %','Warnings %','ECE'],[[r['model'],f"{num(r['brier'])} [{num(r['brier_low'])}; {num(r['brier_high'])}]",num(r['log_loss']),pct(r['precision']),pct(r['recall']),pct(r['false_positive_rate']),pct(r['warning_frequency']),num(r['ece_descriptive'])] for r in m])
    text+='\nРавное среднее B ниже historical Brier, но выше QQQ regime. Обучаемый C не улучшил B.\n'
    refcomp=[r for r in co if ref(r) and r['model'] in ('B','C')]
    text+=table(['Ансамбль','Baseline','Δ Brier','95% CI, block40','Holm p'],[[r['model'],r['baseline'],num(r['delta_brier']),f"[{num(r['low40'])}; {num(r['high40'])}]",num(r['holm_p'])] for r in refcomp])
    text+='''
Первичная семья — 9 TOUCH задач ×6 ансамблей ×3 baseline =162 парных сравнения
на одинаковых observations, Holm. Требуются >=1% относительного Brier gain,
CI upper<0 для block20/40/60, стабильный знак в каждой акции и каждом году,
>=10 календарных блоков и >=10 каждого класса. **0/162 прошли.** В terminal и
strata нет отдельного подтверждающего поиска. Синхронный circular date-block
bootstrap:9999 повторов для primary contrasts,999 для secondary/agreement,399
для метрик strata, seed42117. Первоначальные999 не обеспечивали достаточного
разрешения p-value для Holm162; protocol-numerical-addendum.md опубликован до
исправленного расчёта. Модели/пороги/критерии не менялись.
Интервалы точечные, conditional on fitted models; fitting/design uncertainty
и нестабильность рыночных режимов полностью не покрыты. Holm применяется только
к первичным contrasts; reliability, correlations, ablations и patterns exploratory.

## Все задачи и устойчивость

'''
    text+=table(['Target','Drop %','H','Historical Brier','RV Brier','QQQ Brier','B Brier','C Brier'],[[target,t,h]+[num(next(r['brier'] for r in ms if r['target']==target and r['threshold_pct']==t and r['horizon']==h and r['dimension']=='ALL' and r['model']==model)) for model in ('historical','volatility','regime','B','C')] for target in ('touch','terminal') for t in ('5.0','10.0','15.0') for h in ('5','10','20')])
    text+='\nTOUCH10/20 отдельно по акциям, годам и известным режимам QQQ:\n\n'
    text+=table(['Срез','Значение','n','Historical','Volatility','QQQ','B','C'],[[dim,str(val),next(r['n'] for r in ms if ref(r) and r['dimension']==dim and r['value']==str(val))]+[num(next(r['brier'] for r in ms if ref(r) and r['dimension']==dim and r['value']==str(val) and r['model']==model)) for model in ('historical','volatility','regime','B','C')] for dim,vals in [('symbol',('AMD','NVDA','MU')),('test_year',(2024,2025,2026)),('regime',('UP','DOWN','MIXED'))] for val in vals])
    text+='''
Полные precision/recall/FPR/Brier/logloss/частоты/95% интервалы по всем моделям
и срезам — [metrics.csv](metrics.csv). Фиксированные10 probability bins, средний
прогноз, фактическая частота и её block CI — [reliability.csv](reliability.csv).
ECE — описательная сумма абсолютных ошибок bins, без утверждения о независимой
калибровке на новом рынке. Пустые bins и неустойчивые bootstrap ratios имеют NA.

## Главный вопрос: количество согласных моделей

TOUCH10/20. «Обычная» вероятность по всей той же task-выборке —36.11%.
Дополнительно показана безусловная частота на ТЕХ ЖЕ датах: все три акции в
дни, когда хотя бы одна попала в bucket. Это контролирует общую дату, но не
устраняет stock/regime composition или все confounders. В одном ticker-срезе
такой same-date baseline совпадает с условной частотой по определению;
для него содержательнее overall task baseline. Никакой причинной интерпретации.

'''
    text+=table(['Голосов','n anchors','Падение %, 95% CI','Baseline тех же дат %','Δ п.п., 95% CI','Кластеры hit окон'],[[r['bucket'] if r['bucket']!='3' else '3+',r['n'],f"{pct(r['event_rate'])} [{pct(r['rate_low'])}; {pct(r['rate_high'])}]",pct(r['matched_date_rate']),f"{pct(r['uplift_matched'])} [{pct(r['uplift_low'])}; {pct(r['uplift_high'])}]",r['nonoverlap_positive_clusters']] for r in a])
    text+='''
Монотонного усиления 0→1→2→3+ нет. 3+ выше общего36.11%, но matched-date uplift
+3.82 п.п. имеет95%CI[−0.34;+9.35]. Среди4 голосов precision31.43%, а5 голосов
в этом target не встречалось. Поэтому «больше согласия» не является автоматическим
основанием увеличивать вероятность. [agreement.csv](agreement.csv) содержит все
count buckets и все32 точных patterns по каждой задаче/акции/году/режиму.

**Ответ о наиболее сильном сочетании.** Если после просмотра всех9 TOUCH задач
ранжировать точные patterns по matched-date uplift, максимум — `10101` для
падения5%/20 сессий: technical_combined + Risk Forecast + QQQ предупреждают,
v3_state и RV20 не предупреждают. Частота100% против33.33% на тех же датах,
+66.67 п.п., но всего3 anchors и **один** объединённый кластер положительных окон.
При block bootstrap менее80% реплик содержат это редкое условие, поэтому
достоверный95%CI **не оценивается (NA)**. Нельзя заменять его узким IID интервалом.
Это выбранный ПОСЛЕ просмотра максимум, не подтверждённая комбинация.
По сравнению с общей исторической частотой максимальный uplift у `10011`
для TOUCH10/20:100% против36.11%, но всего1 anchor/1кластер, а baseline тех же дат
тоже100%: matched uplift0. Такой «победитель» не имеет практической доказательной силы.

Для заранее заданной широкой группы3+ TOUCH10/20 доступен95%CI частоты
[30.98%;66.81%],5 объединённых положительных кластеров,16 календарных40-блоков.
**Число статистически независимых событий UNKNOWN:** даже неперекрывающиеся окна
могут зависеть от общих факторов. 5 кластеров — счётчик удаления перекрытия,
не утверждение о пяти независимых подтверждениях. Надёжно установленное
«лучшее сочетание» отсутствует; post-selection интервалы не являются simultaneous.

## Корреляции ошибок и добавочная ценность

Остатки p−y для пяти входов имеют парные корреляции0.9587–0.9962 в TOUCH10/20.
Technical и Risk Forecast:0.9962; v3_state и QQQ:0.9848. Высокая корреляция
частично механически обусловлена общей y, и сама по себе не доказывает отсутствие
условной информации. Однако считать голоса независимыми недопустимо: technical
признаки используются повторно в Forecast, все акции чувствительны к общему рынку.
Полные matrices: error-correlation.csv; по stock/year/regime с block CI:
error-correlation-strata.csv.

C ablations обучены заново на тех же meta/cal folds, без исключаемого входа.
Положительный Δ=loss_without−loss_full означает полезность добавленного входа;
это условная исследовательская оценка в конкретном regularized stack.

'''
    text+=table(['Исключённая модель','Δ Brier without−full','95% CI'],[[r['model'],num(r['delta_brier_without_minus_full'],6),f"[{num(r['low'],6)}; {num(r['high'],6)}]"] for r in ad if ref(r)])
    text+='''
RV20 даёт самый большой положительный conditional contribution в этом срезе;
это exploratory, без множественно скорректированного подтверждения. Technical
и Forecast здесь ухудшают данный C, но это не универсальный вывод об их бесполезности.
Все задачи и strata: added-value.csv / added-value-strata.csv.

## Экономическая проверка фиксированного сокращения

Независимый счёт100000USD на акцию, непрерывно с открытия после первого test
anchor до22октября2026, без годовых reset. После следующего доступного предупреждения
продаются25% текущих акций на open delay1; через20 сессий cash-limited выкуп
до проданного количества. Новый цикл только после завершения предыдущего;
первая anchor-дата определяет начальную покупку, предупреждения обрабатываются
со следующих anchor observations. Остатки cash не реинвестируются сверх sold units,
процент0. Комиссия5bp и adverse slippage5bp на каждой стороне, такие же initial
costs у Buy & Hold. Все шесть ансамблей отдельно, delay2 как фиксированная sensitivity.
Это новая проверка фиксированной политики, не оптимизация торгового алгоритма.

Gross ex-date dividends — nonspendable receivable: фактические payment dates
неизвестны. Split-adjusted provider units используются один раз; dividend basis
унаследован от source pack, не независимая attestation. Price-only NAV и начисленные
дивиденды отдельно. Нет налогов, impact, terminal liquidation; открытые лоты
переоценены, не превращены в фиктивно закрытую прибыль.

'''
    text+=table(['Акция','Модель','B&H NAV $','Policy NAV $','Δ NAV $','MaxDD policy/B&H %','False-warning price opportunity $'],[[r['symbol'],r['model'],num(r['bh_final_nav'],2),num(r['final_nav'],2),num(r['delta_nav'],2),pct(r['max_drawdown'])+'/'+pct(r['bh_max_drawdown']),num(r['false_warning_price_opportunity_usd'],2)] for r in ec if r['delay']=='1'])
    active=[r for r in ec if r['delay']=='1' and int(r['reductions'])>0];sens=[r for r in ec if r['delay']=='2' and int(r['reductions'])>0]
    text+=f'\nВсе {len(active)} активных primary stock/policy счетов ниже B&H; '+f'{len([r for r in ec if r["delay"]=="1" and int(r["reductions"])==0])} без сделок совпадают с B&H. Delay2: {sum(float(r["delta_nav"])>0 for r in sens)}/{len(sens)} активных счетов выше B&H.\n'
    text+='''
Упущенная price opportunity на ложных предупреждениях = sold_qty×(buy_open−sale_open)
для законченных циклов, где TOUCH10/20 от signal close не достигнут. Положительное
значение — пропущенный рост; отрицательное допускается, поскольку reference/holding
окна различаются. Это описательный signed mark без fees/dividend и без дальнейшего
compounding, не аддитивная причинная декомпозиция общего NAV. Missed dividends,
полные marks и costs/cash — economic-summary.csv / economic-lots.csv /
economic-trades.csv / economic-daily.csv.gz. False-warning closed lots — subset;
открытые лоты остаются в общем NAV, не исключаются для улучшения результата.
Экономика использует только anchors с полным исходным20-session label: в последние
20 сессий источника новых сигналов нет. Счёт продолжает держать/восстанавливать
позиции до cutoff; это ограничение end-of-sample, не полноценный live forecast replay.

## Ограничения и решение

1. Нет original historical forecast logs или проверенных PIT vintages. Существующие
technical/v3 forecasts представлены probability estimators, а не production models.
Не утверждается полнота всех исторических Alpha OS outputs. Breadth исключён.
2. Архитектура/профиль/выбор трёх surviving semiconductor stocks сформированы после
наблюдения истории. Walk-forward предотвращает вычислительную утечку, но не делает
многократно просмотренный2021–2026 независимым нетронутым holdout.
3. Редкие сочетания и глубокие падения дают мало событий и NA интервалы. Цена
калибровки — короткие chronological meta/cal блоки. Holm снижает ложные открытия,
но не исправляет малую мощность или post-selection описание patterns.
4. Блоки20/40/60 и синхронные даты учитывают часть зависимости, но не гарантируют
stationarity/independence. Интервалы не включают всю uncertainty повторного обучения.
5. Provider source/license evidence и корпоративные действия не независимо
аттестованы; новых данных не покупали/не скачивали. В public Git сохраняются
собственные производные результаты; raw source pack закреплён по существующему SHA.
6. Экономика зависит от open fill/cost/cash/dividend assumptions, без liquidity/impact,
налогов и реального исполнения. Проверенная политика проигрывает B&H на данном пути;
это не теорема о любой возможной risk strategy.

**GO: нет. RESEARCH ONLY: да, как отрицательный exploratory результат нового вопроса.
NO-GO: для production, live integration и заявления о подтверждённом преимуществе.**
Не выбирать новый лучший ensemble/threshold на этих результатах.

Независимая будущая проверка: заморозить спецификацию/код, логировать фактически
доступные forecasts и исходные vintages до открытия, резервировать период со
следующей сессии после публикации. Минимум2 года и30 de-overlapped market episodes;
вслепую рассчитать мощность для1% Brier gain по исторической block variance,
продлить период при недостатке мощности. Никаких interim winner switches/peeking.
Сохранить фиксированную Holm family, отдельно проверить PIT и экономические gates.
План — рекомендация, не автоматическое разрешение внедрения/покупок.

## Воспроизведение и артефакты

[protocol.md](protocol.md), protocol-registration.json, source-manifest.json;
[README](../../research/ensemble_risk_forecast/README.md), tests, validation.md.
Все probabilities, votes, decisions и labels — predictions.csv.gz (обычный gzip CSV).
Предыдущие исследования/карточки сохранены без перезаписи. Production/торговые
алгоритмы не менялись; merge/deploy/данные за деньги/торговые операции не выполнялись.
'''
    (OUT/'report-ru.md').write_text(text)
    (OUT/'README.md').write_text('# Ensemble Risk Forecast v1\n\n[Русский аналитический отчёт](report-ru.md).\n\nFrozen exploratory research; no production integration. See protocol.md, metrics.csv, agreement.csv, comparisons.csv and economic-summary.csv.\n')
if __name__=='__main__':main()
