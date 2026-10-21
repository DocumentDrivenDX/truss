-- Metadata-only whole mutation-attempt audit. This is separate from ordinary
-- history: a module auditor can see identities and operation metadata without
-- receiving object values, keys, origins, or source payloads.
ALTER TABLE truss.runtime_object_attempt ADD COLUMN IF NOT EXISTS audit_observed_at timestamptz;
ALTER TABLE truss.runtime_object_attempt ALTER COLUMN audit_observed_at SET DEFAULT clock_timestamp();
-- Recover a truthful event observation for retained historical groups that
-- already have journal evidence. No-op groups without a retained timestamp
-- remain unavailable rather than receiving an invented migration-time date.
UPDATE truss.runtime_object_attempt a SET audit_observed_at=(
 SELECT max(observed_at) FROM (
  SELECT (j.value->>'at')::timestamptz observed_at FROM truss.runtime_object_transition t
   CROSS JOIN LATERAL jsonb_array_elements(t.journal) j(value) WHERE t.attempt_id=a.id AND t.writer_xid=a.writer_xid
  UNION ALL
  SELECT (j.value->>'at')::timestamptz FROM truss.runtime_edge_transition t
   CROSS JOIN LATERAL jsonb_array_elements(t.journal) j(value) WHERE t.attempt_id=a.id AND t.writer_xid=a.writer_xid
 ) retained_events)
 WHERE a.audit_observed_at IS NULL AND a.complete;
CREATE INDEX IF NOT EXISTS runtime_object_attempt_audit_observed
 ON truss.runtime_object_attempt(audit_observed_at DESC,id DESC) WHERE complete;

