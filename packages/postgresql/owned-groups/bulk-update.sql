-- Distinct stored-object value updates with unchanged ownership
-- have no order-dependent effects. The original planner, key preflight and
-- finish/commit validators still establish their complete source correspondence.
CREATE FUNCTION truss.runtime_owned_update_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;objects jsonb;transitions jsonb;results jsonb;
 dictionary jsonb:='{}';history_basis jsonb;image_revision int;selected_type int;property record;pin record;type_pin text;
 dictionary_keys text[]:=ARRAY[]::text[];dictionary_values jsonb[]:=ARRAY[]::jsonb[];
 codec_keys text[]:=ARRAY[]::text[];codec_values jsonb[]:=ARRAY[]::jsonb[];
 namespace_keys text[]:=ARRAY[]::text[];namespace_values jsonb[]:=ARRAY[]::jsonb[];map_count int;
 property_pins jsonb;property_order jsonb;source record;actor oid;total int;counted int;
 namespaces jsonb:='{}';compiled_namespace bytea;definition record;keys jsonb;route record;
 slot_results jsonb;projection_problem boolean;journal_refs jsonb;
 journal_chunk_objects jsonb;journal_ref_chunks jsonb[]:=ARRAY[]::jsonb[];journal_chunk_count int;journal_chunk_index int;journal_chunk_start int;
 history_records jsonb;changed_key_count int;changed_object_count int;
 codecs jsonb:='{}';codec jsonb;codec_bytes bigint:=2;
 origin_payload jsonb;expected_origin_wrapper jsonb;
 compact_plans boolean:=false;scope_nodes jsonb;head_revision int;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 total:=jsonb_array_length(input->'operations');
 origin_payload:=jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text);
 expected_origin_wrapper:=truss.runtime_exact_wrapper('origin',convert_to(origin_payload::text,'UTF8'));
 SELECT EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt
  AND p.plan ? 'compactProfile') INTO compact_plans;
 IF compact_plans THEN
  SELECT p.plan->'initialScope'->'nodes' INTO scope_nodes FROM truss.runtime_owned_operation p
   WHERE p.attempt_id=selected_attempt AND p.operation_index=0;
  SELECT rev INTO STRICT head_revision FROM truss.schema_head WHERE id=1;
 END IF;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.complete OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() OR total NOT BETWEEN 1 AND 1024
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored'
    OR o.value ? 'ownershipChange')
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
  OR (SELECT count(DISTINCT plan->>'primary') FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
 THEN
  RAISE EXCEPTION 'independent original value update batch required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 -- Bind every physical before-image before the single UPDATE. The initial
 -- scope has already locked these rows; duplicate targets use ordered execution.
 IF compact_plans THEN
  IF jsonb_typeof(scope_nodes) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'one compact original rootless source snapshot required' USING ERRCODE='55000';END IF;
  -- The capture locked the source rows and retained this snapshot. Reuse it
  -- for history and apply the expected-version predicate in the UPDATE below;
  -- do not clone/recompare complete physical and planned images in four spools.
  WITH members AS (
   SELECT p.operation_index,q."applicationPatch" application_patch,
    q."beforeNodes"->q."primary" prior,q."afterNodes"->q."primary" desired,
    q."beforeNodes"->q."primary"->'identity' identity,
    scope_nodes->substring(q."primary" FROM 8) snapshot
   FROM truss.runtime_owned_operation p
   CROSS JOIN LATERAL jsonb_to_record(p.plan) q("applicationPatch" jsonb,"beforeNodes" jsonb,"afterNodes" jsonb,"primary" text)
   WHERE p.attempt_id=selected_attempt),
  projected AS MATERIALIZED (
   SELECT operation_index,identity,snapshot,desired->'image' desired_header,
    prior IS DISTINCT FROM desired changed,
    snapshot IS NOT NULL AND snapshot->>'ver'=prior->'image'->>'ver' before_matches,
    truss.runtime_owned_application_values((identity->>'typeId')::int,operation_index,
     application_patch,snapshot->'props',nullif(snapshot->'retained','null'::jsonb)) values_image
   FROM members),
  framed AS (
   SELECT operation_index,identity,snapshot,changed,before_matches,
    (desired_header-ARRAY['created_at','updated_at','props','retained','root_id','root_type'])||
     jsonb_build_object('props',values_image->'props','retained',nullif(values_image->'retained','{}'::jsonb),
      'id',(identity->>'id')::bigint,'root_id',NULL::bigint,'root_type',NULL::int) desired_image
   FROM projected)
  SELECT jsonb_agg(jsonb_build_object('index',operation_index,'identity',identity,'before',snapshot,
   'after',CASE WHEN NOT changed THEN snapshot ELSE desired_image||jsonb_build_object(
    'created_at',snapshot->'created_at','updated_at',clock_timestamp()) END,
   'beforeMatches',before_matches,'changed',changed) ORDER BY operation_index)
  INTO objects FROM framed;
 ELSE
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
 END IF;
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
  map_count:=cardinality(dictionary_keys)+1;
  dictionary_keys[map_count]:=jsonb_build_array(image_revision,selected_type)::text;
  dictionary_values[map_count]:=history_basis;
 END LOOP;
 SELECT coalesce(jsonb_object_agg(k,v),'{}'::jsonb) INTO dictionary
  FROM unnest(dictionary_keys,dictionary_values) AS entries(k,v);
 -- Preserve the preflight's complete ordered key simulation and locks. Lower
 -- only the already admitted physical key changes; unchanged memberships keep
 -- their original bytes and permanent reservations are never removed.
 FOR selected_type IN SELECT DISTINCT (value->'after'->>'type_id')::int FROM jsonb_array_elements(objects) LOOP
  FOR definition IN SELECT * FROM truss.key_def WHERE type_id=selected_type AND retired_rev IS NULL ORDER BY key_num LOOP
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',selected_type,definition.key_num);
   codec:=truss.runtime_owned_key_codec_metadata(selected_type,definition.key_num);
   IF codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32<=4194304 THEN
    map_count:=cardinality(codec_keys)+1;
    codec_keys[map_count]:=selected_type::text||':'||definition.key_num::text;
    codec_values[map_count]:=codec;
    codec_bytes:=codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32;
   END IF;
   compiled_namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected_type::text,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   map_count:=cardinality(namespace_keys)+1;
   namespace_keys[map_count]:=selected_type::text||':'||definition.key_num::text;
   namespace_values[map_count]:=to_jsonb(encode(compiled_namespace,'hex'));
  END LOOP;
 END LOOP;
 SELECT coalesce(jsonb_object_agg(k,v),'{}'::jsonb) INTO codecs
  FROM unnest(codec_keys,codec_values) AS entries(k,v);
 SELECT coalesce(jsonb_object_agg(k,v),'{}'::jsonb) INTO namespaces
  FROM unnest(namespace_keys,namespace_values) AS entries(k,v);
 -- Key rows carry identity scalars, never the object's complete images. Each
 -- object can have many keys; retaining its image here multiplies every spool.
 WITH cells AS MATERIALIZED (
  SELECT o.value->>'index' operation_index,(o.value->'after'->>'id')::bigint object_id,
   (o.value->'after'->>'type_id')::int type_id,
   k.key_num,decode(namespaces->>((o.value->'after'->>'type_id')||':'||k.key_num::text),'hex') namespace,
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
  'membership',jsonb_build_object('storage_row_id',member_id,'type_id',type_id,'key_num',key_num,
   'object_id',object_id,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',namespace_sha256,'key_sha256',key_sha256,
   'original_context_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-context/0.2','attemptId',selected_attempt::text,
    'operationIndex',operation_index,'objectId',object_id::text,'xid',attempt.writer_xid::text,'derivation','postgresql-umf-key-tuple-v1')::text,'UTF8')),
  'reservation',jsonb_build_object('storage_row_id',reservation_id,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',namespace_sha256,'key_sha256',key_sha256,
   'original_reservation_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-reservation/0.1','attemptId',selected_attempt::text,
    'operationIndex',operation_index,'objectId',object_id::text,'typeId',type_id::text,
    'keyNumber',key_num::text,'xid',attempt.writer_xid::text)::text,'UTF8')))),'[]') INTO keys FROM allocated;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(keys) k WHERE k.value->'old'='null'::jsonb) THEN
  RAISE EXCEPTION 'original live batch key membership required' USING ERRCODE='55000';END IF;
 -- Key uniqueness and reservations were observed once by preflight under
 -- the held global writer gate; producer DML cannot interleave caller writes.
 -- The trusted producer selects locked keys and native constraints enforce
 -- their identities. Count affected rows; do not serialize every row twice to
 -- defend against administrator-installed rewriting triggers.
 SELECT count(*) INTO changed_key_count FROM jsonb_array_elements(keys) k WHERE k.value->'changed'='true'::jsonb;
 DELETE FROM truss.object_key_bucket old USING jsonb_array_elements(keys) k
 WHERE k.value->'changed'='true'::jsonb AND old.storage_row_id=(k.value->'old'->>'storage_row_id')::bigint;
 GET DIAGNOSTICS counted=ROW_COUNT;
 IF counted<>changed_key_count THEN RAISE EXCEPTION 'complete batch old key removal required' USING ERRCODE='55000';END IF;
 INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
 SELECT r.storage_row_id,r.type_id,r.key_num,r.object_id,r.namespace_bytes,r.key_bytes,r.original_context_bytes
 FROM jsonb_array_elements(keys) k CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,k.value->'membership') r
 WHERE k.value->'changed'='true'::jsonb;
 GET DIAGNOSTICS counted=ROW_COUNT;
 IF counted<>changed_key_count THEN RAISE EXCEPTION 'complete batch key memberships required' USING ERRCODE='55000';END IF;
 INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes)
 SELECT r.storage_row_id,r.namespace_bytes,r.key_bytes,r.original_reservation_bytes FROM jsonb_array_elements(keys) k
 CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_reservation_bucket,k.value->'reservation') r
 WHERE k.value->'changed'='true'::jsonb;
 GET DIAGNOSTICS counted=ROW_COUNT;
 IF counted<>changed_key_count THEN RAISE EXCEPTION 'complete batch key reservations required' USING ERRCODE='55000';END IF;
 WITH key_routes AS MATERIALIZED (
  SELECT substring(value->'old'->>'namespace_sha256' FROM 3) old_namespace_hex,
   substring(value->'old'->>'key_sha256' FROM 3) old_key_hex,
   substring(value->'membership'->>'namespace_sha256' FROM 3) new_namespace_hex,
   substring(value->'membership'->>'key_sha256' FROM 3) new_key_hex
  FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb),
 routes AS MATERIALIZED (
  SELECT decode(namespace_hex,'hex') namespace_sha256,decode(key_hex,'hex') key_sha256,count(*) advances
  FROM (SELECT old_namespace_hex namespace_hex,old_key_hex key_hex FROM key_routes
   UNION ALL SELECT new_namespace_hex,new_key_hex FROM key_routes) all_routes
  GROUP BY namespace_hex,key_hex)
 UPDATE truss.key_bucket_guard g SET generation=g.generation+routes.advances FROM routes
 WHERE g.namespace_sha256=routes.namespace_sha256 AND g.key_sha256=routes.key_sha256;
 SELECT count(*) INTO changed_object_count FROM jsonb_array_elements(objects) v WHERE v.value->'changed'='true'::jsonb;
 UPDATE truss.object o SET props=r.props,retained=r.retained,root_id=r.root_id,root_type=r.root_type,
  rev=r.rev,ver=r.ver,updated_at=r.updated_at
 FROM jsonb_array_elements(objects) v CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object,v.value->'after') r
 WHERE v.value->'changed'='true'::jsonb AND o.id=r.id AND o.type_id=r.type_id
  AND o.ver=(v.value->'before'->>'ver')::bigint;
 GET DIAGNOSTICS counted=ROW_COUNT;
 IF counted<>changed_object_count THEN
  RAISE EXCEPTION 'complete version-matched batch object updates required' USING ERRCODE='55000';END IF;
 journal_chunk_count:=(total+63)/64;
 FOR journal_chunk_index IN 1..journal_chunk_count LOOP
  journal_chunk_start:=(journal_chunk_index-1)*64;
  SELECT coalesce(jsonb_agg(objects->object_offset ORDER BY object_offset),'[]'::jsonb)
   INTO journal_chunk_objects
  FROM generate_series(journal_chunk_start,least(journal_chunk_start+63,total-1)) object_offset;
  SELECT truss.runtime_owned_history_records_in_metadata(journal_chunk_objects,dictionary)
   INTO history_records;
 WITH object_properties AS NOT MATERIALIZED (
  SELECT value object,value->'before'->'props' before_props,value->'after'->'props' after_props
   FROM jsonb_array_elements(journal_chunk_objects) WHERE value->'changed'='true'::jsonb),
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
   'before',history_records->(o.object->>'index')->'before',
   'after',history_records->(o.object->>'index')->'after')
  FROM object_properties o WHERE o.object->'changed'='true'::jsonb),
 allocated AS MATERIALIZED (
  SELECT operation_index,ordinal,nextval('truss.journal_seq') seq,clock_timestamp() at
  FROM semantic ORDER BY operation_index,ordinal),
 events AS MATERIALIZED (
  SELECT s.operation_index,s.ordinal,a.seq,a.at,s.object_id,s.type_id,s.version,s.revision,
   s.event->>'operation' operation,(s.event->>'propertyId')::int property_id,s.event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',a.seq::text,'identity',s.identity,
   'eventVersion',s.version::text,'eventCatalogRevision',s.revision::text,
   'origin',origin_payload) payload FROM semantic s JOIN allocated a USING(operation_index,ordinal)),
 digests AS MATERIALIZED (
  SELECT operation_index,count(*) amount,encode(sha256(convert_to(jsonb_agg(payload ORDER BY ordinal)::text,'UTF8')),'hex') digest
  FROM events GROUP BY operation_index)
