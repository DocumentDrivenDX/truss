-- Truss entity projection source. Integrated by the next versioned query profile.
-- All reads below use the caller query's statement snapshot, including own writes.
CREATE FUNCTION truss.query_object_attribution(binding jsonb,selected_type int,selected_id bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE object_row truss.object%ROWTYPE;owner truss.type_def%ROWTYPE;
 transition truss.runtime_object_transition%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;
 physical truss.journal%ROWTYPE;item jsonb;event jsonb;original bytea;actor text;
 created_actor text;updated_actor text;selected_version bigint;events int;used_bytes bigint:=0;
 creation truss.runtime_create_group%ROWTYPE;member jsonb;journals jsonb;expected_actor text;after_image jsonb;
 source_row truss.record_source%ROWTYPE;source_ledger truss.runtime_import_source%ROWTYPE;
 import_record jsonb;import_payload bytea;payload_value jsonb;expected_source jsonb;source_entry jsonb;
 creation_attempt uuid;operation jsonb;result jsonb;event_group jsonb;semantic_events jsonb;event_refs jsonb;epoch text;
BEGIN
 PERFORM truss.query_scope(binding);
 SELECT source_epoch::text INTO STRICT epoch FROM truss.catalog_runtime_installation;
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type)
 THEN RAISE EXCEPTION 'selected entity metadata scope required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=selected_type AND retired_rev IS NULL;
 SELECT * INTO STRICT object_row FROM truss.object WHERE id=selected_id AND type_id=selected_type;
 IF object_row.ver<1 OR object_row.root_id IS NOT NULL THEN RAISE EXCEPTION 'rootless current entity required' USING ERRCODE='0A000';END IF;
 FOR selected_version IN SELECT DISTINCT v FROM unnest(ARRAY[1::bigint,object_row.ver::bigint]) v LOOP
  expected_actor:=NULL;
  IF selected_version=1 THEN
   SELECT g.* INTO STRICT creation FROM truss.runtime_create_group g
    CROSS JOIN LATERAL jsonb_array_elements(g.expected_members) m
    WHERE m.value->'object'->>'id'=selected_id::text AND m.value->'object'->>'type_id'=selected_type::text;
   SELECT m.value INTO STRICT member FROM jsonb_array_elements(creation.expected_members) m
    WHERE m.value->'object'->>'id'=selected_id::text AND m.value->'object'->>'type_id'=selected_type::text;
   SELECT a.* INTO STRICT attempt FROM truss.runtime_object_attempt a
    WHERE a.complete AND a.writer_xid=creation.writer_xid AND a.actor_oid=creation.actor_oid
    AND EXISTS(SELECT 1 FROM jsonb_array_elements(a.results) r
      WHERE r.value->>'operation'='create_object' AND r.value->'identity'->>'id'=selected_id::text
       AND r.value->'identity'->>'typeId'=selected_type::text);
   creation_attempt:=attempt.id;
   journals:=jsonb_build_array(member->'journal');after_image:=member->'object';expected_actor:=creation.actor_name;
  ELSE
   SELECT * INTO STRICT transition FROM truss.runtime_object_transition t
    WHERE t.object_id=selected_id AND t.type_id=selected_type AND (t.after_object->>'ver')::bigint=selected_version;
   SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=transition.attempt_id;
   IF NOT attempt.complete OR attempt.writer_xid IS DISTINCT FROM transition.writer_xid
    OR attempt.next_index<=transition.operation_index THEN RAISE EXCEPTION 'complete original attribution attempt required' USING ERRCODE='55000';END IF;
   operation:=convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations'->transition.operation_index;
   result:=attempt.results->transition.operation_index;
   IF operation->>'operation' IS DISTINCT FROM 'update_object' OR result->>'operation' IS DISTINCT FROM 'update_object'
    OR result->>'outcome' IS DISTINCT FROM 'changed' OR result->>'version' IS DISTINCT FROM selected_version::text
    OR result->'identity'->>'id' IS DISTINCT FROM selected_id::text OR result->'identity'->>'typeId' IS DISTINCT FROM selected_type::text
   THEN RAISE EXCEPTION 'original changed attribution result required' USING ERRCODE='55000';END IF;
   journals:=transition.journal;after_image:=transition.after_object;
  END IF;
  IF selected_version=object_row.ver AND after_image IS DISTINCT FROM to_jsonb(object_row)
  THEN RAISE EXCEPTION 'current entity and attribution image differ' USING ERRCODE='55000';END IF;
  actor:=NULL;events:=0;event_group:=NULL;semantic_events:='[]';event_refs:='[]';
  FOR item IN SELECT value FROM jsonb_array_elements(journals) LOOP
   events:=events+1;used_bytes:=used_bytes+octet_length(item::text);
   IF events>128 OR used_bytes>(binding->>'maximumBytes')::bigint THEN RAISE EXCEPTION 'bounded attribution evidence required' USING ERRCODE='54000';END IF;
   SELECT * INTO STRICT physical FROM truss.journal WHERE xid=(item->>'xid')::xid8 AND seq=(item->>'seq')::bigint;
   IF to_jsonb(physical) IS DISTINCT FROM item OR physical.entity_kind<>'o' OR physical.entity_id<>selected_id
    OR physical.entity_type<>selected_type OR physical.ver<>selected_version OR physical.xid<>attempt.writer_xid
   THEN RAISE EXCEPTION 'original attribution journal correspondence required' USING ERRCODE='55000';END IF;
   original:=decode(physical.new_value->>'bytesBase64','base64');
   IF physical.new_value IS DISTINCT FROM truss.runtime_exact_wrapper('event',original)
    OR (convert_from(original,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
   THEN RAISE EXCEPTION 'original attribution event required' USING ERRCODE='55000';END IF;
   event:=convert_from(original,'UTF8')::jsonb;
   IF event->>'interfaceVersion' IS DISTINCT FROM 'truss-history-event/0.2.0-proposal'
    OR event->>'sourceEpoch' IS DISTINCT FROM epoch
    OR event->>'historyProfile' IS DISTINCT FROM (CASE selected_version WHEN 1 THEN 'truss-native-scalar-create/0.2' ELSE 'truss-native-scalar-mutation/0.1' END)
    OR physical.op IS DISTINCT FROM (CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END)
    OR physical.prop_id IS DISTINCT FROM (event->>'propertyId')::int
    OR event->'origin'->'asserted' IS DISTINCT FROM (convert_from(attempt.input_bytes,'UTF8')::jsonb)->'assertedOrigin'
    OR event->>'xid' IS DISTINCT FROM physical.xid::text OR event->>'seq' IS DISTINCT FROM physical.seq::text
    OR event->>'eventVersion' IS DISTINCT FROM selected_version::text OR event->>'eventCatalogRevision' IS DISTINCT FROM physical.rev::text
    OR event->'identity'->>'id' IS DISTINCT FROM selected_id::text OR event->'identity'->>'typeId' IS DISTINCT FROM selected_type::text
    OR event->'identity'->'owner' IS DISTINCT FROM jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module)
    OR physical.origin IS DISTINCT FROM truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8'))
    OR nullif(event->'origin'->>'databaseRole','') IS NULL
   THEN RAISE EXCEPTION 'original attribution identity and origin required' USING ERRCODE='55000';END IF;
   IF actor IS NOT NULL AND actor IS DISTINCT FROM event->'origin'->>'databaseRole'
   THEN RAISE EXCEPTION 'one actor per attribution version required' USING ERRCODE='55000';END IF;
   IF event_group IS NULL THEN event_group:=event->'mutationGroup';
   ELSIF event_group IS DISTINCT FROM event->'mutationGroup' THEN RAISE EXCEPTION 'one original attribution group required' USING ERRCODE='55000';END IF;
   semantic_events:=semantic_events||jsonb_build_array(event-'mutationGroup');
   event_refs:=event_refs||jsonb_build_array(jsonb_build_object('sourceEpoch',epoch,'historyProfile',event->>'historyProfile','xid',physical.xid::text,'seq',physical.seq::text));
   actor:=event->'origin'->>'databaseRole';
   IF expected_actor IS NOT NULL AND actor IS DISTINCT FROM expected_actor
   THEN RAISE EXCEPTION 'original creation actor correspondence required' USING ERRCODE='55000';END IF;
   IF selected_version=1 AND event->>'operation'<>'create'
   THEN RAISE EXCEPTION 'original creation attribution required' USING ERRCODE='55000';END IF;
  END LOOP;
  IF event_group IS DISTINCT FROM jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',events::text,'orderedEventDigest',encode(sha256(convert_to(semantic_events::text,'UTF8')),'hex'))
   OR selected_version>1 AND result->'events' IS DISTINCT FROM event_refs
  THEN RAISE EXCEPTION 'complete original attribution event group required' USING ERRCODE='55000';END IF;
  IF events=0 THEN RAISE EXCEPTION 'missing attribution events' USING ERRCODE='55000';END IF;
  IF selected_version=1 THEN created_actor:=actor;END IF;
  IF selected_version=object_row.ver THEN updated_actor:=actor;END IF;
 END LOOP;
 SELECT * INTO source_row FROM truss.record_source WHERE entity_kind='o' AND entity_id=selected_id;
 SELECT * INTO source_ledger FROM truss.runtime_import_source WHERE entity_kind='o' AND entity_id=selected_id;
 IF (source_row.entity_id IS NULL) IS DISTINCT FROM (source_ledger.entity_id IS NULL)
  OR source_row.entity_id IS NOT NULL AND source_ledger.expected_source IS DISTINCT FROM to_jsonb(source_row)
 THEN RAISE EXCEPTION 'immutable import source correspondence required' USING ERRCODE='55000';END IF;
 IF source_ledger.entity_id IS NOT NULL THEN
  SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=source_ledger.group_attempt_id;
  IF attempt.id IS DISTINCT FROM creation_attempt OR NOT attempt.complete OR attempt.writer_xid IS DISTINCT FROM source_ledger.writer_xid
   OR attempt.next_index<>1 OR attempt.results->0->>'outcome' IS DISTINCT FROM 'created'
   OR attempt.results->0->'identity'->>'id' IS DISTINCT FROM selected_id::text
   OR attempt.results->0->'identity'->>'typeId' IS DISTINCT FROM selected_type::text
  THEN RAISE EXCEPTION 'original import creation linkage required' USING ERRCODE='55000';END IF;
  import_record:=convert_from(source_ledger.original_record,'UTF8')::jsonb;
  import_payload:=decode(import_record->'payload'->>'bytesBase64','base64');
  IF encode(sha256(import_payload),'hex') IS DISTINCT FROM import_record->'payload'->>'sha256'
   OR (convert_from(import_payload,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  THEN RAISE EXCEPTION 'original import payload required' USING ERRCODE='55000';END IF;
  payload_value:=convert_from(import_payload,'UTF8')::jsonb;expected_source:='{}'::jsonb;
  operation:=convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations'->0;
  IF import_record->>'kind' IS DISTINCT FROM 'object' OR payload_value->>'kind' IS DISTINCT FROM 'object'
   OR operation->>'operation' IS DISTINCT FROM 'create_object'
   OR operation->>'typeDefinitionPin' IS DISTINCT FROM import_record->'identity'->'type'->>'definitionPin'
   OR operation->'values' IS DISTINCT FROM payload_value->'values' OR operation->'ownership' IS DISTINCT FROM payload_value->'ownership'
   OR attempt.results->0->'identity'->'owner' IS DISTINCT FROM jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module)
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements((convert_from(attempt.input_bytes,'UTF8')::jsonb)->'assertedOrigin'->'entries') e
    WHERE e.value->>'key'='x-load-id' AND e.value->'value'=jsonb_build_object('kind','string','text',source_row.load_id))
  THEN RAISE EXCEPTION 'original import payload and creation correspondence required' USING ERRCODE='55000';END IF;
  IF payload_value->'source' IS NOT NULL THEN
   FOR source_entry IN SELECT value FROM jsonb_array_elements(payload_value->'source'->'entries') LOOP
    expected_source:=expected_source||jsonb_build_object(source_entry->>'key',CASE source_entry->'value'->>'kind'
     WHEN 'string' THEN source_entry->'value'->'text' WHEN 'null' THEN 'null'::jsonb
     WHEN 'boolean' THEN source_entry->'value'->'value' ELSE source_entry->'value' END);
   END LOOP;
  END IF;
  IF source_row.source IS DISTINCT FROM expected_source THEN RAISE EXCEPTION 'original import source facts required' USING ERRCODE='55000';END IF;
 END IF;
 PERFORM truss.query_scope(binding);
 RETURN jsonb_build_object('_version',object_row.ver::text,'_created_by',created_actor,'_updated_by',updated_actor,
  '_original_author',source_row.source->'author','_original_at',source_row.source->'at');
END;
$$;
REVOKE ALL ON FUNCTION truss.query_object_attribution(jsonb,int,bigint) FROM PUBLIC;
