# Лицензия и жизненный цикл

Проверено 2026-11-05 по официальным FAQ N5 и EULA N6 (sources.json). Текст договора на фактическую дату trial/purchase имеет приоритет; это техническая интерпретация для проектирования, не согласование особых прав.

Документация разрешает personal non-commercial research владельца, в том числе private Linux/cloud processing разрешённых exports. Провайдер computing/storage не получает прав использовать данные для собственных целей. Нынешний FAQ не предлагает business/commercial licence. Если Alpha OS обслуживает клиентов/организацию или независимых пользователей, Norgate по текущим условиям — NO-GO до подходящего договора/альтернативы. Персональный Windows NDU и single-user cloud исследование принципиально выполнимы; это не разрешение публичного data service.

| Объект | Public GitHub | Приватно локально / в облаке | После окончания entitlement |
|---|---|---|---|
| Собственный код/схема/политики, вымышленные fixtures | Да, без скопированных licensed SDK/данных | Да | Сохранять собственный код |
| NDU database / backups | Нет | Только authorised personal use | Прекратить доступ, удалить копии по runbook |
| Raw OHLCV / normalized prices / membership / ticker & AssetID mapping / metadata / corporate actions | Нет | Пока действует entitlement, при разрешённых purpose/ACL | Удалить также exports, copies, snapshots, caches, object versions и backups |
| Реконструированные membership snapshots / преобразованные price time series / извлекаемые из них daily breadth rows | Не считать свободными от лицензии вследствие преобразования | Считать restricted до отдельного подтверждения | Удалять как underlying-content-derived rows при отсутствии явно применимого права retention |
| Per-security audit logs, provider IDs, row excerpts, content-bearing hashes/manifests | Не публиковать автоматически | Restricted provenance / diagnostics | Проверить и удалить metadata/copies; hash не очищает правовой режим |
| Собственные уникальные агрегированные выводы/модельные результаты, не воспроизводящие содержание | Только после privacy/licence review | Да в пределах применимых условий | По FAQ собственные уникальные результаты могут сохраняться; это не право сохранить исходные ряды |
| Документ о факте удаления без IDs/рынка/секретов | После review | Да | Сохранить безопасную attestation |

Private GitHub не выбран хранилищем licensed content: участники/CI/support могут получить доступ, а Git history/retention/backups затрудняют удаление. Git LFS, base64, gzip, derived columns и private repo не отменяют договор. Предлагаемая политика — любой GitHub только code/docs/synthetic; настоящие trial reports остаются в isolated restricted storage, GitHub получает лишь reviewed non-reconstructive conclusions.

Runbook перед импортом: inventory всех мест → назначить owner и expiry UTC → проверить отсутствие immutable snapshots/object lock → запрет replicating personal sync → на expiry заблокировать чтение/расчёты → delete raw/normalised/metadata/temp/cache/restricted outputs во всех locations → убрать версии и backups/либо cryptographic erasure по принятой политике и требованиям договора → проверить inventory и безопасную deletion attestation. Не считать завершением удаления простое удаление текущего файла или изменение policy. Эта работа runbook не исполняет: Norgate content отсутствует.

Источники: https://norgatedata.com/faq.php (personal/cloud/backup/retention), https://norgatedata.com/subscribe/eula.php (Personal Use, processing, content restrictions, Derived Data/retention). Нет бессрочного бесплатного двухлетнего архива: trial data под теми же ограничениями; истечение trial — тоже триггер retention review/deletion.
