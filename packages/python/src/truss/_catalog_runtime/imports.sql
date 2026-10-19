-- SPDX-License-Identifier: MIT OR Apache-2.0
CREATE FUNCTION truss.runtime_import_profiles() RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT '{"importProfile":{"identity":"truss-scalar-import","version":"0.3","sha256":"f6bd20e9e82cbf0f6e8884ac07083dfee6dc8f67c4aa2c486b561db873dfd572"},"importPayloadProfile":{"identity":"truss-scalar-import-payload","version":"0.3","sha256":"60f3b8c801fb236b514389b8783909cb8703ab0c2466e879af0e919ec08815ae"},"importKeyProfile":{"identity":"truss-selected-umf-scalar-key","version":"0.2","sha256":"e4b325c5906c759776e7ffbb5b9c298caa23034339d90c4e2e7a9d74eb002708"},"configurationProfile":{"identity":"truss-installed-engine-forbid","version":"0.1","sha256":"502ecaf1a476e1d2350e55d009210b5444a65487f86f9d65b78aec275726fe96"}}'::jsonb || '{"ownedImportProfile":{"identity":"truss-atomic-owned-import","version":"0.1","sha256":"c7d62e8d980556be042c5965f592080215455f5e223af64b4864a3e578688f68"},"ownedImportPayloadProfile":{"identity":"truss-owned-import-payload","version":"0.1","sha256":"58e4b51b06bd4a36cb3c1b5c1384adac6c0bb1654e438b41da76734eed0c0f4a"}}'::jsonb;
$$;
REVOKE ALL ON FUNCTION truss.runtime_import_profiles() FROM PUBLIC;

