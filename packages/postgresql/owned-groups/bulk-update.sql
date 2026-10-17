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
  SELECT * INTO STRICT pin FROM truss.runtime_definition('type',selected_type,NULL,image_revision);type_pin:=pin.definition_pin;
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
   SELECT * INTO STRICT pin FROM truss.runtime_definition('property',selected_type,property.prop_id,image_revision);
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
   SELECT * INTO STRICT pin FROM truss.runtime_definition('key',selected_type,definition.key_num);
   compiled_namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected_type::text,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   namespaces:=namespaces||jsonb_build_object(selected_type::text||':'||definition.key_num::text,encode(compiled_namespace,'hex'));
  END LOOP;
 END LOOP;
 WITH cells AS MATERIALIZED (
  SELECT o.value object,k.key_num,decode(namespaces->>((o.value->'after'->>'type_id')||':'||k.key_num::text),'hex') namespace,
   truss.derive_catalog_key_tuple(k.type_id,k.key_num,
    (SELECT jsonb_agg(o.value->'after'->'props'->i.prop_id::text ORDER BY i.ordinal)
     FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ordinal))) tuple,to_jsonb(old) old
  FROM jsonb_array_elements(objects) o JOIN truss.key_def k ON k.type_id=(o.value->'after'->>'type_id')::int AND k.retired_rev IS NULL
  LEFT JOIN truss.object_key_bucket old ON old.object_id=(o.value->'after'->>'id')::bigint AND old.type_id=k.type_id AND old.key_num=k.key_num
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
  UNION ALL SELECT (o.value->>'index')::int,o.value,2147483647,jsonb_build_object('operation','metadata',
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
  FROM jsonb_array_elements(objects) o LEFT JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int),
 updated AS (
  UPDATE truss.runtime_owned_operation p SET result=s.result FROM slots s
  WHERE p.attempt_id=selected_attempt AND p.operation_index=s.operation_index AND p.result IS NULL RETURNING p.operation_index,p.result)
 SELECT count(*),jsonb_agg(result ORDER BY operation_index) INTO counted,results FROM updated;
 IF counted<>total THEN RAISE EXCEPTION 'complete sealed batch update slots required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch update progress advance required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch(uuid) FROM PUBLIC;
