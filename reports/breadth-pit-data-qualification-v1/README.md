# Breadth PIT Data Qualification v1

Технический проект и независимый offline-валидатор. Реальные данные Norgate НЕ получены, Windows/NDU/API НЕ запускались, trial НЕ активирован. Тесты используют вымышленные данные. Это не успешная квалификация поставщика.

Читать: [решение](decision-ru.md), [архитектура](architecture.md), [контракт](data-contract.md), [лицензия](licensing-and-retention.md), [trial](trial-plan.md), [альтернативы](alternatives.md), [валидация](validation.md). Официальные URL и HTTP-хеши документов — sources.json; они не являются лицензированными market-data exports.

Контекст: PR13@371d7a1135e35f96b5f7583bddc6de1ea007bf82 — нет qualified breadth inputs. PR15@90975c0acdda9c502c7b187c54d8d004b8f514b3 — acquired candidate coverage около26%, но не certified PIT. Knowledge PR14@f9288b42e0d58f521b57c420d79477d5aeb10459 прочитан; он остаётся Draft, не действующая production-функция. Новая ветка основана на PR14 и PR направлен в его docs-ветку, чтобы изменить реальную базу знаний, не переписывая чужой PR и сохранив историю. Runtime main не меняется.
