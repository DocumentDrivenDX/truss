-- Internal already-resolved authored relationship persistence, not public acceptance.
-- Candidate lineage is derived from the archived original authored declaration.
CREATE FUNCTION truss.runtime_stage_new_relationship(revision int,document_id text,module_id text,
  relationship jsonb,source_ids int[],target_ids int[])
RETURNS text LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  op truss.row_home_operation%ROWTYPE;
  doc_ordinal int;
  assigned bigint;
  endpoint int;
  bound jsonb;
  target_key text;
  original_document jsonb;
  original_endpoint jsonb;
  endpoint_ordinal int;
  identity_profile constant text := 'truss-relationship-lineage-bytes/0.1.0';
  identity_bytes bytea;
  matched record;
BEGIN
  SELECT * INTO STRICT op FROM truss.row_home_operation o
    WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' OR revision IS NULL
      OR document_id IS NULL OR octet_length(document_id) NOT BETWEEN 1 AND 4096
      OR module_id IS NULL OR octet_length(module_id) NOT BETWEEN 1 AND 4096
      OR relationship IS NULL OR jsonb_typeof(relationship)<>'object'
      OR octet_length(relationship::text)>1048576 THEN
    RAISE EXCEPTION 'original relationship admission required' USING ERRCODE='22023';
  END IF;
  IF NOT relationship ?& ARRAY['id','name','source','target','sourceMultiplicity','targetMultiplicity','targetLifecycle','directed']
      OR EXISTS(SELECT 1 FROM jsonb_object_keys(relationship) k WHERE k NOT IN
        ('id','name','source','target','sourceMultiplicity','targetMultiplicity','targetLifecycle','directed','extensions'))
      OR EXISTS(SELECT 1 FROM jsonb_each(relationship) e WHERE e.key IN ('id','name','targetLifecycle')
        AND (jsonb_typeof(e.value)<>'string' OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096))
      OR jsonb_typeof(relationship->'directed')<>'boolean'
      OR jsonb_typeof(relationship->'source')<>'array' OR jsonb_typeof(relationship->'target')<>'array' THEN
    RAISE EXCEPTION 'unsupported or invalid original relationship carrier' USING ERRCODE='22023';
  END IF;
  FOREACH bound IN ARRAY ARRAY[relationship->'sourceMultiplicity',relationship->'targetMultiplicity'] LOOP
    IF jsonb_typeof(bound)<>'object' OR NOT bound ?& ARRAY['min','max']
        OR (SELECT count(*) FROM jsonb_object_keys(bound))<>2
        OR jsonb_typeof(bound->'min')<>'number'
        OR jsonb_typeof(bound->'max') NOT IN ('number','string')
        OR NOT (jsonb_typeof(bound->'max')='number' OR bound->>'max'='*')
        OR bound->>'min' !~ '^(0|[1-9][0-9]{0,9})$'
        OR bound->>'max' !~ '^(\*|0|[1-9][0-9]{0,9})$' THEN
      RAISE EXCEPTION 'original relationship multiplicity carrier' USING ERRCODE='22023';
    END IF;
    IF (bound->>'min')::bigint>2147483647 OR
        (bound->>'max'<>'*' AND ((bound->>'max')::bigint>2147483647 OR (bound->>'max')::bigint<(bound->>'min')::bigint)) THEN
      RAISE EXCEPTION 'original relationship multiplicity capacity' USING ERRCODE='22023';
    END IF;
  END LOOP;
  IF source_ids IS NULL OR target_ids IS NULL
      OR cardinality(source_ids) NOT BETWEEN 1 AND 256 OR cardinality(target_ids) NOT BETWEEN 1 AND 256
      OR array_ndims(source_ids)<>1 OR array_ndims(target_ids)<>1
      OR array_lower(source_ids,1)<>1 OR array_lower(target_ids,1)<>1
      OR array_position(source_ids,NULL) IS NOT NULL OR array_position(target_ids,NULL) IS NOT NULL
      OR cardinality(source_ids)<>jsonb_array_length(relationship->'source')
      OR cardinality(target_ids)<>jsonb_array_length(relationship->'target') THEN
    RAISE EXCEPTION 'complete original endpoint correspondence required' USING ERRCODE='22023';
  END IF;
  IF (SELECT count(DISTINCT p) FROM unnest(source_ids) p)<>cardinality(source_ids)
      OR (SELECT count(DISTINCT p) FROM unnest(target_ids) p)<>cardinality(target_ids) THEN
    RAISE EXCEPTION 'duplicate resolved endpoint' USING ERRCODE='22023';
  END IF;
  LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
  SELECT d.ord INTO STRICT doc_ordinal FROM truss.schema_doc d WHERE d.rev=revision AND d.doc_id=runtime_stage_new_relationship.document_id;
  SELECT d.document::jsonb INTO STRICT original_document FROM truss.schema_doc d
    WHERE d.rev=revision AND d.ord=doc_ordinal;
  IF (SELECT count(*) FROM jsonb_array_elements(original_document->'modules') m
      CROSS JOIN LATERAL jsonb_array_elements(m.value->'relationships') r
      WHERE m.value->>'id'=module_id AND r.value=relationship)<>1 THEN
    RAISE EXCEPTION 'relationship does not match original declaring module source' USING ERRCODE='55000';
  END IF;
  identity_bytes:=truss.runtime_catalog_lineage(revision,'authored',document_id,module_id,relationship->>'id');
  -- This JSON-source profile resolves UMF module/element references inside their
  -- original document. Cross-document resolution requires an explicit later profile.
  FOR endpoint_ordinal IN 1..cardinality(source_ids) LOOP
    original_endpoint:=relationship->'source'->(endpoint_ordinal-1);
    PERFORM 1 FROM truss.type_def t WHERE t.type_id=source_ids[endpoint_ordinal]
      AND t.document_id=runtime_stage_new_relationship.document_id
      AND t.module=original_endpoint->>'module' AND t.element=original_endpoint->>'element';
    IF NOT FOUND THEN RAISE EXCEPTION 'original source endpoint correspondence' USING ERRCODE='55000'; END IF;
    PERFORM 1 FROM truss.key_def k WHERE k.type_id=source_ids[endpoint_ordinal] AND k.retired_rev IS NULL;
    IF NOT FOUND THEN RAISE EXCEPTION 'original source endpoint key required' USING ERRCODE='55000'; END IF;
  END LOOP;
  FOR endpoint_ordinal IN 1..cardinality(target_ids) LOOP
    original_endpoint:=relationship->'target'->(endpoint_ordinal-1);
    PERFORM 1 FROM truss.type_def t WHERE t.type_id=target_ids[endpoint_ordinal]
      AND t.document_id=runtime_stage_new_relationship.document_id
      AND t.module=original_endpoint->>'module' AND t.element=original_endpoint->>'element';
    IF NOT FOUND THEN RAISE EXCEPTION 'original target endpoint correspondence' USING ERRCODE='55000'; END IF;
  END LOOP;
  SELECT * INTO STRICT matched FROM truss.runtime_match_relationship_identity(revision,document_id,module_id,relationship->>'id');
  IF matched.match_state<>'new'
      OR EXISTS(SELECT 1 FROM truss.relationship_lineage l WHERE l.identity_profile='truss-relationship-lineage-bytes/0.1.0' AND l.original_identity_bytes=identity_bytes) THEN
    RAISE EXCEPTION 'existing relationship requires original matching' USING ERRCODE='55000';
  END IF;
  FOREACH endpoint IN ARRAY source_ids || target_ids LOOP
    PERFORM 1 FROM truss.type_def t WHERE t.type_id=endpoint AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL;
    IF NOT FOUND THEN RAISE EXCEPTION 'missing active original endpoint' USING ERRCODE='55000'; END IF;
  END LOOP;
  -- Baseline storage has one target-key column; heterogeneous authored keys refuse.
  IF (SELECT count(DISTINCT coalesce(value->>'key','')) FROM jsonb_array_elements(relationship->'target'))>1 THEN
    RAISE EXCEPTION 'heterogeneous target keys require another admitted storage profile' USING ERRCODE='0A000';
  END IF;
  target_key:=relationship->'target'->0->>'key';
  IF target_key IS NOT NULL THEN
    FOREACH endpoint IN ARRAY target_ids LOOP
      PERFORM 1 FROM truss.key_def k WHERE k.type_id=endpoint AND k.key_id=target_key AND k.retired_rev IS NULL;
      IF NOT FOUND THEN RAISE EXCEPTION 'missing active target key' USING ERRCODE='55000'; END IF;
    END LOOP;
  END IF;
  SELECT greatest(coalesce(max(r.rel_type_id)::bigint,0),0)+1 INTO assigned FROM truss.rel_def r;
  IF assigned>2147483647 THEN RAISE EXCEPTION 'relationship capacity exhausted' USING ERRCODE='54000'; END IF;
  INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,source_max,target_min,target_max,
    lifecycle,directed,target_key,composition,since_rev,doc_ord,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id)
  VALUES(document_id,assigned::int,module_id,relationship->>'id',relationship->>'name',
    (relationship->'sourceMultiplicity'->>'min')::int,nullif(relationship->'sourceMultiplicity'->>'max','*')::int,
    (relationship->'targetMultiplicity'->>'min')::int,nullif(relationship->'targetMultiplicity'->>'max','*')::int,
    relationship->>'targetLifecycle',(relationship->>'directed')::boolean,target_key,false,revision,doc_ordinal,
    'accepted_document',revision,doc_ordinal,document_id);
  INSERT INTO truss.relationship_lineage(rel_type_id,lineage_category,identity_profile,original_identity_bytes)
    VALUES(assigned::int,'authored',identity_profile,identity_bytes);
  INSERT INTO truss.rel_endpoint(rel_type_id,source_type,target_type)
    SELECT assigned::int,s,t FROM unnest(source_ids) s CROSS JOIN unnest(target_ids) t;
  RETURN assigned::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_new_relationship(int,text,text,jsonb,int[],int[]) FROM PUBLIC;
