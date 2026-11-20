# Следующие шаги

Это рекомендации Codex, не утверждённые решения владельца.

1. Human review knowledge v1 и CI; не выполнять автоматический merge.
2. Перед любой новой работой проверить main/PR head и data manifest, прочитать status/decisions/next steps и карточки. Если источник изменился — новая версия карточки, старую сохранить.
3. При отдельной авторизации получить original production evidence через безопасный read-only экспорт (R09/R13); не вызывать endpoint только по имени GET без проверки side effects.
4. Согласовать источник, бюджет и licensing breadth; затем отдельный Breadth PIT Data Qualification (предложение R13). Ничего не покупать автоматически.
5. Только после квалификации данных — замороженный протокол нового independent/prospective теста; не повторять R02–R12 без нового вопроса или исправления с обоснованием.

Текущая работа завершается после Draft PR. Автоматизация только проверяет и сообщает об ошибках, не пишет документацию, production или решения.

## Актуализация 2026-11-05

Предшествующий план выше сохранён как checkpoint. Q001 технический проект теперь подготовлен, но реальная data qualification не выполнена. Следующее предложенное действие: human review схемы/прав/изоляции, затем отдельно разрешённый owner trial на Windows (3недели/2года), independent event evidence и deletion plan. Полный2010–2026 gate остаётся закрытым. Не покупать и не интегрировать автоматически. См. [trial-plan](../../reports/breadth-pit-data-qualification-v1/trial-plan.md).

## После Q002

Не заявлять live forecast advantage текущего estimator:0/27newcriteria. Для дальнейшего predictive research — independent prospective log, actual original availability evidence, заранее определённая минимальная полезная loss improvement и power budget. Untouched period отсутствует; не делать feature search на том же2021–2026. Ничего не покупать/не интегрировать автоматически. [Q002](research/Q002-v1.md).

## После Q003

Не выбирать лучший ансамбль на старой истории. Рекомендация: prospective timestamped
logging после публикации, минимум2года и30 de-overlapped market episodes плюс blinded
power check для1%Brier gain; прежняя Holm family, PIT и отдельный economic gate.
Independent event count сейчас UNKNOWN. Ничего не внедрять/покупать автоматически.

## После Q004 / Issue19

Не заявлять validated core:0/33primary. NVDA secondary vsmarket-only не превосходит
простую regime baseline. Следующий допустимый research gate: original PIT evidence,
заранее замороженный будущий shadow log и blinded power check, без peeking/tuning.
Спецификация не запускает live infrastructure. Norgate/Windows acquisition отложен
до возвращения владельца и его явного разрешения. Economic utility — отдельный gate.

## После Q005

Сначала actual portfolio contract и total-return/PIT qualification. Не выпускать
персональные51% и не выбирать news premiums/thresholds из synthetic examples.
Blinded power feasibility вместо30rare clusters/2years;90days не гарантия.
Не запускать live log, Norgate, покупки или protective trades автоматически.

## Q006

Independent action/PIT validation, prospective EOD calibration. Separate reviewed ladder repair; no trading.

## Q007

Resolve MUdated record andQQQ dividend precision, independentlyreconcile continuity; review gates before empirical cal/ledger. No trims or ladder use.

## Q007-v2

Review preliminary v2 results and independent action/price/settlement gaps. Do not
promote lower marginal bias to predictive advantage. Frozen prospective design and
blinded power/precision review needed; no new calibrator/threshold search on test
history. No production/launch/trades authorized. PR28 dependency synchronization
is separate future work, not performed here.

## Q008

Review isolated DB/provider/model/permissions/cost/cron/notifications/retention/backfill/go-live checklist. Obtain separate explicit approval before provisioning, migration, live run or schedule. False Signal Anatomy follow-up preregistration.

## Q008-v2

Resolve verified live data/retention/publication/actions contract and training source
qualification; separate owner approval for exact isolated DB/roles/budget/backup/
notifications/go-live, then supervised actual-record inspection before any live claim.
No provision/deploy/cron/trades are authorized by this preparation milestone.

## Q008-v3

Obtain applicable dated EODHD retention/cloud/backup clarification; personal-only
classification is confirmed, written permissions absent. Verify total invoice<=50,
authorized6symbol/actions/recent2026API and finalization timing. Tiingo retention
exception outside Power/50cap is unresolved. Separate purchase/isolated migration/
first actual one-shot approvals and human evidence review precede any real launch;
no scheduler/production/trading authorized. Full checklist in v3 report.

