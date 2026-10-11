-- Private new-only retained-state parity. Full lifecycle/report qualification separate.
CREATE FUNCTION truss.runtime_verify_new_catalog_prestate(original_revision int) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; original jsonb; actual jsonb; profile text; retained_bindings jsonb;
BEGIN
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' OR original_revision IS NULL OR original_revision<=0
  OR octet_length(op.original_prestate_bytes)>1048576 THEN RAISE EXCEPTION 'original bounded catalog prestate required' USING ERRCODE='55000'; END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 original:=convert_from(op.original_prestate_bytes,'UTF8')::jsonb;
 profile:=original->>'interfaceVersion';
 IF profile NOT IN ('truss-native-catalog-prestate/0.1','truss-native-catalog-prestate/0.2-binding-custody') OR profile IS NULL THEN
  RAISE EXCEPTION 'original prestate format unavailable' USING ERRCODE='0A000';
 END IF;
 IF (profile='truss-native-catalog-prestate/0.1' AND to_regclass('truss.catalog_binding_archive') IS NOT NULL)
  OR (profile='truss-native-catalog-prestate/0.2-binding-custody' AND to_regclass('truss.catalog_binding_archive') IS NULL) THEN
  RAISE EXCEPTION 'original prestate archive profile correspondence required' USING ERRCODE='55000';
 END IF;
 actual:=jsonb_build_object('interfaceVersion',profile,
  'head',(SELECT to_jsonb(h) FROM truss.schema_head h WHERE h.id=1),
  'revisions',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb) FROM truss.schema_rev r WHERE r.rev<>original_revision),
  'documents',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.rev,d.ord),'[]'::jsonb) FROM truss.schema_doc d WHERE d.rev<>original_revision),
  'types',(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.type_id),'[]'::jsonb) FROM truss.type_def t WHERE t.since_rev<>original_revision),
  'properties',(SELECT coalesce(jsonb_agg(to_jsonb(p) ORDER BY p.prop_id),'[]'::jsonb) FROM truss.prop_def p WHERE p.since_rev<>original_revision),
  'keys',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.type_id,k.key_num),'[]'::jsonb) FROM truss.key_def k WHERE k.since_rev<>original_revision),
  'keyHistory',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY to_jsonb(k)::text COLLATE "C"),'[]'::jsonb) FROM truss.key_lifecycle_history k),
  'relationships',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rel_type_id),'[]'::jsonb) FROM truss.rel_def r WHERE r.since_rev<>original_revision),
  'relationshipLineage',(SELECT coalesce(jsonb_agg(to_jsonb(l) ORDER BY l.rel_type_id),'[]'::jsonb) FROM truss.relationship_lineage l JOIN truss.rel_def r ON r.rel_type_id=l.rel_type_id WHERE r.since_rev<>original_revision),
  'endpoints',(SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.rel_type_id,e.source_type,e.target_type),'[]'::jsonb) FROM truss.rel_endpoint e JOIN truss.rel_def r ON r.rel_type_id=e.rel_type_id WHERE r.since_rev<>original_revision),
  'reports',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb) FROM truss.catalog_acceptance_report r));
 IF profile='truss-native-catalog-prestate/0.2-binding-custody' THEN
  EXECUTE 'SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.revision),''[]''::jsonb) FROM truss.catalog_binding_archive a WHERE a.revision<>$1'
   INTO retained_bindings USING original_revision;
  actual:=actual||jsonb_build_object('bindings',retained_bindings);
 END IF;
 IF actual IS DISTINCT FROM original THEN
  RAISE EXCEPTION 'retained catalog differs from original new-only prestate' USING ERRCODE='55000';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_verify_new_catalog_prestate(int) FROM PUBLIC;
