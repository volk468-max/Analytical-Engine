# Data contract v1

Канонический transport — UTF-8 JSON bundle `{"manifest":...,"payload":...}`. Для объёма допустимы приватные Parquet tables, но сначала adapter обязан материализовать эквивалентные поля/инварианты. Никаких provider rows в публичном GitHub. Исполняемый пример полного формата: research/breadth_pit_qualification/synthetic-bundle.json, все значения вымышлены.

## Manifest

schema_version=1; data_kind=synthetic|vendor_export; start/end ISO inclusive horizon; retrieved_at UTC; entitlement_expires_at UTC; purpose=personal_research; private_processing/licence_reviewed booleans; history_basis=historical_all_members; security_master_reviewed/actions_reconciled booleans; payload_sha256 — SHA256 канонического JSON payload (sort_keys, separators без пробелов, allow_nan=False). Изменение payload без нового hash запрещено.

Для реальной поставки в private envelope дополнительно обязательны exporter code SHA, SDK/NDU version, account-purpose review reference (не пароль), provider dataset revision/local-update receipt, query window, padding/adjustment settings, licence version/expiry, file hashes, encryption/storage/deletion inventory. Текущий validator не проверяет эти внешние файлы или истинность подписей review: это обязательная human qualification, не программная аттестация.

## Payload tables: исполняемые поля

| Table | Поля / семантика |
|---|---|
| provenance | id, sha256 (64hex), reviewed bool; row source_id ссылается сюда. Хеш внешнего файла подтверждать отдельно; одна строка с хешем не доказывает подлинность |
| securities | security_id с namespace, issuer_id отдельно, from/to listing-life ISO [from,to), exit_type active/delisted/bankrupt/acquired, source_id. Norgate AssetID — ID бумаги, CIK — issuer, их нельзя взаимозаменять |
| tickers | security_id, exchange, symbol, from/to [from,to), source_id; запрет concurrent symbol reuse на одной площадке и пересечений alias intervals одной security. Разные share classes могут иметь один issuer_id |
| calendar | session ISO, open_at/close_at/decision_at timezone-aware UTC, source_id. Все ожидаемые sessions, holidays/early closes/DST подтверждаются внешним exchange calendar |
| memberships | index=SP500|NDX100, security_id, from/to effective-date interval, available_at UTC, availability_verified bool, source_id. Точно определён session-open effective; intraday events вне этого v1 режима требуют отдельного contract |
| prices | security_id, session, open/high/low/close/volume numeric finite, adjustment_basis=unadjusted, padded=false, available_at UTC, availability_verified bool, source_id. Prices вне listing life/календаря, duplicate keys, invalid OHLCV отклоняются |
| actions | security_id, type, ex_date ISO, ratio для split/reverse_split (>0), available_at, availability_verified, source_id. Это typed ledger, не голый бинарный event flag |
| reference | independent/reviewed booleans, source_id, members: index/session/security_ids. Для каждого index/session полный ожидаемый набор; самосверка current list с его собственной реконструкцией не независимый reference |

Отдельные optional evidence поля в приватном ledger: announced_at, effective_at (exchange timezone и UTC), observed_at, revision_id, supersedes_revision, original provider value, adjustment factor vintage, successor_security_id, distribution type/cash/currency/payment_date. Валидация полного typed corporate-action reconciliation и revision graph в этот executable v1 не входит; `actions_reconciled` требует ручного evidence. Нет объявления даты — null, не estimated midnight с verified=true.

## Bitemporal / PIT policy

Effective date отвечает «когда входило», available_at — «когда мог знать исследователь», observed/retrieved_at — «когда получили эту версию». Применять запись в decision D можно только если effective interval включает session и available_at<=D. Сегодняшняя пересчитанная membership series — не доказательство original announcement/publication vintage. Если SDK не даёт такой evidence, export остаётся retrospective engineering data и strict PIT gate блокируется.

Raw bars с actions хранятся отдельно. Будущий split/dividend нельзя применять к прошлому prefix без доказательства causal adjustment convention. TOTALRETURN не подменяет raw close, не смешивается с unadjusted OHLCV. Для будущего Breadth MA нужна отдельно проверенная causal corporate-action normalization; текущий validator лишь считает доступный raw warmup, не вычисляет торговые сигналы и не признаёт raw MA через split экономически сопоставимым.

Coverage denominator — независимый expected security/session set; missing bars/halt/delist не удаляются из него. Cohort departed определяется security status, а не отсутствием current ticker. Срезы по index/year и departed cohort обязательны; coverage=98% сам по себе ничего не доказывает. Empty cohort — NOT_EVALUATED. MA50/MA200 считают последовательные reference sessions; пропуски и padding не заполняются. Начало двухлетнего окна закономерно не имеет 200 observed warmup; план должен заранее выделить warmup либо сократить область выводов.
