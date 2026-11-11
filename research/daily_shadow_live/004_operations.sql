BEGIN;
DO $$ BEGIN IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'ISOLATED_DATABASE_REQUIRED'; END IF; END $$;
CREATE SCHEMA alpha_operations_v4;
REVOKE ALL ON SCHEMA alpha_operations_v4 FROM PUBLIC;
CREATE TABLE alpha_operations_v4.receipts(id uuid PRIMARY KEY,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),body jsonb NOT NULL);
CREATE TABLE alpha_operations_v4.reports(week date PRIMARY KEY,created_at timestamptz NOT NULL DEFAULT clock_timestamp(),body jsonb NOT NULL);
CREATE TABLE alpha_operations_v4.baselines(forecast_id uuid PRIMARY KEY REFERENCES alpha_research_v3.forecasts,probability double precision NOT NULL CHECK(probability BETWEEN 0 AND 1),support int NOT NULL CHECK(support>=0),cutoff timestamptz NOT NULL);
CREATE TABLE alpha_operations_v4.renewals(id uuid PRIMARY KEY,contract_id uuid NOT NULL REFERENCES alpha_research_v3.contracts,reviewed_at timestamptz NOT NULL DEFAULT clock_timestamp(),access_until timestamptz NOT NULL,evidence_ref text NOT NULL);
CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON alpha_operations_v4.receipts FOR EACH ROW EXECUTE FUNCTION alpha_research_v3.immutable();
CREATE TRIGGER immutable_reports BEFORE UPDATE OR DELETE ON alpha_operations_v4.reports FOR EACH ROW EXECUTE FUNCTION alpha_research_v3.immutable();
CREATE TRIGGER immutable_baselines BEFORE UPDATE OR DELETE ON alpha_operations_v4.baselines FOR EACH ROW EXECUTE FUNCTION alpha_research_v3.immutable();
CREATE TRIGGER immutable_renewals BEFORE UPDATE OR DELETE ON alpha_operations_v4.renewals FOR EACH ROW EXECUTE FUNCTION alpha_research_v3.immutable();
CREATE TABLE alpha_operations_v4.readiness(id uuid PRIMARY KEY,contract_id uuid NOT NULL REFERENCES alpha_research_v3.contracts,session_date date NOT NULL,source_revision text NOT NULL,first_seen timestamptz NOT NULL,second_seen timestamptz NOT NULL,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TRIGGER immutable_readiness BEFORE UPDATE OR DELETE ON alpha_operations_v4.readiness FOR EACH ROW EXECUTE FUNCTION alpha_research_v3.immutable();
CREATE FUNCTION alpha_operations_v4.ready(cid uuid,day date,rev text,base1 text,base2 text,seen1 timestamptz,seen2 timestamptz) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_operations_v4,pg_temp AS $$ BEGIN
 IF alpha_research_v3.authorized(cid) IS DISTINCT FROM true OR base1<>base2 OR length(rev)<>64 OR seen2-seen1<interval '60 seconds' OR seen2>clock_timestamp() OR (seen2 AT TIME ZONE 'America/New_York')::date<>day OR (seen2 AT TIME ZONE 'America/New_York')::time<time '20:30' OR NOT EXISTS(SELECT 1 FROM alpha_research_v3.calendar_sessions c WHERE c.session_date=day AND c.close_at<seen1) THEN RAISE EXCEPTION 'READINESS_NOT_VERIFIED';END IF;
 INSERT INTO readiness VALUES(gen_random_uuid(),cid,day,rev,seen1,seen2,DEFAULT);END $$;
DO $patch$ DECLARE code text; BEGIN
 code:=pg_get_functiondef('alpha_research_v3.append(uuid,text,text,text)'::regprocedure);
 IF position('NOT coalesce((c->>''finalization_verified'')::boolean,false)' IN code)=0 THEN RAISE EXCEPTION 'READINESS_PATCH_CONTRACT_DRIFT';END IF;
 code:=replace(code,'NOT coalesce((c->>''finalization_verified'')::boolean,false)',
 '(NOT coalesce((c->>''finalization_verified'')::boolean,false) AND NOT EXISTS(SELECT 1 FROM alpha_operations_v4.readiness rd WHERE rd.contract_id=(b->>''contract_id'')::uuid AND rd.session_date=(b->>''session'')::date AND rd.source_revision=b->>''source_revision'' AND rd.recorded_at<=(b->>''issued_at'')::timestamptz))');
 EXECUTE code;
END $patch$;
-- No invoice invented. Existing paid personal use explicitly authorized by owner
-- is separate from a verified total invoice; no purchases/overage are enabled.
CREATE OR REPLACE FUNCTION alpha_research_v3.authorized(cid uuid) RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,alpha_research_v3,pg_temp AS $$
 SELECT coalesce((c.body->>'paid')::boolean,false) AND c.body->>'scope' IN('LIVE','FIXTURE_ONLY') AND length(coalesce(c.body->>'reviewer_evidence',''))>0 AND c.body->>'operator_class'<>'UNKNOWN'
 AND ((c.body->>'total_monthly_usd')::numeric BETWEEN 0 AND 50 OR (c.body->>'total_monthly_usd' IS NULL AND coalesce((c.body->>'existing_paid_owner_authorized')::boolean,false) AND (c.body->>'authorized_vendor_cap_usd')::numeric BETWEEN 0 AND 50))
 AND greatest((c.body->>'access_until')::timestamptz,coalesce((SELECT max(r.access_until) FROM alpha_operations_v4.renewals r WHERE r.contract_id=c.id),(c.body->>'access_until')::timestamptz))>clock_timestamp()
 AND (c.body->>'raw_until')::timestamptz>clock_timestamp()
 AND coalesce((c.body->>'raw_storage')::boolean,false) AND coalesce((c.body->>'hash_metadata_retention')::boolean,false) AND coalesce((c.body->>'nonreconstructible_forecasts_retention')::boolean,false) AND coalesce((c.body->>'cloud')::boolean,false) AND coalesce((c.body->>'backups')::boolean,false)
 AND NOT coalesce((c.body->>'revoked')::boolean,false) AND NOT EXISTS(SELECT 1 FROM lifecycle l WHERE l.contract_id=c.id AND l.action='OFFBOARD_REQUESTED') FROM contracts c WHERE c.id=cid
$$;
CREATE FUNCTION alpha_operations_v4.receipt(pid uuid,b jsonb) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_operations_v4,pg_temp AS $$ BEGIN
 IF EXISTS(SELECT 1 FROM jsonb_object_keys(b) x WHERE x NOT IN('phase','status','reason','session','issued','blocked','real_forecasts','first_issue_at','schedule','models','checked','pending','revision','source_quality','error_code','subscription_active','report_week')) THEN RAISE EXCEPTION 'SAFE_RECEIPT_FIELDS_ONLY'; END IF;
 INSERT INTO receipts(id,body) VALUES(pid,b);RETURN pid;END $$;
CREATE FUNCTION alpha_operations_v4.report(w date,b jsonb) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_operations_v4,pg_temp AS $$ BEGIN
 INSERT INTO reports(week,body) VALUES(w,b) ON CONFLICT DO NOTHING;END $$;
CREATE FUNCTION alpha_operations_v4.baseline(fid uuid,p double precision,n int,cut timestamptz) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_operations_v4,pg_temp AS $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM alpha_research_v3.forecasts f WHERE f.id=fid AND f.run_mode='RESEARCH_FORECAST' AND cut<=f.issued_at) THEN RAISE EXCEPTION 'PREISSUE_BASELINE_ONLY';END IF;
 INSERT INTO baselines VALUES(fid,p,n,cut) ON CONFLICT DO NOTHING;END $$;
