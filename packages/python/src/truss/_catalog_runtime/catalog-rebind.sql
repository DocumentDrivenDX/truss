-- Unintegrated source checkpoint: not loaded by _release or selected by an API.
-- Registration-owned retained-value transitions; never ordinary mutation attempts.
CREATE TABLE truss.runtime_catalog_rebind_transition (
 transition_id bigint PRIMARY KEY DEFAULT nextval('truss.runtime_object_transition_seq'),
 registration_id uuid NOT NULL REFERENCES truss.catalog_registration_request(registration_id) DEFERRABLE INITIALLY DEFERRED,
 writer_xid xid8 NOT NULL,actor_oid oid NOT NULL,revision int NOT NULL REFERENCES truss.schema_rev(rev),
 object_id bigint NOT NULL,type_id int NOT NULL,before_object jsonb NOT NULL,after_object jsonb NOT NULL,
 after_keys jsonb NOT NULL,journal jsonb NOT NULL,effects jsonb NOT NULL,
 UNIQUE(registration_id,object_id,type_id),
 CHECK(jsonb_typeof(journal)='array' AND jsonb_array_length(journal)>1),
 CHECK(jsonb_typeof(effects)='array' AND jsonb_array_length(effects)>0));
CREATE INDEX runtime_catalog_rebind_owner ON truss.runtime_catalog_rebind_transition(object_id,type_id,transition_id DESC);
CREATE TRIGGER runtime_catalog_rebind_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.runtime_catalog_rebind_transition
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_catalog_rebind_transition FROM PUBLIC;

