-- Original already-interpreted genuinely-new property batch. Not public acceptance.
CREATE FUNCTION truss.runtime_stage_new_properties(revision int,candidates jsonb)
RETURNS TABLE(owner_type_id text,field_id text,property_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  op truss.row_home_operation%ROWTYPE;
  candidate jsonb;
  owner truss.type_def%ROWTYPE;
  high_water bigint;
  assigned bigint;
  total_new bigint;
BEGIN
  SELECT * INTO STRICT op FROM truss.row_home_operation o
    WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' OR revision IS NULL
      OR candidates IS NULL OR jsonb_typeof(candidates)<>'array'
      OR jsonb_array_length(candidates) NOT BETWEEN 1 AND 4096 OR octet_length(candidates::text)>1048576 THEN
    RAISE EXCEPTION 'original property batch admission required' USING ERRCODE='22023';
  END IF;
  LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
  FOR candidate IN SELECT value FROM jsonb_array_elements(candidates) LOOP
    IF jsonb_typeof(candidate)<>'object' OR NOT candidate ?& ARRAY['ownerTypeId','field','home']
        OR (SELECT count(*) FROM jsonb_object_keys(candidate))<>3
        OR jsonb_typeof(candidate->'ownerTypeId')<>'string'
        OR candidate->>'ownerTypeId' !~ '^[1-9][0-9]{0,9}$'
        OR (candidate->>'ownerTypeId')::bigint>2147483647
        OR candidate->>'home' NOT IN ('json','row') OR candidate->>'home' IS NULL
        OR jsonb_typeof(candidate->'field')<>'object' THEN
      RAISE EXCEPTION 'original property candidate shape' USING ERRCODE='22023';
    END IF;
    IF NOT (candidate->'field') ?& ARRAY['id','name','kind','nullability','cardinality']
        OR candidate->'field'->>'kind'<>'field'
        OR EXISTS(SELECT 1 FROM jsonb_each(candidate->'field') e WHERE e.key IN ('id','name','kind','nullability','cardinality','scalarType') AND (jsonb_typeof(e.value)<>'string' OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096)) THEN
      RAISE EXCEPTION 'original field carrier' USING ERRCODE='22023';
    END IF;
    SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=(candidate->>'ownerTypeId')::int;
    IF owner.since_rev<>revision OR owner.retired_rev IS NOT NULL OR owner.doc_ord IS NULL THEN
      RAISE EXCEPTION 'new property owner correspondence required' USING ERRCODE='55000';
    END IF;
    IF EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.type_id=owner.type_id AND
      (p.element=candidate->'field'->>'id' OR p.name=candidate->'field'->>'name')) THEN
      RAISE EXCEPTION 'existing property requires original matching' USING ERRCODE='55000';
    END IF;
  END LOOP;
  SELECT count(*) INTO total_new FROM (SELECT DISTINCT value->>'ownerTypeId',value->'field'->>'id' FROM jsonb_array_elements(candidates)) q;
  IF total_new<>jsonb_array_length(candidates) THEN RAISE EXCEPTION 'duplicate owner field' USING ERRCODE='22023'; END IF;
  SELECT count(*) INTO total_new FROM (SELECT DISTINCT value->>'ownerTypeId',value->'field'->>'name' FROM jsonb_array_elements(candidates)) q;
  IF total_new<>jsonb_array_length(candidates) THEN RAISE EXCEPTION 'duplicate owner field name' USING ERRCODE='22023'; END IF;
  -- Complete original membership/definition preflight precedes every allocation.
  -- JSON extraction checks correspondence; UMF validity remains the owner's check.
  FOR candidate IN SELECT value FROM jsonb_array_elements(candidates) LOOP
    SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=(candidate->>'ownerTypeId')::int;
    IF (SELECT count(*) FROM truss.schema_doc d
        CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
        CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') r
        CROSS JOIN LATERAL jsonb_array_elements(r.value->'members') member
        CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') fm
        CROSS JOIN LATERAL jsonb_array_elements(fm.value->'elements') f
        WHERE d.rev=revision AND d.ord=owner.doc_ord AND d.doc_id=owner.document_id
          AND m.value->>'id'=owner.module AND r.value->>'id'=owner.element AND r.value->>'kind'='record'
          AND fm.value->>'id'=member.value->>'module' AND f.value->>'id'=member.value->>'element'
          AND f.value=candidate->'field')<>1 THEN
      RAISE EXCEPTION 'property does not match original owner member and Field definition' USING ERRCODE='55000';
    END IF;
  END LOOP;
  SELECT greatest(coalesce(max(p.prop_id)::bigint,0),0) INTO high_water FROM truss.prop_def p;
  IF high_water+total_new>2147483647 THEN RAISE EXCEPTION 'property capacity exhausted' USING ERRCODE='54000'; END IF;
  assigned:=high_water;
  FOR candidate IN SELECT v.value FROM jsonb_array_elements(candidates) v
      JOIN truss.type_def t ON t.type_id=(v.value->>'ownerTypeId')::int
      ORDER BY t.document_id COLLATE "C",t.module COLLATE "C",t.element COLLATE "C",(v.value->'field'->>'id') COLLATE "C" LOOP
    assigned:=assigned+1;
    SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=(candidate->>'ownerTypeId')::int;
    INSERT INTO truss.prop_def(prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,home,
      since_rev,doc_ord,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id)
    VALUES(assigned::int,owner.type_id,candidate->'field'->>'id',candidate->'field'->>'name',candidate->'field'->>'scalarType',
      candidate->'field'->>'nullability',candidate->'field'->>'cardinality',candidate->'field'->'facets',candidate->'field'->'itemType',candidate->>'home',
      revision,owner.doc_ord,'accepted_document',revision,owner.doc_ord,owner.document_id);
    RETURN QUERY SELECT owner.type_id::text,candidate->'field'->>'id',assigned::text;
  END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_new_properties(int,jsonb) FROM PUBLIC;
