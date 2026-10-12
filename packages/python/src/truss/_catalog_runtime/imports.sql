CREATE FUNCTION truss.runtime_import_profiles() RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT '{"importProfile":{"identity":"truss-host-scalar-import","version":"0.1","sha256":"3f8ec350d3184ef4239e3193afb48ed0b37213f36db8fe4f636d55585a2c3b9d"},"importPayloadProfile":{"identity":"truss-scalar-import-payload","version":"0.1","sha256":"bc7624102bf13a1f87d5382be8d7d02007c49f1775dbca14489a650d7d7ec2ed"},"importKeyProfile":{"identity":"truss-selected-umf-string-key","version":"0.1","sha256":"07e1b99b22803e55a378f8068a6b80454b7581129c66eabcb117545746a16625"},"configurationProfile":{"identity":"truss-installed-engine-forbid","version":"0.1","sha256":"502ecaf1a476e1d2350e55d009210b5444a65487f86f9d65b78aec275726fe96"}}'::jsonb;
$$;
REVOKE ALL ON FUNCTION truss.runtime_import_profiles() FROM PUBLIC;

ALTER TABLE truss.catalog_runtime_installation ADD COLUMN import_policy_generation bigint NOT NULL DEFAULT 1 CHECK(import_policy_generation=1);
CREATE FUNCTION truss.import_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE context jsonb;installation truss.catalog_runtime_installation%ROWTYPE;bundle text;profiles jsonb;
BEGIN
 context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();profiles:=truss.runtime_import_profiles();
 IF (SELECT value FROM truss.setting WHERE key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb OR (SELECT value FROM truss.setting WHERE key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
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
DECLARE context jsonb;selected truss.type_def%ROWTYPE;key_row truss.key_def%ROWTYPE;pin record;property truss.prop_def%ROWTYPE;components jsonb:='[]';type_pin text;key_pin text;
BEGIN
 context:=convert_from(truss.import_context(expected_release,expected_digest),'UTF8')::jsonb;
 PERFORM truss.runtime_module_writer(selected_document,selected_module);
 SELECT * INTO selected FROM truss.type_def WHERE document_id=selected_document AND module=selected_module AND element=selected_record AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'accepted import record type required' USING ERRCODE='22023';END IF;
 SELECT * INTO key_row FROM truss.key_def WHERE type_id=selected.type_id AND is_primary AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'import primary key required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_definition('type',selected.type_id);type_pin:=pin.definition_pin;
 SELECT * INTO STRICT pin FROM truss.runtime_definition('key',selected.type_id,key_row.key_num);key_pin:=pin.definition_pin;
 FOR property IN SELECT p.* FROM unnest(key_row.prop_ids) WITH ORDINALITY i(prop_id,ord) JOIN truss.prop_def p ON p.type_id=selected.type_id AND p.prop_id=i.prop_id ORDER BY i.ord LOOP
  IF property.scalar_type<>'string' OR property.cardinality<>'one' OR property.nullability<>'required' OR property.home<>'json' OR property.retired_rev IS NOT NULL THEN RAISE EXCEPTION 'selected string primary key required' USING ERRCODE='0A000';END IF;
  IF NOT truss.runtime_can_read(selected_document,property.declaration_module) THEN RAISE EXCEPTION 'primary property reader required' USING ERRCODE='42501';END IF;
  SELECT * INTO STRICT pin FROM truss.runtime_definition('property',selected.type_id,property.prop_id);
  components:=components||jsonb_build_array(jsonb_build_object('name',property.name,'propertyId',property.prop_id::text,'definitionPin',pin.definition_pin));
 END LOOP;
 FOR property IN SELECT p.* FROM unnest(key_row.prop_ids) i(prop_id) JOIN truss.prop_def p ON p.type_id=selected.type_id AND p.prop_id=i.prop_id LOOP
  IF NOT truss.runtime_can_read(selected_document,property.declaration_module) THEN RAISE EXCEPTION 'current primary declaration reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 PERFORM truss.runtime_module_writer(selected_document,selected_module);
 RETURN convert_to(jsonb_build_object('recordId',selected.element,'type',jsonb_build_object('typeId',selected.type_id::text,'definitionPin',type_pin,'owner',jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module)),
  'keyNumber',key_row.key_num::text,'keyId',key_row.key_id,'keyDefinitionPin',key_pin,'keyEncodingProfile',context->'importKeyProfile','components',components)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.import_key_selection(text,text,text,text,text) FROM PUBLIC;

CREATE FUNCTION truss.import_object_identity(original_identity bytea,original_document bytea,tuple_bytes bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE identity jsonb;selected truss.type_def%ROWTYPE;metadata jsonb;key_row truss.key_def%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 archive truss.schema_doc%ROWTYPE;component jsonb;values_text text[]:=ARRAY[]::text[];fields jsonb:='[]';component_index int:=0;pin record;namespace bytea;transport bytea;observed record;member truss.object_key_bucket%ROWTYPE;object_row truss.object%ROWTYPE;result jsonb;
BEGIN
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 1048576 OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded unique import identity required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 IF identity-ARRAY['operation','type','keyNumber','keyDefinitionPin','keyEncodingProfile','components']<>'{}'::jsonb OR identity->>'operation' IS DISTINCT FROM 'object_key'
  OR (identity->'type')-ARRAY['typeId','definitionPin','owner']<>'{}'::jsonb OR jsonb_typeof(identity->'type'->'typeId') IS DISTINCT FROM 'string'
  OR identity->'type'->>'typeId' !~ '^[1-9][0-9]{0,9}$' OR length(identity->'type'->>'typeId')=10 AND (identity->'type'->>'typeId') COLLATE "C">'2147483647'
  OR jsonb_typeof(identity->'components') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'closed exact primary identity required' USING ERRCODE='22023';END IF;
 SELECT * INTO selected FROM truss.type_def WHERE type_id=(identity->'type'->>'typeId')::int AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'known import type required' USING ERRCODE='22023';END IF;
 metadata:=convert_from(truss.import_key_selection(selected.document_id,selected.module,selected.element,expected_release,expected_digest),'UTF8')::jsonb;
 IF jsonb_typeof(identity->'keyNumber') IS DISTINCT FROM 'string' OR jsonb_typeof(identity->'keyDefinitionPin') IS DISTINCT FROM 'string' OR identity->'type' IS DISTINCT FROM metadata->'type' OR identity->>'keyNumber' IS DISTINCT FROM metadata->>'keyNumber'
  OR identity->>'keyDefinitionPin' IS DISTINCT FROM metadata->>'keyDefinitionPin' OR identity->'keyEncodingProfile' IS DISTINCT FROM metadata->'keyEncodingProfile'
  OR jsonb_array_length(identity->'components')<>jsonb_array_length(metadata->'components') THEN RAISE EXCEPTION 'actual complete primary definition required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT archive FROM truss.schema_doc WHERE doc_id=selected.document_id ORDER BY rev DESC LIMIT 1;
 IF original_document IS DISTINCT FROM convert_to(archive.document,'UTF8') THEN RAISE EXCEPTION 'caller-known original document required' USING ERRCODE='22023';END IF;
 FOR component IN SELECT value FROM jsonb_array_elements(identity->'components') LOOP
  IF jsonb_typeof(component->'propertyId') IS DISTINCT FROM 'string' OR jsonb_typeof(component->'definitionPin') IS DISTINCT FROM 'string' OR component-ARRAY['propertyId','definitionPin','value']<>'{}'::jsonb OR component->>'propertyId' IS DISTINCT FROM metadata->'components'->component_index->>'propertyId'
   OR component->>'definitionPin' IS DISTINCT FROM metadata->'components'->component_index->>'definitionPin' OR truss.valid_scalar_cell(component->'value','string',false) IS NOT TRUE THEN RAISE EXCEPTION 'exact ordered primary component required' USING ERRCODE='22023';END IF;
  values_text:=array_append(values_text,component->'value'->>'text');fields:=fields||jsonb_build_array(jsonb_build_object('name',metadata->'components'->component_index->>'name','value',component->'value'));component_index:=component_index+1;
 END LOOP;
 IF truss.verify_umf_string_key_tuple(tuple_bytes,values_text) IS NOT TRUE THEN RAISE EXCEPTION 'original UMF primary tuple required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,
  'typeId',metadata->'type'->>'typeId','keyNumber',metadata->>'keyNumber','definitionPin',metadata->>'keyDefinitionPin','encoding','umf-key-tuple-v1')::text,'UTF8');
 transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(namespace,transport);
 IF cardinality(observed.member_ids)>1 THEN RAISE EXCEPTION 'unique live primary identity required' USING ERRCODE='55000';END IF;
 IF cardinality(observed.member_ids)=1 THEN
  SELECT * INTO STRICT member FROM truss.object_key_bucket WHERE storage_row_id=observed.member_ids[1];
  SELECT * INTO STRICT object_row FROM truss.object WHERE id=member.object_id AND type_id=selected.type_id FOR UPDATE NOWAIT;
  result:=jsonb_build_object('state','skipped','reason','live_identity','identity',jsonb_build_object('id',object_row.id::text,'typeId',selected.type_id::text,'definitionPin',metadata->'type'->>'definitionPin','owner',metadata->'type'->'owner'));
 ELSIF cardinality(observed.reservation_ids)>0 THEN result:=jsonb_build_object('state','skipped','reason','reserved_identity');
 ELSE result:=jsonb_build_object('state','eligible','documentId',selected.document_id,'moduleId',selected.module,'recordId',selected.element,'definitionPin',metadata->'type'->>'definitionPin','primaryFields',fields);END IF;
 PERFORM truss.import_key_selection(selected.document_id,selected.module,selected.element,expected_release,expected_digest);
 PERFORM truss.runtime_module_writer(selected.document_id,selected.module);
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.import_object_identity(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE TABLE truss.runtime_import_source (
 entity_kind char(1) NOT NULL,entity_id bigint NOT NULL,group_attempt_id uuid NOT NULL UNIQUE REFERENCES truss.runtime_object_attempt(id),
 writer_xid xid8 NOT NULL,original_record bytea NOT NULL,expected_source jsonb NOT NULL,PRIMARY KEY(entity_kind,entity_id));
CREATE TRIGGER runtime_import_source_immutable BEFORE UPDATE OR DELETE ON truss.runtime_import_source FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_record_source_immutable BEFORE UPDATE OR DELETE ON truss.record_source FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();

CREATE FUNCTION truss.import_record_source(selected_attempt uuid,original_record bytea,load_id text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;record jsonb;payload bytea;value jsonb;input jsonb;operation jsonb;result jsonb;source_value jsonb:='{}';entry jsonb;source_row truss.record_source%ROWTYPE;kind char(1);metadata jsonb;selected_type truss.type_def%ROWTYPE;component_index int:=0;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF NOT attempt.complete OR attempt.writer_xid<>pg_current_xact_id() OR attempt.actor_oid<>truss.runtime_person(false) OR attempt.next_index<>1 THEN RAISE EXCEPTION 'current complete one-create import group required' USING ERRCODE='55000';END IF;
 IF original_record IS NULL OR octet_length(original_record) NOT BETWEEN 1 AND 2097152 OR (convert_from(original_record,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  OR load_id IS NULL OR octet_length(load_id) NOT BETWEEN 1 AND 4096 THEN RAISE EXCEPTION 'bounded original import record/load required' USING ERRCODE='22023';END IF;
 record:=convert_from(original_record,'UTF8')::jsonb;payload:=decode(record->'payload'->>'bytesBase64','base64');
 IF record-ARRAY['kind','identity','payload','payloadProfile']<>'{}'::jsonb OR (record->>'kind' IN ('object','edge')) IS NOT TRUE THEN RAISE EXCEPTION 'closed import record required' USING ERRCODE='22023';END IF;
 IF record->'payloadProfile' IS DISTINCT FROM truss.runtime_import_profiles()->'importPayloadProfile' OR encode(sha256(payload),'hex') IS DISTINCT FROM record->'payload'->>'sha256'
  OR octet_length(payload) NOT BETWEEN 1 AND 1048576 OR (convert_from(payload,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'exact original profiled payload required' USING ERRCODE='22023';END IF;
 value:=convert_from(payload,'UTF8')::jsonb;input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;operation:=input->'operations'->0;result:=attempt.results->0;
 IF value-ARRAY['interfaceVersion','kind','values','source',CASE record->>'kind' WHEN 'object' THEN 'ownership' ELSE 'orderKey' END]<>'{}'::jsonb THEN RAISE EXCEPTION 'closed profiled import payload required' USING ERRCODE='22023';END IF;
 IF (record->>'kind' IN ('object','edge')) IS NOT TRUE OR value->>'interfaceVersion' IS DISTINCT FROM 'truss-import-payload/0.1.0' OR value->>'kind' IS DISTINCT FROM record->>'kind' OR result->>'outcome'<>'created'
  OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e WHERE e.value->>'key'='x-load-id' AND e.value->'value'=jsonb_build_object('kind','string','text',load_id)) THEN
  RAISE EXCEPTION 'original import creation/load origin required' USING ERRCODE='22023';END IF;
 IF record->>'kind'='object' THEN
  kind:='o';
  IF operation->>'operation'<>'create_object' OR operation->>'typeDefinitionPin' IS DISTINCT FROM record->'identity'->'type'->>'definitionPin'
   OR operation->'values' IS DISTINCT FROM value->'values' OR operation->'ownership' IS DISTINCT FROM value->'ownership' THEN RAISE EXCEPTION 'original object payload creation required' USING ERRCODE='22023';END IF;
  SELECT * INTO STRICT selected_type FROM truss.type_def WHERE type_id=(result->'identity'->>'typeId')::int;
  metadata:=convert_from(truss.import_key_selection(selected_type.document_id,selected_type.module,selected_type.element,
   (SELECT release_id FROM truss.runtime_current_installation()),(SELECT release_sha256 FROM truss.runtime_current_installation())),'UTF8')::jsonb;
  IF (record->'identity')-ARRAY['operation','type','keyNumber','keyDefinitionPin','keyEncodingProfile','components']<>'{}'::jsonb OR record->'identity'->>'operation' IS DISTINCT FROM 'object_key' OR jsonb_typeof(record->'identity'->'components') IS DISTINCT FROM 'array' OR record->'identity'->'type' IS DISTINCT FROM metadata->'type' OR record->'identity'->>'keyNumber' IS DISTINCT FROM metadata->>'keyNumber'
   OR record->'identity'->>'keyDefinitionPin' IS DISTINCT FROM metadata->>'keyDefinitionPin' OR record->'identity'->'keyEncodingProfile' IS DISTINCT FROM metadata->'keyEncodingProfile'
   OR jsonb_array_length(record->'identity'->'components') IS DISTINCT FROM jsonb_array_length(metadata->'components') THEN RAISE EXCEPTION 'actual complete import primary key required' USING ERRCODE='22023';END IF;
  FOR entry IN SELECT v.value FROM jsonb_array_elements(record->'identity'->'components') v LOOP
   IF entry-ARRAY['propertyId','definitionPin','value']<>'{}'::jsonb OR jsonb_typeof(entry->'propertyId') IS DISTINCT FROM 'string' OR jsonb_typeof(entry->'definitionPin') IS DISTINCT FROM 'string' OR truss.valid_scalar_cell(entry->'value','string',false) IS NOT TRUE OR entry->>'propertyId' IS DISTINCT FROM metadata->'components'->component_index->>'propertyId'
    OR entry->>'definitionPin' IS DISTINCT FROM metadata->'components'->component_index->>'definitionPin'
    OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(value->'values') v WHERE v.value->>'name'=metadata->'components'->component_index->>'name' AND v.value->'value'=entry->'value') THEN
    RAISE EXCEPTION 'original primary field/payload agreement required' USING ERRCODE='22023';END IF;
   component_index:=component_index+1;
   IF NOT EXISTS(SELECT 1 FROM truss.object o WHERE o.id=(result->'identity'->>'id')::bigint AND o.type_id=(result->'identity'->>'typeId')::int AND o.props->(entry->>'propertyId')=entry->'value') THEN RAISE EXCEPTION 'import primary payload agreement required' USING ERRCODE='22023';END IF;
  END LOOP;
 ELSE
  kind:='e';PERFORM truss.runtime_edge_authorize(selected_attempt);
  IF operation->>'operation'<>'create_edge' OR operation->>'relationshipDefinitionPin' IS DISTINCT FROM record->'identity'->>'relationshipDefinitionPin'
   OR operation->'source' IS DISTINCT FROM jsonb_build_object('state','stored','identity',record->'identity'->'source') OR operation->'target' IS DISTINCT FROM jsonb_build_object('state','stored','identity',record->'identity'->'target')
   OR operation->'values' IS DISTINCT FROM value->'values' OR operation->'orderKey' IS DISTINCT FROM value->'orderKey' THEN RAISE EXCEPTION 'original edge payload creation required' USING ERRCODE='22023';END IF;
 END IF;
 IF value ? 'source' THEN
  IF (value->'source')-ARRAY['kind','entries']<>'{}'::jsonb OR value->'source'->>'kind' IS DISTINCT FROM 'map' OR jsonb_typeof(value->'source'->'entries') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'exact source map required' USING ERRCODE='22023';END IF;
  FOR entry IN SELECT v.value FROM jsonb_array_elements(value->'source'->'entries') v LOOP
   IF entry-ARRAY['key','value']<>'{}'::jsonb OR jsonb_typeof(entry->'key') IS DISTINCT FROM 'string' OR octet_length(entry->>'key') NOT BETWEEN 1 AND 4096 OR source_value ? (entry->>'key') OR truss.valid_scalar_cell(entry->'value') IS NOT TRUE
    OR entry->>'key' IN ('author','at','system') AND entry->'value'->>'kind' NOT IN ('string','null') THEN RAISE EXCEPTION 'lossless scalar source facts required' USING ERRCODE='22023';END IF;
   source_value:=source_value||jsonb_build_object(entry->>'key',CASE entry->'value'->>'kind' WHEN 'string' THEN entry->'value'->'text' WHEN 'null' THEN 'null'::jsonb WHEN 'boolean' THEN entry->'value'->'value' ELSE entry->'value' END);
  END LOOP;
 END IF;
 INSERT INTO truss.record_source(entity_kind,entity_id,load_id,source) VALUES(kind,(result->'identity'->>'id')::bigint,load_id,source_value) RETURNING * INTO source_row;
 IF source_row.entity_kind IS DISTINCT FROM kind OR source_row.entity_id IS DISTINCT FROM (result->'identity'->>'id')::bigint
  OR source_row.load_id IS DISTINCT FROM load_id OR source_row.source IS DISTINCT FROM source_value THEN RAISE EXCEPTION 'payload-derived import provenance required' USING ERRCODE='55000';END IF;
 INSERT INTO truss.runtime_import_source VALUES(kind,source_row.entity_id,selected_attempt,attempt.writer_xid,original_record,to_jsonb(source_row));
 PERFORM truss.runtime_module_writer(result->'identity'->'owner'->>'documentId',result->'identity'->'owner'->>'moduleId');
 RETURN convert_to(to_jsonb(source_row)::text,'UTF8');
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
  OR attempt.next_index<>1 OR attempt.results->0->>'outcome'<>'created' OR attempt.results->0->'identity'->>'id'<>ledger.entity_id::text THEN RAISE EXCEPTION 'original pending import creation required' USING ERRCODE='55000';END IF;
 SELECT to_jsonb(s) INTO actual FROM truss.record_source s WHERE entity_kind=ledger.entity_kind AND entity_id=ledger.entity_id;
 IF actual IS DISTINCT FROM ledger.expected_source THEN RAISE EXCEPTION 'immutable exact original import source required' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_import_source_commit() FROM PUBLIC;
CREATE CONSTRAINT TRIGGER runtime_import_source_commit AFTER INSERT ON truss.runtime_import_source DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_import_source_commit();
CREATE CONSTRAINT TRIGGER runtime_record_source_commit AFTER INSERT ON truss.record_source DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_import_source_commit();
ALTER TABLE truss.runtime_import_source ENABLE ALWAYS TRIGGER runtime_import_source_commit;
ALTER TABLE truss.record_source ENABLE ALWAYS TRIGGER runtime_record_source_commit;

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
DECLARE context jsonb;identity jsonb;relation truss.rel_def%ROWTYPE;source_definition truss.type_def%ROWTYPE;target_definition truss.type_def%ROWTYPE;key text;edge_row truss.edge%ROWTYPE;result jsonb;
BEGIN
 context:=convert_from(truss.import_context(expected_release,expected_digest),'UTF8')::jsonb;
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 65536 OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded exact edge import identity required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 IF identity-ARRAY['relationshipDefinitionPin','source','target']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge import identity required' USING ERRCODE='22023';END IF;
 relation:=truss.runtime_operation_relationship(jsonb_build_object('operation','create_edge','relationshipDefinitionPin',identity->>'relationshipDefinitionPin'),'[]',0);
 PERFORM truss.runtime_module_writer(relation.document_id,relation.module);source_definition:=truss.runtime_condition_type(identity->'source');target_definition:=truss.runtime_condition_type(identity->'target');
 IF NOT truss.runtime_can_read(source_definition.document_id,source_definition.module) OR NOT truss.runtime_can_read(target_definition.document_id,target_definition.module) THEN RAISE EXCEPTION 'edge endpoint readers required' USING ERRCODE='42501';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=source_definition.type_id AND target_type=target_definition.type_id) THEN RAISE EXCEPTION 'admitted edge endpoint pair required' USING ERRCODE='22023';END IF;
 PERFORM 1 FROM truss.object WHERE id=(identity->'source'->>'id')::bigint AND type_id=source_definition.type_id FOR UPDATE NOWAIT;
 PERFORM 1 FROM truss.object WHERE id=(identity->'target'->>'id')::bigint AND type_id=target_definition.type_id FOR UPDATE NOWAIT;
 key:=truss.runtime_edge_business_key(relation.rel_type_id,identity->'source',identity->'target');PERFORM truss.runtime_lock_edge_business_key(key);
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
DECLARE identity jsonb;selected truss.type_def%ROWTYPE;metadata bytea;
BEGIN
 IF original_identity IS NULL OR octet_length(original_identity) NOT BETWEEN 1 AND 1048576 OR (convert_from(original_identity,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded unique primary identity required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 IF jsonb_typeof(identity->'type'->'typeId') IS DISTINCT FROM 'string' OR identity->'type'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
  OR length(identity->'type'->>'typeId')=10 AND (identity->'type'->>'typeId') COLLATE "C">'2147483647' THEN RAISE EXCEPTION 'exact import type ID required' USING ERRCODE='22023';END IF;
 SELECT * INTO selected FROM truss.type_def WHERE type_id=(identity->'type'->>'typeId')::int AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'accepted import type required' USING ERRCODE='22023';END IF;
 metadata:=truss.import_key_selection(selected.document_id,selected.module,selected.element,expected_release,expected_digest);
 IF identity->'type' IS DISTINCT FROM convert_from(metadata,'UTF8')::jsonb->'type' THEN RAISE EXCEPTION 'original qualified import type required' USING ERRCODE='22023';END IF;
 RETURN metadata;
END;
$$;
REVOKE ALL ON FUNCTION truss.import_identity_key_selection(bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.import_report_record_authority(original_identity bytea,kind text,expected_release text,expected_digest text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE identity jsonb;relation truss.rel_def%ROWTYPE;source_definition truss.type_def%ROWTYPE;target_definition truss.type_def%ROWTYPE;
BEGIN
 IF kind='object' THEN PERFORM truss.import_identity_key_selection(original_identity,expected_release,expected_digest);RETURN;END IF;
 IF kind<>'edge' THEN RAISE EXCEPTION 'selected report record required' USING ERRCODE='22023';END IF;
 identity:=convert_from(original_identity,'UTF8')::jsonb;
 relation:=truss.runtime_operation_relationship(jsonb_build_object('operation','create_edge','relationshipDefinitionPin',identity->>'relationshipDefinitionPin'),'[]',0);
 PERFORM truss.runtime_module_writer(relation.document_id,relation.module);
 source_definition:=truss.runtime_condition_type(identity->'source');target_definition:=truss.runtime_condition_type(identity->'target');
 IF NOT truss.runtime_can_read(source_definition.document_id,source_definition.module) OR NOT truss.runtime_can_read(target_definition.document_id,target_definition.module) THEN RAISE EXCEPTION 'current report endpoint readers required' USING ERRCODE='42501';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.import_report_record_authority(bytea,text,text,text) FROM PUBLIC;
