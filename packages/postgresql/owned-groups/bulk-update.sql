-- Distinct stored-object value updates with unchanged ownership
-- have no order-dependent effects. The original planner, key preflight and
-- finish/commit validators still establish their complete source correspondence.
CREATE FUNCTION truss.runtime_owned_update_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;objects jsonb;transitions jsonb;results jsonb;expected jsonb;actual jsonb;
 dictionary jsonb:='{}';history_basis jsonb;image_revision int;selected_type int;property record;pin record;type_pin text;
 property_pins jsonb;property_order jsonb;source record;actor oid;total int;counted int;
 namespaces jsonb:='{}';compiled_namespace bytea;definition record;keys jsonb;route record;
 slot_results jsonb;projection_problem boolean;journal_refs jsonb;key_taken boolean;unchanged_problem boolean;
 codecs jsonb:='{}';codec jsonb;codec_bytes bigint:=2;
 origin_payload jsonb;expected_origin_wrapper jsonb;expected_origin_hash bytea;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 total:=jsonb_array_length(input->'operations');
 origin_payload:=jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text);
 expected_origin_wrapper:=truss.runtime_exact_wrapper('origin',convert_to(origin_payload::text,'UTF8'));
 expected_origin_hash:=sha256(convert_to(expected_origin_wrapper::text,'UTF8'));
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
  SELECT metadata-'propertyAccess' INTO STRICT history_basis FROM truss.runtime_type_schema
   WHERE rev=image_revision AND type_id=selected_type;
  dictionary:=dictionary||jsonb_build_object(jsonb_build_array(image_revision,selected_type)::text,history_basis);
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
  SELECT *,sha256(namespace) namespace_sha256,sha256(transport) key_sha256,
   CASE WHEN changed THEN nextval('truss.key_storage_row_seq') END member_id,
   CASE WHEN changed THEN nextval('truss.key_storage_row_seq') END reservation_id FROM checked)
 SELECT coalesce(jsonb_agg(jsonb_build_object('old',old,'changed',changed,'namespace',encode(namespace,'hex'),'transport',encode(transport,'hex'),
  'membership',jsonb_build_object('storage_row_id',member_id,'type_id',(object->'after'->>'type_id')::int,'key_num',key_num,
   'object_id',(object->'after'->>'id')::bigint,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',namespace_sha256,'key_sha256',key_sha256,
   'original_context_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-context/0.2','attemptId',selected_attempt::text,
    'operationIndex',object->>'index','objectId',object->'after'->>'id','xid',attempt.writer_xid::text,'derivation','postgresql-umf-key-tuple-v1')::text,'UTF8')),
  'reservation',jsonb_build_object('storage_row_id',reservation_id,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',namespace_sha256,'key_sha256',key_sha256,
   'original_reservation_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-reservation/0.1','attemptId',selected_attempt::text,
    'operationIndex',object->>'index','objectId',object->'after'->>'id','typeId',object->'after'->>'type_id',
    'keyNumber',key_num::text,'xid',attempt.writer_xid::text)::text,'UTF8')))),'[]') INTO keys FROM allocated;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(keys) k WHERE k.value->'old'='null'::jsonb) THEN
  RAISE EXCEPTION 'original live batch key membership required' USING ERRCODE='55000';END IF;
 -- The planner's key preflight already locked every old and proposed route
 -- under the transaction's graph-writer gate. Replaying
 -- lock_string_key_bucket once per key here repeated several indexed queries
 -- for every row in large batches. Recheck the relevant exact bytes in two
 -- set-based reads while the preflight row locks remain held.
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(keys) k
  WHERE NOT EXISTS(SELECT 1 FROM truss.key_bucket_guard g
   WHERE g.namespace_sha256=decode(substring(k.value->'membership'->>'namespace_sha256' FROM 3),'hex')
    AND g.key_sha256=decode(substring(k.value->'membership'->>'key_sha256' FROM 3),'hex'))) THEN
  RAISE EXCEPTION 'original locked batch key routes required' USING ERRCODE='55000';END IF;
 WITH routes AS MATERIALIZED (
  SELECT value,decode(value->>'namespace','hex') namespace_bytes,decode(value->>'transport','hex') key_bytes,
   decode(substring(value->'membership'->>'namespace_sha256' FROM 3),'hex') namespace_sha256,
   decode(substring(value->'membership'->>'key_sha256' FROM 3),'hex') key_sha256,
   (value->'changed'='true'::jsonb) changed,(value->'old'->>'storage_row_id')::bigint old_storage_row_id
  FROM jsonb_array_elements(keys)), observed AS MATERIALIZED (
  SELECT r.*,coalesce(m.members,0) members,m.member_id,
   EXISTS(SELECT 1 FROM truss.object_key_reservation_bucket z WHERE z.namespace_sha256=r.namespace_sha256
    AND z.key_sha256=r.key_sha256 AND z.namespace_bytes=r.namespace_bytes AND z.key_bytes=r.key_bytes) reserved
  FROM routes r LEFT JOIN LATERAL (SELECT count(*) members,min(b.storage_row_id) member_id
   FROM truss.object_key_bucket b WHERE b.namespace_sha256=r.namespace_sha256
    AND b.key_sha256=r.key_sha256 AND b.namespace_bytes=r.namespace_bytes AND b.key_bytes=r.key_bytes) m ON true)
 SELECT coalesce(bool_or(changed AND (members>0 OR reserved)),false),
  coalesce(bool_or(NOT changed AND (members<>1 OR member_id<>old_storage_row_id)),false)
 INTO key_taken,unchanged_problem FROM observed;
 IF key_taken THEN
  RAISE EXCEPTION 'key allocated or reserved' USING ERRCODE='23505';END IF;
 IF unchanged_problem THEN
  RAISE EXCEPTION 'owned unchanged batch key required' USING ERRCODE='55000';END IF;
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
 WITH object_properties AS MATERIALIZED (
  SELECT value object,value->'before'->'props' before_props,value->'after'->'props' after_props
   FROM jsonb_array_elements(objects) WHERE value->'changed'='true'::jsonb),
 semantic AS MATERIALIZED (
  SELECT (o.object->>'index')::int operation_index,o.object->'identity' identity,(o.object->'after'->>'id')::bigint object_id,
   (o.object->'after'->>'type_id')::int type_id,(o.object->'after'->>'ver')::bigint version,
   (o.object->'after'->>'rev')::int revision,p.prop_id ordinal,
   jsonb_build_object('operation','property','propertyId',p.prop_id::text,
    'definitionPin',dictionary->jsonb_build_array((o.object->'after'->>'rev')::int,p.type_id)::text->'propertyPins'->>p.prop_id::text,
    'before',CASE WHEN o.before_props ? p.prop_id::text THEN jsonb_build_object('present',true,'value',o.before_props->p.prop_id::text) ELSE '{"present":false}'::jsonb END,
    'after',CASE WHEN o.after_props ? p.prop_id::text THEN jsonb_build_object('present',true,'value',o.after_props->p.prop_id::text) ELSE '{"present":false}'::jsonb END) event
  FROM object_properties o JOIN truss.prop_def p ON p.type_id=(o.object->'after'->>'type_id')::int
   AND p.since_rev<=(o.object->'after'->>'rev')::int AND (p.retired_rev IS NULL OR p.retired_rev>(o.object->'after'->>'rev')::int)
  WHERE o.object->'changed'='true'::jsonb AND o.before_props->p.prop_id::text IS DISTINCT FROM o.after_props->p.prop_id::text
  UNION ALL SELECT (o.object->>'index')::int,o.object->'identity' identity,(o.object->'after'->>'id')::bigint object_id,
   (o.object->'after'->>'type_id')::int type_id,(o.object->'after'->>'ver')::bigint version,
   (o.object->'after'->>'rev')::int revision,2147483648,jsonb_build_object('operation','metadata',
   'before',truss.runtime_owned_history_record_in_metadata(o.object->'before',o.object->'identity',dictionary->jsonb_build_array((o.object->'before'->>'rev')::int,(o.object->'before'->>'type_id')::int)::text),
   'after',truss.runtime_owned_history_record_in_metadata(o.object->'after',o.object->'identity',dictionary->jsonb_build_array((o.object->'after'->>'rev')::int,(o.object->'after'->>'type_id')::int)::text))
  FROM object_properties o WHERE o.object->'changed'='true'::jsonb),
 allocated AS MATERIALIZED (
  SELECT *,nextval('truss.journal_seq') seq,clock_timestamp() at FROM semantic ORDER BY operation_index,ordinal),
 events AS MATERIALIZED (
  SELECT operation_index,ordinal,seq,at,object_id,type_id,version,revision,
   event->>'operation' operation,(event->>'propertyId')::int property_id,event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',seq::text,'identity',identity,
   'eventVersion',version::text,'eventCatalogRevision',revision::text,
   'origin',origin_payload) payload FROM allocated),
 digests AS MATERIALIZED (
  SELECT operation_index,count(*) amount,encode(sha256(convert_to(jsonb_agg(payload ORDER BY ordinal)::text,'UTF8')),'hex') digest
  FROM events GROUP BY operation_index)
