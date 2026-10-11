-- Private semantic primitive for row_touch_observe; not event/scope authority.
-- The enclosing observer must independently admit the actual event, original
-- OLD/NEW side membership, producer, exclusions and reservation before use.
CREATE FUNCTION truss.row_image_state_owner_original(value truss.row_home_state)
RETURNS TABLE(owner_kind text, owner_id bigint, discriminator_id int,
              property_owner_type_id int, property_id int, original_image bytea)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 -- Qualify complete native membership and preserve the full original image,
 -- including definition/home/value/source bytes; do not project through JSON.
 original_image:=truss.row_image_state_original(value);
 IF value.state_id IS NULL OR value.state_id<=0
    OR value.owner_kind IS NULL OR value.root_node_id IS NULL OR value.root_node_id<=0
    OR value.property_owner_type_id IS NULL OR value.property_id IS NULL
    OR value.definition_bytes IS NULL OR value.home_profile_bytes IS NULL
    OR value.value_profile_bytes IS NULL OR value.source_bytes IS NULL
    OR octet_length(value.definition_bytes)=0 OR octet_length(value.home_profile_bytes)=0
    OR octet_length(value.value_profile_bytes)=0 OR octet_length(value.source_bytes)=0 THEN
  RAISE EXCEPTION 'original state ownership fields required' USING ERRCODE='22023';
 END IF;
 IF value.owner_kind COLLATE pg_catalog."C"='object' THEN
  IF value.object_id IS NULL OR value.object_type_id IS NULL
     OR value.edge_id IS NOT NULL OR value.relationship_type_id IS NOT NULL
     OR value.property_owner_type_id<>value.object_type_id THEN
   RAISE EXCEPTION 'original object state association required' USING ERRCODE='22023';
  END IF;
  owner_id:=value.object_id;discriminator_id:=value.object_type_id;
 ELSIF value.owner_kind COLLATE pg_catalog."C"='edge' THEN
  IF value.edge_id IS NULL OR value.relationship_type_id IS NULL
     OR value.object_id IS NOT NULL OR value.object_type_id IS NOT NULL THEN
   RAISE EXCEPTION 'original edge state association required' USING ERRCODE='22023';
  END IF;
  -- Edge property owner is independently selected; never replace it with
  -- the relationship discriminator or infer its association here.
  owner_id:=value.edge_id;discriminator_id:=value.relationship_type_id;
 ELSE
  RAISE EXCEPTION 'original state owner kind required' USING ERRCODE='22023';
 END IF;
 owner_kind:=value.owner_kind;
 property_owner_type_id:=value.property_owner_type_id;
 property_id:=value.property_id;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_state_owner_original(truss.row_home_state) FROM PUBLIC;
