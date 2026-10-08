-- Internal persistence of a complete already-matched genuinely-new type batch.
-- No identity interpretation or public acceptance; full report/head/finalizer still required.
CREATE FUNCTION truss.runtime_stage_new_types(revision int, candidates jsonb)
RETURNS TABLE(document_id text,module_id text,element_id text,type_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  actual_xid xid8 := pg_current_xact_id_if_assigned();
  op truss.row_home_operation%ROWTYPE;
  candidate jsonb;
  count_new bigint;
  high_water bigint;
  assigned bigint;
  doc_ordinal int;
BEGIN
  SELECT * INTO STRICT op FROM truss.row_home_operation AS o
    WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted'
      OR revision IS NULL OR candidates IS NULL OR jsonb_typeof(candidates)<>'array'
      OR jsonb_array_length(candidates) NOT BETWEEN 1 AND 4096
      OR octet_length(candidates::text)>1048576 THEN
    RAISE EXCEPTION 'original catalog batch admission required' USING ERRCODE='22023';
  END IF;
  LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
  PERFORM 1 FROM truss.schema_rev AS r WHERE r.rev=revision;
  IF NOT FOUND THEN RAISE EXCEPTION 'missing original revision' USING ERRCODE='55000'; END IF;
  FOR candidate IN SELECT value FROM jsonb_array_elements(candidates) LOOP
    IF jsonb_typeof(candidate)<>'object' OR NOT candidate ?& ARRAY['documentId','moduleId','elementId','lineageProfile','lineageHex']
        OR (SELECT count(*) FROM jsonb_object_keys(candidate))<>5 THEN
      RAISE EXCEPTION 'original type candidate shape' USING ERRCODE='22023';
    END IF;
    IF EXISTS(SELECT 1 FROM jsonb_each(candidate) e WHERE jsonb_typeof(e.value)<>'string' OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 65536)
        OR candidate->>'lineageHex' !~ '^([0-9a-f]{2})+$' THEN
      RAISE EXCEPTION 'original type candidate carrier' USING ERRCODE='22023';
    END IF;
    PERFORM 1 FROM truss.schema_doc d WHERE d.rev=revision AND d.doc_id=candidate->>'documentId';
    IF NOT FOUND THEN RAISE EXCEPTION 'missing original document' USING ERRCODE='55000'; END IF;
    IF (SELECT count(*) FROM truss.schema_doc d
        CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
        CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e
        WHERE d.rev=revision AND d.doc_id=candidate->>'documentId'
          AND m.value->>'id'=candidate->>'moduleId'
          AND e.value->>'id'=candidate->>'elementId' AND e.value->>'kind'='record')<>1 THEN
      RAISE EXCEPTION 'type does not match original Record declaration' USING ERRCODE='55000';
    END IF;
    IF EXISTS(SELECT 1 FROM truss.type_def t WHERE t.document_id=candidate->>'documentId'
        AND t.module=candidate->>'moduleId' AND t.element=candidate->>'elementId') THEN
      RAISE EXCEPTION 'existing identity requires original matching, not new allocation' USING ERRCODE='55000';
    END IF;
  END LOOP;
  SELECT count(*) INTO count_new FROM (SELECT DISTINCT value->>'documentId',value->>'moduleId',value->>'elementId' FROM jsonb_array_elements(candidates)) q;
  IF count_new<>jsonb_array_length(candidates) THEN RAISE EXCEPTION 'duplicate qualified candidate' USING ERRCODE='22023'; END IF;
  SELECT greatest(coalesce(max(t.type_id)::bigint,0),0) INTO high_water FROM truss.type_def t;
  IF high_water+count_new>2147483647 THEN RAISE EXCEPTION 'catalog type capacity exhausted' USING ERRCODE='54000'; END IF;
  assigned:=high_water;
  FOR candidate IN SELECT value FROM jsonb_array_elements(candidates)
      ORDER BY (value->>'documentId') COLLATE "C",(value->>'moduleId') COLLATE "C",(value->>'elementId') COLLATE "C" LOOP
    assigned:=assigned+1;
    SELECT d.ord INTO STRICT doc_ordinal FROM truss.schema_doc d WHERE d.rev=revision AND d.doc_id=candidate->>'documentId';
    INSERT INTO truss.type_def(document_id,type_id,module,element,kind,provisional,since_rev,doc_ord,
      lineage_profile,lineage_bytes,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id)
    VALUES(candidate->>'documentId',assigned::int,candidate->>'moduleId',candidate->>'elementId','record',false,
      revision,doc_ordinal,candidate->>'lineageProfile',decode(candidate->>'lineageHex','hex'),
      'accepted_document',revision,doc_ordinal,candidate->>'documentId');
    RETURN QUERY SELECT candidate->>'documentId',candidate->>'moduleId',candidate->>'elementId',assigned::text;
  END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_new_types(int,jsonb) FROM PUBLIC;
