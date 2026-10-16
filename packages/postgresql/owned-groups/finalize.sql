-- Close the original plan against every actual effect. The final image check is
-- performed at group finish; commit rechecks custody and authority after later
-- groups may legitimately have superseded those images in the same transaction.
CREATE FUNCTION truss.runtime_owned_group_validate(selected_attempt uuid,check_final boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;plan jsonb;last_plan jsonb;initial_scope jsonb;
 operation jsonb;result jsonb;entry record;owner record;transition_id bigint;identity jsonb;actual jsonb;
 reference text;mode text;expected_objects int;expected_edges int;events jsonb;deleted jsonb;aliases jsonb:='[]';
 primary_before jsonb;primary_after jsonb;expected_outcome text;expected_version text;
 node_order text[];projection jsonb;local_owned jsonb;root_reference text;index int;current_actor oid;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 current_actor:=truss.runtime_person(false);
 IF check_final IS NULL OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
  OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR attempt.next_index<>jsonb_array_length(input->'operations') OR jsonb_array_length(attempt.results)<>attempt.next_index
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>attempt.next_index THEN
  RAISE EXCEPTION 'complete original owned group required' USING ERRCODE='55000';END IF;
 FOR index IN 0..attempt.next_index-1 LOOP
  plan:=truss.runtime_owned_plan(selected_attempt,index);operation:=plan->'operation';
  IF operation IS DISTINCT FROM input->'operations'->index
   OR plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile' THEN
   RAISE EXCEPTION 'original owned operation source correspondence required' USING ERRCODE='55000';END IF;
  mode:=operation->>'operation';result:=attempt.results->index;
  IF index=0 THEN initial_scope:=plan->'initialScope';END IF;
  expected_objects:=0;expected_edges:=0;
  FOR entry IN SELECT key,value FROM jsonb_each(plan->'afterNodes') n WHERE n.value IS DISTINCT FROM plan->'beforeNodes'->n.key
   AND (plan->'beforeNodes'->n.key IS NULL OR plan->'beforeNodes'->n.key->'deleted'='false'::jsonb) LOOP
   identity:=truss.runtime_owned_identity(selected_attempt,index,entry.key,'object');
   SELECT t.transition_id INTO STRICT transition_id FROM truss.runtime_object_transition t WHERE t.attempt_id=selected_attempt
    AND t.operation_index=index AND t.object_id=(identity->>'id')::bigint AND t.type_id=(identity->>'typeId')::int;
   PERFORM truss.runtime_owned_object_transition_validate_qualified(transition_id,false,current_actor);expected_objects:=expected_objects+1;
  END LOOP;
  FOR entry IN SELECT key,value FROM jsonb_each(plan->'afterEdges') e WHERE
   (e.value IS DISTINCT FROM plan->'beforeEdges'->e.key OR e.key=plan->>'primary' AND mode='update_edge')
   AND (plan->'beforeEdges'->e.key IS NULL OR plan->'beforeEdges'->e.key->'deleted'='false'::jsonb) LOOP
   identity:=truss.runtime_owned_identity(selected_attempt,index,entry.key,'edge');
   SELECT t.transition_id INTO STRICT transition_id FROM truss.runtime_edge_transition t WHERE t.attempt_id=selected_attempt
    AND t.operation_index=index AND t.edge_id=(identity->>'id')::bigint AND t.rel_type_id=(identity->>'typeId')::int;
   PERFORM truss.runtime_owned_edge_transition_validate(transition_id,false);expected_edges:=expected_edges+1;
  END LOOP;
  IF expected_objects<>(SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt AND operation_index=index)
   OR expected_edges<>(SELECT count(*) FROM truss.runtime_edge_transition WHERE attempt_id=selected_attempt AND operation_index=index) THEN
   RAISE EXCEPTION 'complete original effect inventory required' USING ERRCODE='55000';END IF;
  identity:=truss.runtime_owned_identity(selected_attempt,index,plan->>'primary',CASE WHEN mode LIKE '%object' THEN 'object' ELSE 'edge' END);
  IF result->'identity' IS DISTINCT FROM identity OR result->>'operation' IS DISTINCT FROM mode THEN
   RAISE EXCEPTION 'original primary result identity required' USING ERRCODE='55000';END IF;
  primary_before:=plan->(CASE WHEN mode LIKE '%object' THEN 'beforeNodes' ELSE 'beforeEdges' END)->(plan->>'primary');
  primary_after:=plan->(CASE WHEN mode LIKE '%object' THEN 'afterNodes' ELSE 'afterEdges' END)->(plan->>'primary');
  expected_outcome:=CASE WHEN mode LIKE 'create_%' THEN 'created' WHEN mode LIKE 'delete_%' THEN 'deleted'
   WHEN primary_before IS NOT DISTINCT FROM primary_after THEN 'unchanged' ELSE 'changed' END;
  expected_version:=CASE WHEN mode LIKE 'delete_%' THEN ((primary_before->'image'->>'ver')::bigint+1)::text ELSE primary_after->'image'->>'ver' END;
  IF result->>'outcome' IS DISTINCT FROM expected_outcome
   OR result->>(CASE WHEN mode LIKE 'delete_%' THEN 'deletionVersion' ELSE 'version' END) IS DISTINCT FROM expected_version THEN
   RAISE EXCEPTION 'original primary outcome and version required' USING ERRCODE='55000';END IF;
  IF mode LIKE 'delete_%' THEN
   SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]'::jsonb) INTO deleted FROM (
    SELECT jsonb_build_object('identity',truss.runtime_owned_identity(selected_attempt,index,p.key,'object'),
     'deletionVersion',((p.value->'image'->>'ver')::bigint+1)::text) v
    FROM jsonb_each(plan->'beforeNodes') p WHERE p.value->'deleted'='false'::jsonb AND plan->'afterNodes'->p.key->'deleted'='true'::jsonb
    UNION ALL SELECT jsonb_build_object('identity',truss.runtime_owned_identity(selected_attempt,index,p.key,'edge'),
     'deletionVersion',((p.value->'image'->>'ver')::bigint+1)::text)
    FROM jsonb_each(plan->'beforeEdges') p WHERE p.value->'deleted'='false'::jsonb AND plan->'afterEdges'->p.key->'deleted'='true'::jsonb) members;
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
 FOR entry IN SELECT key,value FROM jsonb_each(last_plan->'afterNodes') LOOP
  identity:=truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,entry.key,'object');
  SELECT to_jsonb(o)-ARRAY['created_at','updated_at'] INTO actual FROM truss.object o WHERE o.id=(identity->>'id')::bigint AND o.type_id=(identity->>'typeId')::int;
  IF actual IS DISTINCT FROM truss.runtime_owned_object_image(selected_attempt,attempt.next_index-1,entry.key,'after') THEN
   RAISE EXCEPTION 'actual final owned object required' USING ERRCODE='55000';END IF;
  IF EXISTS(SELECT 1 FROM truss.edge e WHERE (e.source_id=(identity->>'id')::bigint AND e.source_type=(identity->>'typeId')::int
    OR e.target_id=(identity->>'id')::bigint AND e.target_type=(identity->>'typeId')::int)
   AND NOT EXISTS(SELECT 1 FROM jsonb_each(last_plan->'afterEdges') p WHERE p.value->'deleted'='false'::jsonb
    AND truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,p.key,'edge')->>'id'=e.id::text
    AND truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,p.key,'edge')->>'typeId'=e.rel_type_id::text)) THEN
   RAISE EXCEPTION 'complete final incident edge inventory required' USING ERRCODE='55000';END IF;
 END LOOP;
 FOR entry IN SELECT key,value FROM jsonb_each(last_plan->'afterEdges') LOOP
  identity:=truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,entry.key,'edge');
  SELECT to_jsonb(e)-ARRAY['created_at','updated_at'] INTO actual FROM truss.edge e WHERE e.id=(identity->>'id')::bigint AND e.rel_type_id=(identity->>'typeId')::int;
  IF actual IS DISTINCT FROM truss.runtime_owned_edge_image(selected_attempt,attempt.next_index-1,entry.key,'after') THEN
   RAISE EXCEPTION 'actual final owned edge required' USING ERRCODE='55000';END IF;
 END LOOP;
 SELECT coalesce(array_agg(key ORDER BY key COLLATE "C"),'{}'::text[]) INTO node_order FROM jsonb_each(last_plan->'afterNodes') WHERE value->'deleted'='false'::jsonb;
 local_owned:=truss.runtime_owned_local_edges(last_plan->'afterEdges',node_order,'{}'::text[],true);
 projection:=truss.owned_forest_projection(cardinality(node_order),local_owned);
 FOR entry IN SELECT value FROM jsonb_array_elements(projection) LOOP
  reference:=node_order[(entry.value->>'node')::int+1];
  root_reference:=CASE WHEN entry.value->'root'='null'::jsonb THEN NULL ELSE node_order[(entry.value->>'root')::int+1] END;
  IF last_plan->'afterNodes'->reference->'root' IS DISTINCT FROM coalesce(to_jsonb(root_reference),'null'::jsonb) THEN
   RAISE EXCEPTION 'actual final forest and explicit root correspondence required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_group_validate(uuid,boolean) FROM PUBLIC;