, expected_rows AS MATERIALIZED (
 SELECT e.operation_index,e.seq,e.at,attempt.writer_xid xid,'o'::text entity_kind,e.object_id entity_id,e.type_id entity_type,e.version ver,
  CASE e.operation WHEN 'property' THEN 'update' ELSE 'metadata' END op,e.property_id prop_id,NULL::jsonb old_value,e.revision rev,
  truss.runtime_exact_wrapper('event',convert_to((e.payload||jsonb_build_object('mutationGroup',
   jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',d.amount::text,'orderedEventDigest',d.digest)))::text,'UTF8')) new_value,
  expected_origin_wrapper origin
 FROM events e JOIN digests d ON d.operation_index=e.operation_index),
 fingerprints AS MATERIALIZED (
  SELECT operation_index,seq,at,xid,entity_kind,entity_id,entity_type,ver,op,prop_id,old_value,rev,
   sha256(convert_to(new_value::text,'UTF8')) new_value_hash,expected_origin_hash origin_hash
  FROM expected_rows),
 inserted AS (
  INSERT INTO truss.journal(seq,at,xid,entity_kind,entity_id,entity_type,ver,op,prop_id,old_value,rev,new_value,origin)
  SELECT seq,at,xid,entity_kind,entity_id,entity_type,ver,op,prop_id,old_value,rev,new_value,origin FROM expected_rows
  RETURNING seq,at,xid,entity_kind,entity_id,entity_type,ver,op,prop_id,old_value,rev,
   sha256(convert_to(new_value::text,'UTF8')) new_value_hash,
   sha256(convert_to(origin::text,'UTF8')) origin_hash)
 SELECT coalesce(bool_or(ROW(i.seq,i.at,i.xid,i.entity_kind,i.entity_id,i.entity_type,i.ver,i.op,i.prop_id,i.old_value,i.rev)
  IS DISTINCT FROM ROW(e.seq,e.at,e.xid,e.entity_kind,e.entity_id,e.entity_type,e.ver,e.op,e.prop_id,e.old_value,e.rev)
  OR ROW(i.new_value_hash,i.origin_hash) IS DISTINCT FROM ROW(e.new_value_hash,e.origin_hash)),false),
  coalesce(jsonb_agg(jsonb_build_object('index',e.operation_index,'seq',e.seq,'at',e.at) ORDER BY e.seq),'[]')
 INTO projection_problem,journal_refs FROM fingerprints e FULL JOIN inserted i ON i.seq=e.seq;
 IF projection_problem THEN RAISE EXCEPTION 'exact batch update journals required' USING ERRCODE='55000';END IF;
 -- The physical journal owns the canonical event and origin payloads. Object
 -- transitions retain compact, payload-free references with their exact digests.
 WITH journal_sets AS MATERIALIZED (
  SELECT (r.value->>'index')::int operation_index,jsonb_agg(truss.runtime_owned_journal_reference(j) ORDER BY j.seq) rows
  FROM jsonb_array_elements(journal_refs) r JOIN truss.journal j ON j.seq=(r.value->>'seq')::bigint AND j.at=(r.value->>'at')::timestamptz
  GROUP BY (r.value->>'index')::int),
 expected_rows AS MATERIALIZED (
  SELECT attempt.id attempt_id,(o.value->>'index')::int operation_index,attempt.writer_xid writer_xid,
   (o.value->'after'->>'id')::bigint object_id,(o.value->'after'->>'type_id')::int type_id,
   o.value->'before' before_object,o.value->'after' after_object,
   (SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]') FROM truss.object_key_bucket k
    WHERE k.object_id=(o.value->'after'->>'id')::bigint AND k.type_id=(o.value->'after'->>'type_id')::int) after_keys,
   j.rows journal FROM jsonb_array_elements(objects) o JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int),
 fingerprints AS MATERIALIZED (
  SELECT attempt_id,operation_index,writer_xid,object_id,type_id,
   sha256(convert_to(before_object::text,'UTF8')) before_hash,
   sha256(convert_to(after_object::text,'UTF8')) after_hash,
   sha256(convert_to(after_keys::text,'UTF8')) keys_hash,
   sha256(convert_to(journal::text,'UTF8')) journal_hash
  FROM expected_rows),
 inserted AS (
  INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
  SELECT r.* FROM expected_rows r RETURNING attempt_id,operation_index,writer_xid,object_id,type_id,
   sha256(convert_to(before_object::text,'UTF8')) before_hash,
   sha256(convert_to(after_object::text,'UTF8')) after_hash,
   sha256(convert_to(after_keys::text,'UTF8')) keys_hash,
   sha256(convert_to(journal::text,'UTF8')) journal_hash)
 SELECT coalesce(bool_or(ROW(i.attempt_id,i.operation_index,i.writer_xid,i.object_id,i.type_id)
  IS DISTINCT FROM ROW(e.attempt_id,e.operation_index,e.writer_xid,e.object_id,e.type_id)
  OR ROW(i.before_hash,i.after_hash,i.keys_hash,i.journal_hash)
  IS DISTINCT FROM ROW(e.before_hash,e.after_hash,e.keys_hash,e.journal_hash)),false)
 INTO projection_problem FROM fingerprints e FULL JOIN inserted i ON i.operation_index=e.operation_index;
 IF projection_problem THEN RAISE EXCEPTION 'exact batch update transitions required' USING ERRCODE='55000';END IF;
 WITH journal_sets AS MATERIALIZED (
  SELECT (value->>'index')::int operation_index,jsonb_agg(jsonb_build_object('sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',value->>'seq')
    ORDER BY (value->>'seq')::bigint) events FROM jsonb_array_elements(journal_refs) GROUP BY (value->>'index')::int),
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
DECLARE initial_scope jsonb;last_plan jsonb;scope_nodes jsonb;event_dictionary jsonb;owner record;problem boolean;changed_count int;
 input_operations jsonb:=input->'operations';
BEGIN
 SELECT plan->'initialScope' INTO STRICT initial_scope FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=0;
 scope_nodes:=initial_scope->'nodes';
 SELECT plan INTO STRICT last_plan FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=attempt.next_index-1;
 IF (last_plan->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>(last_plan->>'catalogRevision')::int)
  OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR attempt.next_index<>jsonb_array_length(input_operations)
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id)<>attempt.next_index
  OR attempt.aliases<>'[]'::jsonb OR EXISTS(SELECT 1 FROM jsonb_array_elements(input_operations) o
   WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange')
  OR (SELECT count(DISTINCT plan->>'primary') FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id)<>attempt.next_index
  OR EXISTS(SELECT 1 FROM jsonb_each(scope_nodes) n WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb
   OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb) THEN
  RAISE EXCEPTION 'independent original rootless update inventory required' USING ERRCODE='55000';END IF;
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
  SELECT f.*,f.desired->'identity' identity,
   (f.prior->'image'->>'ver')::bigint IS DISTINCT FROM (f.desired->'image'->>'ver')::bigint changed,
   t.transition_id,t.writer_xid,t.object_id,t.type_id,
   t.before_object,t.after_object
  FROM frames f LEFT JOIN LATERAL (
   SELECT t.* FROM truss.runtime_object_transition t WHERE t.attempt_id=attempt.id AND t.operation_index=f.operation_index OFFSET 0) t ON true)
 SELECT EXISTS(SELECT 1 FROM members m WHERE
  m.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
  OR m.plan->'operationIndex' IS DISTINCT FROM to_jsonb(m.operation_index)
  OR m.plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
  OR m.plan->'operation' IS DISTINCT FROM input_operations->m.operation_index
  OR m.plan->>'actorName' IS DISTINCT FROM session_user::text
  OR m.plan->>'primary' IS DISTINCT FROM 'stored:'||(m.identity->>'typeId')||':'||(m.identity->>'id')
  OR m.operation_index<0 OR m.operation_index>=attempt.next_index
  OR m.identity IS DISTINCT FROM m.plan->'operation'->'target'->'identity'
  OR m.prior IS NULL OR m.desired IS NULL
  OR NOT (scope_nodes ? ((m.identity->>'typeId')||':'||(m.identity->>'id')))
  OR scope_nodes->((m.identity->>'typeId')||':'||(m.identity->>'id'))->>'id' IS DISTINCT FROM m.identity->>'id'
  OR scope_nodes->((m.identity->>'typeId')||':'||(m.identity->>'id'))->>'type_id' IS DISTINCT FROM m.identity->>'typeId'
  OR (scope_nodes->((m.identity->>'typeId')||':'||(m.identity->>'id'))->>'ver')::bigint
   IS DISTINCT FROM (m.prior->'image'->>'ver')::bigint
  OR m.prior->'image'->'ver' IS NULL OR m.desired->'image'->'ver' IS NULL
  OR m.prior->'identity' IS DISTINCT FROM m.identity
  OR m.desired->'identity' IS DISTINCT FROM m.prior->'identity'
  OR m.desired->'root' IS DISTINCT FROM 'null'::jsonb OR m.desired->'deleted' IS DISTINCT FROM 'false'::jsonb
  OR m.prior->'root' IS DISTINCT FROM 'null'::jsonb OR m.prior->'deleted' IS DISTINCT FROM 'false'::jsonb
  OR CASE WHEN m.changed THEN m.transition_id IS NULL OR m.writer_xid IS DISTINCT FROM attempt.writer_xid
   OR m.object_id::text IS DISTINCT FROM m.identity->>'id' OR m.type_id::text IS DISTINCT FROM m.identity->>'typeId'
   OR m.before_object IS NULL OR m.after_object IS NULL
   OR m.before_object->>'id' IS DISTINCT FROM m.identity->>'id'
   OR m.before_object->>'type_id' IS DISTINCT FROM m.identity->>'typeId'
   OR (m.before_object->>'ver')::bigint IS DISTINCT FROM (m.prior->'image'->>'ver')::bigint
   OR m.before_object->'root_id' IS DISTINCT FROM 'null'::jsonb OR m.before_object->'root_type' IS DISTINCT FROM 'null'::jsonb
   OR m.after_object->>'id' IS DISTINCT FROM m.identity->>'id'
   OR m.after_object->>'type_id' IS DISTINCT FROM m.identity->>'typeId'
   OR (m.after_object->>'ver')::bigint IS DISTINCT FROM (m.desired->'image'->>'ver')::bigint
   OR m.after_object->'root_id' IS DISTINCT FROM 'null'::jsonb OR m.after_object->'root_type' IS DISTINCT FROM 'null'::jsonb
   OR m.after_object->'created_at' IS DISTINCT FROM m.before_object->'created_at'
   OR (m.after_object->>'ver')::bigint IS DISTINCT FROM (m.before_object->>'ver')::bigint+1
   ELSE m.transition_id IS NOT NULL END) INTO problem;
 IF problem THEN RAISE EXCEPTION 'original batch update plan and transition correspondence required' USING ERRCODE='55000';END IF;
 SELECT count(*) INTO changed_count FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id
  AND (p.plan->'beforeNodes'->(p.plan->>'primary')->'image'->>'ver')::bigint
   IS DISTINCT FROM (p.plan->'afterNodes'->(p.plan->>'primary')->'image'->>'ver')::bigint;
 IF (SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=attempt.id)<>changed_count
  OR EXISTS(SELECT 1 FROM truss.runtime_edge_transition WHERE attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'complete original batch update effect inventory required' USING ERRCODE='55000';END IF;
 -- The protected batch producer already checked every actual journal and
 -- transition INSERT against its exact prepared rows before advancing progress.
 -- Immutable stores and per-journal commit checks retain physical correspondence.
 -- Settlement checks custody, results, current authority and final native state;
 -- it does not execute the complete semantic history producer a second time.
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
   'outcome',CASE WHEN (p.plan->'beforeNodes'->(p.plan->>'primary')->'image'->>'ver')::bigint
    IS DISTINCT FROM (p.plan->'afterNodes'->(p.plan->>'primary')->'image'->>'ver')::bigint THEN 'changed' ELSE 'unchanged' END,
   'identity',p.plan->'afterNodes'->(p.plan->>'primary')->'identity',
   'version',p.plan->'afterNodes'->(p.plan->>'primary')->'image'->>'ver','events',coalesce(event_dictionary->p.operation_index::text,'[]'::jsonb))) INTO problem;
 IF problem THEN RAISE EXCEPTION 'exact original batch update results required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch_validate(truss.runtime_object_attempt,jsonb,jsonb,oid) FROM PUBLIC;
