-- Private candidate image construction toward row_touch_observe.
-- No data writes or lock acquisition. Codecs inspect native catalogs.
-- Enclosing original producers own complete scope, definition/profile meaning,
-- OLD capture, NEW text/source correspondence, authority and resource custody.
CREATE FUNCTION truss.row_image_existing_string_candidate_original(
  old_state truss.row_home_state, old_node truss.row_home_node,
  old_scalar truss.row_home_scalar, expected_state bytea, expected_node bytea,
  expected_scalar bytea, replacement text, replacement_source bytea)
RETURNS TABLE(old_state_image bytea, old_node_image bytea, old_scalar_image bytea,
              new_state_image bytea, new_node_image bytea, new_scalar_image bytea)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp AS $$
DECLARE candidate truss.row_home_scalar; attributed record;
        new_size bigint; retained_size bigint; state_size bigint; node_size bigint; scalar_size bigint;
BEGIN
 IF replacement IS NULL OR replacement_source IS NULL OR octet_length(replacement_source)=0
    OR octet_length(replacement)>1048576 OR octet_length(replacement_source)>1048576
    OR expected_state IS NULL OR expected_node IS NULL OR expected_scalar IS NULL
    OR old_state.owner_kind COLLATE pg_catalog."C" IS DISTINCT FROM 'object'
    OR old_node.slot_kind COLLATE pg_catalog."C" IS DISTINCT FROM 'root'
    OR old_node.value_kind COLLATE pg_catalog."C" IS DISTINCT FROM 'scalar'
    OR old_scalar.scalar_kind COLLATE pg_catalog."C" IS DISTINCT FROM 'string'
    OR old_node.node_id IS DISTINCT FROM old_state.root_node_id
    OR old_scalar.text_value IS NULL OR old_scalar.original_source_bytes IS NULL THEN
  RAISE EXCEPTION 'original existing string candidate inputs required' USING ERRCODE='22023';
 END IF;
 -- Measure actual typed values before whole-image serialization.
 state_size:=truss.row_image_state_length_original(old_state);
 node_size:=truss.row_image_node_length_original(old_node);
 scalar_size:=truss.row_image_scalar_length_original(old_scalar);
 IF octet_length(expected_state)<>state_size OR octet_length(expected_node)<>node_size
    OR octet_length(expected_scalar)<>scalar_size THEN
  RAISE EXCEPTION 'original expected image length mismatch' USING ERRCODE='22023';
 END IF;
 new_size:=scalar_size-octet_length(old_scalar.text_value)
   -octet_length(old_scalar.original_source_bytes)+octet_length(replacement)+octet_length(replacement_source);
 retained_size:=2*state_size+2*node_size+scalar_size+new_size;
 IF new_size<=0 OR retained_size>8388608 THEN
  RAISE EXCEPTION 'original candidate retained image bound' USING ERRCODE='54000';
 END IF;
 SELECT a.* INTO STRICT attributed FROM truss.row_image_scalar_owner_original(
   old_scalar,expected_scalar,old_node,expected_node,old_state,expected_state) a;
 old_state_image:=attributed.state_image;old_node_image:=attributed.node_image;
 old_scalar_image:=attributed.original_image;
 candidate:=old_scalar;
 candidate.text_value:=replacement;candidate.original_source_bytes:=replacement_source;
 -- State/node images remain separately labeled from the changed scalar.
 new_state_image:=old_state_image;new_node_image:=old_node_image;
 new_scalar_image:=truss.row_image_scalar_original(candidate);
 IF octet_length(new_scalar_image)<>new_size THEN
  RAISE EXCEPTION 'original candidate image length correspondence failed' USING ERRCODE='55000';
 END IF;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_existing_string_candidate_original(
 truss.row_home_state,truss.row_home_node,truss.row_home_scalar,bytea,bytea,bytea,text,bytea) FROM PUBLIC;
