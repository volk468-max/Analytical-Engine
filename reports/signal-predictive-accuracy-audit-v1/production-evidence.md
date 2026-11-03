# Evidence inventory

|Категория|Строк|Значение|
|---|---|---|
|CONFIRMED_PRODUCTION|0|No original decision payloads obtained; UNKNOWN, not HOLD|
|SAVED_RESEARCH_OVERLAY|111|Research snapshots, not original production timestamps|
|SAVED_RESEARCH_FORECAST_STATE|111|Research forecasts/states, not scored as production|
|SAVED_RECONSTRUCTED_SECTOR_ACTIVATIONS|134|Immutable PR11 algorithm reconstruction; the evaluated warning sequence|
|NEW_RETROSPECTIVE_OUTCOME_ROWS|4646|Stock/market and OPEN/CLOSE labels; not new trading signals|

Current main risk.py и investment_memory.py доступны как код с SHA; это не historical output archive. В пакетах нет подтверждённых дневных результатов действующего production RiskEngine за2021–2026. Есть111 Overlay research records и111 Forecast states из поздних исследований AMD/NVDA/MU за1сентября–22октября2026, а не реальные первоначальные payloads. Их разные семантики не подмешиваются к sector precision.

В PR9 read-only provider metadata: app source main, latest deployment создан15октября, DATABASE_URL configured; values не запрашивались. Bounded filtered logs вернули0, retention unknown. Этот архив не доказывает отсутствия production предупреждений или данных вБД. В данном аудите сервисные endpoints/SQL вообще не вызывались: некоторые endpoints способны сохранять записи. Для проверки настоящей точности нужны original timestamped decisions/inputs/model config. Отсутствие записи UNKNOWN, никогда HOLD.

Секторные134активации сохранены после реконструкции вPR11. Новая работа только вычисляет outcome labels и контрольные сравнения, не создаёт production торговых сообщений. Главное заключение относится кэтому реконструированному алгоритму при допущениях о доступности.
