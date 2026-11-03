function buildOutputs(A,input,saved,sources,tests){
const r=A.run(input),m=A.market(input),o={},fmt=v=>v==null?"—":Number(v).toFixed(2);
const csv=rows=>{const ks=[...new Set(rows.flatMap(x=>Object.keys(x)))],esc=v=>{if(v==null)return "";const s=typeof v==="object"?JSON.stringify(v):String(v);return /[,"\n\r]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};return ks.join(",")+"\n"+rows.map(x=>ks.map(k=>esc(x[k])).join(",")).join("\n")+"\n";};
const table=(h,rows)=>"|"+h.join("|")+"|\n|"+h.map(()=>"---").join("|")+"|\n"+rows.map(x=>"|"+x.join("|")+"|").join("\n")+"\n";
const missing=["2026-10-23","2026-10-26","2026-10-27","2026-10-28","2026-10-29","2026-10-30","2026-11-02"];
const market=r.market.map(x=>({...x,data_status:"ARCHIVED_PUBLICATION_UNVERIFIED"})).concat(missing.map(date=>({date,data_status:"DATA_UNAVAILABLE_EXPECTED_WEEKDAY_NOT_VERIFIED_EXCHANGE_CALENDAR",confirmed_trade_signal:false})));
const stocks=r.stock.concat(missing.flatMap(date=>A.STOCKS.map(symbol=>({date,symbol,data_status:"DATA_UNAVAILABLE",actual_production_action:null,production_status:"UNKNOWN_NOT_ACCESSED"}))));
const falseWarnings=A.STOCKS.map(symbol=>{const ws=r.catalog.filter(x=>x.symbol===symbol&&x.flag==="sector_flag"),full=ws.filter(x=>x.complete),n=full.filter(x=>x.false_warning).length;return {symbol,matured:full.length,false_count:n,false_fraction:full.length?n/full.length:null,censored:ws.length-full.length,definition:"NO_LOW_DOWN5_FROM_SIGNAL_CLOSE_WITHIN10_SESSIONS",observations_dependent:true};});
const october=A.STOCKS.flatMap(s=>[0,.05,.1].map(f=>({...A.simulate(m.g[s].filter(x=>x.date>="2026-10-01"),m.all,input.actions.filter(x=>x.symbol===s),f,1).summary,view:"INDEPENDENT_OCTOBER_START_NOT_CONTINUOUS"})));
for(const s of A.STOCKS){const bh=october.find(x=>x.symbol===s&&x.fraction===0);for(const x of october.filter(x=>x.symbol===s))x.excess_vs_buyhold=x.final_equity-bh.final_equity;}
const octWarning=r.warnings.find(w=>w.flag==="sector_flag"&&w.date>="2026-10-01")?.date;
const perStock=A.STOCKS.map(symbol=>{
 const e=r.local.filter(e=>e.symbol===symbol).at(-1),p=r.events.filter(e=>e.symbol===symbol).at(-1),days=m.g[symbol].map(x=>x.date);
 const lead=n=>e?.["hit_"+n]?days.indexOf(e["hit_"+n])-days.indexOf(octWarning):null;
 return {symbol,october_reference_peak:e?.peak_date??null,october_depth_pct:e?.depth_pct??null,first_october_observed_hit5:e?.hit_5??null,first_october_observed_hit10:e?.hit_10??null,first_october_observed_hit15:e?.hit_15??null,september_reference_peak:p?.peak_date??null,september_reference_hit5:p?.hit_5??null,first_sector_warning:r.warnings.find(w=>w.flag==="sector_flag")?.date??null,first_october_sector_warning:octWarning,assumed_earliest_october_fill:octWarning?m.g[symbol].find(x=>x.date>octWarning)?.date:null,lead5_close_sessions:lead(5),lead10_close_sessions:lead(10),lead15_close_sessions:lead(15),left_censored:e?.left_censored??null,interpretation:!e?"NO5_PERCENT_CLOSE_EVENT_BY_CUTOFF":lead(5)>0?"BEFORE5_PERCENT_CLOSE_NOT_INTRADAY_GUARANTEE":lead(5)===0?"SAME5_PERCENT_CLOSE_TOO_LATE_FOR_SAME_DAY_FILL":"AFTER5_PERCENT_CLOSE",actual_production_warning:"UNKNOWN_NOT_ACCESSED",actual_positions_trades:"NOT_PROVIDED",data_end:input.data_end};
});
const hypotheses=["sector_flag","broad_flag","vix_change_flag"].map((flag,i)=>({hypothesis:["sector_Oct8","broad_Oct14","VIX_Oct16"][i],flag,first_window:r.warnings.find(w=>w.flag===flag)?.date??null,first_october:r.warnings.find(w=>w.flag===flag&&w.date>="2026-10-01")?.date??null,source_status:"ARCHIVED_RETROSPECTIVE_NOT_PROVIDER_VERIFIED",production_signal:false}));
const recovery=[];
for(const summary of r.summary.filter(x=>x.fraction>0)){
 const ts=r.trades.filter(x=>x.symbol===summary.symbol&&x.fraction===summary.fraction&&x.delay===summary.delay),lots=[];
 for(const t of ts){if(t.kind==="SELL")lots.push({symbol:t.symbol,fraction:t.fraction,delay:t.delay,sale_signal:t.signal_date,sale_date:t.fill_date,sale_price:t.price,sold:t.shares,remaining:t.shares,matched:0,matched_net_benefit:0,rebuy_dates:[],rebuy_prices:[]});
 if(t.kind==="BUY"){let q=t.shares;for(const l of lots){let n=Math.min(q,l.remaining);if(n>0){l.remaining-=n;l.matched+=n;l.matched_net_benefit+=n*(l.sale_price*.9995-t.price*1.0005);l.rebuy_dates.push(t.fill_date);l.rebuy_prices.push(t.price);q-=n;}}}}
 for(const l of lots)recovery.push({...l,valued_through:input.data_end,residual_marked_benefit:l.remaining*(l.sale_price*.9995-m.g[l.symbol].at(-1).close),status:l.remaining>1e-7?"INCOMPLETE_AT_ARCHIVE_CUTOFF":"RESTORED",not_Nov2_result:true});
}
const coverage=A.STOCKS.map(symbol=>({dataset:symbol,start:A.START,requested_end:A.END,actual_end:input.data_end,rows:r.stock.filter(x=>x.symbol===symbol).length,missing_expected_weekdays:missing.join(";"),publication_status:"UNVERIFIED_ORIGINAL_TIMESTAMPS"}));
coverage.push(...["QQQ_PROXY_NOT_NASDAQ_INDEX","SOX","VIX","DGS10"].map(dataset=>({dataset,actual_end:input.data_end,publication_status:dataset==="DGS10"?"ASSUMED_TWO_SESSION_LAG_NO_VINTAGES":"UNVERIFIED"})),...sources.missing.map(dataset=>({dataset,status:"UNAVAILABLE"})));
const catalogue=r.warnings.map(x=>({...x,symbol:"MARKET_FIXED_SAMPLE"})).concat(saved.map(x=>({...x,production:false,publication_verified:false,calculation_time_status:"RESEARCH_HISTORICAL_LABEL_NOT_ORIGINAL_TIMESTAMP",source_commit:input.source_commit})));
const datasets={"daily-market-chronology.csv":market,"daily-stock-chronology.csv":stocks,"drawdown-events.csv":r.events,"october-local-events.csv":r.local,"stock-audit.csv":perStock,"warning-catalog.csv":catalogue,"warning-outcomes.csv":r.catalog,"false-warnings.csv":falseWarnings,"strategy-comparison.csv":r.summary,"october-independent-comparison.csv":october,"trades.csv":r.trades,"daily-equity.csv":r.daily,"recovery-analysis.csv":recovery,"hypothesis-checks.csv":hypotheses,"data-coverage.csv":coverage};
for(const [name,rows]of Object.entries(datasets))o[name]=csv(rows);
o["test-results.json"]=JSON.stringify({runtime:"JavaScript V8 functions.exec pure functions; not Node CLI or pytest",passed:tests.filter(x=>x.passed).length,failed:tests.filter(x=>!x.passed).length,checks:tests},null,2)+"\n";
const summaryTable=xs=>table(["Акция","B&H, USD","5%, USD","10%, USD","Разница 10% с B&H"],A.STOCKS.map(s=>{const a=xs.filter(x=>x.symbol===s&&x.delay===1);return [s,...[0,.05,.1].map(f=>fmt(a.find(x=>x.fraction===f).final_equity)),fmt(a.find(x=>x.fraction===.1).excess_vs_buyhold)];}));
const thresholdTable=table(["Акция","Пик среза","−5% close","−10% close","−15% close","Опережение −5%, сессий"],perStock.map(x=>[x.symbol,x.october_reference_peak??"—",x.first_october_observed_hit5??"—",x.first_october_observed_hit10??"—",x.first_october_observed_hit15??"—",x.lead5_close_sessions??"—"]));
o["executive-summary-ru.md"]=`# October Risk Failure Audit v2 — предварительный итог

**Полный аудит до 2 ноября не завершён.** Повторены расчёты по сохранённым исследовательским данным до 22 октября. Данные 23 октября — 2 ноября, часть рынков, исходные времена публикации и production-пейлоады отсутствуют. Новый аудит не является восстановленным v1 или независимой проверкой поставщика.

1. Секторное условие впервые в октябре сработало ${octWarning}; в полном окне уже были срабатывания 1 и 14 сентября. Формулировка «первое предупреждение 8 октября» без уточнения периода неверна.
2. QQQ-прокси широкого рынка ухудшился 14 октября; дополнительный признак VIX появился 16 октября через пятисессионный рост, а не высокий уровень.
3. Для AMD/NVDA секторное предупреждение предшествовало закрытию ниже −5%; для MU/TSM совпало с ним, для LRCX/NBIS опоздало. Исполнение возможно лишь следующим open, не по цене сигнального close.
4. Причины фактического поведения Alpha OS не установлены: нет оригинальных решений, входов, настроек, позиций и сделок. Production-действия везде UNKNOWN. Сохранённые research HOLD не означают production HOLD.
5. AUTO-support в проверенной main не отфильтровывает текущую/будущую строку history. Возможность дефекта подтверждена статическим кодом и синтетической проверкой; реальные production-входы неизвестны.
6. Сентябрьская продажа с дорогим выкупом оставляет дефицит акций, который по заранее замороженному правилу блокирует следующую продажу. Отдельный старт 1 октября обходит этот путь и показывает другой результат; его нельзя подменять непрерывным тестом.

У AMD/NVDA/MU 2/3 секторных предупреждений не сопровождались падением low на 5% от signal-close в следующие 10 сессий. Это малая зависимая выборка, не общая оценка надёжности. Отдельные октябрьские сокращения ещё не прошли обратный выкуп к 22 октября.

Рекомендуется получить недостающие данные и read-only экспорт оригинальных решений/входов/версий/сделок, завершить этот аудит. Новую стратегию не выбирать, параметры не внедрять. Risk Engine v3 не разрабатывался.
`;
o["report.md"]=`# October Risk Failure Audit v2

## Статус и доказательства

Ветка непосредственно от main ${sources.base_main}; протокол опубликован до расчётов, Draft PR открыт заранее. Это новый расчёт, не восстановление утраченного v1. **Полный аудит до 2 ноября не завершён:** shell runtime FAILED и отсутствует конец истории.

Входы повторно прочитаны из ${input.source_commit}. sources.json содержит пути, Git blob SHA-1 и исходные манифесты Yahoo/CBOE/FRED. Это исследовательские архивы, а не новая независимая проверка поставщика. Имеются 407 stock-days/37 market-days до 22 октября; 7 последующих ожидаемых рабочих дат явно DATA_UNAVAILABLE. Эти даты не объявляются проверенным биржевым календарём.

Отсутствуют S&P500/Nasdaq/Russell2000, SOXX/SMH, Treasury2Y, DXY, IG/HY, настоящая ширина рынка. QQQ не переименовывается в Nasdaq, фиксированные 7 полупроводников не называются полной шириной сектора. DGS10 — архивная версия с предположением лага 2 сессии; исходные публикации/винтажи не проверены. Непроверенные данные не превращаются в подтверждённую рекомендацию: confirmed_trade_signal=false.

OHLC используют один ретроспективный масштаб, adjclose не смешивается. Дроблений внутри доступного окна нет. Дивиденды начислены ex-date как receivable по pre-open holdings; неизвестная дата выплаты не позволяет тратить receivable на выкуп. NBIS не склеивается с историей прежнего эмитента. 370 перекрывающихся closing values в двух архивных пакетах совпадают; это не два независимых поставщика.

## Проверка дат и формул

Предзаданные правила: R5=Ct/Ct-5−1. Sector: минимум 4/7 R5<0 и средний R5 ниже QQQ R5. Broad: QQQ<MA20 и R5<0. VIX: >=25 либо R5>=20%. Переходы вычислены из предшествующего состояния, без целевой даты в алгоритме.

8 октября: 5/7 падают, средний секторный R5 −1.41365%, QQQ +0.74795%.
14 октября: QQQ 728.9500 < MA20 742.5475, R5 −3.79818%.
16 октября: VIX 19.99, R5 +34.7035%; абсолютный уровень 25 не достигнут во всём доступном окне.

Даты подтверждаются при этих определениях в архиве; это не реальные сообщения Alpha OS и не доказательство прогностической силы. В сентябре были более ранние срабатывания. По price close предположена доступность следующей полуночью UTC: 8 октября → 9 октября 00UTC → самое раннее исполнение 9 октября open. Оригинальные timestamps не аттестованы. VIX, опубликованный после decision cutoff, отсекается. Макро допускается только после предположенного лага; строгая point-in-time достоверность всё равно не доказана.

## Просадки по 11 акциям

${thresholdTable}

Первичный каталог использует известный на дату максимум, seed prior60 на старте сентября и полное close-восстановление; вложенные снижения объединяются. Незавершённые события сохраняются. Октябрьский срез prior20 — вложенная диагностика, не независимые эпизоды. Его даты порогов — первое наблюдение внутри среза: у перенесённых META/AVGO пересечение могло быть до 1 октября; сверять primary drawdown-events.csv. Пики и минимумы — только ретроспективные labels, не торговые входы. Closing lead не означает intraday lead или доступную цену исполнения.

## Фактические и исследовательские сигналы

Оригинальных production-пейлоадов получено 0. Наличие investment_memory.py не доказывает наличия строк; запись request-driven и ошибки сохранения подавляются. Production endpoint/SQL не вызывались. Решения и реальные позиции не выдумывались.

Сохранены 111 research Overlay-строк из reports/risk-diagnostics/daily-signals.csv и 111 forecast-state/probability строк из reports/risk-forecast-v1/october-diagnostic.csv (target10%/10sessions). Это поздние артефакты PR-цепочки. Крупный Risk Signal v3 daily-signals.csv инвентаризирован по blob, не скопирован; Forecast содержит архивные состояния. 8 вновь рассчитанных диагностических transitions выделены отдельно RETROSPECTIVE. Отсутствие записи не HOLD. Original DecisionEngine целиком не replayed: фундаментальные snapshots/regime/manual levels/config отсутствуют. Research Overlay/v3/Forecast отсутствуют в текущем main; сам этот факт не устанавливает хронологию production deploy.

## Ложные предупреждения

False: отсутствие low-падения >=5% от signal-close хотя бы раз в следующие 10 сессий. Terminal return сохранён отдельно. Неполный горизонт не считается ложным. У AMD/NVDA/MU 2/3 false sector warnings; у AMZN 3/3. Даты общие, акции коррелированы, окна пересекаются: это зависимая малая выборка. Надёжные вероятности и независимая статистическая эффективность не заявляются. Поздние broad/VIX исходы censored.

## Модельные действия — непрерывный старт сентября

$100000 на каждую независимую акцию. Начальная покупка с 5bp fee +5bp adverse slip; последующие сделки с теми же расходами. Продажа 5%/10% ORIGINAL shares по новому sector transition, следующий open. Возврат: 3 clear-close подряд и close>MA20. Нет внешних денег, процентов, short или плеча. Новая продажа лишь после полного восстановления — заранее зафиксированный вариант. Delay2 — ещё одна сессия ожидания. NAV=stocks+cash+receivable. Реальных весов нет, строки не являются портфелем владельца.

${summaryTable(r.summary)}

Дорогой сентябрьский возврат оставляет cash-limited share deficit. Даже небольшой остаток блокирует октябрьскую продажу по текущему frozen rule. Это недостаток именно исследуемой политики исполнения, не установленный production-дефект. Правило после просмотра результатов не менялось. recovery-analysis.csv содержит FIFO matched net benefit, цены/количества возврата и marked остаток. Незакрытая часть не выдаётся за прибыль завершённого цикла.

## Независимый старт 1 октября

${summaryTable(october)}

Обе модели здесь заново начинают с полной позицией и одинаковым капиталом 1 октября. Сентябрьский дефицит отсутствует. Для AMD/NVDA/MU продажа 9 октября даёт положительную разницу mark-to-22October, но обратного выкупа нет. Это незавершённый цикл, не результат 2 ноября и не замена непрерывному тесту. Выбор выгодного старта не подтверждает эффективность.

## Причинная атрибуция и остановка

AUTO-support разобран отдельно. Технические/fundamental gates могут запаздывать, но без оригинальных входов это гипотеза причин поведения. Нельзя утверждать, что система действительно выдала HOLD, проигнорировала 8 октября или могла предотвратить конкретный реальный убыток. Новая стратегия не ранжировалась.

Нужны данные 23 октября–2 ноября, отсутствующие рынки, original release/vintage timestamps и read-only экспорт decision/config/deployed versions/positions/trades. После получения можно завершить этот аудит и прогнать Node/Python. К Risk Engine v3 и этапам 2–5 не переходить.
`;
o["auto-support.md"]=`# AUTO-support — условный дефект main

Источник: aae/engines/decision_engine.py @${sources.base_main}, Git blob ${sources.main_code_blob}.

Строки 177–238: usable_history сохраняет dict с close!=None; history_date только сортирует; recent_history=usable_history[-120:]; auto_support=min(lows), иначе price. Строки 391–393: support_broken=price<support. Ограничения по дате решения/исключения текущей свечи в этом фрагменте нет. manual_support имеет приоритет.

При согласованном OHLC low_current<=close_price. Если текущая свеча включена, min(lows)<=low_current<=close_price, и close_price<support невозможно. Fixture: prior low99, current low89/close90: prior-only support99 → breach=true, include-current support89 → breach=false. Будущая строка локально также не отсекается.

Это статический вывод и исполняемый синтетический algebra-check в test.cjs, не запуск полного Python DecisionEngine. Доказана возможность дефекта при таком history; неизвестны реальные production-входы, manual levels и версии по дням. Для prior-only history вывод о невозможности breach неверен. Действующая main не изменялась.
`;
o["validation.md"]=`# Validation and reproducibility

**29/29 pure-JavaScript проверок исполнены в V8 functions.exec, 0 failures.** test.cjs содержит тот же проверенный текст. Проверены costs, next-open, delay, gap, no-repeat, restoration, no borrowing, NAV, ex-date entitlement, prefix invariance, prior support, conditional self-inclusion, nested/censored events, missing outcomes, duplicate dates, VIX availability, unknown production statuses. Имена и результат — test-results.json.

**НЕ выполнены:** Node CLI/fs integration и существующий Python suite (shell environment FAILED); независимый provider refresh; полный период до 2 ноября; исходные публикации/макровинтажи; original production replay/реальные позиции/сделки. Старые 203 tests/20 subtests не повторялись и не входят в 29. Неаттестованная PIT-доступность не считается пройденной исторической проверкой.

Данные: 2639 warmup+audit price rows /13series; 407 stock-days,37 market-days до22 октября;7 weekday-placeholder без цен. 222 saved research rows,8 новых transitions. 370 перекрывающихся stock closes совпадают в двух архивах (не независимые поставщики). Empty/null означает unknown/censored, не ноль.

Воспроизведение после восстановления shell (Node18+, без зависимостей/сети/credentials):

~~~bash
node research/october-risk-failure-audit-v2/test.cjs
node research/october-risk-failure-audit-v2/run.cjs
~~~

run.cjs читает только опубликованные inputs/sources/saved-research-signals и пишет только каталог аудита. Pure code не импортирует приложение, не обращается к production. Общий split engine не заявляется: проверено отсутствие splits в доступном окне. Dividend pay dates неизвестны, receivable не расходуется. Для полной проверки требуются поставщик и дополнительная история.

Гипотезы известны по прежним исследованиям: даже новый протокол не превращает эту выборку в untouched holdout. Воспроизводимость архивной ассоциации не равна инвестиционной эффективности. Полный аудит не завершён; этапы2–5 не выполнялись. No merge/deploy/SQL/live orders.
`;
o["run-metadata.json"]=JSON.stringify({version:"October-Audit-v2",scope:"STAGE1_PARTIAL_ARCHIVED_DATA_ONLY",base_main:sources.base_main,source_commit:input.source_commit,requested_start:A.START,requested_end:A.END,actual_end:input.data_end,counts:Object.fromEntries(Object.entries(datasets).map(([k,v])=>[k,v.length])),pure_v8_tests_passed:tests.filter(x=>x.passed).length,production_payloads_obtained:0,confirmed_trade_signals:0,new_models_fitted:false,parameter_search:false,node_cli_executed:false,python_suite_executed:false,complete_audit:false},null,2)+"\n";
return o;
}
if(typeof module!=="undefined")module.exports=buildOutputs;
