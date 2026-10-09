-- Private empty-provisional inventory proof. Nonempty inventory needs its full producer.
CREATE FUNCTION truss.runtime_require_empty_provisional_catalog(original_revision int)
RETURNS text LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 -- Require the original unfinished catalog operation, exact source carrier and head exclusion.
 PERFORM * FROM truss.runtime_collect_report_documents(original_revision);
 -- Include retained rows too. No new-only or role-filtered subset can prove global emptiness.
 IF EXISTS(SELECT 1 FROM truss.type_def t WHERE t.provisional) THEN
  RAISE EXCEPTION 'complete nonempty provisional report producer required' USING ERRCODE='0A000';
 END IF;
 RETURN '0'::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_require_empty_provisional_catalog(int) FROM PUBLIC;
