# Рекомендация

**GO для data engineering / NO-GO для полноценного predictive Breadth backtest на этих входах.** Это рекомендация исследования, не утверждённое решение владельца.

1. Сохранить все раздельные candidate histories и unresolved discrepancies; не объявлять fja/thuning согласие независимой проверкой и не усреднять составы.
2. Для каждой ticker interval получить issuer и security IDs, effective/announcement timestamps, share class, predecessor/successor corporate-action evidence. Начать с Google, META, Endo, Comcast, GM/DELL/CEG и повторно использованных тикеров; не переносить историю новой security на старую.
3. Квалифицировать цены: missing/delisted/acquired/bankrupt securities, exchange sessions, split/reverse-split/dividend basis, listing endpoints и publication vintages. Единый qualified denominator должен включать прошлые выбывшие securities; высокий survivor coverage недостаточен.
4. Для бесплатного маршрута сначала согласовать законный источник полного OHLCV/delisted archive и лицензию thuning. В этой работе весь free-provider market не исчерпан; недоступность одного endpoint не означает, что бесплатного решения не существует.
5. Для личного некоммерческого проекта Norgate US Platinum $630/год — разумный кандидат, если ценность сэкономленного времени выше суммы и устраивают retention ограничения. Сначала сверить sample спорных периодов и supported access. Для коммерческого/публичного продукта этот plan не обоснован как готовое лицензирование. См. free-vs-paid-comparison.md и первичные ссылки.
6. Лишь после qualification — отдельный заранее замороженный протокол исследования Breadth; текущая задача не создаёт стратегию, пороги, прогнозы или backtest returns.

Исследование расширяет PR13 (371d7a1135e35f96b5f7583bddc6de1ea007bf82): проверяет три конкретных бесплатных membership sources, поэтому не повторяет прежний supplier survey без обоснования. Paid recommendation не равна разрешению покупать. Production, торговля, merge и deploy не выполнялись.
