"""Russian report from every frozen result, including null and negative findings."""
from common import *
import re

def num(x,d=4):return f'{float(x):.{d}f}' if x not in (None,'') else 'NA'
def pct(x):return num(float(x)*100,2) if x not in (None,'') else 'NA'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(map(str,row))+' |' for row in rows])+'\n'
def main():
    inv=read('data-inventory.csv');ms=read('metrics.csv.gz');cs=read('predictive-evaluation.csv');pv=read('factor-prevalence.csv');es=read('market-episodes.csv');lead=read('pre-onset-lead-times.csv');cov=read('pre-onset-coverage.csv');marketonly=read('stock-market-only-evaluation.csv');run=json.loads((OUT/'run-summary.json').read_text());summary=json.loads((OUT/'predictive-summary.json').read_text());reg=json.loads((OUT/'protocol-registration.json').read_text())
    primary=lambda r:r['target']=='TOUCH' and r['threshold_pct']=='5' and r['horizon']=='10'
    report='''# Issue19 — Общерыночные коррекции: предвестники и прогностическая сила

**RESEARCH-ONLY. Преимущество нового прогнозного ядра не установлено; NO-GO для
production и заявления о валидации.** Ни одно из33 первичных сравнений не прошло
заранее заданные критерии. Отсутствие значимости не доказывает отсутствие эффекта.
Основная цель здесь — вероятность **Low на5% ниже anchor Close в следующих10
торговых сессиях**, а не доходность/NAV или сравнение с Buy & Hold. Торгового
backtest нет. Общерыночные SPY/QQQ/SOXX и отдельные AMD/NVDA/MU не смешиваются
в одном outcome. SOXX — секторный ETF proxy, не весь рынок и не историческая breadth.

## Пререгистрация и исследовательская база

'''
    report+=f"Протокол опубликован первым: `{reg['protocol_commit']}`. Аудит данных и\nmarket-only addendum опубликованы до дополнительного сравнения в\n`{reg['data_and_addendum_publication_commit']}`.\n"
    report+='''Первичные33 теста/пороги/признаки/модели сохранены. Дополнение лишь отдельно
проверяет строго market-only baseline: исходная MINIMAL содержит ownRV20 и потому
честно называется market-conditioned, own-volatility-controlled, а не market-only.
Дополнительная семья из3 сравнений вторичная, не заменяет первичную.

Прочитаны pinned PR8@c228624158068db64fe7e487a5be59281448fcd9,
PR17@7fe91ab87dcda3607863a19074e6d7b2400503e8,
PR18@43886c0516b35bcfd61afce583b17112ce94bce0. Все open/unmerged;
#17/#18 Draft. Новая ветка основана на #18 ради текущей knowledge base,
не является его внедрением. Предыдущие результаты0/4,0/27,0/162 не переписаны.
Новый вопрос — dedicated market catalogue, pre-onset anatomy и дополнительная
сила фиксированных факторов, не повтор прежнего ансамблевого теста.

## Квалификация данных:2000–2026 не равно original PIT

'''
    report+=table(['Инструмент','Первый bar','Последний bar','Строк','firstTradeDate metadata (не аттестация IPO)','PIT certified'],[[r['symbol'],r['first'],r['last'],r['rows'],r['first_trade_date'],'нет'] for r in inv])
    report+='''Сохранены бесплатные Yahoo chart responses, URLs, retrievalUTC, SHA256, reported
splits/dividends, normalized split-adjusted OHLC и XNYS4.11.2 calendar с DST и early
closes. Adjclose с dividend adjustment не смешивается с OHLC, второй split-adjustment
не применяется. Внутри фактических диапазонов нет пропущенных сессий/дубликатов/OHLC
ошибок. По каждому инструменту6872 OHLC-field comparisons с frozen PR11 дают нулевое
расхождение. Это проверка совпадения архивов, не независимая provider verification.
SOXX до2001-07-13 в сохранённом источнике отсутствует и не достраивался.
firstTradeDate — поле provider, не независимо проверенная IPO/listing date;
отсутствующая история не считается нулевым риском.

Строгий PIT gate **FAIL**: нет original historical vintages/publication timestamps/
независимо подтверждённой adjustment history. Next-midnight UTC availability —
консервативная гипотеза расписания, не свидетельство оригинального release.
Для этих цен разрешён только **AUDITABLE_RETROSPECTIVE_PRICE** causal replay.
Все результаты условны на достоверности provider history; исходная задача не
превращается в independently validated core. См. data-qualification.md,
data/manifest.json, split-quality.csv, source-coverage-era.csv, archive-overlap.csv.
Цены ETF включают ex-dividend price effects, не dividend total return.

STOP/NO-GO для VIX без исходных timestamps, credit/yields/liquidity без vintages,
true market/sector breadth и concentration без PIT memberships/holdings,
survivor-peer breadth и **H4 revisions**. Они не импутированы и не заменены текущими
данными. missing-factors.csv сохраняет все исключения. Windows/Norgate acquisition
отложен, trial/account/subscription не запускались; платные данные не приобретались.

## Каталог и чисто pre-onset анатомия

Closing observable-history peak, latest equal high, onset — первая более низкая
сессия; первый closing−5% threshold, lowest closing trough, recovery только после
Close>=старого peak. Nested declines объединяются до recovery. TOUCH Low labels
отдельны от closing-episode labels. Это observable-history high с2000/IPO, не
доказанный lifetime ATH. Prior lifetime peak UNKNOWN; left-truncated означает лишь
случай peak в первой доступной строке, неизвестная более ранняя история остаётся
ограничением даже при false этом флаге. Незавершённые эпизоды right-censored.
В каталоге также onset-to-threshold/trough и first60-session depth/completeness.

'''
    report+=table(['Proxy','Эпизоды>=5%','Открытые','С доступными pre-onset snapshots'],[[s,sum(r['symbol']==s for r in es),sum(r['symbol']==s and r['right_censored']=='True' for r in es),len({r['event_id'] for r in read('pre-onset-snapshots.csv') if r['symbol']==s and r['status']=='AVAILABLE'})] for s in MARKET])
    report+=f"\nВсего **{run['market_episode_count']}** proxy episodes, объединены по перекрытию\nв **{run['market_overlap_clusters']}** market interval clusters. Это НЕ{run['market_episode_count']} независимых рыночных\nсобытий; число статистически независимых событий UNKNOWN. Длинные unrecovered\nэпизоды могут объединять несколько известных кризисов в один кластер.\n"
    report+='''Snapshots onset−60/40/20/10/5 строго до начала падения и только по известным
данным. Сам будущий peak/trough не используется как feature. Warmup252 и общий
SOXX контекст ограничивают earliest full feature panel; snapshots ранних2000
часто MISSING_WARMUP. Доступные2008/2020/2022 regimes описаны, но2008–09 относятся
к train/descriptive, а не к held-out prediction window. Прогнозный test начинается
в2010 по опубликованному протоколу; нет заявленного OOS-теста2000–02/2008.

Матчинг до3 controls: тот же proxy/causal QQQ regime/двухлетний блок, вне всех
квалифицируемых ongoing episodes, >=60сессий от onset; nearest date, tie earlier.
Повторы и inverse-reuse weights сохранены, NO_MATCH допускается. Это case-enriched
описание, не выборка для probability training. Все population rates рассчитаны
на **всех** пригодных датах, включая no-crash, а не только matched controls.

Pre-onset60 coverage и lead times по всем флагам, без выбора победителя:

'''
    report+=table(['Proxy','Флаг','Полных60d событий','С предупреждением до onset','Медиана first lead, сессий'],[[s,flag,len(rr),sum(r['pre_onset_coverage']=='True' for r in rr),num(np.median([float(r['first_lead_sessions']) for r in rr if r['first_lead_sessions']!='']),1) if any(r['first_lead_sessions']!='' for r in rr) else 'NA'] for s in MARKET for flag in M_FLAGS for rr in [[r for r in lead if r['symbol']==s and r['flag']==flag and r['status']=='COMPLETE60']]])
    report+='''Чаще всего до onset встречался market_vol_acceleration: хотя бы раз за60 сессий
в19/19 доступных SPY,19/19 QQQ и39/40 SOXX эпизодов. Это описательное сравнение
фиксированных флагов после просмотра, не validated pattern. Для SPY на всех
пригодных датах precision этого флага13.72% при base11.11%, false alarms86.28%.

Высокая coverage в60-session окне не означает точный10-session прогноз: флаг
может сохраняться долго и часто появляться без последующей коррекции. Это не
confusion-метрика и не самостоятельное доказательство предсказательной силы.
Полные offsets/nulls: market-episodes.csv, market-episode-clusters.csv,
pre-onset-snapshots.csv, matched-controls.csv, pre-onset-coverage.csv,
pre-onset-lead-times.csv, matched-factor-prevalence.csv.

## P(feature|crash), P(feature|no crash), P(crash|feature)

TOUCH5/10, все пригодные даты с252-session warmup (train/descriptive+test),
поэтому эти prevalence estimates НЕ являются OOS результатом. Фиксированные
флаги: QQQ−SPY R20<=−3pp; max marketRV20/RV60>=1.1; SOXX−QQQ R20<=−3pp;
SOXXRV20/RV60>=1.1. Stock flags отдельно: MA50extension>=10% AND R60>=20%,
relative weakness<=−5pp, RV ratio>=1.1. Нет unlimited conjunction search.

'''
    report+=table(['Proxy','Флаг','P(F|crash)%','P(F|no crash)%','P(crash|F)%','Base%','False alarm%','Recall%','Lift [95% CI]'],[[r['symbol'],r['flag'],pct(r['P_feature_given_crash']),pct(r['P_feature_given_no_crash']),pct(r['P_crash_given_feature']),pct(r['base_rate']),pct(r['false_alarm_fraction']),pct(r['recall']),f"{num(r['lift'],2)} [{num(r['lift_low'],2)};{num(r['lift_high'],2)}]"] for r in pv if primary(r) and r['population']=='MARKET' and r['dimension']=='ALL'])
    report+='''Все4 market/sector flags и7 stock flags, все12 target tasks и regime slices,
blockCI399/HAC effectiveN — factor-prevalence.csv. Интервалы здесь pointwise,
exploratory, без отдельного победителя/confirmatory significance search. Высокий
lift может отражать уже начавшееся снижение, поэтому pure pre-onset snapshots
и causal near-high (expanding DD>=−2%) diagnostics показаны отдельно. Near-high
не гарантирует «до будущего onset»: это только известный на дату фильтр.

## Frozen predictive evaluation: основная задача TOUCH5/10

Train только из fully matured past labels доJan1(Y−1), anchor purge20 (60 дляh60).
CalibrationY−1 отделена: первые max(20,h) сессий удалены, полный future label должен
созреть до final max(20,h) сессий перед testY. TestY первые max(20,h) исключены.
На каждом году модели и calibration frozen; прошлые test years позднее становятся
past training. Никаких random-row splits, отборов flags/thresholds на итоговых тестах.
Годы2010–2026 chronological, но исторически просмотренные и не untouched holdout.

HIST — annual expanding Beta(1,1), VOL — own logRV20 logistic, REGIME — QQQ causal
UP/DOWN/MIXED frequency shrink20. SIMPLE — own logRV20 + QQQ/SPY trend/R20;
PLUS_M — добавить QQQ−SPY R20 и market volatility ratios; PLUS_S — добавить
SOXX relative weakness/volatility ratio; MINIMAL — SIMPLE+M+S. Для акций PLUS_X
добавляет extension/R60/relative weakness/own volatility ratio к MINIMAL.
L2 C=.1, training-only scaling, intercept-only calibration ridge1 на отдельном
cal year. Raw/calibrated probabilities сохранены; primary metrics используют
calibrated logits, HIST/REGIME без refitted calibration. Пороги alert .20/.50.

'''
    report+=table(['Instrument','n','Base%','HIST Brier','VOL','REGIME','SIMPLE','MINIMAL','PLUS_X'],[[s,rs[0]['n'],pct(rs[0]['base_rate'])]+[num(next((r['brier'] for r in rs if r['model']==m),None),6) for m in ('HIST','VOL','REGIME','SIMPLE','MINIMAL','PLUS_X')] for s in SYMBOLS for rs in [[r for r in ms if primary(r) and r['symbol']==s and r['dimension']=='ALL' and r['operating_threshold']=='0.2']]])
    report+=f"\nВсего{run['forecast_rows']} forecast task rows, не независимых событий.\n**{summary['primary_pass']}/{summary['primary_family']}** primary contrasts прошли criterion, минимальный raw p="+num(min(float(r['p_one_sided']) for r in cs if r['primary']=='True'),4)+', Holm p=1.0000.\n'
    report+='''Синхронный calendar-block bootstrap сохраняет все инструменты на одной sampled
дате:9999 primary repetitions, block40, sensitivity20/60, Holm33. Для secondary
999 repeats, blockmax(40,h), metrics/prevalence399. Критерий также требует>=1%
relative Brier gain, CIupper<0 на всех3длинах, достаточные классы/блоки, sign stability
по>=2eligible years и неухудшение logloss. Интервалы conditional on fitted models;
training/design uncertainty и regime instability полностью не покрыты.

Все18 market и15 stock primary contrasts, включая отрицательные, опубликованы:

'''
    report+=table(['Инструмент','Модель','Baseline','Δ Brier','95% CI40','Holm p','Stable years'],[[r['symbol'],r['model'],r['baseline'],num(r['delta_brier'],6),f"[{num(r['low40'],6)};{num(r['high40'],6)}]",num(r['holm_p'],4),r['stable_years']] for r in cs if r['primary']=='True'])
    report+='''predictive-evaluation.csv включает все baseline comparisons по primary/secondary
TOUCH/TERMINAL tasks с интервалами. Brier/logloss, precision/recall/FPR, alert
frequency, calibration bias/ECE, base-rate lift и их CIs — metrics.csv.gz.
Probability bins10 фиксированы и descriptive (reliability.csv.gz), raw Brier
также сохранён. По каждому инструменту/году/QQQ regime/era/near-high отдельно.
HAC effectiveN не определяется при календарных gaps/zero variance; N anchors и
число40-session blocks не называются independent trials. Terminal/60d результаты
не подменяют основной отрицательный TOUCH5/10 вывод.

## Индивидуальные акции против строго market-only baseline

MARKET_ONLY использует QQQ/SPY/SOXX цены, включая QQQ logRV20; own stock features
отсутствуют. Outcome — по-прежнему отдельное падение акции. PLUS_X отличается
собственной волатильностью и stock X; это другой вопрос, чем X сверх уже
own-volatility-controlled MINIMAL в первичной семье33.

'''
    report+=table(['Акция','Δ Brier PLUS_X−market-only','95% CI40','Δ logloss','Holm secondary3'],[[r['symbol'],num(r['delta_brier'],6),f"[{num(r['low40'],6)};{num(r['high40'],6)}]",num(r['delta_log_loss'],6),num(r['holm_p_secondary3'],4)] for r in marketonly])
    report+='''У NVDA есть **вторичное exploratory** улучшение против конкретного market-only
logistic comparator: ΔBrier−0.011261,95%CI[−0.020541;−0.001878], Holm3=.0291.
Это не глобальная поправка по всем exploratory analyses и не независимая валидация.
Оно не подтверждает новый core: PLUS_X Brier0.249973 хуже простой REGIME0.246977;
X сверх MINIMAL в первичной семье33 значимого преимущества не установил. AMD/MU
не подтверждают переносимость эффекта. Не выбирать NVDA или этот comparator
победителем после просмотра. Все3 secondary tests сохранены отдельно; ни один
из них не заменяет первичный negative результат или PIT/prospective gate.

## Ответ на исследовательский вопрос и ограничения

Повторяющиеся price-relative weakness/volatility conditions действительно можно
описать перед частью market episodes и сопоставить с no-crash controls. Но
присутствие до событий и univariate prevalence не равны дополнительной прогнозной
силе. На фиксированных market/sector feature families **преимущество сверх сильных
baselines не установлено** по пререгистрированной TOUCH5/10 оценке. Нет оснований
называть найденный паттерн validated predictive core.

- Данные2000–2026 retrospective, original PIT timestamps/adjustments не аттестованы.
  Историческая доступность цен реконструирована; составы breadth/H4 недоступны.
- 2000–02/2008–09 покрыты данными/descriptive catalogue, но не представлены как OOS
  model test. Общий SOXX252 warmup делает earliest full panel2002, early snapshots NA.
- ETF price proxy не neutral market breadth; выбранные AMD/NVDA/MU — survivors,
  секторные/общерыночные shocks связаны. Bootstrap date grouping уменьшает, не
  устраняет все проблемы зависимости.25 overlap clusters не25 доказанно независимых
  market shocks. Неизвестная pre-2000 история/длинные recovery меняют segmentation.
- История2021–2026 использована в PR8/17/18; более ранние известные кризисы также
  не становятся исторически слепым holdout от скачивания свежего архива.
- Calibration-window/intercept instability и низкая поддержка редких задач/режимов
  ограничивают precision. NA ratios/intervals остаются NA, не нулём или успехом.
- Pointwise secondary/pattern intervals не доказывают независимый эффект. Глобальный
  поиск сочетаний/порогов/акций не выполнялся; менять specification по этим результатам
  нельзя. Statistical failure не доказывает отсутствие всех возможных предикторов.

**GO: нет для validated core. RESEARCH-ONLY: да для ограниченного causal price-only
исторического исследования. NO-GO: unqualified factors/windows, production,
утверждение о доказанном incremental forecast advantage.** Экономическая полезность
— отдельный будущий gate, в этой задаче не проверялась.

## Дальнейшая независимая проверка

prospective-shadow-log.md и shadow-log-schema.json описывают immutable forecasts:
actual timestamp, frozen code SHA/protocol/input vintage/hash, symbol/population,
TOUCH definition/horizon/probability/quality, отдельно fully matured future label,
append-only records/hash chain и corrections с сохранением истории. Это только
спецификация: live infrastructure не запускалась. Резервировать будущие данные
со следующей сессии после публикации после отдельной авторизации logging setup,
минимум2года и30 market episode clusters плюс blinded power check для1%Brier gain;
продлить при недостатке мощности. No peeking/model switches, retain33-wayHolm,
original PIT input gate; экономический gate позже. Это рекомендация, не решение
владельца о внедрении или покупке данных.

Весь код/методика/тесты/сводные таблицы/полные forecasts сохранены; knowledge base
дополнена без перезаписи прежних карточек/исследований. Validation evidence —
validation.md/verification.json. No production, trades, merge/deploy or paid data.
'''
    (OUT/'report-ru.md').write_text(re.sub(r'(?<=[А-Яа-яЁё])(?=\d)|(?<=\d)(?=[А-Яа-яЁё])', ' ', report))
    brief='''# Issue #19 — краткий итог

**RESEARCH-ONLY. Дополнительное прогностическое преимущество нового ядра не установлено.**
В основной задаче — Low на ≥5% ниже текущего Close в следующие 10 сессий —
**0/33** пререгистрированных сравнений прошли критерий. Минимальный Holm p=1,0.
Рынок SPY/QQQ/SOXX и отдельные акции AMD/NVDA/MU оценены раздельно.

Протокол опубликован до анализа исходов: `'''+reg['protocol_commit']+'''`.
Код, данные, определения и ограничения закреплены; PR #8/#17/#18 остаются unmerged.
Торгового backtest, production changes, merge/deploy и платных данных нет.

## Данные и повторяющиеся условия

Бесплатные цены: пять инструментов с 2000-01-03, SOXX с 2001-07-13, до 2026-11-02.
Внутри фактических диапазонов нет пропусков торговых сессий/дубликатов/OHLC ошибок;
пересечение с архивом PR #11 совпадает. Но original PIT vintages/время публикации
не аттестованы: разрешён только exploratory price-only replay. Breadth, VIX/macro
без timestamps и H4 revisions исключены как unqualified; Norgate не запускался.

Каталог: **87 proxy-эпизодов**, **25 интервалов после объединения перекрытий**;
это не 87/25 доказанно независимых событий. Snapshots −60/40/20/10/5 строго до onset.
Самый частый из фиксированных pre-onset flags — ускорение рыночной волатильности:
хотя бы раз за 60 сессий перед 19/19 SPY, 19/19 QQQ, 39/40 SOXX доступных эпизодов.
Это описательная повторяемость, а не точность 10-сессионного прогноза. На всех
пригодных SPY-датах его precision лишь 13,72% при base 11,11%; false alarms 86,28%.
Новые market/sector families не подтвердили incremental value сверх baselines.

## Основные вероятностные результаты

Chronological test 2010–2026, отдельные train/cal, purge 20/60 сессий,
фиксированная ridge-модель, intercept-only calibration, date-block bootstrap
9 999 повторов (20/40/60), Holm по 33 сравнениям. Пороги предупреждений 0,20/0,50.
Brier, ниже — лучше; по 3 884 зависимых anchors на инструмент для основной задачи:

'''
    brief+=table(['Proxy','HIST','VOL','REGIME','MINIMAL'],[[sym]+[num(next(r['brier'] for r in ms if primary(r) and r['symbol']==sym and r['dimension']=='ALL' and r['operating_threshold']=='0.2' and r['model']==model),6) for model in ('HIST','VOL','REGIME','MINIMAL')] for sym in MARKET])
    brief+='''
Вторичный, отдельно пререгистрированный stock-vs-pure-market тест дал улучшение
NVDA: ΔBrier −0,011261, 95% ДИ [−0,020541; −0,001878], Holm по 3 тестам =0,0291.
Но итоговый Brier 0,249973 хуже простой REGIME 0,246977; в основной семье преимущество
не установлено. AMD/MU не подтвердили переносимость. Это exploratory secondary
результат, не валидированное ядро и не глобальная поправка по всем вторичным анализам.

**GO для validated core: нет. RESEARCH-ONLY: да. NO-GO для внедрения и unqualified
факторов.** История 2021–2026 уже использована, остальные известные кризисы также
не становятся независимым holdout. Предлагается frozen prospective shadow log,
PIT evidence и blinded power plan; инфраструктура не запущена. Экономика — позже.

[Полный русский отчёт](report-ru.md), [квалификация данных](data-qualification.md),
[все сравнения и ДИ](predictive-evaluation.csv), [проверки](validation.md),
[спецификация будущего лога](prospective-shadow-log.md).
'''
    (OUT/'executive-summary-ru.md').write_text(brief)
    (OUT/'README.md').write_text('# Market drawdown precursors v1 / Issue19\n\n[Русский отчёт](executive-summary-ru.md). [Протокол](protocol.md), [Data qualification](data-qualification.md), [Prospective log](prospective-shadow-log.md).\n\nResearch-only; 33 primary comparisons, separate market and stock targets, no trading backtest.\n')
    snaps=read('pre-onset-snapshots.csv');controls=read('matched-controls.csv');matched=[]
    for s in MARKET:
     for off in ('60','40','20','10','5'):
      for flag in M_FLAGS:
        a=[r for r in snaps if r['symbol']==s and r['offset']==off and r['status']=='AVAILABLE'];b=[r for r in controls if r['symbol']==s and r['offset']==off and r['match_status']=='MATCH'];weights=np.array([float(r['inverse_reuse_weight']) for r in b]);vals=np.array([r[flag]=='True' for r in b])
        matched.append(dict(symbol=s,offset=off,flag=flag,case_events=len(a),P_feature_given_case=sum(r[flag]=='True' for r in a)/len(a) if a else None,control_rows=len(b),unique_control_dates=len({r['control_date'] for r in b}),weighted_P_feature_control=float(weights@vals/weights.sum()) if len(b) else None,inference='DESCRIPTIVE_CASE_MATCHED_NOT_POPULATION_PROBABILITY'))
    write('matched-factor-prevalence.csv',matched)

if __name__=='__main__':main()
