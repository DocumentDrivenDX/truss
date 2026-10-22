-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Truss entity projection source. Integrated by the next versioned query profile.
-- All reads below use the caller query's statement snapshot, including own writes.
CREATE FUNCTION truss.query_object_attribution(binding jsonb,selected_type int,selected_id bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE object_row truss.object%ROWTYPE;owner truss.type_def%ROWTYPE;
 registration truss.catalog_registration_request%ROWTYPE;rebound truss.runtime_catalog_rebind_transition%ROWTYPE;
 writer xid8;asserted jsonb;history_profile text;
 attempt truss.runtime_object_attempt%ROWTYPE;selected_transition_id bigint;transition_attempt_id uuid;transition_operation_index int;transition_writer_xid xid8;transition_before_object jsonb;transition_after_object jsonb;transition_journal jsonb;
 physical truss.journal%ROWTYPE;item jsonb;event jsonb;original bytea;actor text;
 created_actor text;updated_actor text;selected_version bigint;events int;used_bytes bigint:=0;
 creation truss.runtime_create_group%ROWTYPE;member jsonb;journals jsonb;expected_actor text;after_image jsonb;
 source_row truss.record_source%ROWTYPE;source_ledger truss.runtime_import_source%ROWTYPE;
 import_record jsonb;import_payload bytea;payload_value jsonb;expected_source jsonb;source_entry jsonb;
 root_identity jsonb;historical_image jsonb;historical_ownership jsonb;owned_mutation boolean;atomic_creation boolean;creation_attempt uuid;operation jsonb;result jsonb;input_header jsonb;event_group jsonb;semantic_events jsonb;event_refs jsonb;legacy_events jsonb[];legacy_event_refs jsonb[];epoch text;
BEGIN
 PERFORM truss.query_scope(binding);
 SELECT source_epoch::text INTO STRICT epoch FROM truss.catalog_runtime_installation;
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type)
 THEN RAISE EXCEPTION 'selected entity metadata scope required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=selected_type AND retired_rev IS NULL;
 SELECT * INTO STRICT object_row FROM truss.object WHERE id=selected_id AND type_id=selected_type;
 root_identity:=truss.query_object_root(binding,object_row);
 FOR selected_version IN SELECT DISTINCT v FROM unnest(ARRAY[1::bigint,object_row.ver::bigint]) v LOOP
  expected_actor:=NULL;registration.registration_id:=NULL;result:=NULL;transition_journal:=NULL;journals:=NULL;owned_mutation:=false;atomic_creation:=false;
  IF selected_version=1 THEN
   -- Modern creations have an indexed, immutable transition coordinate.
   SELECT a.* INTO attempt FROM truss.runtime_object_transition t
    JOIN truss.runtime_object_attempt a ON a.id=t.attempt_id
    WHERE t.object_id=selected_id AND t.type_id=selected_type AND t.before_object IS NULL AND a.complete;
   IF NOT FOUND THEN
   SELECT a.* INTO STRICT attempt FROM truss.runtime_object_attempt a WHERE a.complete
    AND EXISTS(SELECT 1 FROM jsonb_array_elements(a.results) r
     WHERE r.value->>'operation'='create_object' AND r.value->'identity'->>'id'=selected_id::text
      AND r.value->'identity'->>'typeId'=selected_type::text);
   END IF;
   IF attempt.context->'creationTransitionProfile'='{"identity":"truss-unified-create-transition","version":"0.2","sha256":"073782e2517f2a7e26c8d6479c6266ececf68963681ccfb6a380e9cd16f2e11b"}'::jsonb THEN
    SELECT t.transition_id,t.attempt_id,t.operation_index,t.writer_xid,t.before_object,t.after_object
     INTO STRICT selected_transition_id,transition_attempt_id,transition_operation_index,transition_writer_xid,transition_before_object,transition_after_object
     FROM truss.runtime_object_transition t
     WHERE t.attempt_id=attempt.id AND t.object_id=selected_id AND t.type_id=selected_type AND t.before_object IS NULL;
    IF attempt.context->'mutationProfile'=truss.runtime_owned_profile() THEN
     SELECT p.plan->'operation',p.result,p.plan->>'actorName' INTO STRICT operation,result,expected_actor FROM truss.runtime_owned_operation p
      WHERE p.attempt_id=attempt.id AND p.operation_index=transition_operation_index AND p.writer_xid=attempt.writer_xid;
    ELSE
    operation:=convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations'->transition_operation_index;
    result:=attempt.results->transition_operation_index;
    SELECT t.journal INTO STRICT transition_journal FROM truss.runtime_object_transition t WHERE t.transition_id=selected_transition_id;
    END IF;
    IF transition_writer_xid IS DISTINCT FROM attempt.writer_xid OR attempt.next_index<=transition_operation_index
     OR attempt.result_count<>attempt.next_index
     OR operation->>'operation' IS DISTINCT FROM 'create_object' OR result->>'operation' IS DISTINCT FROM 'create_object'
     OR result->>'outcome' IS DISTINCT FROM 'created' OR result->>'version' IS DISTINCT FROM '1'
     OR result->'identity'->>'id' IS DISTINCT FROM selected_id::text OR result->'identity'->>'typeId' IS DISTINCT FROM selected_type::text
     OR result->'identity'->>'definitionPin' IS DISTINCT FROM operation->>'typeDefinitionPin'
     OR transition_after_object->>'id' IS DISTINCT FROM selected_id::text
     OR transition_after_object->>'type_id' IS DISTINCT FROM selected_type::text
     OR transition_after_object->>'ver' IS DISTINCT FROM '1' THEN
     RAISE EXCEPTION 'completed atomic creation attribution required' USING ERRCODE='55000';END IF;
    creation_attempt:=attempt.id;journals:=transition_journal;after_image:=transition_after_object;atomic_creation:=true;
    owned_mutation:=attempt.context->'mutationProfile'=truss.runtime_owned_profile();
    IF owned_mutation AND nullif(expected_actor,'') IS NULL
    THEN RAISE EXCEPTION 'original creation actor required' USING ERRCODE='55000';END IF;
   ELSIF attempt.context->'creationTransitionProfile' IS NULL OR attempt.context->'creationTransitionProfile'=
    '{"identity":"truss-unified-create-transition","version":"0.1","sha256":"765d7def5e677dba5d3ed5cdc841b1aa43eb2f4a493f1d2603ff3698536a5396"}'::jsonb THEN
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
   ELSE RAISE EXCEPTION 'known original creation attribution profile required' USING ERRCODE='55000';END IF;
   input_header:=CASE WHEN attempt.context ? 'originalAssertedOrigin'
    THEN jsonb_build_object('assertedOrigin',attempt.context->'originalAssertedOrigin','mutationProfile',attempt.context->'mutationProfile')
    ELSE convert_from(attempt.input_bytes,'UTF8')::jsonb END;
   writer:=attempt.writer_xid;asserted:=input_header->'assertedOrigin';history_profile:=CASE WHEN input_header->'mutationProfile'=truss.runtime_owned_profile() THEN 'truss-native-owned-create/0.1' ELSE 'truss-native-scalar-create/0.2' END;
  ELSE
   SELECT * INTO rebound FROM truss.runtime_catalog_rebind_transition t WHERE t.object_id=selected_id AND t.type_id=selected_type AND (t.after_object->>'ver')::bigint=selected_version;
   IF FOUND THEN
    SELECT * INTO STRICT registration FROM truss.catalog_registration_request r WHERE r.registration_id=rebound.registration_id;
    IF registration.writer_xid IS DISTINCT FROM rebound.writer_xid OR registration.actor_oid IS DISTINCT FROM rebound.actor_oid OR registration.revision IS DISTINCT FROM rebound.revision THEN RAISE EXCEPTION 'original catalog attribution source required' USING ERRCODE='55000';END IF;
    PERFORM truss.catalog_rebind_transition_reader(rebound);
    journals:=rebound.journal;after_image:=rebound.after_object;expected_actor:=registration.actor_name;
    writer:=registration.writer_xid;asserted:=convert_from(registration.origin_bytes,'UTF8')::jsonb;history_profile:=truss.catalog_rebind_profile(rebound.journal);
   ELSE
   SELECT t.transition_id,t.attempt_id,t.operation_index,t.writer_xid,t.before_object,t.after_object
    INTO STRICT selected_transition_id,transition_attempt_id,transition_operation_index,transition_writer_xid,transition_before_object,transition_after_object
    FROM truss.runtime_object_transition t
    WHERE t.object_id=selected_id AND t.type_id=selected_type AND (t.after_object->>'ver')::bigint=selected_version;
   SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=transition_attempt_id;
   IF NOT attempt.complete OR attempt.writer_xid IS DISTINCT FROM transition_writer_xid
    OR attempt.next_index<=transition_operation_index OR attempt.result_count<>attempt.next_index
   THEN RAISE EXCEPTION 'complete original attribution attempt required' USING ERRCODE='55000';END IF;
   input_header:=CASE WHEN attempt.context ? 'originalAssertedOrigin'
    THEN jsonb_build_object('assertedOrigin',attempt.context->'originalAssertedOrigin','mutationProfile',attempt.context->'mutationProfile')
    ELSE convert_from(attempt.input_bytes,'UTF8')::jsonb END;
   owned_mutation:=input_header->'mutationProfile'=truss.runtime_owned_profile();
   IF owned_mutation THEN
    SELECT p.plan->'operation',p.result,p.plan->>'actorName' INTO STRICT operation,result,expected_actor FROM truss.runtime_owned_operation p
     WHERE p.attempt_id=attempt.id AND p.operation_index=transition_operation_index AND p.writer_xid=attempt.writer_xid;
   ELSE
    operation:=input_header->'operations'->transition_operation_index;result:=attempt.results->transition_operation_index;
    IF operation IS NULL THEN operation:=convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations'->transition_operation_index;END IF;
   END IF;
   IF owned_mutation THEN
    IF operation->>'operation' IS DISTINCT FROM 'update_object' OR result->>'operation' IS DISTINCT FROM 'update_object'
     OR result->>'outcome' IS DISTINCT FROM 'changed'
     OR transition_after_object->>'id' IS DISTINCT FROM selected_id::text
     OR transition_after_object->>'type_id' IS DISTINCT FROM selected_type::text
     OR transition_after_object->>'ver' IS DISTINCT FROM selected_version::text OR nullif(expected_actor,'') IS NULL
    THEN RAISE EXCEPTION 'original owned update attribution required' USING ERRCODE='55000';END IF;
   ELSIF operation->>'operation' IS DISTINCT FROM 'update_object' OR result->>'operation' IS DISTINCT FROM 'update_object'
    OR result->>'outcome' IS DISTINCT FROM 'changed' OR result->>'version' IS DISTINCT FROM selected_version::text
    OR result->'identity'->>'id' IS DISTINCT FROM selected_id::text OR result->'identity'->>'typeId' IS DISTINCT FROM selected_type::text
   THEN RAISE EXCEPTION 'original changed attribution result required' USING ERRCODE='55000';END IF;
   IF NOT owned_mutation THEN SELECT t.journal INTO STRICT transition_journal FROM truss.runtime_object_transition t WHERE t.transition_id=selected_transition_id;END IF;
   journals:=transition_journal;after_image:=transition_after_object;
   writer:=attempt.writer_xid;asserted:=input_header->'assertedOrigin';history_profile:=CASE WHEN owned_mutation THEN 'truss-native-owned-mutation/0.1' ELSE 'truss-native-scalar-mutation/0.1' END;
   END IF;
  END IF;
  IF selected_version=object_row.ver AND (after_image->>'id' IS DISTINCT FROM object_row.id::text
   OR after_image->>'type_id' IS DISTINCT FROM object_row.type_id::text OR after_image->>'ver' IS DISTINCT FROM object_row.ver::text)
  THEN RAISE EXCEPTION 'current entity attribution identity differs' USING ERRCODE='55000';END IF;
  -- Original attribution can depend on roots that no longer own this object.
  -- Their original identities must be covered by final selected-scope checks.
  FOR historical_image IN SELECT value FROM jsonb_array_elements(jsonb_build_array(after_image,
   CASE WHEN owned_mutation THEN transition_before_object ELSE NULL END)) WHERE value<>'null'::jsonb LOOP
   historical_ownership:=truss.runtime_object_ownership_at(historical_image);
   IF historical_ownership->>'state'='owned' THEN
    IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'documents') d JOIN truss.schema_doc archive
     ON archive.doc_id=d.value->>'documentId' AND archive.doc_revision=d.value->>'revision' AND archive.content_sha256=d.value->>'sha256'
     WHERE archive.doc_id=historical_ownership->'root'->'owner'->>'documentId' AND archive.rev<=(binding->>'catalogRevision')::int
      AND EXISTS(SELECT 1 FROM jsonb_array_elements(archive.document::jsonb->'modules') m
       WHERE m.value->>'id'=historical_ownership->'root'->'owner'->>'moduleId')) THEN
     RAISE EXCEPTION 'historical attribution root document must be selected for query' USING ERRCODE='0A000';END IF;
    PERFORM truss.runtime_history_ownership(jsonb_build_object('identity',jsonb_build_object('id',selected_id::text,'typeId',selected_type::text),
     'catalogRevision',historical_image->>'rev','ownership',historical_ownership));
   END IF;
  END LOOP;
  actor:=NULL;events:=0;event_group:=NULL;semantic_events:='[]';event_refs:='[]';legacy_events:='{}';legacy_event_refs:='{}';
  IF owned_mutation OR registration.registration_id IS NOT NULL THEN
   actor:=expected_actor;
   IF nullif(actor,'') IS NULL THEN RAISE EXCEPTION 'immutable attribution actor required' USING ERRCODE='55000';END IF;
   IF selected_version=1 THEN created_actor:=actor;END IF;
   IF selected_version=object_row.ver THEN updated_actor:=actor;END IF;
  ELSE
  FOR item IN SELECT value FROM jsonb_array_elements(journals) LOOP
   events:=events+1;used_bytes:=used_bytes+octet_length(item::text);
   IF events>128 OR used_bytes>(binding->>'maximumBytes')::bigint THEN RAISE EXCEPTION 'bounded attribution evidence required' USING ERRCODE='54000';END IF;
   SELECT * INTO STRICT physical FROM truss.journal WHERE xid=(item->>'xid')::xid8 AND seq=(item->>'seq')::bigint;
   IF physical IS DISTINCT FROM jsonb_populate_record(NULL::truss.journal,item) OR physical.entity_kind<>'o' OR physical.entity_id<>selected_id
    OR physical.entity_type<>selected_type OR physical.ver<>selected_version OR physical.xid<>writer
   THEN RAISE EXCEPTION 'original attribution journal correspondence required' USING ERRCODE='55000';END IF;
   original:=decode(physical.new_value->>'bytesBase64','base64');
   IF physical.new_value IS DISTINCT FROM truss.runtime_exact_wrapper('event',original)
    OR (convert_from(original,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
   THEN RAISE EXCEPTION 'original attribution event required' USING ERRCODE='55000';END IF;
   event:=convert_from(original,'UTF8')::jsonb;
   IF event->>'interfaceVersion' IS DISTINCT FROM 'truss-history-event/0.2.0-proposal'
    OR event->>'sourceEpoch' IS DISTINCT FROM epoch
    OR event->>'historyProfile' IS DISTINCT FROM history_profile
    OR physical.op IS DISTINCT FROM (CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END)
    OR physical.prop_id IS DISTINCT FROM (event->>'propertyId')::int
    OR event->'origin'->'asserted' IS DISTINCT FROM asserted
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
   legacy_events[cardinality(legacy_events)+1]:=event-'mutationGroup';
   legacy_event_refs[cardinality(legacy_event_refs)+1]:=jsonb_build_object('sourceEpoch',epoch,'historyProfile',event->>'historyProfile','xid',physical.xid::text,'seq',physical.seq::text);
   actor:=event->'origin'->>'databaseRole';
   IF expected_actor IS NOT NULL AND actor IS DISTINCT FROM expected_actor
   THEN RAISE EXCEPTION 'original creation actor correspondence required' USING ERRCODE='55000';END IF;
   IF selected_version=1 AND event->>'operation'<>'create'
   THEN RAISE EXCEPTION 'original creation attribution required' USING ERRCODE='55000';END IF;
  END LOOP;
  SELECT coalesce(jsonb_agg(v ORDER BY n),'[]'::jsonb) INTO semantic_events FROM unnest(legacy_events) WITH ORDINALITY e(v,n);
  SELECT coalesce(jsonb_agg(v ORDER BY n),'[]'::jsonb) INTO event_refs FROM unnest(legacy_event_refs) WITH ORDINALITY e(v,n);
  IF event_group IS DISTINCT FROM jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',events::text,'orderedEventDigest',encode(sha256(convert_to(semantic_events::text,'UTF8')),'hex'))
   OR selected_version>1 AND result->'events' IS DISTINCT FROM event_refs
  THEN RAISE EXCEPTION 'complete original attribution event group required' USING ERRCODE='55000';END IF;
  IF events=0 THEN RAISE EXCEPTION 'missing attribution events' USING ERRCODE='55000';END IF;
  IF selected_version=1 THEN created_actor:=actor;END IF;
  IF selected_version=object_row.ver THEN updated_actor:=actor;END IF;
  END IF;
 END LOOP;
 SELECT * INTO source_row FROM truss.record_source WHERE entity_kind='o' AND entity_id=selected_id;
 SELECT * INTO source_ledger FROM truss.runtime_import_source WHERE entity_kind='o' AND entity_id=selected_id;
 IF (source_row.entity_id IS NULL) IS DISTINCT FROM (source_ledger.entity_id IS NULL)
 THEN RAISE EXCEPTION 'original import source linkage required' USING ERRCODE='55000';END IF;
 IF source_ledger.entity_id IS NOT NULL THEN
  SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=source_ledger.group_attempt_id;
  IF attempt.context->'mutationProfile'=truss.runtime_owned_profile() THEN
   -- Modern source rows were admitted with the atomic group. Resolve their
   -- indexed result without decoding the entire group or replaying its payload.
   SELECT p.result INTO STRICT result FROM truss.runtime_owned_operation p
    WHERE p.attempt_id=attempt.id AND p.operation_index=source_ledger.operation_index
     AND p.writer_xid=source_ledger.writer_xid;
  ELSE result:=attempt.results->source_ledger.operation_index;END IF;
  IF attempt.id IS DISTINCT FROM creation_attempt OR NOT attempt.complete OR attempt.writer_xid IS DISTINCT FROM source_ledger.writer_xid
   OR source_ledger.operation_index<0 OR source_ledger.operation_index>=attempt.next_index
   OR result->>'outcome' IS DISTINCT FROM 'created'
   OR result->'identity'->>'id' IS DISTINCT FROM selected_id::text
   OR result->'identity'->>'typeId' IS DISTINCT FROM selected_type::text
   OR result->'identity'->'owner' IS DISTINCT FROM jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module)
  THEN RAISE EXCEPTION 'original import creation linkage required' USING ERRCODE='55000';END IF;
  -- Keep the historical scalar-import qualification separate. Modern trusted
  -- imports read their immutable source facts directly, including owned roots.
  IF attempt.context->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() THEN
  IF attempt.next_index<>1 OR source_ledger.operation_index<>0 THEN
   RAISE EXCEPTION 'legacy singleton import creation required' USING ERRCODE='55000';END IF;
  import_record:=convert_from(source_ledger.original_record,'UTF8')::jsonb;
  import_payload:=decode(import_record->'payload'->>'bytesBase64','base64');
  IF encode(sha256(import_payload),'hex') IS DISTINCT FROM import_record->'payload'->>'sha256'
   OR (convert_from(import_payload,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  THEN RAISE EXCEPTION 'original import payload required' USING ERRCODE='55000';END IF;
  payload_value:=convert_from(import_payload,'UTF8')::jsonb;expected_source:='{}'::jsonb;
  input_header:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
  operation:=input_header->'operations'->source_ledger.operation_index;
  IF import_record->>'kind' IS DISTINCT FROM 'object' OR payload_value->>'kind' IS DISTINCT FROM 'object'
   OR operation->>'operation' IS DISTINCT FROM 'create_object'
   OR operation->>'typeDefinitionPin' IS DISTINCT FROM import_record->'identity'->'type'->>'definitionPin'
   OR operation->'values' IS DISTINCT FROM payload_value->'values' OR operation->'ownership' IS DISTINCT FROM payload_value->'ownership'
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(input_header->'assertedOrigin'->'entries') e
    WHERE e.value->>'key'='x-load-id' AND e.value->'value'=jsonb_build_object('kind','string','text',source_row.load_id))
  THEN RAISE EXCEPTION 'original import payload and creation correspondence required' USING ERRCODE='55000';END IF;
  IF payload_value->'source' IS NOT NULL THEN
   SELECT coalesce(jsonb_object_agg(source_entry->>'key',CASE source_entry->'value'->>'kind'
     WHEN 'string' THEN source_entry->'value'->'text' WHEN 'null' THEN 'null'::jsonb
     WHEN 'boolean' THEN source_entry->'value'->'value' ELSE source_entry->'value' END ORDER BY ordinal),'{}'::jsonb)
    INTO expected_source FROM jsonb_array_elements(payload_value->'source'->'entries') WITH ORDINALITY s(source_entry,ordinal);
  END IF;
  IF source_row.source IS DISTINCT FROM expected_source THEN RAISE EXCEPTION 'original import source facts required' USING ERRCODE='55000';END IF;
  END IF;
 END IF;
 PERFORM truss.query_scope(binding);
 IF root_identity IS NOT NULL AND NOT truss.runtime_can_read(root_identity->'owner'->>'documentId',root_identity->'owner'->>'moduleId') THEN RAISE EXCEPTION 'current attribution aggregate root reader required' USING ERRCODE='P1403';END IF;
 RETURN jsonb_build_object('_version',object_row.ver::text,'_created_by',created_actor,'_updated_by',updated_actor,
  '_original_author',source_row.source->'author','_original_at',source_row.source->'at');
END;
$$;
REVOKE ALL ON FUNCTION truss.query_object_attribution(jsonb,int,bigint) FROM PUBLIC;

-- Convert only a proven complete bounded result; never discard truncation.
CREATE FUNCTION truss.query_complete_related_keys(value jsonb,maximum int,key_arity int) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;item jsonb;
BEGIN
 IF maximum IS NULL OR maximum NOT BETWEEN 1 AND 100 OR key_arity IS NULL OR key_arity NOT BETWEEN 1 AND 128
  OR value IS NULL OR jsonb_typeof(value) IS DISTINCT FROM 'object' OR value-ARRAY['items','truncated']<>'{}'::jsonb
  OR jsonb_typeof(value->'items') IS DISTINCT FROM 'array' OR jsonb_typeof(value->'truncated') IS DISTINCT FROM 'boolean'
 THEN RAISE EXCEPTION 'exact complete relationship result required' USING ERRCODE='22023';END IF;
 IF value->'truncated'='true'::jsonb OR jsonb_array_length(value->'items')>maximum
 THEN RAISE EXCEPTION 'complete relationship cardinality exceeds bound' USING ERRCODE='54000';END IF;
 FOR item IN SELECT x.value FROM jsonb_array_elements(value->'items') x LOOP
  IF jsonb_typeof(item) IS DISTINCT FROM 'array' OR jsonb_array_length(item)<>key_arity
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(item) component WHERE jsonb_typeof(component.value) NOT IN ('string','boolean'))
  THEN RAISE EXCEPTION 'exact authored key tuple required' USING ERRCODE='22023';END IF;
 END LOOP;
 IF key_arity=1 THEN
  SELECT coalesce(jsonb_agg(x.value->0 ORDER BY x.ordinality),'[]'::jsonb) INTO result
   FROM jsonb_array_elements(value->'items') WITH ORDINALITY x(value,ordinality);
 ELSE result:=value->'items';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_complete_related_keys(jsonb,int,int) FROM PUBLIC;
