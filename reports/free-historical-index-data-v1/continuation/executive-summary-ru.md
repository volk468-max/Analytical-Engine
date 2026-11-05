# Продолжение аудита: бесплатный ценовой архив

Дата: 2026-11-05. Дополнение к исходному PR15 commit 8cc80cdf31690fd74639b8fc498283d6cca1399d, без изменения его 27 файлов. Период сопоставления сохранён 2010-01-04–2026-11-03: новые ноябрьские даты не добавлены, поэтому before/after сравнимы.

**Удалось существенно увеличить acquired candidate coverage, но qualified PIT coverage и готовность к полноценному Breadth-backtest по-прежнему не подтверждены.**

## Источник и фактическая загрузка

[Kaggle camnugent/sandp500](https://www.kaggle.com/datasets/camnugent/sandp500), версия 4. На странице автор указывает CC0 Public Domain и отбор компаний, текущих на момент формирования снимка (обновление февраля 2018). Публичный versioned download API вернул HTTP200, ZIP 20283917 bytes. API и SHA256 ZIP/CSV сохранены в source-manifest.json. Никаких credentials, аккаунтов, покупок, retries или обхода ограничений нет. Raw dataset в GitHub не перепубликуется; указание CC0 автором не является независимой проверкой всех upstream прав.

В архиве прочитан полный all_stocks_5yr.csv: 619040 rows, 505 tickers, 2013-02-08–2018-02-07. Вложенный getSandP.py вызывает pandas_datareader с provider `iex`; updater из текущего авторского GitHub использует `yahoo`. Текущий updater НЕ является доказательством происхождения исторического CSV; ни один updater не запускался. Adjustment basis / splits / dividend treatment независимо не аттестованы.

527 rows исключены из механического покрытия: 11 missing/non-numeric, 12 impossible/nonpositive OHLCV, 210 AAL до 2013-12-09, 294 GOOG/GOOGL до class split 2014-04-03. Даты identity quarantine опираются на первичные события исходного data-quality-report.md. Для Google ранние provider-relabelled ряды не подменяются известной прежней share class автоматически. Это ограниченный список известных identity-проблем, не аттестация остальных securities. Осталось 618513 mechanically usable reference-session rows; дубли ключей и non-session rows не обнаружены.

## Что изменилось

| Source | Было member-days | Добавлено | Coverage после | Departed coverage после |
|---|---:|---:|---:|---:|
| fja_sp500 | 13660 | 548450 | 26.4357% | 27.4564% |
| lawcal_sp500 | 13661 | 542381 | 26.2755% | 26.8250% |
| thuning_ndx | 13596 | 100603 | 26.2157% | 24.9792% |
| thuning_sp500 | 13660 | 548450 | 26.4357% | 27.4272% |

Все доли — acquired exact-ticker candidate member-day observations / source-derived candidate member-days за весь период, включая помеченные stale tails. Это не verified security coverage, не доля полных компаний и не оценка истинного полного denominator. Числа старого executive summary за 2026-11-04 сохранены как исторический checkpoint; таблица выше — новый результат на 2026-11-05.

Подгруппа departed определяется исходным source-observed index exit, включая ticker renames; она НЕ равна списку bankrupt/exchange-delisted companies. Получены более ранние цены части тех, кто ушёл из индекса после снимка 2018, но это не полные истории до поглощения/банкротства/делистинга. Например ATVI присутствует, ENDP/CMCSK/WFM/SIVB отсутствуют среди 505 symbols. Отсутствие SIVB в архиве не ошибка состава 2018: его индексное включение позже cutoff; это иллюстрация ограниченности выбранной universe. Нельзя считать survivors 2018 историческим полным составом каждого индекса.

## Как читать таблицы

annual-price-coverage.csv: 68 source/year rows с original/new/union member-days, дополнительным MA50/MA200 и departed coverage. all-ticker-price-coverage.csv: все 2819 source/ticker candidates, включая not acquired. MA counts требуют последовательных reference sessions, без заполнения дыр и без переноса warmup через разрыв между архивом 2018 и исходными ценами 2020. Они остаются candidate, confirmed_pit_days=0. Старые и новые данные не перекрываются по датам; union counts сложены после явной проверки раздельности. Цена не используется для восстановления состава.

## Вывод и следующие шаги

Предыдущая оценка 0.64%/3.12% отражала только прежний архив, а не максимум бесплатного рынка. Новый законно опубликованный набор повышает приобретённое покрытие примерно до 26%, и departed subgroup больше не имеет нулевого acquired coverage. Это не снимает основного NO-GO: нет полной непрерывной истории 2010–2026, verified historical security IDs/memberships/publication vintages, corporate-action/delisting completeness. 2010–2012 и существенные части остальных лет остаются непокрытыми; ошибка выборки по survivors 2018 известна.

Следующий research шаг: источники с explicit delisted/security-ID/adjustment contracts и лицензией; сверка конкретных банкротств/поглощений до 2018 и gaps 2018–2020, без наращивания survivor coverage как доказательства unbiased history. Norgate остаётся лишь условным personal-use кандидатом; покупка не одобрена. Production/trading, merge и deploy не менялись.

## Воспроизведение

`python research/free_historical_index_data/continue_prices.py --archive /tmp/sandp500-v4.zip --fetch`

По умолчанию режим offline; --fetch делает один versioned public archive download только если файла нет, затем проверяет фиксированные ZIP и CSV SHA256. Старые membership snapshots/годовые таблицы остаются pinned inputs. Для независимого output использовать --output /tmp/price-replay. `python -m unittest discover -s research/free_historical_index_data -v` запускает исходные и новые tests. Проверки и повторное сравнение — verification.json.
