-- Change future active target guards only. No existing rows are modified.
BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED';END IF;END $$;
DO $patch$ DECLARE code text;needle text; BEGIN
 code:=pg_get_functiondef('alpha_research_v3.append(uuid,text,text,text)'::regprocedure);
 needle:=quote_literal('NBIS');
 IF (length(code)-length(replace(code,needle,'')))/length(needle)<>2 THEN RAISE EXCEPTION 'AVGO_UNIVERSE_PATCH_CONTRACT_DRIFT';END IF;
 code:=replace(code,needle,quote_literal('AVGO'));
 EXECUTE code;
END $patch$;
COMMIT;
