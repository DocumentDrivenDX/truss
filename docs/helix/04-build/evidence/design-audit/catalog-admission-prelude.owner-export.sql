CREATE FUNCTION truss.acquire_catalog_shared_prelude_v01() RETURNS TABLE (admission_mode text, native_advisory_identity text) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL unsafe SET search_path TO pg_catalog, pg_temp AS $$
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
$$; REVOKE ALL ON FUNCTION truss.acquire_catalog_shared_prelude_v01() FROM public; CREATE FUNCTION truss.acquire_catalog_exclusive_prelude_v01() RETURNS TABLE (admission_mode text, native_advisory_identity text) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL unsafe SET search_path TO pg_catalog, pg_temp AS $$
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
$$; REVOKE ALL ON FUNCTION truss.acquire_catalog_exclusive_prelude_v01() FROM public