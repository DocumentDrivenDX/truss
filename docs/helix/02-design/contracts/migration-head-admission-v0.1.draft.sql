-- CONTRACT-001/005 candidate truss-migration-head-exclusion/0.1.0.
-- Unapplied/unqualified: exact internal migration owner/EXECUTE closure required.
-- Caller supplies original owned native READ COMMITTED read/write transaction.
CREATE FUNCTION truss.acquire_migration_head_v01()
RETURNS TABLE (catalog_revision text, configuration_generation text, acting_role text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path = pg_catalog, pg_temp
AS $body$
BEGIN
  IF pg_catalog.current_setting('transaction_read_only') = 'on' THEN
    RAISE EXCEPTION 'migration admission requires read/write scope' USING ERRCODE = '25006';
  END IF;
  IF pg_catalog.current_setting('transaction_isolation') <> 'read committed' THEN
    RAISE EXCEPTION 'unsupported migration isolation' USING ERRCODE = '55000';
  END IF;
  acting_role := CASE WHEN pg_catalog.current_setting('role') = 'none'
    THEN session_user::text ELSE pg_catalog.current_setting('role') END;
  SELECT h.rev::text INTO catalog_revision
    FROM truss.schema_head AS h WHERE h.id = 1 FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'missing original migration head' USING ERRCODE = '55000';
  END IF;
  SELECT a.configuration_generation::text INTO configuration_generation
    FROM truss.installation_admission AS a WHERE a.head_id = 1;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'missing installed migration admission' USING ERRCODE = '55000';
  END IF;
  RETURN NEXT;
END;
$body$;
REVOKE ALL ON FUNCTION truss.acquire_migration_head_v01() FROM PUBLIC;
-- No public/ordinary GRANT, transaction mode change, COMMIT or binding switch.
-- Native original custody/initial admin admission must precede invocation;
-- full fresh binding/policy/disclosure admission follows under retained head.
