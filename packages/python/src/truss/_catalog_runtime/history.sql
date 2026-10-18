-- Current-reader access to complete original committed mutation groups.
CREATE FUNCTION truss.runtime_history_entity(selection jsonb,expected_release text,expected_digest text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;selected_type int;
BEGIN
 PERFORM truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest
 OR pg_is_in_recovery() THEN RAISE EXCEPTION 'selected retained authority history required' USING ERRCODE='0A000';END IF;
 IF selection-ARRAY['kind','documentId','moduleId','definitionId','id']<>'{}'::jsonb
 OR (selection->>'kind' IN ('object','edge')) IS NOT TRUE
 OR jsonb_typeof(selection->'id') IS DISTINCT FROM 'string' OR selection->>'id' !~ '^[1-9][0-9]{0,18}$'
 OR length(selection->>'id')=19 AND (selection->>'id') COLLATE "C">'9223372036854775807'
 OR NOT EXISTS(SELECT 1 FROM jsonb_each(selection) WHERE key='documentId' AND jsonb_typeof(value)='string' AND octet_length(value#>>'{}') BETWEEN 1 AND 4096)
 OR NOT EXISTS(SELECT 1 FROM jsonb_each(selection) WHERE key='moduleId' AND jsonb_typeof(value)='string' AND octet_length(value#>>'{}') BETWEEN 1 AND 4096)
 OR NOT EXISTS(SELECT 1 FROM jsonb_each(selection) WHERE key='definitionId' AND jsonb_typeof(value)='string' AND octet_length(value#>>'{}') BETWEEN 1 AND 4096) THEN
  RAISE EXCEPTION 'bounded qualified history entity required' USING ERRCODE='22023';END IF;
 IF NOT truss.runtime_can_read(selection->>'documentId',selection->>'moduleId') THEN RAISE EXCEPTION 'current history owner reader required' USING ERRCODE='42501';END IF;
 IF selection->>'kind'='object' THEN
  SELECT type_id INTO selected_type FROM truss.type_def WHERE document_id=selection->>'documentId' AND module=selection->>'moduleId' AND element=selection->>'definitionId'
   AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 ELSE
  SELECT rel_type_id INTO selected_type FROM truss.rel_def WHERE document_id=selection->>'documentId' AND module=selection->>'moduleId' AND rel_id=selection->>'definitionId' AND retired_rev IS NULL;
 END IF;
 IF selected_type IS NULL THEN RAISE EXCEPTION 'retained entity definition unavailable' USING ERRCODE='P1010';END IF;
 RETURN selection||jsonb_build_object('typeId',selected_type::text,'installationId',installation.installation_id::text,
  'sourceEpoch',installation.source_epoch::text,'releaseSha256',installation.release_sha256);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_entity(jsonb,text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_property_qualified(selected_type int,property_id int,revision int,definition_pin text,qualified_actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE basis jsonb;property truss.prop_def%ROWTYPE;pin record;
BEGIN
 SELECT CASE WHEN revision=(SELECT rev FROM truss.schema_head WHERE id=1)
  AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>revision)
 THEN jsonb_build_object(
  'type_def',(SELECT coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) FROM truss.type_def t WHERE t.type_id=selected_type),
  'prop_def',(SELECT coalesce(jsonb_agg(to_jsonb(p)),'[]'::jsonb) FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=property_id)) END INTO basis;
 IF basis IS NULL THEN basis:=truss.catalog_all_expected_records(revision);END IF;
 SELECT * INTO STRICT property FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=selected_type AND p.prop_id=property_id;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata_in_basis('property',selected_type,property_id,revision,basis);
 IF pin.definition_pin IS DISTINCT FROM definition_pin THEN RAISE EXCEPTION 'original property interpretation required' USING ERRCODE='55000';END IF;
 IF NOT truss.runtime_can_read_qualified(property.definition_document_id,property.declaration_module,qualified_actor) THEN RAISE EXCEPTION 'current historical property reader required' USING ERRCODE='42501';END IF;
 IF property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable_qualified(property.item,qualified_actor) IS NOT TRUE THEN RAISE EXCEPTION 'current historical item reader required' USING ERRCODE='42501';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_property_qualified(int,int,int,text,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_property(selected_type int,property_id int,revision int,definition_pin text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_history_property_qualified(selected_type,property_id,revision,definition_pin,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_property(int,int,int,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_image_qualified(image jsonb,entity jsonb,expected_version bigint,qualified_actor oid) RETURNS void
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
  PERFORM truss.runtime_history_property_qualified((entity->>'typeId')::int,(member->>'propertyId')::int,revision,member->>'definitionPin',qualified_actor);
 END LOOP;
 IF entity->>'kind'='object' THEN PERFORM truss.runtime_history_ownership_qualified(image,qualified_actor);END IF;
 IF entity->>'kind'='edge' THEN
  FOR endpoint IN SELECT value FROM jsonb_array_elements(jsonb_build_array(image->'source',image->'target')) LOOP
   SELECT * INTO STRICT endpoint_pin FROM truss.runtime_owned_definition_metadata('type',(endpoint->>'typeId')::int,NULL,revision);
   IF endpoint->>'definitionPin' IS DISTINCT FROM endpoint_pin.definition_pin OR endpoint->'owner' IS DISTINCT FROM jsonb_build_object('documentId',endpoint_pin.document_id,'moduleId',endpoint_pin.module_id) THEN
    RAISE EXCEPTION 'original endpoint interpretation required' USING ERRCODE='55000';END IF;
   IF NOT truss.runtime_can_read_qualified(endpoint_pin.document_id,endpoint_pin.module_id,qualified_actor) THEN RAISE EXCEPTION 'current historical endpoint reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_image_qualified(jsonb,jsonb,bigint,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_image(image jsonb,entity jsonb,expected_version bigint) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_history_image_qualified(image,entity,expected_version,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_image(jsonb,jsonb,bigint) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_group_qualified(entity jsonb,writer xid8,version bigint,maximum_events int,maximum_bytes int,qualified_actor oid) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE physical truss.journal%ROWTYPE;original bytea;event jsonb;items jsonb:='[]';semantic jsonb:='[]';group_pin jsonb;
 count_events int:=0;size int:=0;expected_pin text;selected_transition bigint;
BEGIN
 FOR physical IN SELECT * FROM truss.journal j WHERE j.entity_kind=(CASE entity->>'kind' WHEN 'object' THEN 'o' ELSE 'e' END)::char(1)
  AND j.entity_id=(entity->>'id')::bigint AND j.entity_type=(entity->>'typeId')::int AND j.xid=writer AND j.ver=version ORDER BY j.seq LIMIT maximum_events+1 LOOP
  count_events:=count_events+1;
  IF count_events>maximum_events THEN RAISE EXCEPTION 'whole history group exceeds event limit' USING ERRCODE='54000';END IF;
  size:=size+octet_length(physical.new_value::text)+octet_length(physical.origin::text);
  IF size>maximum_bytes THEN RAISE EXCEPTION 'whole history group exceeds byte limit' USING ERRCODE='54000';END IF;
  original:=decode(physical.new_value->>'bytesBase64','base64');
  IF physical.new_value IS DISTINCT FROM truss.runtime_exact_wrapper('event',original)
  OR (convert_from(original,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'original exact history wrapper required' USING ERRCODE='55000';END IF;
  event:=convert_from(original,'UTF8')::jsonb;
  IF event->>'interfaceVersion' IS DISTINCT FROM 'truss-history-event/0.2.0-proposal'
  OR (event->>'historyProfile' IN ('truss-native-scalar-create/0.2','truss-native-owned-create/0.1','truss-native-scalar-mutation/0.1','truss-native-owned-mutation/0.1','truss-native-edge-mutation/0.1','truss-native-owned-edge-mutation/0.1','truss-native-catalog-rebind/0.1','truss-native-catalog-rebind/0.2','truss-native-catalog-rebind/0.3','truss-native-catalog-rebind/0.4')) IS NOT TRUE
  OR event->>'sourceEpoch' IS DISTINCT FROM entity->>'sourceEpoch' OR event->>'xid' IS DISTINCT FROM physical.xid::text
  OR event->>'seq' IS DISTINCT FROM physical.seq::text OR event->>'eventVersion' IS DISTINCT FROM physical.ver::text
  OR event->>'eventCatalogRevision' IS DISTINCT FROM physical.rev::text
  OR event->'identity'->>'id' IS DISTINCT FROM entity->>'id' OR event->'identity'->>'typeId' IS DISTINCT FROM entity->>'typeId'
  OR event->'identity'->'owner' IS DISTINCT FROM jsonb_build_object('documentId',entity->>'documentId','moduleId',entity->>'moduleId')
  OR physical.op IS DISTINCT FROM (CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END)
  OR physical.prop_id IS DISTINCT FROM (event->>'propertyId')::int
  OR physical.origin IS DISTINCT FROM truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8')) THEN
   RAISE EXCEPTION 'physical and semantic history correspondence required' USING ERRCODE='55000';END IF;
  IF event->>'historyProfile'='truss-native-owned-mutation/0.1' THEN
   SELECT t.transition_id INTO STRICT selected_transition FROM truss.runtime_object_transition t
    CROSS JOIN LATERAL jsonb_array_elements(t.journal) j WHERE t.object_id=physical.entity_id
     AND t.type_id=physical.entity_type AND t.writer_xid=physical.xid AND j.value=to_jsonb(physical);
   PERFORM truss.runtime_owned_object_transition_validate_qualified(selected_transition,true,qualified_actor);
  END IF;
  IF event->>'historyProfile'='truss-native-owned-edge-mutation/0.1' THEN
   SELECT t.transition_id INTO STRICT selected_transition FROM truss.runtime_edge_transition t
    CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
    WHERE t.edge_id=physical.entity_id AND t.rel_type_id=physical.entity_type AND t.writer_xid=physical.xid
     AND j.value=to_jsonb(physical);
   PERFORM truss.runtime_owned_edge_transition_validate(selected_transition,true);
  END IF;
  IF entity->>'kind'='object' THEN SELECT definition_pin INTO STRICT expected_pin FROM truss.runtime_owned_definition_metadata('type',physical.entity_type,NULL,physical.rev);
  ELSE expected_pin:=truss.runtime_relationship_pin(physical.entity_type,physical.rev);END IF;
  IF event->'identity'->>'definitionPin' IS DISTINCT FROM expected_pin THEN RAISE EXCEPTION 'original event interpretation required' USING ERRCODE='55000';END IF;
  IF event->>'operation'='property' THEN
   PERFORM truss.runtime_history_property_qualified(physical.entity_type,physical.prop_id,physical.rev,event->>'definitionPin',qualified_actor);
  ELSIF event->>'operation'='rebind' THEN
   IF (event->>'historyProfile' IN ('truss-native-catalog-rebind/0.1','truss-native-catalog-rebind/0.2','truss-native-catalog-rebind/0.3','truss-native-catalog-rebind/0.4')) IS NOT TRUE THEN RAISE EXCEPTION 'original catalog rebind profile required' USING ERRCODE='55000';END IF;
   PERFORM truss.runtime_history_property_qualified(physical.entity_type,physical.prop_id,physical.rev,event->>'afterDefinitionPin',qualified_actor);
   PERFORM truss.catalog_rebind_history_group(entity,writer,version);
  ELSIF event->>'operation'='create' THEN PERFORM truss.runtime_history_image_qualified(event->'after',entity,version,qualified_actor);
  ELSIF event->>'operation'='metadata' THEN
   PERFORM truss.runtime_history_image_qualified(event->'before',entity,version-1,qualified_actor);PERFORM truss.runtime_history_image_qualified(event->'after',entity,version,qualified_actor);
  ELSIF event->>'operation'='delete' THEN PERFORM truss.runtime_history_image_qualified(event->'before',entity,version-1,qualified_actor);
  ELSE RAISE EXCEPTION 'supported retained event required' USING ERRCODE='0A000';END IF;
  IF group_pin IS NULL THEN group_pin:=event->'mutationGroup';
  ELSIF group_pin IS DISTINCT FROM event->'mutationGroup' THEN RAISE EXCEPTION 'one complete mutation group required' USING ERRCODE='55000';END IF;
  semantic:=semantic||jsonb_build_array(event-'mutationGroup');
  items:=items||jsonb_build_array(jsonb_build_object('contentBase64',replace(encode(original,'base64'),chr(10),''),'sha256',encode(sha256(original),'hex'),
   'writerXid',physical.xid::text,'seq',physical.seq::text,'version',physical.ver::text));
 END LOOP;
 IF count_events=0 THEN RAISE EXCEPTION 'retained history unavailable' USING ERRCODE='P1010';END IF;
 IF group_pin IS DISTINCT FROM jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',count_events::text,'orderedEventDigest',encode(sha256(convert_to(semantic::text,'UTF8')),'hex')) THEN
  RAISE EXCEPTION 'complete original history group digest required' USING ERRCODE='55000';END IF;
 RETURN items;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_group_qualified(jsonb,xid8,bigint,int,int,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_group(entity jsonb,writer xid8,version bigint,maximum_events int,maximum_bytes int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN truss.runtime_history_group_qualified(entity,writer,version,maximum_events,maximum_bytes,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_group(jsonb,xid8,bigint,int,int) FROM PUBLIC;

CREATE FUNCTION truss.read_history(selection jsonb,cursor_bytes bytea,selected_version bigint,maximum_events int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE entity jsonb;frontier xid8;captured_revision int;after_xid xid8:='0';after_seq bigint:=0;cursor jsonb;
 first_event truss.journal%ROWTYPE;items jsonb;item jsonb;event jsonb;result bytea;next_cursor jsonb;record_image jsonb;deleted boolean:=false;
BEGIN
 IF maximum_events IS NULL OR maximum_events NOT BETWEEN 1 AND 65536 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216
 OR selected_version IS NOT NULL AND selected_version<1 THEN RAISE EXCEPTION 'bounded history request required' USING ERRCODE='22023';END IF;
 entity:=truss.runtime_history_entity(selection,expected_release,expected_digest);
 captured_revision:=(SELECT rev FROM truss.schema_head WHERE id=1);frontier:=pg_snapshot_xmin(pg_current_snapshot());
 IF cursor_bytes IS NOT NULL THEN
  IF selected_version IS NOT NULL OR octet_length(cursor_bytes) NOT BETWEEN 1 AND 16384 OR (convert_from(cursor_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
   RAISE EXCEPTION 'exact page cursor required' USING ERRCODE='22023';END IF;
  cursor:=convert_from(cursor_bytes,'UTF8')::jsonb;
  IF cursor-ARRAY['profile','entity','afterXid','afterSeq']<>'{}'::jsonb OR cursor->>'profile' IS DISTINCT FROM 'truss-native-history-cursor/0.1' OR cursor->'entity' IS DISTINCT FROM entity
  OR jsonb_typeof(cursor->'afterXid') IS DISTINCT FROM 'string' OR jsonb_typeof(cursor->'afterSeq') IS DISTINCT FROM 'string'
  OR cursor->>'afterXid' !~ '^(0|[1-9][0-9]{0,19})$' OR cursor->>'afterSeq' !~ '^(0|[1-9][0-9]{0,18})$' THEN RAISE EXCEPTION 'current scoped history cursor required' USING ERRCODE='22023';END IF;
  after_xid:=(cursor->>'afterXid')::xid8;after_seq:=(cursor->>'afterSeq')::bigint;
 END IF;
 SELECT * INTO first_event FROM truss.journal j WHERE j.entity_kind=(CASE entity->>'kind' WHEN 'object' THEN 'o' ELSE 'e' END)::char(1)
  AND j.entity_id=(entity->>'id')::bigint AND j.entity_type=(entity->>'typeId')::int AND j.xid<frontier
  AND (selected_version IS NOT NULL AND j.ver=selected_version OR selected_version IS NULL AND (j.xid,j.seq)>(after_xid,after_seq)) ORDER BY j.xid,j.seq LIMIT 1;
 IF NOT FOUND THEN
  IF selected_version IS NOT NULL THEN RAISE EXCEPTION 'requested retained history unavailable' USING ERRCODE='P1010';END IF;
  result:=convert_to(jsonb_build_object('outcome','page','events','[]'::jsonb,'safeWatermarkXid',frontier::text)::text,'UTF8');
 ELSE
  items:=truss.runtime_history_group(entity,first_event.xid,first_event.ver,maximum_events,maximum_bytes);
  IF selected_version IS NULL THEN
   IF (first_event.xid,(items->0->>'seq')::bigint)<=(after_xid,after_seq) THEN RAISE EXCEPTION 'complete group cursor required' USING ERRCODE='22023';END IF;
   next_cursor:=jsonb_build_object('profile','truss-native-history-cursor/0.1','entity',entity,'afterXid',first_event.xid::text,'afterSeq',items->-1->>'seq');
   result:=convert_to(jsonb_build_object('outcome','page','events',items,'safeWatermarkXid',frontier::text,
    'cursorBase64',replace(encode(convert_to(next_cursor::text,'UTF8'),'base64'),chr(10),''))::text,'UTF8');
  ELSE
   FOR item IN SELECT value FROM jsonb_array_elements(items) LOOP
    event:=convert_from(decode(item->>'contentBase64','base64'),'UTF8')::jsonb;
    IF event->>'operation' IN ('create','metadata','delete') THEN
     IF record_image IS NOT NULL THEN RAISE EXCEPTION 'one complete version witness required' USING ERRCODE='55000';END IF;
     deleted:=event->>'operation'='delete';record_image:=CASE WHEN deleted THEN event->'before' ELSE event->'after' END;
     result:=convert_to(jsonb_build_object('outcome',CASE WHEN deleted THEN 'deleted' ELSE 'record' END,'version',selected_version::text,
      'recordBase64',replace(encode(convert_to(record_image::text,'UTF8'),'base64'),chr(10),''),'event',item)::text,'UTF8');
    END IF;
   END LOOP;
   IF record_image IS NULL THEN RAISE EXCEPTION 'complete retained version witness unavailable' USING ERRCODE='P1010';END IF;
  END IF;
  -- Recheck every original group dependency immediately before publication.
  PERFORM truss.runtime_history_group(entity,first_event.xid,first_event.ver,maximum_events,maximum_bytes);
 END IF;
 PERFORM truss.runtime_history_entity(selection,expected_release,expected_digest);
 IF captured_revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1) THEN RAISE EXCEPTION 'history catalog changed' USING ERRCODE='55P03';END IF;
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'whole history output exceeds byte limit' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.read_history(jsonb,bytea,bigint,int,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.lookup_import_source(selection jsonb,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE entity jsonb;kind char(1);ledger truss.runtime_import_source%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;
 identity jsonb;actual jsonb;content bytea;result bytea;creation jsonb;captured_revision int;frontier xid8;
BEGIN
 entity:=truss.runtime_history_entity(selection,expected_release,expected_digest);
 captured_revision:=(SELECT rev FROM truss.schema_head WHERE id=1);frontier:=pg_snapshot_xmin(pg_current_snapshot());
 IF maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 THEN RAISE EXCEPTION 'bounded provenance output required' USING ERRCODE='22023';END IF;
 kind:=CASE entity->>'kind' WHEN 'object' THEN 'o' ELSE 'e' END;
 SELECT * INTO ledger FROM truss.runtime_import_source WHERE entity_kind=kind AND entity_id=(entity->>'id')::bigint;
 IF NOT FOUND THEN
  IF EXISTS(SELECT 1 FROM truss.record_source WHERE entity_kind=kind AND entity_id=(entity->>'id')::bigint) THEN
   RAISE EXCEPTION 'original source ledger required' USING ERRCODE='55000';END IF;
  -- Absence is meaningful only for an authorized original committed creation.
  creation:=convert_from(truss.read_history(selection,NULL,1,4096,maximum_bytes,expected_release,expected_digest),'UTF8')::jsonb;
  IF creation->>'outcome' IS DISTINCT FROM 'record' THEN RAISE EXCEPTION 'original committed creation required' USING ERRCODE='P1010';END IF;
  IF creation->'event'->>'writerXid' IS NULL OR (creation->'event'->>'writerXid')::xid8>=frontier THEN
   RAISE EXCEPTION 'creation outside fixed source observation' USING ERRCODE='P1010';END IF;
  IF EXISTS(SELECT 1 FROM truss.runtime_import_source WHERE entity_kind=kind AND entity_id=(entity->>'id')::bigint)
   OR EXISTS(SELECT 1 FROM truss.record_source WHERE entity_kind=kind AND entity_id=(entity->>'id')::bigint) THEN
   RAISE EXCEPTION 'source absence observation changed' USING ERRCODE='55P03';END IF;
  result:=convert_to('{"outcome":"absent"}','UTF8');
 ELSE
  IF ledger.writer_xid>=frontier THEN RAISE EXCEPTION 'committed provenance unavailable' USING ERRCODE='P1010';END IF;
  SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=ledger.group_attempt_id;
  identity:=attempt.results->ledger.operation_index->'identity';
  IF NOT attempt.complete OR ledger.operation_index<0 OR ledger.operation_index>=attempt.next_index
   OR (convert_from(ledger.original_record,'UTF8')::jsonb->'payloadProfile' IS DISTINCT FROM truss.runtime_import_profiles()->'ownedImportPayloadProfile' AND attempt.next_index<>1)
   OR attempt.writer_xid IS DISTINCT FROM ledger.writer_xid
   OR attempt.results->ledger.operation_index->>'outcome' IS DISTINCT FROM 'created' OR identity->>'id' IS DISTINCT FROM entity->>'id'
   OR identity->>'typeId' IS DISTINCT FROM entity->>'typeId'
   OR identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',entity->>'documentId','moduleId',entity->>'moduleId')
   OR (convert_from(attempt.input_bytes,'UTF8')::jsonb)->'operations'->ledger.operation_index->>'operation' IS DISTINCT FROM
      (CASE kind WHEN 'o' THEN 'create_object' ELSE 'create_edge' END) THEN
   RAISE EXCEPTION 'original qualified import creation required' USING ERRCODE='55000';END IF;
  IF NOT truss.runtime_receipt_can_read(attempt.id) THEN RAISE EXCEPTION 'original creation dependency reader required' USING ERRCODE='42501';END IF;
  SELECT to_jsonb(s) INTO actual FROM truss.record_source s WHERE entity_kind=kind AND entity_id=(entity->>'id')::bigint;
  IF actual IS DISTINCT FROM ledger.expected_source OR actual->>'entity_kind' IS DISTINCT FROM kind::text
   OR actual->>'entity_id' IS DISTINCT FROM entity->>'id' THEN
   RAISE EXCEPTION 'retained native source correspondence required' USING ERRCODE='55000';END IF;
  content:=convert_to(ledger.expected_source::text,'UTF8');
  result:=convert_to(jsonb_build_object('outcome','found','loadId',actual->>'load_id','writerXid',ledger.writer_xid::text,
   'contentBase64',replace(encode(content,'base64'),chr(10),''),'sha256',encode(sha256(content),'hex'))::text,'UTF8');
  IF NOT truss.runtime_receipt_can_read(attempt.id) THEN RAISE EXCEPTION 'current creation dependency reader required' USING ERRCODE='42501';END IF;
 END IF;
 PERFORM truss.runtime_history_entity(selection,expected_release,expected_digest);
 IF captured_revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1) THEN RAISE EXCEPTION 'provenance context changed' USING ERRCODE='55P03';END IF;
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'provenance exceeds byte limit' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.lookup_import_source(jsonb,int,text,text) FROM PUBLIC;
