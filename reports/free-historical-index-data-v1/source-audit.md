# Аудит исходных источников

Дата проверки 2026-11-04. Все входы скачаны по commit URL, SHA256 и Git blob SHA сверены; source-manifest.json содержит 20 файлов. Код авторов прочитан как данные, не запускался. Source-statistics.csv — проверенные размеры/диапазоны. Последний commit репозитория не доказывает последнюю торговую дату или полноту каждого файла.

| Источник | Commit / дата commit UTC | Проверенные файлы и глубина | Идентификаторы / права |
|---|---|---|---|
| fja05680/sp500 | a2430f2af0c79ddf0748e91de11bdeb1616ab5a7 / 2026-09-07 | 2720 snapshot rows, 1996-01-02–2026-08-18; в исследуемом окне 496–507 securities | date/tickers; стабильных IDs/имён в историческом CSV нет; LICENSE MIT, underlying Clenow/book-data provenance отдельно не аттестована |
| thuningxu/sp500nq100 | 1cc1de2770874293597a418b41b079e5337b260c / 2026-06-07 | SP 2712 rows 1996-01-02–2026-06-02; NDX 112 rows 2007-02-01–2026-05-18, 100–108 securities | date/tickers; IDs нет; LICENSE отсутствует в полном Git tree, явное разрешение downstream redistribution не установлено |
| lawcal/sp500-components-history | bb43682b4078a6266bc1ad157f3e1ec8b12af31f / 2026-10-26 | 1005 interval records; reconstruction поддерживается с 2007-03-05, хотя date_added отдельных строк старше; latest created_at 2026-10-08; 484–506 securities по helper | symbol/cik/name/sector/date_added/date_removed/created_at; 898 source issuer CIK, security ID нет; MIT |

## Реальная реконструкция

fja/thuning: последний snapshot с date<=session; до первого snapshot — отсутствует. Между change rows переносится прошлое состояние; отсутствующая daily row не означает пропуск, это sparse change format. Дубли дат/тикеров проверены: 0/0 в трёх snapshot CSV. Совпадение SP thuning/fja не независимо: build.py прямо использует fja base, причём pinned filename в URL относится к движущемуся master, не commit. В этой работе входы закреплены на SHA.

Lawcal: применён опубликованный helper-contract max(date_added,created_at)<=date<date_removed; * сохранён как approximate, не удалён из provenance. Вариант, использующий только declared dates без created_at, отличается в 4216 сессиях (lawcal-date-semantics.csv). Его нельзя без обоснования объявить исправлением: created_at также удерживает современные тикеры от переноса назад. В исходных строках 33 повторяющихся символа; это могут быть разные периоды/эмитенты, не дубли одной бумаги. 257 date_added и 131 date_removed помечены *. Названия свободные и не снабжены полными effective histories.

## Объявление, вступление и давность

В snapshot CSV дата названа effective автором, но независимых announcement/effective timestamps в строках нет. У lawcal created_at — revision observation date, а не гарантированное время публикации события. В membership-changes.csv announcement_date пусто, effective_date_verified=False; date — дата изменения source-derived daily state. Начальные состояния 2010 не выдаются за новые additions.

Использованы консервативно обозначенные верхние горизонты: fja 2026-09-07 (дата commit, лишь upper bound свежести), thuning 2026-06-06 (as-of контекст README/сборки), lawcal 2026-10-26 (commit upper bound). Даже внутри горизонта это APPROXIMATE_SOURCE_RECONSTRUCTION, не PIT certification. После него — STALE_UNCONFIRMED. Число stale sessions в 2026: 41 / 104 / 6 соответственно. Last change date не равна as-of completeness.

## Лицензии и данные

MIT в fja/lawcal относится к материалам в области действия LICENSE; он не подтверждает права на все исходные биржевые/Wikipedia/book databases и не отменяет условия upstream. У thuning явной лицензии не найдено: публичная видимость не даёт разрешение повторно распространять код/датасет. Raw upstream files и код не включаются в PR. Выходы — результаты фактического сравнения и реконструкции; для повторного использования/распространения их как готовой базы нужны отдельная проверка прав и при необходимости разрешение автора. Это audit limitation, не юридическая аттестация.

Pinned originals: [fja CSV](https://github.com/fja05680/sp500/blob/a2430f2af0c79ddf0748e91de11bdeb1616ab5a7/S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv), [fja README](https://github.com/fja05680/sp500/blob/a2430f2af0c79ddf0748e91de11bdeb1616ab5a7/README.md), [fja licence](https://github.com/fja05680/sp500/blob/a2430f2af0c79ddf0748e91de11bdeb1616ab5a7/LICENSE), [thuning SP](https://github.com/thuningxu/sp500nq100/blob/1cc1de2770874293597a418b41b079e5337b260c/sp500_components_history.csv), [NDX](https://github.com/thuningxu/sp500nq100/blob/1cc1de2770874293597a418b41b079e5337b260c/nasdaq100_components_history.csv), [build](https://github.com/thuningxu/sp500nq100/blob/1cc1de2770874293597a418b41b079e5337b260c/build.py), [lawcal intervals](https://github.com/lawcal/sp500-components-history/blob/bb43682b4078a6266bc1ad157f3e1ec8b12af31f/data/components_history.csv), [helper](https://github.com/lawcal/sp500-components-history/blob/bb43682b4078a6266bc1ad157f3e1ec8b12af31f/bin/update.py), [licence](https://github.com/lawcal/sp500-components-history/blob/bb43682b4078a6266bc1ad157f3e1ec8b12af31f/LICENSE).