-- Planned basis is produced and checked within native acceptance. No consumer grant.
CREATE FUNCTION truss.catalog_rebind_definition(selected_kind text,selected_type int,selected_number int,planned_basis jsonb)
RETURNS TABLE(definition_pin text,original_fragment bytea,original_pointer text,document_id text,module_id text,element_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE basis jsonb;definition jsonb; archive truss.schema_doc%ROWTYPE; native_type truss.type_def%ROWTYPE;
 source_module text;source_element text;module_json json;module_index int;element_json json;element_index int;
 key_json json;key_index int;fragment json;pointer text;pin_input text;
BEGIN
 IF planned_basis IS NULL THEN
  SELECT * INTO STRICT native_type FROM truss.type_def WHERE type_id=selected_type AND NOT provisional AND retired_rev IS NULL;
 ELSE
  basis:=planned_basis;
  SELECT * INTO STRICT native_type FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t WHERE t.type_id=selected_type;
 END IF;
 IF selected_kind='type' THEN
  definition:=to_jsonb(native_type);source_module:=native_type.module;source_element:=native_type.element;
 ELSIF selected_kind='property' THEN
  IF planned_basis IS NULL THEN
   SELECT to_jsonb(p),p.declaration_module,p.element INTO STRICT definition,source_module,source_element FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=selected_number AND p.retired_rev IS NULL;
  ELSE
   SELECT to_jsonb(p),p.declaration_module,p.element INTO STRICT definition,source_module,source_element FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=selected_type AND p.prop_id=selected_number;
  END IF;
 ELSIF selected_kind='key' THEN
  IF planned_basis IS NULL THEN
   SELECT to_jsonb(k) INTO STRICT definition FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_num=selected_number AND k.retired_rev IS NULL;
  ELSE
   SELECT to_jsonb(k) INTO STRICT definition FROM jsonb_populate_recordset(NULL::truss.key_def,basis->'key_def') k WHERE k.type_id=selected_type AND k.key_num=selected_number;
  END IF;
  source_module:=native_type.module;source_element:=native_type.element;
 ELSE RAISE EXCEPTION 'supported definition kind required' USING ERRCODE='22023'; END IF;
 IF definition->>'definition_source_kind'<>'accepted_document' OR (definition->>'definition_rev')::int<1 THEN
  RAISE EXCEPTION 'original accepted definition source required' USING ERRCODE='0A000'; END IF;
 SELECT * INTO STRICT archive FROM truss.schema_doc d WHERE d.rev=(definition->>'definition_rev')::int AND d.ord=(definition->>'definition_doc_ord')::int
  AND d.doc_id=definition->>'definition_document_id';
 SELECT m.value,m.ordinality::int-1 INTO STRICT module_json,module_index
  FROM json_array_elements(archive.document::json->'modules') WITH ORDINALITY m WHERE m.value->>'id'=source_module;
 SELECT e.value,e.ordinality::int-1 INTO STRICT element_json,element_index
  FROM json_array_elements(module_json->'elements') WITH ORDINALITY e WHERE e.value->>'id'=source_element;
 fragment:=element_json;pointer:='/modules/'||module_index||'/elements/'||element_index;
 IF selected_kind='key' THEN
  SELECT k.value,k.ordinality::int-1 INTO STRICT key_json,key_index
   FROM json_array_elements(element_json->'keys') WITH ORDINALITY k WHERE k.value->>'id'=definition->>'key_id';
  fragment:=key_json;pointer:=pointer||'/keys/'||key_index;
 END IF;
 original_fragment:=convert_to(fragment::text,'UTF8');original_pointer:=pointer;
 pin_input:='['||archive.rev||','||archive.ord||',"'||archive.content_sha256||'","'||pointer
  ||'",{"identity":"truss-original-json-definition","sha256":"08c2ec8c520b39ded40f270be0b26812db1d240d5bac1a00339b437200a2f58d","version":"0.1"},"'
  ||encode(sha256(original_fragment),'hex')||'"]';
 definition_pin:=encode(sha256(convert_to(pin_input,'UTF8')),'hex');
 document_id:=native_type.document_id;module_id:=native_type.module;element_id:=native_type.element;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_definition(text,int,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_rebind_history(object_image jsonb,identity jsonb,planned_basis jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE properties jsonb:='[]';retained jsonb;property truss.prop_def%ROWTYPE;pin record;basis jsonb;written_revision int:=(object_image->>'rev')::int;
BEGIN
 basis:=planned_basis;
 SELECT * INTO STRICT pin FROM truss.catalog_rebind_definition('type',(object_image->>'type_id')::int,NULL,planned_basis);
 identity:=jsonb_set(identity,'{definitionPin}',to_jsonb(pin.definition_pin));
 FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=(object_image->>'type_id')::int ORDER BY prop_id LOOP
  IF object_image->'props' ? property.prop_id::text THEN
   SELECT * INTO STRICT pin FROM truss.catalog_rebind_definition('property',property.type_id,property.prop_id,planned_basis);
   properties:=properties||jsonb_build_array(jsonb_build_object('propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,'value',object_image->'props'->property.prop_id::text));
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',key,'value',value) ORDER BY key COLLATE "C"),'[]'::jsonb) INTO retained FROM jsonb_each(coalesce(nullif(object_image->'retained','null'::jsonb),'{}'));
 RETURN jsonb_build_object('interfaceVersion','truss-history-record/0.1.0','kind','object','identity',identity,
  'recordVersion',object_image->>'ver','catalogRevision',object_image->>'rev',
  'createdAt',to_char((object_image->>'created_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'updatedAt',to_char((object_image->>'updated_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'properties',properties,'retained',retained,'ownership',jsonb_build_object('state','rootless'));
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_history(jsonb,jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_rebind_objects(request truss.catalog_registration_request,planned_basis jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE object_row truss.object%ROWTYPE;original jsonb;after_image jsonb;identity jsonb;before_record jsonb;after_record jsonb;
 owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;pin record;installation truss.catalog_runtime_installation%ROWTYPE;
 effects jsonb;events jsonb;event jsonb;journals jsonb;journal truss.journal%ROWTYPE;keys jsonb;group_digest text;property_count int;object_count int:=0;
BEGIN
 IF request.actor_oid IS DISTINCT FROM truss.catalog_actor() OR request.actor_name IS DISTINCT FROM session_user::text
  OR request.writer_xid IS DISTINCT FROM pg_current_xact_id() OR request.registration_id IS NULL THEN
  RAISE EXCEPTION 'current original catalog registration required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 FOR object_row IN SELECT o.* FROM truss.object o WHERE EXISTS(SELECT 1 FROM truss.prop_def p
  WHERE p.type_id=o.type_id AND p.since_rev=request.revision AND o.retained ? p.name) ORDER BY o.type_id,o.id FOR UPDATE LOOP
  object_count:=object_count+1;
  IF object_count>10000 OR object_row.ver=9223372036854775807 THEN RAISE EXCEPTION 'bounded catalog rebinding required' USING ERRCODE='54000';END IF;
  SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=object_row.type_id;
  PERFORM truss.runtime_module_writer(owner.document_id,owner.module);
  IF truss.runtime_object_values_readable(object_row.type_id) IS NOT TRUE THEN RAISE EXCEPTION 'current rebind interpretation reader required' USING ERRCODE='42501';END IF;
  original:=to_jsonb(object_row);effects:='[]';events:='[]';journals:='[]';property_count:=0;
  SELECT definition_pin INTO STRICT pin FROM truss.catalog_rebind_definition('type',object_row.type_id,NULL,planned_basis);
  identity:=jsonb_build_object('id',object_row.id::text,'typeId',object_row.type_id::text,
   'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module));
  before_record:=truss.runtime_object_history(original,identity);
  FOR property IN SELECT * FROM truss.prop_def p WHERE p.type_id=object_row.type_id AND p.since_rev=request.revision
   AND object_row.retained ? p.name ORDER BY p.prop_id LOOP
   property_count:=property_count+1;
   IF property_count>127 OR property.nullability IS DISTINCT FROM 'absent-allowed' OR object_row.props ? property.prop_id::text
    OR EXISTS(SELECT 1 FROM truss.key_def k WHERE k.type_id=property.type_id AND property.prop_id=ANY(k.prop_ids))
    OR truss.valid_property_value(object_row.retained->property.name,property) IS NOT TRUE THEN
    RAISE EXCEPTION 'valid absent non-key catalog rebind destination required' USING ERRCODE='22023';END IF;
   SELECT definition_pin INTO STRICT pin FROM truss.catalog_rebind_definition('property',property.type_id,property.prop_id,planned_basis);
   effects:=effects||jsonb_build_array(jsonb_build_object('propertyId',property.prop_id::text,'originalName',property.name,
    'definitionPin',pin.definition_pin,'value',object_row.retained->property.name));
   events:=events||jsonb_build_array(jsonb_build_object('operation','rebind','propertyId',property.prop_id::text,
    'retainedName',property.name,'beforeDefinitionContext',before_record->'identity'->>'definitionPin','afterDefinitionPin',pin.definition_pin,
    'retainedBefore',jsonb_build_object('present',true,'value',object_row.retained->property.name),
    'retainedAfter',jsonb_build_object('present',false),'propertyBefore',jsonb_build_object('present',false),
    'propertyAfter',jsonb_build_object('present',true,'value',object_row.retained->property.name)));
   object_row.props:=object_row.props||jsonb_build_object(property.prop_id::text,object_row.retained->property.name);
   object_row.retained:=object_row.retained-property.name;
  END LOOP;
  IF octet_length(convert_to(jsonb_build_object('props',object_row.props,'retained',object_row.retained)::text,'UTF8'))>1048576 THEN
   RAISE EXCEPTION 'bounded rebound object values required' USING ERRCODE='54000';END IF;
  object_row.retained:=nullif(object_row.retained,'{}'::jsonb);object_row.ver:=object_row.ver+1;
  object_row.rev:=request.revision;object_row.updated_at:=clock_timestamp();after_image:=to_jsonb(object_row);
  after_record:=truss.catalog_rebind_history(after_image,identity,planned_basis);
  events:=events||jsonb_build_array(jsonb_build_object('operation','metadata','before',before_record,'after',after_record));
  FOR event_index IN 0..jsonb_array_length(events)-1 LOOP
   event:=(events->event_index)||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal',
    'historyProfile','truss-native-catalog-rebind/0.1','sourceEpoch',installation.source_epoch::text,
    'xid',request.writer_xid::text,'seq',nextval('truss.journal_seq')::text,
    'identity',identity,'eventVersion',object_row.ver::text,'eventCatalogRevision',request.revision::text,
    'origin',jsonb_build_object('asserted',convert_from(request.origin_bytes,'UTF8')::jsonb,'databaseRole',session_user::text));
   events:=jsonb_set(events,ARRAY[event_index::text],event);
  END LOOP;
  group_digest:=encode(sha256(convert_to(events::text,'UTF8')),'hex');
  FOR event IN SELECT value FROM jsonb_array_elements(events) LOOP
   event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0',
    'eventCount',jsonb_array_length(events)::text,'orderedEventDigest',group_digest));
   journal.seq:=(event->>'seq')::bigint;journal.at:=clock_timestamp();journal.xid:=request.writer_xid;
   journal.entity_kind:='o';journal.entity_id:=object_row.id;journal.entity_type:=object_row.type_id;journal.ver:=object_row.ver;
   journal.op:=event->>'operation';journal.prop_id:=(event->>'propertyId')::int;journal.old_value:=event->'retainedBefore'->'value';
   journal.new_value:=truss.runtime_exact_wrapper('event',convert_to(event::text,'UTF8'));journal.rev:=request.revision;
   journal.origin:=truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8'));
   INSERT INTO truss.journal SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(journal))).*;
   journals:=journals||jsonb_build_array(to_jsonb(journal));
  END LOOP;
  SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]'::jsonb) INTO keys FROM truss.object_key_bucket k
   WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id;
  UPDATE truss.object SET props=object_row.props,retained=object_row.retained,ver=object_row.ver,rev=object_row.rev,updated_at=object_row.updated_at
   WHERE id=object_row.id AND type_id=object_row.type_id;
  INSERT INTO truss.runtime_catalog_rebind_transition(registration_id,writer_xid,actor_oid,revision,object_id,type_id,before_object,after_object,after_keys,journal,effects)
   VALUES(request.registration_id,request.writer_xid,request.actor_oid,request.revision,object_row.id,object_row.type_id,original,after_image,keys,journals,effects);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_objects(truss.catalog_registration_request,jsonb) FROM PUBLIC;
