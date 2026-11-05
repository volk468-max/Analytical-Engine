# План двухлетнего trial: не выполнен

Официальный N7: три недели доступа, два года исторических данных, equity trial Platinum-level с delisted и historical constituents. Это rolling limited history, а не разрешение выбрать любые два года 2010–2026 и не вечный бесплатный архив. За пределами trial-window нельзя проверить точную полноту ранних лет.

## До активации

Владелец определяет personal/commercial purpose, trial account/Windows environment и private processing terms, подписывает область хранения/удаления. Зафиксировать actual trial start/end/expiry и policy/SDK versions, бюджет всех расходов Windows/cloud; ничего не приобретать автоматически. Активация trial не делается в этом PR. Нужен доступ к реальной Windows NDU environment, которого сейчас нет.

## Трёхнедельная последовательность

1. Дни1–3: установить/проверить NDU+Windows Python; inventory всех доступных databases, stable AssetIDs и current/past members двух индексов. Пробный export нескольких полей; явно NONE adjustment/padding, захват версии и provenance. Сразу проверить remote expiry/deletion feasibility.
2. Дни4–8: полный daily universe trial-window, оба индекса, exits/halt/multiple classes/renames в ДЕЙСТВИТЕЛЬНО доступном окне. Создать независимый reference ledger по официальным index notices, exchange calendars и corporate filings. Не использовать Kaggle/current lists как истинный denominator. Сверить event effective vs announcement.
3. Дни9–13: price/action/identity qualification. Проверить реальный split, reverse split, takeover/bankruptcy/delisting и ticker change, которые попадают в окно. Нет редкого события в доступной выборке — NOT_EVALUATED, а не PASS и не synthetic substitute. Сверить raw / CAPITAL / TOTALRETURN и padding, adjustment volumes, duplicate/missing sessions. Native binary capital-event flag не превращать в выдуманные ratios.
4. Дни14–17: независимый validator на полной trial выборке, missingness по index/year/sector при наличии taxonomy и особенно departed cohort; compare extraction hashes/repeatability, prefix tests против более позднего snapshot. MA windows только там, где хватает warmup. Размеры срезов и неизвестности включить в private report. Никакого strategy fitting.
5. До expiry: human review GO/NO-GO, deletion dry-run на собственных synthetic copies и затем фактическое удаление trial content при прекращении прав. Экспорт в Linux должен остаться приватным; отчёты с IDs не выносить в GitHub.

## Gates (предложения, не решения владельца)

- Contract/purpose/cloud/retention legal gate: unresolved → NO-GO для покупки под эту архитектуру.
- 0 unresolved security-identity collisions, membership timing conflicts, unsafe future use или fabricated data; universe/reference comparison обязан выявлять и additions, и removals. 98% общий coverage не компенсирует исключённые bankrupt names.
- Численные пороги configurable в policy.example.json: overall>=0.98, departed>=1.0; это стартовый engineering policy, не statistical guarantee. Все пробелы должны быть классифицированы; материальная систематическая missingness → NO-GO независимо от суммы.
- Отдельное наличие реальных samples actions/renames/deaths, independent evidence и reproduce/prefix results. Не хватило trial-window → HOLD/NOT_EVALUATED, не полная успешная квалификация.
- GO_TO_CONSIDER_PURCHASE возможен только человеком для явно указанного личного использования после trial gates и согласованного retention бюджета. GO_TO_FULL_2010_2026_RESEARCH — отдельный последующий gate на платном историческом наборе; trial его не открывает.
- В отсутствие original historical publication/vintage evidence допустима лишь retrospective corrected-history engineering scope. Честный запрет строгой online/PIT predictive интерпретации сохраняется, даже если effective-date membership корректен.

Текущее решение: NO-GO для немедленной покупки/полного backtest, CONDITIONAL GO для организации trial после owner/licence/environment readiness. Это не утверждение, что Norgate не может подойти.
