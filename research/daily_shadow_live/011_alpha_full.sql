-- Separate append-only experiment archive; no prior model/history changes.
BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED'; END IF; END $$;
CREATE SCHEMA alpha_full_v1;
REVOKE ALL ON SCHEMA alpha_full_v1 FROM public;
CREATE TABLE alpha_full_v1.runs (
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
CREATE FUNCTION alpha_full_v1.immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'ALPHA_FULL_APPEND_ONLY'; END $$;
CREATE TRIGGER no_update_delete BEFORE UPDATE OR DELETE ON alpha_full_v1.runs FOR EACH ROW EXECUTE FUNCTION alpha_full_v1.immutable();
CREATE TRIGGER no_truncate BEFORE TRUNCATE ON alpha_full_v1.runs FOR EACH STATEMENT EXECUTE FUNCTION alpha_full_v1.immutable();
CREATE FUNCTION alpha_full_v1.record(pid uuid,pbody text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_full_v1,pg_temp AS $$
DECLARE b jsonb:=pbody::jsonb; r jsonb; old uuid; sd date; latest date; stamp timestamptz;
BEGIN
 IF NOT (b ?& ARRAY['schema_version','model_name','fixture','qualified','model_version','rows','session','issued_at'])
    OR b->>'session' IS NULL OR b->>'issued_at' IS NULL OR b->>'model_version' IS NULL
    OR length(pbody)>3000000 OR b->>'schema_version' IS DISTINCT FROM 'ALPHA_FULL_RUN_V1'
    OR b->>'model_name' IS DISTINCT FROM 'ALPHA_FULL' OR b->>'fixture' IS DISTINCT FROM 'false' OR b->>'qualified' IS DISTINCT FROM 'false'
    OR (b->>'model_version') !~ '^ALPHA_FULL_V1-[0-9a-f]{16}$'
    OR jsonb_typeof(b->'rows')<>'array' OR jsonb_array_length(b->'rows')<>120
 THEN RAISE EXCEPTION 'ALPHA_FULL_INVALID_MANIFEST'; END IF;
 sd:=(b->>'session')::date; stamp:=(b->>'issued_at')::timestamptz;
 PERFORM pg_advisory_xact_lock(280011);
 SELECT id INTO old FROM runs WHERE session_date=sd AND model_version=b->>'model_version';
 IF FOUND THEN RETURN old; END IF;
 SELECT max(session_date) INTO latest FROM alpha_research_v3.calendar_sessions WHERE close_at<=clock_timestamp();
 IF sd IS DISTINCT FROM latest OR stamp>clock_timestamp() OR stamp<clock_timestamp()-interval '10 minutes'
    OR NOT EXISTS(SELECT 1 FROM alpha_research_v3.calendar_sessions WHERE session_date=sd AND close_at<=stamp AND close_at>stamp-interval '36 hours')
 THEN RAISE EXCEPTION 'ALPHA_FULL_NO_BACKFILL_OR_FUTURE_ISSUE'; END IF;
 IF (SELECT count(DISTINCT (x->>'symbol',x->>'horizon',x->>'threshold_pct',x->>'label_type')) FROM jsonb_array_elements(b->'rows') x)<>120
 THEN RAISE EXCEPTION 'ALPHA_FULL_DUPLICATE_TARGET'; END IF;
 FOR r IN SELECT value FROM jsonb_array_elements(b->'rows') LOOP
  IF NOT (r ?& ARRAY['symbol','horizon','threshold_pct','label_type','model_name','model_version','session','issued_at','qualified','calibrated','status','probability_raw'])
    OR r->>'symbol' IS NULL OR r->>'horizon' IS NULL OR r->>'threshold_pct' IS NULL OR r->>'label_type' IS NULL
    OR r->>'symbol' NOT IN ('ANET','NVDA','AMD','CRWD','AVGO','GOOG','GS','META','MU','LRCX')
    OR r->>'horizon' NOT IN ('10','30') OR r->>'threshold_pct' NOT IN ('5','10','15')
    OR r->>'label_type' NOT IN ('LOW_INTRADAY','EOD_CLOSE')
    OR r->>'model_name' IS DISTINCT FROM 'ALPHA_FULL' OR r->>'model_version' IS DISTINCT FROM b->>'model_version'
    OR r->>'session' IS DISTINCT FROM b->>'session' OR r->>'issued_at' IS DISTINCT FROM b->>'issued_at'
    OR r->>'qualified' IS DISTINCT FROM 'false' OR r->>'calibrated' IS DISTINCT FROM 'false'
    OR r->>'status' IS NULL
    OR r->>'status' NOT IN ('EXPERIMENTAL_FORECAST','STATUS_BLOCKED')
    OR (r->>'status'='EXPERIMENTAL_FORECAST' AND (r->>'probability_raw' IS NULL OR (r->>'probability_raw')::numeric NOT BETWEEN 0 AND 1))
    OR (r->>'status'='STATUS_BLOCKED' AND r->>'probability_raw' IS NOT NULL)
  THEN RAISE EXCEPTION 'ALPHA_FULL_INVALID_ROW'; END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(b->'rows') a CROSS JOIN jsonb_array_elements(b->'rows') c
   WHERE a->>'symbol'=c->>'symbol' AND a->>'probability_raw' IS NOT NULL AND c->>'probability_raw' IS NOT NULL
   AND (a->>'probability_raw')::numeric+0.0000000001<(c->>'probability_raw')::numeric
   AND ((a->>'horizon'=c->>'horizon' AND a->>'label_type'=c->>'label_type' AND (a->>'threshold_pct')::int<(c->>'threshold_pct')::int)
     OR (a->>'threshold_pct'=c->>'threshold_pct' AND a->>'label_type'=c->>'label_type' AND a->>'horizon'='30' AND c->>'horizon'='10')
     OR (a->>'threshold_pct'=c->>'threshold_pct' AND a->>'horizon'=c->>'horizon' AND a->>'label_type'='LOW_INTRADAY' AND c->>'label_type'='EOD_CLOSE')))
 THEN RAISE EXCEPTION 'ALPHA_FULL_INCOHERENT_PROBABILITIES'; END IF;
 INSERT INTO runs VALUES(pid,sd,b->>'model_version',stamp,pbody,b,encode(sha256(convert_to(pbody,'UTF8')),'hex'));
 RETURN pid;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA alpha_full_v1 FROM public;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA alpha_full_v1 FROM public;
GRANT USAGE ON SCHEMA alpha_full_v1 TO alpha_shadow_writer;
GRANT SELECT ON alpha_full_v1.runs TO alpha_shadow_writer;
GRANT EXECUTE ON FUNCTION alpha_full_v1.record(uuid,text) TO alpha_shadow_writer;
COMMIT;
