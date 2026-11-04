"""Deterministic reports for the clarified specification."""
import csv,hashlib,json,statistics
from research.signal_predictive_accuracy.completion import O
from research.signal_predictive_accuracy.io import R,ROOT
def rows(n):return list(csv.DictReader((O/n).open()))
def main():
    stats=rows('signal-accuracy.csv');annual=rows('annual-accuracy.csv');base=rows('baseline-comparison.csv');miss=rows('missed-drawdowns.csv');out=rows('signal-outcomes.csv');false=rows('false-signals.csv')
    text=['# Независимый аудит точности sector_flag — уточнённое задание','',
    'Формула PR11 (5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7) не изменена: пятисессионные доходности AMD/NVDA/MU/TSM/AVGO/AMAT/LRCX, минимум четыре отрицательных, средняя ниже QQQ, только переход False→True. Все 134 даты совпали. Период 2021-01-01–2026-11-02; торговые наблюдения начинаются 4 января. Подтверждённых production-предупреждений в полученных материалах нет; оценивается реконструкция, а не факт публикации клиенту.','',
    '## Основная секторная оценка','',
    'Десять полных сессий начиная с открытия следующей сессии. TRUE POSITIVE: −5% раньше +5%; FALSE POSITIVE: условие не выполнено. Неполное окно и неизвестный порядок внутри одной свечи — UNRESOLVED. Числа по сектору и акциям не объединяются.','',
    '| Инструмент | Правильных | Ложных | Неразрешённых | Точность |','|---|---:|---:|---:|---:|']
    for x in stats:
        if x['anchor']=='OPEN':text.append(f"| {x['symbol']} | {x['tp']} | {x['fp']} | {x['unresolved']} | {100*float(x['precision']):.1f}% |")
    text+=['','## Годы: основной инструмент SOX','', '| Год | Дат | Правильных | Ложных | Неразрешённых | Точность | Пропущено 5%-эпизодов до начала / всего |','|---|---:|---:|---:|---:|---:|---:|']
    for x in annual:
        if x['symbol']=='^SOX' and x['anchor']=='OPEN':text.append(f"| {x['year']} | {x['n']} | {x['tp']} | {x['fp']} | {x['unresolved']} | {100*float(x['precision']):.1f}% | {x['missed_before_onset']}/{x['eligible_5pct_events']} |")
    text+=['','## Базовая вероятность','',
    'Следующая таблица оценивает достижение нижнего порога независимо от верхнего; это другой исход, чем основная точность. Контроль — все торговые дни без новой активации, в том числе дни продолжающегося активного sector_flag. Блоки календаря 60 сессий, 499 синхронных реплик. Интервалы 95% точечные, исследовательские, без поправки на множественность; отдельные значимые ячейки не считаются подтверждением.','',
    '| SOX, 10 сессий | После сигнала | Без сигнала | Разница, п.п. | 95% ДИ разницы | Lift |','|---|---:|---:|---:|---:|---:|']
    for x in base:
        if x['group']=='^SOX' and x['horizon']=='10' and x['down_pct'] in ['5','10','15'] and x['control']=='ALL_NONWARNING':text.append(f"| −{x['down_pct']}% | {100*float(x['probability_signal']):.2f}% | {100*float(x['probability_control']):.2f}% | {float(x['difference_pp']):+.2f} | [{float(x['difference_ci_low']):.2f}; {float(x['difference_ci_high']):.2f}] | {float(x['lift']):.3f} |")
    text+=['', 'Сопоставление по кварталу, известному на дату режиму QQQ и доступному составу также опубликовано. Для SOX/−5%/10 сессий: +5,43 п.п., ДИ [−0,97; +13,24]. Результат не подтверждает преимущество. Контроли выбираются по календарю и текущим признакам, не по будущему исходу; сравнение ретроспективное, не онлайн-прогноз вероятности. Первоначальные дополнительные механические контроли сохранены в родительском каталоге.','',
    '## Пропущенные падения и своевременность','',
    'Эпизоды отсчитываются от предшествующего пика закрытия с начальной историей 20 сессий, вложенные снижения объединяются до полного восстановления; незавершённые эпизоды сохраняются. Это длительные эпизоды полной просадки, а не каждый краткий отскок. Дополнительно прежний аудит проверял 60-сессионную и 98%-восстановительную чувствительность.','',
    'Основная новая проверка — предупреждение за 10 сессий ДО НАЧАЛА эпизода: SOX пропущено 11/21 эпизодов −5%, 7/10 эпизодов −10%, 4/5 эпизодов −15%. Число малое, особенно для глубоких падений. Неполные ранние lookback-окна исключены. Таблица содержит отдельно предупреждение до начала и до достижения порога: это разные определения, их нельзя смешивать. Пиковые даты и последующие минимумы — только ретроспективные метки.','',
    'При правильном SOX-предупреждении медиана времени до достижения −5% от следующего открытия — 4 сессии, сессия отсчёта считается первой. Это НЕ четыре дня до начала падения. В 47,4% зрелых SOX-наблюдений цена к моменту сигнала уже потеряла ≥5% от предшествующего 20-сессионного максимума закрытия. Для AMD — 70,7%, NVDA — 58,6%, MU — 69,2%. Из 134 сигналов SOX 78 находились между пиком и минимумом каталожного эпизода; в 38 из этих 78 (48,7%) уже произошла минимум половина окончательного снижения. Эти 38 составляют 28,4% всех дат; остальные даты не объявляются своевременными автоматически. Это ретроспективная оценка только для описания (signal-timing.csv), не доступный алгоритму признак. Сигнал часто фиксирует уже начавшееся ухудшение; это не доказывает, что он всегда опаздывает или никогда не полезен.','',
    '## Ложные предупреждения','',
    'false-signals.csv ранжирован по максимальному росту за 20 сессий. Для SOX после сигнала 2022-10-20 максимум был +26,42%, конечная доходность 20 сессий +20,67%, максимальное падение только 0,68%. Другие примеры: 2026-04-21 (+23,68% максимум), 2026-05-01 (+23,08%). Это описания исходов, не доходность торговой стратегии.','',
    'В таблице есть падение после основного окна (сессии 11–20), доходности 10/20, ценовые экстремумы и время до пика. «Продолжительность роста» определена как число сессий до первого максимума окна; это не утверждение о непрерывном росте. Неполный хвост явно помечен.','',
    '## Вывод и дальнейшая работа','',
    'Статистически подтверждённая дополнительная прогностическая сила основного sector_flag не установлена. По SOX вероятность ложного предупреждения среди разрешённых исходов — 57,1%. В первоначальной таблице режимов наблюдалась более высокая точность по акциям в BEAR, но это не доказывает добавочную информацию сверх большей фоновой вероятности падения; секторные разрезы см. regime-accuracy.csv. Текущий сигнал разумно сохранять как прозрачный базовый ориентир, но нет оснований внедрять его как доказанную защиту капитала. Принципиально другой подход этим аудитом тоже не доказан: дальнейшие гипотезы требуют новых, не использованных при разработке данных.','',
    '## Ограничения','',
    '134 даты — единицы предупреждения; 1374 зрелых исхода по акциям не являются независимыми сигналами. Окна перекрываются, текущий список содержит survivorship/selection bias, история уже многократно исследовалась. Ежедневные OHLC не дают порядок внутри свечи. Исходные даты публикации котировок не подтверждены: принято следующее UTC-полуночь и следующее регулярное открытие. Сплиты приведены к постоянным единицам, дивиденды не превращены в total return. Это аудит цен, не торговли. Нет доступа к оригинальным production-выходам и историческим корпоративным/новостным vintage. Отсутствие архивной записи не означает HOLD. Полный реестр источников и хешей сохранён в ../inputs/provenance.json.','',
    'Расчёты без сделок, без изменения production, алгоритмов, merge/deploy.']
    (O/'executive-summary-ru.md').write_text('\n'.join(text)+'\n')
    (O/'protocol.md').write_text('# Clarified specification protocol\n\nFrozen PR11 SHA 5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7; 134 unchanged activations. Original PR12 results retained. Next regular open, full 10 sessions including reference session; same-bar/incomplete UNRESOLVED. SOX primary, SOXX/SMH/QQQ separate, stock outcomes dependent by date. Horizons5/10/20, lower3/5/10/15%, upper5%. Nonwarning and quarter/regime/eligibility-matched controls; 60-calendar-session circular bootstrap,499reps,seed20261104. No signal/parameter optimization or trades.\n\nRequested research/signal-predictive-accuracy-v1 is a continuation of existing PR12 ancestry from main; both branch refs will point at the same completion commit. Existing PR12 head retains its original name because GitHub cannot change the source branch of an existing PR. No history rewrite.\n')
    (O/'validation.md').write_text('''# Validation and reproducibility

Commands from repository root:
```
python -m research.signal_predictive_accuracy.completion
python -m research.signal_predictive_accuracy.completion_report
PYTHONPATH=/tmp/alpha-audit-test-deps python -m pytest tests research/signal_predictive_accuracy -q
```

Fresh test run: 43 passed, 0 failed; one environment anyio PytestRemovedIn10Warning. pytest9.2.0 installed in temporary dependency directory; not a repository dependency change. This comprises the prior37 plus6 new tests, all rerun, not claimed from old runs. Frozen-source load validates SHA256 hashes, 1465 daily states and134activation dates; no new signal indicators. New tests enforce full-window censoring, same-bar unresolved, execution-session counting, pre-onset exclusion/boundaries, and resolved denominator.

Original first-audit files remain unchanged. Supplement uses strict UNRESOLVED for all incomplete windows, even when an early event already decided the logical outcome. In original files, UNKNOWN is distinct and partial outcomes may be known; these definitions are not mixed. Time-to-extreme fields require complete windows, first tied date chosen deterministically. Nonwarning control includes active-state days without new activation. Control matching uses only contemporaneous eligibility and recorded price regime; future labels never choose a control. Empty matching cells omitted and counted. Matching by quarter is retrospective and not a deployable online probability model.

Circular calendar-block bootstrap shares calendar resampling across all symbols; within-date equities are averaged before resampling. Confidence intervals here are exploratory pointwise,499reps; no significance claim based on multiple threshold scans. Parent audit contains longer1999rep bootstrap and20/120block sensitivity for its different primary competing-barrier targets. Do not substitute those CIs for supplement touch probabilities.

Corporate actions and publication-vintage limitations from ../inputs/provenance.json and parent validation.md remain. No new feed, production query, data backfill, prices, model weights or trading operations introduced. Price-only labels, not dividend-inclusive investor returns. No private production payload obtained; missing evidence UNKNOWN, not HOLD. Non-nested peak-to-recovery episodes may span years; annual missed-event counts assign threshold year, not imply independently discovered yearly episodes. Pre-onset recall and pre-threshold recall are separate; no F1 combining them with competing-barrier accuracy.
''')
    files=list(O.glob('*'))+[ROOT/'research/signal_predictive_accuracy/completion.py',ROOT/'research/signal_predictive_accuracy/completion_report.py',ROOT/'research/signal_predictive_accuracy/test_completion.py']
    m={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(files) if f.is_file() and f.name!='manifest.json'}
    (O/'manifest.json').write_text(json.dumps(dict(source_commit='5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7',parameters=dict(horizons=[5,10,20],lower_thresholds=[3,5,10,15],upper_threshold=5,bootstrap_block=60,replicates=499,seed=20261104),sha256=m),indent=2)+'\n')
if __name__=='__main__':main()
