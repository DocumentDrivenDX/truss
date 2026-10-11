CREATE FUNCTION truss.runtime_require_catalog_only_business_guards_candidate() RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE name text; rel oid; procedure oid; kind "char";
BEGIN
 procedure:=to_regprocedure('truss.runtime_catalog_only_business_refusal_candidate()');
 IF procedure IS NULL THEN RAISE EXCEPTION 'catalog-only event function missing' USING ERRCODE='55000'; END IF;
 FOREACH name IN ARRAY ARRAY['object','edge','edge_limit','key_tombstone','record_source','feed_consumer','journal','row_home_journal_stage','row_home_state','row_home_node','row_home_scalar','row_home_touch','row_home_capacity','key_bucket_guard','object_key_bucket','object_key_reservation_bucket','complete_feed_consumer','complete_feed_administration_receipt','complete_feed_seed_attempt','complete_feed_seed_artifact','key_lifecycle_history','key_migration_receipt','request_receipt_route_guard','request_receipt','request_receipt_protection','schema_change'] LOOP
  rel:=to_regclass(format('truss.%I',name));
  IF rel IS NULL THEN RAISE EXCEPTION 'catalog-only business relation missing' USING ERRCODE='55000'; END IF;
  EXECUTE format('LOCK TABLE truss.%I IN SHARE MODE NOWAIT',name);
  IF to_regclass(format('truss.%I',name)) IS DISTINCT FROM rel THEN RAISE EXCEPTION 'original business relation changed' USING ERRCODE='55000'; END IF;
  SELECT relkind INTO STRICT kind FROM pg_class WHERE oid=rel AND NOT relrowsecurity;
  IF (name='journal' AND (kind<>'p' OR pg_get_partkeydef(rel) IS DISTINCT FROM 'RANGE (at)'))
   OR (name<>'journal' AND kind<>'r')
   OR EXISTS(SELECT 1 FROM pg_inherits WHERE inhparent=rel OR inhrelid=rel) THEN
   RAISE EXCEPTION 'catalog-only original topology required' USING ERRCODE='55000'; END IF;
  IF (SELECT count(*) FROM pg_trigger WHERE tgrelid=rel AND tgname='a_truss_catalog_only_business_refusal')<>1
   OR NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=rel AND t.tgname='a_truss_catalog_only_business_refusal'
    AND t.tgfoid=procedure AND t.tgtype=62 AND t.tgenabled='A' AND NOT t.tgisinternal
    AND NOT t.tgdeferrable AND NOT t.tginitdeferred AND t.tgnargs=0
    AND t.tgargs=decode('','hex') AND t.tgattr=''::int2vector AND t.tgqual IS NULL
    AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL AND t.tgconstraint=0
    AND t.tgconstrrelid=0 AND t.tgconstrindid=0 AND t.tgparentid=0) THEN
   RAISE EXCEPTION 'exact catalog-only ALWAYS statement guard required' USING ERRCODE='55000'; END IF;
 END LOOP;
 IF (SELECT count(*) FROM pg_trigger t WHERE t.tgfoid=procedure)<>26 THEN
  RAISE EXCEPTION 'complete original catalog-only trigger footprint required' USING ERRCODE='55000'; END IF;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_require_catalog_only_business_guards_candidate() FROM public