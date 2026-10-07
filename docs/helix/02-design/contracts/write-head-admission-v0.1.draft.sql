-- CONTRACT-001/005/011 candidate PostgreSQL 17; unapplied/unqualified.
-- Role owner/EXECUTE whitelist and complete native callable inventory required.
-- Deployment schema is qualified from its admitted identifier; truss is draft default.
CREATE FUNCTION truss.acquire_write_head_v01()
RETURNS TABLE (catalog_revision text, configuration_generation text, acting_role text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $body$
BEGIN
  IF pg_catalog.current_setting('transaction_read_only') = 'on' THEN
    RAISE EXCEPTION 'write admission requires read/write scope' USING ERRCODE = '25006';
  END IF;
  acting_role := CASE WHEN pg_catalog.current_setting('role') = 'none'
    THEN session_user::text ELSE pg_catalog.current_setting('role') END;
  SELECT h.rev::text INTO catalog_revision
    FROM truss.schema_head AS h WHERE h.id = 1 FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'missing original admission head' USING ERRCODE = '55000';
  END IF;
  SELECT a.configuration_generation::text INTO configuration_generation
    FROM truss.installation_admission AS a WHERE a.head_id = 1;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'missing installed admission state' USING ERRCODE = '55000';
  END IF;
  RETURN NEXT;
END;
$body$;
REVOKE ALL ON FUNCTION truss.acquire_write_head_v01() FROM PUBLIC;
-- No GRANT here: whitelist actual qualified ordinary writer roles only after
-- exact owner/role closure/search-path/dependency verification. Never grant them
-- head UPDATE merely to enable locking. Callable does not change state or
-- prove current policy/full configuration/binding/installed-inventory admission.
