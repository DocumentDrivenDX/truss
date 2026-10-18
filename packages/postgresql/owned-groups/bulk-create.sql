-- Independent rootless creates have no order-dependent reads. Lower their
-- already admitted native plans to INSERT ... SELECT, retaining the ordinary
-- transitions, original journals, permanent key reservations and settlement.
CREATE FUNCTION truss.runtime_owned_create_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;objects jsonb;keys jsonb;journals jsonb;transitions jsonb;results jsonb;
 expected jsonb;actual jsonb;dictionary jsonb:='{}';namespaces jsonb:='{}';metadata jsonb;
 dictionary_keys text[]:=ARRAY[]::text[];dictionary_values jsonb[]:=ARRAY[]::jsonb[];
 codec_keys text[]:=ARRAY[]::text[];codec_values jsonb[]:=ARRAY[]::jsonb[];
 namespace_keys text[]:=ARRAY[]::text[];namespace_values jsonb[]:=ARRAY[]::jsonb[];map_count int;
 selected_type int;definition record;pin record;type_pin text;property_pins jsonb;property_order jsonb;head_revision int;
 group_id uuid:=gen_random_uuid();actor oid;counted int;total int;compiled_namespace bytea;route record;
 slot_results jsonb;slot_problem boolean;
 codecs jsonb:='{}';codec jsonb;codec_bytes bigint:=2;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 total:=jsonb_array_length(input->'operations');
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.complete OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR total NOT BETWEEN 1 AND 1024 OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_object'
    OR o.value->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb)
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
  OR EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND
   (p.writer_xid IS DISTINCT FROM attempt.writer_xid OR p.result IS NOT NULL
    OR p.plan->'operation' IS DISTINCT FROM input->'operations'->p.operation_index
    OR p.plan->>'primary' IS DISTINCT FROM 'create:'||p.operation_index::text
    OR (p.plan->'beforeNodes') ? (p.plan->>'primary') OR p.plan->'beforeEdges'<>'{}'::jsonb
    OR p.plan->'afterEdges'<>'{}'::jsonb
    OR p.plan->'afterNodes'->(p.plan->>'primary')->'root' IS DISTINCT FROM 'null'::jsonb)) THEN
  RAISE EXCEPTION 'independent original rootless create batch required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF (SELECT value FROM truss.setting WHERE key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb
  OR (SELECT value FROM truss.setting WHERE key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
  RAISE EXCEPTION 'selected engine key/history settings required' USING ERRCODE='0A000';END IF;
 SELECT rev INTO STRICT head_revision FROM truss.schema_head WHERE id=1;
 -- Catalog interpretation is compiled once per type, not once per object.
 FOR selected_type IN SELECT DISTINCT (p.plan->'afterNodes'->(p.plan->>'primary')->'image'->>'type_id')::int
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt LOOP
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',selected_type);
  type_pin:=pin.definition_pin;
  PERFORM truss.runtime_module_writer_qualified(pin.document_id,pin.module_id,actor);
  IF NOT truss.runtime_object_values_readable_qualified(selected_type,actor) THEN
   RAISE EXCEPTION 'current property and item readers required' USING ERRCODE='42501';END IF;
  SELECT s.metadata INTO STRICT metadata FROM truss.runtime_type_schema s
   WHERE s.rev=head_revision AND s.type_id=selected_type;
  IF metadata->>'typeId' IS DISTINCT FROM selected_type::text
   OR metadata->>'revision' IS DISTINCT FROM head_revision::text
   OR metadata->>'typePin' IS DISTINCT FROM type_pin THEN
   RAISE EXCEPTION 'current compiled create schema required' USING ERRCODE='55000';END IF;
  property_pins:=metadata->'propertyPins';property_order:=metadata->'propertyOrder';
  map_count:=cardinality(dictionary_keys)+1;
  dictionary_keys[map_count]:=selected_type::text;
  dictionary_values[map_count]:=jsonb_build_object('typeId',selected_type::text,
   'revision',head_revision::text,'typePin',type_pin,'propertyOrder',property_order,'propertyPins',property_pins);
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
 -- Assemble each wide lookup map once after its inputs have been collected.
 -- Repeated jsonb concatenation recopies the growing map for every distinct type.
 SELECT coalesce(jsonb_object_agg(k,v),'{}'::jsonb) INTO dictionary
  FROM unnest(dictionary_keys,dictionary_values) AS entries(k,v);
 SELECT coalesce(jsonb_object_agg(k,v),'{}'::jsonb) INTO codecs
  FROM unnest(codec_keys,codec_values) AS entries(k,v);
 SELECT coalesce(jsonb_object_agg(k,v),'{}'::jsonb) INTO namespaces
  FROM unnest(namespace_keys,namespace_values) AS entries(k,v);
 WITH allocated AS MATERIALIZED (
  SELECT p.operation_index,p.plan->'operation' operation,
   p.plan->'afterNodes'->(p.plan->>'primary') state,nextval('truss.id_seq') id,clock_timestamp() created_at
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt ORDER BY p.operation_index),
 rows AS (
  SELECT operation_index,operation,jsonb_build_object('id',id,'type_id',(state->'image'->>'type_id')::int,
   'root_id',NULL,'root_type',NULL,'rev',(state->'image'->>'rev')::int,'ver',1,
   'props',state->'image'->'props','retained',nullif(state->'image'->'retained','{}'::jsonb),
   'created_at',created_at,'updated_at',created_at) image,
   (state->'identity')||jsonb_build_object('id',id::text) identity FROM allocated)
 SELECT jsonb_agg(jsonb_build_object('index',operation_index,'operation',operation,'object',image,'identity',identity) ORDER BY operation_index)
 INTO objects FROM rows;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(objects) o WHERE (o.value->'object'->>'id')::bigint<=0) THEN
  RAISE EXCEPTION 'positive native object ids required' USING ERRCODE='54000';END IF;
 -- One canonical object INSERT for the whole batch. Compare returned rows and
 -- the stored rows so BEFORE/AFTER triggers cannot silently change an image.
 SELECT jsonb_agg(value->'object' ORDER BY (value->'object'->>'id')::bigint) INTO expected FROM jsonb_array_elements(objects);
 WITH inserted AS (
  INSERT INTO truss.object SELECT r.* FROM jsonb_array_elements(objects) o
   CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object,o.value->'object') r
  RETURNING *) SELECT jsonb_agg(to_jsonb(inserted) ORDER BY id) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected OR expected IS DISTINCT FROM
  (SELECT jsonb_agg(to_jsonb(t) ORDER BY t.id) FROM truss.object t JOIN jsonb_array_elements(objects) o
   ON t.id=(o.value->'object'->>'id')::bigint AND t.type_id=(o.value->'object'->>'type_id')::int) THEN
  RAISE EXCEPTION 'exact batch object insert required' USING ERRCODE='55000';END IF;
 WITH cells AS MATERIALIZED (
  SELECT o.value object,k.key_num,k.prop_ids,decode(namespaces->>((o.value->'object'->>'type_id')||':'||k.key_num::text),'hex') namespace,
   truss.runtime_owned_key_tuple_in_metadata(k.type_id,k.key_num,
    (SELECT jsonb_agg(o.value->'object'->'props'->i.prop_id::text ORDER BY i.ordinal)
     FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ordinal)),
    coalesce(codecs->(k.type_id::text||':'||k.key_num::text),truss.runtime_owned_key_codec_metadata(k.type_id,k.key_num))) tuple
  FROM jsonb_array_elements(objects) o JOIN truss.key_def k ON k.type_id=(o.value->'object'->>'type_id')::int AND k.retired_rev IS NULL),
 encoded AS MATERIALIZED (
  SELECT *,convert_to('umf-key-tuple-v1:hex:'||encode(tuple,'hex'),'UTF8') transport,
   convert_to(jsonb_build_object('profile','truss-created-key-context/0.2','groupId',group_id::text,
    'sourceEpoch',installation.source_epoch::text,'xid',attempt.writer_xid::text,'actorOid',actor::text,
    'actor',session_user::text,'operationIndex',object->>'index','derivation','postgresql-umf-key-tuple-v1')::text,'UTF8') context
  FROM cells),
 rows AS (
  SELECT object->'index' index,jsonb_build_object('storage_row_id',nextval('truss.key_storage_row_seq'),
   'type_id',(object->'object'->>'type_id')::int,'key_num',key_num,'object_id',(object->'object'->>'id')::bigint,
   'namespace_bytes',namespace,'key_bytes',transport,'original_context_bytes',context,
   'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport)) membership,
   jsonb_build_object('storage_row_id',nextval('truss.key_storage_row_seq'),'namespace_bytes',namespace,'key_bytes',transport,
    'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport),
    'original_reservation_bytes',convert_to(jsonb_build_object('profile','truss-created-key-reservation/0.1',
     'groupId',group_id::text,'sourceEpoch',installation.source_epoch::text,'xid',attempt.writer_xid::text,
     'objectId',object->'object'->>'id','typeId',object->'object'->>'type_id','keyNumber',key_num::text,
     'contextBase64',replace(encode(context,'base64'),chr(10),''))::text,'UTF8')) reservation
  FROM encoded)
 SELECT coalesce(jsonb_agg(to_jsonb(rows) ORDER BY (index#>>'{}')::int,(membership->>'key_num')::int),'[]'::jsonb) INTO keys FROM rows;
 -- Capture already acquired these exact key routes in canonical order. Recheck
 -- every bucket after object triggers and before writing membership/reservation.
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(keys) e
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,e.value->'membership') r
  WHERE NOT EXISTS(SELECT 1 FROM truss.key_bucket_guard g WHERE g.namespace_sha256=r.namespace_sha256 AND g.key_sha256=r.key_sha256)
   OR EXISTS(SELECT 1 FROM truss.object_key_bucket b WHERE b.namespace_sha256=r.namespace_sha256 AND b.key_sha256=r.key_sha256 AND b.namespace_bytes=r.namespace_bytes AND b.key_bytes=r.key_bytes)
   OR EXISTS(SELECT 1 FROM truss.object_key_reservation_bucket b WHERE b.namespace_sha256=r.namespace_sha256 AND b.key_sha256=r.key_sha256 AND b.namespace_bytes=r.namespace_bytes AND b.key_bytes=r.key_bytes)) THEN
  RAISE EXCEPTION 'key already allocated or reserved' USING ERRCODE='23505';END IF;
 SELECT coalesce(jsonb_agg(value->'membership' ORDER BY (value->'membership'->>'storage_row_id')::bigint),'[]') INTO expected FROM jsonb_array_elements(keys);
 WITH inserted AS (
  INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
  SELECT r.storage_row_id,r.type_id,r.key_num,r.object_id,r.namespace_bytes,r.key_bytes,r.original_context_bytes
  FROM jsonb_array_elements(keys) o CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,o.value->'membership') r
  RETURNING *) SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch key membership required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(value->'reservation' ORDER BY (value->'reservation'->>'storage_row_id')::bigint),'[]') INTO expected FROM jsonb_array_elements(keys);
 WITH inserted AS (
  INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes)
  SELECT r.storage_row_id,r.namespace_bytes,r.key_bytes,r.original_reservation_bytes
  FROM jsonb_array_elements(keys) o CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_reservation_bucket,o.value->'reservation') r
  RETURNING *) SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch key reservation required' USING ERRCODE='55000';END IF;
 UPDATE truss.key_bucket_guard g SET generation=g.generation+r.advances
 FROM (SELECT k.namespace_sha256,k.key_sha256,count(*) advances FROM jsonb_array_elements(keys) o
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,o.value->'membership') k
  GROUP BY k.namespace_sha256,k.key_sha256) r WHERE g.namespace_sha256=r.namespace_sha256 AND g.key_sha256=r.key_sha256;
 WITH events AS MATERIALIZED (
  SELECT o.value object,nextval('truss.journal_seq') seq,clock_timestamp() at,
   truss.runtime_owned_history_record_in_metadata(o.value->'object',o.value->'identity',dictionary->(o.value->'object'->>'type_id')) image
  FROM jsonb_array_elements(objects) o),
 payloads AS MATERIALIZED (
  SELECT *,jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-create/0.1','xid',attempt.writer_xid::text,'seq',seq::text,'identity',object->'identity',
   'eventVersion','1','eventCatalogRevision',object->'object'->>'rev','operation','create','after',image,
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text)) event FROM events),
 grouped AS (
  SELECT *,event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0',
   'eventCount','1','orderedEventDigest',encode(sha256(convert_to(jsonb_build_array(event)::text,'UTF8')),'hex'))) payload FROM payloads)
 SELECT jsonb_agg(jsonb_build_object('index',object->'index','journal',jsonb_build_object('seq',seq,'at',at,'xid',attempt.writer_xid::text,
  'entity_kind','o','entity_id',(object->'object'->>'id')::bigint,'entity_type',(object->'object'->>'type_id')::int,
  'ver',1,'op','create','prop_id',NULL,'old_value',NULL,'rev',(object->'object'->>'rev')::int,
  'new_value',truss.runtime_exact_wrapper('event',convert_to(payload::text,'UTF8')),
  'origin',truss.runtime_exact_wrapper('origin',convert_to((payload->'origin')::text,'UTF8')))) ORDER BY seq) INTO journals FROM grouped;
 SELECT jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint) INTO expected FROM jsonb_array_elements(journals);
 WITH inserted AS (
  INSERT INTO truss.journal SELECT r.* FROM jsonb_array_elements(journals) o
   CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.journal,o.value->'journal') r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted) ORDER BY seq) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch journal append required' USING ERRCODE='55000';END IF;
 WITH key_sets AS MATERIALIZED (
  SELECT (value->>'index')::int index,jsonb_agg(value->'membership' ORDER BY (value->'membership'->>'key_num')::int) members
  FROM jsonb_array_elements(keys) GROUP BY (value->>'index')::int)
 SELECT jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(o.value->>'index')::int,
  'writer_xid',attempt.writer_xid::text,'object_id',(o.value->'object'->>'id')::bigint,'type_id',(o.value->'object'->>'type_id')::int,
  'before_object',NULL,'after_object',o.value->'object','after_keys',coalesce(k.members,'[]'::jsonb),
  'journal',jsonb_build_array(j.value->'journal')) ORDER BY (o.value->>'index')::int) INTO transitions
 FROM jsonb_array_elements(objects) o JOIN jsonb_array_elements(journals) j ON (j.value->>'index')::int=(o.value->>'index')::int
 LEFT JOIN key_sets k ON k.index=(o.value->>'index')::int;
 WITH inserted AS (
  INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
  SELECT r.attempt_id,r.operation_index,r.writer_xid,r.object_id,r.type_id,r.before_object,r.after_object,r.after_keys,r.journal
  FROM jsonb_populate_recordset(NULL::truss.runtime_object_transition,transitions) r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted)-'transition_id' ORDER BY operation_index) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM transitions THEN RAISE EXCEPTION 'exact batch transitions required' USING ERRCODE='55000';END IF;
 WITH slots AS (
  SELECT (o.value->>'index')::int index,jsonb_build_object('operation','create_object','outcome','created','identity',o.value->'identity','version','1',
   'events',jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-owned-create/0.1',
    'xid',attempt.writer_xid::text,'seq',j.value->'journal'->>'seq')))
   ||CASE WHEN (o.value->'operation') ? 'alias' THEN jsonb_build_object('alias',o.value->'operation'->>'alias') ELSE '{}'::jsonb END result
  FROM jsonb_array_elements(objects) o JOIN jsonb_array_elements(journals) j ON j.value->'index'=o.value->'index')
 SELECT jsonb_object_agg(index::text,result) INTO slot_results FROM slots;
 WITH updated AS (
  UPDATE truss.runtime_owned_operation p SET result=slot_results->p.operation_index::text
  WHERE p.attempt_id=selected_attempt AND p.result IS NULL AND slot_results ? p.operation_index::text
  RETURNING p.operation_index,p.result)
 SELECT count(*),coalesce(bool_or(result IS DISTINCT FROM slot_results->operation_index::text),false)
 INTO counted,slot_problem FROM updated;
 IF counted<>total OR slot_problem THEN RAISE EXCEPTION 'complete sealed batch result slots required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch progress advance required' USING ERRCODE='55000';END IF;
 -- Settlement retains current authority, result/effect custody and final native
 -- state. Canonical returned rows above already bind the immutable payloads.
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_create_batch(uuid) FROM PUBLIC;

