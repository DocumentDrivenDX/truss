-- Close the original plan against every actual effect. The final image check is
-- performed at group finish; commit rechecks custody and authority after later
-- groups may legitimately have superseded those images in the same transaction.
CREATE FUNCTION truss.runtime_owned_group_validate(selected_attempt uuid,check_final boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;plan jsonb;last_plan jsonb;initial_scope jsonb;
 operations jsonb;before_nodes jsonb;after_nodes jsonb;before_edges jsonb;after_edges jsonb;
 operation jsonb;result jsonb;entry record;owner record;transition_id bigint;identity jsonb;actual jsonb;
 reference text;mode text;expected_objects int;expected_edges int;events jsonb;deleted jsonb;aliases jsonb:='[]';
 primary_before jsonb;primary_after jsonb;expected_outcome text;expected_version text;
 node_order text[];projection jsonb;local_owned jsonb;root_reference text;index int;current_actor oid;live_edges jsonb;final_nodes jsonb;final_edges jsonb;final_problem text;
 history_dictionary jsonb:='{}';historical_basis jsonb;historical_revision int;history_group record;history_basis jsonb;
 history_property truss.prop_def%ROWTYPE;history_pin record;history_pins jsonb;history_order jsonb;history_key text;history_type_pin text;sealed record;
 independent_updates boolean;independent_endpoints boolean;independent_edge_creates boolean;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 operations:=input->'operations';
 IF attempt.context ? 'originalAssertedOrigin' AND attempt.context->'originalAssertedOrigin' IS DISTINCT FROM input->'assertedOrigin' THEN
  RAISE EXCEPTION 'original asserted origin projection required' USING ERRCODE='55000';END IF;
 current_actor:=truss.runtime_person(false);
 IF check_final IS NULL OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
  OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR attempt.next_index<>jsonb_array_length(operations) OR jsonb_array_length(attempt.results)<>attempt.next_index
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>attempt.next_index THEN
  RAISE EXCEPTION 'complete original owned group required' USING ERRCODE='55000';END IF;
 -- Both finish and mandatory commit close the retained arrays against every
 -- immutable result slot, including no-ops and aggregate cascade results.
 SELECT coalesce(jsonb_agg(p.result ORDER BY p.operation_index),'[]'::jsonb) results,
  coalesce(jsonb_agg(jsonb_build_object('alias',p.plan->'operation'->>'alias','identity',p.result->'identity') ORDER BY p.operation_index)
   FILTER(WHERE (p.plan->'operation') ? 'alias'),'[]'::jsonb) aliases,
  array_agg(p.operation_index ORDER BY p.operation_index) ordinals,
  count(*) FILTER(WHERE p.result IS NULL) missing,bool_and(p.writer_xid=attempt.writer_xid) writer_matches
 INTO sealed FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt;
 IF sealed.missing<>0 OR sealed.writer_matches IS DISTINCT FROM true
  OR sealed.ordinals IS DISTINCT FROM ARRAY(SELECT generate_series(0,attempt.next_index-1))
  OR sealed.results IS DISTINCT FROM attempt.results OR sealed.aliases IS DISTINCT FROM attempt.aliases THEN
  RAISE EXCEPTION 'exact complete retained owned result slots required' USING ERRCODE='55000';END IF;
 -- Compile source metadata for created and changed object images. Each
 -- independent settlement invocation resolves its own historical source cut.
 FOR history_group IN
  WITH frames AS MATERIALIZED (
   SELECT o.plan->'beforeNodes' before_nodes,o.plan->'afterNodes' after_nodes
   FROM truss.runtime_owned_operation o WHERE o.attempt_id=selected_attempt),
  changes AS MATERIALIZED (
   SELECT f.before_nodes->n.key before_state,n.value after_state
   FROM frames f CROSS JOIN LATERAL jsonb_each(f.after_nodes) n
   WHERE f.before_nodes->n.key IS NULL OR (f.before_nodes->n.key->'deleted'='false'::jsonb
    AND n.value IS DISTINCT FROM f.before_nodes->n.key)),
  images AS MATERIALIZED (
   SELECT member.state->'image' image FROM changes c
   CROSS JOIN LATERAL (VALUES(c.before_state),(c.after_state)) member(state)
   WHERE member.state->'deleted'='false'::jsonb)
  SELECT (image->>'rev')::int revision,(image->>'type_id')::int type_id,
   coalesce(array_agg(DISTINCT property_names.name) FILTER(WHERE property_names.name IS NOT NULL),'{}'::text[]) present_names
  FROM images LEFT JOIN LATERAL jsonb_object_keys(image->'props') property_names(name) ON true
  GROUP BY (image->>'rev')::int,(image->>'type_id')::int
  ORDER BY (image->>'rev')::int,(image->>'type_id')::int
 LOOP
  SELECT metadata INTO STRICT history_basis FROM truss.runtime_type_schema
   WHERE rev=history_group.revision AND type_id=history_group.type_id;
  IF EXISTS(SELECT 1 FROM jsonb_each(history_basis->'propertyAccess') p
   WHERE p.key=ANY(history_group.present_names) AND p.value->'itemsValid' IS DISTINCT FROM 'true'::jsonb) THEN
   RAISE EXCEPTION 'current historical property and item readers required' USING ERRCODE='42501';END IF;
  FOR owner IN SELECT DISTINCT r.value->>'documentId' document_id,r.value->>'moduleId' module
   FROM jsonb_each(history_basis->'propertyAccess') p
   CROSS JOIN LATERAL jsonb_array_elements(p.value->'readers') r WHERE p.key=ANY(history_group.present_names) LOOP
   IF truss.runtime_can_read_qualified(owner.document_id,owner.module,current_actor) IS NOT TRUE THEN
    RAISE EXCEPTION 'current historical property and item readers required' USING ERRCODE='42501';END IF;
  END LOOP;
  history_key:=jsonb_build_array(history_group.revision,history_group.type_id)::text;
  history_dictionary:=history_dictionary||jsonb_build_object(history_key,history_basis-ARRAY['propertyAccess']);
 END LOOP;
 -- The closed independent-create shape has a set-based reconstruction.
 -- Mixed/owned operations keep the general ordered graph validator.
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
  WHERE o.value->>'operation' IS DISTINCT FROM 'create_object'
   OR o.value->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb) THEN
  PERFORM truss.runtime_owned_create_batch_validate(attempt,input,history_dictionary,check_final,current_actor);
  RETURN;
 END IF;
 independent_updates:=NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
  WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange')
  AND (SELECT count(DISTINCT p.plan->>'primary') FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt)=attempt.next_index
  AND EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=0
   AND (p.plan->>'catalogRevision')::int=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>(p.plan->>'catalogRevision')::int))
  AND NOT EXISTS(SELECT 1 FROM truss.runtime_owned_operation p CROSS JOIN LATERAL jsonb_each(p.plan->'initialScope'->'nodes') n
   WHERE p.attempt_id=selected_attempt AND p.operation_index=0 AND
    (n.value->'root_id' IS DISTINCT FROM 'null'::jsonb OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb));
 SELECT p.plan->'initialScope' INTO STRICT initial_scope FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=selected_attempt AND p.operation_index=0;
 independent_edge_creates:=initial_scope->'independentEndpointScope'='true'::jsonb
  AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_edge'
    OR o.value->'source'->>'state' IS DISTINCT FROM 'stored' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored')
  AND NOT EXISTS(SELECT 1 FROM truss.rel_def WHERE retired_rev IS NULL AND lifecycle='owned')
  AND NOT EXISTS(SELECT 1 FROM jsonb_each(initial_scope->'nodes') n
   WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb);
 IF independent_updates THEN
  PERFORM truss.runtime_owned_update_batch_validate(attempt,input,history_dictionary,current_actor);
  SELECT p.plan->'initialScope' INTO STRICT initial_scope FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=0;
  SELECT p.plan INTO STRICT last_plan FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=attempt.next_index-1;
  IF initial_scope->'independentEndpointScope'='true'::jsonb THEN
   SELECT last_plan||jsonb_build_object('afterNodes',jsonb_object_agg(p.plan->>'primary',p.plan->'afterNodes'->(p.plan->>'primary')))
    INTO last_plan FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt;
  END IF;
 ELSIF independent_edge_creates THEN
  SELECT p.plan INTO STRICT last_plan FROM truss.runtime_owned_operation p
   WHERE p.attempt_id=selected_attempt AND p.operation_index=attempt.next_index-1;
  IF (last_plan->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
   OR EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>(last_plan->>'catalogRevision')::int)
   OR (SELECT count(*) FROM truss.runtime_edge_transition WHERE attempt_id=selected_attempt)<>attempt.next_index
   OR EXISTS(SELECT 1 FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt) THEN
   RAISE EXCEPTION 'complete original edge batch effect inventory required' USING ERRCODE='55000';END IF;
  -- The trusted batch producer already checked the actual edge, journal and
  -- transition INSERTs. Settlement closes source/result/effect slots and keeps
  -- current authority and final physical images below; it does not execute the
  -- entire edge semantic/history program a second time for every operation.
  IF EXISTS(
   SELECT 1 FROM truss.runtime_owned_operation p
   LEFT JOIN truss.runtime_edge_transition t ON t.attempt_id=p.attempt_id AND t.operation_index=p.operation_index
   WHERE p.attempt_id=selected_attempt AND (
    p.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
    OR p.plan->'operationIndex' IS DISTINCT FROM to_jsonb(p.operation_index)
    OR p.plan->'operation' IS DISTINCT FROM operations->p.operation_index
    OR p.plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
    OR p.plan->>'actorName' IS DISTINCT FROM session_user::text
    OR p.plan->>'primary' IS DISTINCT FROM 'create:'||p.operation_index::text
    OR t.transition_id IS NULL OR t.writer_xid IS DISTINCT FROM attempt.writer_xid
    OR t.before_edge IS NOT NULL OR t.after_edge IS NULL
    OR p.result->>'operation' IS DISTINCT FROM 'create_edge' OR p.result->>'outcome' IS DISTINCT FROM 'created'
    OR p.result->>'version' IS DISTINCT FROM '1'
    OR p.result->'identity'->>'id' IS DISTINCT FROM t.edge_id::text
    OR p.result->'identity'->>'typeId' IS DISTINCT FROM t.rel_type_id::text
    OR (p.result->'identity')-'id' IS DISTINCT FROM
     (p.plan->'afterEdges'->(p.plan->>'primary')->'identity')-'id'
    OR t.source_identity IS DISTINCT FROM p.plan->'operation'->'source'->'identity'
    OR t.target_identity IS DISTINCT FROM p.plan->'operation'->'target'->'identity'
    OR jsonb_array_length(t.journal) IS DISTINCT FROM 1
    OR jsonb_array_length(p.result->'events') IS DISTINCT FROM 1
    OR p.result->'events'->0->>'seq' IS DISTINCT FROM t.journal->0->>'seq'
    OR p.result->'events'->0->>'xid' IS DISTINCT FROM attempt.writer_xid::text)) THEN
   RAISE EXCEPTION 'original edge batch source result and transition correspondence required' USING ERRCODE='55000';END IF;
  -- Lean endpoint scopes do not carry a relationship inventory. Recheck each
  -- actual relationship writer explicitly, including mandatory commit closure.
  FOR owner IN SELECT DISTINCT r.document_id,r.module FROM truss.runtime_edge_transition t
   JOIN truss.rel_def r ON r.rel_type_id=t.rel_type_id WHERE t.attempt_id=selected_attempt LOOP
   PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,current_actor);
  END LOOP;
 ELSE
 FOR index IN 0..attempt.next_index-1 LOOP
  plan:=truss.runtime_owned_plan(selected_attempt,index);operation:=plan->'operation';
  IF operation IS DISTINCT FROM jsonb_extract_path(operations,index::text)
   OR plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile' THEN
   RAISE EXCEPTION 'original owned operation source correspondence required' USING ERRCODE='55000';END IF;
  before_nodes:=plan->'beforeNodes';after_nodes:=plan->'afterNodes';
  before_edges:=plan->'beforeEdges';after_edges:=plan->'afterEdges';
  mode:=operation->>'operation';result:=attempt.results->index;
  IF index=0 THEN initial_scope:=plan->'initialScope';END IF;
  expected_objects:=0;expected_edges:=0;
  FOR entry IN SELECT key,value FROM jsonb_each(after_nodes) n WHERE n.value IS DISTINCT FROM jsonb_extract_path(before_nodes,n.key)
   AND (jsonb_extract_path(before_nodes,n.key) IS NULL OR jsonb_extract_path(before_nodes,n.key)->'deleted'='false'::jsonb) LOOP
   identity:=truss.runtime_owned_identity(selected_attempt,index,entry.key,'object',plan,attempt);
   SELECT t.transition_id INTO STRICT transition_id FROM truss.runtime_object_transition t WHERE t.attempt_id=selected_attempt
    AND t.operation_index=index AND t.object_id=(identity->>'id')::bigint AND t.type_id=(identity->>'typeId')::int;
   PERFORM truss.runtime_owned_object_transition_validate_qualified(transition_id,false,current_actor,input,attempt.input_bytes,attempt,history_dictionary);expected_objects:=expected_objects+1;
  END LOOP;
  FOR entry IN SELECT key,value FROM jsonb_each(after_edges) e WHERE
   (e.value IS DISTINCT FROM jsonb_extract_path(before_edges,e.key) OR e.key=plan->>'primary' AND mode='update_edge')
   AND (jsonb_extract_path(before_edges,e.key) IS NULL OR jsonb_extract_path(before_edges,e.key)->'deleted'='false'::jsonb) LOOP
   identity:=truss.runtime_owned_identity(selected_attempt,index,entry.key,'edge',plan,attempt);
   SELECT t.transition_id INTO STRICT transition_id FROM truss.runtime_edge_transition t WHERE t.attempt_id=selected_attempt
    AND t.operation_index=index AND t.edge_id=(identity->>'id')::bigint AND t.rel_type_id=(identity->>'typeId')::int;
   PERFORM truss.runtime_owned_edge_transition_validate_qualified(transition_id,false,current_actor,input,attempt.input_bytes,attempt);expected_edges:=expected_edges+1;
  END LOOP;
  IF expected_objects<>(SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt AND operation_index=index)
   OR expected_edges<>(SELECT count(*) FROM truss.runtime_edge_transition WHERE attempt_id=selected_attempt AND operation_index=index) THEN
   RAISE EXCEPTION 'complete original effect inventory required' USING ERRCODE='55000';END IF;
  identity:=truss.runtime_owned_identity(selected_attempt,index,plan->>'primary',CASE WHEN mode LIKE '%object' THEN 'object' ELSE 'edge' END,plan,attempt);
  IF result->'identity' IS DISTINCT FROM identity OR result->>'operation' IS DISTINCT FROM mode THEN
   RAISE EXCEPTION 'original primary result identity required' USING ERRCODE='55000';END IF;
  primary_before:=jsonb_extract_path(plan,CASE WHEN mode LIKE '%object' THEN 'beforeNodes' ELSE 'beforeEdges' END,plan->>'primary');
  primary_after:=jsonb_extract_path(plan,CASE WHEN mode LIKE '%object' THEN 'afterNodes' ELSE 'afterEdges' END,plan->>'primary');
  expected_outcome:=CASE WHEN mode LIKE 'create_%' THEN 'created' WHEN mode LIKE 'delete_%' THEN 'deleted'
   WHEN primary_before IS NOT DISTINCT FROM primary_after THEN 'unchanged' ELSE 'changed' END;
  expected_version:=CASE WHEN mode LIKE 'delete_%' THEN ((primary_before->'image'->>'ver')::bigint+1)::text ELSE primary_after->'image'->>'ver' END;
  IF result->>'outcome' IS DISTINCT FROM expected_outcome
   OR result->>(CASE WHEN mode LIKE 'delete_%' THEN 'deletionVersion' ELSE 'version' END) IS DISTINCT FROM expected_version THEN
   RAISE EXCEPTION 'original primary outcome and version required' USING ERRCODE='55000';END IF;
  IF mode LIKE 'delete_%' THEN
   SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]'::jsonb) INTO deleted FROM (
    SELECT jsonb_build_object('identity',truss.runtime_owned_identity(selected_attempt,index,p.key,'object',plan,attempt),
     'deletionVersion',((p.value->'image'->>'ver')::bigint+1)::text) v
    FROM jsonb_each(before_nodes) p WHERE p.value->'deleted'='false'::jsonb AND jsonb_extract_path(after_nodes,p.key)->'deleted'='true'::jsonb
    UNION ALL SELECT jsonb_build_object('identity',truss.runtime_owned_identity(selected_attempt,index,p.key,'edge',plan,attempt),
     'deletionVersion',((p.value->'image'->>'ver')::bigint+1)::text)
    FROM jsonb_each(before_edges) p WHERE p.value->'deleted'='false'::jsonb AND plan->'afterEdges'->p.key->'deleted'='true'::jsonb) members;
   IF deleted IS DISTINCT FROM (SELECT jsonb_agg(value ORDER BY value::text COLLATE "C") FROM jsonb_array_elements(result->'deleted')) THEN
    RAISE EXCEPTION 'complete original deleted identity inventory required' USING ERRCODE='55000';END IF;
  END IF;
  PERFORM truss.runtime_module_writer_qualified(identity->'owner'->>'documentId',identity->'owner'->>'moduleId',current_actor);
  IF mode<>'create_object' THEN
   SELECT coalesce(jsonb_agg(jsonb_build_object('sourceEpoch',event->>'sourceEpoch','historyProfile',event->>'historyProfile',
    'xid',event->>'xid','seq',event->>'seq') ORDER BY (event->>'seq')::bigint),'[]'::jsonb) INTO events FROM (
    SELECT convert_from(decode(j.value->'new_value'->>'bytesBase64','base64'),'UTF8')::jsonb event
    FROM (SELECT journal FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt AND operation_index=index
     UNION ALL SELECT journal FROM truss.runtime_edge_transition WHERE attempt_id=selected_attempt AND operation_index=index) t
    CROSS JOIN LATERAL jsonb_array_elements(t.journal) j) all_events;
   IF result->'events' IS DISTINCT FROM events THEN RAISE EXCEPTION 'complete original public event references required' USING ERRCODE='55000';END IF;
  END IF;
  IF operation ? 'alias' THEN aliases:=aliases||jsonb_build_array(jsonb_build_object('alias',operation->>'alias','identity',identity));END IF;
  last_plan:=plan;
 END LOOP;
 IF aliases IS DISTINCT FROM attempt.aliases THEN RAISE EXCEPTION 'original create aliases required' USING ERRCODE='55000';END IF;
 END IF;
 -- Recheck all discovered component writers and outside endpoint readers even
 -- when the original operation was unchanged or the affected member was deleted.
 FOR owner IN SELECT DISTINCT value->>'document_id' document_id,value->>'module' module_id FROM (
  SELECT value FROM jsonb_each(initial_scope->'types') UNION ALL SELECT value FROM jsonb_each(initial_scope->'relationships')) owners LOOP
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module_id,current_actor);
 END LOOP;
 FOR entry IN SELECT value FROM jsonb_each(initial_scope->'boundary') LOOP
  IF NOT truss.runtime_can_read_qualified(entry.value->'definition'->>'document_id',entry.value->'definition'->>'module',current_actor) THEN
   RAISE EXCEPTION 'current original boundary reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 FOR entry IN SELECT DISTINCT (value->'identity'->>'typeId')::int type_id FROM jsonb_each(last_plan->'afterNodes') LOOP
  IF NOT truss.runtime_object_values_readable_qualified(entry.type_id,current_actor) THEN RAISE EXCEPTION 'current complete object value readers required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF NOT check_final THEN RETURN;END IF;
 -- Resolve each final member once. The private projection carries its exact
 -- checked state; genuine create identities still check the original result and
 -- creation-index plan independently inside runtime_owned_identity.
 WITH resolved AS MATERIALIZED (
  SELECT n.reference,n.ordinal,CASE WHEN n.reference='stored:'||(n.state->'identity'->>'typeId')||':'||(n.state->'identity'->>'id')
   THEN n.state->'identity' ELSE truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,n.reference,'object',
   jsonb_build_object('catalogRevision',last_plan->'catalogRevision','afterNodes',jsonb_build_object(n.reference,n.state)),attempt) END identity
  FROM jsonb_each(last_plan->'afterNodes') WITH ORDINALITY n(reference,state,ordinal))
 SELECT coalesce(jsonb_object_agg(resolved.reference,resolved.identity ORDER BY resolved.ordinal),'{}'::jsonb) INTO final_nodes FROM resolved;
 IF independent_edge_creates THEN
  SELECT jsonb_object_agg('create:'||p.operation_index::text,p.result->'identity') INTO final_edges
   FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt;
 ELSE
 WITH resolved AS MATERIALIZED (
  SELECT e.reference,e.ordinal,CASE WHEN e.reference='stored:'||(e.state->'identity'->>'typeId')||':'||(e.state->'identity'->>'id')
   THEN e.state->'identity' ELSE truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,e.reference,'edge',
   jsonb_build_object('catalogRevision',last_plan->'catalogRevision','afterEdges',jsonb_build_object(e.reference,e.state)),attempt) END identity
  FROM jsonb_each(last_plan->'afterEdges') WITH ORDINALITY e(reference,state,ordinal))
 SELECT coalesce(jsonb_object_agg(resolved.reference,resolved.identity ORDER BY resolved.ordinal),'{}'::jsonb) INTO final_edges FROM resolved;
 END IF;
 SELECT coalesce(jsonb_object_agg(jsonb_build_array(e.value->>'typeId',e.value->>'id')::text,true),'{}'::jsonb)
  INTO live_edges FROM jsonb_each(final_edges) e WHERE jsonb_extract_path(last_plan,'afterEdges',e.key,'deleted')='false'::jsonb;
 -- A lean endpoint scope intentionally omits unrelated independent edges.
 -- Recheck its closed operation shape and ownership conditions independently.
 independent_endpoints:=initial_scope->'independentEndpointScope'='true'::jsonb
  AND NOT EXISTS(SELECT 1 FROM truss.rel_def WHERE retired_rev IS NULL AND lifecycle='owned')
  AND (NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_edge'
    OR o.value->'source'->>'state' IS DISTINCT FROM 'stored' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored')
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
    WHERE o.value->>'operation' IS DISTINCT FROM 'update_object'
     OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange'))
  AND NOT EXISTS(SELECT 1 FROM jsonb_each(initial_scope->'nodes') n
   WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb);
 -- Preserve node order and image-before-incident refusal priority. Deleted
 -- members remain in the identity and incident inventories with a NULL image.
 WITH members AS MATERIALIZED (
  SELECT n.reference,n.state,n.ordinal,final_nodes->n.reference identity,
   CASE WHEN n.state->'deleted' IS DISTINCT FROM 'true'::jsonb AND n.state->>'root' IS NOT NULL
    THEN coalesce(final_nodes->(n.state->>'root'),
     truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,n.state->>'root','object',last_plan,attempt)) END root_identity
  FROM jsonb_each(last_plan->'afterNodes') WITH ORDINALITY n(reference,state,ordinal)),
 problems AS MATERIALIZED (
  SELECT n.ordinal,CASE WHEN (to_jsonb(o)-ARRAY['created_at','updated_at']) IS DISTINCT FROM
   CASE WHEN n.state->'deleted'='true'::jsonb THEN NULL ELSE
    ((n.state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(n.identity->>'id')::bigint,
     'root_id',(n.root_identity->>'id')::bigint,'root_type',(n.root_identity->>'typeId')::int) END THEN 'object'
   WHEN (EXISTS(SELECT 1 FROM truss.edge e WHERE
    e.source_id=(n.identity->>'id')::bigint AND e.source_type=(n.identity->>'typeId')::int
    AND NOT (live_edges ? jsonb_build_array(e.rel_type_id::text,e.id::text)::text)
    AND (NOT coalesce(independent_endpoints,false) OR to_jsonb(e) IS DISTINCT FROM
     (SELECT t.after_edge FROM truss.runtime_edge_transition t WHERE t.edge_id=e.id AND t.rel_type_id=e.rel_type_id
      ORDER BY t.transition_id DESC LIMIT 1)))
   OR EXISTS(SELECT 1 FROM truss.edge e WHERE
    e.target_id=(n.identity->>'id')::bigint AND e.target_type=(n.identity->>'typeId')::int
    AND NOT (live_edges ? jsonb_build_array(e.rel_type_id::text,e.id::text)::text)
    AND (NOT coalesce(independent_endpoints,false) OR to_jsonb(e) IS DISTINCT FROM
     (SELECT t.after_edge FROM truss.runtime_edge_transition t WHERE t.edge_id=e.id AND t.rel_type_id=e.rel_type_id
      ORDER BY t.transition_id DESC LIMIT 1)))) THEN 'incident' END problem
  FROM members n LEFT JOIN truss.object o ON o.id=(n.identity->>'id')::bigint AND o.type_id=(n.identity->>'typeId')::int)
 SELECT problem INTO final_problem FROM problems WHERE problem IS NOT NULL ORDER BY ordinal LIMIT 1;
 IF final_problem='object' THEN RAISE EXCEPTION 'actual final owned object required' USING ERRCODE='55000';END IF;
 IF final_problem='incident' THEN RAISE EXCEPTION 'complete final incident edge inventory required' USING ERRCODE='55000';END IF;
 WITH members AS MATERIALIZED (
  SELECT e.state,e.ordinal,final_edges->e.reference identity,
   CASE WHEN e.state->'deleted' IS DISTINCT FROM 'true'::jsonb THEN coalesce(final_nodes->(e.state->>'source'),
    truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,e.state->>'source','object',last_plan,attempt)) END source_identity,
   CASE WHEN e.state->'deleted' IS DISTINCT FROM 'true'::jsonb THEN coalesce(final_nodes->(e.state->>'target'),
    truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,e.state->>'target','object',last_plan,attempt)) END target_identity
  FROM jsonb_each(last_plan->'afterEdges') WITH ORDINALITY e(reference,state,ordinal))
 SELECT 'edge' INTO final_problem FROM members m LEFT JOIN truss.edge e
  ON e.id=(m.identity->>'id')::bigint AND e.rel_type_id=(m.identity->>'typeId')::int
 WHERE (to_jsonb(e)-ARRAY['created_at','updated_at']) IS DISTINCT FROM
  CASE WHEN m.state->'deleted'='true'::jsonb THEN NULL ELSE
   ((m.state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(m.identity->>'id')::bigint,
    'source_id',(m.source_identity->>'id')::bigint,'source_type',(m.source_identity->>'typeId')::int,
    'target_id',(m.target_identity->>'id')::bigint,'target_type',(m.target_identity->>'typeId')::int,
    'order_key',m.state->'orderKey'->>'text') END ORDER BY m.ordinal LIMIT 1;
 IF final_problem='edge' THEN RAISE EXCEPTION 'actual final owned edge required' USING ERRCODE='55000';END IF;
 IF independent_edge_creates THEN
  -- This scope contains only rootless stored endpoints and the catalog has no
  -- owned relationships. Every node is a forest root without graph traversal.
  IF EXISTS(SELECT 1 FROM jsonb_each(last_plan->'afterNodes') n
   WHERE n.value->'root' IS DISTINCT FROM 'null'::jsonb) THEN
   RAISE EXCEPTION 'actual final forest and explicit root correspondence required' USING ERRCODE='55000';END IF;
  RETURN;
 END IF;
 SELECT coalesce(array_agg(key ORDER BY key COLLATE "C"),'{}'::text[]) INTO node_order FROM jsonb_each(last_plan->'afterNodes') WHERE value->'deleted'='false'::jsonb;
 local_owned:=truss.runtime_owned_local_edges(last_plan->'afterEdges',node_order,'{}'::text[],true);
 projection:=truss.owned_forest_projection(cardinality(node_order),local_owned);
 FOR entry IN SELECT value FROM jsonb_array_elements(projection) LOOP
  reference:=node_order[(entry.value->>'node')::int+1];
  root_reference:=CASE WHEN entry.value->'root'='null'::jsonb THEN NULL ELSE node_order[(entry.value->>'root')::int+1] END;
  IF jsonb_extract_path(last_plan,'afterNodes',reference,'root') IS DISTINCT FROM coalesce(to_jsonb(root_reference),'null'::jsonb) THEN
   RAISE EXCEPTION 'actual final forest and explicit root correspondence required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_group_validate(uuid,boolean) FROM PUBLIC;
