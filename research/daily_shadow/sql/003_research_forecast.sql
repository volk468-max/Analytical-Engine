-- Manual, isolated research DB only. Leaves legacy validated/prospective/synthetic tables intact.
BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED'; END IF; END $$;
CREATE SCHEMA alpha_research_v3;
CREATE SCHEMA alpha_licensed_v3;
REVOKE ALL ON SCHEMA alpha_research_v3,alpha_licensed_v3 FROM PUBLIC;
CREATE ROLE alpha_shadow_legal_reviewer NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE TABLE alpha_research_v3.contracts(id uuid PRIMARY KEY,body jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TABLE alpha_research_v3.lifecycle(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,contract_id uuid NOT NULL REFERENCES alpha_research_v3.contracts,action text NOT NULL CHECK(action IN('OFFBOARD_REQUESTED','PURGE_CONFIRMED')),evidence_ref text NOT NULL,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TABLE alpha_research_v3.calendar_sessions(session_date date PRIMARY KEY,close_at timestamptz NOT NULL,version text NOT NULL);
CREATE TABLE alpha_research_v3.journal(id uuid PRIMARY KEY,seq bigint GENERATED ALWAYS AS IDENTITY UNIQUE,event_key text NOT NULL UNIQUE,kind text NOT NULL CHECK(kind IN('FORECAST','OUTCOME','CORRECTION','HEALTH')),body_text text NOT NULL,body jsonb NOT NULL,previous_hash text,record_hash text NOT NULL UNIQUE,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),CHECK(body=body_text::jsonb));
CREATE TABLE alpha_research_v3.forecasts(id uuid PRIMARY KEY REFERENCES alpha_research_v3.journal,contract_id uuid REFERENCES alpha_research_v3.contracts,model_id uuid NOT NULL REFERENCES alpha_shadow_v1.model_registry,session_date date NOT NULL,symbol text NOT NULL,label_type text NOT NULL,threshold_pct int NOT NULL CHECK(threshold_pct IN(5,10,15)),horizon int NOT NULL CHECK(horizon IN(10,20,60)),run_mode text NOT NULL CHECK(run_mode IN('SYNTHETIC','RESEARCH_FORECAST')),status text NOT NULL CHECK(status IN('STATUS_BLOCKED','RESEARCH_FORECAST')),probability_raw double precision CHECK(probability_raw BETWEEN 0 AND 1),probability_calibrated double precision CHECK(probability_calibrated IS NULL),model_status text NOT NULL CHECK(model_status='MODEL_NOT_VALIDATED'),training_status text NOT NULL CHECK(training_status='TRAINING_REPLAY_NOT_PIT'),issued_at timestamptz NOT NULL,horizon_end_at timestamptz NOT NULL,anchor_ref uuid,UNIQUE(session_date,symbol,label_type,threshold_pct,horizon,model_id,run_mode),CHECK(status='RESEARCH_FORECAST' OR probability_raw IS NULL),CHECK(status<>'RESEARCH_FORECAST' OR (probability_raw IS NOT NULL AND anchor_ref IS NOT NULL)));
CREATE TABLE alpha_research_v3.outcomes(id uuid PRIMARY KEY REFERENCES alpha_research_v3.journal,forecast_id uuid NOT NULL REFERENCES alpha_research_v3.forecasts,status text NOT NULL CHECK(status IN('IMMATURE','UNRESOLVED','MATURED')),outcome boolean,CHECK((status='MATURED')=(outcome IS NOT NULL)));
CREATE TABLE alpha_licensed_v3.payloads(id uuid PRIMARY KEY,contract_id uuid NOT NULL REFERENCES alpha_research_v3.contracts,ciphertext bytea NOT NULL,expires_at timestamptz NOT NULL,revision text NOT NULL,UNIQUE(contract_id,revision));
CREATE FUNCTION alpha_research_v3.immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'APPEND_ONLY'; END $$;
DO $$ DECLARE n text; BEGIN FOREACH n IN ARRAY ARRAY['contracts','lifecycle','calendar_sessions','journal','forecasts','outcomes'] LOOP EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON alpha_research_v3.%I FOR EACH ROW EXECUTE FUNCTION alpha_research_v3.immutable()',n); EXECUTE format('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON alpha_research_v3.%I FOR EACH STATEMENT EXECUTE FUNCTION alpha_research_v3.immutable()',n); END LOOP; END $$;
CREATE FUNCTION alpha_research_v3.register_contract(cid uuid,p jsonb) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,pg_temp AS $$
DECLARE old jsonb; BEGIN
 SELECT body INTO old FROM contracts WHERE id=cid;
 IF FOUND THEN IF old<>p THEN RAISE EXCEPTION 'CONTRACT_IMMUTABLE'; END IF; RETURN cid; END IF;
 IF p->>'scope' NOT IN ('UNQUALIFIED','FIXTURE_ONLY','LIVE') THEN RAISE EXCEPTION 'INVALID_SCOPE'; END IF;
 IF p->>'scope'='LIVE' AND current_setting('role')<>'alpha_shadow_legal_reviewer' THEN RAISE EXCEPTION 'LEGAL_REVIEWER_REQUIRED'; END IF;
 INSERT INTO contracts(id,body) VALUES(cid,p);RETURN cid;
END $$;
CREATE FUNCTION alpha_research_v3.authorized(cid uuid) RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,pg_temp AS $$
 SELECT coalesce((c.body->>'paid')::boolean,false) AND c.body->>'scope' IN('LIVE','FIXTURE_ONLY') AND length(coalesce(c.body->>'reviewer_evidence',''))>0 AND c.body->>'operator_class'<>'UNKNOWN'
 AND (c.body->>'total_monthly_usd')::numeric BETWEEN 0 AND 50 AND (c.body->>'access_until')::timestamptz>clock_timestamp() AND (c.body->>'raw_until')::timestamptz>clock_timestamp()
 AND coalesce((c.body->>'raw_storage')::boolean,false) AND coalesce((c.body->>'hash_metadata_retention')::boolean,false) AND coalesce((c.body->>'nonreconstructible_forecasts_retention')::boolean,false) AND coalesce((c.body->>'cloud')::boolean,false) AND coalesce((c.body->>'backups')::boolean,false)
 AND NOT coalesce((c.body->>'revoked')::boolean,false) AND NOT EXISTS(SELECT 1 FROM lifecycle l WHERE l.contract_id=c.id AND l.action='OFFBOARD_REQUESTED') FROM contracts c WHERE c.id=cid
$$;
CREATE FUNCTION alpha_research_v3.save_payload(pid uuid,cid uuid,encrypted bytea,expires timestamptz,rev text) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,alpha_licensed_v3,pg_temp AS $$
DECLARE old uuid; BEGIN
 IF authorized(cid) IS DISTINCT FROM true THEN RAISE EXCEPTION 'LICENSE_OR_TTL_BLOCK'; END IF;
 IF expires> (SELECT (body->>'raw_until')::timestamptz FROM contracts WHERE id=cid) OR expires<=clock_timestamp() THEN RAISE EXCEPTION 'TTL_OUTSIDE_LICENSE'; END IF;
 SELECT id INTO old FROM payloads WHERE contract_id=cid AND revision=rev; IF FOUND THEN RETURN old; END IF;
 INSERT INTO payloads VALUES(pid,cid,encrypted,expires,rev);RETURN pid;
END $$;
CREATE FUNCTION alpha_research_v3.load_payload(pid uuid) RETURNS bytea LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,alpha_licensed_v3,pg_temp AS $$
DECLARE r payloads; BEGIN SELECT * INTO STRICT r FROM payloads WHERE id=pid; IF authorized(r.contract_id) IS DISTINCT FROM true OR r.expires_at<=clock_timestamp() THEN RAISE EXCEPTION 'LICENSE_OR_TTL_BLOCK'; END IF;RETURN r.ciphertext; END $$;
CREATE FUNCTION alpha_research_v3.offboard(cid uuid,receipt text) RETURNS int LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,alpha_licensed_v3,pg_temp AS $$
DECLARE n int; BEGIN
 INSERT INTO lifecycle(contract_id,action,evidence_ref) VALUES(cid,'OFFBOARD_REQUESTED',receipt);
 DELETE FROM payloads WHERE contract_id=cid;GET DIAGNOSTICS n=ROW_COUNT;RETURN n;
END $$;
CREATE FUNCTION alpha_research_v3.expire_payloads() RETURNS int LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,alpha_licensed_v3,pg_temp AS $$
DECLARE n int; BEGIN DELETE FROM payloads p WHERE p.expires_at<=clock_timestamp() OR authorized(p.contract_id) IS DISTINCT FROM true;GET DIAGNOSTICS n=ROW_COUNT;RETURN n; END $$;
CREATE FUNCTION alpha_research_v3.confirm_purge(cid uuid,receipt text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,pg_temp AS $$ BEGIN
 IF current_setting('role')<>'alpha_shadow_legal_reviewer' OR length(receipt)<10 THEN RAISE EXCEPTION 'INDEPENDENT_PURGE_RECEIPT_REQUIRED'; END IF;
 INSERT INTO lifecycle(contract_id,action,evidence_ref) VALUES(cid,'PURGE_CONFIRMED',receipt);
END $$;
CREATE FUNCTION alpha_research_v3.append(pid uuid,k text,ek text,t text) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,alpha_licensed_v3,pg_temp AS $$
DECLARE b jsonb:=t::jsonb;old journal;prev text;h text;f forecasts;c jsonb;m jsonb;mt text;model_recorded timestamptz;closing timestamptz;ending timestamptz;payload payloads;
BEGIN
 PERFORM pg_advisory_xact_lock(280003);
 SELECT * INTO old FROM journal WHERE event_key=ek;IF FOUND THEN IF old.body_text<>t OR old.kind<>k THEN RAISE EXCEPTION 'IDEMPOTENCY_CONFLICT'; END IF;RETURN old.id;END IF;
 -- Whitelist rather than a blacklist: no prices/anchor/raw data can enter immutable JSON.
 IF k='FORECAST' THEN
  IF EXISTS(SELECT 1 FROM jsonb_object_keys(b) x WHERE x NOT IN('contract_id','model_id','session','symbol','label_type','threshold_pct','horizon','run_mode','status','reason','probability_raw','probability_calibrated','model_status','training_status','issued_at','decision_at','horizon_end_at','anchor_ref','source_fixture','source_retrieved_at','source_publication_at','source_revision','model_hash','calendar','label_definition','data_status')) THEN RAISE EXCEPTION 'IMMUTABLE_PAYLOAD_FIELD_NOT_ALLOWED'; END IF;
  SELECT body,body_text,recorded_at INTO STRICT m,mt,model_recorded FROM alpha_shadow_v1.audit_events WHERE id=(b->>'model_id')::uuid AND kind='model';
  IF b->>'model_hash' IS DISTINCT FROM encode(sha256(convert_to(mt,'UTF8')),'hex') THEN RAISE EXCEPTION 'FROZEN_MODEL_HASH_MISMATCH'; END IF;
  IF m->>'name' NOT IN('HIST','REGIME') OR m->'series'->>'symbol'<>b->>'symbol' OR m->'series'->>'label_type'<>b->>'label_type' OR m->'series'->>'threshold_pct'<>b->>'threshold_pct' OR m->'series'->>'horizon'<>b->>'horizon' THEN RAISE EXCEPTION 'MODEL_SERIES_MISMATCH'; END IF;
  SELECT close_at INTO STRICT closing FROM calendar_sessions WHERE session_date=(b->>'session')::date;
  SELECT close_at INTO STRICT ending FROM calendar_sessions WHERE session_date>(b->>'session')::date ORDER BY session_date OFFSET ((b->>'horizon')::int-1) LIMIT 1;
  IF ending<>(b->>'horizon_end_at')::timestamptz THEN RAISE EXCEPTION 'EXACT_FUTURE_SESSION_MATURITY_REQUIRED'; END IF;
  IF b->>'status'='RESEARCH_FORECAST' THEN
   IF NOT b ?& ARRAY['contract_id','model_id','decision_at','issued_at','source_retrieved_at','source_fixture','anchor_ref','data_status'] OR b->>'decision_at' IS NULL OR b->>'data_status' NOT IN('REVIEWED_INPUTS','UNQUALIFIED_FIXTURE') THEN RAISE EXCEPTION 'EXPLICIT_ASOF_DATA_GATES_REQUIRED'; END IF;
   IF authorized((b->>'contract_id')::uuid) IS DISTINCT FROM true THEN RAISE EXCEPTION 'LICENSE_OR_TTL_BLOCK'; END IF;
   SELECT body INTO STRICT c FROM contracts WHERE id=(b->>'contract_id')::uuid;
   SELECT * INTO STRICT payload FROM payloads WHERE id=(b->>'anchor_ref')::uuid AND contract_id=(b->>'contract_id')::uuid;
   IF payload.expires_at<=ending+interval '1 day' OR (b->>'source_retrieved_at') IS NULL OR (b->>'source_retrieved_at')::timestamptz>(b->>'decision_at')::timestamptz OR (b->>'decision_at')::timestamptz>(b->>'issued_at')::timestamptz OR (b->>'issued_at')::timestamptz<=closing OR ((b->>'issued_at')::timestamptz AT TIME ZONE 'America/New_York')::date<>(b->>'session')::date OR ((b->>'issued_at')::timestamptz AT TIME ZONE 'America/New_York')::time<time '20:30' OR NOT coalesce((c->>'finalization_verified')::boolean,false) THEN RAISE EXCEPTION 'ASOF_OR_RETENTION_FAILURE'; END IF;
   IF (b->>'source_publication_at')::timestamptz>(b->>'source_retrieved_at')::timestamptz OR (m->>'fit_cutoff')::timestamptz>(b->>'issued_at')::timestamptz OR (m->>'created_at') IS NULL OR (m->>'created_at')::timestamptz>(b->>'issued_at')::timestamptz THEN RAISE EXCEPTION 'FUTURE_INPUT_OR_MODEL'; END IF;
   IF b->>'symbol' IN('A','B','C') THEN RAISE EXCEPTION 'PORTFOLIO_NAV_NOT_QUALIFIED'; END IF;
   IF (b->>'run_mode'='RESEARCH_FORECAST' AND (model_recorded>(b->>'issued_at')::timestamptz OR c->>'scope'<>'LIVE' OR b->>'data_status'<>'REVIEWED_INPUTS' OR coalesce((b->>'source_fixture')::boolean,true) OR coalesce((m->>'fixture')::boolean,false) OR clock_timestamp()-(b->>'issued_at')::timestamptz>interval '10 minutes' OR (b->>'issued_at')::timestamptz>clock_timestamp())) OR (b->>'run_mode'='SYNTHETIC' AND (c->>'scope'<>'FIXTURE_ONLY' OR NOT coalesce((b->>'source_fixture')::boolean,false))) THEN RAISE EXCEPTION 'FIXTURE_LIVE_OR_BACKDATE_BOUNDARY'; END IF;
  END IF;
 ELSIF k='OUTCOME' THEN
  IF EXISTS(SELECT 1 FROM jsonb_object_keys(b) x WHERE x NOT IN('forecast_id','status','outcome','completed_sessions','last_publication_at','revision_ref','supersedes_id','reason')) THEN RAISE EXCEPTION 'OUTCOME_RAW_FIELD_FORBIDDEN'; END IF;
  SELECT * INTO STRICT f FROM forecasts WHERE id=(b->>'forecast_id')::uuid;
  IF b->>'status'='MATURED' AND (coalesce((b->>'completed_sessions')::int,0)<>f.horizon OR f.horizon_end_at>clock_timestamp() OR b->>'last_publication_at' IS NULL OR (b->>'last_publication_at')::timestamptz<f.horizon_end_at OR (b->>'last_publication_at')::timestamptz>clock_timestamp() OR authorized(f.contract_id) IS DISTINCT FROM true) THEN RAISE EXCEPTION 'FULL_MATURE_LICENSED_OUTCOME_REQUIRED'; END IF;
  IF b->>'supersedes_id' IS NOT NULL AND NOT EXISTS(SELECT 1 FROM outcomes o WHERE o.id=(b->>'supersedes_id')::uuid AND o.forecast_id=f.id) THEN RAISE EXCEPTION 'CORRECTION_LINK_MISMATCH'; END IF;
 ELSIF k='CORRECTION' THEN
  IF EXISTS(SELECT 1 FROM jsonb_object_keys(b) x WHERE x NOT IN('forecast_id','replacement_payload_ref','source_revision','observed_at','reason')) THEN RAISE EXCEPTION 'CORRECTION_FIELDS_FORBIDDEN'; END IF;
  SELECT * INTO STRICT f FROM forecasts WHERE id=(b->>'forecast_id')::uuid;
  IF NOT EXISTS(SELECT 1 FROM payloads p WHERE p.id=(b->>'replacement_payload_ref')::uuid AND p.contract_id=f.contract_id AND p.revision=b->>'source_revision' AND p.expires_at>clock_timestamp()) OR authorized(f.contract_id) IS DISTINCT FROM true OR b->>'observed_at' IS NULL OR (b->>'observed_at')::timestamptz>clock_timestamp() THEN RAISE EXCEPTION 'CORRECTION_SOURCE_UNAVAILABLE'; END IF;
 ELSIF k='HEALTH' THEN
  IF EXISTS(SELECT 1 FROM jsonb_object_keys(b) x WHERE x NOT IN('status','reason')) THEN RAISE EXCEPTION 'HEALTH_FIELDS_FORBIDDEN'; END IF;
 ELSE RAISE EXCEPTION 'INVALID_KIND'; END IF;
 SELECT record_hash INTO prev FROM journal ORDER BY seq DESC LIMIT 1;
 h:=encode(sha256(convert_to(coalesce(prev,'')||'|'||k||'|'||ek||'|'||t,'UTF8')),'hex');INSERT INTO journal VALUES(pid,DEFAULT,ek,k,t,b,prev,h,DEFAULT);
 IF k='FORECAST' THEN INSERT INTO forecasts VALUES(pid,(b->>'contract_id')::uuid,(b->>'model_id')::uuid,(b->>'session')::date,b->>'symbol',b->>'label_type',(b->>'threshold_pct')::int,(b->>'horizon')::int,b->>'run_mode',b->>'status',(b->>'probability_raw')::double precision,(b->>'probability_calibrated')::double precision,b->>'model_status',b->>'training_status',(b->>'issued_at')::timestamptz,(b->>'horizon_end_at')::timestamptz,(b->>'anchor_ref')::uuid);
 ELSIF k='OUTCOME' THEN INSERT INTO outcomes VALUES(pid,(b->>'forecast_id')::uuid,b->>'status',(b->>'outcome')::boolean);END IF;
 RETURN pid;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA alpha_research_v3,alpha_licensed_v3 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA alpha_research_v3 FROM PUBLIC;
GRANT USAGE ON SCHEMA alpha_research_v3 TO alpha_shadow_writer,alpha_shadow_reader,alpha_shadow_legal_reviewer;
GRANT SELECT ON ALL TABLES IN SCHEMA alpha_research_v3 TO alpha_shadow_writer,alpha_shadow_reader,alpha_shadow_legal_reviewer;
GRANT EXECUTE ON FUNCTION alpha_research_v3.register_contract(uuid,jsonb),alpha_research_v3.save_payload(uuid,uuid,bytea,timestamptz,text),alpha_research_v3.load_payload(uuid),alpha_research_v3.offboard(uuid,text),alpha_research_v3.expire_payloads(),alpha_research_v3.append(uuid,text,text,text) TO alpha_shadow_writer;
GRANT EXECUTE ON FUNCTION alpha_research_v3.register_contract(uuid,jsonb),alpha_research_v3.confirm_purge(uuid,text) TO alpha_shadow_legal_reviewer;
COMMIT;
