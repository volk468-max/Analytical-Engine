# Validation / evidence limits

## Контроль и данные

PR10 snapshots37files с SHA256. До длинного теста control.py подтвердил4 даты (1сентября,14сентября,8октября,2ноября2026),44daily sector states,15generated artifacts byte-for-byte,66 адаптированных engine cases. Новый длинный Yahoo pack также совпал по2730 overlapping bars OHLC и датам. Gate failure прерывает процесс до long economics.

Formula: seven fixed semis AMD/NVDA/MU/TSM/AVGO/AMAT/LRCX; five-session returns;>=4negative AND equal mean<QQQreturn5. Полнота7+QQQобязательна; prev-state хранится через warmup, true transitions, не ежедневные повторы. Контекст SOX/SOXX/SMH/SPY/indices/VIX не входит в сигнал. Future suffix mutation/invariance проверяется.

Provider raw includes OHLCV, actions, source URL, retrieval time, firstTradeDate and hashes; регулярная сессия includePrePost=false. XNYS1465sessions, DST/holidays и eligibility проверены; missing invested-session quote запрещает расчёт, не заполняется forward fabricated price. NBIS только21октября2024, с issuer/exchange reference, без suspended YNDX splice. Прогрев2020; PLTR с30сентября2020, доступна на старте2021.

## Корпоративные действия и единицы

OHLC provider split-adjusted, без использования dividend-adjusted adjclose. Внутренний ledger в одной terminal share unit, с counterpart nominal shares/prices. Для исторического дня factor=product splits AFTER day: nominal price=adjusted price×factor, nominal shares=normalized shares/factor. Это восстановление единиц, не торговый признак. Экономический return5 эквивалентен nominal return с ONLY splits уже effective между двумя датами;35 split-crossing windows проверены. Дополнительная метаморфная проверка пересчёта всех цен/количеств в4раза сохраняет NAV. Для лота черезsplit actual current limit и quantity меняются обратно/прямо пропорционально, стоимости совпадают.

Yahoo dividend events интерпретируются в той же split-normalized unit, gross entitlement наex-date поpre-open shares. Нет выдуманных pay dates, withholding/tax/ADRfees или dividend reinvestment. Нерасходуемый receivable включён в NAV и отдельно в долях портфеля. При разрешённом exact-quantity buyback net proceeds сами покрывают target и комиссию; receipts не нужны для финансирования. Первичные исходные корпоративные vintages не аттестованы независимо.

## Прогоны

Тесты:30 inherited PR10 execution checks направлены на исторический adapter без копирования логики; новые проверки control/raw/calendar/eligibility/splits/nominal value/costs/annual continuity/NAV/production categories/prior-policy adapter. Финальный прогон:54passed (2main+30inherited execution+22historical/data/accounting checks),0failures,1anyio deprecation warning. GitHub read-back — verification.json. Старые203 tests из иной PR-цепочки не заявляются. pytest deprecation warning anyio относится к окружению.

PR9 restoration policy воспроизведена в optional E: source unchanged кроме START2026-09-01→2021-01-01. Проверка source text ровно одна замена; CSV prior-* и original source hashes опубликованы. Это legacy tactical policy, не полный DecisionEngine с придумыванием отсутствующих historical fundamentals. Стоимость риска E почти как B&H, поэтому её похожая доходность не означает хорошую protection.

## Неподтверждённое

Нет original publication feeds/attested timestamp/vintages, production decisions/orders/holdings. Next-midnight availability — сохранённое модельное допущение. Exact real queue/limit fills/volume impact не подтверждены; base touch и strict5bp penetration/gap-cap stress опубликованы. Calendar availability известна на дату, будущие highs/lows — только execution assumptions/outcome labels; не predictors. Gross open proceeds не profit. Весь current-survivor universe biased, no delisted panel. Нельзя считать multi-use2021–2026 независимым holdout. Метрики rf0%, vol sqrt252/sample std, CAGRactual calendar, periods<year CAGRblank.

## Offline reproduction

Python3.12, Node24, pytest9.2.0, exchange-calendars4.13.2. Fetch_data.py только для НОВОГО snapshot, не повторять для идентичности. Все остальные шаги читают замороженные inputs.

~~~bash
python -m research.historical_sell_buyback.control
python -m research.historical_sell_buyback.prepare
python -m research.historical_sell_buyback.run
python -m research.historical_sell_buyback.prior
python -m research.historical_sell_buyback.quality
python -m research.historical_sell_buyback.report
python -m pytest -q -p no:cacheprovider tests research/historical_sell_buyback
~~~

Dependencies устанавливаются в отдельный /tmp target, PYTHONPATH включает root и target; production requirements не изменялись. Никаких production calls/SQL/real orders/merge/deploy/force push.
