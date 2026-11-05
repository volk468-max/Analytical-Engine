# Журнал изменений

Формат новой append-only записи: дата UTC | ID | автор/роль | тип fact/hypothesis/recommendation/owner-decision/status/correction | что/почему | PR | source SHA | affected files | supersedes ID (если нужно). Итоговый commit самой записи берётся из Git history, чтобы избежать self-referential SHA.

- 2026-11-04 | K001 | Codex | fact/status/recommendation | Первичный каталог 13 PR, чтение pinned отчётов и main; #14 вернул 404. Приведены ограничения восстановления. PR и source SHA: research.json, sources/PR01-v1.json–PR13-v1.json; affected: knowledge folder, AGENTS.md, validator/workflow/tests. Owner approval только для scope D001; research recommendations не утверждены.

Не редактировать старые записи; correction добавляет новый ID и ссылку на исправляемый. Локальные/CI проверки проверяют append-only сохранность baseline при --base-ref.

- 2026-11-05 | K002 | Codex | fact/status/recommendation | R14/R15 каталогизированы на pinned SHA; Q001 технический проект и synthetic gates, не реальные Norgate результаты. Источники PR13@371d7a1135e35f96b5f7583bddc6de1ea007bf82, PR14@f9288b42e0d58f521b57c420d79477d5aeb10459, PR15@90975c0acdda9c502c7b187c54d8d004b8f514b3, official docs reports/breadth-pit-data-qualification-v1/sources.json. Обновлены catalogue/status/limits/next steps; старые карточки/результаты не изменены. Новая работа — текущий Draft PR/SHA из Git history, без self-reference.
