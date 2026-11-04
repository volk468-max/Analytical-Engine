# Историческая достоверность и полнота

## Статус

Ни один полный год не квалифицирован как complete verified PIT history. Подтверждены факты о скачанных файлах, вычисленных расхождениях и отдельные первичные события; это не аттестация полной базы. Daily output содержит quality и full_membership_verified=False; approximate и stale не смешиваются с confirmed.

Сохранены 16940 source/date rows и source-separated ticker lists (daily-membership.csv.gz.b64). Имеются 68 годовых строк, 2819 source/ticker inventory rows, 847 интервальных расхождений. Семейства источников не независимы: fja/thuning SP — одна основа; lawcal тоже использует Wikipedia, хотя иной способ реконструкции. Нет третьего официального эталона всего периода.

## Конкретные ошибки, проверенные первичными источниками

- **Google:** fja и thuning SP показывают GOOGL до 2014-04-03. По [Nasdaq symbology notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2014-24), до этой даты class A торговался как GOOG, затем GOOGL; новый GOOG — class C. У lawcal helper обе Google-линии отсутствуют на 2010-01-04 из-за date_added/created_at. Один CIK не делает эти две акции одной ценной бумагой. [S&P notice](https://press.spglobal.com/2014-02-03-Treatment-of-Google-Stock-Split-in-the-S-P-100-and-S-P-500) подтверждает две линии с апреля 2014. Составы не исправлялись вручную.
- **META:** lawcal начинает META 2022-06-08 и прекращает FB тем же днём, тогда как [сообщение эмитента](https://investor.atmeta.com/investor-news/press-release-details/2022/Meta-Platforms-Inc.-to-Change-Ticker-Symbol-to-META-on-June-9/default.aspx) и [Nasdaq](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-125) указывают effective 2022-06-09. Announcement был 2022-05-31; ни announcement, ни revision date не заменяют effective date.
- **ENDP:** thuning Nasdaq не содержит исторического ticker ENDP вообще. [Nasdaq annual announcement 2015](https://ir.nasdaq.com/news-releases/news-release-details/annual-changes-nasdaq-100-index-4) включает его с 2015-12-21; [Nasdaq 2016 removal notice](https://ir.nasdaq.com/static-files/2475f257-006d-44c4-8693-efa058adfef4) заменяет его MCHP с 2016-07-18. В ряду встречается NDOI уже до 2010; без security mapping его нельзя автоматически считать тем же ENDP. Это identity/membership gap, а не доказательство отсутствия компании в каждой строке под любым alias.
- **CMCSK:** ticker отсутствует во всех snapshots thuning Nasdaq. [Nasdaq announcement 2014](https://ir.nasdaq.com/news-releases/news-release-details/annual-changes-nasdaq-100-index-3) добавляет именно class A Special CMCSK с 2014-12-22, а не сегодняшнюю произвольную линию Comcast. [Comcast](https://corporate.comcast.com/news-information/news-feed/comcast-shareholders-approve-the-reclassification-of-each-share-of-class-a-special-common-stock-into-one-share-of-class-a-common-stock) сообщает прекращение торговли после 2015-12-11. Отдельная официальная index-removal effective дата этим corporate event не подменяется.
- **NLOK/QRTEA:** в Nasdaq snapshots эти символы есть уже в 2010. [Эмитент/Nasdaq NLOK](https://www.nasdaq.com/press-release/symantec-completes-sale-of-enterprise-security-assets-to-broadcom-2019-11-04) указывает symbol change с 2019-11-05, [QVC issuer](https://investors.qvcgrp.com/news-media/press-releases/detail/14/liberty-interactive-and-gci-liberty-announce-completion-of) — QRTEA с 2018-03-12. Следовательно, декларация README о чистом 2017+ окне не заменяет проверки ticker validity.

Точные first/last dates каждого S&P разногласия, ticker, имена/CIK при наличии и обе pinned ссылки: source-disagreements.csv. Это не список произвольно выбранных исправлений. Primary findings отдельно воспроизводятся primary-checks.csv и кодом inspect_primary.py.

## Цены и survivorship

| Source | Candidate ticker histories | Observed departed tickers | Archived OHLCV member-days / candidate member-days | Coverage |
|---|---:|---:|---:|---:|
| fja_sp500 | 848 | 345 | 13660 / 2126329 | 0.6424% |
| thuning_sp500 | 841 | 338 | 13660 / 2126328 | 0.6424% |
| thuning_ndx | 241 | 140 | 13596 / 435613 | 3.1211% |
| lawcal_sp500 | 889 | 386 | 13661 / 2116199 | 0.6455% |

Всего архив содержит 31248 строк по 19 инструментам с 2020 warmup. Для 2010–2019 acquired coverage=0%, а не утверждение о недоступности бесплатных цен в мире. Для source-observed departed subgroup acquired exact-ticker member-days=0 во всех четырёх рядах. Одна security может появляться под несколькими tickers, а один ticker принадлежать разным securities; число тикеров не равно числу компаний.

Delisted-price-coverage.csv проверяет наличие цены для каждого source/ticker/member-session в доступном архиве. exchange_delisted_status=UNKNOWN не подменяется index exit. Нет индивидуальных live API запросов ко всем бумагам; NOT_ACQUIRED_NOT_PROOF_UNAVAILABLE означает именно отсутствие среди полученных входов. Банкротные/поглощённые/переименованные истории остаются неподтверждёнными, не заменяются ценой покупателя/новой акции. CIK сохраняется как source issuer evidence, security_id пуст до доказательства; lawcal record ID — лишь локальный ключ записи.

Цены — provider split-adjusted OHLC, не dividend-adjusted close. Повторно сплиты не применяются; corporate actions и raw hashes остаются в PR11 manifest. Ни original vintage accuracy, ни полнота reverse-split/merger/delisting handling во всей индексной вселенной не установлены. Generic OHLCV/duplicates checks пройдены для полученного архива; это не проверка отсутствующих бумаг. Дыры не заполняются.

MA50/MA200 candidate counts требуют 50/200 последовательных reference sessions с полученными closes, включая текущую. Это техническая доступность ряда, а не историческая квалификация: confirmed counts=0, поскольку исходные publication/security/membership gates не пройдены. Число confirmed_components=0 означает «не аттестовано этим аудитом», не «в индексе нет настоящих компаний».

## Bias gates

No future snapshot применяется алгоритмически, но surviving-current anchor и неполный backward change log могут давать survivorship/look-ahead artefacts в исходнике. Ретроспективные исправления источника не являются оригинальными PIT vintages. High numerical coverage или совпадение источников не исключают bias. Подмены символов автоматически не делаются; даже законный FB/META mapping потребовал бы явного issuer/security validity contract и отдельного результата. Полное certified coverage по компаниям/бумагам вычислить нельзя: неизвестен истинный denominator. Публикуется только source-derived ticker denominator и acquired lower bound.
