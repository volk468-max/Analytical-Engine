-- DESIGN/LOCAL TEST ONLY. Never auto-run against a Railway database.
BEGIN;
DO $$ BEGIN
 IF current_database() <> 'alpha_shadow_research' THEN
 RAISE EXCEPTION 'Isolated alpha_shadow_research database required'; END IF;
END $$;
CREATE SCHEMA alpha_shadow_v1;
REVOKE ALL ON SCHEMA alpha_shadow_v1 FROM PUBLIC;
CREATE ROLE alpha_shadow_writer NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE alpha_shadow_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE TABLE alpha_shadow_v1.audit_events(
 id uuid PRIMARY KEY, seq bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
 kind text NOT NULL CHECK(kind IN ('run','vintage','forecast','outcome','correction','model','health')),
 event_key text NOT NULL, body_text text NOT NULL, body jsonb NOT NULL,
 previous_hash text, record_hash text NOT NULL UNIQUE,
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(kind,event_key), CHECK(body=body_text::jsonb)
);
CREATE TABLE alpha_shadow_v1.forecast_runs(id uuid PRIMARY KEY REFERENCES alpha_shadow_v1.audit_events, session_date date NOT NULL, mode text NOT NULL CHECK(mode IN('SYNTHETIC','PROSPECTIVE','BACKFILL')));
CREATE TABLE alpha_shadow_v1.source_vintages(id uuid PRIMARY KEY REFERENCES alpha_shadow_v1.audit_events, source_hash text NOT NULL, qualification text NOT NULL, publication_at timestamptz, ingestion_at timestamptz CHECK(qualification<>'QUALIFIED_PIT' OR ingestion_at>=publication_at), CHECK(qualification<>'QUALIFIED_PIT' OR (publication_at IS NOT NULL AND ingestion_at IS NOT NULL)));
CREATE TABLE alpha_shadow_v1.model_registry(id uuid PRIMARY KEY REFERENCES alpha_shadow_v1.audit_events, model_name text NOT NULL, version text NOT NULL, UNIQUE(model_name,version));
CREATE TABLE alpha_shadow_v1.forecast_records(
 id uuid PRIMARY KEY REFERENCES alpha_shadow_v1.audit_events,
 run_id uuid NOT NULL REFERENCES alpha_shadow_v1.forecast_runs,
 vintage_id uuid NOT NULL REFERENCES alpha_shadow_v1.source_vintages,
 model_id uuid NOT NULL REFERENCES alpha_shadow_v1.model_registry,
 session_date date NOT NULL, symbol text NOT NULL,
 label_type text NOT NULL CHECK(label_type IN('LOW_INTRADAY','EOD_CLOSE','PORTFOLIO_EOD_CLOSE')),
 threshold_pct integer NOT NULL CHECK(threshold_pct IN(5,10,15)), horizon integer NOT NULL CHECK(horizon IN(10,20,60)),
 issued_at timestamptz NOT NULL, decision_at timestamptz NOT NULL,
 status text NOT NULL CHECK(status IN('FORECAST','STATUS_BLOCKED','NO_FORECAST')),
 probability_raw double precision CHECK(probability_raw BETWEEN 0 AND 1),
 probability_calibrated double precision CHECK(probability_calibrated BETWEEN 0 AND 1),
 UNIQUE(session_date,symbol,label_type,threshold_pct,horizon,model_id),
 CHECK(status='FORECAST' OR (probability_raw IS NULL AND probability_calibrated IS NULL)),
 CHECK(status<>'FORECAST' OR probability_raw IS NOT NULL),
 CHECK(symbol NOT IN ('A','B','C') OR (label_type='PORTFOLIO_EOD_CLOSE' AND threshold_pct=10 AND horizon=60))
);
CREATE TABLE alpha_shadow_v1.outcome_records(id uuid PRIMARY KEY REFERENCES alpha_shadow_v1.audit_events,forecast_id uuid NOT NULL REFERENCES alpha_shadow_v1.forecast_records,status text NOT NULL CHECK(status IN('IMMATURE','MATURED','UNRESOLVED')), outcome boolean, source_vintage_id uuid REFERENCES alpha_shadow_v1.source_vintages, CHECK(status<> 'MATURED' OR source_vintage_id IS NOT NULL), CHECK(status='MATURED' OR outcome IS NULL));
CREATE TABLE alpha_shadow_v1.forecast_corrections(id uuid PRIMARY KEY REFERENCES alpha_shadow_v1.audit_events,forecast_id uuid NOT NULL REFERENCES alpha_shadow_v1.forecast_records,reason text NOT NULL);
CREATE TABLE alpha_shadow_v1.job_health(id uuid PRIMARY KEY REFERENCES alpha_shadow_v1.audit_events,status text NOT NULL);
CREATE FUNCTION alpha_shadow_v1.no_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Append only: % forbidden',TG_OP; END $$;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['audit_events','forecast_runs','source_vintages','model_registry','forecast_records','outcome_records','forecast_corrections','job_health'] LOOP
 EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON alpha_shadow_v1.%I FOR EACH ROW EXECUTE FUNCTION alpha_shadow_v1.no_mutation()',t);
 EXECUTE format('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON alpha_shadow_v1.%I FOR EACH STATEMENT EXECUTE FUNCTION alpha_shadow_v1.no_mutation()',t);
 END LOOP;
