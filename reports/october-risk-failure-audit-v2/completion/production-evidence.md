# Production evidence — read-only

|Категория|Получено|Интерпретация|
|---|---|---|
|Подтверждённые production-сигналы|0 payloads|UNKNOWN, не HOLD|
|Сохранённые research snapshots|222 Overlay/Forecast строки|Архив PR-цепочки, не production|
|Ретроспективные расчёты|10 новых переходов флагов в44 сессиях|Фиксированные diagnostic rules, не сообщения Alpha OS|
|Недоступные решения/позиции/заявки|Нет read-only SQL/export|UNKNOWN, сделки не реконструируются|

Проверены provider describe-service и get-logs. Service source repo соответствует репозиторию, branchmain, latest deployment SUCCESS создан15 октября. Список variable names включаетDATABASE_URL; значения не запрашивались. У среды нет boundDATABASE_URL/readonlySQLconnection. Детальный sanitized результат в platform-evidence.json. Запрос deploy logs за1сентября–3ноября, filter Investment Memory, limit200 вернул0. Retention/completeness неизвестны: это не доказательство отсутствия сохранённых решений. Пейлоады исторических торговых заявок не доступны.

Текущая main DecisionEngine-v1.1 и investment_memory.py исследованы read-only. Исследовательские Overlay/Forecast находятся в отдельных ветках, а не в main; их прошлые артефакты и версии зафиксированы исходными sources.json. Ни current source main, ни latest deployment metadata не доказывают точную версию/конфигурацию в каждый день сентября. Полный исторический replay с несуществующими fundamentals не выполнялся.

Приложен saved-research-evidence.csv; дата в строке — историческая метка исследования, не подтверждённая дата production-расчёта. Для причинной атрибуции нужен read-only экспорт инвестиционных решений с created_at, полными входами и model/config version, deployment chronology, holdings и execution logs. Без них нельзя утверждать, что Alpha OS выдала HOLD, проигнорировала предупреждение или реально сэкономила/потеряла конкретную сумму. Никакие productionHTTP endpoints, SQL, записи или торговые заявки не выполнялись.
