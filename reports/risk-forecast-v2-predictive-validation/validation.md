# Проверки и воспроизводимость

До новых вычислений протокол опубликован commit b1d43275bb10bc69516e868b625377ceea4119b6; protocol-registration.json содержит hash. Исходный v1 source366f8cd00e8c228d4796d0abbe9997f717a3b6ad воспроизведён в отдельном клоне:13CSV byte-identical, plots/report также прежние, отличается run.json из-за путей среды. Никакая исходная research ветка не редактировалась/не пушилась. Числа0/18 original подтверждены, не заменены newbenchmark0/27.

Оригинальные27forecast tests пройдены без изменения тестового кода. Первоначально один test падал из-за абсолютного пути /workspace/Analytical-Engine/aae/research/risk_v3_study.py в старом source manifest. После независимой проверки всех исходных hashes добавлен только environment symlink к byte-identical frozen source, затем27tests passed. Это явно environment portability accommodation, не исправление модели и не скрытый пропуск теста.

Новые tests покрывают full maturity, embargo/cutoff, terminal/touch различие, known-only QQQregime, missing warmup, proper scoring, confusion denominators, synchronous panel resampling, cash-limited share/cash identity и actual fit/output boundaries. Synthetic fixtures проверяют код, не predictive power. Real calculations используют frozen provider observations/reconstructed features, не synthetic prices.

Повторные numerical outputs сравниваются побайтно; итог verification.json указывает точный count/status. В первоначальной новой реализации исправлена синтаксическая ошибка dict construction до успешного расчёта, без изменения frozen protocol/модельных параметров. Missing pytest установлен только в изолированный research test dependency directory; production requirements не менялись.

Reproduction: research/risk_forecast_validation/README.md. Input manifests/code SHA pinning; no production imports вне отдельного frozen source checkout. Native v1 loads research-only aae/backtest modules, а не production endpoints. Нет новых provider calls, broker, платных данных, signal changes, merge/deploy. CI success будущего PR не заявляется.
