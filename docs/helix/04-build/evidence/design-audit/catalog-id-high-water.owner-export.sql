CREATE FUNCTION truss.catalog_global_high_water_v01() RETURNS TABLE (allocation_domain text, maximum_id text) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL unsafe SET search_path TO pg_catalog, pg_temp AS $$
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
$$; REVOKE ALL ON FUNCTION truss.catalog_global_high_water_v01() FROM public; CREATE FUNCTION truss.catalog_key_high_water_v01(original_type_id int) RETURNS TABLE (owner_type_id text, maximum_key_num text) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL unsafe SET search_path TO pg_catalog, pg_temp AS $$
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
$$; REVOKE ALL ON FUNCTION truss.catalog_key_high_water_v01(int) FROM public