END $$;
CREATE FUNCTION alpha_shadow_v1.append_event(p_id uuid,p_kind text,p_key text,p_body text)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_shadow_v1 AS $$
DECLARE old audit_events; b jsonb:=p_body::jsonb; prev text; h text; f forecast_records; v source_vintages; model audit_events; maturity timestamptz;
BEGIN
 PERFORM pg_advisory_xact_lock(270027);
 SELECT * INTO old FROM audit_events WHERE kind=p_kind AND event_key=p_key;
 IF FOUND THEN
 IF old.body_text<>p_body THEN RAISE EXCEPTION 'Idempotency conflict'; END IF;
 RETURN old.id;
 END IF;
 SELECT record_hash INTO prev FROM audit_events ORDER BY seq DESC LIMIT 1;
 h:=encode(sha256(convert_to(coalesce(prev,'')||'|'||p_kind||'|'||p_key||'|'||p_body,'UTF8')),'hex');
 INSERT INTO audit_events(id,kind,event_key,body_text,body,previous_hash,record_hash) VALUES(p_id,p_kind,p_key,p_body,b,prev,h);
 CASE p_kind
 WHEN 'run' THEN INSERT INTO forecast_runs VALUES(p_id,(b->>'session')::date,b->>'mode');
 WHEN 'vintage' THEN
 IF encode(sha256(decode(b->>'raw_b64','base64')),'hex')<>b->>'source_hash' THEN RAISE EXCEPTION 'Source hash mismatch'; END IF;
 INSERT INTO source_vintages VALUES(p_id,b->>'source_hash',b->>'qualification',(b->>'publication_at')::timestamptz,(b->>'ingestion_at')::timestamptz);
 WHEN 'model' THEN INSERT INTO model_registry VALUES(p_id,b->>'name',b->>'version');
 WHEN 'forecast' THEN
 SELECT * INTO STRICT v FROM source_vintages WHERE id=(b->>'vintage_id')::uuid;
 SELECT * INTO STRICT model FROM audit_events WHERE id=(b->>'model_id')::uuid AND kind='model';
 IF (b->>'issued_at')::timestamptz>clock_timestamp() OR (b->>'decision_at')::timestamptz>(b->>'issued_at')::timestamptz OR (b->>'status'='FORECAST' AND v.ingestion_at>(b->>'issued_at')::timestamptz) THEN RAISE EXCEPTION 'Time travel'; END IF;
 IF (SELECT mode FROM forecast_runs WHERE id=(b->>'run_id')::uuid)='PROSPECTIVE' AND ((clock_timestamp()-(b->>'issued_at')::timestamptz)>interval '10 minutes' OR ((b->>'issued_at')::timestamptz AT TIME ZONE 'UTC')::date<>(b->>'session')::date) THEN RAISE EXCEPTION 'Backdated prospective issuance'; END IF;
 IF b->>'status'='FORECAST' AND (v.qualification<>'QUALIFIED_PIT' OR coalesce((model.body->>'qualified')::boolean,false)=false) THEN RAISE EXCEPTION 'Unqualified forecast'; END IF;
 IF b->>'probability_calibrated' IS NOT NULL AND coalesce((model.body->>'calibrated')::boolean,false)=false THEN RAISE EXCEPTION 'Unsupported calibration'; END IF;
 INSERT INTO forecast_records VALUES(p_id,(b->>'run_id')::uuid,v.id,model.id,(b->>'session')::date,b->>'symbol',b->>'label_type',(b->>'threshold_pct')::int,(b->>'horizon')::int,(b->>'issued_at')::timestamptz,(b->>'decision_at')::timestamptz,b->>'status',(b->>'probability_raw')::double precision,(b->>'probability_calibrated')::double precision);
 WHEN 'outcome' THEN
 SELECT * INTO STRICT f FROM forecast_records WHERE id=(b->>'forecast_id')::uuid;
 SELECT (body->>'horizon_end_at')::timestamptz INTO maturity FROM audit_events WHERE id=f.id;
 IF b->>'status'='MATURED' AND (maturity IS NULL OR maturity>clock_timestamp() OR (b->>'last_publication_at')::timestamptz<maturity OR b->>'completed_sessions' IS NULL OR b->>'last_publication_at' IS NULL OR (b->>'completed_sessions')::int<>f.horizon OR (b->>'last_publication_at')::timestamptz>clock_timestamp() OR b->>'outcome' IS NULL) THEN RAISE EXCEPTION 'Immature outcome'; END IF;
 INSERT INTO outcome_records VALUES(p_id,f.id,b->>'status',(b->>'outcome')::boolean,(b->>'source_vintage_id')::uuid);
 WHEN 'correction' THEN INSERT INTO forecast_corrections VALUES(p_id,(b->>'forecast_id')::uuid,b->>'reason');
 WHEN 'health' THEN INSERT INTO job_health VALUES(p_id,b->>'status');
 ELSE RAISE EXCEPTION 'Unsupported event'; END CASE;
 RETURN p_id;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA alpha_shadow_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA alpha_shadow_v1 FROM PUBLIC;
GRANT USAGE ON SCHEMA alpha_shadow_v1 TO alpha_shadow_writer,alpha_shadow_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA alpha_shadow_v1 TO alpha_shadow_writer,alpha_shadow_reader;
GRANT EXECUTE ON FUNCTION alpha_shadow_v1.append_event(uuid,text,text,text) TO alpha_shadow_writer;
COMMIT;
