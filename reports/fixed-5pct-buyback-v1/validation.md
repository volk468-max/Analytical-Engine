# Validation / воспроизводимость

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
