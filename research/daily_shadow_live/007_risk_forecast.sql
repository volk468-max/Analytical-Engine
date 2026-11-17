BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED';END IF;END $$;
DO $patch$ DECLARE code text;needle text; BEGIN
 code:=pg_get_functiondef('alpha_research_v3.append(uuid,text,text,text)'::regprocedure);
 needle:='m->>''name'' NOT IN(''HIST'',''REGIME'',''VOL'')';
 IF position(needle IN code)=0 THEN RAISE EXCEPTION 'RISK_FORECAST_PATCH_CONTRACT_DRIFT';END IF;
 code:=replace(code,needle,'m->>''name'' NOT IN(''HIST'',''REGIME'',''VOL'',''RISK_FORECAST'')');
 code:=replace(code,'m->>''name''=''VOL'' AND','m->>''name'' IN(''VOL'',''RISK_FORECAST'') AND');
 code:=replace(code,'m->>''name''<>''VOL'' THEN','m->>''name'' NOT IN(''VOL'',''RISK_FORECAST'') THEN');
 EXECUTE code;
END $patch$;
COMMIT;
