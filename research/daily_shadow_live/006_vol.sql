-- Add VOL/30 sessions without modifying applied001-005 or existing journal rows.
BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED';END IF;END $$;
ALTER TABLE alpha_research_v3.forecasts DROP CONSTRAINT forecasts_horizon_check;
ALTER TABLE alpha_research_v3.forecasts ADD CONSTRAINT forecasts_horizon_check CHECK(horizon IN(10,20,30,60));
DO $patch$ DECLARE code text;needle text;replacement text; BEGIN
 code:=pg_get_functiondef('alpha_research_v3.append(uuid,text,text,text)'::regprocedure);
 needle:='m->>''name'' NOT IN(''HIST'',''REGIME'')';
 IF position(needle IN code)=0 THEN RAISE EXCEPTION 'VOL_PATCH_CONTRACT_DRIFT';END IF;
 code:=replace(code,needle,'m->>''name'' NOT IN(''HIST'',''REGIME'',''VOL'')');
 needle:='SELECT close_at INTO STRICT closing FROM calendar_sessions';
 IF position(needle IN code)=0 THEN RAISE EXCEPTION 'VOL_PATCH_TARGET_DRIFT';END IF;
 replacement:=$guard$
  IF m->>'name'='VOL' AND (b->>'symbol' NOT IN('ANET','NVDA','AMD','CRWD','NBIS','GOOG','GS','META','MU','LRCX') OR (b->>'horizon')::int NOT IN(10,30) OR b->>'label_type' NOT IN('LOW_INTRADAY','EOD_CLOSE')) THEN RAISE EXCEPTION 'VOL_TARGET_OUTSIDE_OWNER_MANIFEST';END IF;
  IF (b->>'horizon')::int=30 AND m->>'name'<>'VOL' THEN RAISE EXCEPTION 'LEGACY_MODEL_30_NOT_PREPARED';END IF;
  SELECT close_at INTO STRICT closing FROM calendar_sessions
$guard$;
 code:=replace(code,needle,replacement);
 EXECUTE code;
END $patch$;
COMMIT;