ALTER TABLE truss.catalog_runtime_installation ADD COLUMN import_policy_generation bigint NOT NULL DEFAULT 1 CHECK(import_policy_generation=1);
CREATE FUNCTION truss.import_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE context jsonb;installation truss.catalog_runtime_installation%ROWTYPE;bundle text;profiles jsonb;
BEGIN
 context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();profiles:=truss.runtime_import_profiles();
 IF (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb OR (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
  RAISE EXCEPTION 'installed engine/forbid import policy required' USING ERRCODE='0A000';END IF;
 SELECT encode(sha256(convert_to(coalesce(jsonb_agg(jsonb_build_object('documentId',doc_id,'revision',doc_revision,'sha256',content_sha256) ORDER BY doc_id COLLATE "C"),'[]')::text,'UTF8')),'hex') INTO bundle
  FROM (SELECT DISTINCT ON(doc_id) doc_id,doc_revision,content_sha256 FROM truss.schema_doc WHERE rev>0 ORDER BY doc_id,rev DESC) documents;
 RETURN convert_to((context||profiles||jsonb_build_object('catalog',jsonb_build_object('revision',(SELECT rev::text FROM truss.schema_head WHERE id=1),'modelBundleSha256',bundle),
  'selectedConfiguration',jsonb_build_object('sourceEpoch',installation.source_epoch::text,'installationId',installation.installation_id::text,
   'generation',installation.import_policy_generation::text,'keyReuse','forbid','journalMode','engine','configurationProfile',profiles->'configurationProfile',
   'installedProducerInventorySha256',installation.release_sha256)))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.import_context(text,text) FROM PUBLIC;

CREATE FUNCTION truss.import_key_selection(selected_document text,selected_module text,selected_record text,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE context jsonb;selected truss.type_def%ROWTYPE;key_row truss.key_def%ROWTYPE;pin record;property truss.prop_def%ROWTYPE;components jsonb;component_buffer jsonb[]:=ARRAY[]::jsonb[];type_pin text;key_pin text;
BEGIN
 -- Selection needs current custody/configuration and the key profile, not a
 -- reconstruction/hash of the complete catalog bundle for every record.
 PERFORM truss.group_context(expected_release,expected_digest);
 IF (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb OR (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
  RAISE EXCEPTION 'installed engine/forbid import policy required' USING ERRCODE='0A000';END IF;
 context:=truss.runtime_import_profiles();
 PERFORM truss.runtime_module_writer(selected_document,selected_module);
 SELECT * INTO selected FROM truss.type_def WHERE document_id=selected_document AND module=selected_module AND element=selected_record AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'accepted import record type required' USING ERRCODE='22023';END IF;
 SELECT * INTO key_row FROM truss.key_def WHERE type_id=selected.type_id AND is_primary AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'import primary key required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',selected.type_id);type_pin:=pin.definition_pin;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',selected.type_id,key_row.key_num);key_pin:=pin.definition_pin;
 FOR property IN SELECT p.* FROM unnest(key_row.prop_ids) WITH ORDINALITY i(prop_id,ord) JOIN truss.prop_def p ON p.type_id=selected.type_id AND p.prop_id=i.prop_id ORDER BY i.ord LOOP
  IF property.scalar_type NOT IN ('string','integer','decimal','boolean','binary') OR property.scalar_type IS NULL OR property.cardinality<>'one' OR property.nullability<>'required' OR property.home<>'json' OR property.retired_rev IS NOT NULL THEN RAISE EXCEPTION 'selected string primary key required' USING ERRCODE='0A000';END IF;
  IF NOT truss.runtime_can_read(selected_document,property.declaration_module) THEN RAISE EXCEPTION 'primary property reader required' USING ERRCODE='42501';END IF;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',selected.type_id,property.prop_id);
  component_buffer:=array_append(component_buffer,jsonb_build_object('name',property.name,'propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,'scalarType',property.scalar_type,'facets',coalesce(property.facets,'{}'::jsonb)));
 END LOOP;
 FOR property IN SELECT p.* FROM unnest(key_row.prop_ids) i(prop_id) JOIN truss.prop_def p ON p.type_id=selected.type_id AND p.prop_id=i.prop_id LOOP
  IF NOT truss.runtime_can_read(selected_document,property.declaration_module) THEN RAISE EXCEPTION 'current primary declaration reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 PERFORM truss.runtime_module_writer(selected_document,selected_module);
 components:=to_jsonb(component_buffer);
 RETURN convert_to(jsonb_build_object('recordId',selected.element,'type',jsonb_build_object('typeId',selected.type_id::text,'definitionPin',type_pin,'owner',jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module)),
  'keyNumber',key_row.key_num::text,'keyId',key_row.key_id,'keyDefinitionPin',key_pin,'keyEncodingProfile',context->'importKeyProfile','components',components)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.import_key_selection(text,text,text,text,text) FROM PUBLIC;

CREATE FUNCTION truss.import_object_identity(original_identity bytea,original_document bytea,tuple_bytes bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE identity jsonb;selected truss.type_def%ROWTYPE;metadata jsonb;key_row truss.key_def%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 archive truss.schema_doc%ROWTYPE;component jsonb;values_text text[]:=ARRAY[]::text[];values_cells jsonb;values_buffer jsonb[]:=ARRAY[]::jsonb[];key_facets jsonb;facets_buffer jsonb[]:=ARRAY[]::jsonb[];fields jsonb;fields_buffer jsonb[]:=ARRAY[]::jsonb[];component_index int:=0;pin record;namespace bytea;transport bytea;observed record;member truss.object_key_bucket%ROWTYPE;object_row truss.object%ROWTYPE;result jsonb;owned_selection boolean:=false;root_owner record;
BEGIN
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 1048576 OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded unique import identity required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 IF identity->'profile'=truss.runtime_import_profiles()->'ownedImportProfile'
  AND identity-ARRAY['profile','identity']='{}'::jsonb THEN
  owned_selection:=true;identity:=identity->'identity';
 END IF;

 IF identity-ARRAY['operation','type','keyNumber','keyDefinitionPin','keyEncodingProfile','components']<>'{}'::jsonb OR identity->>'operation' IS DISTINCT FROM 'object_key'
  OR (identity->'type')-ARRAY['typeId','definitionPin','owner']<>'{}'::jsonb OR jsonb_typeof(identity->'type'->'typeId') IS DISTINCT FROM 'string'
  OR identity->'type'->>'typeId' !~ '^[1-9][0-9]{0,9}$' OR length(identity->'type'->>'typeId')=10 AND (identity->'type'->>'typeId') COLLATE "C">'2147483647'
  OR jsonb_typeof(identity->'components') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'closed exact primary identity required' USING ERRCODE='22023';END IF;
 SELECT * INTO selected FROM truss.type_def WHERE type_id=(identity->'type'->>'typeId')::int AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'known import type required' USING ERRCODE='22023';END IF;
 metadata:=convert_from(truss.import_key_selection(selected.document_id,selected.module,selected.element,expected_release,expected_digest),'UTF8')::jsonb;
 IF jsonb_typeof(identity->'keyNumber') IS DISTINCT FROM 'string' OR jsonb_typeof(identity->'keyDefinitionPin') IS DISTINCT FROM 'string' OR identity->'type' IS DISTINCT FROM metadata->'type' OR identity->>'keyNumber' IS DISTINCT FROM metadata->>'keyNumber'
  OR identity->>'keyDefinitionPin' IS DISTINCT FROM metadata->>'keyDefinitionPin' OR (identity->'keyEncodingProfile' IS DISTINCT FROM metadata->'keyEncodingProfile' AND NOT ((identity->'keyEncodingProfile'='{"identity":"truss-selected-umf-string-key","version":"0.1","sha256":"07e1b99b22803e55a378f8068a6b80454b7581129c66eabcb117545746a16625"}'::jsonb AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(identity->'components') c WHERE c.value->'value'->>'kind' IS DISTINCT FROM 'string')) IS TRUE))
  OR jsonb_array_length(identity->'components')<>jsonb_array_length(metadata->'components') THEN RAISE EXCEPTION 'actual complete primary definition required' USING ERRCODE='22023';END IF;
 IF NOT owned_selection THEN
  SELECT * INTO STRICT archive FROM truss.schema_doc WHERE doc_id=selected.document_id ORDER BY rev DESC LIMIT 1;
  IF original_document IS DISTINCT FROM convert_to(archive.document,'UTF8') THEN RAISE EXCEPTION 'caller-known original document required' USING ERRCODE='22023';END IF;
 END IF;
 FOR component IN SELECT value FROM jsonb_array_elements(identity->'components') LOOP
  IF jsonb_typeof(component->'propertyId') IS DISTINCT FROM 'string' OR jsonb_typeof(component->'definitionPin') IS DISTINCT FROM 'string' OR component-ARRAY['propertyId','definitionPin','value']<>'{}'::jsonb OR component->>'propertyId' IS DISTINCT FROM metadata->'components'->component_index->>'propertyId'
   OR component->>'definitionPin' IS DISTINCT FROM metadata->'components'->component_index->>'definitionPin' OR truss.valid_scalar_property(component->'value',metadata->'components'->component_index->>'scalarType',false,metadata->'components'->component_index->'facets') IS NOT TRUE THEN RAISE EXCEPTION 'exact ordered primary component required' USING ERRCODE='22023';END IF;
  values_buffer:=array_append(values_buffer,component->'value');
  facets_buffer:=array_append(facets_buffer,metadata->'components'->component_index->'facets');
  fields_buffer:=array_append(fields_buffer,jsonb_build_object('name',metadata->'components'->component_index->>'name','value',component->'value'));
  component_index:=component_index+1;
 END LOOP;
 values_cells:=to_jsonb(values_buffer);key_facets:=to_jsonb(facets_buffer);fields:=to_jsonb(fields_buffer);
 IF tuple_bytes IS NOT NULL THEN RAISE EXCEPTION 'client key encoding is no longer accepted' USING ERRCODE='22023';END IF;
 tuple_bytes:=truss.derive_catalog_key_tuple(selected.type_id,(metadata->>'keyNumber')::smallint,values_cells);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,
  'typeId',metadata->'type'->>'typeId','keyNumber',metadata->>'keyNumber','definitionPin',metadata->>'keyDefinitionPin','encoding','umf-key-tuple-v1')::text,'UTF8');
 LOCK TABLE truss.object IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 LOCK TABLE truss.edge IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(namespace,transport);
 IF cardinality(observed.member_ids)>1 THEN RAISE EXCEPTION 'unique live primary identity required' USING ERRCODE='55000';END IF;
 IF cardinality(observed.member_ids)=1 THEN
  SELECT * INTO STRICT member FROM truss.object_key_bucket WHERE storage_row_id=observed.member_ids[1];
  SELECT * INTO STRICT object_row FROM truss.object WHERE id=member.object_id AND type_id=selected.type_id FOR UPDATE NOWAIT;
  IF object_row.root_id IS NOT NULL OR object_row.root_type IS NOT NULL THEN
   IF NOT owned_selection THEN RAISE EXCEPTION 'owned object import requires an explicit supported ownership import profile' USING ERRCODE='0A000';END IF;
   SELECT t.document_id,t.module INTO STRICT root_owner FROM truss.type_def t WHERE t.type_id=object_row.root_type;
   IF NOT truss.runtime_can_read(root_owner.document_id,root_owner.module) THEN
    RAISE EXCEPTION 'current imported root reader required' USING ERRCODE='42501';END IF;
  END IF;
  result:=jsonb_build_object('state','skipped','reason','live_identity','identity',jsonb_build_object('id',object_row.id::text,'typeId',selected.type_id::text,'definitionPin',metadata->'type'->>'definitionPin','owner',metadata->'type'->'owner'));
 ELSIF cardinality(observed.reservation_ids)>0 THEN result:=jsonb_build_object('state','skipped','reason','reserved_identity');
 ELSE result:=jsonb_build_object('state','eligible','documentId',selected.document_id,'moduleId',selected.module,'recordId',selected.element,'definitionPin',metadata->'type'->>'definitionPin','primaryFields',fields);END IF;
 PERFORM truss.import_key_selection(selected.document_id,selected.module,selected.element,expected_release,expected_digest);
 PERFORM truss.runtime_module_writer(selected.document_id,selected.module);
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.import_object_identity(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE TABLE truss.runtime_import_source (entity_kind char(1) NOT NULL, entity_id bigint NOT NULL, group_attempt_id uuid NOT NULL REFERENCES truss.runtime_object_attempt (id), writer_xid xid8 NOT NULL, original_record bytea NOT NULL, expected_source jsonb NOT NULL, operation_index int NOT NULL DEFAULT 0 CHECK (operation_index BETWEEN 0 AND 1023), PRIMARY KEY (entity_kind, entity_id), CONSTRAINT runtime_import_source_attempt_operation UNIQUE (group_attempt_id, operation_index));
CREATE TRIGGER runtime_import_source_immutable BEFORE UPDATE OR DELETE ON truss.runtime_import_source FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_record_source_immutable BEFORE UPDATE OR DELETE ON truss.record_source FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();

CREATE FUNCTION truss.runtime_owned_import_record_source_checked(checked_attempt uuid,checked_next_index int,checked_writer_xid xid8,checked_operation jsonb,checked_result jsonb,owned_profile_matches boolean,load_id_asserted boolean,selected_index int,original_record bytea,load_id text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE selected_attempt uuid:=checked_attempt;record jsonb;payload bytea;value jsonb;operation jsonb:=checked_operation;result jsonb:=checked_result;source_value jsonb:='{}';source_invalid boolean;component_invalid boolean;expected_source jsonb;source_row truss.record_source%ROWTYPE;kind char(1);metadata jsonb;selected_type truss.type_def%ROWTYPE;owned_selection boolean;root_identity jsonb;resolved_source_identity jsonb;resolved_target_identity jsonb;source_entity_id bigint;inserted_rows int;
BEGIN
 IF selected_index IS NULL OR selected_index<0 OR selected_index>=checked_next_index THEN RAISE EXCEPTION 'current complete indexed import group required' USING ERRCODE='55000';END IF;
 IF original_record IS NULL OR octet_length(original_record) NOT BETWEEN 1 AND 2097152 OR (convert_from(original_record,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  OR load_id IS NULL OR octet_length(load_id) NOT BETWEEN 1 AND 4096 THEN RAISE EXCEPTION 'bounded original import record/load required' USING ERRCODE='22023';END IF;
 record:=convert_from(original_record,'UTF8')::jsonb;payload:=decode(record->'payload'->>'bytesBase64','base64');
 IF record-ARRAY['kind','identity','payload','payloadProfile']<>'{}'::jsonb OR (record->>'kind' IN ('object','edge')) IS NOT TRUE THEN RAISE EXCEPTION 'closed import record required' USING ERRCODE='22023';END IF;
 IF octet_length(payload) NOT BETWEEN 1 AND 1048576 OR (convert_from(payload,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded unique original payload required' USING ERRCODE='22023';END IF;
 value:=convert_from(payload,'UTF8')::jsonb;
 owned_selection:=record->'payloadProfile'=truss.runtime_import_profiles()->'ownedImportPayloadProfile';
 IF owned_selection IS NOT TRUE AND (selected_index<>0 OR checked_next_index<>1) THEN
  RAISE EXCEPTION 'legacy one-create import group required' USING ERRCODE='0A000';END IF;

 IF (record->'payloadProfile' IS DISTINCT FROM truss.runtime_import_profiles()->'ownedImportPayloadProfile'
  AND record->'payloadProfile' IS DISTINCT FROM truss.runtime_import_profiles()->'importPayloadProfile'
  AND NOT ((record->'payloadProfile'='{"identity":"truss-scalar-import-payload","version":"0.2","sha256":"45180a79836394b3c3c945cfe908b67e3a45ab3c81362f052b12ae45e7042281"}'::jsonb
   AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(value->'values') v WHERE truss.valid_flat_cell(v.value->'value') IS NOT TRUE)
   AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(value->'values') v
    CROSS JOIN LATERAL jsonb_array_elements(CASE v.value->'value'->>'kind' WHEN 'sequence' THEN v.value->'value'->'items' WHEN 'map' THEN v.value->'value'->'entries' ELSE '[]'::jsonb END) child
    WHERE truss.valid_scalar_cell(CASE v.value->'value'->>'kind' WHEN 'map' THEN child.value->'value' ELSE child.value END) IS NOT TRUE)) IS TRUE)
  AND NOT ((record->'payloadProfile'='{"identity":"truss-scalar-import-payload","version":"0.1","sha256":"bc7624102bf13a1f87d5382be8d7d02007c49f1775dbca14489a650d7d7ec2ed"}'::jsonb AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(value->'values') v WHERE truss.valid_scalar_cell(v.value->'value') IS NOT TRUE)) IS TRUE)) OR encode(sha256(payload),'hex') IS DISTINCT FROM record->'payload'->>'sha256'
  OR octet_length(payload) NOT BETWEEN 1 AND 1048576 OR (convert_from(payload,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'exact original profiled payload required' USING ERRCODE='22023';END IF;
 IF owned_selection AND owned_profile_matches IS NOT TRUE THEN RAISE EXCEPTION 'owned import group profile required' USING ERRCODE='0A000';END IF;
 IF value-ARRAY['interfaceVersion','kind','values','source',CASE record->>'kind' WHEN 'object' THEN 'ownership' ELSE 'orderKey' END]<>'{}'::jsonb THEN RAISE EXCEPTION 'closed profiled import payload required' USING ERRCODE='22023';END IF;
 IF (record->>'kind' IN ('object','edge')) IS NOT TRUE OR value->>'interfaceVersion' IS DISTINCT FROM (CASE WHEN owned_selection THEN 'truss-owned-import-payload/0.1.0' ELSE 'truss-import-payload/0.1.0' END) OR value->>'kind' IS DISTINCT FROM record->>'kind' OR result->>'outcome'<>'created'
  OR load_id_asserted IS NOT TRUE THEN
  RAISE EXCEPTION 'original import creation/load origin required' USING ERRCODE='22023';END IF;
 IF record->>'kind'='object' THEN
  kind:='o';
  IF operation->>'operation'<>'create_object' OR operation->>'typeDefinitionPin' IS DISTINCT FROM record->'identity'->'type'->>'definitionPin'
   OR operation->'values' IS DISTINCT FROM value->'values' OR NOT owned_selection AND operation->'ownership' IS DISTINCT FROM value->'ownership' THEN RAISE EXCEPTION 'original object payload creation required' USING ERRCODE='22023';END IF;
  SELECT * INTO STRICT selected_type FROM truss.type_def WHERE type_id=(result->'identity'->>'typeId')::int;
  metadata:=convert_from(truss.import_key_selection(selected_type.document_id,selected_type.module,selected_type.element,
   (SELECT release_id FROM truss.runtime_current_installation()),(SELECT release_sha256 FROM truss.runtime_current_installation())),'UTF8')::jsonb;
  IF (record->'identity')-ARRAY['operation','type','keyNumber','keyDefinitionPin','keyEncodingProfile','components']<>'{}'::jsonb OR record->'identity'->>'operation' IS DISTINCT FROM 'object_key' OR jsonb_typeof(record->'identity'->'components') IS DISTINCT FROM 'array' OR record->'identity'->'type' IS DISTINCT FROM metadata->'type' OR record->'identity'->>'keyNumber' IS DISTINCT FROM metadata->>'keyNumber'
   OR record->'identity'->>'keyDefinitionPin' IS DISTINCT FROM metadata->>'keyDefinitionPin' OR (record->'identity'->'keyEncodingProfile' IS DISTINCT FROM metadata->'keyEncodingProfile' AND NOT ((record->'identity'->'keyEncodingProfile'='{"identity":"truss-selected-umf-string-key","version":"0.1","sha256":"07e1b99b22803e55a378f8068a6b80454b7581129c66eabcb117545746a16625"}'::jsonb AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(record->'identity'->'components') c WHERE c.value->'value'->>'kind' IS DISTINCT FROM 'string')) IS TRUE))
   OR jsonb_array_length(record->'identity'->'components') IS DISTINCT FROM jsonb_array_length(metadata->'components') THEN RAISE EXCEPTION 'actual complete import primary key required' USING ERRCODE='22023';END IF;
  WITH value_rows AS MATERIALIZED (
   SELECT v.value AS authored_value,v.ordinality
   FROM jsonb_array_elements(value->'values') WITH ORDINALITY v(value,ordinality)
  ), values_by_name AS MATERIALIZED (
   SELECT jsonb_object_agg(authored_value->>'name',authored_value->'value')
    FILTER(WHERE jsonb_typeof(authored_value->'name')='string') AS value_map FROM value_rows
  ), components AS MATERIALIZED (
   SELECT c.value AS component,c.ordinality,
    metadata->'components'->((c.ordinality-1)::int) AS metadata_field
   FROM jsonb_array_elements(record->'identity'->'components') WITH ORDINALITY c(value,ordinality)
  ), component_checks AS (
   SELECT (component-ARRAY['propertyId','definitionPin','value']<>'{}'::jsonb
    OR jsonb_typeof(component->'propertyId') IS DISTINCT FROM 'string'
    OR jsonb_typeof(component->'definitionPin') IS DISTINCT FROM 'string'
    OR truss.valid_scalar_cell(component->'value',NULL,false) IS NOT TRUE
    OR component->>'propertyId' IS DISTINCT FROM metadata_field->>'propertyId'
    OR component->>'definitionPin' IS DISTINCT FROM metadata_field->>'definitionPin'
    OR value_map->(metadata_field->>'name') IS DISTINCT FROM component->'value') AS invalid
   FROM components CROSS JOIN values_by_name
  )
  SELECT coalesce(bool_or(invalid),false)
    OR (SELECT count(*)<>count(DISTINCT authored_value->>'name') FROM value_rows)
   INTO component_invalid FROM component_checks;
  IF component_invalid THEN RAISE EXCEPTION 'original primary field/payload agreement required' USING ERRCODE='22023';END IF;
 ELSE
  kind:='e';
  IF operation->>'operation'<>'create_edge' OR operation->>'relationshipDefinitionPin' IS DISTINCT FROM record->'identity'->>'relationshipDefinitionPin'
   OR NOT owned_selection AND (operation->'source' IS DISTINCT FROM jsonb_build_object('state','stored','identity',record->'identity'->'source') OR operation->'target' IS DISTINCT FROM jsonb_build_object('state','stored','identity',record->'identity'->'target'))
   OR operation->'values' IS DISTINCT FROM value->'values' OR operation->'orderKey' IS DISTINCT FROM value->'orderKey' THEN RAISE EXCEPTION 'original edge payload creation required' USING ERRCODE='22023';END IF;
 END IF;
 -- The granted source-registration facade enforces the same selected import
 -- subset itself; calling the Python identity preflight is not authority.
 IF owned_selection THEN
  IF kind='o' THEN
   IF value->'ownership'='{"state":"rootless"}'::jsonb THEN root_identity:=NULL;
   ELSIF value->'ownership'->>'state'='owned' AND (value->'ownership')-ARRAY['state','root']='{}'::jsonb THEN
    root_identity:=truss.runtime_owned_import_reference(convert_to((value->'ownership'->'root')::text,'UTF8'),
     (SELECT release_id FROM truss.runtime_current_installation()),(SELECT release_sha256 FROM truss.runtime_current_installation()))->'identity';
    root_identity:=nullif(root_identity,'null'::jsonb);
    IF root_identity IS NULL THEN RAISE EXCEPTION 'live imported aggregate root required' USING ERRCODE='22023';END IF;
   ELSE RAISE EXCEPTION 'explicit original imported ownership required' USING ERRCODE='22023';END IF;
   IF operation->'ownership'->>'state' IS DISTINCT FROM value->'ownership'->>'state' OR NOT EXISTS(
    SELECT 1 FROM truss.object o WHERE o.id=(result->'identity'->>'id')::bigint AND o.type_id=(result->'identity'->>'typeId')::int
     AND o.root_id IS NOT DISTINCT FROM (root_identity->>'id')::bigint
     AND o.root_type IS NOT DISTINCT FROM (root_identity->>'typeId')::int) THEN
    RAISE EXCEPTION 'original imported ownership correspondence required' USING ERRCODE='55000';END IF;
  ELSE
   resolved_source_identity:=truss.runtime_owned_import_reference(convert_to((record->'identity'->'source')::text,'UTF8'),
    (SELECT release_id FROM truss.runtime_current_installation()),(SELECT release_sha256 FROM truss.runtime_current_installation()))->'identity';
   resolved_target_identity:=truss.runtime_owned_import_reference(convert_to((record->'identity'->'target')::text,'UTF8'),
    (SELECT release_id FROM truss.runtime_current_installation()),(SELECT release_sha256 FROM truss.runtime_current_installation()))->'identity';
   resolved_source_identity:=nullif(resolved_source_identity,'null'::jsonb);resolved_target_identity:=nullif(resolved_target_identity,'null'::jsonb);
   IF resolved_source_identity IS NULL OR resolved_target_identity IS NULL OR NOT EXISTS(
    SELECT 1 FROM truss.runtime_edge_transition t WHERE t.attempt_id=selected_attempt AND t.operation_index=selected_index
     AND t.before_edge IS NULL AND t.edge_id=(result->'identity'->>'id')::bigint AND t.rel_type_id=(result->'identity'->>'typeId')::int
     AND t.source_identity IS NOT DISTINCT FROM resolved_source_identity AND t.target_identity IS NOT DISTINCT FROM resolved_target_identity) THEN
    RAISE EXCEPTION 'original imported endpoint correspondence required' USING ERRCODE='55000';END IF;
  END IF;
 ELSIF kind='o' THEN
  IF operation->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb OR NOT EXISTS(
   SELECT 1 FROM truss.object o WHERE o.id=(result->'identity'->>'id')::bigint AND o.type_id=(result->'identity'->>'typeId')::int
    AND o.root_id IS NULL AND o.root_type IS NULL) THEN
   RAISE EXCEPTION 'original rootless object source profile required' USING ERRCODE='0A000';END IF;
 ELSE
  IF NOT EXISTS(SELECT 1 FROM truss.edge e JOIN truss.rel_def r ON r.rel_type_id=e.rel_type_id
   JOIN truss.object source_object ON source_object.id=e.source_id AND source_object.type_id=e.source_type
   JOIN truss.object target_object ON target_object.id=e.target_id AND target_object.type_id=e.target_type
   WHERE e.id=(result->'identity'->>'id')::bigint AND e.rel_type_id=(result->'identity'->>'typeId')::int
    AND r.lifecycle='independent' AND source_object.root_id IS NULL AND source_object.root_type IS NULL
    AND target_object.root_id IS NULL AND target_object.root_type IS NULL)
   OR NOT EXISTS(SELECT 1 FROM truss.runtime_edge_transition t WHERE t.attempt_id=selected_attempt AND t.operation_index=0
    AND t.edge_id=(result->'identity'->>'id')::bigint AND t.rel_type_id=(result->'identity'->>'typeId')::int
    AND t.before_edge IS NULL AND t.endpoint_ownership->'after'->'source'->'ownership'='{"state":"rootless"}'::jsonb
    AND t.endpoint_ownership->'after'->'target'->'ownership'='{"state":"rootless"}'::jsonb) THEN
   RAISE EXCEPTION 'original rootless independent edge source profile required' USING ERRCODE='0A000';END IF;
 END IF;
 IF value ? 'source' THEN
  IF (value->'source')-ARRAY['kind','entries']<>'{}'::jsonb OR value->'source'->>'kind' IS DISTINCT FROM 'map' OR jsonb_typeof(value->'source'->'entries') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'exact source map required' USING ERRCODE='22023';END IF;
  WITH source_entries AS MATERIALIZED (
   SELECT e.value AS source_entry,e.ordinal
   FROM jsonb_array_elements(value->'source'->'entries') WITH ORDINALITY e(value,ordinal)
  ), projected AS (
   SELECT se.source_entry,se.ordinal,se.source_entry->>'key' AS source_key,
    CASE se.source_entry->'value'->>'kind' WHEN 'string' THEN se.source_entry->'value'->'text' WHEN 'null' THEN 'null'::jsonb WHEN 'boolean' THEN se.source_entry->'value'->'value' ELSE se.source_entry->'value' END AS cell_source_value,
    (se.source_entry-ARRAY['key','value']<>'{}'::jsonb OR jsonb_typeof(se.source_entry->'key') IS DISTINCT FROM 'string'
     OR octet_length(se.source_entry->>'key') NOT BETWEEN 1 AND 4096 OR truss.valid_scalar_cell(se.source_entry->'value') IS NOT TRUE
     OR se.source_entry->>'key' IN ('author','at','system') AND se.source_entry->'value'->>'kind' NOT IN ('string','null')) AS invalid
   FROM source_entries se
  )
  SELECT coalesce(bool_or(projected.invalid),false) OR count(projected.source_key)<>count(DISTINCT projected.source_key),
   coalesce(jsonb_object_agg(projected.source_key,projected.cell_source_value ORDER BY projected.ordinal)
    FILTER(WHERE projected.source_key IS NOT NULL),'{}'::jsonb)
   INTO source_invalid,source_value FROM projected;
  IF source_invalid THEN RAISE EXCEPTION 'lossless unique scalar source facts required' USING ERRCODE='22023';END IF;
 END IF;
 source_entity_id:=(result->'identity'->>'id')::bigint;
 INSERT INTO truss.record_source(entity_kind,entity_id,load_id,source) VALUES(kind,source_entity_id,load_id,source_value) RETURNING * INTO source_row;
 GET DIAGNOSTICS inserted_rows=ROW_COUNT;
 IF inserted_rows<>1 THEN RAISE EXCEPTION 'one imported source row required' USING ERRCODE='55000';END IF;
 expected_source:=to_jsonb(source_row);
 -- Preserve imported_at in the scalar result; the immutable row is the
 -- canonical source fact, so the compatibility ledger column stays empty.
 INSERT INTO truss.runtime_import_source(entity_kind,entity_id,group_attempt_id,writer_xid,original_record,expected_source,operation_index)
 VALUES(kind,source_entity_id,selected_attempt,checked_writer_xid,original_record,'{}'::jsonb,selected_index);
 PERFORM truss.runtime_module_writer(result->'identity'->'owner'->>'documentId',result->'identity'->'owner'->>'moduleId');
 RETURN convert_to(expected_source::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_import_record_source_checked(uuid,int,xid8,jsonb,jsonb,boolean,boolean,int,bytea,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_import_record_source(selected_attempt uuid,selected_index int,original_record bytea,load_id text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;operations jsonb;results jsonb;owned_profile_matches boolean;load_id_asserted boolean;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF NOT attempt.complete OR attempt.writer_xid<>pg_current_xact_id() OR attempt.actor_oid<>truss.runtime_person(false) THEN
  RAISE EXCEPTION 'current complete import attempt required' USING ERRCODE='55000';END IF;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 operations:=input->'operations';results:=attempt.results;
 owned_profile_matches:=input->'mutationProfile' IS NOT DISTINCT FROM truss.runtime_owned_profile();
 load_id_asserted:=EXISTS(SELECT 1 FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e
  WHERE e.value->>'key'='x-load-id' AND e.value->'value'=jsonb_build_object('kind','string','text',load_id));
 RETURN truss.runtime_owned_import_record_source_checked(attempt.id,attempt.next_index,attempt.writer_xid,
  operations->selected_index,results->selected_index,owned_profile_matches,load_id_asserted,selected_index,original_record,load_id);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_import_record_source(uuid,int,bytea,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_import_record_sources(selected_attempt uuid,records jsonb,load_id text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;operations jsonb;results jsonb;owned_profile_matches boolean;load_id_asserted boolean;entry jsonb;encoded text;original_record bytea;selected_index int;record_count int;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF NOT attempt.complete OR attempt.writer_xid<>pg_current_xact_id() OR attempt.actor_oid<>truss.runtime_person(false)
  OR records IS NULL OR jsonb_typeof(records) IS DISTINCT FROM 'array'
  OR octet_length(records::text)>16777216 OR load_id IS NULL OR octet_length(load_id) NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'bounded current completed import source batch required' USING ERRCODE='22023';END IF;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 operations:=input->'operations';results:=attempt.results;
 owned_profile_matches:=input->'mutationProfile' IS NOT DISTINCT FROM truss.runtime_owned_profile();
 load_id_asserted:=EXISTS(SELECT 1 FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e
  WHERE e.value->>'key'='x-load-id' AND e.value->'value'=jsonb_build_object('kind','string','text',load_id));
 record_count:=jsonb_array_length(records);
 IF record_count NOT BETWEEN 1 AND 1024 THEN RAISE EXCEPTION 'bounded nonempty import source batch required' USING ERRCODE='22023';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(records) r WHERE jsonb_typeof(r.value) IS DISTINCT FROM 'object'
  OR r.value-ARRAY['operationIndex','originalRecordBase64']<>'{}'::jsonb
  OR jsonb_typeof(r.value->'operationIndex') IS DISTINCT FROM 'number'
  OR (r.value->>'operationIndex') !~ '^(0|[1-9][0-9]{0,2}|10[01][0-9]|102[0-3])$'
  OR jsonb_typeof(r.value->'originalRecordBase64') IS DISTINCT FROM 'string'
  OR octet_length(r.value->>'originalRecordBase64') NOT BETWEEN 4 AND 2796204) THEN
  RAISE EXCEPTION 'exact bounded ordered import source batch entries required' USING ERRCODE='22023';END IF;
 IF (SELECT count(DISTINCT (r.value->>'operationIndex')::int) FROM jsonb_array_elements(records) r)<>record_count
  OR EXISTS(SELECT 1 FROM (SELECT (r.value->>'operationIndex')::int selected_index,
    lag((r.value->>'operationIndex')::int) OVER(ORDER BY r.ordinal) previous_index
   FROM jsonb_array_elements(records) WITH ORDINALITY r(value,ordinal)) ordered
   WHERE ordered.previous_index IS NOT NULL AND ordered.selected_index<=ordered.previous_index)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(records) r
   WHERE (r.value->>'operationIndex')::int>=attempt.next_index) THEN
  RAISE EXCEPTION 'unique input-ordered completed import indexes required' USING ERRCODE='22023';END IF;
 FOR entry IN SELECT r.value FROM jsonb_array_elements(records) WITH ORDINALITY r(value,ordinal) ORDER BY r.ordinal LOOP
  selected_index:=(entry->>'operationIndex')::int;encoded:=entry->>'originalRecordBase64';
  original_record:=decode(encoded,'base64');
  IF octet_length(original_record) NOT BETWEEN 1 AND 2097152 THEN
   RAISE EXCEPTION 'bounded original import record required' USING ERRCODE='22023';END IF;
  PERFORM truss.runtime_owned_import_record_source_checked(attempt.id,attempt.next_index,attempt.writer_xid,
   operations->selected_index,results->selected_index,owned_profile_matches,load_id_asserted,selected_index,original_record,load_id);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_import_record_sources(uuid,jsonb,text) FROM PUBLIC;

CREATE FUNCTION truss.import_record_source(selected_attempt uuid,original_record bytea,load_id text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 IF convert_from(original_record,'UTF8')::jsonb->'payloadProfile'=truss.runtime_import_profiles()->'ownedImportPayloadProfile' THEN
  RAISE EXCEPTION 'explicit owned import source facade required' USING ERRCODE='0A000';END IF;
 IF (SELECT next_index FROM truss.runtime_object_attempt WHERE id=selected_attempt) IS DISTINCT FROM 1 THEN
  RAISE EXCEPTION 'legacy one-create import group required' USING ERRCODE='55000';END IF;
 RETURN truss.runtime_owned_import_record_source(selected_attempt,0,original_record,load_id);
END;
$$;
REVOKE ALL ON FUNCTION truss.import_record_source(uuid,bytea,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_import_source_commit() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE ledger truss.runtime_import_source%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;actual jsonb;
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=session_user AND rolsuper) THEN RETURN NULL;END IF;
 SELECT * INTO STRICT ledger FROM truss.runtime_import_source WHERE entity_kind=NEW.entity_kind AND entity_id=NEW.entity_id;
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=ledger.group_attempt_id;
 IF ledger.writer_xid<>pg_current_xact_id() OR attempt.writer_xid<>ledger.writer_xid OR attempt.actor_oid<>truss.runtime_person(false) OR NOT attempt.complete
  OR ledger.operation_index<0 OR ledger.operation_index>=attempt.next_index
  OR attempt.results->ledger.operation_index->>'outcome'<>'created' OR attempt.results->ledger.operation_index->'identity'->>'id'<>ledger.entity_id::text
  OR (convert_from(ledger.original_record,'UTF8')::jsonb->'payloadProfile' IS DISTINCT FROM truss.runtime_import_profiles()->'ownedImportPayloadProfile'
   AND (ledger.operation_index<>0 OR attempt.next_index<>1)) THEN RAISE EXCEPTION 'original pending import creation required' USING ERRCODE='55000';END IF;
 SELECT to_jsonb(s) INTO actual FROM truss.record_source s WHERE entity_kind=ledger.entity_kind AND entity_id=ledger.entity_id;
 IF actual IS DISTINCT FROM ledger.expected_source THEN RAISE EXCEPTION 'immutable exact original import source required' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_import_source_commit() FROM PUBLIC;
-- Retained for upgrade compatibility with recorded routine inventories; new
-- installs do not attach this legacy per-row deferred proof trigger.

CREATE FUNCTION truss.runtime_edge_business_key(relation int,source_identity jsonb,target_identity jsonb) RETURNS text
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT jsonb_build_object('profile','truss-edge-import-identity/0.2','installationId',installation_id::text,'sourceEpoch',source_epoch::text,'relationshipId',relation::text,
  'source',source_identity-'definitionPin','target',target_identity-'definitionPin')::text FROM truss.runtime_current_installation();
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_business_key(int,jsonb,jsonb) FROM PUBLIC;
CREATE FUNCTION truss.runtime_lock_edge_business_key(key text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF key IS NULL OR octet_length(key)>65536 THEN RAISE EXCEPTION 'bounded exact edge identity required' USING ERRCODE='22023';END IF;
 IF NOT pg_try_advisory_xact_lock(('x'||substr(encode(sha256(convert_to('edge-import-route:'||key,'UTF8')),'hex'),1,16))::bit(64)::bigint) THEN RAISE EXCEPTION 'edge identity in flight' USING ERRCODE='55P03';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_lock_edge_business_key(text) FROM PUBLIC;

CREATE FUNCTION truss.import_edge_identity(original_identity bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE context jsonb;identity jsonb;relation truss.rel_def%ROWTYPE;source_definition truss.type_def%ROWTYPE;target_definition truss.type_def%ROWTYPE;key text;edge_row truss.edge%ROWTYPE;result jsonb;matches int;owned_selection boolean:=false;endpoint record;
BEGIN
 -- Selection needs current custody/configuration and the key profile, not a
 -- reconstruction/hash of the complete catalog bundle for every record.
 PERFORM truss.group_context(expected_release,expected_digest);
 IF (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb OR (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
  RAISE EXCEPTION 'installed engine/forbid import policy required' USING ERRCODE='0A000';END IF;
 context:=truss.runtime_import_profiles();
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 65536 OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded exact edge import identity required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 IF identity->'profile'=truss.runtime_import_profiles()->'ownedImportProfile'
  AND identity-ARRAY['profile','identity']='{}'::jsonb THEN
  owned_selection:=true;identity:=identity->'identity';
 END IF;

 IF identity-ARRAY['relationshipDefinitionPin','source','target']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge import identity required' USING ERRCODE='22023';END IF;
 relation:=truss.runtime_operation_relationship(jsonb_build_object('operation','create_edge','relationshipDefinitionPin',identity->>'relationshipDefinitionPin'),'[]',0);
 PERFORM truss.runtime_module_writer(relation.document_id,relation.module);source_definition:=truss.runtime_condition_type(identity->'source');target_definition:=truss.runtime_condition_type(identity->'target');
 IF NOT truss.runtime_can_read(source_definition.document_id,source_definition.module) OR NOT truss.runtime_can_read(target_definition.document_id,target_definition.module) THEN RAISE EXCEPTION 'edge endpoint readers required' USING ERRCODE='42501';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=source_definition.type_id AND target_type=target_definition.type_id) THEN RAISE EXCEPTION 'admitted edge endpoint pair required' USING ERRCODE='22023';END IF;
 LOCK TABLE truss.object IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 LOCK TABLE truss.edge IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 IF NOT owned_selection AND (relation.lifecycle IS DISTINCT FROM 'independent' OR EXISTS(SELECT 1 FROM truss.object o WHERE
  (o.id=(identity->'source'->>'id')::bigint AND o.type_id=source_definition.type_id OR o.id=(identity->'target'->>'id')::bigint AND o.type_id=target_definition.type_id)
  AND (o.root_id IS NOT NULL OR o.root_type IS NOT NULL))) THEN
  RAISE EXCEPTION 'rootless independent edge import profile required' USING ERRCODE='0A000';END IF;
 IF owned_selection THEN
  IF relation.lifecycle NOT IN ('owned','independent') THEN RAISE EXCEPTION 'supported owned import relationship required' USING ERRCODE='0A000';END IF;
  FOR endpoint IN SELECT DISTINCT t.document_id,t.module FROM truss.object o JOIN truss.type_def t ON t.type_id=o.root_type
   WHERE (o.id=(identity->'source'->>'id')::bigint AND o.type_id=source_definition.type_id
     OR o.id=(identity->'target'->>'id')::bigint AND o.type_id=target_definition.type_id) LOOP
   IF NOT truss.runtime_can_read(endpoint.document_id,endpoint.module) THEN RAISE EXCEPTION 'current imported endpoint root reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 END IF;
 PERFORM 1 FROM truss.object WHERE id=(identity->'source'->>'id')::bigint AND type_id=source_definition.type_id FOR UPDATE NOWAIT;
 PERFORM 1 FROM truss.object WHERE id=(identity->'target'->>'id')::bigint AND type_id=target_definition.type_id FOR UPDATE NOWAIT;
 key:=truss.runtime_edge_business_key(relation.rel_type_id,identity->'source',identity->'target');PERFORM truss.runtime_lock_edge_business_key(key);
 SELECT count(*) INTO matches FROM (SELECT 1 FROM truss.edge WHERE rel_type_id=relation.rel_type_id
  AND source_id=(identity->'source'->>'id')::bigint AND source_type=source_definition.type_id
  AND target_id=(identity->'target'->>'id')::bigint AND target_type=target_definition.type_id LIMIT 2) candidates;
 IF matches>1 THEN RAISE EXCEPTION 'ambiguous endpoint-only edge import identity' USING ERRCODE='22023';END IF;
 SELECT * INTO edge_row FROM truss.edge WHERE rel_type_id=relation.rel_type_id AND source_id=(identity->'source'->>'id')::bigint AND source_type=source_definition.type_id AND target_id=(identity->'target'->>'id')::bigint AND target_type=target_definition.type_id FOR UPDATE NOWAIT;
 IF FOUND THEN result:=jsonb_build_object('state','skipped','reason','live_identity','identity',jsonb_build_object('id',edge_row.id::text,'typeId',relation.rel_type_id::text,'definitionPin',identity->>'relationshipDefinitionPin','owner',jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module)));
 ELSIF EXISTS(SELECT 1 FROM truss.key_tombstone WHERE entity_kind='e' AND type_id=relation.rel_type_id AND key_num=0 AND k=key) THEN result:=jsonb_build_object('state','skipped','reason','reserved_identity');
 ELSE result:=jsonb_build_object('state','eligible','documentId',relation.document_id,'moduleId',relation.module,'relationshipDefinitionPin',identity->>'relationshipDefinitionPin');END IF;
 PERFORM truss.runtime_module_writer(relation.document_id,relation.module);
 IF NOT truss.runtime_can_read(source_definition.document_id,source_definition.module) OR NOT truss.runtime_can_read(target_definition.document_id,target_definition.module) THEN RAISE EXCEPTION 'current endpoint readers required' USING ERRCODE='42501';END IF;
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.import_edge_identity(bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.import_identity_key_selection(original_identity bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE identity jsonb;selected truss.type_def%ROWTYPE;metadata bytea;parsed jsonb;component jsonb;component_index int:=0;
BEGIN
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 1048576 OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded unique primary identity required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 IF jsonb_typeof(identity->'type'->'typeId') IS DISTINCT FROM 'string' OR identity->'type'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
  OR length(identity->'type'->>'typeId')=10 AND (identity->'type'->>'typeId') COLLATE "C">'2147483647' THEN RAISE EXCEPTION 'exact import type ID required' USING ERRCODE='22023';END IF;
 SELECT * INTO selected FROM truss.type_def WHERE type_id=(identity->'type'->>'typeId')::int AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'accepted import type required' USING ERRCODE='22023';END IF;
 metadata:=truss.import_key_selection(selected.document_id,selected.module,selected.element,expected_release,expected_digest);
 IF identity->'type' IS DISTINCT FROM convert_from(metadata,'UTF8')::jsonb->'type' THEN RAISE EXCEPTION 'original qualified import type required' USING ERRCODE='22023';END IF;
 parsed:=convert_from(metadata,'UTF8')::jsonb;
 IF jsonb_typeof(identity->'components') IS DISTINCT FROM 'array' OR jsonb_array_length(identity->'components')<>jsonb_array_length(parsed->'components') THEN RAISE EXCEPTION 'complete ordered import key cells required' USING ERRCODE='22023';END IF;
 FOR component IN SELECT value FROM jsonb_array_elements(identity->'components') LOOP
  IF component->>'propertyId' IS DISTINCT FROM parsed->'components'->component_index->>'propertyId'
   OR component->>'definitionPin' IS DISTINCT FROM parsed->'components'->component_index->>'definitionPin'
   OR truss.valid_scalar_property(component->'value',parsed->'components'->component_index->>'scalarType',false,parsed->'components'->component_index->'facets') IS NOT TRUE THEN
   RAISE EXCEPTION 'exact declared import key cell required' USING ERRCODE='22023';END IF;
  component_index:=component_index+1;
 END LOOP;
 RETURN metadata;
END;
$$;
REVOKE ALL ON FUNCTION truss.import_identity_key_selection(bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.import_report_record_authority(original_identity bytea,kind text,expected_release text,expected_digest text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE envelope jsonb;outcome_identity jsonb;object_row truss.object;edge_row truss.edge;endpoint record;identity jsonb;relation truss.rel_def%ROWTYPE;source_definition truss.type_def%ROWTYPE;target_definition truss.type_def%ROWTYPE;owned_selection boolean:=false;root_owner record;
BEGIN
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 2097152
  OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'bounded original report selection and outcome required' USING ERRCODE='22023';END IF;
 envelope:=convert_from(original_identity,'UTF8')::jsonb;
 IF envelope-ARRAY['originalIdentity','outcomeIdentity']<>'{}'::jsonb OR NOT envelope ?& ARRAY['originalIdentity','outcomeIdentity']
  OR jsonb_typeof(envelope->'originalIdentity') IS DISTINCT FROM 'object'
  OR jsonb_typeof(envelope->'outcomeIdentity') NOT IN ('object','null') THEN
  RAISE EXCEPTION 'exact original report outcome envelope required' USING ERRCODE='22023';END IF;
 outcome_identity:=nullif(envelope->'outcomeIdentity','null'::jsonb);
 IF outcome_identity IS NOT NULL AND (outcome_identity-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb
  OR jsonb_typeof(outcome_identity->'id') IS DISTINCT FROM 'string' OR outcome_identity->>'id' !~ '^[1-9][0-9]{0,18}$') THEN
  RAISE EXCEPTION 'retained typed report outcome required' USING ERRCODE='22023';END IF;
 original_identity:=convert_to((envelope->'originalIdentity')::text,'UTF8');
 IF envelope->'originalIdentity'->'profile'=truss.runtime_import_profiles()->'ownedImportProfile'
  AND (envelope->'originalIdentity')-ARRAY['profile','identity']='{}'::jsonb THEN
  owned_selection:=true;original_identity:=convert_to((envelope->'originalIdentity'->'identity')::text,'UTF8');
 END IF;

 IF kind='object' THEN
  IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 1048576 OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded unique report identity required' USING ERRCODE='22023';END IF;
  identity:=convert_from(original_identity,'UTF8')::jsonb;
  IF jsonb_typeof(identity->'type'->'typeId') IS DISTINCT FROM 'string' OR identity->'type'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
   OR length(identity->'type'->>'typeId')=10 AND (identity->'type'->>'typeId') COLLATE "C">'2147483647' THEN RAISE EXCEPTION 'exact report type ID required' USING ERRCODE='22023';END IF;
  SELECT t.* INTO source_definition FROM truss.type_def t WHERE t.type_id=(identity->'type'->>'typeId')::int AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'known report type required' USING ERRCODE='22023';END IF;
  IF identity->'type' IS DISTINCT FROM convert_from(truss.import_key_selection(source_definition.document_id,source_definition.module,source_definition.element,expected_release,expected_digest),'UTF8')::jsonb->'type' THEN RAISE EXCEPTION 'original report type identity required' USING ERRCODE='22023';END IF;
  IF outcome_identity IS NOT NULL THEN
   IF outcome_identity-'id' IS DISTINCT FROM identity->'type' THEN RAISE EXCEPTION 'original object report outcome type required' USING ERRCODE='22023';END IF;
   SELECT * INTO object_row FROM truss.object WHERE id=(outcome_identity->>'id')::bigint AND type_id=source_definition.type_id;
   IF FOUND AND (object_row.root_id IS NOT NULL OR object_row.root_type IS NOT NULL) THEN
    IF NOT owned_selection THEN RAISE EXCEPTION 'rootless object import report profile required' USING ERRCODE='0A000';END IF;
    SELECT t.document_id,t.module INTO STRICT root_owner FROM truss.type_def t WHERE t.type_id=object_row.root_type;
    IF NOT truss.runtime_can_read(root_owner.document_id,root_owner.module) THEN RAISE EXCEPTION 'current imported root report reader required' USING ERRCODE='42501';END IF;
   END IF;
  END IF;
  RETURN;
 END IF;
 IF kind<>'edge' THEN RAISE EXCEPTION 'selected report record required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 relation:=truss.runtime_operation_relationship(jsonb_build_object('operation','create_edge','relationshipDefinitionPin',identity->>'relationshipDefinitionPin'),'[]',0);
 PERFORM truss.runtime_module_writer(relation.document_id,relation.module);
 IF owned_selection THEN
  PERFORM truss.runtime_owned_import_reference(convert_to((identity->'source')::text,'UTF8'),expected_release,expected_digest);
  PERFORM truss.runtime_owned_import_reference(convert_to((identity->'target')::text,'UTF8'),expected_release,expected_digest);
  SELECT * INTO STRICT source_definition FROM truss.type_def WHERE type_id=(identity->'source'->'type'->>'typeId')::int;
  SELECT * INTO STRICT target_definition FROM truss.type_def WHERE type_id=(identity->'target'->'type'->>'typeId')::int;
  IF relation.lifecycle NOT IN ('owned','independent') THEN RAISE EXCEPTION 'supported owned import report relationship required' USING ERRCODE='0A000';END IF;
 ELSE
  source_definition:=truss.runtime_condition_type(identity->'source');target_definition:=truss.runtime_condition_type(identity->'target');
  IF relation.lifecycle IS DISTINCT FROM 'independent' THEN RAISE EXCEPTION 'independent import report profile required' USING ERRCODE='0A000';END IF;
 END IF;
 IF outcome_identity IS NOT NULL THEN
  IF outcome_identity->>'typeId' IS DISTINCT FROM relation.rel_type_id::text
   OR outcome_identity->>'definitionPin' IS DISTINCT FROM identity->>'relationshipDefinitionPin'
   OR outcome_identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module) THEN
   RAISE EXCEPTION 'original edge report outcome type required' USING ERRCODE='22023';END IF;
  SELECT * INTO edge_row FROM truss.edge WHERE id=(outcome_identity->>'id')::bigint AND rel_type_id=relation.rel_type_id;
  IF FOUND THEN
   FOR endpoint IN SELECT o.*,t.document_id,t.module FROM truss.object o JOIN truss.type_def t ON t.type_id=o.type_id
    WHERE (o.id=edge_row.source_id AND o.type_id=edge_row.source_type OR o.id=edge_row.target_id AND o.type_id=edge_row.target_type) LOOP
    IF NOT truss.runtime_can_read(endpoint.document_id,endpoint.module) THEN RAISE EXCEPTION 'current retained report endpoint reader required' USING ERRCODE='42501';END IF;
    IF endpoint.root_id IS NOT NULL OR endpoint.root_type IS NOT NULL THEN
     IF NOT owned_selection THEN RAISE EXCEPTION 'rootless endpoint import report profile required' USING ERRCODE='0A000';END IF;
     SELECT t.document_id,t.module INTO STRICT root_owner FROM truss.type_def t WHERE t.type_id=endpoint.root_type;
     IF NOT truss.runtime_can_read(root_owner.document_id,root_owner.module) THEN RAISE EXCEPTION 'current imported endpoint root report reader required' USING ERRCODE='42501';END IF;
    END IF;
   END LOOP;
  END IF;
 END IF;
 IF NOT truss.runtime_can_read(source_definition.document_id,source_definition.module) OR NOT truss.runtime_can_read(target_definition.document_id,target_definition.module) THEN RAISE EXCEPTION 'current report endpoint readers required' USING ERRCODE='42501';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.import_report_record_authority(bytea,text,text,text) FROM PUBLIC;

-- Resolve an accepted primary-key reference through the ordinary read contract.
-- This does not require writer membership in the referenced object's module.
CREATE FUNCTION truss.runtime_owned_import_reference(original_identity bytea,expected_release text,expected_digest text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE identity jsonb;selected truss.type_def%ROWTYPE;key_row truss.key_def%ROWTYPE;pin record;
 component record;supplied jsonb;values_json jsonb;values_buffer jsonb[]:=ARRAY[]::jsonb[];found_bytes bytea;found_object jsonb;context jsonb;
BEGIN
 -- Selection needs current custody/configuration and the key profile, not a
 -- reconstruction/hash of the complete catalog bundle for every record.
 PERFORM truss.group_context(expected_release,expected_digest);
 IF (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb OR (SELECT selected_setting.value FROM truss.setting selected_setting WHERE selected_setting.key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
  RAISE EXCEPTION 'installed engine/forbid import policy required' USING ERRCODE='0A000';END IF;
 context:=truss.runtime_import_profiles();
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 1048576
  OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'bounded exact primary reference required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 IF identity-ARRAY['operation','type','keyNumber','keyDefinitionPin','keyEncodingProfile','components']<>'{}'::jsonb
  OR identity->>'operation' IS DISTINCT FROM 'object_key'
  OR jsonb_typeof(identity->'components') IS DISTINCT FROM 'array'
  OR jsonb_typeof(identity->'type'->'typeId') IS DISTINCT FROM 'string'
  OR identity->'type'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
  OR length(identity->'type'->>'typeId')=10 AND (identity->'type'->>'typeId') COLLATE "C">'2147483647' THEN
  RAISE EXCEPTION 'closed original primary reference required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT selected FROM truss.type_def WHERE type_id=(identity->'type'->>'typeId')::int
  AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 SELECT * INTO STRICT key_row FROM truss.key_def WHERE type_id=selected.type_id AND is_primary AND retired_rev IS NULL;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',selected.type_id);
 IF identity->'type' IS DISTINCT FROM jsonb_build_object('typeId',selected.type_id::text,'definitionPin',pin.definition_pin,
    'owner',jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module))
  OR identity->>'keyNumber' IS DISTINCT FROM key_row.key_num::text
  OR identity->'keyEncodingProfile' IS DISTINCT FROM context->'importKeyProfile'
  OR jsonb_array_length(identity->'components') IS DISTINCT FROM cardinality(key_row.prop_ids) THEN
  RAISE EXCEPTION 'current qualified primary reference required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',selected.type_id,key_row.key_num);
 IF identity->>'keyDefinitionPin' IS DISTINCT FROM pin.definition_pin THEN
  RAISE EXCEPTION 'current original primary definition required' USING ERRCODE='22023';END IF;
 FOR component IN SELECT p.*,i.n FROM unnest(key_row.prop_ids) WITH ORDINALITY i(prop_id,n)
  JOIN truss.prop_def p ON p.type_id=selected.type_id AND p.prop_id=i.prop_id ORDER BY i.n LOOP
  supplied:=identity->'components'->(component.n::int-1);
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',selected.type_id,component.prop_id);
  IF supplied-ARRAY['propertyId','definitionPin','value']<>'{}'::jsonb
   OR supplied->>'propertyId' IS DISTINCT FROM component.prop_id::text
   OR supplied->>'definitionPin' IS DISTINCT FROM pin.definition_pin THEN
   RAISE EXCEPTION 'original ordered primary component required' USING ERRCODE='22023';END IF;
  values_buffer:=array_append(values_buffer,supplied->'value');
 END LOOP;
 values_json:=to_jsonb(values_buffer);
 found_bytes:=truss.lookup_string_key(selected.document_id,selected.module,selected.element,key_row.key_id,
  NULL,convert_to(values_json::text,'UTF8'),NULL,1048576,expected_release,expected_digest);
 IF found_bytes IS NULL THEN RETURN jsonb_build_object('identity',NULL,'keyIdentity',jsonb_build_array(selected.type_id,key_row.key_num,encode(truss.derive_catalog_key_tuple(selected.type_id,key_row.key_num,values_json),'hex'))::text);END IF;
 found_object:=convert_from(found_bytes,'UTF8')::jsonb;
 RETURN jsonb_build_object('identity',jsonb_build_object('id',found_object->>'id','typeId',found_object->>'typeId',
  'definitionPin',found_object->>'definitionPin','owner',identity->'type'->'owner'),
  'keyIdentity',jsonb_build_array(selected.type_id,key_row.key_num,encode(truss.derive_catalog_key_tuple(selected.type_id,key_row.key_num,values_json),'hex'))::text);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_import_reference(bytea,text,text) FROM PUBLIC;
