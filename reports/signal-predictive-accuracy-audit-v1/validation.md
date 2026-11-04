# Validation and reproducibility

Фактически37Python tests passed:2existing main +35audit checks;0failures. Final readback record inverification.json. Проверки охватывают competing-barrier order/UNKNOWN, partial vs complete, nextopen vsclose anchor, execution-session inclusion, exacttouch, future-prefix invariance, split-unit invariance, nested/unfinished episodes, shared bootstrap weights, unmatched cells, mechanical overlaps, source hashes, eligibility, censoring, baseline cell/frequency invariants, nonoverlap, separate stock/market recall and missing-history denominator. Final actual pass count иповторный прогон после публикации фиксируются отдельно.

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
