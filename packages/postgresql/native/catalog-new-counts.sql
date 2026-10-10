-- Private new-only report count basis. No complete report/public acceptance authority.
CREATE FUNCTION truss.runtime_collect_new_catalog_counts(original_revision int)
RETURNS TABLE(types_added text,properties_added text,keys_added text,relationships_added text,endpoints_added text,elements_retired text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 -- The collector verifies complete original source, actual definitions/endpoints and
 -- unchanged retained prestate, and refuses retirement/reactivation/edit profiles.
 RETURN QUERY SELECT
  (count(*) FILTER (WHERE i.family='type'))::text,
  (count(*) FILTER (WHERE i.family='property'))::text,
  (count(*) FILTER (WHERE i.family='key'))::text,
  (count(*) FILTER (WHERE i.family='relationship'))::text,
  (count(*) FILTER (WHERE i.family='endpoint'))::text,
  '0'::text
 FROM truss.runtime_collect_new_catalog_inventory(original_revision) i;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_new_catalog_counts(int) FROM PUBLIC;
