-- Distinct stored-object value updates with unchanged ownership
-- have no order-dependent effects. The original planner, key preflight and
-- finish/commit validators still establish their complete source correspondence.
CREATE FUNCTION truss.runtime_owned_update_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;objects jsonb;journals jsonb;transitions jsonb;results jsonb;expected jsonb;actual jsonb;
 dictionary jsonb:='{}';history_basis jsonb;image_revision int;selected_type int;property record;pin record;type_pin text;
 property_pins jsonb;property_order jsonb;source record;actor oid;total int;counted int;
 namespaces jsonb:='{}';compiled_namespace bytea;definition record;keys jsonb;route record;
 slot_results jsonb;
 codecs jsonb:='{}';codec jsonb;codec_bytes bigint:=2;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 total:=jsonb_array_length(input->'operations');
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.complete OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() OR total NOT BETWEEN 1 AND 1024
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored'
    OR o.value ? 'ownershipChange')
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
  OR (SELECT count(DISTINCT plan->>'primary') FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
  OR EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND
   (p.writer_xid IS DISTINCT FROM attempt.writer_xid OR p.result IS NOT NULL
    OR p.plan->'operation' IS DISTINCT FROM input->'operations'->p.operation_index
    OR p.plan->'beforeNodes'->(p.plan->>'primary') IS NULL
    OR p.plan->'afterNodes'->(p.plan->>'primary') IS NULL
    OR p.plan->'beforeNodes'->(p.plan->>'primary')->'deleted' IS DISTINCT FROM 'false'::jsonb
    OR p.plan->'afterNodes'->(p.plan->>'primary')->'deleted' IS DISTINCT FROM 'false'::jsonb
    OR p.plan->'beforeNodes'->(p.plan->>'primary')->'root' IS DISTINCT FROM p.plan->'afterNodes'->(p.plan->>'primary')->'root')) THEN
  RAISE EXCEPTION 'independent original value update batch required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 -- Bind every physical before-image before the single UPDATE. The initial
 -- scope has already locked these rows; duplicate targets use ordered execution.
 WITH members AS MATERIALIZED (
  SELECT p.operation_index,p.plan,p.plan->'beforeNodes'->(p.plan->>'primary') prior,
   p.plan->'afterNodes'->(p.plan->>'primary') desired,
   truss.runtime_owned_identity(selected_attempt,p.operation_index,p.plan->>'primary','object',p.plan,attempt) identity
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt),
 checked AS MATERIALIZED (
  SELECT m.*,to_jsonb(o) physical,
   truss.runtime_owned_object_image(selected_attempt,m.operation_index,m.plan->>'primary','before',m.plan,attempt) before_image,
   truss.runtime_owned_object_image(selected_attempt,m.operation_index,m.plan->>'primary','after',m.plan,attempt) after_image
  FROM members m LEFT JOIN truss.object o ON o.id=(m.identity->>'id')::bigint AND o.type_id=(m.identity->>'typeId')::int)
 SELECT jsonb_agg(jsonb_build_object('index',operation_index,'identity',identity,'before',physical,
  'after',CASE WHEN prior=desired THEN physical ELSE after_image||jsonb_build_object(
   'created_at',physical->'created_at','updated_at',clock_timestamp()) END,
  'beforeMatches',physical-ARRAY['created_at','updated_at'] IS NOT DISTINCT FROM before_image,
  'changed',prior IS DISTINCT FROM desired) ORDER BY operation_index) INTO objects FROM checked;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(objects) o WHERE o.value->'beforeMatches' IS DISTINCT FROM 'true'::jsonb
  OR o.value->'before'='null'::jsonb
  OR o.value->'changed'='true'::jsonb AND ((o.value->'before'->>'ver')::bigint=9223372036854775807
   OR (o.value->'after'->>'ver')::bigint<>(o.value->'before'->>'ver')::bigint+1)) THEN
  RAISE EXCEPTION 'original batch object prestate and version required' USING ERRCODE='55000';END IF;
 -- Resolve native history metadata once per type and image revision.
 FOR source IN SELECT DISTINCT (image->>'type_id')::int type_id,(image->>'rev')::int revision
  FROM jsonb_array_elements(objects) o CROSS JOIN LATERAL (VALUES(o.value->'before'),(o.value->'after')) v(image)
  WHERE o.value->'changed'='true'::jsonb LOOP
  selected_type:=source.type_id;image_revision:=source.revision;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',selected_type,NULL,image_revision);type_pin:=pin.definition_pin;
  PERFORM truss.runtime_module_writer_qualified(pin.document_id,pin.module_id,actor);
  IF NOT truss.runtime_object_values_readable_qualified(selected_type,actor) THEN
   RAISE EXCEPTION 'current property and item readers required' USING ERRCODE='42501';END IF;
  property_pins:='{}';property_order:='[]';
  IF image_revision=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>image_revision) THEN
   SELECT jsonb_build_object('prop_def',coalesce(jsonb_agg(to_jsonb(p)),'[]'::jsonb)) INTO history_basis
    FROM truss.prop_def p WHERE p.type_id=selected_type;
  ELSE history_basis:=truss.catalog_all_expected_records(image_revision);END IF;
  FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,history_basis->'prop_def') p
   WHERE p.type_id=selected_type ORDER BY prop_id LOOP
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',selected_type,property.prop_id,image_revision);
   property_pins:=property_pins||jsonb_build_object(property.prop_id::text,pin.definition_pin);
   property_order:=property_order||jsonb_build_array(property.prop_id::text);
  END LOOP;
  dictionary:=dictionary||jsonb_build_object(jsonb_build_array(image_revision,selected_type)::text,jsonb_build_object(
   'typeId',selected_type::text,'revision',image_revision::text,'typePin',type_pin,
   'propertyOrder',property_order,'propertyPins',property_pins));
 END LOOP;
 -- Preserve the preflight's complete ordered key simulation and locks. Lower
 -- only the already admitted physical key changes; unchanged memberships keep
 -- their original bytes and permanent reservations are never removed.
 FOR selected_type IN SELECT DISTINCT (value->'after'->>'type_id')::int FROM jsonb_array_elements(objects) LOOP
  FOR definition IN SELECT * FROM truss.key_def WHERE type_id=selected_type AND retired_rev IS NULL ORDER BY key_num LOOP
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',selected_type,definition.key_num);
   codec:=truss.runtime_owned_key_codec_metadata(selected_type,definition.key_num);
   IF codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32<=4194304 THEN
    codecs:=codecs||jsonb_build_object(selected_type::text||':'||definition.key_num::text,codec);
    codec_bytes:=codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32;
   END IF;
   compiled_namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected_type::text,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   namespaces:=namespaces||jsonb_build_object(selected_type::text||':'||definition.key_num::text,encode(compiled_namespace,'hex'));
  END LOOP;
 END LOOP;
 WITH cells AS MATERIALIZED (
  SELECT o.value object,k.key_num,decode(namespaces->>((o.value->'after'->>'type_id')||':'||k.key_num::text),'hex') namespace,
   truss.runtime_owned_key_tuple_in_metadata(k.type_id,k.key_num,
    (SELECT jsonb_agg(o.value->'after'->'props'->i.prop_id::text ORDER BY i.ordinal)
     FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ordinal)),
    coalesce(codecs->(k.type_id::text||':'||k.key_num::text),truss.runtime_owned_key_codec_metadata(k.type_id,k.key_num))) tuple,to_jsonb(old) old
  FROM jsonb_array_elements(objects) o CROSS JOIN LATERAL (
   SELECT k.* FROM truss.key_def k WHERE k.type_id=(o.value->'after'->>'type_id')::int AND k.retired_rev IS NULL OFFSET 0) k
  LEFT JOIN LATERAL (SELECT old.* FROM truss.object_key_bucket old WHERE old.object_id=(o.value->'after'->>'id')::bigint
   AND old.type_id=k.type_id AND old.key_num=k.key_num OFFSET 0) old ON true
  WHERE o.value->'changed'='true'::jsonb),
 encoded AS MATERIALIZED (
  SELECT *,convert_to('umf-key-tuple-v1:hex:'||encode(tuple,'hex'),'UTF8') transport FROM cells),
 checked AS MATERIALIZED (
  SELECT *,namespace IS DISTINCT FROM decode(substring(old->>'namespace_bytes' FROM 3),'hex')
   OR transport IS DISTINCT FROM decode(substring(old->>'key_bytes' FROM 3),'hex') changed FROM encoded),
 allocated AS MATERIALIZED (
  SELECT *,CASE WHEN changed THEN nextval('truss.key_storage_row_seq') END member_id,
   CASE WHEN changed THEN nextval('truss.key_storage_row_seq') END reservation_id FROM checked)
 SELECT coalesce(jsonb_agg(jsonb_build_object('old',old,'changed',changed,'namespace',encode(namespace,'hex'),'transport',encode(transport,'hex'),
  'membership',jsonb_build_object('storage_row_id',member_id,'type_id',(object->'after'->>'type_id')::int,'key_num',key_num,
   'object_id',(object->'after'->>'id')::bigint,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport),
   'original_context_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-context/0.2','attemptId',selected_attempt::text,
    'operationIndex',object->>'index','objectId',object->'after'->>'id','xid',attempt.writer_xid::text,'derivation','postgresql-umf-key-tuple-v1')::text,'UTF8')),
  'reservation',jsonb_build_object('storage_row_id',reservation_id,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport),
   'original_reservation_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-reservation/0.1','attemptId',selected_attempt::text,
    'operationIndex',object->>'index','objectId',object->'after'->>'id','typeId',object->'after'->>'type_id',
    'keyNumber',key_num::text,'xid',attempt.writer_xid::text)::text,'UTF8')))),'[]') INTO keys FROM allocated;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(keys) k WHERE k.value->'old'='null'::jsonb) THEN
  RAISE EXCEPTION 'original live batch key membership required' USING ERRCODE='55000';END IF;
 FOR route IN SELECT k.value,observed.member_ids,observed.reservation_ids FROM jsonb_array_elements(keys) k
  CROSS JOIN LATERAL truss.lock_string_key_bucket(decode(k.value->>'namespace','hex'),decode(k.value->>'transport','hex')) observed LOOP
  IF route.value->'changed'='true'::jsonb THEN
   IF cardinality(route.member_ids)>0 OR cardinality(route.reservation_ids)>0 THEN
    RAISE EXCEPTION 'key allocated or reserved' USING ERRCODE='23505';END IF;
  ELSIF cardinality(route.member_ids)<>1 OR route.member_ids[1]<>(route.value->'old'->>'storage_row_id')::bigint THEN
   RAISE EXCEPTION 'owned unchanged batch key required' USING ERRCODE='55000';END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(value->'old' ORDER BY (value->'old'->>'storage_row_id')::bigint),'[]') INTO expected
  FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb;
 WITH deleted AS (
  DELETE FROM truss.object_key_bucket old USING jsonb_array_elements(keys) k
  WHERE k.value->'changed'='true'::jsonb AND old.storage_row_id=(k.value->'old'->>'storage_row_id')::bigint RETURNING old.*)
 SELECT coalesce(jsonb_agg(to_jsonb(deleted) ORDER BY storage_row_id),'[]') INTO actual FROM deleted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch old key removal required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(value->'membership' ORDER BY (value->'membership'->>'storage_row_id')::bigint),'[]') INTO expected
  FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb;
 WITH inserted AS (
  INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
  SELECT r.storage_row_id,r.type_id,r.key_num,r.object_id,r.namespace_bytes,r.key_bytes,r.original_context_bytes
  FROM jsonb_array_elements(keys) k CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,k.value->'membership') r
  WHERE k.value->'changed'='true'::jsonb RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch updated key memberships required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(value->'reservation' ORDER BY (value->'reservation'->>'storage_row_id')::bigint),'[]') INTO expected
  FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb;
 WITH inserted AS (
  INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes)
  SELECT r.storage_row_id,r.namespace_bytes,r.key_bytes,r.original_reservation_bytes FROM jsonb_array_elements(keys) k
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_reservation_bucket,k.value->'reservation') r
  WHERE k.value->'changed'='true'::jsonb RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch updated key reservations required' USING ERRCODE='55000';END IF;
 UPDATE truss.key_bucket_guard g SET generation=g.generation+routes.advances FROM (
  SELECT decode(entry->>'namespace_sha256','hex') namespace_sha256,decode(entry->>'key_sha256','hex') key_sha256,count(*) advances
  FROM (SELECT jsonb_build_object('namespace_sha256',substring(value->'old'->>'namespace_sha256' FROM 3),
   'key_sha256',substring(value->'old'->>'key_sha256' FROM 3)) entry FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb
   UNION ALL SELECT jsonb_build_object('namespace_sha256',substring(value->'membership'->>'namespace_sha256' FROM 3),
   'key_sha256',substring(value->'membership'->>'key_sha256' FROM 3)) FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb) all_routes
  GROUP BY entry->>'namespace_sha256',entry->>'key_sha256') routes
 WHERE g.namespace_sha256=routes.namespace_sha256 AND g.key_sha256=routes.key_sha256;
 SELECT coalesce(jsonb_agg(value->'after' ORDER BY (value->'after'->>'id')::bigint),'[]') INTO expected
 FROM jsonb_array_elements(objects) WHERE value->'changed'='true'::jsonb;
 WITH updated AS (
  UPDATE truss.object o SET props=r.props,retained=r.retained,root_id=r.root_id,root_type=r.root_type,
   rev=r.rev,ver=r.ver,updated_at=r.updated_at
  FROM jsonb_array_elements(objects) v CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object,v.value->'after') r
  WHERE v.value->'changed'='true'::jsonb AND o.id=r.id AND o.type_id=r.type_id RETURNING o.*)
 SELECT coalesce(jsonb_agg(to_jsonb(updated) ORDER BY id),'[]') INTO actual FROM updated;
 IF actual IS DISTINCT FROM expected OR EXISTS(SELECT 1 FROM jsonb_array_elements(objects) v LEFT JOIN truss.object o
  ON o.id=(v.value->'after'->>'id')::bigint AND o.type_id=(v.value->'after'->>'type_id')::int
  WHERE to_jsonb(o) IS DISTINCT FROM v.value->'after') THEN
  RAISE EXCEPTION 'exact batch object updates required' USING ERRCODE='55000';END IF;
 WITH semantic AS MATERIALIZED (
  SELECT (o.value->>'index')::int operation_index,o.value object,p.prop_id ordinal,
   jsonb_build_object('operation','property','propertyId',p.prop_id::text,
    'definitionPin',dictionary->jsonb_build_array((o.value->'after'->>'rev')::int,p.type_id)::text->'propertyPins'->>p.prop_id::text,
    'before',CASE WHEN o.value->'before'->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',o.value->'before'->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END,
    'after',CASE WHEN o.value->'after'->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',o.value->'after'->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END) event
  FROM jsonb_array_elements(objects) o JOIN truss.prop_def p ON p.type_id=(o.value->'after'->>'type_id')::int
   AND p.since_rev<=(o.value->'after'->>'rev')::int AND (p.retired_rev IS NULL OR p.retired_rev>(o.value->'after'->>'rev')::int)
  WHERE o.value->'changed'='true'::jsonb AND o.value->'before'->'props'->p.prop_id::text IS DISTINCT FROM o.value->'after'->'props'->p.prop_id::text
  UNION ALL SELECT (o.value->>'index')::int,o.value,2147483648,jsonb_build_object('operation','metadata',
   'before',truss.runtime_owned_history_record_in_metadata(o.value->'before',o.value->'identity',dictionary->jsonb_build_array((o.value->'before'->>'rev')::int,(o.value->'before'->>'type_id')::int)::text),
   'after',truss.runtime_owned_history_record_in_metadata(o.value->'after',o.value->'identity',dictionary->jsonb_build_array((o.value->'after'->>'rev')::int,(o.value->'after'->>'type_id')::int)::text))
  FROM jsonb_array_elements(objects) o WHERE o.value->'changed'='true'::jsonb),
 allocated AS MATERIALIZED (
  SELECT *,nextval('truss.journal_seq') seq,clock_timestamp() at FROM semantic ORDER BY operation_index,ordinal),
 events AS MATERIALIZED (
  SELECT *,event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',seq::text,'identity',object->'identity',
   'eventVersion',object->'after'->>'ver','eventCatalogRevision',object->'after'->>'rev',
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text)) payload FROM allocated),
 digests AS MATERIALIZED (
  SELECT operation_index,count(*) amount,encode(sha256(convert_to(jsonb_agg(payload ORDER BY ordinal)::text,'UTF8')),'hex') digest
  FROM events GROUP BY operation_index)
 SELECT coalesce(jsonb_agg(jsonb_build_object('index',e.operation_index,'journal',jsonb_build_object(
  'seq',e.seq,'at',e.at,'xid',attempt.writer_xid::text,'entity_kind','o','entity_id',(e.object->'after'->>'id')::bigint,
  'entity_type',(e.object->'after'->>'type_id')::int,'ver',(e.object->'after'->>'ver')::bigint,
  'op',CASE e.event->>'operation' WHEN 'property' THEN 'update' ELSE 'metadata' END,'prop_id',(e.event->>'propertyId')::int,
  'old_value',NULL,'rev',(e.object->'after'->>'rev')::int,
  'new_value',truss.runtime_exact_wrapper('event',convert_to((e.payload||jsonb_build_object('mutationGroup',
   jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',d.amount::text,'orderedEventDigest',d.digest)))::text,'UTF8')),
  'origin',truss.runtime_exact_wrapper('origin',convert_to((e.payload->'origin')::text,'UTF8')))) ORDER BY e.seq),'[]') INTO journals
 FROM events e JOIN digests d ON d.operation_index=e.operation_index;
 SELECT coalesce(jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint),'[]') INTO expected FROM jsonb_array_elements(journals);
 WITH inserted AS (INSERT INTO truss.journal SELECT r.* FROM jsonb_array_elements(journals) j
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.journal,j.value->'journal') r RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY seq),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch update journals required' USING ERRCODE='55000';END IF;
 WITH journal_sets AS MATERIALIZED (
  SELECT (value->>'index')::int operation_index,jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint) rows
  FROM jsonb_array_elements(journals) GROUP BY (value->>'index')::int)
 SELECT coalesce(jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(o.value->>'index')::int,
  'writer_xid',attempt.writer_xid::text,'object_id',(o.value->'after'->>'id')::bigint,'type_id',(o.value->'after'->>'type_id')::int,
  'before_object',o.value->'before','after_object',o.value->'after',
  'after_keys',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]') FROM truss.object_key_bucket k
   WHERE k.object_id=(o.value->'after'->>'id')::bigint AND k.type_id=(o.value->'after'->>'type_id')::int),
  'journal',j.rows) ORDER BY (o.value->>'index')::int),'[]') INTO transitions
 FROM jsonb_array_elements(objects) o JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int;
 WITH inserted AS (
  INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
  SELECT r.attempt_id,r.operation_index,r.writer_xid,r.object_id,r.type_id,r.before_object,r.after_object,r.after_keys,r.journal
  FROM jsonb_populate_recordset(NULL::truss.runtime_object_transition,transitions) r RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted)-'transition_id' ORDER BY operation_index),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM transitions THEN RAISE EXCEPTION 'exact batch update transitions required' USING ERRCODE='55000';END IF;
 WITH journal_sets AS MATERIALIZED (
  SELECT (value->>'index')::int operation_index,jsonb_agg(jsonb_build_object('sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',value->'journal'->>'seq')
    ORDER BY (value->'journal'->>'seq')::bigint) events FROM jsonb_array_elements(journals) GROUP BY (value->>'index')::int),
 slots AS (
  SELECT (o.value->>'index')::int operation_index,jsonb_build_object('operation','update_object',
   'outcome',CASE WHEN o.value->'changed'='true'::jsonb THEN 'changed' ELSE 'unchanged' END,'identity',o.value->'identity',
   'version',o.value->'after'->>'ver','events',coalesce(j.events,'[]'::jsonb)) result
  FROM jsonb_array_elements(objects) o LEFT JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int)
 SELECT jsonb_object_agg(operation_index::text,result) INTO slot_results FROM slots;
 WITH updated AS (
  UPDATE truss.runtime_owned_operation p SET result=slot_results->p.operation_index::text
  WHERE p.attempt_id=selected_attempt AND p.result IS NULL AND slot_results ? p.operation_index::text
  RETURNING p.operation_index,p.result)
 SELECT count(*) INTO counted FROM updated;
 IF counted<>total THEN RAISE EXCEPTION 'complete sealed batch update slots required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch update progress advance required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch(uuid) FROM PUBLIC;

