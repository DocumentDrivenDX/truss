-- Private provisional byte custody. No vocabulary interpretation or acceptance publication.
CREATE TABLE truss.catalog_binding_archive (
 revision int PRIMARY KEY REFERENCES truss.schema_rev(rev),
 vocabulary jsonb NOT NULL CHECK(jsonb_typeof(vocabulary)='object'),
 artifact_identity_utf8 bytea NOT NULL CHECK(octet_length(artifact_identity_utf8) BETWEEN 1 AND 4096),
 original_binding_bytes bytea NOT NULL CHECK(octet_length(original_binding_bytes) BETWEEN 1 AND 1048576),
 original_input_bytes bytea NOT NULL CHECK(octet_length(original_input_bytes) BETWEEN 1 AND 1048576),
 original_writer_xid xid8 NOT NULL,
 binding_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_binding_bytes)) STORED
);
REVOKE ALL ON truss.catalog_binding_archive FROM PUBLIC;
CREATE FUNCTION truss.runtime_capture_binding_catalog_prestate() RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE snapshot jsonb; bytes bytea;
BEGIN
 IF EXISTS(SELECT 1 FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized') THEN
  RAISE EXCEPTION 'catalog prestate must precede original operation admission' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted AND l.relation='truss.schema_head'::regclass AND l.mode IN ('RowShareLock','RowExclusiveLock'))
  AND NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'earlier shared head admission cannot upgrade for catalog prestate' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 snapshot:=jsonb_build_object('interfaceVersion','truss-native-catalog-prestate/0.2-binding-custody',
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
  'reports',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb) FROM truss.catalog_acceptance_report r),
  'bindings',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.revision),'[]'::jsonb) FROM truss.catalog_binding_archive a));
 IF snapshot->'head' IS NULL OR snapshot->'head'='null'::jsonb THEN RAISE EXCEPTION 'original catalog head required' USING ERRCODE='55000'; END IF;
 bytes:=convert_to(snapshot::text,'UTF8');
 IF octet_length(bytes)>1048576 THEN RAISE EXCEPTION 'catalog prestate component capacity exceeded' USING ERRCODE='54000'; END IF;
 RETURN encode(bytes,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_binding_catalog_prestate() FROM PUBLIC;
CREATE FUNCTION truss.runtime_stage_catalog_binding(revision int,original_binding bytea)
RETURNS text LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; input jsonb; binding jsonb; artifact jsonb;
 vocabulary jsonb; decoded bytea; prestate jsonb; item record; archived truss.schema_doc%ROWTYPE;
BEGIN
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' OR revision IS NULL OR original_binding IS NULL
  OR octet_length(original_binding) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'original catalog binding operation required' USING ERRCODE='22023';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
  AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'original catalog binding exclusion required' USING ERRCODE='55000';
 END IF;
 prestate:=convert_from(op.original_prestate_bytes,'UTF8')::jsonb;
 IF prestate->>'interfaceVersion' IS DISTINCT FROM 'truss-native-catalog-prestate/0.2-binding-custody'
  OR jsonb_typeof(prestate->'revisions') IS DISTINCT FROM 'array' OR jsonb_typeof(prestate->'bindings') IS DISTINCT FROM 'array'
  OR (SELECT to_jsonb(h) FROM truss.schema_head h WHERE h.id=1) IS DISTINCT FROM prestate->'head'
  OR NOT EXISTS(SELECT 1 FROM truss.schema_rev r WHERE r.rev=runtime_stage_catalog_binding.revision AND r.rev>(prestate->'head'->>'rev')::int)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(prestate->'revisions') r WHERE (r.value->>'rev')::int=runtime_stage_catalog_binding.revision)
  OR (SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb) FROM truss.schema_rev r WHERE r.rev<>runtime_stage_catalog_binding.revision) IS DISTINCT FROM prestate->'revisions'
  OR (SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.revision),'[]'::jsonb) FROM truss.catalog_binding_archive a WHERE a.revision<>runtime_stage_catalog_binding.revision) IS DISTINCT FROM prestate->'bindings' THEN
  RAISE EXCEPTION 'current unpublished catalog revision and original binding prestate required' USING ERRCODE='55000';
 END IF;
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 binding:=input->'binding';artifact:=binding->'artifact';vocabulary:=binding->'vocabulary';
 IF input->>'interfaceVersion' IS DISTINCT FROM 'truss-acceptance-input/0.1.0'
  OR jsonb_typeof(binding) IS DISTINCT FROM 'object' OR binding->>'state' IS DISTINCT FROM 'present'
  OR NOT binding ?& ARRAY['state','vocabulary','artifact'] OR (SELECT count(*) FROM jsonb_object_keys(binding))<>3
  OR jsonb_typeof(artifact) IS DISTINCT FROM 'object' OR NOT artifact ?& ARRAY['identity','bytesBase64','sha256']
  OR (SELECT count(*) FROM jsonb_object_keys(artifact))<>3
  OR jsonb_typeof(vocabulary) IS DISTINCT FROM 'object' OR NOT vocabulary ?& ARRAY['identity','version','sha256']
  OR (SELECT count(*) FROM jsonb_object_keys(vocabulary))<>3 THEN
  RAISE EXCEPTION 'original present binding carrier required' USING ERRCODE='22023';
 END IF;
 IF EXISTS(SELECT 1 FROM jsonb_each(artifact) e WHERE jsonb_typeof(e.value)<>'string')
  OR EXISTS(SELECT 1 FROM jsonb_each(vocabulary) e WHERE jsonb_typeof(e.value)<>'string')
  OR octet_length(artifact->>'identity') NOT BETWEEN 1 AND 4096
  OR octet_length(vocabulary->>'identity') NOT BETWEEN 1 AND 4096
  OR octet_length(vocabulary->>'version') NOT BETWEEN 1 AND 4096
  OR artifact->>'sha256' !~ '^[0-9a-f]{64}$' OR vocabulary->>'sha256' !~ '^[0-9a-f]{64}$'
  OR octet_length(artifact->>'bytesBase64') NOT BETWEEN 4 AND 1398104
  OR artifact->>'bytesBase64' !~ '^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$' THEN
  RAISE EXCEPTION 'bounded original binding artifact required' USING ERRCODE='22023';
 END IF;
 decoded:=decode(artifact->>'bytesBase64','base64');
 IF replace(encode(decoded,'base64'),chr(10),'') IS DISTINCT FROM artifact->>'bytesBase64'
  OR octet_length(decoded) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'canonical original binding encoding required' USING ERRCODE='22023';
 END IF;
 IF decoded IS DISTINCT FROM original_binding OR artifact->>'sha256' IS DISTINCT FROM encode(sha256(decoded),'hex') THEN
  RAISE EXCEPTION 'original admitted binding bytes required' USING ERRCODE='55000';
 END IF;
 -- Match the complete original document cohort, without rewriting its source.
 IF jsonb_typeof(input->'documents') IS DISTINCT FROM 'array' OR jsonb_array_length(input->'documents') NOT BETWEEN 1 AND 512
  OR (SELECT count(*) FROM truss.schema_doc d WHERE d.rev=runtime_stage_catalog_binding.revision)<>jsonb_array_length(input->'documents') THEN
  RAISE EXCEPTION 'complete original binding document cohort required' USING ERRCODE='55000';
 END IF;
 FOR item IN SELECT value,ordinality FROM jsonb_array_elements(input->'documents') WITH ORDINALITY LOOP
  SELECT d.* INTO archived FROM truss.schema_doc d WHERE d.rev=runtime_stage_catalog_binding.revision AND d.ord=item.ordinality::int-1;
  IF NOT FOUND OR archived.doc_id IS DISTINCT FROM item.value->>'documentId'
   OR archived.doc_revision IS DISTINCT FROM item.value->>'documentRevision'
   OR convert_to(archived.document,'UTF8') IS DISTINCT FROM decode(item.value->'artifact'->>'bytesBase64','base64')
   OR archived.content_sha256 IS DISTINCT FROM item.value->'artifact'->>'sha256'
   OR archived.content_sha256 IS DISTINCT FROM encode(sha256(convert_to(archived.document,'UTF8')),'hex') THEN
   RAISE EXCEPTION 'original binding document correspondence required' USING ERRCODE='55000';
  END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM truss.catalog_binding_archive a WHERE a.revision=runtime_stage_catalog_binding.revision) THEN
  RAISE EXCEPTION 'original binding archive already staged' USING ERRCODE='55000';
 END IF;
 INSERT INTO truss.catalog_binding_archive(revision,vocabulary,artifact_identity_utf8,original_binding_bytes,original_input_bytes,original_writer_xid)
 VALUES(runtime_stage_catalog_binding.revision,vocabulary,convert_to(artifact->>'identity','UTF8'),decoded,op.original_input_bytes,op.original_writer_xid);
 RETURN encode(sha256(decoded),'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_binding(int,bytea) FROM PUBLIC;
CREATE FUNCTION truss.runtime_refuse_binding_archive_change() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RAISE EXCEPTION 'original binding archive is immutable; retention profile required' USING ERRCODE='55000';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_refuse_binding_archive_change() FROM PUBLIC;
CREATE TRIGGER runtime_binding_archive_immutable BEFORE UPDATE OR DELETE ON truss.catalog_binding_archive
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_refuse_binding_archive_change();
ALTER TABLE truss.catalog_binding_archive ENABLE ALWAYS TRIGGER runtime_binding_archive_immutable;
CREATE TRIGGER runtime_binding_archive_no_truncate BEFORE TRUNCATE ON truss.catalog_binding_archive
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_refuse_binding_archive_change();
ALTER TABLE truss.catalog_binding_archive ENABLE ALWAYS TRIGGER runtime_binding_archive_no_truncate;
CREATE TRIGGER runtime_catalog_generation AFTER INSERT ON truss.catalog_binding_archive
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_catalog_generation();
ALTER TABLE truss.catalog_binding_archive ENABLE ALWAYS TRIGGER runtime_catalog_generation;
