-- Internal matched key declaration persistence; no dataset uniqueness/acceptance proof.
CREATE FUNCTION truss.runtime_stage_new_key(revision int,owner_id int,original_key_id text,ordered_property_ids int[],primary_key boolean)
RETURNS text LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  op truss.row_home_operation%ROWTYPE;
  owner truss.type_def%ROWTYPE;
  next_number bigint;
  component int;
BEGIN
  SELECT * INTO STRICT op FROM truss.row_home_operation o
    WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' OR revision IS NULL OR owner_id IS NULL
      OR original_key_id IS NULL OR octet_length(original_key_id) NOT BETWEEN 1 AND 4096
      OR primary_key IS NULL OR ordered_property_ids IS NULL
      OR array_ndims(ordered_property_ids)<>1 OR array_lower(ordered_property_ids,1)<>1
      OR cardinality(ordered_property_ids) NOT BETWEEN 1 AND 256
      OR array_position(ordered_property_ids,NULL) IS NOT NULL THEN
    RAISE EXCEPTION 'original ordered key input required' USING ERRCODE='22023';
  END IF;
  LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
  SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=owner_id;
  IF owner.since_rev<>revision OR owner.retired_rev IS NOT NULL OR owner.doc_ord IS NULL THEN
    RAISE EXCEPTION 'original key owner correspondence required' USING ERRCODE='55000';
  END IF;
  IF (SELECT count(DISTINCT p) FROM unnest(ordered_property_ids) p)<>cardinality(ordered_property_ids) THEN
    RAISE EXCEPTION 'duplicate ordered key component' USING ERRCODE='22023';
  END IF;
  FOREACH component IN ARRAY ordered_property_ids LOOP
    PERFORM 1 FROM truss.prop_def p WHERE p.prop_id=component AND p.type_id=owner_id AND p.retired_rev IS NULL;
    IF NOT FOUND THEN RAISE EXCEPTION 'foreign or missing key component' USING ERRCODE='55000'; END IF;
  END LOOP;
  IF EXISTS(SELECT 1 FROM truss.key_def k WHERE k.type_id=owner_id AND (k.key_id=original_key_id OR (primary_key AND k.is_primary AND k.retired_rev IS NULL))) THEN
    RAISE EXCEPTION 'existing key requires original matching' USING ERRCODE='55000';
  END IF;
  SELECT greatest(coalesce(max(k.key_num)::bigint,0),0)+1 INTO next_number FROM truss.key_def k WHERE k.type_id=owner_id;
  IF next_number>32767 THEN RAISE EXCEPTION 'owner key number exhausted' USING ERRCODE='54000'; END IF;
  INSERT INTO truss.key_def(type_id,key_id,key_num,prop_ids,is_primary,since_rev,definition_source_kind,
      definition_rev,definition_doc_ord,definition_document_id)
  VALUES(owner_id,original_key_id,next_number::smallint,ordered_property_ids,primary_key,revision,
      'accepted_document',revision,owner.doc_ord,owner.document_id);
  RETURN next_number::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_new_key(int,int,text,int[],boolean) FROM PUBLIC;
