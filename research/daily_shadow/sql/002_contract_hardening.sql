-- REVIEW / DISPOSABLE STAGING ONLY. No automatic production migration.
BEGIN;
DO $$ BEGIN
 IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'Isolated database required'; END IF;
END $$;
CREATE ROLE alpha_shadow_model_registrar NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT USAGE ON SCHEMA alpha_shadow_v1 TO alpha_shadow_model_registrar;
GRANT SELECT ON ALL TABLES IN SCHEMA alpha_shadow_v1 TO alpha_shadow_model_registrar;
ALTER FUNCTION alpha_shadow_v1.append_event(uuid,text,text,text) RENAME TO append_event_v1;
REVOKE ALL ON FUNCTION alpha_shadow_v1.append_event_v1(uuid,text,text,text) FROM PUBLIC,alpha_shadow_writer;
CREATE FUNCTION alpha_shadow_v1.append_event(p_id uuid,p_kind text,p_key text,p_body text)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_shadow_v1 AS $$
DECLARE b jsonb:=p_body::jsonb; m jsonb; v jsonb; mode text;
BEGIN
 PERFORM pg_advisory_xact_lock(270027);
 IF p_kind='model' AND coalesce((b->>'qualified')::boolean,false) AND b->>'qualification_scope' IS DISTINCT FROM 'SYNTHETIC_ONLY'
 AND current_setting('role')<>'alpha_shadow_model_registrar'
 AND NOT EXISTS(SELECT 1 FROM audit_events WHERE kind='model' AND event_key=p_key AND body_text=p_body)
 THEN RAISE EXCEPTION 'Separate model registrar approval required'; END IF;
 IF current_setting('role')='alpha_shadow_model_registrar' AND p_kind<>'model' THEN RAISE EXCEPTION 'Registrar may only register models'; END IF;
 IF p_kind='forecast' THEN
  SELECT body INTO STRICT m FROM audit_events WHERE id=(b->>'model_id')::uuid AND kind='model';
  SELECT body INTO STRICT v FROM audit_events WHERE id=(b->>'vintage_id')::uuid AND kind='vintage';
  SELECT r.mode INTO STRICT mode FROM forecast_runs r WHERE id=(b->>'run_id')::uuid;
  IF m ? 'series' AND (m->'series'->>'symbol'<>b->>'symbol' OR m->'series'->>'label_type'<>b->>'label_type' OR m->'series'->>'threshold_pct'<>b->>'threshold_pct' OR m->'series'->>'horizon'<>b->>'horizon') THEN RAISE EXCEPTION 'Wrong model series'; END IF;
  IF mode='PROSPECTIVE' AND (m->>'qualification_scope'='SYNTHETIC_ONLY' OR coalesce((v->>'synthetic')::boolean,false)) THEN RAISE EXCEPTION 'Synthetic input/model is not prospective'; END IF;
  IF b->>'status'='FORECAST' THEN
   IF NOT coalesce(m->'supported_tasks' ? ((b->>'label_type')||':'||(b->>'threshold_pct')||':'||(b->>'horizon')),false)
   OR NOT coalesce((v->>'actions_qualified')::boolean,false)
   OR coalesce((v->>'historical_archive')::boolean,false)
   OR b->>'frozen_anchor' IS NULL OR (b->>'frozen_anchor')::double precision<=0
   OR b->>'horizon_end_at' IS NULL OR (b->>'horizon_end_at')::timestamptz<=(b->>'issued_at')::timestamptz
   OR (v->>'ingestion_at')::timestamptz>(b->>'decision_at')::timestamptz
   OR (v->>'publication_at')::timestamptz>(b->>'decision_at')::timestamptz
   OR (m->>'fit_cutoff')::timestamptz>(b->>'issued_at')::timestamptz
   OR (m->>'created_at')::timestamptz>(b->>'issued_at')::timestamptz
   OR (m->>'qualification_scope' IS DISTINCT FROM 'SYNTHETIC_ONLY' AND m->>'created_at' IS NULL)
   THEN RAISE EXCEPTION 'Unsupported or unavailable forecast inputs'; END IF;
   IF (b->>'label_type'='PORTFOLIO_EOD_CLOSE' AND v->>'basis'<>'FROZEN_TOTAL_RETURN_NAV')
   OR (b->>'label_type'<>'PORTFOLIO_EOD_CLOSE' AND v->>'basis'<>'SPLIT_NORMALIZED_PRICE') THEN RAISE EXCEPTION 'Wrong source basis'; END IF;
  END IF;
 END IF;
 RETURN append_event_v1(p_id,p_kind,p_key,p_body);
END $$;
REVOKE ALL ON FUNCTION alpha_shadow_v1.append_event(uuid,text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION alpha_shadow_v1.append_event(uuid,text,text,text) TO alpha_shadow_writer,alpha_shadow_model_registrar;
COMMIT;
