# AUTO-support — условный дефект main

Источник: aae/engines/decision_engine.py @a14ebf9c268bea5cb01de962edfb98b8df94652a, Git blob 26721ae07a6ae2d60d1c771754981e714b479624.

Строки 177–238: usable_history сохраняет dict с close!=None; history_date только сортирует; recent_history=usable_history[-120:]; auto_support=min(lows), иначе price. Строки 391–393: support_broken=price<support. Ограничения по дате решения/исключения текущей свечи в этом фрагменте нет. manual_support имеет приоритет.

При согласованном OHLC low_current<=close_price. Если текущая свеча включена, min(lows)<=low_current<=close_price, и close_price<support невозможно. Fixture: prior low99, current low89/close90: prior-only support99 → breach=true, include-current support89 → breach=false. Будущая строка локально также не отсекается.

Это статический вывод и исполняемый синтетический algebra-check в test.cjs, не запуск полного Python DecisionEngine. Доказана возможность дефекта при таком history; неизвестны реальные production-входы, manual levels и версии по дням. Для prior-only history вывод о невозможности breach неверен. Действующая main не изменялась.
