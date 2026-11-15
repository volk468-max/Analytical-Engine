-- Additive diagnostics only. No forecast/outcome/model history is rewritten.
BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED';END IF;END $$;
CREATE OR REPLACE FUNCTION alpha_operations_v4.receipt(pid uuid,b jsonb) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_operations_v4,pg_temp AS $$ BEGIN
 IF EXISTS(SELECT 1 FROM jsonb_object_keys(b) x WHERE x NOT IN('phase','status','reason','session','issued','blocked','real_forecasts','first_issue_at','latest_issue_at','issued_at','schedule','models','checked','pending','revision','source_quality','error_code','subscription_active','report_week','run_id','timestamp','message','level','http_responses','http_failures','http_status_counts','exception_type','traceback','exit_code','partial_phases','unresolved','readiness_attempt','fingerprint_kind','first_raw_revision','second_raw_revision','first_semantic_hash','second_semantic_hash','changed_components','first_payload_ref','second_payload_ref')) THEN RAISE EXCEPTION 'SAFE_RECEIPT_FIELDS_ONLY';END IF;
 IF b ? 'run_id' THEN PERFORM (b->>'run_id')::uuid;END IF;
 INSERT INTO receipts(id,body) VALUES(pid,b);RETURN pid;
END $$;
COMMIT;
