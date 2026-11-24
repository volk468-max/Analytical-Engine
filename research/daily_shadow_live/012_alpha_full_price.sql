-- Separate append-only experiment archive; no prior model/history changes.
BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED'; END IF; END $$;
CREATE SCHEMA alpha_full_price_v1;
REVOKE ALL ON SCHEMA alpha_full_price_v1 FROM public;
CREATE TABLE alpha_full_price_v1.runs (
 id uuid PRIMARY KEY,
 session_date date NOT NULL,
 model_version text NOT NULL,
 issued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 body_text text NOT NULL,
 body jsonb NOT NULL,
 sha256 text NOT NULL,
 UNIQUE(session_date,model_version),
 CHECK(body=body_text::jsonb)
);
CREATE FUNCTION alpha_full_price_v1.immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'ALPHA_FULL_PRICE_APPEND_ONLY'; END $$;
CREATE TRIGGER no_update_delete BEFORE UPDATE OR DELETE ON alpha_full_price_v1.runs FOR EACH ROW EXECUTE FUNCTION alpha_full_price_v1.immutable();
CREATE TRIGGER no_truncate BEFORE TRUNCATE ON alpha_full_price_v1.runs FOR EACH STATEMENT EXECUTE FUNCTION alpha_full_price_v1.immutable();
CREATE FUNCTION alpha_full_price_v1.record(pid uuid,pbody text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_full_price_v1,pg_temp AS $$
DECLARE b jsonb:=pbody::jsonb; r jsonb; old uuid; sd date; latest date; stamp timestamptz;
BEGIN
 IF NOT (b ?& ARRAY['schema_version','model_name','fixture','qualified','model_version','rows','session','issued_at'])
    OR b->>'session' IS NULL OR b->>'issued_at' IS NULL OR b->>'model_version' IS NULL
    OR length(pbody)>3000000 OR b->>'schema_version' IS DISTINCT FROM 'ALPHA_FULL_PRICE_RUN_V1'
    OR b->>'model_name' IS DISTINCT FROM 'ALPHA_FULL_PRICE' OR b->>'fixture' IS DISTINCT FROM 'false' OR b->>'qualified' IS DISTINCT FROM 'false'
    OR jsonb_typeof(b->'fixture') IS DISTINCT FROM 'boolean' OR jsonb_typeof(b->'qualified') IS DISTINCT FROM 'boolean'
    OR (b->>'model_version') !~ '^ALPHA_FULL_PRICE_V1-[0-9a-f]{16}$'
    OR jsonb_typeof(b->'rows')<>'array' OR jsonb_array_length(b->'rows')<>118
 THEN RAISE EXCEPTION 'ALPHA_FULL_PRICE_INVALID_MANIFEST'; END IF;
 sd:=(b->>'session')::date; stamp:=(b->>'issued_at')::timestamptz;
 PERFORM pg_advisory_xact_lock(280012);
 SELECT id INTO old FROM runs WHERE session_date=sd AND model_version=b->>'model_version';
 IF FOUND THEN RETURN old; END IF;
 SELECT max(session_date) INTO latest FROM alpha_research_v3.calendar_sessions WHERE close_at<=clock_timestamp();
 IF sd IS DISTINCT FROM latest OR stamp>clock_timestamp() OR stamp<clock_timestamp()-interval '10 minutes'
    OR NOT EXISTS(SELECT 1 FROM alpha_research_v3.calendar_sessions WHERE session_date=sd AND close_at<=stamp AND close_at>stamp-interval '36 hours')
 THEN RAISE EXCEPTION 'ALPHA_FULL_PRICE_NO_BACKFILL_OR_FUTURE_ISSUE'; END IF;
 IF (SELECT count(DISTINCT (x->>'symbol',x->>'horizon')) FROM jsonb_array_elements(b->'rows') x)<>118
 THEN RAISE EXCEPTION 'ALPHA_FULL_PRICE_DUPLICATE_TARGET'; END IF;
 FOR r IN SELECT value FROM jsonb_array_elements(b->'rows') LOOP
  IF NOT(r ?& ARRAY['symbol','horizon','target_session','session','issued_at','status','model_name','model_version','qualified','calibrated','expected_return_pct'])
   OR r->>'symbol' IS NULL OR r->>'symbol' NOT IN ('ANET','NVDA','AMD','CRWD','AVGO','GOOG','GS','META','MU','LRCX','ADI','AEIS','AGQ','ALAB','ALLT','ALNY','AMAT','AMZN','AUGO','B','BABA','BBIO','BE','BILI','CDE','CQQQ','CRDO','CSCO','CYBR','FMCC','FNLPF','FNMA','GDX','GE','GEV','KLAC','LI','LITE','LLY','MKSI','MRVL','NBIS','NET','NFLX','NUGT','OCUL','ORCL','PAAS','RDDT','RTX','SCZM','SEZL','STRIP','SYM','TSM','TWLO','U','UGL','UPST')
   OR r->>'horizon' IS NULL OR r->>'horizon' NOT IN ('10','30')
   OR r->>'model_name' IS DISTINCT FROM 'ALPHA_FULL_PRICE'
   OR r->>'model_version' IS DISTINCT FROM b->>'model_version'
   OR r->>'session' IS DISTINCT FROM b->>'session' OR r->>'issued_at' IS DISTINCT FROM b->>'issued_at'
   OR r->>'qualified' IS DISTINCT FROM 'false' OR r->>'calibrated' IS DISTINCT FROM 'false'
   OR r->>'status' IS NULL OR r->>'status' NOT IN ('STATUS_BLOCKED','EXPERIMENTAL_PRICE_FORECAST')
   OR (r->>'status'='EXPERIMENTAL_PRICE_FORECAST' AND (r->>'expected_return_pct' IS NULL OR (r->>'expected_return_pct')::numeric NOT BETWEEN -100 AND 10000
      OR r->>'band_low_pct' IS NULL OR r->>'band_high_pct' IS NULL OR (r->>'band_low_pct')::numeric>(r->>'band_high_pct')::numeric
      OR (r->>'band_low_pct')::numeric NOT BETWEEN -100 AND 100000 OR (r->>'band_high_pct')::numeric NOT BETWEEN -100 AND 100000))
   OR (r->>'status'='STATUS_BLOCKED' AND r->>'expected_return_pct' IS NOT NULL)
   OR (r->>'target_session')::date IS DISTINCT FROM (SELECT session_date FROM alpha_research_v3.calendar_sessions WHERE session_date>sd ORDER BY session_date OFFSET ((r->>'horizon')::int-1) LIMIT 1)
  THEN RAISE EXCEPTION 'ALPHA_FULL_PRICE_INVALID_ROW'; END IF;
 END LOOP;
 INSERT INTO runs VALUES(pid,sd,b->>'model_version',stamp,pbody,b,encode(sha256(convert_to(pbody,'UTF8')),'hex'));
 RETURN pid;
END $$;
CREATE TABLE alpha_full_price_v1.outcomes (
 run_id uuid REFERENCES alpha_full_price_v1.runs, symbol text NOT NULL,horizon int NOT NULL,
 actual_return_pct double precision NOT NULL, available_at timestamptz NOT NULL,
 PRIMARY KEY(run_id,symbol,horizon), CHECK(actual_return_pct>=-100 AND actual_return_pct<'Infinity'::float8)
);
CREATE TRIGGER immutable_outcomes BEFORE UPDATE OR DELETE ON alpha_full_price_v1.outcomes FOR EACH ROW EXECUTE FUNCTION alpha_full_price_v1.immutable();
CREATE TRIGGER immutable_outcomes_truncate BEFORE TRUNCATE ON alpha_full_price_v1.outcomes FOR EACH STATEMENT EXECUTE FUNCTION alpha_full_price_v1.immutable();
CREATE FUNCTION alpha_full_price_v1.resolve(pid uuid,s text,h int,y double precision,available timestamptz) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_full_price_v1,pg_temp AS $$
DECLARE r jsonb; closes timestamptz;
BEGIN
 SELECT x INTO r FROM runs a CROSS JOIN LATERAL jsonb_array_elements(a.body->'rows') x
 WHERE a.id=pid AND x->>'symbol'=s AND (x->>'horizon')::int=h AND x->>'status'='EXPERIMENTAL_PRICE_FORECAST';
 IF NOT FOUND THEN RAISE EXCEPTION 'PRICE_FORECAST_NOT_FOUND'; END IF;
 SELECT close_at INTO closes FROM alpha_research_v3.calendar_sessions WHERE session_date=(r->>'target_session')::date;
 IF closes IS NULL OR available>clock_timestamp() OR available<closes OR available<clock_timestamp()-interval '10 minutes'
 THEN RAISE EXCEPTION 'PRICE_OUTCOME_NOT_MATURE_OR_FUTURE_AVAILABLE'; END IF;
 INSERT INTO outcomes VALUES(pid,s,h,y,available) ON CONFLICT DO NOTHING;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA alpha_full_price_v1 FROM public;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA alpha_full_price_v1 FROM public;
GRANT USAGE ON SCHEMA alpha_full_price_v1 TO alpha_shadow_writer;
GRANT SELECT ON alpha_full_price_v1.runs,alpha_full_price_v1.outcomes TO alpha_shadow_writer;
GRANT EXECUTE ON FUNCTION alpha_full_price_v1.resolve(uuid,text,int,double precision,timestamptz) TO alpha_shadow_writer;
GRANT EXECUTE ON FUNCTION alpha_full_price_v1.record(uuid,text) TO alpha_shadow_writer;
COMMIT;
