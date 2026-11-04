# Модели риска

Подтверждено в main: [RiskEngine](https://github.com/volk468-max/Analytical-Engine/blob/a14ebf9c268bea5cb01de962edfb98b8df94652a/aae/engines/risk.py) объединяет VIX 40%, breadth proxy 25%, inverse market score 20%, event risk 15%; уровни LOW/MODERATE/HIGH/EXTREME. Это описание исходного кода, не калиброванная вероятность. [DecisionEngine](https://github.com/volk468-max/Analytical-Engine/blob/a14ebf9c268bea5cb01de962edfb98b8df94652a/aae/engines/decision_engine.py) и [StrategyEngine](https://github.com/volk468-max/Analytical-Engine/blob/a14ebf9c268bea5cb01de962edfb98b8df94652a/aae/engines/strategy_engine.py) — отдельные company paths. Production SHA не восстановлен.

| Предложение | Статус внедрения | Исследовательский вывод |
|---|---|---|
| Tactical Risk Overlay v2, R01–R03 | Unmerged | Независимые HOLD/REVIEW/TRIM; recent drawdown сам по себе не TRIM |
| Signal v3 A/B/C, R05–R06 | Unmerged | C раньше обнаруживает часть declines; economic benefit не показан |
| Forecast v1, R07 | Unmerged | 0/18 incremental primary tasks |
| Sector flag, R09–R12 | Draft, unmerged | Экономическая политика и predictive audit — отдельные вопросы; преимущество не подтверждено |
| Breadth prototype, R13 | Draft, unmerged | Descriptive proxies, no qualified historical backtest |

Источники: [карточки R01–R13](RESEARCH_INDEX.md). Гипотезы о пользе сигналов не превращать в утверждённые торговые правила. Рекомендация: новый сигнал требует independent prospective validation и явного human approval до интеграции.