CREATE FUNCTION alpha_operations_v4.renew(cid uuid,expiry timestamptz,evidence text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,alpha_operations_v4,pg_temp AS $$ BEGIN
 IF current_setting('role')<>'alpha_shadow_legal_reviewer' OR expiry>clock_timestamp()+interval '32 days' OR expiry<=clock_timestamp() OR length(evidence)<10 THEN RAISE EXCEPTION 'BOUNDED_REVIEWER_RENEWAL_REQUIRED';END IF;
 INSERT INTO renewals(id,contract_id,access_until,evidence_ref) VALUES(gen_random_uuid(),cid,expiry,evidence);END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA alpha_operations_v4 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA alpha_operations_v4 FROM PUBLIC;
GRANT USAGE ON SCHEMA alpha_operations_v4 TO alpha_shadow_writer,alpha_shadow_reader,alpha_shadow_legal_reviewer;
GRANT SELECT ON ALL TABLES IN SCHEMA alpha_operations_v4 TO alpha_shadow_writer,alpha_shadow_reader;
GRANT EXECUTE ON FUNCTION alpha_operations_v4.ready(uuid,date,text,text,text,timestamptz,timestamptz),alpha_operations_v4.receipt(uuid,jsonb),alpha_operations_v4.report(date,jsonb),alpha_operations_v4.baseline(uuid,double precision,int,timestamptz) TO alpha_shadow_writer;
GRANT EXECUTE ON FUNCTION alpha_operations_v4.renew(uuid,timestamptz,text) TO alpha_shadow_legal_reviewer;
COMMIT;
