# Alpha OS — Project Knowledge System v1

Старт: [PROJECT_STATUS](PROJECT_STATUS.md) → [DECISIONS](DECISIONS.md) → [NEXT_STEPS](NEXT_STEPS.md), затем связанные [исследования](RESEARCH_INDEX.md).

| Документ | Назначение |
|---|---|
| [ARCHITECTURE](ARCHITECTURE.md) | Компоненты и потоки main |
| [DATA_INVENTORY](DATA_INVENTORY.md) | Данные, версии, качество |
| [RISK_MODELS](RISK_MODELS.md) | Исходный код и исследуемые модели |
| [BACKTEST_RESULTS](BACKTEST_RESULTS.md) | Исторические результаты без замещения |
| [OPEN_QUESTIONS](OPEN_QUESTIONS.md) | UNKNOWN и блокеры |
| [CHANGELOG](CHANGELOG.md) | Append-only изменения |
| [QUALITY](QUALITY.md) | Проверки и ограничения |

Каждое существенное описание факта ссылается на pinned code/report или Rxx карточку. Гипотезы и рекомендации явно помечены; owner-approved решения только в DECISIONS с evidence. GitHub API snapshots фиксируют факт публикации результата, не независимую правильность исходного расчёта.

**ChatGPT:** подключить GitHub с доступом к репозиторию, явно попросить прочитать эту папку в выбранном PR/ветке/SHA. До merge указать `docs/project-knowledge-system-v1`; после merge читать актуальный main. Если коннектор не видит ветку, дать pinned blob URLs из PR. Файлы не загружаются в память ChatGPT автоматически; в новом чате снова указать README, status, decisions, next steps. Не выдавать чтение docs за доступ к production.

**Codex:** открыть checkout нужной ветки, прочитать корневой AGENTS.md и три стартовых документа; сверить GitHub heads и data manifests, затем карточки. После задания обновить каталог, факты, статус, ограничения, вопросы и следующие шаги с PR/SHA. Обосновать повторное исследование.

**Восстановление:** Git history + pinned report URLs + sources/ snapshots + research.json. Записи/карточки исследований append-only; status.json обновляемый снимок. Старые report артефакты остаются в исходных ветках/коммитах: для полной автономной offline сохранности нужен отдельно согласованный архив репозитория; эта работа не копирует market raw данные. Проверять доступность pinned commits в CI.

Проверка: `python scripts/validate_project_knowledge.py`; live GitHub verification: `python scripts/validate_project_knowledge.py --online`; PR freshness/history: добавить `--base-ref <base SHA>`. Только stdlib и GitHub API, без платных сервисов, LLM calls или отправки raw данных сторонним сервисам.
