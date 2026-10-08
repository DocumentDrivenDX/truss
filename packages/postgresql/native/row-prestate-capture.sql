-- Private native property prestate capture. Not a complete operation admission.
-- Retains deleted-parent attribution for the later original OLD/NEW observer.
CREATE FUNCTION truss.runtime_capture_row_prestate(kind text,owner_id bigint,discriminator_id int,
  property_owner_id int,property_id int)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  op truss.row_home_operation%ROWTYPE;
  head_revision int;
  owner_snapshot jsonb;
  property_snapshot jsonb;
  state_snapshot jsonb;
  node_snapshot jsonb;
  scalar_snapshot jsonb;
  captured bytea;
  native_state_id bigint;
BEGIN
  SELECT * INTO STRICT op FROM truss.row_home_operation o
    WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.phase NOT IN ('admitted','effects_ready','row_sealed') OR kind IS NULL OR kind NOT IN ('object','edge')
      OR owner_id IS NULL OR owner_id<=0 OR discriminator_id IS NULL OR discriminator_id<=0
      OR property_owner_id IS NULL OR property_owner_id<=0 OR property_id IS NULL OR property_id<=0 THEN
    RAISE EXCEPTION 'original native prestate scope required' USING ERRCODE='22023';
  END IF;
  SELECT h.rev INTO STRICT head_revision FROM truss.schema_head h WHERE h.id=1 FOR SHARE;
  SELECT to_jsonb(p) INTO STRICT property_snapshot FROM truss.prop_def p
    WHERE p.prop_id=runtime_capture_row_prestate.property_id AND p.type_id=property_owner_id AND p.retired_rev IS NULL;
  IF kind='object' THEN
    IF property_owner_id<>discriminator_id THEN RAISE EXCEPTION 'foreign object property owner' USING ERRCODE='55000'; END IF;
    SELECT to_jsonb(o) INTO STRICT owner_snapshot FROM truss.object o
      WHERE o.id=owner_id AND o.type_id=discriminator_id FOR NO KEY UPDATE;
    SELECT s.state_id,to_jsonb(s) INTO native_state_id,state_snapshot FROM truss.row_home_state s
      WHERE s.object_id=owner_id AND s.object_type_id=discriminator_id AND s.property_id=runtime_capture_row_prestate.property_id;
  ELSE
    SELECT to_jsonb(e) INTO STRICT owner_snapshot FROM truss.edge e
      JOIN truss.rel_def r ON r.rel_type_id=e.rel_type_id
      WHERE e.id=owner_id AND e.rel_type_id=discriminator_id AND r.assoc_type_id=property_owner_id FOR NO KEY UPDATE OF e;
    SELECT s.state_id,to_jsonb(s) INTO native_state_id,state_snapshot FROM truss.row_home_state s
      WHERE s.edge_id=owner_id AND s.relationship_type_id=discriminator_id
        AND s.property_owner_type_id=property_owner_id AND s.property_id=runtime_capture_row_prestate.property_id;
  END IF;
  IF (SELECT count(*) FROM truss.row_home_node n WHERE n.state_id=native_state_id)>4096 THEN
    RAISE EXCEPTION 'native prestate node bound' USING ERRCODE='54000';
  END IF;
  SELECT coalesce(jsonb_agg(to_jsonb(n) ORDER BY n.node_id),'[]'::jsonb) INTO node_snapshot
    FROM truss.row_home_node n WHERE n.state_id=native_state_id;
  SELECT coalesce(jsonb_agg(to_jsonb(s) ORDER BY s.node_id),'[]'::jsonb) INTO scalar_snapshot
    FROM truss.row_home_scalar s WHERE s.state_id=native_state_id;
  -- Native JSON is an opaque snapshot codec, not the canonical report encoder.
  -- All original native cells remain inside these exact bytes; host numeric parsing is forbidden.
  captured:=convert_to(jsonb_build_object('interfaceVersion','truss-native-row-prestate/0.1',
    'writerXid',op.original_writer_xid::text,'operationOrdinal',op.operation_ordinal::text,
    'effectGeneration',op.effect_generation::text,'operationKind',op.operation_kind,
    'nativeContextHex',encode(op.original_context_bytes,'hex'),
    'headRevision',head_revision::text,'kind',kind,'ownerId',owner_id::text,
    'discriminatorId',discriminator_id::text,'propertyOwnerId',property_owner_id::text,
    'propertyId',property_id::text,'owner',owner_snapshot,'property',property_snapshot,
    'state',state_snapshot,'nodes',node_snapshot,'scalars',scalar_snapshot)::text,'UTF8');
  IF octet_length(captured)>4194304 THEN RAISE EXCEPTION 'native prestate byte bound' USING ERRCODE='54000'; END IF;
  RETURN captured;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_row_prestate(text,bigint,int,int,int) FROM PUBLIC;
