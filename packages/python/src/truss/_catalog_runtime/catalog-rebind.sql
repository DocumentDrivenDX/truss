-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Native61 candidate: storage prefix is retained source; install uses the UMF owner export.
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
CREATE INDEX runtime_catalog_rebind_writer ON truss.runtime_catalog_rebind_transition(writer_xid);
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
DECLARE properties jsonb;property_buffer jsonb[]:=ARRAY[]::jsonb[];retained jsonb;ownership jsonb:='{"state":"rootless"}';property truss.prop_def%ROWTYPE;pin record;basis jsonb;written_revision int:=(object_image->>'rev')::int;
BEGIN
 basis:=planned_basis;
 SELECT * INTO STRICT pin FROM truss.catalog_rebind_definition('type',(object_image->>'type_id')::int,NULL,planned_basis);
 identity:=jsonb_set(identity,'{definitionPin}',to_jsonb(pin.definition_pin));
 FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=(object_image->>'type_id')::int ORDER BY prop_id LOOP
  IF object_image->'props' ? property.prop_id::text THEN
   SELECT * INTO STRICT pin FROM truss.catalog_rebind_definition('property',property.type_id,property.prop_id,planned_basis);
   property_buffer:=array_append(property_buffer,jsonb_build_object('propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,'value',object_image->'props'->property.prop_id::text));
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',key,'value',value) ORDER BY key COLLATE "C"),'[]'::jsonb) INTO retained FROM jsonb_each(coalesce(nullif(object_image->'retained','null'::jsonb),'{}'));
 IF (object_image->>'root_id' IS NULL) IS DISTINCT FROM (object_image->>'root_type' IS NULL) THEN
  RAISE EXCEPTION 'complete rebound root pair required' USING ERRCODE='55000';END IF;
 IF object_image->>'root_id' IS NOT NULL THEN
  SELECT * INTO STRICT pin FROM truss.catalog_rebind_definition('type',(object_image->>'root_type')::int,NULL,planned_basis);
  ownership:=jsonb_build_object('state','owned','root',jsonb_build_object(
   'id',object_image->>'root_id','typeId',object_image->>'root_type','definitionPin',pin.definition_pin,
   'owner',jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id)));
 END IF;
 properties:=to_jsonb(property_buffer);
 RETURN jsonb_build_object('interfaceVersion','truss-history-record/0.1.0','kind','object','identity',identity,
  'recordVersion',object_image->>'ver','catalogRevision',object_image->>'rev',
  'createdAt',to_char((object_image->>'created_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'updatedAt',to_char((object_image->>'updated_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'properties',properties,'retained',retained,'ownership',ownership);
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_history(jsonb,jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_rebind_objects(request truss.catalog_registration_request,planned_basis jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE object_row truss.object%ROWTYPE;original jsonb;after_image jsonb;identity jsonb;before_record jsonb;after_record jsonb;
 owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;pin record;installation truss.catalog_runtime_installation%ROWTYPE;
 observed_after jsonb;effects jsonb;effects_buffer jsonb[];events jsonb;event jsonb;event_buffer jsonb[];decorated_events jsonb[];journals jsonb;journal_buffer jsonb[];journal truss.journal%ROWTYPE;keys jsonb;group_digest text;property_count int;object_count int:=0;selected_profile text;
BEGIN
 IF request.actor_oid IS DISTINCT FROM truss.catalog_actor() OR request.actor_name IS DISTINCT FROM session_user::text
  OR request.writer_xid IS DISTINCT FROM pg_current_xact_id() OR request.registration_id IS NULL THEN
  RAISE EXCEPTION 'current original catalog registration required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 selected_profile:=CASE WHEN EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.since_rev=request.revision AND p.cardinality IN ('array','map') AND p.item ? 'descendants')
  THEN 'truss-native-catalog-rebind/0.4' WHEN EXISTS(
  SELECT 1 FROM truss.key_def k CROSS JOIN LATERAL unnest(k.prop_ids) member(prop_id)
  JOIN truss.prop_def p ON p.type_id=k.type_id AND p.prop_id=member.prop_id
  WHERE k.since_rev=request.revision AND NOT k.is_primary AND p.since_rev=request.revision)
  THEN 'truss-native-catalog-rebind/0.3' ELSE 'truss-native-catalog-rebind/0.2' END;
 FOR object_row IN SELECT o.* FROM truss.object o WHERE EXISTS(SELECT 1 FROM truss.prop_def p
  WHERE p.type_id=o.type_id AND p.since_rev=request.revision AND o.retained ? p.name) ORDER BY o.type_id,o.id FOR UPDATE LOOP
  object_count:=object_count+1;
  IF object_count>10000 OR object_row.ver=9223372036854775807 THEN RAISE EXCEPTION 'bounded catalog rebinding required' USING ERRCODE='54000';END IF;
  SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=object_row.type_id;
  PERFORM truss.runtime_module_writer(owner.document_id,owner.module);
  IF truss.runtime_object_values_readable(object_row.type_id) IS NOT TRUE THEN RAISE EXCEPTION 'current rebind interpretation reader required' USING ERRCODE='42501';END IF;
  PERFORM truss.runtime_history_ownership(jsonb_build_object(
   'identity',jsonb_build_object('id',object_row.id::text,'typeId',object_row.type_id::text),
   'catalogRevision',object_row.rev,'ownership',truss.runtime_object_ownership_at(to_jsonb(object_row))));
  original:=to_jsonb(object_row);effects_buffer:=ARRAY[]::jsonb[];event_buffer:=ARRAY[]::jsonb[];decorated_events:=ARRAY[]::jsonb[];journal_buffer:=ARRAY[]::jsonb[];property_count:=0;
  SELECT definition_pin INTO STRICT pin FROM truss.catalog_rebind_definition('type',object_row.type_id,NULL,planned_basis);
  identity:=jsonb_build_object('id',object_row.id::text,'typeId',object_row.type_id::text,
   'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module));
  before_record:=truss.runtime_object_history(original,identity);
  FOR property IN SELECT * FROM truss.prop_def p WHERE p.type_id=object_row.type_id AND p.since_rev=request.revision
   AND object_row.retained ? p.name ORDER BY p.prop_id LOOP
   property_count:=property_count+1;
   IF property_count>127 OR property.nullability NOT IN ('required','absent-allowed') OR object_row.props ? property.prop_id::text
    OR EXISTS(SELECT 1 FROM truss.key_def k WHERE k.type_id=property.type_id AND property.prop_id=ANY(k.prop_ids)
     AND (k.since_rev IS DISTINCT FROM request.revision OR k.is_primary IS DISTINCT FROM false
      OR property.nullability IS DISTINCT FROM 'required' OR property.cardinality IS DISTINCT FROM 'one'
      OR property.scalar_type NOT IN ('string','integer','decimal','boolean','binary')))
    OR truss.valid_property_definition(property) IS NOT TRUE OR truss.valid_property_value(object_row.retained->property.name,property) IS NOT TRUE THEN
    RAISE EXCEPTION 'valid absent catalog rebind destination required' USING ERRCODE='22023';END IF;
   SELECT definition_pin INTO STRICT pin FROM truss.catalog_rebind_definition('property',property.type_id,property.prop_id,planned_basis);
   effects_buffer:=array_append(effects_buffer,jsonb_build_object('propertyId',property.prop_id::text,'originalName',property.name,
    'definitionPin',pin.definition_pin,'value',object_row.retained->property.name));
   event_buffer:=array_append(event_buffer,jsonb_build_object('operation','rebind','propertyId',property.prop_id::text,
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
  event_buffer:=array_append(event_buffer,jsonb_build_object('operation','metadata','before',before_record,'after',after_record));
  FOR event_index IN 1..cardinality(event_buffer) LOOP
   event:=event_buffer[event_index]||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal',
    'historyProfile',selected_profile,'sourceEpoch',installation.source_epoch::text,
    'xid',request.writer_xid::text,'seq',nextval('truss.journal_seq')::text,
    'identity',identity,'eventVersion',object_row.ver::text,'eventCatalogRevision',request.revision::text,
    'origin',jsonb_build_object('asserted',convert_from(request.origin_bytes,'UTF8')::jsonb,'databaseRole',session_user::text));
   decorated_events:=array_append(decorated_events,event);
  END LOOP;
  events:=to_jsonb(decorated_events);effects:=to_jsonb(effects_buffer);
  group_digest:=encode(sha256(convert_to(events::text,'UTF8')),'hex');
  FOR event IN SELECT value FROM jsonb_array_elements(events) LOOP
   event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0',
    'eventCount',jsonb_array_length(events)::text,'orderedEventDigest',group_digest));
   journal.seq:=(event->>'seq')::bigint;journal.at:=clock_timestamp();journal.xid:=request.writer_xid;
   journal.entity_kind:='o';journal.entity_id:=object_row.id;journal.entity_type:=object_row.type_id;journal.ver:=object_row.ver;
   journal.op:=event->>'operation';journal.prop_id:=(event->>'propertyId')::int;journal.old_value:=NULL;
   journal.new_value:=truss.runtime_exact_wrapper('event',convert_to(event::text,'UTF8'));journal.rev:=request.revision;
   journal.origin:=truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8'));
   INSERT INTO truss.journal SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(journal))).*;
   journal_buffer:=array_append(journal_buffer,to_jsonb(journal));
  END LOOP;
  journals:=to_jsonb(journal_buffer);
  SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]'::jsonb) INTO keys FROM truss.object_key_bucket k
   WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id;
  UPDATE truss.object o SET props=object_row.props,retained=object_row.retained,ver=object_row.ver,rev=object_row.rev,updated_at=object_row.updated_at
   WHERE id=object_row.id AND type_id=object_row.type_id RETURNING to_jsonb(o) INTO observed_after;
  IF NOT FOUND OR observed_after IS DISTINCT FROM after_image THEN RAISE EXCEPTION 'exact applied catalog rebind image required' USING ERRCODE='55000';END IF;
  INSERT INTO truss.runtime_catalog_rebind_transition(registration_id,writer_xid,actor_oid,revision,object_id,type_id,before_object,after_object,after_keys,journal,effects)
   VALUES(request.registration_id,request.writer_xid,request.actor_oid,request.revision,object_row.id,object_row.type_id,original,after_image,keys,journals,effects);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_objects(truss.catalog_registration_request,jsonb) FROM PUBLIC;

-- Check retained candidates against the actual native planned property definition.
CREATE FUNCTION truss.catalog_rebind_violations(planned_basis jsonb,revision int) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE property truss.prop_def%ROWTYPE;owner truss.type_def%ROWTYPE;object_row truss.object%ROWTYPE;affected bigint;missing bigint;violations jsonb;violation_buffer jsonb[]:=ARRAY[]::jsonb[];owner_index jsonb;
BEGIN
 SELECT coalesce(jsonb_object_agg(t.value->>'type_id',t.value),'{}'::jsonb) INTO owner_index FROM jsonb_array_elements(planned_basis->'type_def') t;
 FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,planned_basis->'prop_def') p WHERE p.since_rev=revision LOOP
  SELECT * INTO STRICT owner FROM jsonb_populate_record(NULL::truss.type_def,owner_index->property.type_id::text) t WHERE t.type_id=property.type_id;
  IF NOT EXISTS(SELECT 1 FROM truss.type_def WHERE type_id=property.type_id) THEN CONTINUE;END IF;
  IF truss.runtime_can_read(owner.document_id,owner.module) IS NOT TRUE
   OR truss.runtime_can_read(owner.document_id,property.declaration_module) IS NOT TRUE
   OR property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable(property.item) IS NOT TRUE THEN
   RAISE EXCEPTION 'original candidate owner/property/item readers required' USING ERRCODE='42501';END IF;
  IF truss.valid_property_definition(property) IS NOT TRUE THEN RAISE EXCEPTION 'supported planned rebind property required' USING ERRCODE='0A000';END IF;
  FOR object_row IN SELECT o.* FROM truss.object o WHERE o.type_id=property.type_id
   AND (o.root_id IS NOT NULL OR o.root_type IS NOT NULL)
   AND (property.nullability='required' OR coalesce(o.retained ? property.name,false)) LOOP
  PERFORM truss.runtime_history_ownership(jsonb_build_object(
   'identity',jsonb_build_object('id',object_row.id::text,'typeId',object_row.type_id::text),
   'catalogRevision',object_row.rev,'ownership',truss.runtime_object_ownership_at(to_jsonb(object_row))));
  END LOOP;
  SELECT count(*) INTO missing FROM truss.object o WHERE o.type_id=property.type_id AND property.nullability='required'
   AND (coalesce(o.retained ? property.name,false) IS NOT TRUE OR o.retained->property.name='{"kind":"null"}'::jsonb);
  IF missing>0 THEN
   violation_buffer:=array_append(violation_buffer,jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module,
    'recordId',owner.element,'fieldModuleId',property.declaration_module,'fieldId',property.element,
    'rule','property.required','affectedObjectCount',missing::text));
  END IF;
  SELECT count(*) INTO affected FROM truss.object o WHERE o.type_id=property.type_id AND coalesce(o.retained ? property.name,false)
   AND NOT (property.nullability='required' AND o.retained->property.name='{"kind":"null"}'::jsonb)
   AND (property.nullability NOT IN ('required','absent-allowed') OR o.props ? property.prop_id::text
    OR EXISTS(SELECT 1 FROM jsonb_populate_recordset(NULL::truss.key_def,planned_basis->'key_def') k WHERE k.type_id=property.type_id AND property.prop_id=ANY(k.prop_ids)
     AND (k.since_rev IS DISTINCT FROM revision OR k.is_primary IS DISTINCT FROM false
      OR property.nullability IS DISTINCT FROM 'required' OR property.cardinality IS DISTINCT FROM 'one'
      OR property.scalar_type NOT IN ('string','integer','decimal','boolean','binary')))
    OR truss.valid_property_value(o.retained->property.name,property) IS NOT TRUE);
  IF truss.runtime_can_read(owner.document_id,owner.module) IS NOT TRUE
   OR truss.runtime_can_read(owner.document_id,property.declaration_module) IS NOT TRUE
   OR property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable(property.item) IS NOT TRUE THEN
   RAISE EXCEPTION 'original candidate owner/property/item readers required' USING ERRCODE='42501';END IF;
  IF affected>0 THEN
   violation_buffer:=array_append(violation_buffer,jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module,
    'recordId',owner.element,'fieldModuleId',property.declaration_module,'fieldId',property.element,
    'rule','property.rebind_value','affectedObjectCount',affected::text));
  END IF;
 END LOOP;
 FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,planned_basis->'prop_def') p WHERE p.since_rev=revision AND EXISTS(SELECT 1 FROM truss.type_def t WHERE t.type_id=p.type_id) LOOP
  SELECT * INTO STRICT owner FROM jsonb_populate_record(NULL::truss.type_def,owner_index->property.type_id::text) t WHERE t.type_id=property.type_id;
  IF truss.runtime_can_read(owner.document_id,owner.module) IS NOT TRUE
   OR truss.runtime_can_read(owner.document_id,property.declaration_module) IS NOT TRUE
   OR property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable(property.item) IS NOT TRUE THEN
   RAISE EXCEPTION 'original candidate owner/property/item readers required' USING ERRCODE='42501';END IF;
  FOR object_row IN SELECT o.* FROM truss.object o WHERE o.type_id=property.type_id
   AND (o.root_id IS NOT NULL OR o.root_type IS NOT NULL)
   AND (property.nullability='required' OR coalesce(o.retained ? property.name,false)) LOOP
  PERFORM truss.runtime_history_ownership(jsonb_build_object(
   'identity',jsonb_build_object('id',object_row.id::text,'typeId',object_row.type_id::text),
   'catalogRevision',object_row.rev,'ownership',truss.runtime_object_ownership_at(to_jsonb(object_row))));
  END LOOP;
 END LOOP;
 violations:=to_jsonb(violation_buffer);
 IF violations='[]'::jsonb THEN RETURN NULL;END IF;
 RETURN convert_to(violations::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_violations(jsonb,int) FROM PUBLIC;

-- Reports now contain original data: registrar authority alone cannot disclose it.
-- Original definitions survive object deletion and later catalog evolution.
CREATE FUNCTION truss.catalog_rebind_transition_reader(transition truss.runtime_catalog_rebind_transition,planned_basis jsonb DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;basis jsonb;property_id text;image jsonb;
BEGIN
  basis:=coalesce(planned_basis,truss.catalog_all_expected_records(transition.revision));
  SELECT * INTO STRICT owner FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t WHERE t.type_id=transition.type_id;
  IF truss.runtime_can_read(owner.document_id,owner.module) IS NOT TRUE THEN RAISE EXCEPTION 'current original rebind owner reader required' USING ERRCODE='42501';END IF;
  FOR image IN SELECT value FROM jsonb_array_elements(jsonb_build_array(transition.before_object,transition.after_object)) LOOP
   PERFORM truss.runtime_history_ownership(jsonb_build_object(
    'identity',jsonb_build_object('id',image->>'id','typeId',image->>'type_id'),
    'catalogRevision',image->'rev','ownership',truss.runtime_object_ownership_at(image)));
  END LOOP;
  FOR property_id IN SELECT jsonb_object_keys(transition.before_object->'props') LOOP
   PERFORM truss.runtime_history_property(transition.type_id,property_id::int,(transition.before_object->>'rev')::int,
    (SELECT definition_pin FROM truss.runtime_owned_definition_metadata('property',transition.type_id,property_id::int,(transition.before_object->>'rev')::int)));
  END LOOP;
  FOR property_id IN SELECT jsonb_object_keys(transition.after_object->'props') LOOP
   SELECT * INTO STRICT property FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=transition.type_id AND p.prop_id=property_id::int;
   IF truss.runtime_can_read(owner.document_id,property.declaration_module) IS NOT TRUE
    OR property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable(property.item) IS NOT TRUE THEN
    RAISE EXCEPTION 'current original rebind property/item reader required' USING ERRCODE='42501';END IF;
  END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_transition_reader(truss.runtime_catalog_rebind_transition,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_rebind_report_reader(selected_registration uuid,planned_basis jsonb DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE transition truss.runtime_catalog_rebind_transition%ROWTYPE;
BEGIN
 PERFORM truss.catalog_key_backfill_report_reader(selected_registration,planned_basis);
 FOR transition IN SELECT * FROM truss.runtime_catalog_rebind_transition WHERE registration_id=selected_registration LOOP
  PERFORM truss.catalog_rebind_transition_reader(transition,planned_basis);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_report_reader(uuid,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_rebind_history_group(entity jsonb,writer xid8,version bigint) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE transition truss.runtime_catalog_rebind_transition%ROWTYPE;request truss.catalog_registration_request%ROWTYPE;
 basis jsonb;entry jsonb;event jsonb;before_record jsonb;after_record jsonb;identity jsonb;
 history_profile text;moved_props jsonb;moved_retained jsonb;seen text[]:='{}';metadata_count int:=0;physical jsonb;
BEGIN
 SELECT * INTO STRICT transition FROM truss.runtime_catalog_rebind_transition t
  WHERE t.object_id=(entity->>'id')::bigint AND t.type_id=(entity->>'typeId')::int AND t.writer_xid=writer AND (t.after_object->>'ver')::bigint=version;
 SELECT * INTO STRICT request FROM truss.catalog_registration_request r WHERE r.registration_id=transition.registration_id;
 IF request.writer_xid IS DISTINCT FROM writer OR request.actor_oid IS DISTINCT FROM transition.actor_oid OR request.revision IS DISTINCT FROM transition.revision
  OR (transition.before_object->>'ver')::bigint+1<>version THEN RAISE EXCEPTION 'original registration-owned history transition required' USING ERRCODE='55000';END IF;
 PERFORM truss.catalog_rebind_transition_reader(transition);
 history_profile:=truss.catalog_rebind_profile(transition.journal);
 basis:=truss.catalog_all_expected_records(request.revision);
 identity:=jsonb_build_object('id',entity->>'id','typeId',entity->>'typeId','owner',jsonb_build_object('documentId',entity->>'documentId','moduleId',entity->>'moduleId'));
 before_record:=truss.runtime_object_history(transition.before_object,identity);
 after_record:=truss.catalog_rebind_history(transition.after_object,identity,basis);
 moved_props:=transition.before_object->'props';moved_retained:=coalesce(nullif(transition.before_object->'retained','null'::jsonb),'{}');
 FOR entry IN SELECT value FROM jsonb_array_elements(transition.journal) LOOP
  SELECT to_jsonb(j) INTO STRICT physical FROM truss.journal j WHERE j.xid=writer AND j.seq=(entry->>'seq')::bigint;
  IF physical IS DISTINCT FROM entry THEN RAISE EXCEPTION 'original registration journal row required' USING ERRCODE='55000';END IF;
  event:=convert_from(decode(entry->'new_value'->>'bytesBase64','base64'),'UTF8')::jsonb;
  IF event->>'historyProfile' IS DISTINCT FROM history_profile OR event->'origin'->>'databaseRole' IS DISTINCT FROM request.actor_name OR event->'origin'->'asserted' IS DISTINCT FROM convert_from(request.origin_bytes,'UTF8')::jsonb THEN
   RAISE EXCEPTION 'original registration history actor and origin required' USING ERRCODE='55000';END IF;
  IF event->>'operation'='rebind' THEN
   IF event->>'propertyId'=ANY(seen) OR NOT moved_retained ? (event->>'retainedName') OR moved_props ? (event->>'propertyId')
    OR event->>'beforeDefinitionContext' IS DISTINCT FROM before_record->'identity'->>'definitionPin'
    OR event->'retainedBefore' IS DISTINCT FROM jsonb_build_object('present',true,'value',moved_retained->(event->>'retainedName'))
    OR event->'retainedAfter' IS DISTINCT FROM '{"present":false}'::jsonb
    OR event->'propertyBefore' IS DISTINCT FROM '{"present":false}'::jsonb
    OR event->'propertyAfter' IS DISTINCT FROM event->'retainedBefore' THEN RAISE EXCEPTION 'exact original rebind presence facts required' USING ERRCODE='55000';END IF;
   PERFORM truss.runtime_history_property(transition.type_id,(event->>'propertyId')::int,request.revision,event->>'afterDefinitionPin');
   moved_props:=moved_props||jsonb_build_object(event->>'propertyId',moved_retained->(event->>'retainedName'));
   moved_retained:=moved_retained-(event->>'retainedName');seen:=array_append(seen,event->>'propertyId');
  ELSIF event->>'operation'='metadata' THEN
   metadata_count:=metadata_count+1;
   IF event->'before' IS DISTINCT FROM before_record OR event->'after' IS DISTINCT FROM after_record THEN RAISE EXCEPTION 'original complete rebind metadata witness required' USING ERRCODE='55000';END IF;
  ELSE RAISE EXCEPTION 'registration rebind-only journal required' USING ERRCODE='55000';END IF;
 END LOOP;
 IF metadata_count<>1 OR cardinality(seen)<>jsonb_array_length(transition.effects)
  OR moved_props IS DISTINCT FROM transition.after_object->'props'
  OR nullif(moved_retained,'{}'::jsonb) IS DISTINCT FROM nullif(transition.after_object->'retained','null'::jsonb) THEN
  RAISE EXCEPTION 'complete original rebind home transition required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_history_group(jsonb,xid8,bigint) FROM PUBLIC;

-- Derive semantic selection from retained bytes, never the current engine version.
CREATE FUNCTION truss.catalog_rebind_profile(journal jsonb) RETURNS text
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE entry jsonb;event jsonb;original bytea;selected text;candidate text;
BEGIN
 IF jsonb_typeof(journal) IS DISTINCT FROM 'array' OR jsonb_array_length(journal) NOT BETWEEN 2 AND 128 THEN
  RAISE EXCEPTION 'bounded original rebind group required' USING ERRCODE='55000';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(journal) LOOP
  original:=decode(entry->'new_value'->>'bytesBase64','base64');
  IF entry->'new_value' IS DISTINCT FROM truss.runtime_exact_wrapper('event',original)
   OR (convert_from(original,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
   RAISE EXCEPTION 'original rebind profile bytes required' USING ERRCODE='55000';END IF;
  event:=convert_from(original,'UTF8')::jsonb;candidate:=event->>'historyProfile';
  IF event->>'interfaceVersion' IS DISTINCT FROM 'truss-history-event/0.2.0-proposal'
   OR (candidate IN ('truss-native-catalog-rebind/0.1','truss-native-catalog-rebind/0.2','truss-native-catalog-rebind/0.3','truss-native-catalog-rebind/0.4')) IS NOT TRUE
   OR selected IS NOT NULL AND selected IS DISTINCT FROM candidate THEN
   RAISE EXCEPTION 'one supported original rebind profile required' USING ERRCODE='55000';END IF;
  selected:=candidate;
 END LOOP;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_rebind_profile(jsonb) FROM PUBLIC;

CREATE CONSTRAINT TRIGGER runtime_catalog_rebind_commit AFTER INSERT ON truss.runtime_catalog_rebind_transition
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check();
ALTER TABLE truss.runtime_catalog_rebind_transition ENABLE ALWAYS TRIGGER runtime_catalog_rebind_commit;
ALTER TABLE truss.runtime_catalog_rebind_transition ENABLE ALWAYS TRIGGER runtime_catalog_rebind_immutable;
