-- Native owned-group execution preparation. Called only by the installed
-- mutation entry point after original-input admission and the graph-write gate.
-- References for new objects/edges are original create ordinals, never fake IDs.
CREATE FUNCTION truss.runtime_owned_reference(reference jsonb,aliases jsonb,states jsonb) RETURNS text
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected text;identity jsonb;state jsonb;
BEGIN
 IF jsonb_typeof(reference) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'explicit graph reference required' USING ERRCODE='22023';END IF;
 IF reference->>'state'='alias' THEN
  IF reference-ARRAY['state','alias']<>'{}'::jsonb OR jsonb_typeof(reference->'alias') IS DISTINCT FROM 'string' THEN
   RAISE EXCEPTION 'closed prior alias required' USING ERRCODE='22023';END IF;
  selected:=aliases->> (reference->>'alias');
 ELSIF reference->>'state'='stored' THEN
  identity:=reference->'identity';
  IF reference-ARRAY['state','identity']<>'{}'::jsonb OR jsonb_typeof(identity) IS DISTINCT FROM 'object'
   OR identity-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb THEN
   RAISE EXCEPTION 'closed original stored reference required' USING ERRCODE='22023';END IF;
  selected:='stored:'||(identity->>'typeId')||':'||(identity->>'id');
 ELSE RAISE EXCEPTION 'stored or prior alias required' USING ERRCODE='22023';END IF;
 state:=states->selected;
 IF selected IS NULL OR state IS NULL THEN RAISE EXCEPTION 'existing reference of the correct kind required' USING ERRCODE='22023';END IF;
 IF state->'deleted'='true'::jsonb THEN RAISE EXCEPTION 'referenced graph member deleted' USING ERRCODE='P1004';END IF;
 IF identity IS NOT NULL AND identity IS DISTINCT FROM state->'identity' THEN
  RAISE EXCEPTION 'original qualified identity correspondence required' USING ERRCODE='22023';END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_reference(jsonb,jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_local_edges(edges jsonb,node_order text[],boundary_order text[],owned boolean) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE entry record;source_node int;target_node int;result jsonb:='[]';ordinal int:=0;
BEGIN
 FOR entry IN SELECT key,value FROM jsonb_each(edges) ORDER BY key COLLATE "C" LOOP
  IF entry.value->'deleted'='true'::jsonb THEN CONTINUE;END IF;
  IF (entry.value->>'lifecycle'='owned') IS DISTINCT FROM owned THEN CONTINUE;END IF;
  source_node:=array_position(node_order,entry.value->>'source')-1;
  target_node:=array_position(node_order,entry.value->>'target')-1;
  IF source_node IS NULL THEN source_node:=cardinality(node_order)+array_position(boundary_order,entry.value->>'source')-1;END IF;
  IF target_node IS NULL THEN target_node:=cardinality(node_order)+array_position(boundary_order,entry.value->>'target')-1;END IF;
  IF source_node IS NULL OR target_node IS NULL OR owned AND (source_node>=cardinality(node_order) OR target_node>=cardinality(node_order)) THEN
   RAISE EXCEPTION 'complete typed endpoint scope required' USING ERRCODE='55000';END IF;
  -- Ordinals count all live edges so the two lifecycle arrays stay disjoint.
  SELECT count(*) INTO ordinal FROM jsonb_each(edges) e WHERE e.value->'deleted'='false'::jsonb AND e.key COLLATE "C"<entry.key COLLATE "C";
  result:=result||jsonb_build_array(jsonb_build_object('edge',ordinal,'source',source_node,'target',target_node));
 END LOOP;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_local_edges(jsonb,text[],text[],boolean) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_prepare(input jsonb,scope jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE nodes jsonb:='{}';edges jsonb:='{}';aliases jsonb:='{}';plans jsonb:='[]';
 node_order text[]:='{}';boundary_order text[]:='{}';entry record;selected text;source_ref text;target_ref text;root_ref text;
 operation jsonb;before_nodes jsonb;before_edges jsonb;state jsonb;prior jsonb;image jsonb;values_image jsonb;ownership jsonb;
 selected_type truss.type_def%ROWTYPE;relation truss.rel_def%ROWTYPE;pin record;identity jsonb;revision int;
 index int:=0;before_count int;descendants text[];descendant text;projection jsonb;deleted jsonb;local_owned jsonb;local_independent jsonb;
 unset_name text;authored jsonb;retained jsonb;order_key jsonb;selected_source_type int;selected_target_type int;plan jsonb;outgoing bigint;incoming bigint;
BEGIN
 IF jsonb_typeof(input->'operations') IS DISTINCT FROM 'array' OR jsonb_array_length(input->'operations') NOT BETWEEN 1 AND 128
  OR jsonb_typeof(scope->'nodes') IS DISTINCT FROM 'object' OR jsonb_typeof(scope->'edges') IS DISTINCT FROM 'object'
  OR octet_length(convert_to(scope::text,'UTF8'))>4194304 THEN
  RAISE EXCEPTION 'complete bounded original group scope required' USING ERRCODE='54000';END IF;
 revision:=(scope->>'catalogRevision')::int;
 IF revision IS NULL OR revision<1 OR revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1) THEN
  RAISE EXCEPTION 'current admitted group catalog required' USING ERRCODE='55P03';END IF;
 FOR entry IN SELECT key,value FROM jsonb_each(scope->'nodes') ORDER BY (value->>'type_id')::int,(value->>'id')::bigint LOOP
  selected:='stored:'||entry.key;image:=entry.value;
  SELECT * INTO STRICT pin FROM truss.runtime_definition('type',(image->>'type_id')::int);
  identity:=jsonb_build_object('id',image->>'id','typeId',image->>'type_id','definitionPin',pin.definition_pin,
   'owner',jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id));
  root_ref:=CASE WHEN image->'root_id'='null'::jsonb THEN NULL ELSE 'stored:'||(image->>'root_type')||':'||(image->>'root_id') END;
  nodes:=nodes||jsonb_build_object(selected,jsonb_build_object('identity',identity,'image',image-ARRAY['root_id','root_type','updated_at'],
   'root',root_ref,'deleted',false));node_order:=array_append(node_order,selected);
 END LOOP;
 FOR entry IN SELECT key,value FROM jsonb_each(scope->'boundary') ORDER BY key COLLATE "C" LOOP
  boundary_order:=array_append(boundary_order,'stored:'||entry.key);
 END LOOP;
 FOR entry IN SELECT key,value FROM jsonb_each(scope->'edges') ORDER BY (value->>'rel_type_id')::int,(value->>'id')::bigint LOOP
  image:=entry.value;SELECT * INTO STRICT relation FROM truss.rel_def WHERE rel_type_id=(image->>'rel_type_id')::int;
  identity:=jsonb_build_object('id',image->>'id','typeId',image->>'rel_type_id','definitionPin',truss.runtime_relationship_pin(relation.rel_type_id),
   'owner',jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module));
  selected:='stored:'||(image->>'rel_type_id')||':'||(image->>'id');
  edges:=edges||jsonb_build_object(selected,jsonb_build_object('identity',identity,'image',image-ARRAY['source_id','source_type','target_id','target_type','order_key','updated_at'],
   'source','stored:'||(image->>'source_type')||':'||(image->>'source_id'),
   'target','stored:'||(image->>'target_type')||':'||(image->>'target_id'),'lifecycle',relation.lifecycle,'deleted',false,
   'orderKey',CASE WHEN image->'order_key'='null'::jsonb THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',image->>'order_key') END));
 END LOOP;
 FOR operation IN SELECT value FROM jsonb_array_elements(input->'operations') LOOP
  before_nodes:=nodes;before_edges:=edges;
  IF operation ? 'alias' AND (jsonb_typeof(operation->'alias') IS DISTINCT FROM 'string'
   OR octet_length(operation->>'alias') NOT BETWEEN 1 AND 1024 OR aliases ? (operation->>'alias')) THEN
   RAISE EXCEPTION 'unique bounded original alias required' USING ERRCODE='22023';END IF;
  IF operation->>'operation' IN ('create_object','update_object','delete_object') THEN
   selected_type:=truss.runtime_operation_type(operation,input->'operations',index);
   IF operation->>'operation'='create_object' THEN
    IF operation-ARRAY['operation','typeDefinitionPin','values','ownership','alias']<>'{}'::jsonb
     OR jsonb_typeof(operation->'ownership') IS DISTINCT FROM 'object' THEN
     RAISE EXCEPTION 'closed original object create required' USING ERRCODE='22023';END IF;
    IF cardinality(node_order)>=128 THEN RAISE EXCEPTION 'bounded complete group objects required' USING ERRCODE='54000';END IF;
    selected:='create:'||index;node_order:=array_append(node_order,selected);
    values_image:=truss.owned_object_values(selected_type.type_id,operation,NULL,NULL);
    state:=jsonb_build_object('identity',jsonb_build_object('id',NULL,'typeId',selected_type.type_id::text,
     'definitionPin',operation->>'typeDefinitionPin','owner',jsonb_build_object('documentId',selected_type.document_id,'moduleId',selected_type.module)),
     'image',jsonb_build_object('id',NULL,'type_id',selected_type.type_id,'props',values_image->'props',
      'retained',nullif(values_image->'retained','{}'::jsonb),'rev',revision,'ver',1),
     'createIndex',index,'root',NULL,'deleted',false);
    ownership:=operation->'ownership';
   ELSE
    selected:=truss.runtime_owned_reference(operation->'target',aliases,nodes);state:=nodes->selected;
    IF state->'identity'->>'typeId' IS DISTINCT FROM selected_type.type_id::text THEN RAISE EXCEPTION 'original object reference type required' USING ERRCODE='22023';END IF;
    IF operation ? 'expectedVersion' AND (jsonb_typeof(operation->'expectedVersion') IS DISTINCT FROM 'string'
     OR operation->>'expectedVersion' IS DISTINCT FROM state->'image'->>'ver') THEN
     RAISE EXCEPTION 'expected object version failed' USING ERRCODE='P1003';END IF;
    ownership:=operation->'ownershipChange';
   END IF;
   IF operation->>'operation'='delete_object' THEN
    IF operation-ARRAY['operation','target','expectedVersion']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed object delete required' USING ERRCODE='22023';END IF;
    local_owned:=truss.runtime_owned_local_edges(edges,node_order,boundary_order,true);
    local_independent:=truss.runtime_owned_local_edges(edges,node_order,boundary_order,false);
    deleted:=truss.owned_delete_projection(cardinality(node_order),local_owned,local_independent,array_position(node_order,selected)-1);
    FOR entry IN SELECT value FROM jsonb_array_elements(deleted->'deletedNodes') LOOP
     descendant:=node_order[(entry.value#>>'{}')::int+1];
     IF (nodes->descendant->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'object version exhausted' USING ERRCODE='54000';END IF;
     nodes:=jsonb_set(nodes,ARRAY[descendant,'deleted'],'true'::jsonb);
    END LOOP;
    FOR entry IN SELECT key,value FROM jsonb_each(edges) WHERE value->'deleted'='false'::jsonb LOOP
     IF nodes->(entry.value->>'source')->'deleted'='true'::jsonb OR nodes->(entry.value->>'target')->'deleted'='true'::jsonb THEN
      IF (entry.value->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
      edges:=jsonb_set(edges,ARRAY[entry.key,'deleted'],'true'::jsonb);
     END IF;
    END LOOP;
   ELSE
    IF operation->>'operation'='update_object' THEN
     IF operation-ARRAY['operation','target','set','unset','expectedVersion','ownershipChange']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed object update required' USING ERRCODE='22023';END IF;
     values_image:=truss.owned_object_values(selected_type.type_id,operation,state->'image'->'props',nullif(state->'image'->'retained','null'::jsonb));
     state:=jsonb_set(state,'{image,props}',values_image->'props');
     state:=jsonb_set(state,'{image,retained}',coalesce(nullif(values_image->'retained','{}'::jsonb),'null'::jsonb));
    END IF;
    IF ownership IS NOT NULL THEN
     IF ownership='{"state":"rootless"}'::jsonb THEN root_ref:=NULL;
     ELSIF ownership->>'state'='owned' AND ownership-ARRAY['state','root']='{}'::jsonb THEN
      root_ref:=truss.runtime_owned_reference(ownership->'root',aliases,nodes);
      IF root_ref=selected OR nodes->root_ref->'root'<>'null'::jsonb THEN RAISE EXCEPTION 'selected live rootless aggregate root required' USING ERRCODE='22023';END IF;
     ELSE RAISE EXCEPTION 'explicit exact ownership selection required' USING ERRCODE='22023';END IF;
     IF state->'root' IS DISTINCT FROM coalesce(to_jsonb(root_ref),'null'::jsonb) THEN
      descendants:=ARRAY[selected];
      LOOP
       before_count:=cardinality(descendants);
       SELECT array_agg(DISTINCT reference COLLATE "C" ORDER BY reference COLLATE "C") INTO descendants FROM (
        SELECT unnest(descendants) AS reference UNION ALL SELECT value->>'target' FROM jsonb_each(edges)
         WHERE value->'deleted'='false'::jsonb AND value->>'lifecycle'='owned' AND value->>'source'=ANY(descendants)) expanded;
       EXIT WHEN cardinality(descendants)=before_count;
      END LOOP;
      IF root_ref=ANY(descendants) THEN RAISE EXCEPTION 'aggregate root outside moved subtree required' USING ERRCODE='22023';END IF;
      FOR descendant IN SELECT unnest(descendants) LOOP
       IF descendant=selected THEN state:=jsonb_set(state,'{root}',coalesce(to_jsonb(root_ref),'null'::jsonb));
       ELSE nodes:=jsonb_set(nodes,ARRAY[descendant,'root'],coalesce(to_jsonb(coalesce(root_ref,selected)),'null'::jsonb));END IF;
      END LOOP;
     END IF;
    END IF;
    nodes:=nodes||jsonb_build_object(selected,state);
    FOR entry IN SELECT key,value FROM jsonb_each(nodes) LOOP
     IF before_nodes ? entry.key AND entry.value IS DISTINCT FROM before_nodes->entry.key THEN
      IF (entry.value->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'object version exhausted' USING ERRCODE='54000';END IF;
      state:=jsonb_set(entry.value,'{image,ver}',to_jsonb((entry.value->'image'->>'ver')::bigint+1));
      nodes:=jsonb_set(nodes,ARRAY[entry.key],jsonb_set(state,'{image,rev}',to_jsonb(revision)));
     END IF;
    END LOOP;
   END IF;
  ELSIF operation->>'operation' IN ('create_edge','update_edge','delete_edge') THEN
   relation:=truss.runtime_operation_relationship(operation,input->'operations',index);
   IF relation.lifecycle NOT IN ('owned','independent') OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL THEN
    RAISE EXCEPTION 'supported directed relationship required' USING ERRCODE='0A000';END IF;
   IF operation->>'operation'='create_edge' THEN
    IF operation-ARRAY['operation','relationshipDefinitionPin','source','target','values','orderKey','alias']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge create required' USING ERRCODE='22023';END IF;
    IF (SELECT count(*) FROM jsonb_each(edges))>=1024 THEN RAISE EXCEPTION 'bounded complete group edges required' USING ERRCODE='54000';END IF;
    selected:='create:'||index;source_ref:=truss.runtime_owned_reference(operation->'source',aliases,nodes);
    target_ref:=truss.runtime_owned_reference(operation->'target',aliases,nodes);retained:='{}';authored:=operation->'values';order_key:=operation->'orderKey';
    state:=jsonb_build_object('identity',jsonb_build_object('id',NULL,'typeId',relation.rel_type_id::text,
     'definitionPin',operation->>'relationshipDefinitionPin','owner',jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module)),
     'image',jsonb_build_object('id',NULL,'rel_type_id',relation.rel_type_id,'props','{}'::jsonb,'retained',NULL,'ver',1,'rev',revision),
     'createIndex',index,'lifecycle',relation.lifecycle,'deleted',false);
   ELSE
    selected:=truss.runtime_owned_reference(operation->'target',aliases,edges);state:=edges->selected;
    IF state->'identity'->>'typeId' IS DISTINCT FROM relation.rel_type_id::text THEN RAISE EXCEPTION 'original edge reference type required' USING ERRCODE='22023';END IF;
    IF operation ? 'expectedVersion' AND (jsonb_typeof(operation->'expectedVersion') IS DISTINCT FROM 'string'
     OR operation->>'expectedVersion' IS DISTINCT FROM state->'image'->>'ver') THEN RAISE EXCEPTION 'expected edge version failed' USING ERRCODE='P1003';END IF;
    source_ref:=state->>'source';target_ref:=state->>'target';retained:=coalesce(nullif(state->'image'->'retained','null'::jsonb),'{}');
    order_key:=state->'orderKey';
    IF order_key IS NULL THEN order_key:=CASE WHEN state->'image'->'order_key'='null'::jsonb THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',state->'image'->>'order_key') END;END IF;
    IF operation->>'operation'='delete_edge' THEN
     IF operation-ARRAY['operation','target','expectedVersion']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge delete required' USING ERRCODE='22023';END IF;
     IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
     edges:=jsonb_set(edges,ARRAY[selected,'deleted'],'true'::jsonb);
    ELSE
     IF operation-ARRAY['operation','target','set','unset','expectedVersion','endpointChange','orderKeyChange']<>'{}'::jsonb
      OR jsonb_typeof(operation->'unset') IS DISTINCT FROM 'array' OR jsonb_array_length(operation->'unset')>1024
      OR EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'unset') u WHERE jsonb_typeof(value) IS DISTINCT FROM 'string' OR octet_length(value#>>'{}') NOT BETWEEN 1 AND 4096)
      OR jsonb_array_length(operation->'unset')<>(SELECT count(DISTINCT value) FROM jsonb_array_elements(operation->'unset')) THEN RAISE EXCEPTION 'closed edge update required' USING ERRCODE='22023';END IF;
     FOR unset_name IN SELECT value#>>'{}' FROM jsonb_array_elements(operation->'unset') LOOP retained:=retained-unset_name;END LOOP;
     authored:=operation->'set';
     IF operation ? 'endpointChange' THEN
      IF jsonb_typeof(operation->'endpointChange') IS DISTINCT FROM 'object' OR (operation->'endpointChange')-ARRAY['source','target']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed endpoint change required' USING ERRCODE='22023';END IF;
      source_ref:=truss.runtime_owned_reference(operation->'endpointChange'->'source',aliases,nodes);target_ref:=truss.runtime_owned_reference(operation->'endpointChange'->'target',aliases,nodes);
     END IF;
     IF operation ? 'orderKeyChange' THEN order_key:=operation->'orderKeyChange';END IF;
    END IF;
   END IF;
   IF operation->>'operation'<>'delete_edge' THEN
    IF jsonb_typeof(authored) IS DISTINCT FROM 'array' OR jsonb_array_length(authored)>1024
     OR EXISTS(SELECT 1 FROM jsonb_array_elements(authored) v WHERE value-ARRAY['name','value']<>'{}'::jsonb OR jsonb_typeof(value->'name') IS DISTINCT FROM 'string'
      OR octet_length(value->>'name') NOT BETWEEN 1 AND 4096 OR truss.valid_scalar_cell(value->'value') IS NOT TRUE)
     OR jsonb_array_length(authored)<>(SELECT count(DISTINCT value->>'name') FROM jsonb_array_elements(authored))
     OR EXISTS(SELECT 1 FROM jsonb_array_elements(authored) v JOIN jsonb_array_elements(coalesce(operation->'unset','[]')) u ON v.value->>'name'=u.value#>>'{}') THEN RAISE EXCEPTION 'unique exact scalar edge values required' USING ERRCODE='22023';END IF;
    FOR entry IN SELECT value FROM jsonb_array_elements(authored) LOOP retained:=retained||jsonb_build_object(entry.value->>'name',truss.canonical_flat_cell(entry.value->'value'));END LOOP;
    IF octet_length(convert_to(retained::text,'UTF8'))>1048576 THEN RAISE EXCEPTION 'bounded edge values required' USING ERRCODE='54000';END IF;
    IF (order_key='{"state":"null"}'::jsonb OR order_key->>'state'='text' AND jsonb_typeof(order_key->'text')='string'
     AND order_key-ARRAY['state','text']='{}'::jsonb AND octet_length(order_key->>'text')<=4096) IS NOT TRUE THEN RAISE EXCEPTION 'exact bounded order key required' USING ERRCODE='22023';END IF;
    selected_source_type:=(nodes->source_ref->'identity'->>'typeId')::int;selected_target_type:=(nodes->target_ref->'identity'->>'typeId')::int;
    IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=selected_source_type AND target_type=selected_target_type) THEN RAISE EXCEPTION 'admitted endpoint pair required' USING ERRCODE='22023';END IF;
    state:=state||jsonb_build_object('source',source_ref,'target',target_ref,'orderKey',order_key);
    state:=jsonb_set(state,'{image,retained}',coalesce(nullif(retained,'{}'::jsonb),'null'::jsonb));
    IF before_edges ? selected AND state IS DISTINCT FROM before_edges->selected THEN
     IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
     state:=jsonb_set(state,'{image,ver}',to_jsonb((state->'image'->>'ver')::bigint+1));state:=jsonb_set(state,'{image,rev}',to_jsonb(revision));
    END IF;
    edges:=edges||jsonb_build_object(selected,state);
   END IF;
  ELSE RAISE EXCEPTION 'supported original graph operation required' USING ERRCODE='0A000';END IF;
  IF operation ? 'alias' THEN aliases:=aliases||jsonb_build_object(operation->>'alias',selected);END IF;
  plan:=jsonb_build_object('profile','truss-owned-operation-plan/0.1','operationIndex',index,'operation',operation,
   'primary',selected,'beforeNodes',before_nodes,'afterNodes',nodes,'beforeEdges',before_edges,'afterEdges',edges);
  plans:=plans||jsonb_build_array(plan);
  IF octet_length(convert_to(plans::text,'UTF8'))>16777216 THEN RAISE EXCEPTION 'bounded whole group execution inventory required' USING ERRCODE='54000';END IF;
  index:=index+1;
 END LOOP;
 SELECT coalesce(array_agg(reference ORDER BY ordinal),'{}'::text[]) INTO node_order FROM unnest(node_order) WITH ORDINALITY n(reference,ordinal) WHERE nodes->reference->'deleted'='false'::jsonb;
 local_owned:=truss.runtime_owned_local_edges(edges,node_order,boundary_order,true);
 projection:=truss.owned_forest_projection(cardinality(node_order),local_owned);
 FOR entry IN SELECT value FROM jsonb_array_elements(projection) LOOP
  selected:=node_order[(entry.value->>'node')::int+1];root_ref:=CASE WHEN entry.value->'root'='null'::jsonb THEN NULL ELSE node_order[(entry.value->>'root')::int+1] END;
  IF nodes->selected->'root' IS DISTINCT FROM coalesce(to_jsonb(root_ref),'null'::jsonb) THEN RAISE EXCEPTION 'final ownership graph requires explicit root change' USING ERRCODE='22023';END IF;
 END LOOP;
 FOREACH selected IN ARRAY node_order LOOP
  selected_source_type:=(nodes->selected->'identity'->>'typeId')::int;
  FOR relation IN SELECT r.* FROM truss.rel_def r WHERE r.retired_rev IS NULL AND EXISTS(
   SELECT 1 FROM truss.rel_endpoint ep WHERE ep.rel_type_id=r.rel_type_id AND selected_source_type IN(ep.source_type,ep.target_type)) LOOP
   IF EXISTS(SELECT 1 FROM truss.rel_endpoint ep WHERE ep.rel_type_id=relation.rel_type_id AND ep.source_type=selected_source_type) THEN
    SELECT count(*) INTO outgoing FROM jsonb_each(edges) e WHERE e.value->'deleted'='false'::jsonb
     AND e.value->'identity'->>'typeId'=relation.rel_type_id::text AND e.value->>'source'=selected;
    IF outgoing<relation.target_min OR relation.target_max IS NOT NULL AND outgoing>relation.target_max THEN RAISE EXCEPTION 'final outgoing multiplicity failed' USING ERRCODE='P1005';END IF;
   END IF;
   IF EXISTS(SELECT 1 FROM truss.rel_endpoint ep WHERE ep.rel_type_id=relation.rel_type_id AND ep.target_type=selected_source_type) THEN
    SELECT count(*) INTO incoming FROM jsonb_each(edges) e WHERE e.value->'deleted'='false'::jsonb
     AND e.value->'identity'->>'typeId'=relation.rel_type_id::text AND e.value->>'target'=selected;
    IF incoming<relation.source_min OR relation.source_max IS NOT NULL AND incoming>relation.source_max THEN RAISE EXCEPTION 'final incoming multiplicity failed' USING ERRCODE='P1005';END IF;
   END IF;
  END LOOP;
 END LOOP;
 plan:=jsonb_build_object('profile','truss-owned-group-plan/0.1','catalogRevision',revision,
  'initialScope',scope,'operations',plans,'aliases',aliases);
 IF octet_length(convert_to(plan::text,'UTF8'))>16777216 THEN RAISE EXCEPTION 'bounded complete group execution inventory required' USING ERRCODE='54000';END IF;
 RETURN plan;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_prepare(jsonb,jsonb) FROM PUBLIC;


-- This is the execution entry's native preflight, not a caller-supplied plan.
-- Admission is before predicate/key/row locks. No canonical graph rows change.
CREATE FUNCTION truss.runtime_owned_capture(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;observed jsonb;locked jsonb;
 inventory jsonb;entry jsonb;owner record;selected_type int;relation truss.rel_def%ROWTYPE;endpoint_owner record;retained_bytes bigint:=0;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
  OR attempt.actor_oid IS DISTINCT FROM truss.runtime_person(false) OR attempt.complete
  OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR attempt.context->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
  OR input->'mutationProfile'->>'identity' IS DISTINCT FROM 'truss-owned-scalar-graph'
  OR input->'mutationProfile'->>'version' IS DISTINCT FROM '0.1'
  OR EXISTS(SELECT 1 FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt) THEN
  RAISE EXCEPTION 'original unused owned attempt required' USING ERRCODE='55000';END IF;
 observed:=truss.runtime_owned_input_scope(input);
 -- All component objects and relationships can participate in reparent/cascade;
 -- outside independent endpoints are read witnesses only.
 FOR owner IN SELECT document_id,module_id FROM (SELECT DISTINCT document_id,module_id FROM (
  SELECT value->>'document_id' document_id,value->>'module' module_id FROM jsonb_each(observed->'types')
  UNION ALL SELECT value->>'document_id',value->>'module' FROM jsonb_each(observed->'relationships')
 ) owners) distinct_owners ORDER BY document_id COLLATE "C",module_id COLLATE "C" LOOP
  PERFORM truss.runtime_module_writer(owner.document_id,owner.module_id);
 END LOOP;
 FOR owner IN SELECT document_id,module_id FROM (SELECT DISTINCT value->'definition'->>'document_id' document_id,
  value->'definition'->>'module' module_id FROM jsonb_each(observed->'boundary')) distinct_owners
  ORDER BY document_id COLLATE "C",module_id COLLATE "C" LOOP
  IF NOT truss.runtime_can_read(owner.document_id,owner.module_id) THEN
   RAISE EXCEPTION 'current outside endpoint reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 -- Implicit descendant values and zero-edge multiplicity checks require the
 -- same original readers as explicit operations, before graph exclusion.
 FOR selected_type IN SELECT type_id FROM (
  SELECT DISTINCT (value->>'type_id')::int type_id FROM jsonb_each(observed->'types')
  UNION SELECT (truss.runtime_operation_type(value,input->'operations',(ordinal-1)::int)).type_id
   FROM jsonb_array_elements(input->'operations') WITH ORDINALITY o(value,ordinal)
   WHERE value->>'operation' IN ('create_object','update_object','delete_object')
 ) affected_types ORDER BY type_id LOOP
  IF truss.runtime_object_values_readable(selected_type) IS NOT TRUE THEN
   RAISE EXCEPTION 'complete affected property and item readers required' USING ERRCODE='42501';END IF;
  FOR relation IN SELECT r.* FROM truss.rel_def r WHERE r.retired_rev IS NULL AND EXISTS(
   SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=r.rel_type_id AND selected_type IN(e.source_type,e.target_type))
   ORDER BY r.rel_type_id LOOP
   IF NOT truss.runtime_can_read(relation.document_id,relation.module) THEN
    RAISE EXCEPTION 'counted relationship reader required' USING ERRCODE='42501';END IF;
   FOR endpoint_owner IN SELECT DISTINCT t.document_id,t.module FROM truss.rel_endpoint e
    JOIN truss.type_def t ON t.type_id IN(e.source_type,e.target_type) WHERE e.rel_type_id=relation.rel_type_id LOOP
    IF NOT truss.runtime_can_read(endpoint_owner.document_id,endpoint_owner.module) THEN
     RAISE EXCEPTION 'counted relationship endpoint reader required' USING ERRCODE='42501';END IF;
   END LOOP;
  END LOOP;
 END LOOP;
 -- Every graph writer joins this same exclusion in object/edge order. NOWAIT
 -- gives one refusal; it does not hide a retry loop in the embedded library.
 LOCK TABLE truss.object IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 LOCK TABLE truss.edge IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 locked:=truss.runtime_owned_input_scope(input);
 IF locked IS DISTINCT FROM observed THEN
  RAISE EXCEPTION 'graph changed before write exclusion' USING ERRCODE='55P03';END IF;
 inventory:=truss.runtime_owned_prepare(input,locked);
 FOR entry IN SELECT value FROM jsonb_array_elements(inventory->'operations') LOOP
  entry:=entry||jsonb_build_object('mutationProfile',input->'mutationProfile',
   'catalogRevision',inventory->'catalogRevision');
  IF entry->>'operationIndex'='0' THEN
   entry:=entry||jsonb_build_object('initialScope',inventory->'initialScope');END IF;
  retained_bytes:=retained_bytes+octet_length(convert_to(entry::text,'UTF8'));
  IF retained_bytes>16777216 THEN RAISE EXCEPTION 'bounded retained whole group inventory required' USING ERRCODE='54000';END IF;
  INSERT INTO truss.runtime_owned_operation(attempt_id,operation_index,writer_xid,plan)
  VALUES(attempt.id,(entry->>'operationIndex')::int,attempt.writer_xid,entry);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_capture(uuid) FROM PUBLIC;

-- Reuse original operation evidence after rows move or disappear. Identity-only
-- matching never attributes a descendant transition to an unrelated operation.
CREATE FUNCTION truss.runtime_owned_plan(selected_attempt uuid,selected_index int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;original truss.runtime_owned_operation%ROWTYPE;input jsonb;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 SELECT * INTO STRICT original FROM truss.runtime_owned_operation
  WHERE attempt_id=selected_attempt AND operation_index=selected_index;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 IF selected_index NOT BETWEEN 0 AND jsonb_array_length(input->'operations')-1
  OR original.writer_xid IS DISTINCT FROM attempt.writer_xid
  OR original.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.1'
  OR original.plan->'operationIndex' IS DISTINCT FROM to_jsonb(selected_index)
  OR original.plan->'operation' IS DISTINCT FROM input->'operations'->selected_index
  OR original.plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
  OR input->'mutationProfile' IS DISTINCT FROM attempt.context->'mutationProfile'
  OR input->'mutationProfile'->>'identity' IS DISTINCT FROM 'truss-owned-scalar-graph'
  OR input->'mutationProfile'->>'version' IS DISTINCT FROM '0.1' THEN
  RAISE EXCEPTION 'original owned operation correspondence required' USING ERRCODE='55000';END IF;
 RETURN original.plan;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_plan(uuid,int) FROM PUBLIC;
