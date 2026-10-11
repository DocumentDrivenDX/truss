-- Private attribution primitives for the original OLD or NEW side inventory.
-- Exact byte/association correspondence is not original side completeness,
-- allocation, event, operation, reservation or authorization evidence.
CREATE FUNCTION truss.row_image_node_owner_original(value truss.row_home_node,
  retained_event bytea, retained_state truss.row_home_state, expected_state_image bytea)
RETURNS TABLE(owner_kind text, owner_id bigint, discriminator_id int,
  property_owner_type_id int, property_id int, original_image bytea, state_image bytea)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp AS $$
DECLARE association record;
BEGIN
 original_image:=truss.row_image_node_original(value);
 IF retained_event IS NULL OR original_image<>retained_event
    OR value.state_id IS NULL OR value.state_id<=0
    OR value.node_id IS NULL OR value.node_id<=0
    OR value.slot_kind IS NULL OR value.value_kind IS NULL
    OR value.definition_bytes IS NULL OR octet_length(value.definition_bytes)=0
    OR value.source_bytes IS NULL OR octet_length(value.source_bytes)=0
    OR retained_state.state_id IS NULL OR value.state_id<>retained_state.state_id THEN
  RAISE EXCEPTION 'original retained node side correspondence required' USING ERRCODE='22023';
 END IF;
 IF value.value_kind COLLATE pg_catalog."C" NOT IN ('scalar','null','sequence','map','record','structured')
    OR (value.parent_node_id IS NOT NULL AND (value.parent_node_id<=0 OR value.parent_node_id=value.node_id))
    OR NOT ((value.slot_kind COLLATE pg_catalog."C"='root' AND value.parent_node_id IS NULL
        AND value.sequence_ordinal IS NULL AND value.map_key IS NULL AND value.record_field_identity_bytes IS NULL)
      OR (value.slot_kind COLLATE pg_catalog."C"='sequence' AND value.parent_node_id IS NOT NULL
        AND value.sequence_ordinal IS NOT NULL AND value.sequence_ordinal>=0
        AND value.map_key IS NULL AND value.record_field_identity_bytes IS NULL)
      OR (value.slot_kind COLLATE pg_catalog."C"='map' AND value.parent_node_id IS NOT NULL
        AND value.map_key IS NOT NULL AND value.sequence_ordinal IS NULL AND value.record_field_identity_bytes IS NULL)
      OR (value.slot_kind COLLATE pg_catalog."C"='record' AND value.parent_node_id IS NOT NULL
        AND value.record_field_identity_bytes IS NOT NULL AND octet_length(value.record_field_identity_bytes)>0
        AND value.sequence_ordinal IS NULL AND value.map_key IS NULL)) IS TRUE THEN
  RAISE EXCEPTION 'original node slot grammar required' USING ERRCODE='22023';
 END IF;
 SELECT a.* INTO STRICT association FROM truss.row_image_state_owner_original(retained_state) a;
 IF expected_state_image IS NULL OR association.original_image<>expected_state_image THEN
  RAISE EXCEPTION 'original retained state image correspondence required' USING ERRCODE='22023';
 END IF;
 owner_kind:=association.owner_kind;owner_id:=association.owner_id;
 discriminator_id:=association.discriminator_id;
 property_owner_type_id:=association.property_owner_type_id;property_id:=association.property_id;
 state_image:=association.original_image;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_node_owner_original(truss.row_home_node,bytea,truss.row_home_state,bytea) FROM PUBLIC;

CREATE FUNCTION truss.row_image_scalar_owner_original(value truss.row_home_scalar,
  retained_event bytea, retained_node truss.row_home_node, expected_node_image bytea,
  retained_state truss.row_home_state, expected_state_image bytea)
RETURNS TABLE(owner_kind text, owner_id bigint, discriminator_id int,
  property_owner_type_id int, property_id int, original_image bytea, node_image bytea, state_image bytea)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp AS $$
DECLARE association record; active boolean[]; required boolean[];
BEGIN
 original_image:=truss.row_image_scalar_original(value);
 IF retained_event IS NULL OR original_image<>retained_event
    OR value.state_id IS NULL OR value.state_id<=0
    OR value.node_id IS NULL OR value.node_id<=0 OR value.scalar_kind IS NULL
    OR value.codec_definition_bytes IS NULL OR octet_length(value.codec_definition_bytes)=0
    OR value.original_source_bytes IS NULL OR octet_length(value.original_source_bytes)=0
    OR retained_node.state_id IS NULL OR retained_node.node_id IS NULL
    OR value.state_id<>retained_node.state_id OR value.node_id<>retained_node.node_id THEN
  RAISE EXCEPTION 'original retained scalar side correspondence required' USING ERRCODE='22023';
 END IF;
 active:=ARRAY[value.text_value IS NOT NULL,value.boolean_value IS NOT NULL,
   value.numeric_value IS NOT NULL,value.numeric_token IS NOT NULL,value.binary_value IS NOT NULL,
   value.temporal_text IS NOT NULL,value.temporal_instant IS NOT NULL,value.opaque_bytes IS NOT NULL];
 CASE value.scalar_kind COLLATE pg_catalog."C"
  WHEN 'string' THEN required:=ARRAY[true,false,false,false,false,false,false,false];
  WHEN 'boolean' THEN required:=ARRAY[false,true,false,false,false,false,false,false];
  WHEN 'integer','decimal' THEN
   required:=ARRAY[false,false,true,true,false,false,false,false];
   IF value.numeric_token IS NULL OR octet_length(value.numeric_token)=0
      OR value.numeric_value::text COLLATE pg_catalog."C" IN ('NaN','Infinity','-Infinity')
      OR (value.scalar_kind COLLATE pg_catalog."C"='integer' AND value.numeric_value<>trunc(value.numeric_value)) THEN
    RAISE EXCEPTION 'original numeric scalar carrier shape required' USING ERRCODE='22023';
   END IF;
  WHEN 'binary' THEN required:=ARRAY[false,false,false,false,true,false,false,false];
  WHEN 'timestamp' THEN required:=ARRAY[false,false,false,false,false,true,active[7],false];
  WHEN 'opaque' THEN required:=ARRAY[false,false,false,false,false,false,false,true];
  ELSE RAISE EXCEPTION 'original scalar family required' USING ERRCODE='22023';
 END CASE;
 IF active<>required THEN
  RAISE EXCEPTION 'original scalar active slots required' USING ERRCODE='22023';
 END IF;
 node_image:=truss.row_image_node_original(retained_node);
 IF expected_node_image IS NULL OR node_image<>expected_node_image
    OR retained_node.value_kind COLLATE pg_catalog."C" IS DISTINCT FROM 'scalar' THEN
  RAISE EXCEPTION 'original retained scalar node correspondence required' USING ERRCODE='22023';
 END IF;
 SELECT a.* INTO STRICT association FROM truss.row_image_node_owner_original(
   retained_node,expected_node_image,retained_state,expected_state_image) a;
 owner_kind:=association.owner_kind;owner_id:=association.owner_id;
 discriminator_id:=association.discriminator_id;
 property_owner_type_id:=association.property_owner_type_id;property_id:=association.property_id;
 state_image:=association.state_image;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_scalar_owner_original(truss.row_home_scalar,bytea,truss.row_home_node,bytea,truss.row_home_state,bytea) FROM PUBLIC;