## Q008-v4

Follow exact v4 Railway handover after deployment approval is actually granted.
Create isolated DB/service instance, configure dedicated worker paths and pinned
CI-passing SHA, never start root production app. Verify EODHD actual API, migrations,
real models and same-session readiness, then actual SQL count/first issue and active
cron. Currently all operational acceptance items remain unfulfilled. No backdate.
Address credential separation/key rotation/native backup/notification/revision review
limitations; private historical comparison only, no public licensed series.

## Q008-v5

Review dependent fix PR and additive005. Request explicit approval before pinning
fix SHA only in research worker. Preserve cron; verify new run UUID/completion/HTTP
status and independent read-only persistence audit. Historical432/first timestamp
are app-log observations, not fresh SQL. Sunday skip is not forecast-generation
acceptance; do not backdate the failed historical session. No merge/production.


## Q009
Publish/review feature/vol-daily-ten-stocks on pinned PR29 base, verify CI and
source/schema/asof/support. Enable only authorised isolated worker. Capture real
10-stock preflight then actual future valid-window issue+read-only SQL; no backdate.
Save actual status in Notion, distinguish deployed/scheduled from first issuance.


### Q009 final code checkpoint
Published Draft PR34; fixed knowledge test-fixture scope and isolated legacy
issuance errors from VOL. One extra runtime regression passes:211distinct pipeline
tests across local runs, plus9knowledge tests; four-schema backup/restore passes.
No VOL live issuance asserted. Deployment/source preflight remain next gate.


## 2026-11-17 — Q009-v2 / code verified, platform deployment rejected

