# Альтернативы при неподходящей лицензии/Windows архитектуре

Это предварительная оценка официальной документации; котировки/подписки не запрашивались. Условия enterprise pricing, сохранения после termination, cloud processing и точная 2010–2026 depth требуют contract review и sample. Нет утверждения об автоматически разрешённой коммерческой лицензии.

| Кандидат | За что рассматривать | Блокеры / условия |
|---|---|---|
| CRSP US Stock / Indexes через институциональный доступ или договор | Постоянный security PERMNO отдельно от company PERMCO, active/inactive prices, distributions/delist data; хорош для independent cross-check | S&P constituent product/coverage и точный Nasdaq100 membership нужно подтвердить отдельно; цены сами не гарантируют оба index histories; third-party redistribution/retention не предполагается |
| EODHD historical constituents + prices | HTTP/cloud architecture, documented S&P membership add/remove log | SP continuous history начинается2012-04-04, не2010. Marketplace other indices требуют проверки NDX origin/depth/IDs/actions/лицензии; не считать решением всего периода |
| AlgoSeek US Equities Index Components + prices | Документирован PIT component endpoint и API-based workflow | Документация прямо говорит Nasdaq100 based on QQQ holdings. ETF holdings не эквивалентны официальному индексу; без independent effective-date qualification — proxy-only/NO-GO для exact NDX |
| Прямые licensed S&P DJI/Nasdaq index notices/history + отдельный licensed price/security master | Разделить официальный membership и независимый security/price источник | Нужны права join/derived/cloud/retention, документированная история IDs, duplicate share classes и timing; не сделан готовый export |
| Бесплатные источники PR15 | Полезны как diagnostic discrepancy/reference candidates | Общая fja lineage, stale/ambiguous symbols, survivor-selected prices; около26% acquired candidate member-day coverage не является certified PIT |

Практический выбор: если только Windows нежелателен, single-user Windows extractor + Linux private processing может устранить архитектурный барьер без смены вендора. Если цель коммерческая/публичная либо нужен бессрочный licensed archive, выбирать договор с подходящими правами, а не personal Norgate plan. Никакой поставщик не освобождает от независимого validator/reference и human review.

Primary sources: https://www.crsp.org/research/crsp-us-stock-databases/ и https://www.crsp.org/wp-content/uploads/guides/CRSP10_Year_US_Stock_Database_Guide.pdf ; https://eodhd.com/financial-apis-blog/sp-500-historical-constituents-data ; https://algoseek.com/docs/rest-api/reference/endpoint-v-1-data-us-equity-ref-index-comp-get .
