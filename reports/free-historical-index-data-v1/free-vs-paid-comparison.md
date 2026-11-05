# Бесплатные источники и платная альтернатива

| Вариант | Что проверено | Что не решено |
|---|---|---|
| Три GitHub membership repositories | Файлы, диапазоны, hashes, daily reconstruction, конкретные ошибки | Complete PIT/security histories, независимость, downstream licences |
| Alpha OS PR11 prices | Реально полученные 31248 строк, 19 инструментов; pinned provenance | 2010–2019, выбывшие securities, полные индексы |
| Stooq | Страница db/h требует browser verification; один CSV probe вернул HTTP404 | Допустимая массовая выгрузка и полный delisted archive не подтверждены; обходов/повторов нет |
| Alpha Vantage | Официальная daily documentation: compact=100 bars free/premium; full premium | Без настроенного ключа/entitlement полная daily история бесплатно не получена |
| Norgate US Platinum | По документации active+delisted, historical SP500/NDX memberships и 1990+ prices; $630/12мес или $346.50/6мес | Sample data не куплены/не валидированы; rights и Windows NDU setup отдельно |

Проверено 2026-11-04: [Stooq download](https://stooq.com/db/h/), [Alpha Vantage daily docs](https://www.alphavantage.co/documentation/#daily), [Norgate pricing](https://norgatedata.com/stockmarketpackages.php), [content](https://norgatedata.com/data-content-tables.php), [licensing FAQ](https://norgatedata.com/faq.php), [EULA](https://norgatedata.com/subscribe/eula.php). Никакие undocumented Yahoo chart массовые запросы не запускались; reused Yahoo archive не даёт разрешения на новую выгрузку/публичную перепубликацию raw.

Norgate заявляет constituents SP500 с 1957 и Nasdaq100 с 1990; доступ Platinum/Diamond. Это documented vendor coverage, не независимо проверенная полнота покупного набора. Для личного 2010–2026 исследования Platinum по глубине достаточен, Diamond ради pre-1990 не нужен. $630 — текущий ориентир за data subscription, без Windows host/налогов/хранения. NDU для загрузки нужен Windows; Python/приватная обработка экспортов на Linux/cloud допускаются в пределах personal use.

FAQ на дату проверки не предлагает business/commercial licensing. Публичный GitHub/shared raw dataset не разрешён этим personal plan. При прекращении entitlement underlying raw/normalized data и metadata нельзя бессрочно хранить; собственные уникальные исследовательские выводы отделяются от underlying data. Поэтому подписка может ускорить личный аудит, но не создаёт постоянную общедоступную базу Alpha OS. Перед решением о покупке определить владельца данных, режим использования и допустимость хранения; коммерческий проект потребует поставщика с подходящей лицензией.
