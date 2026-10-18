-- Original operation-time endpoint contexts. No current-row fallback for history.
CREATE FUNCTION truss.runtime_endpoint_ownership(identity jsonb,captured_revision int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE endpoint truss.object%ROWTYPE;root_object truss.object%ROWTYPE;endpoint_type truss.type_def%ROWTYPE;root_type truss.type_def%ROWTYPE;pin record;ownership jsonb;
BEGIN
 IF captured_revision<1 OR (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN
  RAISE EXCEPTION 'current ownership observation revision required' USING ERRCODE='55P03';END IF;
 IF identity-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb OR jsonb_typeof(identity->'owner') IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'exact endpoint identity required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT endpoint_type FROM truss.type_def WHERE type_id=(identity->>'typeId')::int AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',endpoint_type.type_id,NULL,captured_revision);
 IF identity->>'definitionPin' IS DISTINCT FROM pin.definition_pin OR identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',endpoint_type.document_id,'moduleId',endpoint_type.module) THEN
  RAISE EXCEPTION 'original endpoint definition correspondence required' USING ERRCODE='22023';END IF;
 IF NOT truss.runtime_can_read(endpoint_type.document_id,endpoint_type.module) THEN RAISE EXCEPTION 'endpoint reader required' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT endpoint FROM truss.object WHERE id=(identity->>'id')::bigint AND type_id=endpoint_type.type_id;
 IF (endpoint.root_id IS NULL) IS DISTINCT FROM (endpoint.root_type IS NULL) THEN RAISE EXCEPTION 'complete root pair required' USING ERRCODE='55000';END IF;
 ownership:='{"state":"rootless"}';
 IF endpoint.root_id IS NOT NULL THEN
  SELECT * INTO STRICT root_type FROM truss.type_def WHERE type_id=endpoint.root_type AND kind='record' AND NOT provisional AND retired_rev IS NULL;
  IF NOT truss.runtime_can_read(root_type.document_id,root_type.module) THEN RAISE EXCEPTION 'aggregate root reader required' USING ERRCODE='42501';END IF;
  SELECT * INTO STRICT root_object FROM truss.object WHERE id=endpoint.root_id AND type_id=endpoint.root_type;
  IF root_object.root_id IS NOT NULL OR root_object.root_type IS NOT NULL OR root_object.id=endpoint.id AND root_object.type_id=endpoint.type_id THEN
   RAISE EXCEPTION 'live rootless aggregate root required' USING ERRCODE='22023';END IF;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',root_type.type_id,NULL,captured_revision);
  ownership:=jsonb_build_object('state','owned','root',jsonb_build_object('id',root_object.id::text,'typeId',root_type.type_id::text,'definitionPin',pin.definition_pin,
    'owner',jsonb_build_object('documentId',root_type.document_id,'moduleId',root_type.module)));
 END IF;
 RETURN jsonb_build_object('identity',identity,'ownership',ownership);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_endpoint_ownership(jsonb,int) FROM PUBLIC;
