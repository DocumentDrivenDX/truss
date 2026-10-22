-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Append-only performance override: preserve the collector semantics while
-- accumulating owner and entry values in native arrays before one JSONB build.
CREATE OR REPLACE FUNCTION truss.runtime_read_mutation_group_audit(selected_attempt uuid,maximum_events int,
 expected_release text,expected_digest text,include_data boolean) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE actor oid;installation truss.catalog_runtime_installation%ROWTYPE;
 attempt truss.runtime_object_attempt%ROWTYPE;owner_values jsonb[]:=ARRAY[]::jsonb[];owner_union jsonb;
 owner jsonb;transition_row record;physical truss.journal%ROWTYPE;resolved jsonb;
 entry jsonb;event jsonb;original bytea;image jsonb;member jsonb;schema_metadata jsonb;
 property_context jsonb;event_pin text;image_revision int;image_type int;operation_index int;
 event_count int:=0;byte_count int:=0;entry_values jsonb[]:=ARRAY[]::jsonb[];entries jsonb;operation_entries jsonb;
 edge_context jsonb;endpoint jsonb;operation_name text;actor_name text;group_action text;
 plan_row record;owner_candidate jsonb;owner_count int;scope_entry jsonb;image_map jsonb;projected_entries jsonb;projected_data jsonb;node jsonb;side text;key_entry record;key_values jsonb;key_rows jsonb;result_bytes bytea;
