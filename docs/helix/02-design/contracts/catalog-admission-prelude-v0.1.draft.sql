-- CONTRACT-003/TD-013 optional native prelude candidate; unapplied/unqualified.
-- No owner assignment/GRANT; exact original host/executor admission is required.
-- These helpers do not detect original session holds, prior locks or upgrades.
CREATE FUNCTION truss.acquire_catalog_shared_prelude_v01()
RETURNS TABLE (admission_mode text, native_advisory_identity text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path = pg_catalog, pg_temp
AS $body$
DECLARE
  original_key bigint;
BEGIN
  IF pg_catalog.current_setting('transaction_read_only') = 'on' THEN
    RAISE EXCEPTION 'catalog prelude requires read/write scope' USING ERRCODE = '25006';
  END IF;
  original_key := pg_catalog.hashtextextended('truss.catalog'::text, 0::bigint);
  PERFORM pg_catalog.pg_advisory_xact_lock_shared(original_key);
  RETURN QUERY SELECT 'shared'::text, original_key::text;
END;
$body$;
REVOKE ALL ON FUNCTION truss.acquire_catalog_shared_prelude_v01() FROM PUBLIC;

CREATE FUNCTION truss.acquire_catalog_exclusive_prelude_v01()
RETURNS TABLE (admission_mode text, native_advisory_identity text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path = pg_catalog, pg_temp
AS $body$
DECLARE
  original_key bigint;
BEGIN
  IF pg_catalog.current_setting('transaction_read_only') = 'on' THEN
    RAISE EXCEPTION 'catalog prelude requires read/write scope' USING ERRCODE = '25006';
  END IF;
  original_key := pg_catalog.hashtextextended('truss.catalog'::text, 0::bigint);
  PERFORM pg_catalog.pg_advisory_xact_lock(original_key);
  RETURN QUERY SELECT 'exclusive'::text, original_key::text;
END;
$body$;
REVOKE ALL ON FUNCTION truss.acquire_catalog_exclusive_prelude_v01() FROM PUBLIC;

-- Returned identity is exact native bigint text, not an ownership certificate.
-- Native timeout/statement settings remain original host-owned selected policy.
-- Retain mandatory original head/policy admission after this prelude.
-- No session lock/unlock, transaction control, timer reset or custom key input.