CREATE FUNCTION truss.read_mutation_group_audit(selected_attempt uuid,maximum_events int,
 expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE actor oid;installation truss.catalog_runtime_installation%ROWTYPE;
 attempt truss.runtime_object_attempt%ROWTYPE;owner_union jsonb:='[]'::jsonb;
 owner jsonb;transition_row record;physical truss.journal%ROWTYPE;resolved jsonb;
 entry jsonb;event jsonb;original bytea;image jsonb;member jsonb;schema_metadata jsonb;
 property_context jsonb;event_pin text;image_revision int;image_type int;operation_index int;
 event_count int:=0;byte_count int:=0;entries jsonb:='[]'::jsonb;operation_entries jsonb;
 edge_context jsonb;endpoint jsonb;operation_name text;actor_name text;group_action text;
 plan_row record;owner_candidate jsonb;owner_count int;scope_entry jsonb;image_map jsonb;
BEGIN
 actor:=truss.runtime_person(false);
 IF selected_attempt IS NULL OR maximum_events IS NULL OR maximum_events NOT BETWEEN 1 AND 1024 THEN
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
   owner_union:=owner_union||jsonb_build_array(jsonb_build_object(
    'documentId',owner_candidate->>'documentId','moduleId',owner_candidate->>'moduleId'));
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
      owner_union:=owner_union||jsonb_build_array(owner_candidate);
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
    owner_union:=owner_union||jsonb_build_array(owner);
    IF endpoint->'ownership'->>'state'='owned' THEN
     owner:=endpoint->'ownership'->'root'->'owner';
     IF jsonb_typeof(owner) IS DISTINCT FROM 'object' OR owner-ARRAY['documentId','moduleId']<>'{}'::jsonb THEN
      RAISE EXCEPTION 'retained endpoint root owner unavailable' USING ERRCODE='P1010';END IF;
     owner_union:=owner_union||jsonb_build_array(owner);
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
   owner_union:=owner_union||jsonb_build_array(owner);
   IF event->>'operation' IN ('create','metadata','delete') THEN
    FOR image IN SELECT value FROM jsonb_array_elements(jsonb_build_array(event->'before',event->'after'))
     WHERE value IS NOT NULL AND value<>'null'::jsonb LOOP
     image_revision:=(image->>'catalogRevision')::int;image_type:=(image->'identity'->>'typeId')::int;
     owner:=image->'identity'->'owner';
     IF jsonb_typeof(owner) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'retained image owner unavailable' USING ERRCODE='P1010';END IF;
     owner_union:=owner_union||jsonb_build_array(owner);
     IF image->'ownership'->>'state'='owned' THEN
      owner:=image->'ownership'->'root'->'owner';
      IF jsonb_typeof(owner) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'retained root owner unavailable' USING ERRCODE='P1010';END IF;
      owner_union:=owner_union||jsonb_build_array(owner);
     END IF;
     IF transition_row.kind='edge' THEN
      FOR endpoint IN SELECT value FROM jsonb_array_elements(jsonb_build_array(image->'source',image->'target')) LOOP
       owner:=endpoint->'owner';
       IF jsonb_typeof(owner) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'retained edge endpoint owner unavailable' USING ERRCODE='P1010';END IF;
       owner_union:=owner_union||jsonb_build_array(owner);
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
       owner_union:=owner_union||jsonb_build_array(owner);
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
    FOR owner IN SELECT value FROM jsonb_array_elements(property_context->'readers') LOOP owner_union:=owner_union||jsonb_build_array(owner);END LOOP;
   ELSE RAISE EXCEPTION 'retained operation profile unsupported' USING ERRCODE='0A000';END IF;
   entries:=entries||jsonb_build_array(jsonb_build_object('operationIndex',transition_row.operation_index::text,
    'entityKind',transition_row.kind,'entityId',transition_row.entity_id::text,'entityType',transition_row.entity_type::text,
    'operation',event->>'operation','observedAt',to_char(physical.at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
  END LOOP;
 END LOOP;
 -- A completed unchanged operation has no event row. Its sealed plan/result
 -- is still a retained native observation, with a timestamp captured when the
 -- attempt row was created. Never manufacture an audit time at read time.
 FOR plan_row IN SELECT p.operation_index,p.plan,p.result FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=attempt.id AND p.writer_xid=attempt.writer_xid ORDER BY p.operation_index LOOP
  IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(entries) e
   WHERE e.value->>'operationIndex'=plan_row.operation_index::text) THEN
   IF attempt.audit_observed_at IS NULL THEN RAISE EXCEPTION 'no-op attempt observation unavailable' USING ERRCODE='P1010';END IF;
   operation_name:=plan_row.result->>'operation';
   image:=plan_row.result->'identity';
   IF operation_name NOT IN ('create_object','update_object','delete_object','create_edge','update_edge','delete_edge')
    OR jsonb_typeof(image) IS DISTINCT FROM 'object'
    OR jsonb_typeof(image->'id') IS DISTINCT FROM 'string'
    OR jsonb_typeof(image->'typeId') IS DISTINCT FROM 'string' THEN
    RAISE EXCEPTION 'no-op retained identity unavailable' USING ERRCODE='P1010';END IF;
   entries:=entries||jsonb_build_array(jsonb_build_object('operationIndex',plan_row.operation_index::text,
    'entityKind',CASE WHEN operation_name LIKE '%_edge' THEN 'edge' ELSE 'object' END,
    'entityId',image->>'id','entityType',image->>'typeId','operation',operation_name,
    'observedAt',to_char(attempt.audit_observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')));
  END IF;
 END LOOP;
 IF jsonb_array_length(entries)=0 THEN RAISE EXCEPTION 'retained group has no supported operation evidence' USING ERRCODE='P1010';END IF;
 IF jsonb_array_length(entries)>maximum_events THEN RAISE EXCEPTION 'whole group exceeds audit page limit' USING ERRCODE='54000';END IF;
 SELECT coalesce(jsonb_agg(value ORDER BY value->>'documentId',value->>'moduleId'),'[]'::jsonb) INTO owner_union
  FROM (SELECT DISTINCT value FROM jsonb_array_elements(owner_union)) owners;
 IF jsonb_array_length(owner_union)>4096 THEN RAISE EXCEPTION 'complete audit owner union exceeds limit' USING ERRCODE='54000';END IF;
 FOR owner IN SELECT value FROM jsonb_array_elements(owner_union) LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
   AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
   RAISE EXCEPTION 'complete mutation group audit membership required' USING ERRCODE='42501';END IF;
 END LOOP;
 -- Recheck every original owner after constructing the whole-group projection.
 FOR owner IN SELECT value FROM jsonb_array_elements(owner_union) LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
   AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
   RAISE EXCEPTION 'mutation group audit authority changed before release' USING ERRCODE='42501';END IF;
 END LOOP;
 PERFORM truss.runtime_person(false);
 RETURN convert_to(jsonb_build_object('outcome','page','attemptId',attempt.id::text,
  'nativeActorOid',attempt.actor_oid::text,'nativeActorName',actor_name,'assertedAction',group_action,'writerXid',attempt.writer_xid::text,
  'observedAt',to_char(attempt.audit_observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'ownerScopes',owner_union,
  'operationCount',attempt.next_index::text,'eventCount',jsonb_array_length(entries)::text,'entries',entries)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.read_mutation_group_audit(uuid,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_mutation_audit_cursor(selected_installation uuid,selected_epoch uuid,
 selected_release text,selected_digest text,frontier xid8,selected_filters_sha text,
 last_observed timestamptz,last_attempt uuid) RETURNS bytea
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT convert_to(jsonb_build_object('profile','truss-mutation-group-audit-cursor/0.2',
  'installationId',selected_installation::text,'sourceEpoch',selected_epoch,
  'releaseId',selected_release,'releaseSha256',selected_digest,
  'frontierXid',frontier::text,'filtersSha256',selected_filters_sha,
  'afterObservedAt',to_char(last_observed AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'afterAttemptId',last_attempt::text)::text,'UTF8');
$$;
REVOKE ALL ON FUNCTION truss.runtime_mutation_audit_cursor(uuid,uuid,text,text,xid8,text,timestamptz,uuid) FROM PUBLIC;

-- Historical key filters are evaluated against the key codec and ordered
-- component values retained at each operation's catalog revision. No current
-- object row or live key bucket participates in selection.
CREATE FUNCTION truss.runtime_mutation_audit_key_matches(selected_attempt uuid,key_filter jsonb) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;operation_row record;image_map jsonb;node record;
 operation_plan jsonb;image jsonb;identity jsonb;revision int;type_number int;key_number smallint;basis jsonb;
 key_definition truss.key_def%ROWTYPE;definition_pin text;codec jsonb;cells jsonb;provided_tuple bytea;stored_tuple bytea;
 type_definition truss.type_def%ROWTYPE;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 type_number:=(key_filter->>'typeId')::int;key_number:=(key_filter->>'keyNumber')::smallint;
 FOR operation_row IN SELECT p.operation_index FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=attempt.id AND p.writer_xid=attempt.writer_xid LOOP
  operation_plan:=truss.runtime_owned_plan(attempt.id,operation_row.operation_index);
  FOR image_map IN SELECT value FROM (VALUES(operation_plan->'beforeNodes'),
       (operation_plan->'afterNodes')) x(value) WHERE jsonb_typeof(value)='object' LOOP
   FOR node IN SELECT value FROM jsonb_each(image_map) LOOP
    image:=node.value->'image';identity:=node.value->'identity';
    IF image IS NULL OR identity IS NULL OR image->>'type_id' IS DISTINCT FROM type_number::text
     OR identity->'owner' IS DISTINCT FROM jsonb_build_object(
       'documentId',key_filter->>'documentId','moduleId',key_filter->>'moduleId') THEN CONTINUE;END IF;
    revision:=(image->>'rev')::int;
    basis:=truss.catalog_all_expected_records(revision);
    SELECT k.* INTO key_definition FROM jsonb_populate_recordset(NULL::truss.key_def,basis->'key_def') k
     WHERE k.type_id=type_number AND k.key_num=key_number;
    IF NOT FOUND THEN CONTINUE;END IF;
    SELECT t.* INTO type_definition FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t
     WHERE t.type_id=type_number;
    IF NOT FOUND THEN RAISE EXCEPTION 'retained key owner definition unavailable' USING ERRCODE='P1010';END IF;
    SELECT d.definition_pin INTO definition_pin FROM truss.runtime_definition_source d
     WHERE d.rev=key_definition.definition_rev AND d.ord=key_definition.definition_doc_ord
      AND d.doc_id=key_definition.definition_document_id AND d.module_id=type_definition.module
      AND d.element_id=type_definition.element AND d.kind='key' AND d.key_id=key_definition.key_id;
    IF definition_pin IS DISTINCT FROM key_filter->>'definitionPin' THEN CONTINUE;END IF;
    SELECT s.metadata->'keyCodecs'->key_number::text INTO codec FROM truss.runtime_type_schema s
     WHERE s.rev=revision AND s.type_id=type_number;
    IF codec IS NULL THEN RAISE EXCEPTION 'retained key codec unavailable' USING ERRCODE='P1010';END IF;
    SELECT jsonb_agg(image->'props'->component.prop_id::text ORDER BY component.ordinality)
     INTO cells FROM unnest(key_definition.prop_ids) WITH ORDINALITY component(prop_id,ordinality);
    IF cells IS NULL OR EXISTS(SELECT 1 FROM jsonb_array_elements(cells) c WHERE c.value IS NULL OR c.value='null'::jsonb) THEN CONTINUE;END IF;
    provided_tuple:=truss.runtime_owned_key_tuple_in_metadata(type_number,key_number,key_filter->'values',codec);
    stored_tuple:=truss.runtime_owned_key_tuple_in_metadata(type_number,key_number,cells,codec);
    IF stored_tuple=provided_tuple THEN RETURN true;END IF;
   END LOOP;
  END LOOP;
 END LOOP;
 RETURN false;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_mutation_audit_key_matches(uuid,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_mutation_audit_identity_matches(selected_attempt uuid,selected_filters jsonb) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;operation_row record;plan jsonb;map_row record;
 reference text;identity jsonb;kind text;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 FOR operation_row IN SELECT p.operation_index FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=attempt.id AND p.writer_xid=attempt.writer_xid ORDER BY p.operation_index LOOP
  plan:=truss.runtime_owned_plan(attempt.id,operation_row.operation_index);
  FOR map_row IN SELECT * FROM (VALUES
    ('object',plan->'beforeNodes'),('object',plan->'afterNodes'),
    ('edge',plan->'beforeEdges'),('edge',plan->'afterEdges')) m(kind,value)
   WHERE jsonb_typeof(value)='object' LOOP
   kind:=map_row.kind;
   FOR reference IN SELECT key FROM jsonb_each(map_row.value) LOOP
    identity:=truss.runtime_owned_identity(attempt.id,operation_row.operation_index,reference,kind,plan,attempt);
    IF (NOT selected_filters ? 'entityId' OR identity->>'id'=selected_filters->>'entityId')
      AND (NOT selected_filters ? 'entityType' OR identity->>'typeId'=selected_filters->>'entityType')
      AND (NOT selected_filters ? 'documentId' OR
       (identity->'owner'->>'documentId'=selected_filters->>'documentId'
        AND identity->'owner'->>'moduleId'=selected_filters->>'moduleId')) THEN
     RETURN true;
    END IF;
   END LOOP;
  END LOOP;
 END LOOP;
 RETURN false;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_mutation_audit_identity_matches(uuid,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_mutation_audit_attempt_matches(selected_attempt uuid,selected_filters jsonb) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;identity_found boolean;action_value text;from_time timestamptz;until_time timestamptz;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF selected_filters ? 'attemptId' AND selected_filters->>'attemptId' IS DISTINCT FROM attempt.id::text THEN RETURN false;END IF;
 IF selected_filters ? 'nativeActorOid' AND selected_filters->>'nativeActorOid' IS DISTINCT FROM attempt.actor_oid::text THEN RETURN false;END IF;
 IF selected_filters ? 'assertedAction' THEN
  IF jsonb_typeof(attempt.context->'originalAssertedOrigin'->'entries')='array'
   AND (SELECT count(*)=1 FROM jsonb_array_elements(attempt.context->'originalAssertedOrigin'->'entries') e WHERE e.value->>'key'='x-action')
   AND (SELECT count(*)=1 FROM jsonb_array_elements(attempt.context->'originalAssertedOrigin'->'entries') e
     WHERE e.value->>'key'='x-action' AND e.value->'value'->>'kind'='string'
      AND jsonb_typeof(e.value->'value'->'text')='string'
      AND octet_length(e.value->'value'->>'text') BETWEEN 1 AND 4096) THEN
   SELECT e.value->'value'->>'text' INTO action_value
    FROM jsonb_array_elements(attempt.context->'originalAssertedOrigin'->'entries') e WHERE e.value->>'key'='x-action';
  END IF;
  IF action_value COLLATE pg_catalog."C" IS DISTINCT FROM (selected_filters->>'assertedAction') COLLATE pg_catalog."C" THEN RETURN false;END IF;
 END IF;
 IF selected_filters ? 'entityId' OR selected_filters ? 'entityType' THEN
  IF truss.runtime_mutation_audit_identity_matches(attempt.id,selected_filters) IS NOT TRUE THEN RETURN false;END IF;
 END IF;
 IF selected_filters ? 'entityKey' AND
   truss.runtime_mutation_audit_key_matches(attempt.id,selected_filters->'entityKey') IS NOT TRUE THEN RETURN false;END IF;
 BEGIN
  from_time:=CASE WHEN selected_filters ? 'observedAtFrom' THEN (selected_filters->>'observedAtFrom')::timestamptz END;
  until_time:=CASE WHEN selected_filters ? 'observedAtUntil' THEN (selected_filters->>'observedAtUntil')::timestamptz END;
 EXCEPTION WHEN SQLSTATE '22007' OR SQLSTATE '22008' THEN
  RAISE EXCEPTION 'canonical mutation audit timestamp required' USING ERRCODE='22023';
 END;
 IF from_time IS NOT NULL OR until_time IS NOT NULL THEN
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_object_transition t
    CROSS JOIN LATERAL jsonb_array_elements(t.journal) j(value)
    WHERE t.attempt_id=attempt.id AND t.writer_xid=attempt.writer_xid
     AND (from_time IS NULL OR (j.value->>'at')::timestamptz>=from_time)
     AND (until_time IS NULL OR (j.value->>'at')::timestamptz<until_time))
   AND NOT EXISTS(SELECT 1 FROM truss.runtime_edge_transition t
    CROSS JOIN LATERAL jsonb_array_elements(t.journal) j(value)
    WHERE t.attempt_id=attempt.id AND t.writer_xid=attempt.writer_xid
     AND (from_time IS NULL OR (j.value->>'at')::timestamptz>=from_time)
     AND (until_time IS NULL OR (j.value->>'at')::timestamptz<until_time))
   AND NOT (EXISTS(SELECT 1 FROM truss.runtime_owned_operation p
    WHERE p.attempt_id=attempt.id AND p.writer_xid=attempt.writer_xid
     AND NOT EXISTS(SELECT 1 FROM truss.runtime_object_transition t
      CROSS JOIN LATERAL jsonb_array_elements(t.journal) j(value)
      WHERE t.attempt_id=attempt.id AND t.operation_index=p.operation_index AND t.writer_xid=attempt.writer_xid)
     AND NOT EXISTS(SELECT 1 FROM truss.runtime_edge_transition t
      CROSS JOIN LATERAL jsonb_array_elements(t.journal) j(value)
      WHERE t.attempt_id=attempt.id AND t.operation_index=p.operation_index AND t.writer_xid=attempt.writer_xid))
    AND attempt.audit_observed_at IS NOT NULL
    AND (from_time IS NULL OR attempt.audit_observed_at>=from_time)
    AND (until_time IS NULL OR attempt.audit_observed_at<until_time)) THEN RETURN false;END IF;
 END IF;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_mutation_audit_attempt_matches(uuid,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.page_mutation_group_audit(filters jsonb,maximum_events int,original_cursor bytea,
 expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' AS $$
DECLARE actor oid;installation truss.catalog_runtime_installation%ROWTYPE;filter_sha text;
 cursor_value jsonb;frontier xid8;last_observed timestamptz;last_attempt uuid;candidate record;
 group_bytes bytea;group_value jsonb;cursor_bytes bytea;key_filter jsonb;release_check bytea;
BEGIN
 actor:=truss.runtime_person(false);
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a
   WHERE truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
  RAISE EXCEPTION 'current mutation audit enrollment required' USING ERRCODE='42501';END IF;
 IF filters IS NULL OR jsonb_typeof(filters) IS DISTINCT FROM 'object'
  OR filters-ARRAY['attemptId','documentId','moduleId','entityId','entityType','entityKey','nativeActorOid',
    'assertedAction','observedAtFrom','observedAtUntil']<>'{}'::jsonb
  OR octet_length(convert_to(filters::text,'UTF8'))>65536
  OR maximum_events IS NULL OR maximum_events NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'bounded mutation-group audit listing required' USING ERRCODE='22023';END IF;
 IF filters ? 'attemptId' AND (jsonb_typeof(filters->'attemptId') IS DISTINCT FROM 'string'
   OR filters->>'attemptId' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
  OR (filters ? 'documentId') IS NOT TRUE OR (filters ? 'moduleId') IS NOT TRUE
  OR filters ? 'entityId' AND (filters ? 'entityType') IS NOT TRUE
  OR filters ? 'nativeActorOid' AND (jsonb_typeof(filters->'nativeActorOid') IS DISTINCT FROM 'string'
   OR filters->>'nativeActorOid' !~ '^[1-9][0-9]{0,9}$' OR (filters->>'nativeActorOid')::numeric>4294967295)
  OR filters ? 'entityId' AND (jsonb_typeof(filters->'entityId') IS DISTINCT FROM 'string'
   OR filters->>'entityId' !~ '^[1-9][0-9]{0,18}$')
  OR filters ? 'entityType' AND (jsonb_typeof(filters->'entityType') IS DISTINCT FROM 'string'
   OR filters->>'entityType' !~ '^[1-9][0-9]{0,9}$')
  OR filters ? 'entityKey' AND (jsonb_typeof(filters->'entityKey') IS DISTINCT FROM 'object'
   OR (filters->'entityKey')-ARRAY['documentId','moduleId','typeId','keyNumber','definitionPin','values']<>'{}'::jsonb
   OR jsonb_typeof(filters->'entityKey'->'documentId') IS DISTINCT FROM 'string'
   OR octet_length(filters->'entityKey'->>'documentId') NOT BETWEEN 1 AND 4096
   OR jsonb_typeof(filters->'entityKey'->'moduleId') IS DISTINCT FROM 'string'
   OR octet_length(filters->'entityKey'->>'moduleId') NOT BETWEEN 1 AND 4096
   OR jsonb_typeof(filters->'entityKey'->'typeId') IS DISTINCT FROM 'string'
   OR filters->'entityKey'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
   OR (filters->'entityKey'->>'typeId')::numeric>2147483647
   OR jsonb_typeof(filters->'entityKey'->'keyNumber') IS DISTINCT FROM 'string'
   OR filters->'entityKey'->>'keyNumber' !~ '^(0|[1-9][0-9]{0,4})$'
   OR (filters->'entityKey'->>'keyNumber')::numeric>32767
   OR jsonb_typeof(filters->'entityKey'->'definitionPin') IS DISTINCT FROM 'string'
   OR octet_length(filters->'entityKey'->>'definitionPin') NOT BETWEEN 1 AND 256
   OR jsonb_typeof(filters->'entityKey'->'values') IS DISTINCT FROM 'array'
   OR jsonb_array_length(filters->'entityKey'->'values') NOT BETWEEN 1 AND 128)
  OR filters ? 'documentId' AND (jsonb_typeof(filters->'documentId') IS DISTINCT FROM 'string'
   OR octet_length(filters->>'documentId') NOT BETWEEN 1 AND 4096)
  OR filters ? 'moduleId' AND (jsonb_typeof(filters->'moduleId') IS DISTINCT FROM 'string'
   OR octet_length(filters->>'moduleId') NOT BETWEEN 1 AND 4096)
  OR filters ? 'assertedAction' AND (jsonb_typeof(filters->'assertedAction') IS DISTINCT FROM 'string'
   OR octet_length(filters->>'assertedAction') NOT BETWEEN 1 AND 4096)
  OR filters ? 'observedAtFrom' AND (jsonb_typeof(filters->'observedAtFrom') IS DISTINCT FROM 'string'
   OR filters->>'observedAtFrom' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})$')
  OR filters ? 'observedAtUntil' AND (jsonb_typeof(filters->'observedAtUntil') IS DISTINCT FROM 'string'
   OR filters->>'observedAtUntil' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})$') THEN
  RAISE EXCEPTION 'canonical bounded mutation audit filters required' USING ERRCODE='22023';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a
   WHERE a.document_id=filters->>'documentId' AND a.module=filters->>'moduleId'
    AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
  RAISE EXCEPTION 'qualified mutation audit module enrollment required' USING ERRCODE='42501';END IF;
 IF filters ? 'assertedAction' AND octet_length(convert_to(filters->>'assertedAction','UTF8'))>4096 THEN
  RAISE EXCEPTION 'bounded mutation audit action required' USING ERRCODE='22023';END IF;
 IF filters ? 'observedAtFrom' AND filters ? 'observedAtUntil' THEN
  BEGIN
   IF (filters->>'observedAtFrom')::timestamptz >= (filters->>'observedAtUntil')::timestamptz THEN
    RAISE EXCEPTION 'ordered observed-time range required' USING ERRCODE='22023';END IF;
  EXCEPTION WHEN SQLSTATE '22007' OR SQLSTATE '22008' THEN
   RAISE EXCEPTION 'canonical mutation audit time range required' USING ERRCODE='22023';END;
 END IF;
 IF filters ? 'entityKey' THEN
  key_filter:=filters->'entityKey';
  IF jsonb_typeof(key_filter) IS DISTINCT FROM 'object'
   OR key_filter-ARRAY['documentId','moduleId','typeId','keyNumber','definitionPin','values']<>'{}'::jsonb
   OR jsonb_typeof(key_filter->'documentId') IS DISTINCT FROM 'string'
   OR jsonb_typeof(key_filter->'moduleId') IS DISTINCT FROM 'string'
   OR jsonb_typeof(key_filter->'typeId') IS DISTINCT FROM 'string' OR key_filter->>'typeId' !~ '^[1-9][0-9]{0,9}$'
   OR length(key_filter->>'typeId')=10 AND key_filter->>'typeId' COLLATE "C">'2147483647'
   OR jsonb_typeof(key_filter->'keyNumber') IS DISTINCT FROM 'string' OR key_filter->>'keyNumber' !~ '^[1-9][0-9]{0,4}$'
   OR (key_filter->>'keyNumber')::int>32767
   OR jsonb_typeof(key_filter->'definitionPin') IS DISTINCT FROM 'string' OR key_filter->>'definitionPin' !~ '^[0-9a-f]{64}$'
   OR jsonb_typeof(key_filter->'values') IS DISTINCT FROM 'array'
   OR jsonb_array_length(key_filter->'values') NOT BETWEEN 1 AND 32 THEN
   RAISE EXCEPTION 'exact archived entity-key filter required' USING ERRCODE='22023';END IF;
  IF key_filter->>'documentId' IS DISTINCT FROM filters->>'documentId'
   OR key_filter->>'moduleId' IS DISTINCT FROM filters->>'moduleId' THEN
   RAISE EXCEPTION 'entity-key and module listing scopes must agree' USING ERRCODE='22023';END IF;
 END IF;
 IF octet_length(convert_to(filters::text,'UTF8'))>16384 THEN RAISE EXCEPTION 'mutation audit filters exceed limits' USING ERRCODE='54000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest
  OR pg_is_in_recovery() THEN RAISE EXCEPTION 'current mutation audit release required' USING ERRCODE='0A000';END IF;
 filter_sha:=encode(sha256(convert_to(filters::text,'UTF8')),'hex');
 frontier:=pg_catalog.pg_snapshot_xmin(pg_catalog.pg_current_snapshot());
 IF EXISTS(SELECT 1 FROM truss.runtime_object_attempt a
   WHERE a.complete AND a.writer_xid<frontier AND a.audit_observed_at IS NULL
    AND EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=a.id AND p.writer_xid=a.writer_xid
     AND jsonb_path_exists(p.plan,'$.** ? (@.documentId == $document && @.moduleId == $module)',
      jsonb_build_object('document',to_jsonb(filters->>'documentId'),'module',to_jsonb(filters->>'moduleId'))))) THEN
  RAISE EXCEPTION 'retained mutation group has no truthful observation time' USING ERRCODE='P1010';END IF;
 IF original_cursor IS NOT NULL THEN
  IF octet_length(original_cursor) NOT BETWEEN 1 AND 65536
   OR (convert_from(original_cursor,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
   RAISE EXCEPTION 'bounded exact mutation audit cursor required' USING ERRCODE='22023';END IF;
  cursor_value:=convert_from(original_cursor,'UTF8')::jsonb;
  IF cursor_value-ARRAY['profile','installationId','sourceEpoch','releaseId','releaseSha256','frontierXid',
      'filtersSha256','afterObservedAt','afterAttemptId']<>'{}'::jsonb
   OR cursor_value->>'profile' IS DISTINCT FROM 'truss-mutation-group-audit-cursor/0.2'
   OR cursor_value->>'installationId' IS DISTINCT FROM installation.installation_id::text
   OR cursor_value->>'sourceEpoch' IS DISTINCT FROM installation.source_epoch::text
   OR cursor_value->>'releaseId' IS DISTINCT FROM expected_release
   OR cursor_value->>'releaseSha256' IS DISTINCT FROM expected_digest
   OR cursor_value->>'filtersSha256' IS DISTINCT FROM filter_sha
   OR jsonb_typeof(cursor_value->'frontierXid') IS DISTINCT FROM 'string'
   OR cursor_value->>'frontierXid' !~ '^[1-9][0-9]{0,19}$'
   OR (cursor_value->>'frontierXid')::numeric>18446744073709551615
   OR jsonb_typeof(cursor_value->'afterObservedAt') IS DISTINCT FROM 'string'
   OR cursor_value->>'afterObservedAt' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$'
   OR jsonb_typeof(cursor_value->'afterAttemptId') IS DISTINCT FROM 'string'
   OR cursor_value->>'afterAttemptId' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
   RAISE EXCEPTION 'current mutation audit cursor context required' USING ERRCODE='P1002';END IF;
  frontier:=(cursor_value->>'frontierXid')::xid8;
  BEGIN last_observed:=(cursor_value->>'afterObservedAt')::timestamptz;
  EXCEPTION WHEN SQLSTATE '22007' OR SQLSTATE '22008' THEN
   RAISE EXCEPTION 'canonical mutation audit cursor timestamp required' USING ERRCODE='22023';END;
  last_attempt:=(cursor_value->>'afterAttemptId')::uuid;
  IF cursor_value IS DISTINCT FROM convert_from(truss.runtime_mutation_audit_cursor(
    installation.installation_id,installation.source_epoch,expected_release,expected_digest,
    frontier,filter_sha,last_observed,last_attempt),'UTF8')::jsonb
   OR frontier>pg_catalog.pg_snapshot_xmin(pg_catalog.pg_current_snapshot()) THEN
   RAISE EXCEPTION 'exact frozen mutation audit cursor required' USING ERRCODE='P1002';END IF;
 ELSE
  last_observed:='infinity'::timestamptz;last_attempt:='ffffffff-ffff-ffff-ffff-ffffffffffff'::uuid;
 END IF;
 FOR candidate IN SELECT a.id,a.writer_xid,a.audit_observed_at FROM truss.runtime_object_attempt a
  WHERE a.complete AND a.writer_xid<frontier
   AND a.audit_observed_at IS NOT NULL
   AND EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=a.id AND p.writer_xid=a.writer_xid
    AND jsonb_path_exists(p.plan,'$.** ? (@.documentId == $document && @.moduleId == $module)',
     jsonb_build_object('document',to_jsonb(filters->>'documentId'),'module',to_jsonb(filters->>'moduleId'))))
   AND (original_cursor IS NULL OR (a.audit_observed_at,a.id)<(last_observed,last_attempt))
   AND (NOT filters ? 'attemptId' OR a.id=(filters->>'attemptId')::uuid)
   AND (NOT filters ? 'nativeActorOid' OR a.actor_oid=(filters->>'nativeActorOid')::oid)
  ORDER BY a.audit_observed_at DESC,a.id DESC LOOP
  -- Authorize and validate the complete original owner union before applying
  -- identity or business-key filters that inspect retained private values.
  group_bytes:=truss.read_mutation_group_audit(candidate.id,maximum_events,expected_release,expected_digest);
  group_value:=convert_from(group_bytes,'UTF8')::jsonb;
  IF filters ? 'documentId' AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(group_value->'ownerScopes') scope(value)
    WHERE scope.value->>'documentId'=filters->>'documentId' AND scope.value->>'moduleId'=filters->>'moduleId') THEN CONTINUE;END IF;
  IF truss.runtime_mutation_audit_attempt_matches(candidate.id,filters) IS NOT TRUE THEN CONTINUE;END IF;
  cursor_bytes:=truss.runtime_mutation_audit_cursor(installation.installation_id,
    installation.source_epoch,expected_release,expected_digest,frontier,filter_sha,
    candidate.audit_observed_at,candidate.id);
  -- The collector checks the complete historical owner union. Re-run it after
  -- cursor/projection work so revocation during page assembly cannot release
  -- a group on the strength of an earlier membership observation.
  release_check:=truss.read_mutation_group_audit(candidate.id,maximum_events,expected_release,expected_digest);
  PERFORM truss.runtime_person(false);
  RETURN convert_to((group_value||jsonb_build_object('nextPageCursor',convert_from(cursor_bytes,'UTF8')::jsonb))::text,'UTF8');
 END LOOP;
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a
   WHERE a.document_id=filters->>'documentId' AND a.module=filters->>'moduleId'
    AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
  RAISE EXCEPTION 'mutation audit module authority changed before empty-page release' USING ERRCODE='42501';END IF;
 PERFORM truss.runtime_person(false);
 RETURN convert_to('{"outcome":"end","nextPageCursor":null}','UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.page_mutation_group_audit(jsonb,int,bytea,text,text) FROM PUBLIC;
