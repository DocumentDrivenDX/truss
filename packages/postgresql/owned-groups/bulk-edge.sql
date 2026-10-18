-- Independent edges between stored endpoints do not read earlier operations.
-- Keep ownership-changing/alias/mixed groups on the ordered graph path.
CREATE FUNCTION truss.runtime_owned_edge_create_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;last_plan jsonb;edges jsonb;journals jsonb;transitions jsonb;expected jsonb;actual jsonb;
 endpoints jsonb;contexts jsonb;actor oid;total int;counted int;revision int;owner record;
 slot_results jsonb;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;total:=jsonb_array_length(input->'operations');
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.complete OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR total NOT BETWEEN 1 AND 1024 OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_edge'
    OR o.value->'source'->>'state' IS DISTINCT FROM 'stored' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored')
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total THEN
  RAISE EXCEPTION 'independent original edge create batch required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 SELECT plan INTO STRICT last_plan FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt AND operation_index=total-1;
 FOR owner IN SELECT DISTINCT r.* FROM truss.runtime_owned_operation p JOIN truss.rel_def r
  ON r.rel_type_id=(p.plan->'afterEdges'->(p.plan->>'primary')->'identity'->>'typeId')::int
  WHERE p.attempt_id=selected_attempt LOOP
  IF owner.lifecycle<>'independent' OR NOT owner.directed OR owner.composition OR owner.assoc_type_id IS NOT NULL OR owner.retired_rev IS NOT NULL THEN
   RAISE EXCEPTION 'selected independent relationship required' USING ERRCODE='0A000';END IF;
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,actor);
 END LOOP;
 -- Resolve each distinct stored endpoint/root context once before edge writes.
 WITH endpoint_refs AS MATERIALIZED (
  SELECT p.plan->'afterEdges'->(p.plan->>'primary')->>'source' reference FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt
  UNION SELECT p.plan->'afterEdges'->(p.plan->>'primary')->>'target' FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt)
 SELECT jsonb_object_agg(reference,truss.runtime_owned_identity(selected_attempt,total-1,reference,'object',last_plan,attempt)) INTO endpoints FROM endpoint_refs;
 SELECT jsonb_object_agg(key,truss.runtime_endpoint_ownership(value,revision)) INTO contexts FROM jsonb_each(endpoints);
 IF EXISTS(SELECT 1 FROM jsonb_each(endpoints) e LEFT JOIN truss.object o
  ON o.id=(e.value->>'id')::bigint AND o.type_id=(e.value->>'typeId')::int
  WHERE to_jsonb(o)-ARRAY['created_at','updated_at'] IS DISTINCT FROM
   truss.runtime_owned_object_image(selected_attempt,total-1,e.key,'before',last_plan,attempt)) THEN
  RAISE EXCEPTION 'original batch endpoint prestate required' USING ERRCODE='55000';END IF;
 WITH planned AS MATERIALIZED (
  SELECT p.operation_index,p.plan->'operation' operation,p.plan->'afterEdges'->(p.plan->>'primary') state,
   nextval('truss.id_seq') id,clock_timestamp() created_at FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=selected_attempt ORDER BY p.operation_index),
 images AS (
  SELECT *,state->'image'||jsonb_build_object('id',id,
   'source_id',(endpoints->(state->>'source')->>'id')::bigint,'source_type',(endpoints->(state->>'source')->>'typeId')::int,
   'target_id',(endpoints->(state->>'target')->>'id')::bigint,'target_type',(endpoints->(state->>'target')->>'typeId')::int,
   'order_key',state->'orderKey'->>'text','created_at',created_at,'updated_at',created_at) image,
   state->'identity'||jsonb_build_object('id',id::text) identity FROM planned)
 SELECT jsonb_agg(jsonb_build_object('index',operation_index,'operation',operation,'edge',image,'identity',identity,
  'source',endpoints->(state->>'source'),'target',endpoints->(state->>'target'),
  'endpointOwnership',jsonb_build_object('profile','truss-edge-endpoint-ownership/0.1','captureCatalogRevision',revision::text,
   'before',NULL,'after',jsonb_build_object('source',contexts->(state->>'source'),'target',contexts->(state->>'target'))))
  ORDER BY operation_index) INTO edges FROM images;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(edges) e WHERE (e.value->'edge'->>'id')::bigint<=0) THEN
  RAISE EXCEPTION 'positive native edge ids required' USING ERRCODE='54000';END IF;
 PERFORM truss.runtime_lock_edge_business_key(routes.k) FROM (
  SELECT truss.runtime_edge_business_key((value->'edge'->>'rel_type_id')::int,value->'source',value->'target') k
  FROM jsonb_array_elements(edges)) routes ORDER BY routes.k COLLATE "C";
 SELECT jsonb_agg(value->'edge' ORDER BY (value->'edge'->>'id')::bigint) INTO expected FROM jsonb_array_elements(edges);
 WITH inserted AS (INSERT INTO truss.edge SELECT r.* FROM jsonb_array_elements(edges) e
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.edge,e.value->'edge') r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted) ORDER BY id) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected OR expected IS DISTINCT FROM
  (SELECT jsonb_agg(to_jsonb(t) ORDER BY t.id) FROM truss.edge t JOIN jsonb_array_elements(edges) e ON t.id=(e.value->'edge'->>'id')::bigint) THEN
  RAISE EXCEPTION 'exact batch edge insert required' USING ERRCODE='55000';END IF;
 WITH allocated AS MATERIALIZED (
  SELECT value edge,nextval('truss.journal_seq') seq,clock_timestamp() at FROM jsonb_array_elements(edges)),
 events AS MATERIALIZED (
  SELECT *,jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-edge-mutation/0.1','xid',attempt.writer_xid::text,'seq',seq::text,'identity',edge->'identity',
   'eventVersion','1','eventCatalogRevision',revision::text,'operation','create',
   'after',truss.runtime_edge_history(edge->'edge',edge->'identity',edge->'source',edge->'target'),
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text)) event FROM allocated),
 grouped AS (
  SELECT *,event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount','1',
   'orderedEventDigest',encode(sha256(convert_to(jsonb_build_array(event)::text,'UTF8')),'hex'))) payload FROM events)
 SELECT jsonb_agg(jsonb_build_object('index',edge->'index','journal',jsonb_build_object('seq',seq,'at',at,'xid',attempt.writer_xid::text,
  'entity_kind','e','entity_id',(edge->'edge'->>'id')::bigint,'entity_type',(edge->'edge'->>'rel_type_id')::int,
  'ver',1,'op','create','prop_id',NULL,'old_value',NULL,'rev',revision,
  'new_value',truss.runtime_exact_wrapper('event',convert_to(payload::text,'UTF8')),
  'origin',truss.runtime_exact_wrapper('origin',convert_to((payload->'origin')::text,'UTF8')))) ORDER BY seq) INTO journals FROM grouped;
 SELECT jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint) INTO expected FROM jsonb_array_elements(journals);
 WITH inserted AS (INSERT INTO truss.journal SELECT r.* FROM jsonb_array_elements(journals) e
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.journal,e.value->'journal') r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted) ORDER BY seq) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch edge journal append required' USING ERRCODE='55000';END IF;
 SELECT jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(e.value->>'index')::int,'writer_xid',attempt.writer_xid::text,
  'edge_id',(e.value->'edge'->>'id')::bigint,'rel_type_id',(e.value->'edge'->>'rel_type_id')::int,'before_edge',NULL,'after_edge',e.value->'edge',
  'journal',jsonb_build_array(j.value->'journal'),'old_source',NULL,'old_target',NULL,
  'source_identity',e.value->'source','target_identity',e.value->'target','endpoint_ownership',e.value->'endpointOwnership')
  ORDER BY (e.value->>'index')::int) INTO transitions
 FROM jsonb_array_elements(edges) e JOIN jsonb_array_elements(journals) j ON (j.value->>'index')::int=(e.value->>'index')::int;
 WITH inserted AS (
  INSERT INTO truss.runtime_edge_transition(attempt_id,operation_index,writer_xid,edge_id,rel_type_id,before_edge,after_edge,journal,old_source,old_target,source_identity,target_identity,endpoint_ownership)
  SELECT r.attempt_id,r.operation_index,r.writer_xid,r.edge_id,r.rel_type_id,r.before_edge,r.after_edge,r.journal,r.old_source,r.old_target,r.source_identity,r.target_identity,r.endpoint_ownership
  FROM jsonb_populate_recordset(NULL::truss.runtime_edge_transition,transitions) r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted)-'transition_id' ORDER BY operation_index) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM transitions THEN RAISE EXCEPTION 'exact batch edge transitions required' USING ERRCODE='55000';END IF;
 WITH slots AS (
  SELECT (e.value->>'index')::int index,jsonb_build_object('operation','create_edge','outcome','created','identity',e.value->'identity','version','1',
   'events',jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-owned-edge-mutation/0.1',
    'xid',attempt.writer_xid::text,'seq',j.value->'journal'->>'seq')))
   ||CASE WHEN (e.value->'operation') ? 'alias' THEN jsonb_build_object('alias',e.value->'operation'->>'alias') ELSE '{}'::jsonb END result
  FROM jsonb_array_elements(edges) e JOIN jsonb_array_elements(journals) j ON (j.value->>'index')::int=(e.value->>'index')::int)
 SELECT jsonb_object_agg(index::text,result) INTO slot_results FROM slots;
 WITH updated AS (
  UPDATE truss.runtime_owned_operation p SET result=slot_results->p.operation_index::text
  WHERE p.attempt_id=selected_attempt AND p.result IS NULL AND slot_results ? p.operation_index::text
  RETURNING p.operation_index,p.result)
 SELECT count(*) INTO counted FROM updated;
 IF counted<>total THEN RAISE EXCEPTION 'complete sealed edge batch results required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch edge progress advance required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_create_batch(uuid) FROM PUBLIC;
