# Матрица квалификации источников — НЕ live feed approval

Read-only проверен **код**, не работающий Railway API. Collector commit
`ef80df85b5faead5068854afbf9517f97cf9ba00`; точные paths/blob hashes в source-inspection.json.
Source main не доказывает deployed SHA. Старый Railway inventory v1 — отдельный
checkpoint; environment/services не изменялись и production DB не подключалась.

| Контракт / свойство | Что действительно найдено | Gate / что отсутствует |
|---|---|---|
| MarketRecord | symbol,name,asset_type,currency,open,high,low,close,volume,trade_date,metadata | Наличие полей не подтверждает freshness/availability |
| metadata | provider,version,latency_ms,quality_score,timestamp | timestamp создаётся datetime.utcnow(), без UTC offset; это generation time, не публикация биржи |
| Дополнительный snapshot | previous_close,regular/pre/post market price/change/pct,market_state; storage также сохраняет MA20/50/100/200,RSI,MACD,ROC20,volatility20 | Не нужны как замена causal raw/action lineage; качество не аттестовано |
| GET /market/history/{symbol} | symbol,count,records; limit1…5000/default250; storage OHLCV/provider/version/created_at | Не raw exchange response, нет настоящих publication/ingestion fields и original vintage |
| GET /market/snapshot,/market/*,/runs | Read handlers существуют в source | Даже repository()->Database() запускает CREATE/ALTER/init_schema с commit; HTTP GET не гарантирует read-only |
| POST /collect/*; app lifespan | Collection writes; lifespan запускает scheduler | НЕ вызывались и НЕ импортировались |
| Покрытие конфигурации | SPY,QQQ,AMD,NVDA,MU входят в universe | SOXX отсутствует; actual endpoint coverage и fresh rows НЕ проверены |
| История | get_history period2y, provider config1y; yfinance>=0.2.40, не pinned | Не доказано покрытие/доступность длинной истории; запросы не выполнялись |
| Corporate actions / adjustment | Yahoo history(auto_adjust=False), OHLCV извлекаются в MarketRecord | Dividends/Stock Splits не передаются в этот контракт; independent actions/basis не подтверждены; auto_adjust=False не означает отсутствие split normalization |
| Винтажи | market_history UNIQUE(symbol,trade_date), INSERT OR REPLACE | Предыдущий вариант теряется, original raw bytes/hash не сохраняются |
| Currency | Yahoo adapter присваивает USD | Не независимая проверка каждой бумаги/листинга |
| Лицензия | README yfinance указывает Apache для кода и отдельно отсылает к Yahoo terms для данных; personal-use notice | Нет проверенного owner-specific разрешения на автоматический сбор, долговременный архив и дальнейшее использование; open-source code не даёт data rights |
| Retention / redistribution | В проверенном коде нет contract-specific retention policy или raw archive SLA | Сроки, redistributions, raw backup/WORM rights НЕ согласованы |
| Reliability / release SLA | quality_score = доля успешно загруженных symbols | Это не измеренная latency публикации, не SLA, не action/PIT certification |
| PR20 / PR24 / PR26 | Frozen source hashes и numerical labels доступны локально | RESEARCH_PRICE_REPLAY_NOT_PIT; не live source; PR26 0/9 и unvalidated thresholds сохраняются |

**Конкретный внешний blocker:** отсутствует проверенный разрешённый live контракт,
который одновременно предоставляет нужное покрытие6symbols, actual publication UTC,
actual raw-response ingestion/archive и независимо проверенную action/price basis.
Нельзя исправить это добавлением выдуманного timestamp к collector metadata.

Поэтому network live adapter не реализован/не подключён. Рабочий fail-closed
UnavailableLiveProvider выдаёт missing source с NULL publication/ingestion, source_present=false
и конкретным reason. Empty bytes означают отсутствие ответа, не якобы полученный raw
payload. Все genuine live P остаются NULL. Отдельный FixtureProvider и WindowFixture
проверяют контракты только в SYNTHETIC staging; не являются live adapter.

Для снятия blocker необходим source contract с документированными правами/retention,
полными OHLC/actions/NAV inputs и availability UTC, read-only-safe integration boundary,
отдельно reviewed ingestion adapter и audit доказательств. Автоматически менять
существующий collector, источники, production или покупать подписку не разрешено.
