-- CONTRACT-003 candidate; unapplied and unqualified.
-- Original protected acceptance must already hold exclusive head and complete
-- integrity visibility. SELECT-only observer owner and exact internal grants
-- are installation prerequisites; PUBLIC revoke is not a complete installation.
-- No lifecycle filter: active, provisional and retired retained rows contribute.
CREATE FUNCTION truss.catalog_global_high_water_v01()
RETURNS TABLE (allocation_domain text, maximum_id text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path = pg_catalog, pg_temp
AS $body$
BEGIN
  RETURN QUERY
  SELECT 'type_id'::text, GREATEST(COALESCE(MAX(t.type_id)::bigint, 0), 0)::text
  FROM truss.type_def AS t
  UNION ALL
  SELECT 'prop_id'::text, GREATEST(COALESCE(MAX(p.prop_id)::bigint, 0), 0)::text
  FROM truss.prop_def AS p
  UNION ALL
  SELECT 'rel_type_id'::text, GREATEST(COALESCE(MAX(r.rel_type_id)::bigint, 0), 0)::text
  FROM truss.rel_def AS r;
END
$body$;
REVOKE ALL ON FUNCTION truss.catalog_global_high_water_v01() FROM PUBLIC;

CREATE FUNCTION truss.catalog_key_high_water_v01(original_type_id int)
RETURNS TABLE (owner_type_id text, maximum_key_num text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path = pg_catalog, pg_temp
AS $body$
DECLARE
  retained_type_id int;
BEGIN
  IF original_type_id IS NULL THEN
    RAISE EXCEPTION 'missing original key owner' USING ERRCODE = '22023';
  END IF;
  SELECT t.type_id INTO STRICT retained_type_id
  FROM truss.type_def AS t WHERE t.type_id = original_type_id;
  RETURN QUERY
  SELECT retained_type_id::text,
         GREATEST(COALESCE(MAX(k.key_num)::bigint, 0), 0)::text
  FROM truss.key_def AS k WHERE k.type_id = retained_type_id;
END
$body$;
REVOKE ALL ON FUNCTION truss.catalog_key_high_water_v01(int) FROM PUBLIC;
-- A wholly new private type has no persisted original owner yet. Its key floor
-- is derived as zero only after complete original identity/owner matching.
-- These observations do not allocate IDs, prove provenance or hidden-row
-- visibility, lock the head, enforce budgets, finalize or commit acceptance.
