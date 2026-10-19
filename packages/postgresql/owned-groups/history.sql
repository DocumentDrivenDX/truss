-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Owned-provider history implementation; installed with the complete provider.
-- Root interpretation comes from the original image revision, never a live root.
CREATE FUNCTION truss.runtime_object_ownership_at(object_image jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE revision int;root_id bigint;root_type int;pin record;
BEGIN
 IF jsonb_typeof(object_image) IS DISTINCT FROM 'object'
  OR NOT (object_image ?& ARRAY['id','type_id','root_id','root_type','rev']) THEN
  RAISE EXCEPTION 'original complete object root fields required' USING ERRCODE='55000';END IF;
 IF (object_image->'root_id'='null'::jsonb) IS DISTINCT FROM (object_image->'root_type'='null'::jsonb) THEN
  RAISE EXCEPTION 'complete original root pair required' USING ERRCODE='55000';END IF;
 IF object_image->'root_id'='null'::jsonb THEN RETURN '{"state":"rootless"}'::jsonb;END IF;
 revision:=(object_image->>'rev')::int;root_id:=(object_image->>'root_id')::bigint;root_type:=(object_image->>'root_type')::int;
 IF revision IS NULL OR revision<1 OR root_id IS NULL OR root_id<1 OR root_type IS NULL OR root_type<1
  OR root_id=(object_image->>'id')::bigint AND root_type=(object_image->>'type_id')::int THEN
  RAISE EXCEPTION 'original aggregate root identity required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',root_type,NULL,revision);
 RETURN jsonb_build_object('state','owned','root',jsonb_build_object('id',root_id::text,
  'typeId',root_type::text,'definitionPin',pin.definition_pin,
  'owner',jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id)));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_ownership_at(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_ownership_qualified(image jsonb,qualified_actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE ownership jsonb:=image->'ownership';root jsonb;pin record;revision int;
BEGIN
 IF ownership='{"state":"rootless"}'::jsonb THEN RETURN;END IF;
 IF ownership->>'state' IS DISTINCT FROM 'owned' OR ownership-ARRAY['state','root']<>'{}'::jsonb
  OR jsonb_typeof(ownership->'root') IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original explicit ownership selection required' USING ERRCODE='55000';END IF;
 root:=ownership->'root';revision:=(image->>'catalogRevision')::int;
 IF root-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb
  OR jsonb_typeof(root->'id') IS DISTINCT FROM 'string' OR root->>'id' !~ '^[1-9][0-9]{0,18}$'
  OR length(root->>'id')=19 AND (root->>'id') COLLATE "C">'9223372036854775807'
  OR jsonb_typeof(root->'typeId') IS DISTINCT FROM 'string' OR root->>'typeId' !~ '^[1-9][0-9]{0,9}$'
  OR (root->>'typeId')::bigint>2147483647
  OR root->>'id'=image->'identity'->>'id' AND root->>'typeId'=image->'identity'->>'typeId'
  OR revision IS NULL OR revision<1 THEN
  RAISE EXCEPTION 'exact historical aggregate root required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(root->>'typeId')::int,NULL,revision);
 IF root->>'definitionPin' IS DISTINCT FROM pin.definition_pin
  OR root->'owner' IS DISTINCT FROM jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id) THEN
  RAISE EXCEPTION 'original aggregate root interpretation required' USING ERRCODE='55000';END IF;
 IF NOT truss.runtime_can_read_qualified(pin.document_id,pin.module_id,qualified_actor) THEN
  RAISE EXCEPTION 'current historical root reader required' USING ERRCODE='42501';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_ownership_qualified(jsonb,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_ownership(image jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_history_ownership_qualified(image,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_ownership(jsonb) FROM PUBLIC;

CREATE OR REPLACE FUNCTION truss.runtime_object_history(object_image jsonb,identity jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE properties jsonb:='[]';retained jsonb;property truss.prop_def%ROWTYPE;pin record;basis jsonb;written_revision int:=(object_image->>'rev')::int;
BEGIN
 basis:=truss.catalog_all_expected_records(written_revision);
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(object_image->>'type_id')::int,NULL,written_revision);
 identity:=jsonb_set(identity,'{definitionPin}',to_jsonb(pin.definition_pin));
 FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=(object_image->>'type_id')::int ORDER BY prop_id LOOP
  IF object_image->'props' ? property.prop_id::text THEN
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',property.type_id,property.prop_id,written_revision);
   properties:=properties||jsonb_build_array(jsonb_build_object('propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,'value',object_image->'props'->property.prop_id::text));
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',key,'value',value) ORDER BY key COLLATE "C"),'[]'::jsonb) INTO retained FROM jsonb_each(coalesce(nullif(object_image->'retained','null'::jsonb),'{}'));
 RETURN jsonb_build_object('interfaceVersion','truss-history-record/0.1.0','kind','object','identity',identity,
  'recordVersion',object_image->>'ver','catalogRevision',object_image->>'rev',
  'createdAt',to_char((object_image->>'created_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'updatedAt',to_char((object_image->>'updated_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'properties',properties,'retained',retained,'ownership',truss.runtime_object_ownership_at(object_image));
END;
$$;

CREATE OR REPLACE FUNCTION truss.runtime_history_image(image jsonb,entity jsonb,expected_version bigint) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE revision int;pin text;member jsonb;endpoint jsonb;endpoint_pin record;
BEGIN
 IF image->>'interfaceVersion' IS DISTINCT FROM 'truss-history-record/0.1.0' OR image->>'kind' IS DISTINCT FROM entity->>'kind'
 OR image->'identity'->>'id' IS DISTINCT FROM entity->>'id' OR image->'identity'->>'typeId' IS DISTINCT FROM entity->>'typeId'
 OR image->'identity'->'owner' IS DISTINCT FROM jsonb_build_object('documentId',entity->>'documentId','moduleId',entity->>'moduleId')
 OR image->>'recordVersion' IS DISTINCT FROM expected_version::text THEN RAISE EXCEPTION 'original complete history image required' USING ERRCODE='55000';END IF;
 revision:=(image->>'catalogRevision')::int;
 IF entity->>'kind'='object' THEN SELECT definition_pin INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(entity->>'typeId')::int,NULL,revision);
 ELSE pin:=truss.runtime_relationship_pin((entity->>'typeId')::int,revision);END IF;
 IF image->'identity'->>'definitionPin' IS DISTINCT FROM pin THEN RAISE EXCEPTION 'original image interpretation required' USING ERRCODE='55000';END IF;
 FOR member IN SELECT value FROM jsonb_array_elements(image->'properties') LOOP
  PERFORM truss.runtime_history_property((entity->>'typeId')::int,(member->>'propertyId')::int,revision,member->>'definitionPin');
 END LOOP;
 IF entity->>'kind'='object' THEN PERFORM truss.runtime_history_ownership(image);END IF;
 IF entity->>'kind'='edge' THEN
  FOR endpoint IN SELECT value FROM jsonb_array_elements(jsonb_build_array(image->'source',image->'target')) LOOP
   SELECT * INTO STRICT endpoint_pin FROM truss.runtime_owned_definition_metadata('type',(endpoint->>'typeId')::int,NULL,revision);
   IF endpoint->>'definitionPin' IS DISTINCT FROM endpoint_pin.definition_pin OR endpoint->'owner' IS DISTINCT FROM jsonb_build_object('documentId',endpoint_pin.document_id,'moduleId',endpoint_pin.module_id) THEN
    RAISE EXCEPTION 'original endpoint interpretation required' USING ERRCODE='55000';END IF;
   IF NOT truss.runtime_can_read(endpoint_pin.document_id,endpoint_pin.module_id) THEN RAISE EXCEPTION 'current historical endpoint reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 END IF;
END;
$$;