-- Independent rootless value updates close their immutable source/result,
-- transition and journal correspondence as relations. Full final graph checks
-- remain in group_validate; row/journal constraint triggers remain independent.
CREATE FUNCTION truss.runtime_owned_update_batch_validate(attempt truss.runtime_object_attempt,input jsonb,history_dictionary jsonb,actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE initial_scope jsonb;last_plan jsonb;initial_nodes jsonb;initial_edges jsonb;final_nodes jsonb;before_nodes jsonb;
 states jsonb;event_dictionary jsonb;owner record;problem boolean;changed_count int;
BEGIN
 SELECT plan->'initialScope' INTO STRICT initial_scope FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=0;
 SELECT plan INTO STRICT last_plan FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=attempt.next_index-1;
 IF (last_plan->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>(last_plan->>'catalogRevision')::int)
  OR attempt.aliases<>'[]'::jsonb OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange')
  OR (SELECT count(DISTINCT plan->>'primary') FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id)<>attempt.next_index
  OR EXISTS(SELECT 1 FROM jsonb_each(initial_scope->'nodes') n WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb
   OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb) THEN
  RAISE EXCEPTION 'independent original rootless update inventory required' USING ERRCODE='55000';END IF;
 WITH types AS MATERIALIZED (
  SELECT DISTINCT (value->>'type_id')::int type_id FROM jsonb_each(initial_scope->'nodes')),
 pins AS MATERIALIZED (
  SELECT t.type_id,d.* FROM types t CROSS JOIN LATERAL truss.runtime_owned_definition_metadata('type',t.type_id,NULL,(last_plan->>'catalogRevision')::int) d)
 SELECT coalesce(jsonb_object_agg('stored:'||n.key,jsonb_build_object('identity',jsonb_build_object(
  'id',n.value->>'id','typeId',n.value->>'type_id','definitionPin',p.definition_pin,
  'owner',jsonb_build_object('documentId',p.document_id,'moduleId',p.module_id)),
  'image',n.value-ARRAY['root_id','root_type','updated_at'],'root',NULL,'deleted',false)),'{}') INTO initial_nodes
 FROM jsonb_each(initial_scope->'nodes') n JOIN pins p ON p.type_id=(n.value->>'type_id')::int;
 WITH relations AS MATERIALIZED (
  SELECT r.*,truss.runtime_relationship_pin(r.rel_type_id) pin FROM truss.rel_def r JOIN
   (SELECT DISTINCT (value->>'rel_type_id')::int rel_type_id FROM jsonb_each(initial_scope->'edges')) e USING(rel_type_id))
 SELECT coalesce(jsonb_object_agg('stored:'||(e.value->>'rel_type_id')||':'||(e.value->>'id'),jsonb_build_object(
  'identity',jsonb_build_object('id',e.value->>'id','typeId',e.value->>'rel_type_id','definitionPin',r.pin,
   'owner',jsonb_build_object('documentId',r.document_id,'moduleId',r.module)),
  'image',e.value-ARRAY['source_id','source_type','target_id','target_type','order_key','updated_at'],
  'source','stored:'||(e.value->>'source_type')||':'||(e.value->>'source_id'),
  'target','stored:'||(e.value->>'target_type')||':'||(e.value->>'target_id'),
  'lifecycle',r.lifecycle,'deleted',false,'orderKey',CASE WHEN e.value->'order_key'='null'::jsonb
   THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',e.value->>'order_key') END)),'{}') INTO initial_edges
 FROM jsonb_each(initial_scope->'edges') e JOIN relations r ON r.rel_type_id=(e.value->>'rel_type_id')::int;
 SELECT jsonb_object_agg(p.plan->>'primary',p.plan->'afterNodes'->(p.plan->>'primary')),
  coalesce(jsonb_object_agg(p.plan->>'primary',p.plan->'afterNodes'->(p.plan->>'primary')) FILTER(WHERE p.operation_index<attempt.next_index-1),'{}')
 INTO states,before_nodes FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id;
 final_nodes:=initial_nodes||states;before_nodes:=initial_nodes||before_nodes;
 IF last_plan->'afterNodes' IS DISTINCT FROM final_nodes OR last_plan->'beforeNodes' IS DISTINCT FROM before_nodes
  OR last_plan->'beforeEdges' IS DISTINCT FROM initial_edges OR last_plan->'afterEdges' IS DISTINCT FROM initial_edges THEN
  RAISE EXCEPTION 'complete original independent update graph required' USING ERRCODE='55000';END IF;
 FOR owner IN SELECT DISTINCT t.type_id,t.document_id,t.module FROM truss.type_def t JOIN
  (SELECT DISTINCT (p.plan->'afterNodes'->(p.plan->>'primary')->'identity'->>'typeId')::int type_id
   FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id) members USING(type_id) LOOP
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,actor);
  IF NOT truss.runtime_object_values_readable_qualified(owner.type_id,actor) THEN
   RAISE EXCEPTION 'current original update value readers required' USING ERRCODE='42501';END IF;
 END LOOP;
 WITH frames AS MATERIALIZED (
  SELECT p.operation_index,p.plan,p.plan->'beforeNodes'->(p.plan->>'primary') prior,
   p.plan->'afterNodes'->(p.plan->>'primary') desired
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id),
 members AS MATERIALIZED (
  SELECT f.*,f.desired->'identity' identity,f.prior IS DISTINCT FROM f.desired changed,t.transition_id,t.writer_xid,t.object_id,t.type_id,
   t.before_object,t.after_object
  FROM frames f LEFT JOIN LATERAL (
   SELECT t.* FROM truss.runtime_object_transition t WHERE t.attempt_id=attempt.id AND t.operation_index=f.operation_index OFFSET 0) t ON true)
 SELECT EXISTS(SELECT 1 FROM members m WHERE
  m.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
  OR m.plan->'operationIndex' IS DISTINCT FROM to_jsonb(m.operation_index)
  OR m.plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
  OR m.plan->'operation' IS DISTINCT FROM input->'operations'->m.operation_index
  OR m.plan->>'actorName' IS DISTINCT FROM session_user::text
  OR m.plan->>'primary' IS DISTINCT FROM 'stored:'||(m.identity->>'typeId')||':'||(m.identity->>'id')
  OR m.identity IS DISTINCT FROM m.plan->'operation'->'target'->'identity'
  OR m.prior IS DISTINCT FROM initial_nodes->(m.plan->>'primary')
  OR m.desired->'identity' IS DISTINCT FROM m.prior->'identity'
  OR m.desired->'root' IS DISTINCT FROM 'null'::jsonb OR m.desired->'deleted' IS DISTINCT FROM 'false'::jsonb
  OR m.operation_index<attempt.next_index-1 AND
   (m.plan->'beforeNodes' IS DISTINCT FROM jsonb_build_object(m.plan->>'primary',m.prior)
    OR m.plan->'afterNodes' IS DISTINCT FROM jsonb_build_object(m.plan->>'primary',m.desired)
    OR m.plan->'beforeEdges' IS DISTINCT FROM '{}'::jsonb OR m.plan->'afterEdges' IS DISTINCT FROM '{}'::jsonb)
  OR CASE WHEN m.changed THEN m.transition_id IS NULL OR m.writer_xid IS DISTINCT FROM attempt.writer_xid
   OR m.object_id::text IS DISTINCT FROM m.identity->>'id' OR m.type_id::text IS DISTINCT FROM m.identity->>'typeId'
   OR m.before_object IS DISTINCT FROM initial_scope->'nodes'->((m.identity->>'typeId')||':'||(m.identity->>'id'))
   OR m.after_object IS NULL OR m.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM
    ((m.desired->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',m.object_id,'root_id',NULL,'root_type',NULL)
   OR m.after_object->'created_at' IS DISTINCT FROM m.before_object->'created_at'
   OR (m.after_object->>'ver')::bigint IS DISTINCT FROM (m.before_object->>'ver')::bigint+1
   ELSE m.transition_id IS NOT NULL END) INTO problem;
 IF problem THEN RAISE EXCEPTION 'original batch update plan and transition correspondence required' USING ERRCODE='55000';END IF;
 SELECT count(*) INTO changed_count FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id
  AND p.plan->'beforeNodes'->(p.plan->>'primary') IS DISTINCT FROM p.plan->'afterNodes'->(p.plan->>'primary');
 IF (SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=attempt.id)<>changed_count
  OR EXISTS(SELECT 1 FROM truss.runtime_edge_transition WHERE attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'complete original batch update effect inventory required' USING ERRCODE='55000';END IF;
 -- Reconstruct semantic property/metadata events from the original physical
 -- transition and independently compiled source dictionary. Never trust the
 -- journal payload to supply its own meaning or group digest.
 WITH members AS MATERIALIZED (
  SELECT t.operation_index,t.object_id,t.type_id,t.before_object,t.after_object,t.journal,
   p.plan->>'catalogRevision' capture_revision,p.plan->>'actorName' actor_name,
   p.plan->'afterNodes'->(p.plan->>'primary')->'identity' identity
  FROM truss.runtime_object_transition t CROSS JOIN LATERAL (
   SELECT p.plan FROM truss.runtime_owned_operation p WHERE p.attempt_id=t.attempt_id AND p.operation_index=t.operation_index OFFSET 0) p
  WHERE t.attempt_id=attempt.id),
 semantics AS MATERIALIZED (
  SELECT m.operation_index,m.object_id,m.type_id,m.after_object->>'ver' expected_version,m.capture_revision,m.actor_name,m.identity,
   jsonb_array_length(m.journal) journal_count,s.event_index,s.event_count,m.journal->s.event_index::int entry,s.event
  FROM members m CROSS JOIN LATERAL (
   SELECT e.event,row_number() OVER(ORDER BY e.metadata,e.ordinal)-1 event_index,count(*) OVER() event_count FROM (
    SELECT false metadata,p.prop_id::bigint ordinal,jsonb_build_object('operation','property','propertyId',p.prop_id::text,
     'definitionPin',coalesce(history_dictionary->jsonb_build_array((m.after_object->>'rev')::int,m.type_id)::text->'propertyPins'->>p.prop_id::text,
      (SELECT d.definition_pin FROM truss.runtime_owned_definition_metadata('property',m.type_id,p.prop_id,m.capture_revision::int) d)),
     'before',CASE WHEN m.before_object->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',m.before_object->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END,
     'after',CASE WHEN m.after_object->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',m.after_object->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END) event
    FROM truss.prop_def p WHERE p.type_id=m.type_id AND p.since_rev<=m.capture_revision::int
     AND (p.retired_rev IS NULL OR p.retired_rev>m.capture_revision::int)
     AND m.before_object->'props'->p.prop_id::text IS DISTINCT FROM m.after_object->'props'->p.prop_id::text
    UNION ALL SELECT true,0::bigint,jsonb_build_object('operation','metadata',
     'before',truss.runtime_owned_history_record_in_metadata(m.before_object,m.identity,history_dictionary->jsonb_build_array((m.before_object->>'rev')::int,m.type_id)::text),
     'after',truss.runtime_owned_history_record_in_metadata(m.after_object,m.identity,history_dictionary->jsonb_build_array((m.after_object->>'rev')::int,m.type_id)::text))
   ) e) s),
 payloads AS MATERIALIZED (
  SELECT s.*,s.event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',attempt.context->>'sourceEpoch',
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,
   'seq',s.entry->>'seq','identity',s.identity,'eventVersion',s.expected_version,
   'eventCatalogRevision',s.capture_revision,'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',s.actor_name)) payload
  FROM semantics s),
 digests AS MATERIALIZED (
  SELECT p.*,CASE WHEN event_index=0 THEN encode(sha256(convert_to((jsonb_agg(payload) OVER (
   PARTITION BY operation_index ORDER BY event_index ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING))::text,'UTF8')),'hex') END digest
  FROM payloads p),
 complete AS MATERIALIZED (
  SELECT d.*,d.payload||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0',
   'eventCount',d.event_count::text,'orderedEventDigest',first_value(digest) OVER(PARTITION BY operation_index ORDER BY event_index))) expected_payload
  FROM digests d)
 SELECT EXISTS(SELECT 1 FROM complete p LEFT JOIN LATERAL (
  SELECT j.* FROM truss.journal j WHERE j.seq=(p.entry->>'seq')::bigint AND j.at=(p.entry->>'at')::timestamptz OFFSET 0) j ON true WHERE
  p.journal_count IS DISTINCT FROM p.event_count OR to_jsonb(j) IS DISTINCT FROM p.entry
  OR p.entry IS DISTINCT FROM jsonb_build_object('seq',(p.entry->>'seq')::bigint,'at',p.entry->'at','xid',attempt.writer_xid::text,
   'entity_kind','o','entity_id',p.object_id,'entity_type',p.type_id,'ver',p.expected_version::bigint,
   'op',CASE p.expected_payload->>'operation' WHEN 'property' THEN 'update' ELSE 'metadata' END,
   'prop_id',(p.expected_payload->>'propertyId')::int,'old_value',NULL,'rev',p.capture_revision::int,
   'new_value',truss.runtime_exact_wrapper('event',convert_to(p.expected_payload::text,'UTF8')),
   'origin',truss.runtime_exact_wrapper('origin',convert_to((p.payload->'origin')::text,'UTF8')))) INTO problem;
 IF problem THEN RAISE EXCEPTION 'exact original batch update journals required' USING ERRCODE='55000';END IF;
 -- A local event map avoids joining two materialized batch relations whose
 -- row estimates can collapse to one after ANALYZE of retained attempt history.
 WITH event_sets AS MATERIALIZED (
  SELECT t.operation_index,jsonb_agg(jsonb_build_object('sourceEpoch',attempt.context->>'sourceEpoch',
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',j.value->>'seq')
    ORDER BY (j.value->>'seq')::bigint) events
  FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
  WHERE t.attempt_id=attempt.id GROUP BY t.operation_index)
 SELECT coalesce(jsonb_object_agg(operation_index::text,events),'{}'::jsonb) INTO event_dictionary FROM event_sets;
 SELECT EXISTS(SELECT 1 FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=attempt.id AND p.result IS DISTINCT FROM jsonb_build_object('operation','update_object',
   'outcome',CASE WHEN p.plan->'beforeNodes'->(p.plan->>'primary') IS DISTINCT FROM p.plan->'afterNodes'->(p.plan->>'primary') THEN 'changed' ELSE 'unchanged' END,
   'identity',p.plan->'afterNodes'->(p.plan->>'primary')->'identity',
   'version',p.plan->'afterNodes'->(p.plan->>'primary')->'image'->>'ver','events',coalesce(event_dictionary->p.operation_index::text,'[]'::jsonb))) INTO problem;
 IF problem THEN RAISE EXCEPTION 'exact original batch update results required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch_validate(truss.runtime_object_attempt,jsonb,jsonb,oid) FROM PUBLIC;