-- The independent producer binds every canonical native INSERT and result
-- UPDATE before advancing progress. Journal, transition and reservation rows
-- are immutable; settlement checks custody, current authority and inventory
-- rather than producing their semantic payloads a second time.
CREATE FUNCTION truss.runtime_owned_create_batch_validate(attempt truss.runtime_object_attempt,input jsonb,history_dictionary jsonb,check_final boolean,actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE total int:=attempt.next_index;final_revision int;problem boolean;owner record;
BEGIN
 SELECT (plan->>'catalogRevision')::int INTO STRICT final_revision
 FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=total-1;
 IF total NOT BETWEEN 1 AND 1024 OR total<>jsonb_array_length(input->'operations')
  OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR final_revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>final_revision)
  OR (SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=attempt.id)<>total
  OR EXISTS(SELECT 1 FROM truss.runtime_edge_transition WHERE attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'complete original create effect inventory required' USING ERRCODE='55000';END IF;
 FOR owner IN SELECT DISTINCT t.type_id,t.document_id,t.module FROM truss.runtime_object_transition x JOIN truss.type_def t USING(type_id)
  WHERE x.attempt_id=attempt.id LOOP
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,actor);
  IF NOT truss.runtime_object_values_readable_qualified(owner.type_id,actor) THEN
   RAISE EXCEPTION 'current original property readers required' USING ERRCODE='42501';END IF;
 END LOOP;
 WITH frames AS MATERIALIZED (
  SELECT p.operation_index,q.profile,q."operationIndex" plan_index,q."mutationProfile" mutation_profile,
   q.operation,q."actorName" actor_name,q."primary" primary_node,q."afterNodes"->q."primary" state
  FROM truss.runtime_owned_operation p
  CROSS JOIN LATERAL jsonb_to_record(p.plan) q(profile text,"operationIndex" jsonb,"mutationProfile" jsonb,
   operation jsonb,"actorName" text,"primary" text,"afterNodes" jsonb)
  WHERE p.attempt_id=attempt.id)
 SELECT EXISTS(SELECT 1 FROM frames f LEFT JOIN LATERAL (
  SELECT t.* FROM truss.runtime_object_transition t
  WHERE t.attempt_id=attempt.id AND t.operation_index=f.operation_index OFFSET 0) t ON true WHERE
  t.transition_id IS NULL OR t.writer_xid IS DISTINCT FROM attempt.writer_xid
  OR f.profile IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
  OR f.plan_index IS DISTINCT FROM to_jsonb(f.operation_index)
  OR f.mutation_profile IS DISTINCT FROM input->'mutationProfile'
  OR f.operation IS DISTINCT FROM input->'operations'->f.operation_index
  OR f.actor_name IS DISTINCT FROM session_user::text
  OR f.operation->>'operation' IS DISTINCT FROM 'create_object'
  OR f.operation->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb
  OR f.primary_node IS DISTINCT FROM 'create:'||f.operation_index::text
  OR f.state IS NULL OR f.state->'root' IS DISTINCT FROM 'null'::jsonb
  OR f.state->'deleted' IS DISTINCT FROM 'false'::jsonb
  OR t.before_object IS NOT NULL OR t.after_object IS NULL
  OR t.object_id<=0 OR t.type_id IS DISTINCT FROM (f.state->'image'->>'type_id')::int
  OR jsonb_array_length(t.journal)<>1) INTO problem;
 IF problem THEN RAISE EXCEPTION 'original batch create source and transition inventory required' USING ERRCODE='55000';END IF;
 -- Canonical reservation INSERT RETURNING was compared before sealing the
 -- immutable transition. Rewalking all historical reservations adds no proof.
 -- Final native object/key images are checked by object_group_finish. Keep the
 -- incident-edge cut here: an independent create has no authored edge effects.
 IF check_final AND EXISTS(SELECT 1 FROM truss.runtime_object_transition t JOIN truss.edge e
  ON (e.source_id=t.object_id AND e.source_type=t.type_id) OR (e.target_id=t.object_id AND e.target_type=t.type_id)
  WHERE t.attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'complete final incident edge inventory required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_create_batch_validate(truss.runtime_object_attempt,jsonb,jsonb,boolean,oid) FROM PUBLIC;
