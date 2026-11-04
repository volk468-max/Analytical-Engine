# Журнал изменений

Формат новой append-only записи: дата UTC | ID | автор/роль | тип fact/hypothesis/recommendation/owner-decision/status/correction | что/почему | PR | source SHA | affected files | supersedes ID (если нужно). Итоговый commit самой записи берётся из Git history, чтобы избежать self-referential SHA.

- 2026-11-04 | K001 | Codex | fact/status/recommendation | Первичный каталог 13 PR, чтение pinned отчётов и main; #14 вернул 404. Приведены ограничения восстановления. PR и source SHA: research.json, sources/PR01-v1.json–PR13-v1.json; affected: knowledge folder, AGENTS.md, validator/workflow/tests. Owner approval только для scope D001; research recommendations не утверждены.

Не редактировать старые записи; correction добавляет новый ID и ссылку на исправляемый. Локальные/CI проверки проверяют append-only сохранность baseline при --base-ref.
