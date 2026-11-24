BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED'; END IF; END $$;
CREATE OR REPLACE FUNCTION alpha_full_price_v1.record(pid uuid,pbody text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_full_price_v1,pg_temp AS $$
DECLARE b jsonb:=pbody::jsonb; r jsonb; old uuid; sd date; latest date; stamp timestamptz; allowed_symbols text[]; expected_rows integer;
BEGIN
 IF b->'manifest'->'symbols' = to_jsonb(ARRAY['ANET','NVDA','AMD','CRWD','AVGO','GOOG','GS','META','MU','LRCX','ADI','ALAB','AMAT','AMZN','CRDO','CSCO','GE','GEV','KLAC','LLY','MRVL','NET','ORCL','RTX','TSM']::text[]) THEN
  allowed_symbols := ARRAY['ANET','NVDA','AMD','CRWD','AVGO','GOOG','GS','META','MU','LRCX','ADI','ALAB','AMAT','AMZN','CRDO','CSCO','GE','GEV','KLAC','LLY','MRVL','NET','ORCL','RTX','TSM']::text[];
 ELSE
  allowed_symbols := ARRAY['ANET','NVDA','AMD','CRWD','AVGO','GOOG','GS','META','MU','LRCX','ADI','AEIS','AGQ','ALAB','ALLT','ALNY','AMAT','AMZN','AUGO','B','BABA','BBIO','BE','BILI','CDE','CQQQ','CRDO','CSCO','CYBR','FMCC','FNLPF','FNMA','GDX','GE','GEV','KLAC','LI','LITE','LLY','MKSI','MRVL','NBIS','NET','NFLX','NUGT','OCUL','ORCL','PAAS','RDDT','RTX','SCZM','SEZL','STRIP','SYM','TSM','TWLO','U','UGL','UPST']::text[];
 END IF;
 expected_rows := cardinality(allowed_symbols)*2;
 IF NOT (b ?& ARRAY['schema_version','model_name','fixture','qualified','model_version','rows','session','issued_at'])
    OR b->>'session' IS NULL OR b->>'issued_at' IS NULL OR b->>'model_version' IS NULL
    OR length(pbody)>3000000 OR b->>'schema_version' IS DISTINCT FROM 'ALPHA_FULL_PRICE_RUN_V1'
    OR b->>'model_name' IS DISTINCT FROM 'ALPHA_FULL_PRICE' OR b->>'fixture' IS DISTINCT FROM 'false' OR b->>'qualified' IS DISTINCT FROM 'false'
    OR jsonb_typeof(b->'fixture') IS DISTINCT FROM 'boolean' OR jsonb_typeof(b->'qualified') IS DISTINCT FROM 'boolean'
    OR (b->>'model_version') !~ '^ALPHA_FULL_PRICE_V1-[0-9a-f]{16}$'
    OR jsonb_typeof(b->'rows')<>'array' OR jsonb_array_length(b->'rows')<>expected_rows
 THEN RAISE EXCEPTION 'ALPHA_FULL_PRICE_INVALID_MANIFEST'; END IF;
 sd:=(b->>'session')::date; stamp:=(b->>'issued_at')::timestamptz;
 PERFORM pg_advisory_xact_lock(280012);
 SELECT id INTO old FROM runs WHERE session_date=sd AND model_version=b->>'model_version';
 IF FOUND THEN RETURN old; END IF;
 SELECT max(session_date) INTO latest FROM alpha_research_v3.calendar_sessions WHERE close_at<=clock_timestamp();
 IF sd IS DISTINCT FROM latest OR stamp>clock_timestamp() OR stamp<clock_timestamp()-interval '10 minutes'
    OR NOT EXISTS(SELECT 1 FROM alpha_research_v3.calendar_sessions WHERE session_date=sd AND close_at<=stamp AND close_at>stamp-interval '36 hours')
 THEN RAISE EXCEPTION 'ALPHA_FULL_PRICE_NO_BACKFILL_OR_FUTURE_ISSUE'; END IF;
 IF (SELECT count(DISTINCT (x->>'symbol',x->>'horizon')) FROM jsonb_array_elements(b->'rows') x)<>expected_rows
 THEN RAISE EXCEPTION 'ALPHA_FULL_PRICE_DUPLICATE_TARGET'; END IF;
 FOR r IN SELECT value FROM jsonb_array_elements(b->'rows') LOOP
  IF NOT(r ?& ARRAY['symbol','horizon','target_session','session','issued_at','status','model_name','model_version','qualified','calibrated','expected_return_pct'])
   OR r->>'symbol' IS NULL OR NOT ((r->>'symbol') = ANY(allowed_symbols))
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
COMMIT;
