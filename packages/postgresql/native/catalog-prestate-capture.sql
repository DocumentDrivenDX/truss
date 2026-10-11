-- Private native catalog start-cut artifact. Encoding/resource/security qualification separate.
CREATE FUNCTION truss.runtime_capture_catalog_prestate() RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE snapshot jsonb; bytes bytea;
BEGIN
 IF to_regclass('truss.catalog_binding_archive') IS NOT NULL THEN
  RAISE EXCEPTION 'catalog binding prestate profile required' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized') THEN
  RAISE EXCEPTION 'catalog prestate must precede original operation admission' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted AND l.relation='truss.schema_head'::regclass AND l.mode IN ('RowShareLock','RowExclusiveLock'))
  AND NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'earlier shared head admission cannot upgrade for catalog prestate' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 snapshot:=jsonb_build_object('interfaceVersion','truss-native-catalog-prestate/0.1',
  'head',(SELECT to_jsonb(h) FROM truss.schema_head h WHERE h.id=1),
  'revisions',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb) FROM truss.schema_rev r),
  'documents',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.rev,d.ord),'[]'::jsonb) FROM truss.schema_doc d),
  'types',(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.type_id),'[]'::jsonb) FROM truss.type_def t),
  'properties',(SELECT coalesce(jsonb_agg(to_jsonb(p) ORDER BY p.prop_id),'[]'::jsonb) FROM truss.prop_def p),
  'keys',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.type_id,k.key_num),'[]'::jsonb) FROM truss.key_def k),
  'keyHistory',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY to_jsonb(k)::text COLLATE "C"),'[]'::jsonb) FROM truss.key_lifecycle_history k),
  'relationships',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rel_type_id),'[]'::jsonb) FROM truss.rel_def r),
  'relationshipLineage',(SELECT coalesce(jsonb_agg(to_jsonb(l) ORDER BY l.rel_type_id),'[]'::jsonb) FROM truss.relationship_lineage l),
  'endpoints',(SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.rel_type_id,e.source_type,e.target_type),'[]'::jsonb) FROM truss.rel_endpoint e),
  'reports',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb) FROM truss.catalog_acceptance_report r));
 IF snapshot->'head' IS NULL OR snapshot->'head'='null'::jsonb THEN RAISE EXCEPTION 'original catalog head required' USING ERRCODE='55000'; END IF;
 bytes:=convert_to(snapshot::text,'UTF8');
 IF octet_length(bytes)>1048576 THEN RAISE EXCEPTION 'catalog prestate component capacity exceeded' USING ERRCODE='54000'; END IF;
 RETURN encode(bytes,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_catalog_prestate() FROM PUBLIC;
