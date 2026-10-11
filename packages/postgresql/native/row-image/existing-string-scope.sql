-- Complete selected object/property scope for the pending string writer.
-- Caller owns catalog/owner exclusions and complete integrity visibility. INVOKER
-- observations do not establish RLS completeness, authority, readiness or seals.
-- Length checks bound selected retained images, not detoast/allocator/deadline
-- costs or the complete operation resource account.
CREATE FUNCTION truss.row_image_existing_string_scope_original(
 selected_owner bigint, selected_discriminator int, selected_property_owner int,
 selected_property int, selected_state bigint)
RETURNS TABLE(state_row truss.row_home_state, node_row truss.row_home_node,
 scalar_row truss.row_home_scalar, state_image bytea, node_image bytea, scalar_image bytea)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp AS $$
DECLARE state_count bigint; node_count bigint; scalar_count bigint;
 state_size bigint; node_size bigint; scalar_size bigint; images record;
BEGIN
 IF selected_owner IS NULL OR selected_owner<=0 OR selected_discriminator IS NULL
    OR selected_property_owner IS NULL OR selected_property IS NULL
    OR selected_state IS NULL OR selected_state<=0 THEN
  RAISE EXCEPTION 'complete original object property tuple required' USING ERRCODE='22023';
 END IF;
 -- Enumerate the full tuple first; selected_state is not a completeness filter.
 SELECT count(*),coalesce(sum(truss.row_image_state_length_original(s)),0)
  INTO state_count,state_size FROM truss.row_home_state s
  WHERE s.owner_kind='object' AND s.object_id=selected_owner
    AND s.object_type_id=selected_discriminator
    AND s.property_owner_type_id=selected_property_owner AND s.property_id=selected_property;
 IF state_count<>1 OR state_size NOT BETWEEN 1 AND 8388608 THEN
  RAISE EXCEPTION 'complete singleton string property scope required' USING ERRCODE='55000';
 END IF;
 SELECT s.* INTO STRICT state_row FROM truss.row_home_state s
  WHERE s.owner_kind='object' AND s.object_id=selected_owner
    AND s.object_type_id=selected_discriminator
    AND s.property_owner_type_id=selected_property_owner AND s.property_id=selected_property;
 IF state_row.state_id IS DISTINCT FROM selected_state THEN
  RAISE EXCEPTION 'selected state differs from complete property scope' USING ERRCODE='55000';
 END IF;
 SELECT count(*),coalesce(sum(truss.row_image_node_length_original(n)),0)
  INTO node_count,node_size FROM truss.row_home_node n WHERE n.state_id=state_row.state_id;
 SELECT count(*),coalesce(sum(truss.row_image_scalar_length_original(c)),0)
  INTO scalar_count,scalar_size FROM truss.row_home_scalar c WHERE c.state_id=state_row.state_id;
 IF node_count<>1 OR scalar_count<>1 OR node_size<=0 OR scalar_size<=0
    OR 2*(state_size+node_size+scalar_size)>8388608 THEN
  RAISE EXCEPTION 'bounded complete string node and payload membership required' USING ERRCODE='55000';
 END IF;
 SELECT n.* INTO STRICT node_row FROM truss.row_home_node n WHERE n.state_id=state_row.state_id;
 SELECT c.* INTO STRICT scalar_row FROM truss.row_home_scalar c WHERE c.state_id=state_row.state_id;
 IF node_row.node_id IS DISTINCT FROM state_row.root_node_id
    OR node_row.parent_node_id IS NOT NULL OR node_row.slot_kind IS DISTINCT FROM 'root'
    OR node_row.value_kind IS DISTINCT FROM 'scalar'
    OR scalar_row.node_id IS DISTINCT FROM node_row.node_id
    OR scalar_row.scalar_kind IS DISTINCT FROM 'string' THEN
  RAISE EXCEPTION 'complete parentless string root and payload correspondence required' USING ERRCODE='55000';
 END IF;
 state_image:=truss.row_image_state_original(state_row);
 node_image:=truss.row_image_node_original(node_row);
 scalar_image:=truss.row_image_scalar_original(scalar_row);
 -- Reuse attribution, exclusive-column and OLD/NEW exact-token checks.
 SELECT a.* INTO STRICT images FROM truss.row_image_existing_string_candidate_original(
  state_row,node_row,scalar_row,state_image,node_image,scalar_image,
  scalar_row.text_value,scalar_row.original_source_bytes) a;
 IF images.old_state_image IS DISTINCT FROM state_image OR images.new_state_image IS DISTINCT FROM state_image
    OR images.old_node_image IS DISTINCT FROM node_image OR images.new_node_image IS DISTINCT FROM node_image
    OR images.old_scalar_image IS DISTINCT FROM scalar_image OR images.new_scalar_image IS DISTINCT FROM scalar_image THEN
  RAISE EXCEPTION 'complete unchanged string scope byte correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_existing_string_scope_original(bigint,int,int,int,bigint) FROM PUBLIC;