[PR34](https://github.com/volk468-max/Analytical-Engine/pull/34) calculation SHA
`84fcc8dff22d08ce186eaf0d8753a9700b428e15`: final GitHub
[daily pipeline](https://github.com/volk468-max/Analytical-Engine/actions/runs/44060183233)
and [online knowledge](https://github.com/volk468-max/Analytical-Engine/actions/runs/44060183208)
completed SUCCESS, including PostgreSQL16/18, full parent regression/replay and restore.
Local211distinct pipeline tests+9knowledge, four-schema synthetic restore pass.

Owner repeated connection request after platform rejection. Both accept-deploy
attempts returned: Cancelled — the user did not approve this action. No changes
were made. This is a platform result, not an assertion owner intentionally refused.
No bypass attempted. Patch0bc08fd0-33af-4f97-b3ee-03ca1c0a73ea remains STAGED,
worker-only. Current live source stays fe834c77cbadf4baa3eab68135cbdee1ecdad1f0.
VOL not enabled; migration006/live10-symbol preflight/realVOL issuance NOT RUN.
Notion Alpha OS received decisions, exact universe, implementation and this
blocked operational checkpoint. No production/trading/merge/purchases.

Next: approve/apply existing research patch, observe terminal deploy SUCCESS,
bootstrap/migration006 and actual10-symbol preflight, direct read-only SQL, cron.
Do not call code/CI/staging a completed connection; no historical backfill.


## 2026-11-17 — Q009-v3 / deployment and actual preflight

Owner applied the research patch manually. Source84fcc8dff22d08ce186eaf0d8753a9700b428e15
deployment8b87b0b1-8d8a-484e-97f3-b96963756390 reached SUCCESS. Bootstrap READY/exit0
run d4a3036b-175b-49b6-9974-bc3c80846e4a confirms migration/setup completed; no
independent migration-catalog SQL yet. Existing cron unchanged, no staged changes.

An authorised worker-only restart ran real preflight89344101-1cdd-4ce5-b7f7-e3676fcdd0c8:
63HTTP200/0failures,10stock checks completed108ready/12blocked. All12NBIS targets
blocked INSUFFICIENT_MATURE_TRAINING_SUPPORT; other9names12/12ready each. No
actual VOL forecast published: daytime gate BEFORE_OFFICIAL_CLOSE. This is not
prospective forecast acceptance/model validation. Old forecast total648 is old
HIST/REGIME application SQL-log evidence, not VOL.

Run ended PARTIAL_FAILURE/exit2 because inspect_vol selected repeatable-read after
Store.connect had already queried database identity in the same transaction. New
three-line fix commits the setup transaction before the read-only snapshot,
retaining the restricted session role. Real disposable PostgreSQL17 regression
plus6runtime tests PASS7/7. No estimator/targets/threshold/model changes.

[PR34](https://github.com/volk468-max/Analytical-Engine/pull/34) continues; isolated
research fix deployment and repeat audit/preflight are next, already within owner
authorisation. No production/trading/merge/purchases. Project list-services read
confirms only one environment, research; no other environment could receive a
service source update. After acceptance verify first real next valid cron issue.


## 2026-11-17 — Q009-v4 / operational preflight accepted, first issue pending

Actual deployed/pinned source `a2855b5107eb02946cb6e7e1dc41ab69db61ecfb`,
deploymentd20392cf-7044-4ac5-8264-d050168bbefd SUCCESS. No pending patch.
After minimal audit-transaction fix, actual run8688b6b2-7b50-465b-93d6-b04f67ff93a7
ended SUCCESS/exit0 at2026-11-17T10:19:12UTC:108/120targets ready,12NBIS blocked
INSUFFICIENT_MATURE_TRAINING_SUPPORT; other9stocks12/12ready.63HTTP200/0failures.
Read-only SQL audit inside worker reports0VOLrecords/0numeric/NULLfirst/lastissue,
DUPLICATES=0. These are SQL results read from application logs, not an independent
SQL session. BEFORE_OFFICIAL_CLOSE prevented a daytime/backdated forecast.
[Sanitised evidence](../../reports/vol-daily-v1/operational-acceptance.json).

Cron0 2 * * 2-6 remains05:00Moscow Tue–Sat. First real VOL issue expected2026-11-18
05:00Moscow (USsession2026-11-17); pending, not claimed as issued. One-time
automation for05:30Moscow will audit actual manifest/timestamps/duplicates/blocks
and save in Notion; IDAutomation_a3be3fb079a881918909c1cd592c1d7c.
Notion Alpha OS history saved including old failures and successful resolution.
Next: first prospective issuance acceptance, then mature10/30session scoring;
NBIS…50487 tokens truncated….25 else (-1 if v<-.25 else 0)
            m.update(mae_percentage_points=sum(abs(v) for v in error)/len(error),
                rmse_percentage_points=(sum(v*v for v in error)/len(error))**.5,
                directional_accuracy=sum(direction(a)==direction(b) for a,b in zip(expected,actual))/len(error),
                strict_sign_accuracy=sum(((a>0)-(a<0))==((b>0)-(b<0)) for a,b in zip(expected,actual))/len(error),
                empirical_band_coverage=sum(r['band_low_pct']<=y<=r['band_high_pct'] for r,y,t in mature)/len(mature),
                matched_technical_mae_pp=sum(abs(100*r['technical_return']-y) for r,y,t in mature)/len(mature),
                matched_zero_return_mae_pp=sum(abs(y) for r,y,t in mature)/len(mature),
                matured_last7days=sum((utc(issued)-t).total_seconds()<=7*86400 for r,y,t in mature))
        result[str(h)]=m
    cases.sort(key=lambda r:abs(r['error_percentage_points']),reverse=True)
    return dict(cutoff_utc=issued,by_horizon=result,accuracy_status='EXPERIMENTAL_NOT_VALIDATED',
                direction_deadband_pct=.25,recent_error_cases=cases[:20],recent_error_case_count=len(cases),
                error_case_selection='LARGEST_20_ABSOLUTE_ERRORS_MATURED_LAST7D_NOT_CAUSAL_ATTRIBUTION')


def export_body(audit,rid,body,*,already=False):
    raw=canonical(body).encode();checksum=hashlib.sha256(raw).hexdigest()
    encoded=base64.b64encode(gzip.compress(raw,mtime=0)).decode();chunks=[encoded[i:i+2000] for i in range(0,len(encoded),2000)]
    for i,chunk in enumerate(chunks):audit.emit(persist=False,phase='ALPHA_FULL_PRICE_EXPORT',status='CHUNK',session=body['session'],full_run_id=str(rid),json_sha256=checksum,chunk_index=i,chunk_count=len(chunks),payload_b64=chunk,encoding='gzip+base64')
    audit.emit(persist=False,phase='ALPHA_FULL_PRICE_EXPORT',status='READY',session=body['session'],full_run_id=str(rid),json_sha256=checksum,chunk_count=len(chunks),row_count=118,numeric=sum(r['expected_return_pct'] is not None for r in body['rows']),already_recorded=already,encoding='gzip+base64')


def run_price(store,audit,permit,session,*,now=None,collector=None):
    if os.environ.get('ALPHA_FULL_PRICE_ENABLED')!='true':return
    stamp=(now or datetime.now(timezone.utc)).isoformat()
    reason=issuance_gate(session,stamp,replace(permit,finalization_verified=True))
    if reason:
        audit.emit(persist=False,phase='ALPHA_FULL_PRICE',status='SKIPPED',session=session,reason=reason);return
    with store.connect() as c:old=c.execute('SELECT id,body FROM alpha_full_price_v1.runs WHERE session_date=%s AND model_version=%s',(session,model.VERSION)).fetchone()
    if old:export_body(audit,old[0],old[1],already=True);return
    try:bundle=load_bundle()
    except Exception:bundle=None
    frames,failures,snapshots=collect_frames(permit,session,collector=collector,identities=(bundle or {}).get('instrument_identity'))
    # Raw histories remain in the existing encrypted/expiring payload plane only.
    from .bootstrap import CONTRACT
    refs={}
    for s,snapshot in snapshots.items():
        try:refs[s]=str(store.payload(CONTRACT,snapshot,permit.raw_until))
        except Exception:
            frames.pop(s,None);failures[s]='SOURCE_ARCHIVE_UNAVAILABLE'
    cutoff=datetime.now(timezone.utc).isoformat()
    if issuance_gate(session,cutoff,replace(permit,finalization_verified=True)):
        audit.emit(persist=False,phase='ALPHA_FULL_PRICE',status='SKIPPED',session=session,reason='SOURCE_COLLECTION_OUTSIDE_ISSUE_WINDOW');return
    matured=resolve_mature(store,frames,cutoff)
    cutoff=datetime.now(timezone.utc).isoformat()
    body=model.forecast(frames,failures,session,cutoff,bundle=bundle,records=training_records(store,cutoff))
    completed=datetime.now(timezone.utc).isoformat()
    for group in ('technical_heads','context_heads'):
        for head in body[group].values():
            if head is not None:
                head['data_cutoff_utc']=head['trained_at'];head['trained_at']=completed
    # Publication timestamps are genuine post-calculation UTC, never scheduled/backdated times.
    with store.connect() as c:issued=c.execute('SELECT clock_timestamp()').fetchone()[0].isoformat()
    if utc(issued)<utc(completed):raise ValueError('PRICE_CLOCK_SKEW_DATABASE_BEHIND_CALCULATION')
    body['calculation_cutoff_utc']=cutoff;body['issued_at']=issued
    for r in body['rows']+body['market_rows']:
        r['issued_at']=issued
        if r['technical_return'] is not None:
            r['technical_weights_sha256']=model.digest(body['technical_heads'][r['horizon']])
            head=body['context_heads'][r['horizon']]
            if head is not None:r['context_weights_sha256']=model.digest(head)
    if issuance_gate(session,issued,replace(permit,finalization_verified=True)):
        audit.emit(persist=False,phase='ALPHA_FULL_PRICE',status='SKIPPED',session=session,reason='CALCULATION_OUTSIDE_ISSUE_WINDOW');return
    for r in body['rows']+body['market_rows']:
        end=calendar().session_close(pd.Timestamp(r['target_session'])).to_pydatetime()+timedelta(days=1)
        why=permit.reason(issued,fixture=False,horizon_end=end.isoformat())
        if why:
            r['license_reason']=why
            if r['status']=='EXPERIMENTAL_PRICE_FORECAST':r.update(status='STATUS_BLOCKED',reason=why,expected_return_pct=None,band_low_pct=None,band_high_pct=None,direction=None)
    body['resolved_at_this_run']=matured
    body['source_revision_sha256']={s:snapshots[s].revision for s in frames}
    body['source_payload_refs']={s:refs[s] for s in frames}
    body['source_retrieved_at_utc']={s:snapshots[s].retrieved_at for s in frames}
    body['source_quality']='SINGLE_RESEARCH_SNAPSHOT_NOT_INDEPENDENTLY_FINALIZED'
    with store.connect() as c:
        rid=c.execute('SELECT alpha_full_price_v1.record(%s,%s)',(uuid.uuid4(),canonical(body))).fetchone()[0]
        saved=c.execute('SELECT body FROM alpha_full_price_v1.runs WHERE id=%s',(rid,)).fetchone()[0]
    export_body(audit,rid,saved)
    audit.emit(persist=False,phase='ALPHA_FULL_PRICE_EVALUATION',status='READY',session=session,statistics=evaluation(store,issued))
