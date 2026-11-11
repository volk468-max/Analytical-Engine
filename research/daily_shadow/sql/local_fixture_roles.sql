-- Disposable local/CI fixture ONLY. These are explicitly synthetic credentials.
DO $$ BEGIN
 IF current_database()<>'alpha_shadow_research' THEN RAISE EXCEPTION 'Disposable DB required'; END IF;
END $$;
CREATE ROLE alpha_shadow_test_app LOGIN PASSWORD 'synthetic-local-only' NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT alpha_shadow_writer TO alpha_shadow_test_app;
