BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED';END IF;END $$;
DO $patch$ DECLARE code text;needle text; BEGIN
 code:=pg_get_functiondef('alpha_research_v3.append(uuid,text,text,text)'::regprocedure);
 needle:='m->>''name'' NOT IN(''HIST'',''REGIME'',''VOL'',''RISK_FORECAST'',''ENSEMBLE_RISK'')';
 IF position(needle IN code)=0 THEN RAISE EXCEPTION 'MARKET_PRECURSORS_PATCH_CONTRACT_DRIFT';END IF;
 code:=replace(code,needle,'m->>''name'' NOT IN(''HIST'',''REGIME'',''VOL'',''RISK_FORECAST'',''ENSEMBLE_RISK'',''MARKET_PRECURSORS'')');
 code:=replace(code,'m->>''name'' NOT IN(''VOL'',''RISK_FORECAST'',''ENSEMBLE_RISK'') THEN','m->>''name'' NOT IN(''VOL'',''RISK_FORECAST'',''ENSEMBLE_RISK'',''MARKET_PRECURSORS'') THEN');
 needle:='SELECT close_at INTO STRICT closing FROM calendar_sessions';
 IF position(needle IN code)=0 THEN RAISE EXCEPTION 'MARKET_PRECURSORS_TARGET_PATCH_DRIFT';END IF;
 code:=replace(code,needle,$guard$
 IF m->>'name'='MARKET_PRECURSORS' AND (b->>'symbol' NOT IN('ANET','NVDA','AMD','CRWD','NBIS','GOOG','GS','META','MU','LRCX','SPY','QQQ','SOXX') OR (b->>'horizon')::int NOT IN(10,30) OR b->>'label_type' NOT IN('LOW_INTRADAY','EOD_CLOSE')) THEN RAISE EXCEPTION 'MARKET_PRECURSORS_TARGET_OUTSIDE_MANIFEST';END IF;
 SELECT close_at INTO STRICT closing FROM calendar_sessions
 $guard$);
 EXECUTE code;
END $patch$;
COMMIT;