BEGIN
 actor:=truss.runtime_person(false);
 IF include_data IS NULL OR selected_attempt IS NULL OR maximum_events IS NULL OR maximum_events NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'bounded complete mutation group required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest
  OR pg_is_in_recovery() THEN RAISE EXCEPTION 'selected retained mutation audit required' USING ERRCODE='0A000';END IF;
 SELECT * INTO attempt FROM truss.runtime_object_attempt a WHERE a.id=selected_attempt AND a.complete
  AND a.writer_xid<pg_catalog.pg_snapshot_xmin(pg_catalog.pg_current_snapshot());
 IF NOT FOUND THEN RAISE EXCEPTION 'committed complete mutation group required' USING ERRCODE='P0002';END IF;
 IF attempt.context->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() THEN
  RAISE EXCEPTION 'retained mutation audit profile unsupported' USING ERRCODE='0A000';END IF;
 IF attempt.next_index<1 OR attempt.result_count<>attempt.next_index
  OR (SELECT count(*) FROM truss.runtime_owned_operation o WHERE o.attempt_id=attempt.id
      AND o.writer_xid=attempt.writer_xid AND o.result IS NOT NULL)<>attempt.next_index THEN
  RAISE EXCEPTION 'complete retained operation census required' USING ERRCODE='P1010';END IF;
 IF octet_length(attempt.input_bytes)>1048576 THEN RAISE EXCEPTION 'retained mutation input too large' USING ERRCODE='54000';END IF;
 -- Preserve the actor captured by the native attempt even if its login role
 -- was later renamed or removed. No role-name lookup is part of audit identity.
 SELECT min(p.plan->>'actorName'),count(DISTINCT p.plan->>'actorName') INTO actor_name,owner_count
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.writer_xid=attempt.writer_xid;
 IF actor_name IS NULL OR owner_count<>1 THEN RAISE EXCEPTION 'retained native actor name unavailable' USING ERRCODE='P1010';END IF;
 IF jsonb_typeof(attempt.context->'originalAssertedOrigin'->'entries')='array'
  AND (SELECT count(*)=1 FROM jsonb_array_elements(attempt.context->'originalAssertedOrigin'->'entries') e
       WHERE e.value->>'key'='x-action')
  AND (SELECT count(*)=1 FROM jsonb_array_elements(attempt.context->'originalAssertedOrigin'->'entries') e
       WHERE e.value->>'key'='x-action' AND e.value->'value'->>'kind'='string'
        AND jsonb_typeof(e.value->'value'->'text')='string'
        AND octet_length(e.value->'value'->>'text') BETWEEN 1 AND 4096) THEN
  SELECT e.value->'value'->>'text' INTO group_action
   FROM jsonb_array_elements(attempt.context->'originalAssertedOrigin'->'entries') e WHERE e.value->>'key'='x-action';
 END IF;

 -- Retained plans cover unchanged operations that have no journal row. These
 -- plans are immutable witnesses; every owner-shaped item is conservatively
 -- included, and all exact property-reader dependencies are added from the
 -- image's own retained catalog revision.
 FOR plan_row IN SELECT p.operation_index,p.plan,p.result FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=attempt.id AND p.writer_xid=attempt.writer_xid ORDER BY p.operation_index LOOP
  IF plan_row.operation_index<0 OR plan_row.operation_index>=attempt.next_index
   OR plan_row.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
   OR plan_row.plan->'operationIndex' IS DISTINCT FROM to_jsonb(plan_row.operation_index)
   OR plan_row.plan->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
   OR plan_row.result IS NULL THEN RAISE EXCEPTION 'complete immutable operation plan required' USING ERRCODE='P1010';END IF;
  owner_count:=0;
  FOR owner_candidate IN SELECT jsonb_path_query(plan_row.plan,
   '$.** ? (@.documentId.type() == "string" && @.moduleId.type() == "string")') LOOP
   IF octet_length(owner_candidate->>'documentId') NOT BETWEEN 1 AND 4096
    OR octet_length(owner_candidate->>'moduleId') NOT BETWEEN 1 AND 4096 THEN
    RAISE EXCEPTION 'bounded operation-plan owner required' USING ERRCODE='P1010';END IF;
   owner_values:=array_append(owner_values,coalesce(jsonb_build_object(
    'documentId',owner_candidate->>'documentId','moduleId',owner_candidate->>'moduleId'),'null'::jsonb));
   owner_count:=owner_count+1;
  END LOOP;
  IF owner_count=0 THEN RAISE EXCEPTION 'complete operation-plan owner scope required' USING ERRCODE='P1010';END IF;
  FOR image_map IN SELECT value FROM (VALUES(plan_row.plan->'beforeNodes'),(plan_row.plan->'afterNodes')) x(value)
   WHERE jsonb_typeof(value)='object' LOOP
   FOR image IN SELECT n.value->'image' FROM jsonb_each(image_map) n(key,value)
    WHERE jsonb_typeof(n.value->'image')='object' LOOP
    image_revision:=(image->>'rev')::int;image_type:=(image->>'type_id')::int;
    IF image_revision IS NULL OR image_type IS NULL THEN RAISE EXCEPTION 'retained image catalog coordinate required' USING ERRCODE='P1010';END IF;
    SELECT s.metadata INTO STRICT schema_metadata FROM truss.runtime_type_schema s
     WHERE s.rev=image_revision AND s.type_id=image_type;
    IF jsonb_typeof(schema_metadata->'propertyAccess') IS DISTINCT FROM 'object' THEN
     RAISE EXCEPTION 'retained type property scope unavailable' USING ERRCODE='P1010';END IF;
    FOR scope_entry IN SELECT value FROM jsonb_each(schema_metadata->'propertyAccess') LOOP
     IF (scope_entry->>'itemsValid')::boolean IS NOT TRUE OR jsonb_typeof(scope_entry->'readers') IS DISTINCT FROM 'array' THEN
      RAISE EXCEPTION 'retained property readers unavailable' USING ERRCODE='P1010';END IF;
     FOR owner_candidate IN SELECT value FROM jsonb_array_elements(scope_entry->'readers') LOOP
      IF jsonb_typeof(owner_candidate) IS DISTINCT FROM 'object'
       OR jsonb_typeof(owner_candidate->'documentId') IS DISTINCT FROM 'string'
       OR jsonb_typeof(owner_candidate->'moduleId') IS DISTINCT FROM 'string' THEN
       RAISE EXCEPTION 'retained property owner unavailable' USING ERRCODE='P1010';END IF;
      owner_values:=array_append(owner_values,coalesce(owner_candidate,'null'::jsonb));
     END LOOP;
    END LOOP;
   END LOOP;
  END LOOP;
 END LOOP;

 FOR transition_row IN
  SELECT t.operation_index,t.writer_xid,'object'::text AS kind,t.object_id AS entity_id,
   t.type_id AS entity_type,t.journal
   FROM truss.runtime_object_transition t WHERE t.attempt_id=attempt.id AND t.writer_xid=attempt.writer_xid
  UNION ALL
  SELECT t.operation_index,t.writer_xid,'edge'::text,t.edge_id,t.rel_type_id,t.journal
   FROM truss.runtime_edge_transition t WHERE t.attempt_id=attempt.id AND t.writer_xid=attempt.writer_xid
  ORDER BY operation_index,kind,entity_id
 LOOP
  event_count:=event_count+1;
  IF event_count>maximum_events THEN RAISE EXCEPTION 'whole mutation group exceeds audit event limit' USING ERRCODE='54000';END IF;
  IF transition_row.kind='edge' THEN
   SELECT t.endpoint_ownership INTO edge_context FROM truss.runtime_edge_transition t
    WHERE t.attempt_id=attempt.id AND t.operation_index=transition_row.operation_index
     AND t.writer_xid=attempt.writer_xid AND t.edge_id=transition_row.entity_id AND t.rel_type_id=transition_row.entity_type;
   IF edge_context IS NULL OR
    (jsonb_typeof(edge_context->'before') IS DISTINCT FROM 'object' AND jsonb_typeof(edge_context->'before') IS DISTINCT FROM 'null') OR
    (jsonb_typeof(edge_context->'after') IS DISTINCT FROM 'object' AND jsonb_typeof(edge_context->'after') IS DISTINCT FROM 'null') THEN
    RAISE EXCEPTION 'retained endpoint ownership unavailable' USING ERRCODE='P1010';END IF;
   FOR endpoint IN SELECT value FROM jsonb_array_elements(jsonb_build_array(
     edge_context->'before'->'source',edge_context->'before'->'target',
     edge_context->'after'->'source',edge_context->'after'->'target')) WHERE value<>'null'::jsonb LOOP
    owner:=endpoint->'identity'->'owner';
    IF jsonb_typeof(owner) IS DISTINCT FROM 'object' OR owner-ARRAY['documentId','moduleId']<>'{}'::jsonb THEN
     RAISE EXCEPTION 'retained endpoint identity owner unavailable' USING ERRCODE='P1010';END IF;
    owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));
    IF endpoint->'ownership'->>'state'='owned' THEN
     owner:=endpoint->'ownership'->'root'->'owner';
     IF jsonb_typeof(owner) IS DISTINCT FROM 'object' OR owner-ARRAY['documentId','moduleId']<>'{}'::jsonb THEN
      RAISE EXCEPTION 'retained endpoint root owner unavailable' USING ERRCODE='P1010';END IF;
     owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));
    ELSIF endpoint->'ownership'->>'state' IS DISTINCT FROM 'rootless' THEN
     RAISE EXCEPTION 'retained endpoint ownership state unavailable' USING ERRCODE='P1010';END IF;
   END LOOP;
  END IF;
  IF jsonb_typeof(transition_row.journal) IS DISTINCT FROM 'array' THEN
   RAISE EXCEPTION 'retained group journal unavailable' USING ERRCODE='P1010';END IF;
  resolved:=truss.runtime_owned_journal_materialize(transition_row.journal);
  FOR entry IN SELECT value FROM jsonb_array_elements(resolved) LOOP
   IF jsonb_typeof(entry) IS DISTINCT FROM 'object' OR entry-ARRAY['seq','at','xid','entity_kind','entity_id','entity_type','ver','op','prop_id','old_value','new_value','rev','origin']<>'{}'::jsonb THEN
    RAISE EXCEPTION 'closed retained journal row required' USING ERRCODE='55000';END IF;
   physical:=jsonb_populate_record(NULL::truss.journal,entry);
   byte_count:=byte_count+octet_length(physical.new_value::text)+octet_length(physical.origin::text);
   IF byte_count>4194304 THEN RAISE EXCEPTION 'whole mutation group audit exceeds byte limit' USING ERRCODE='54000';END IF;
   IF physical.xid IS DISTINCT FROM attempt.writer_xid OR physical.entity_id IS DISTINCT FROM transition_row.entity_id
    OR physical.entity_type IS DISTINCT FROM transition_row.entity_type
    OR physical.entity_kind IS DISTINCT FROM (CASE WHEN transition_row.kind='object' THEN 'o'::char(1) ELSE 'e'::char(1) END)
    OR physical.new_value->>'component' IS DISTINCT FROM 'event' THEN
    RAISE EXCEPTION 'retained journal transition correspondence required' USING ERRCODE='55000';END IF;
   BEGIN
    original:=decode(physical.new_value->>'bytesBase64','base64');
    IF physical.new_value IS DISTINCT FROM truss.runtime_exact_wrapper('event',original)
     OR (convert_from(original,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
     RAISE EXCEPTION 'exact retained event required' USING ERRCODE='55000';END IF;
    event:=convert_from(original,'UTF8')::jsonb;
   EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'retained event unavailable' USING ERRCODE='P1010';END;
   IF event->>'interfaceVersion' IS DISTINCT FROM 'truss-history-event/0.2.0-proposal'
   OR (event->>'historyProfile' IN ('truss-native-scalar-create/0.2','truss-native-owned-create/0.1',
     'truss-native-scalar-mutation/0.1','truss-native-owned-mutation/0.1',
     'truss-native-edge-mutation/0.1','truss-native-owned-edge-mutation/0.1')) IS NOT TRUE
    OR event->>'sourceEpoch' IS DISTINCT FROM installation.source_epoch::text
    OR event->>'xid' IS DISTINCT FROM physical.xid::text OR event->>'seq' IS DISTINCT FROM physical.seq::text
    OR event->>'eventVersion' IS DISTINCT FROM physical.ver::text
    OR event->>'eventCatalogRevision' IS DISTINCT FROM physical.rev::text
    OR event->'identity'->>'id' IS DISTINCT FROM physical.entity_id::text
    OR event->'identity'->>'typeId' IS DISTINCT FROM physical.entity_type::text
    OR physical.op IS DISTINCT FROM (CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END)
    OR physical.prop_id IS DISTINCT FROM (event->>'propertyId')::int
    OR physical.origin IS DISTINCT FROM truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8')) THEN
    RAISE EXCEPTION 'retained event provenance unavailable' USING ERRCODE='55000';END IF;
   IF transition_row.kind='object' THEN
    SELECT s.metadata->>'typePin' INTO event_pin FROM truss.runtime_type_schema s
     WHERE s.rev=physical.rev AND s.type_id=physical.entity_type;
   ELSE event_pin:=truss.runtime_relationship_pin(physical.entity_type,physical.rev);END IF;
   IF event_pin IS NULL OR event->'identity'->>'definitionPin' IS DISTINCT FROM event_pin THEN
    RAISE EXCEPTION 'retained event definition pin unavailable' USING ERRCODE='P1010';END IF;
   owner:=event->'identity'->'owner';
   IF jsonb_typeof(owner) IS DISTINCT FROM 'object' OR owner-ARRAY['documentId','moduleId']<>'{}'::jsonb
    OR jsonb_typeof(owner->'documentId') IS DISTINCT FROM 'string' OR jsonb_typeof(owner->'moduleId') IS DISTINCT FROM 'string' THEN
    RAISE EXCEPTION 'complete retained entity owner required' USING ERRCODE='P1010';END IF;
   owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));
   IF event->>'operation' IN ('create','metadata','delete') THEN
    FOR image IN SELECT value FROM jsonb_array_elements(jsonb_build_array(event->'before',event->'after'))
     WHERE value IS NOT NULL AND value<>'null'::jsonb LOOP
     image_revision:=(image->>'catalogRevision')::int;image_type:=(image->'identity'->>'typeId')::int;
     owner:=image->'identity'->'owner';
     IF jsonb_typeof(owner) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'retained image owner unavailable' USING ERRCODE='P1010';END IF;
     owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));
     IF image->'ownership'->>'state'='owned' THEN
      owner:=image->'ownership'->'root'->'owner';
      IF jsonb_typeof(owner) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'retained root owner unavailable' USING ERRCODE='P1010';END IF;
      owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));
     END IF;
     IF transition_row.kind='edge' THEN
      FOR endpoint IN SELECT value FROM jsonb_array_elements(jsonb_build_array(image->'source',image->'target')) LOOP
       owner:=endpoint->'owner';
       IF jsonb_typeof(owner) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'retained edge endpoint owner unavailable' USING ERRCODE='P1010';END IF;
       owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));
      END LOOP;
     END IF;
     FOR member IN SELECT value FROM jsonb_array_elements(image->'properties') LOOP
      SELECT s.metadata INTO STRICT schema_metadata FROM truss.runtime_type_schema s WHERE s.rev=image_revision AND s.type_id=image_type;
      property_context:=schema_metadata->'propertyAccess'->(member->>'propertyId');
      event_pin:=schema_metadata->'propertyPins'->>(member->>'propertyId');
      IF event_pin IS DISTINCT FROM member->>'definitionPin' OR property_context IS NULL
       OR (property_context->>'itemsValid')::boolean IS NOT TRUE OR jsonb_typeof(property_context->'readers') IS DISTINCT FROM 'array' THEN
       RAISE EXCEPTION 'retained property scope unavailable' USING ERRCODE='P1010';END IF;
      FOR owner IN SELECT value FROM jsonb_array_elements(property_context->'readers') LOOP
       owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));
      END LOOP;
     END LOOP;
    END LOOP;
   ELSIF event->>'operation' IN ('property','rebind') THEN
    SELECT s.metadata INTO STRICT schema_metadata FROM truss.runtime_type_schema s
     WHERE s.rev=physical.rev AND s.type_id=physical.entity_type;
    event_pin:=CASE WHEN event->>'operation'='rebind' THEN event->>'afterDefinitionPin' ELSE event->>'definitionPin' END;
    property_context:=schema_metadata->'propertyAccess'->physical.prop_id::text;
    IF schema_metadata->'propertyPins'->>physical.prop_id::text IS DISTINCT FROM event_pin OR property_context IS NULL
     OR (property_context->>'itemsValid')::boolean IS NOT TRUE OR jsonb_typeof(property_context->'readers') IS DISTINCT FROM 'array' THEN
     RAISE EXCEPTION 'retained property delta scope unavailable' USING ERRCODE='P1010';END IF;
    FOR owner IN SELECT value FROM jsonb_array_elements(property_context->'readers') LOOP owner_values:=array_append(owner_values,coalesce(owner,'null'::jsonb));END LOOP;
   ELSE RAISE EXCEPTION 'retained operation profile unsupported' USING ERRCODE='0A000';END IF;
   entry_values:=array_append(entry_values,jsonb_build_object('operationIndex',transition_row.operation_index::text,
    'entityKind',transition_row.kind,'entityId',transition_row.entity_id::text,'entityType',transition_row.entity_type::text,
    'operation',event->>'operation','observedAt',to_char(physical.at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
  END LOOP;
 END LOOP;
 -- A completed unchanged operation has no event row. Its sealed plan/result
 -- is still a retained native observation, with a timestamp captured when the
 -- attempt row was created. Never manufacture an audit time at read time.
 FOR plan_row IN SELECT p.operation_index,p.plan,p.result FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=attempt.id AND p.writer_xid=attempt.writer_xid ORDER BY p.operation_index LOOP
  IF NOT EXISTS(SELECT 1 FROM unnest(entry_values) e(value)
   WHERE e.value->>'operationIndex'=plan_row.operation_index::text) THEN
   IF attempt.audit_observed_at IS NULL THEN RAISE EXCEPTION 'no-op attempt observation unavailable' USING ERRCODE='P1010';END IF;
   operation_name:=plan_row.result->>'operation';
   image:=plan_row.result->'identity';
   IF operation_name NOT IN ('create_object','update_object','delete_object','create_edge','update_edge','delete_edge')
    OR jsonb_typeof(image) IS DISTINCT FROM 'object'
    OR jsonb_typeof(image->'id') IS DISTINCT FROM 'string'
    OR jsonb_typeof(image->'typeId') IS DISTINCT FROM 'string' THEN
    RAISE EXCEPTION 'no-op retained identity unavailable' USING ERRCODE='P1010';END IF;
   entry_values:=array_append(entry_values,jsonb_build_object('operationIndex',plan_row.operation_index::text,
    'entityKind',CASE WHEN operation_name LIKE '%_edge' THEN 'edge' ELSE 'object' END,
    'entityId',image->>'id','entityType',image->>'typeId','operation',operation_name,
    'observedAt',to_char(attempt.audit_observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
  END IF;
 END LOOP;
 entries:=coalesce(to_jsonb(entry_values),'[]'::jsonb);
 IF jsonb_array_length(entries)=0 THEN RAISE EXCEPTION 'retained group has no supported operation evidence' USING ERRCODE='P1010';END IF;
 IF jsonb_array_length(entries)>maximum_events THEN RAISE EXCEPTION 'whole group exceeds audit page limit' USING ERRCODE='54000';END IF;
 owner_union:=coalesce(to_jsonb(owner_values),'[]'::jsonb);
 SELECT coalesce(jsonb_agg(value ORDER BY value->>'documentId',value->>'moduleId'),'[]'::jsonb) INTO owner_union
  FROM (SELECT DISTINCT value FROM jsonb_array_elements(owner_union)) owners;
 IF jsonb_array_length(owner_union)>4096 THEN RAISE EXCEPTION 'complete audit owner union exceeds limit' USING ERRCODE='54000';END IF;
 FOR owner IN SELECT value FROM jsonb_array_elements(owner_union) LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
   AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
   RAISE EXCEPTION 'complete mutation group audit membership required' USING ERRCODE='P1403';END IF;
 END LOOP;
 IF include_data THEN
  FOR owner IN SELECT value FROM jsonb_array_elements(owner_union) LOOP
   IF truss.runtime_can_read(owner->>'documentId',owner->>'moduleId') IS NOT TRUE THEN
    RAISE EXCEPTION 'separate complete retained data readership required' USING ERRCODE='P1403';END IF;
  END LOOP;
  projected_entries:='[]'::jsonb;
  FOR entry IN SELECT value FROM jsonb_array_elements(entries) LOOP
   image_map:=truss.runtime_owned_plan(attempt.id,(entry->>'operationIndex')::int);
   projected_data:=jsonb_build_object('basis','retained-operation','before',NULL,'after',NULL);
   FOREACH side IN ARRAY ARRAY['before','after'] LOOP
    SELECT n.value INTO node FROM jsonb_each(image_map->(side||CASE WHEN entry->>'entityKind'='edge' THEN 'Edges' ELSE 'Nodes' END)) n
     WHERE truss.runtime_owned_identity(attempt.id,(entry->>'operationIndex')::int,n.key,entry->>'entityKind',image_map,attempt)->>'id'=entry->>'entityId'
      AND n.value->'identity'->>'typeId'=entry->>'entityType';
    image:=node->'image';key_rows:='[]'::jsonb;
    IF image IS NOT NULL AND image<>'null'::jsonb THEN
     IF entry->>'entityKind'='object' THEN
      FOR key_entry IN SELECT k.key_id,k.key_num,k.prop_ids,d.definition_pin
       FROM jsonb_populate_recordset(NULL::truss.key_def,truss.catalog_all_expected_records((image->>'rev')::int)->'key_def') k JOIN truss.type_def t ON t.type_id=k.type_id
       JOIN truss.runtime_definition_source d ON d.rev=k.definition_rev AND d.ord=k.definition_doc_ord
        AND d.doc_id=k.definition_document_id AND d.module_id=t.module AND d.element_id=t.element AND d.kind='key' AND d.key_id=k.key_id
       WHERE k.type_id=(entry->>'entityType')::int AND k.since_rev<=(image->>'rev')::int
        AND (k.retired_rev IS NULL OR k.retired_rev>(image->>'rev')::int) ORDER BY k.key_num LOOP
       SELECT jsonb_agg(image->'props'->p.id::text ORDER BY p.ordinality) INTO key_values
        FROM unnest(key_entry.prop_ids) WITH ORDINALITY p(id,ordinality);
       IF key_values IS NULL OR EXISTS(SELECT 1 FROM jsonb_array_elements(key_values) v WHERE v.value='null'::jsonb) THEN
        RAISE EXCEPTION 'complete retained key values unavailable' USING ERRCODE='P1010';END IF;
       key_rows:=key_rows||jsonb_build_array(jsonb_build_object('keyId',key_entry.key_id,'keyNumber',key_entry.key_num::text,
        'definitionPin',key_entry.definition_pin,'values',key_values));
      END LOOP;
     END IF;
     projected_data:=jsonb_set(projected_data,ARRAY[side],jsonb_build_object('version',image->>'ver','keys',key_rows));
    END IF;
   END LOOP;
   IF projected_data->'before'='null'::jsonb AND projected_data->'after'='null'::jsonb THEN RAISE EXCEPTION 'retained operation images unavailable' USING ERRCODE='P1010';END IF;
   projected_entries:=projected_entries||jsonb_build_array(entry||jsonb_build_object('data',projected_data));
  END LOOP;
  entries:=projected_entries;
  IF octet_length(entries::text)>1048576 THEN RAISE EXCEPTION 'projected audit byte bound exceeded' USING ERRCODE='54000';END IF;
 END IF;
 -- Recheck every original owner after constructing the whole-group projection.
 FOR owner IN SELECT value FROM jsonb_array_elements(owner_union) LOOP
  IF include_data AND truss.runtime_can_read(owner->>'documentId',owner->>'moduleId') IS NOT TRUE THEN RAISE EXCEPTION 'retained data readership changed' USING ERRCODE='P1403';END IF;
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
   AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
   RAISE EXCEPTION 'mutation group audit authority changed before release' USING ERRCODE='P1403';END IF;
 END LOOP;
 PERFORM truss.runtime_person(false);
 result_bytes:=convert_to(jsonb_build_object('outcome','page','attemptId',attempt.id::text,
  'nativeActorOid',attempt.actor_oid::text,'nativeActorName',actor_name,'assertedAction',group_action,'writerXid',attempt.writer_xid::text,
  'observedAt',to_char(attempt.audit_observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'ownerScopes',owner_union,
  'operationCount',attempt.next_index::text,'eventCount',jsonb_array_length(entries)::text,'entries',entries)::text,'UTF8');
 IF octet_length(result_bytes)>1048576 THEN RAISE EXCEPTION 'complete audit response exceeds byte bound' USING ERRCODE='54000';END IF;
 RETURN result_bytes;
END;
$$;
