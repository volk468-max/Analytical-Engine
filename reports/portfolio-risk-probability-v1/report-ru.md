# Portfolio Risk Probability Engine v1 — подробный отчёт

[Краткий итог и DONE/BLOCKED/NOT DONE](executive-summary-ru.md).

## Метод и результат

Данные пользователя отсутствуют. Не вычислялись пользовательские позиции, валюта,
NAV, HWM, drawdown, вероятность, CI или predictive performance. Протокол и контракт
опубликованы перед программированием. Предыдущие результаты не пересчитывались
для поиска удачного ансамбля; новая работа — контракт и gated architecture.

Синтетические fixtures проверяют total-return accounting frozen book, cash,
FX синхронность, splits и dividend receivable/pay, полную зрелость60sessions.
Портфельные позиции копируются, будущие rebalanced weights/flows не принимаются.
Exact ANY-point requires complete synchronous intraday coverage. Daily no-hit
остаётся primaryNA, positive daily hit подтверждает наличие касания, но label
всё равно ждёт полного окна. Source completeness — отдельный внешний gate,
код не способен доказать истинность flag actions_complete от поставщика.

15%от HWM считается отдельно. HWM должен быть unitised/flow-adjusted и известен
на дату решения; helper получает его явно, не восстанавливает из отсутствующей
истории. При NAV90/HWM100 потрачено10, осталось5; ещё10%отNAV —9, то есть может
превысить оставшийся бюджет. Порог вероятности сам по себе не ограничивает DD.

Baseline fixture считает частоту по joint NAV paths; cash/FX/correlation должны
входить в исходное совместное распределение. Mean(asset probabilities) запрещён.
ES5%определён по terminal losses с дробным весом на границе tail, отдельно от
path minimum/TOUCH. Нет реальной training/calibration выборки: baseline calibration,
VOL/regime fitting и12ablation comparisons BLOCKED; все реальные метрики NA.

Факторный реестр содержит механизм и направление как гипотезы, exact timestamps,
credibility/revision/coverage/missingness/correlation/license fields. Неполный
архив не заменяется нулевым фактором. News events deduplicate bycanonical id и
verified near-duplicate fingerprint; семантическое выделение этих ids потребует
источника/разметки, автоматический NLP classifier здесь не реализован. Официальный
FOMC release и related narrative относятся к одному rates group; нужна market-
implied surprise, не произвольная надбавка за ставку. Реальная attribution NA;
synthetic logit contributions не являются уникальными причинными эффектами.

## Защита и границы реализации

[Архитектура](architecture.md) описывает prototype state machine и блокировки.
35%WATCH без продаж;51/60экспериментальные candidate levels. Размеры, confirmation,
cooldown и reentry задаются явно, real calls alwaysblocked. Учёт cumulative targets
не разрешает каждый день повторно продавать одинаковую долю. Pending intent требует
следующегоsession и явного settle. Но это НЕ полноценный cash/tax/fill ledger:
реальные reentry affordability, concentration, exposure/risk-budget coupling и
сравнения экономической эффективности BLOCKED, не объявлены реализованными.

Original Ladder отделена: fixture фиксированного anchor,5%original units/2%move,
50%floor. Это mechanism target, не доказательство точного исторического original
production replay. Сравнения B&H/risk-matched overlay/Ladder/new policy, CAGR/DD/ES,
turnover/missed upside/recovery не проводились без данных. Комбинации NOT DONE.

## Shadow log и следующий gate

Офлайн mock демонстрирует append-only hash chain, separate label, nullable P/CI и
source versions. Code SHA null в synthetic mock честно отражает отсутствие
зафиксированного model deployment; source content SHA256 присутствует. Настоящие
forecast records требуют frozen commit/model/protocolSHA, snapshot id/hash,
actual release/ingest/decision timestamps и maturity, immutable input vintages.
Corrections append with reference to superseded record, no overwriting. Hashchain
сам по себе не даёт защищённого immutable storage. Никакой инфраструктуры/cron/live
record collection не запускалось. Нельзя backfill и назвать это prospective log.

Реалистичная мощность: first data-quality pilot, затем blinded block-variance и
arrival-rate estimates, Monte Carlo alternatives1%Brier/Holm12/80%power; заранее
зафиксировать необходимую длину и правила monitoring. Нет обещаний90days significance
или30rare independent episodes за2years. Untouched holdout на2021–2026 отсутствует.

Открыто: source coverage/licensing, actual account/flows/actions/FX, полная
синхронная intraday history, original expectation/news/revisions. Norgate/Windows
и платные источники не приобретались. GO только review и software fixtures;
NO-GO calibrated forecast, protection deployment и economic advantage claims.