, expected_rows AS (
 SELECT e.operation_index,e.seq,e.at,attempt.writer_xid xid,'o'::text entity_kind,e.object_id entity_id,e.type_id entity_type,e.version ver,
  CASE e.operation WHEN 'property' THEN 'update' ELSE 'metadata' END op,e.property_id prop_id,NULL::jsonb old_value,e.revision rev,
  truss.runtime_exact_wrapper('event',convert_to((e.payload||jsonb_build_object('mutationGroup',
   jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',d.amount::text,'orderedEventDigest',d.digest)))::text,'UTF8')) new_value,
  expected_origin_wrapper origin
 FROM events e JOIN digests d ON d.operation_index=e.operation_index),
 inserted AS (
  INSERT INTO truss.journal(seq,at,xid,entity_kind,entity_id,entity_type,ver,op,prop_id,old_value,rev,new_value,origin)
  SELECT seq,at,xid,entity_kind,entity_id,entity_type,ver,op,prop_id,old_value,rev,new_value,origin FROM expected_rows
  RETURNING seq,at,xid,entity_kind,entity_id,entity_type,ver,op,prop_id,old_value,rev,
   new_value->'bytesSha256' event_sha256,origin->'bytesSha256' origin_sha256)
 SELECT count(*) IS DISTINCT FROM (SELECT count(*) FROM allocated),
  coalesce(jsonb_agg(jsonb_build_object('index',a.operation_index,'reference',jsonb_build_object(
   'referenceProfile','truss-native-journal-reference/0.1','seq',i.seq,'at',i.at,'xid',i.xid,
   'entity_kind',i.entity_kind,'entity_id',i.entity_id,'entity_type',i.entity_type,'ver',i.ver,
   'op',i.op,'prop_id',i.prop_id,'old_value',i.old_value,'rev',i.rev,
   'eventSha256',i.event_sha256,'originSha256',i.origin_sha256)) ORDER BY i.seq),'[]')
 INTO projection_problem,journal_refs
 FROM inserted i JOIN allocated a ON a.seq=i.seq;
 IF projection_problem THEN RAISE EXCEPTION 'complete batch update journals required' USING ERRCODE='55000';END IF;
  journal_ref_chunks[journal_chunk_index]:=journal_refs;
 END LOOP;
 SELECT coalesce(jsonb_agg(entry.value ORDER BY page.page_index,entry.item_index),'[]'::jsonb)
  INTO journal_refs
 FROM unnest(journal_ref_chunks) WITH ORDINALITY page(page_refs,page_index)
 CROSS JOIN LATERAL jsonb_array_elements(page.page_refs) WITH ORDINALITY entry(value,item_index);
 -- The physical journal owns the canonical event and origin payloads. Object
 -- transitions retain compact, payload-free references with their exact digests.
 WITH journal_sets AS MATERIALIZED (
  SELECT (r.value->>'index')::int operation_index,
   jsonb_agg(r.value->'reference' ORDER BY (r.value->'reference'->>'seq')::bigint) rows
  FROM jsonb_array_elements(journal_refs) r GROUP BY (r.value->>'index')::int),
 expected_rows AS (
  SELECT attempt.id attempt_id,(o.value->>'index')::int operation_index,attempt.writer_xid writer_xid,
   (o.value->'after'->>'id')::bigint object_id,(o.value->'after'->>'type_id')::int type_id,
   o.value->'before' before_object,o.value->'after' after_object,
   (SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]') FROM truss.object_key_bucket k
    WHERE k.object_id=(o.value->'after'->>'id')::bigint AND k.type_id=(o.value->'after'->>'type_id')::int) after_keys,
   j.rows journal FROM jsonb_array_elements(objects) o JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int),
 inserted AS (
  INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
  SELECT r.* FROM expected_rows r RETURNING operation_index)
 SELECT count(*) INTO counted FROM inserted;
 IF counted<>changed_object_count THEN
  RAISE EXCEPTION 'complete batch update transitions required' USING ERRCODE='55000';END IF;
 WITH journal_sets AS MATERIALIZED (
  SELECT (value->>'index')::int operation_index,jsonb_agg(jsonb_build_object('sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',value->'reference'->>'seq')
    ORDER BY (value->'reference'->>'seq')::bigint) events FROM jsonb_array_elements(journal_refs) GROUP BY (value->>'index')::int),
 slots AS (
  SELECT (o.value->>'index')::int operation_index,jsonb_build_object('operation','update_object',
   'outcome',CASE WHEN o.value->'changed'='true'::jsonb THEN 'changed' ELSE 'unchanged' END,'identity',o.value->'identity',
   'version',o.value->'after'->>'ver','events',coalesce(j.events,'[]'::jsonb)) result
  FROM jsonb_array_elements(objects) o LEFT JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int)
 SELECT jsonb_object_agg(operation_index::text,result) INTO slot_results FROM slots;
 WITH updated AS (
  UPDATE truss.runtime_owned_operation p SET result=slot_results->p.operation_index::text
  WHERE p.attempt_id=selected_attempt AND p.result IS NULL AND slot_results ? p.operation_index::text
  RETURNING p.operation_index)
 SELECT count(*) INTO counted FROM updated;
 IF counted<>total THEN RAISE EXCEPTION 'complete exact batch update result slots required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch update progress advance required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch(uuid) FROM PUBLIC;

-- The trusted producer owns plan interpretation and exact event construction.
-- Settlement checks freshness and transaction custody; common group settlement
-- checks the retained result inventory and current authority. Do not replay the
-- private immutable plans as an independent semantic verifier.
CREATE FUNCTION truss.runtime_owned_update_batch_validate(attempt truss.runtime_object_attempt,input jsonb,history_dictionary jsonb,actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE revision int;
BEGIN
 SELECT (p.plan->>'catalogRevision')::int INTO STRICT revision
 FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.operation_index=0;
 IF revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>revision)
  OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
  OR attempt.actor_oid IS DISTINCT FROM actor THEN
  RAISE EXCEPTION 'current update revision and transaction required' USING ERRCODE='55000';END IF;
 IF (SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=attempt.id)
  IS DISTINCT FROM (SELECT count(*) FROM jsonb_array_elements(attempt.results) r WHERE r.value->>'outcome'='changed')
  OR EXISTS(SELECT 1 FROM truss.runtime_edge_transition WHERE attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'batch update effect inventory required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch_validate(truss.runtime_object_attempt,jsonb,jsonb,oid) FROM PUBLIC;
