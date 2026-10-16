-- Profile digest: SHA-256 of these exact UTF-8 bytes, without a newline:
-- Owned scalar graph groups v1: existing exact value profile; explicit aggregate root selection and subtree reparent; directed acyclic owned forest; independent edge delete refusal; ordered cascade; global native keys; original per-operation custody; same host transaction and idempotent receipts.
CREATE FUNCTION truss.runtime_owned_profile() RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT '{"identity":"truss-owned-scalar-graph","version":"0.1","sha256":"5f5badaa3b0beb01fef08d48883395eabc8499155d4c31f7ef802e63d49a6dde"}'::jsonb;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_profile() FROM PUBLIC;

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
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
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
 PERFORM truss.runtime_owned_key_preflight(inventory);
 FOR entry IN SELECT value FROM jsonb_array_elements(inventory->'operations') LOOP
  entry:=entry||jsonb_build_object('actorName',session_user::text,'mutationProfile',input->'mutationProfile',
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
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() THEN
  RAISE EXCEPTION 'original owned operation correspondence required' USING ERRCODE='55000';END IF;
 RETURN original.plan;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_plan(uuid,int) FROM PUBLIC;


-- Actual identities come only from the admitted stored state or the genuine
-- original create result. Local create ordinals never stand in for native IDs.
CREATE FUNCTION truss.runtime_owned_identity(selected_attempt uuid,selected_index int,reference text,entity_kind text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;attempt truss.runtime_object_attempt%ROWTYPE;
 creation_index int;result jsonb;operation jsonb;witness jsonb;pin record;
BEGIN
 IF entity_kind NOT IN ('object','edge') OR entity_kind IS NULL OR reference IS NULL THEN
  RAISE EXCEPTION 'explicit original entity reference required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);
 state:=coalesce(plan->(CASE entity_kind WHEN 'object' THEN 'afterNodes' ELSE 'afterEdges' END)->reference,
  plan->(CASE entity_kind WHEN 'object' THEN 'beforeNodes' ELSE 'beforeEdges' END)->reference);
 IF state IS NULL AND entity_kind='object' AND reference LIKE 'stored:%' THEN
  SELECT p.plan->'initialScope'->'boundary'->substring(reference FROM 8) INTO witness
   FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=0;
  IF witness IS NOT NULL THEN
   SELECT * INTO STRICT pin FROM truss.runtime_definition('type',(witness->'object'->>'type_id')::int,NULL,(plan->>'catalogRevision')::int);
   state:=jsonb_build_object('identity',jsonb_build_object('id',witness->'object'->>'id','typeId',witness->'object'->>'type_id',
    'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id)));
  END IF;
 END IF;
 IF state IS NULL THEN RAISE EXCEPTION 'original operation member required' USING ERRCODE='55000';END IF;
 identity:=state->'identity';
 IF reference LIKE 'stored:%' THEN
  IF reference IS DISTINCT FROM 'stored:'||(identity->>'typeId')||':'||(identity->>'id') THEN
   RAISE EXCEPTION 'original stored identity correspondence required' USING ERRCODE='55000';END IF;
 ELSIF reference ~ '^create:(0|[1-9][0-9]{0,2})$' THEN
  creation_index:=substring(reference FROM 8)::int;
  SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
  IF creation_index>selected_index OR creation_index>=attempt.next_index THEN
   RAISE EXCEPTION 'prior original create progress required' USING ERRCODE='55000';END IF;
  result:=attempt.results->creation_index;
  operation:=convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations'->creation_index;
  IF result->>'operation' IS DISTINCT FROM 'create_'||entity_kind
   OR operation->>'operation' IS DISTINCT FROM result->>'operation'
   OR result->>'outcome' IS DISTINCT FROM 'created'
   OR (result->'identity')-'id' IS DISTINCT FROM identity-'id'
   OR jsonb_typeof(result->'identity'->'id') IS DISTINCT FROM 'string'
   OR result->'identity'->>'id' !~ '^[1-9][0-9]{0,18}$'
   OR length(result->'identity'->>'id')=19 AND result->'identity'->>'id' COLLATE "C">'9223372036854775807' THEN
   RAISE EXCEPTION 'genuine original create result required' USING ERRCODE='55000';END IF;
  identity:=result->'identity';
 ELSE RAISE EXCEPTION 'original stored or create reference required' USING ERRCODE='55000';END IF;
 RETURN identity;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_identity(uuid,int,text,text) FROM PUBLIC;

-- Compare semantic simulation with realized transitions. Physical timestamps
-- remain in the original member/transition; this is not their replacement.
CREATE FUNCTION truss.runtime_owned_object_image(selected_attempt uuid,selected_index int,reference text,phase text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;root_identity jsonb;root_reference text;
BEGIN
 IF phase IS NULL OR phase NOT IN ('before','after') THEN RAISE EXCEPTION 'explicit image phase required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);state:=plan->(phase||'Nodes')->reference;
 IF state IS NULL OR state->'deleted'='true'::jsonb THEN RETURN NULL;END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'object');
 root_reference:=state->>'root';
 IF root_reference IS NOT NULL THEN root_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,root_reference,'object');END IF;
 RETURN ((state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(identity->>'id')::bigint,
  'root_id',(root_identity->>'id')::bigint,'root_type',(root_identity->>'typeId')::int);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_image(uuid,int,text,text) FROM PUBLIC;


CREATE FUNCTION truss.runtime_owned_edge_image(selected_attempt uuid,selected_index int,reference text,phase text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;source_identity jsonb;target_identity jsonb;
BEGIN
 IF phase IS NULL OR phase NOT IN ('before','after') THEN RAISE EXCEPTION 'explicit edge image phase required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);state:=plan->(phase||'Edges')->reference;
 IF state IS NULL OR state->'deleted'='true'::jsonb THEN RETURN NULL;END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'edge');
 source_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,state->>'source','object');
 target_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,state->>'target','object');
 RETURN ((state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(identity->>'id')::bigint,
  'source_id',(source_identity->>'id')::bigint,'source_type',(source_identity->>'typeId')::int,
  'target_id',(target_identity->>'id')::bigint,'target_type',(target_identity->>'typeId')::int,
  'order_key',state->'orderKey'->>'text');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_image(uuid,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_edge_metadata(selected_attempt uuid,selected_index int,reference text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;plan jsonb;prior jsonb;desired jsonb;identity jsonb;physical jsonb;
 source_identity jsonb;target_identity jsonb;old_source jsonb;old_target jsonb;endpoint_identity jsonb;
 endpoint_reference text;endpoint_image jsonb;relation truss.rel_def%ROWTYPE;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM truss.runtime_person(false)
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index THEN
  RAISE EXCEPTION 'current original owned effect required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);prior:=plan->'beforeEdges'->reference;desired:=plan->'afterEdges'->reference;
 IF desired IS NULL OR prior->'deleted'='true'::jsonb THEN RAISE EXCEPTION 'original live edge effect required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT relation FROM truss.rel_def WHERE rel_type_id=(desired->'identity'->>'typeId')::int AND retired_rev IS NULL;
 PERFORM truss.runtime_module_writer(relation.document_id,relation.module);
 IF relation.lifecycle NOT IN ('independent','owned') OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL THEN
  RAISE EXCEPTION 'selected owned or independent relationship required' USING ERRCODE='0A000';END IF;
 IF prior IS NOT NULL THEN
  identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'edge');
  SELECT to_jsonb(e) INTO STRICT physical FROM truss.edge e WHERE id=(identity->>'id')::bigint AND rel_type_id=relation.rel_type_id;
  IF physical-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_edge_image(selected_attempt,selected_index,reference,'before') THEN
   RAISE EXCEPTION 'original edge prestate required' USING ERRCODE='55000';END IF;
  old_source:=truss.runtime_owned_identity(selected_attempt,selected_index,prior->>'source','object');
  old_target:=truss.runtime_owned_identity(selected_attempt,selected_index,prior->>'target','object');
 END IF;
 source_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,desired->>'source','object');
 target_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,desired->>'target','object');
 FOR endpoint_reference IN SELECT DISTINCT value#>>'{}' FROM jsonb_array_elements(jsonb_build_array(
  desired->'source',desired->'target',prior->'source',prior->'target')) WHERE value<>'null'::jsonb LOOP
  endpoint_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,endpoint_reference,'object');
  IF NOT truss.runtime_can_read(endpoint_identity->'owner'->>'documentId',endpoint_identity->'owner'->>'moduleId') THEN
   RAISE EXCEPTION 'original endpoint reader required' USING ERRCODE='42501';END IF;
  SELECT to_jsonb(o) INTO STRICT endpoint_image FROM truss.object o
   WHERE id=(endpoint_identity->>'id')::bigint AND type_id=(endpoint_identity->>'typeId')::int;
  IF endpoint_image-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(selected_attempt,selected_index,endpoint_reference,'before') THEN
   RAISE EXCEPTION 'original endpoint prestate required' USING ERRCODE='55000';END IF;
 END LOOP;
 PERFORM truss.runtime_lock_edge_business_key(truss.runtime_edge_business_key(relation.rel_type_id,source_identity,target_identity));
 IF old_source IS NOT NULL THEN PERFORM truss.runtime_lock_edge_business_key(truss.runtime_edge_business_key(relation.rel_type_id,old_source,old_target));END IF;
 RETURN jsonb_build_object('ownedReference',reference,'documentId',relation.document_id,'moduleId',relation.module,'typeId',relation.rel_type_id::text,
  'identity',identity,'prior',physical,'source',source_identity,'target',target_identity,'oldSource',old_source,'oldTarget',old_target,
  'retained',coalesce(nullif(desired->'image'->'retained','null'::jsonb),'{}'::jsonb),'orderKey',desired->'orderKey','keys','[]'::jsonb,'values','[]'::jsonb);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_metadata(uuid,int,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_edge_effect_selection(selected_attempt uuid,selected_index int,metadata jsonb,effect_operation text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;reference text:=metadata->>'ownedReference';prior jsonb;desired jsonb;derived_operation text;original_operation text;
BEGIN
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);prior:=plan->'beforeEdges'->reference;desired:=plan->'afterEdges'->reference;
 original_operation:=plan->'operation'->>'operation';
 derived_operation:=CASE WHEN prior IS NULL THEN 'create_edge' WHEN desired->'deleted'='true'::jsonb THEN 'delete_edge' ELSE 'update_edge' END;
 IF desired IS NULL OR prior->'deleted'='true'::jsonb OR effect_operation IS DISTINCT FROM derived_operation
  OR (original_operation='delete_object' AND (derived_operation<>'delete_edge' OR prior IS NULL))
  OR (original_operation<>'delete_object' AND (original_operation IS DISTINCT FROM derived_operation OR reference IS DISTINCT FROM plan->>'primary'))
  OR metadata IS DISTINCT FROM truss.runtime_owned_edge_metadata(selected_attempt,selected_index,reference) THEN
  RAISE EXCEPTION 'original planned edge effect required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_effect_selection(uuid,int,jsonb,text) FROM PUBLIC;


-- Original operation-time endpoint roots; no live endpoint/root lookup.
CREATE FUNCTION truss.runtime_owned_endpoint_at(selected_attempt uuid,selected_index int,reference text,phase text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;ownership jsonb;root_identity jsonb;
BEGIN
 IF phase IS NULL OR phase NOT IN ('before','after') THEN RAISE EXCEPTION 'explicit endpoint phase required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);state:=plan->(phase||'Nodes')->reference;
 IF state IS NULL OR state->'deleted'='true'::jsonb THEN RAISE EXCEPTION 'original live endpoint context required' USING ERRCODE='55000';END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'object');ownership:='{"state":"rootless"}'::jsonb;
 IF state->>'root' IS NOT NULL THEN
  root_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,state->>'root','object');
  ownership:=jsonb_build_object('state','owned','root',root_identity);
 END IF;
 RETURN jsonb_build_object('identity',identity,'ownership',ownership);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_endpoint_at(uuid,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_edge_transition_validate(selected_transition bigint,authorize_read boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE transition truss.runtime_edge_transition%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;
 plan jsonb;reference text;candidate text;identity jsonb;prior jsonb;desired jsonb;expected_context jsonb;
 before_context jsonb;after_context jsonb;context jsonb;scope jsonb;previous_image jsonb;has_previous boolean;
 expected_mode text;original_mode text;expected_version bigint;journal jsonb;event jsonb;matches int:=0;
BEGIN
 IF authorize_read IS NULL THEN RAISE EXCEPTION 'explicit validation authority mode required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT transition FROM truss.runtime_edge_transition WHERE transition_id=selected_transition;
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=transition.attempt_id;
 IF attempt.writer_xid IS DISTINCT FROM transition.writer_xid OR transition.operation_index<0 OR transition.operation_index>=attempt.next_index
  OR jsonb_array_length(attempt.results)<>attempt.next_index
  OR (authorize_read AND NOT attempt.complete)
  OR (NOT authorize_read AND (attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM truss.runtime_person(false))) THEN
  RAISE EXCEPTION 'original completed edge operation progress required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(attempt.id,transition.operation_index);
 FOR candidate IN SELECT key FROM jsonb_each(plan->'afterEdges') LOOP
  identity:=truss.runtime_owned_identity(attempt.id,transition.operation_index,candidate,'edge');
  IF identity->>'id'=transition.edge_id::text AND identity->>'typeId'=transition.rel_type_id::text THEN
   reference:=candidate;matches:=matches+1;END IF;
 END LOOP;
 IF matches<>1 THEN RAISE EXCEPTION 'one original edge plan member required' USING ERRCODE='55000';END IF;
 prior:=plan->'beforeEdges'->reference;desired:=plan->'afterEdges'->reference;
 expected_mode:=CASE WHEN prior IS NULL THEN 'create_edge' WHEN desired->'deleted'='true'::jsonb THEN 'delete_edge' ELSE 'update_edge' END;
 original_mode:=plan->'operation'->>'operation';
 IF prior->'deleted'='true'::jsonb
  OR (original_mode='delete_object' AND expected_mode<>'delete_edge')
  OR (original_mode<>'delete_object' AND (original_mode IS DISTINCT FROM expected_mode OR reference IS DISTINCT FROM plan->>'primary'))
  OR transition.before_edge-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_edge_image(attempt.id,transition.operation_index,reference,'before')
  OR transition.after_edge-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_edge_image(attempt.id,transition.operation_index,reference,'after') THEN
  RAISE EXCEPTION 'original edge plan and transition images required' USING ERRCODE='55000';END IF;
 -- Exact physical prestate chains back to the original captured scope, including
 -- timestamps, rather than being reconstructed from the semantic projection.
 SELECT after_edge INTO previous_image FROM truss.runtime_edge_transition
  WHERE attempt_id=attempt.id AND edge_id=transition.edge_id AND rel_type_id=transition.rel_type_id
   AND operation_index<transition.operation_index ORDER BY operation_index DESC LIMIT 1;
 has_previous:=FOUND;
 IF NOT has_previous THEN
  SELECT p.plan->'initialScope' INTO STRICT scope FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.operation_index=0;
  previous_image:=scope->'edges'->transition.edge_id::text;
 END IF;
 IF transition.before_edge IS DISTINCT FROM previous_image THEN RAISE EXCEPTION 'original physical edge prestate chain required' USING ERRCODE='55000';END IF;
 IF prior IS NOT NULL THEN
  before_context:=jsonb_build_object('source',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,prior->>'source','before'),
   'target',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,prior->>'target','before'));
 END IF;
 IF desired->'deleted'='false'::jsonb THEN
  after_context:=jsonb_build_object('source',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,desired->>'source','after'),
   'target',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,desired->>'target','after'));
 END IF;
 expected_context:=jsonb_build_object('profile','truss-edge-endpoint-ownership/0.1','captureCatalogRevision',plan->>'catalogRevision',
  'before',before_context,'after',after_context);
 IF transition.endpoint_ownership IS DISTINCT FROM expected_context
  OR nullif(transition.old_source,'null'::jsonb) IS DISTINCT FROM before_context->'source'->'identity'
  OR nullif(transition.old_target,'null'::jsonb) IS DISTINCT FROM before_context->'target'->'identity'
  OR transition.source_identity IS DISTINCT FROM truss.runtime_owned_identity(attempt.id,transition.operation_index,desired->>'source','object')
  OR transition.target_identity IS DISTINCT FROM truss.runtime_owned_identity(attempt.id,transition.operation_index,desired->>'target','object') THEN
  RAISE EXCEPTION 'original endpoint and aggregate root context required' USING ERRCODE='55000';END IF;
 IF transition.before_edge IS NOT DISTINCT FROM transition.after_edge THEN
  IF transition.journal<>'[]'::jsonb THEN RAISE EXCEPTION 'unchanged edge has no journal' USING ERRCODE='55000';END IF;
 ELSE
  IF jsonb_array_length(transition.journal)<>1 THEN RAISE EXCEPTION 'one complete original edge event required' USING ERRCODE='55000';END IF;
  journal:=transition.journal->0;event:=convert_from(decode(journal->'new_value'->>'bytesBase64','base64'),'UTF8')::jsonb;
  expected_version:=CASE WHEN expected_mode='delete_edge' THEN (transition.before_edge->>'ver')::bigint+1 ELSE (transition.after_edge->>'ver')::bigint END;
  IF event->>'historyProfile' IS DISTINCT FROM 'truss-native-owned-edge-mutation/0.1'
   OR event->>'operation' IS DISTINCT FROM (CASE expected_mode WHEN 'create_edge' THEN 'create' WHEN 'delete_edge' THEN 'delete' ELSE 'metadata' END)
   OR event->>'eventVersion' IS DISTINCT FROM expected_version::text
   OR event->'identity' IS DISTINCT FROM truss.runtime_owned_identity(attempt.id,transition.operation_index,reference,'edge') THEN
   RAISE EXCEPTION 'original owned edge event required' USING ERRCODE='55000';END IF;
 END IF;
 IF authorize_read THEN
  FOR context IN SELECT value FROM jsonb_array_elements(jsonb_build_array(before_context->'source',before_context->'target',after_context->'source',after_context->'target')) WHERE value<>'null'::jsonb LOOP
   IF NOT truss.runtime_can_read(context->'identity'->'owner'->>'documentId',context->'identity'->'owner'->>'moduleId') THEN
    RAISE EXCEPTION 'current original endpoint reader required' USING ERRCODE='42501';END IF;
   PERFORM truss.runtime_history_ownership(jsonb_build_object('identity',context->'identity','catalogRevision',plan->>'catalogRevision','ownership',context->'ownership'));
  END LOOP;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_transition_validate(bigint,boolean) FROM PUBLIC;


-- Apply one object member of an original operation. The outer step alone emits
-- its public result and advances progress; descendants are never child groups.
CREATE FUNCTION truss.runtime_owned_object_effect(selected_attempt uuid,selected_index int,reference text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;plan jsonb;input jsonb;prior jsonb;desired jsonb;identity jsonb;
 object_row truss.object%ROWTYPE;old_image jsonb;new_image jsonb;expected_image jsonb;before_record jsonb;after_record jsonb;
 installation truss.catalog_runtime_installation%ROWTYPE;property truss.prop_def%ROWTYPE;pin record;
 events jsonb:='[]';event_refs jsonb:='[]';journals jsonb:='[]';event jsonb;entry jsonb;journal truss.journal%ROWTYPE;
 keys jsonb;version bigint;revision int;event_digest text;ordinal int;mode text;result jsonb;actual_deleted jsonb;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM truss.runtime_person(false)
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index THEN
  RAISE EXCEPTION 'current original object effect required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 prior:=plan->'beforeNodes'->reference;desired:=plan->'afterNodes'->reference;mode:=plan->'operation'->>'operation';
 IF mode NOT IN ('update_object','delete_object') OR prior IS NULL OR desired IS NULL OR prior->'deleted'='true'::jsonb
  OR (mode='update_object' AND desired->'deleted'='true'::jsonb)
  OR (mode='delete_object' AND desired->'deleted' IS DISTINCT FROM 'true'::jsonb)
  OR (reference IS DISTINCT FROM plan->>'primary' AND prior IS NOT DISTINCT FROM desired) THEN
  RAISE EXCEPTION 'original primary or affected descendant required' USING ERRCODE='55000';END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'object');
 PERFORM truss.runtime_module_writer(identity->'owner'->>'documentId',identity->'owner'->>'moduleId');
 IF NOT truss.runtime_object_values_readable((identity->>'typeId')::int) THEN RAISE EXCEPTION 'current original property/item readers required' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT object_row FROM truss.object WHERE id=(identity->>'id')::bigint AND type_id=(identity->>'typeId')::int FOR UPDATE NOWAIT;
 old_image:=to_jsonb(object_row);
 IF old_image-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(selected_attempt,selected_index,reference,'before') THEN
  RAISE EXCEPTION 'original complete object prestate required' USING ERRCODE='55000';END IF;
 IF prior IS NOT DISTINCT FROM desired THEN
  RETURN jsonb_build_object('outcome','unchanged','operation','update_object','identity',identity,'version',object_row.ver::text,'events','[]'::jsonb);
 END IF;
 IF object_row.ver=9223372036854775807 THEN RAISE EXCEPTION 'record version exhausted' USING ERRCODE='54000';END IF;
 version:=object_row.ver+1;revision:=(plan->>'catalogRevision')::int;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 before_record:=truss.runtime_object_history(old_image,identity);
 IF mode='update_object' THEN
  expected_image:=truss.runtime_owned_object_image(selected_attempt,selected_index,reference,'after');
  IF expected_image->>'ver' IS DISTINCT FROM version::text THEN RAISE EXCEPTION 'one original version advance required' USING ERRCODE='55000';END IF;
  IF object_row.props IS DISTINCT FROM expected_image->'props' THEN
   PERFORM truss.runtime_object_update_keys(object_row.id,object_row.type_id,expected_image->'props',convert_to('[]','UTF8'),selected_attempt,selected_index);
  END IF;
  object_row.props:=expected_image->'props';object_row.retained:=nullif(expected_image->'retained','null'::jsonb);
  object_row.root_id:=(expected_image->>'root_id')::bigint;object_row.root_type:=(expected_image->>'root_type')::int;
  object_row.rev:=revision;object_row.ver:=version;object_row.updated_at:=clock_timestamp();
  UPDATE truss.object SET props=object_row.props,retained=object_row.retained,root_id=object_row.root_id,root_type=object_row.root_type,
   rev=object_row.rev,ver=object_row.ver,updated_at=object_row.updated_at WHERE id=object_row.id AND type_id=object_row.type_id
   RETURNING to_jsonb(object) INTO STRICT new_image;
  IF new_image-ARRAY['created_at','updated_at'] IS DISTINCT FROM expected_image OR new_image->'created_at' IS DISTINCT FROM old_image->'created_at' THEN
   RAISE EXCEPTION 'original planned object update required' USING ERRCODE='55000';END IF;
  after_record:=truss.runtime_object_history(new_image,identity);
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=object_row.type_id AND retired_rev IS NULL ORDER BY prop_id LOOP
   IF old_image->'props'->property.prop_id::text IS DISTINCT FROM new_image->'props'->property.prop_id::text THEN
    SELECT * INTO STRICT pin FROM truss.runtime_definition('property',object_row.type_id,property.prop_id);
    events:=events||jsonb_build_array(jsonb_build_object('operation','property','propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,
     'before',CASE WHEN old_image->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',old_image->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END,
     'after',CASE WHEN new_image->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',new_image->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END));
   END IF;
  END LOOP;
  events:=events||jsonb_build_array(jsonb_build_object('operation','metadata','before',before_record,'after',after_record));
 ELSE
  FOR entry IN SELECT to_jsonb(k) FROM truss.object_key_bucket k WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id ORDER BY k.namespace_bytes,k.key_bytes LOOP
   PERFORM truss.lock_string_key_bucket(decode(substring(entry->>'namespace_bytes' FROM 3),'hex'),decode(substring(entry->>'key_bytes' FROM 3),'hex'));
   UPDATE truss.key_bucket_guard SET generation=generation+1 WHERE namespace_sha256=decode(substring(entry->>'namespace_sha256' FROM 3),'hex') AND key_sha256=decode(substring(entry->>'key_sha256' FROM 3),'hex');
  END LOOP;
  DELETE FROM truss.object WHERE id=object_row.id AND type_id=object_row.type_id RETURNING to_jsonb(object) INTO STRICT actual_deleted;
  IF actual_deleted IS DISTINCT FROM old_image THEN RAISE EXCEPTION 'original planned deletion required' USING ERRCODE='55000';END IF;
  events:=jsonb_build_array(jsonb_build_object('operation','delete','before',before_record));
 END IF;
 FOR ordinal IN 0..jsonb_array_length(events)-1 LOOP
  event:=events->ordinal;event:=event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',nextval('truss.journal_seq')::text,
   'identity',identity,'eventVersion',version::text,'eventCatalogRevision',revision::text,
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text));
  events:=jsonb_set(events,ARRAY[ordinal::text],event);
 END LOOP;
 event_digest:=encode(sha256(convert_to(events::text,'UTF8')),'hex');
 FOR event IN SELECT value FROM jsonb_array_elements(events) LOOP
  event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',jsonb_array_length(events)::text,'orderedEventDigest',event_digest));
  journal.seq:=(event->>'seq')::bigint;journal.at:=clock_timestamp();journal.xid:=attempt.writer_xid;journal.entity_kind:='o';journal.entity_id:=object_row.id;journal.entity_type:=object_row.type_id;
  journal.ver:=version;journal.op:=CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END;journal.prop_id:=(event->>'propertyId')::int;
  journal.old_value:=NULL;journal.new_value:=truss.runtime_exact_wrapper('event',convert_to(event::text,'UTF8'));journal.rev:=revision;
  journal.origin:=truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8'));
  INSERT INTO truss.journal SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(journal))).*;
  journals:=journals||jsonb_build_array(to_jsonb(journal));event_refs:=event_refs||jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',journal.seq::text));
 END LOOP;
 SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]'::jsonb) INTO keys FROM truss.object_key_bucket k WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id;
 INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
 VALUES(selected_attempt,selected_index,attempt.writer_xid,object_row.id,object_row.type_id,old_image,new_image,keys,journals);
 PERFORM truss.runtime_module_writer(identity->'owner'->>'documentId',identity->'owner'->>'moduleId');
 IF NOT truss.runtime_object_values_readable((identity->>'typeId')::int) THEN RAISE EXCEPTION 'current final property/item readers required' USING ERRCODE='42501';END IF;
 IF mode='update_object' THEN RETURN jsonb_build_object('outcome','changed','operation','update_object','identity',identity,'version',version::text,'events',event_refs);END IF;
 RETURN jsonb_build_object('outcome','deleted','operation','delete_object','identity',identity,'deletionVersion',version::text,
  'deleted',jsonb_build_array(jsonb_build_object('identity',identity,'deletionVersion',version::text)),'events',event_refs);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_effect(uuid,int,text) FROM PUBLIC;


CREATE FUNCTION truss.runtime_owned_step(selected_attempt uuid,selected_index int) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;plan jsonb;mode text;entry record;prior jsonb;effect_mode text;
 metadata jsonb;effect jsonb;primary_result jsonb;events jsonb:='[]';deleted jsonb:='[]';result jsonb;selected_transition bigint;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM truss.runtime_person(false)
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index THEN
  RAISE EXCEPTION 'current ordered owned operation required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);mode:=plan->'operation'->>'operation';
 IF mode NOT IN ('create_edge','update_edge','delete_edge','update_object','delete_object') THEN
  RAISE EXCEPTION 'selected original owned operation required' USING ERRCODE='55000';END IF;
 -- Cascade edges precede every endpoint deletion. No child effect advances the
 -- original attempt or adds a synthetic operation/result to its input.
 FOR entry IN SELECT key,value FROM jsonb_each(plan->'afterEdges') e WHERE e.value IS DISTINCT FROM plan->'beforeEdges'->e.key
  OR e.key=plan->>'primary' AND mode='update_edge' ORDER BY key COLLATE "C" LOOP
  prior:=plan->'beforeEdges'->entry.key;
  IF prior->'deleted'='true'::jsonb THEN CONTINUE;END IF;
  effect_mode:=CASE WHEN prior IS NULL THEN 'create_edge' WHEN entry.value->'deleted'='true'::jsonb THEN 'delete_edge' ELSE 'update_edge' END;
  metadata:=truss.runtime_owned_edge_metadata(selected_attempt,selected_index,entry.key);
  effect:=convert_from(truss.runtime_edge_effect(selected_attempt,selected_index,metadata,effect_mode,false),'UTF8')::jsonb;
  events:=events||(effect->'events');deleted:=deleted||coalesce(effect->'deleted','[]'::jsonb);
  IF entry.key=plan->>'primary' THEN primary_result:=effect;END IF;
 END LOOP;
 -- Aggregate-root FKs are immediate: remove nonroots before their root.
 FOR entry IN SELECT key,value FROM jsonb_each(plan->'afterNodes') n WHERE
  (plan->'beforeNodes') ? n.key AND (n.value IS DISTINCT FROM plan->'beforeNodes'->n.key OR n.key=plan->>'primary' AND mode='update_object')
  ORDER BY CASE WHEN plan->'beforeNodes'->n.key->'root'='null'::jsonb THEN 1 ELSE 0 END,key COLLATE "C" LOOP
  IF plan->'beforeNodes'->entry.key->'deleted'='true'::jsonb THEN CONTINUE;END IF;
  effect:=truss.runtime_owned_object_effect(selected_attempt,selected_index,entry.key);
  events:=events||(effect->'events');deleted:=deleted||coalesce(effect->'deleted','[]'::jsonb);
  IF entry.key=plan->>'primary' THEN primary_result:=effect;END IF;
 END LOOP;
 IF primary_result IS NULL OR primary_result->>'operation' IS DISTINCT FROM mode THEN RAISE EXCEPTION 'one original primary result required' USING ERRCODE='55000';END IF;
 result:=jsonb_set(primary_result,'{events}',events);
 IF mode IN ('delete_object','delete_edge') THEN result:=jsonb_set(result,'{deleted}',deleted);END IF;
 IF octet_length(convert_to(result::text,'UTF8'))>16777216 THEN RAISE EXCEPTION 'bounded complete original result required' USING ERRCODE='54000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=next_index+1,results=results||jsonb_build_array(result),
  aliases=aliases||CASE WHEN mode='create_edge' AND (plan->'operation') ? 'alias' THEN
   jsonb_build_array(jsonb_build_object('alias',plan->'operation'->>'alias','identity',result->'identity')) ELSE '[]'::jsonb END WHERE id=selected_attempt;
 -- New edge IDs are now backed by their genuine original parent result.
 FOR selected_transition IN SELECT transition_id FROM truss.runtime_edge_transition WHERE attempt_id=selected_attempt AND operation_index=selected_index LOOP
  PERFORM truss.runtime_owned_edge_transition_validate(selected_transition,false);
 END LOOP;
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_step(uuid,int) FROM PUBLIC;


-- Lock the complete initial/planned key union before allocating an identity or
-- writing a graph row. Reservation simulation preserves key_reuse=forbid even
-- when an earlier operation in this same group changes or deletes its object.
CREATE FUNCTION truss.runtime_owned_key_preflight(inventory jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;candidate jsonb;definition truss.key_def%ROWTYPE;
 component int;cells jsonb;before_cells jsonb;tuple_bytes bytea;namespace bytea;transport bytea;pin record;
 routes jsonb:='[]';lock_routes jsonb:='[]';entry jsonb;route record;observed record;member truss.object_key_bucket%ROWTYPE;
 seen jsonb:='{}';route_key text;reference text;unchanged boolean;
BEGIN
 IF inventory->>'profile' IS DISTINCT FROM 'truss-owned-group-plan/0.1'
  OR (inventory->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR (SELECT value FROM truss.setting WHERE key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb THEN
  RAISE EXCEPTION 'original current forbid-reuse inventory required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 FOR candidate IN SELECT value FROM (
  SELECT -1 ordinal,n.key reference,jsonb_build_object('phase','initial','reference','stored:'||n.key,'image',n.value) value
   FROM jsonb_each(inventory->'initialScope'->'nodes') n
  UNION ALL SELECT (p.value->>'operationIndex')::int,n.key,jsonb_build_object('phase','after','reference',n.key,
   'image',n.value->'image','before',p.value->'beforeNodes'->n.key->'image')
   FROM jsonb_array_elements(inventory->'operations') p CROSS JOIN LATERAL jsonb_each(p.value->'afterNodes') n
   WHERE n.value->'deleted'='false'::jsonb AND n.value IS DISTINCT FROM p.value->'beforeNodes'->n.key
 ) candidates ORDER BY candidates.ordinal,candidates.reference COLLATE "C" LOOP
  FOR definition IN SELECT k.* FROM truss.key_def k WHERE k.type_id=(candidate->'image'->>'type_id')::int AND k.retired_rev IS NULL ORDER BY k.key_num LOOP
   cells:='[]';before_cells:='[]';
   FOREACH component IN ARRAY definition.prop_ids LOOP
    cells:=cells||jsonb_build_array(candidate->'image'->'props'->component::text);
    before_cells:=before_cells||jsonb_build_array(candidate->'before'->'props'->component::text);
   END LOOP;
   tuple_bytes:=truss.derive_catalog_key_tuple(definition.type_id,definition.key_num,cells);
   SELECT * INTO STRICT pin FROM truss.runtime_definition('key',definition.type_id,definition.key_num);
   namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',definition.type_id::text,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');
   routes:=routes||jsonb_build_array(jsonb_build_object('phase',candidate->>'phase','reference',candidate->>'reference',
    'objectId',candidate->'image'->>'id','typeId',definition.type_id,'keyNumber',definition.key_num,
    'namespace',encode(namespace,'hex'),'transport',encode(transport,'hex'),'tuple',encode(tuple_bytes,'hex'),
    'unchanged',CASE WHEN candidate->'before' IS NOT NULL AND candidate->'before'<>'null'::jsonb THEN truss.derive_catalog_key_tuple(definition.type_id,definition.key_num,before_cells)=tuple_bytes ELSE false END));
   IF jsonb_array_length(routes)>4096 OR octet_length(convert_to(routes::text,'UTF8'))>8388608 THEN
    RAISE EXCEPTION 'bounded whole-group key footprint required' USING ERRCODE='54000';END IF;
  END LOOP;
 END LOOP;
 -- Retired definitions may still have original live memberships. Deletion
 -- touches these bytes too; include them without reinterpreting retired keys.
 FOR member IN SELECT k.* FROM truss.object_key_bucket k JOIN jsonb_each(inventory->'initialScope'->'nodes') n
  ON k.object_id=(n.value->>'id')::bigint AND k.type_id=(n.value->>'type_id')::int LOOP
  lock_routes:=lock_routes||jsonb_build_array(jsonb_build_object('namespace',encode(member.namespace_bytes,'hex'),'transport',encode(member.key_bytes,'hex')));
  IF jsonb_array_length(lock_routes)+jsonb_array_length(routes)>4096 OR octet_length(convert_to(lock_routes::text,'UTF8'))+octet_length(convert_to(routes::text,'UTF8'))>8388608 THEN
   RAISE EXCEPTION 'bounded whole-group key footprint required' USING ERRCODE='54000';END IF;
 END LOOP;
 FOR route IN SELECT DISTINCT decode(value->>'namespace','hex') route_namespace,decode(value->>'transport','hex') route_transport FROM jsonb_array_elements(routes||lock_routes)
  ORDER BY route_namespace,route_transport LOOP
  PERFORM truss.lock_string_key_bucket(route.route_namespace,route.route_transport);
 END LOOP;
 FOR entry IN SELECT value FROM jsonb_array_elements(routes) LOOP
  namespace:=decode(entry->>'namespace','hex');transport:=decode(entry->>'transport','hex');
  route_key:=(entry->>'namespace')||':'||(entry->>'transport');reference:=entry->>'reference';
  SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(namespace,transport);
  IF entry->>'phase'='initial' THEN
   IF cardinality(observed.member_ids)<>1 THEN RAISE EXCEPTION 'one original live key member required' USING ERRCODE='55000';END IF;
   SELECT * INTO STRICT member FROM truss.object_key_bucket WHERE storage_row_id=observed.member_ids[1];
   IF member.object_id::text IS DISTINCT FROM entry->>'objectId' OR member.type_id IS DISTINCT FROM (entry->>'typeId')::int
    OR member.key_num IS DISTINCT FROM (entry->>'keyNumber')::smallint
    OR NOT truss.verify_object_string_key(member.object_id,member.type_id,member.key_num,decode(entry->>'tuple','hex')) THEN
    RAISE EXCEPTION 'original key membership and values required' USING ERRCODE='55000';END IF;
   seen:=seen||jsonb_build_object(route_key,reference);
  ELSIF entry->'unchanged'='true'::jsonb THEN
   IF seen->>route_key IS DISTINCT FROM reference THEN RAISE EXCEPTION 'original unchanged key owner required' USING ERRCODE='55000';END IF;
  ELSE
   IF seen ? route_key OR cardinality(observed.member_ids)>0 OR cardinality(observed.reservation_ids)>0 THEN
    RAISE EXCEPTION 'key already allocated or reserved' USING ERRCODE='23505';END IF;
   seen:=seen||jsonb_build_object(route_key,reference);
  END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_key_preflight(jsonb) FROM PUBLIC;

-- Check each changed object against its original operation, including descendants.
-- Physical before-images chain to the captured scope or an earlier original step.
CREATE FUNCTION truss.runtime_owned_object_transition_validate(selected_transition bigint,authorize_read boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE transition truss.runtime_object_transition%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;
 plan jsonb;reference text;candidate text;identity jsonb;prior jsonb;desired jsonb;previous_image jsonb;scope jsonb;
 original_mode text;expected_version bigint;matches int:=0;has_previous boolean;property truss.prop_def;pin record;
 expected_events jsonb:='[]';expected_event jsonb;journal jsonb;event jsonb;ordinal int:=0;
 before_record jsonb;after_record jsonb;semantic_events jsonb:='[]';group_pin jsonb;input jsonb;
BEGIN
 IF authorize_read IS NULL THEN RAISE EXCEPTION 'explicit object validation mode required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT transition FROM truss.runtime_object_transition WHERE transition_id=selected_transition;
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=transition.attempt_id;
 IF attempt.writer_xid IS DISTINCT FROM transition.writer_xid OR transition.operation_index<0 OR transition.operation_index>=attempt.next_index
  OR jsonb_array_length(attempt.results)<>attempt.next_index OR (authorize_read AND NOT attempt.complete)
  OR (NOT authorize_read AND (attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM truss.runtime_person(false))) THEN
  RAISE EXCEPTION 'original completed object operation progress required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(attempt.id,transition.operation_index);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 FOR candidate IN SELECT key FROM jsonb_each(plan->'afterNodes') LOOP
  identity:=truss.runtime_owned_identity(attempt.id,transition.operation_index,candidate,'object');
  IF identity->>'id'=transition.object_id::text AND identity->>'typeId'=transition.type_id::text THEN reference:=candidate;matches:=matches+1;END IF;
 END LOOP;
 IF matches<>1 THEN RAISE EXCEPTION 'one original object plan member required' USING ERRCODE='55000';END IF;
 identity:=truss.runtime_owned_identity(attempt.id,transition.operation_index,reference,'object');
 prior:=plan->'beforeNodes'->reference;desired:=plan->'afterNodes'->reference;original_mode:=plan->'operation'->>'operation';
 IF transition.before_object IS NULL THEN
  IF original_mode IS DISTINCT FROM 'create_object' OR reference IS DISTINCT FROM plan->>'primary'
   OR transition.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(attempt.id,transition.operation_index,reference,'after') THEN
   RAISE EXCEPTION 'original object creation required' USING ERRCODE='55000';END IF;
  IF NOT authorize_read THEN PERFORM truss.runtime_create_transition_validate(selected_transition);END IF;
  RETURN;
 END IF;
 IF original_mode NOT IN ('update_object','delete_object') OR prior IS NULL OR desired IS NULL
  OR prior->'deleted'='true'::jsonb OR prior IS NOT DISTINCT FROM desired
  OR (original_mode='update_object' AND desired->'deleted' IS DISTINCT FROM 'false'::jsonb)
  OR (original_mode='delete_object' AND desired->'deleted' IS DISTINCT FROM 'true'::jsonb)
  OR transition.before_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(attempt.id,transition.operation_index,reference,'before')
  OR transition.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(attempt.id,transition.operation_index,reference,'after') THEN
  RAISE EXCEPTION 'original changed object plan and images required' USING ERRCODE='55000';END IF;
 SELECT after_object INTO previous_image FROM truss.runtime_object_transition WHERE attempt_id=attempt.id
  AND object_id=transition.object_id AND type_id=transition.type_id AND operation_index<transition.operation_index ORDER BY operation_index DESC LIMIT 1;
 has_previous:=FOUND;
 IF NOT has_previous THEN
  SELECT p.plan->'initialScope' INTO STRICT scope FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.operation_index=0;
  previous_image:=scope->'nodes'->(transition.type_id::text||':'||transition.object_id::text);
 END IF;
 IF transition.before_object IS DISTINCT FROM previous_image THEN RAISE EXCEPTION 'original physical object prestate chain required' USING ERRCODE='55000';END IF;
 expected_version:=(transition.before_object->>'ver')::bigint+1;
 before_record:=truss.runtime_object_history(transition.before_object,identity);
 IF transition.after_object IS NOT NULL THEN
  IF transition.after_object->>'ver' IS DISTINCT FROM expected_version::text
   OR transition.after_object->'created_at' IS DISTINCT FROM transition.before_object->'created_at' THEN
   RAISE EXCEPTION 'one object version advance and original creation time required' USING ERRCODE='55000';END IF;
  after_record:=truss.runtime_object_history(transition.after_object,identity);
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=transition.type_id AND since_rev<=(plan->>'catalogRevision')::int
   AND (retired_rev IS NULL OR retired_rev>(plan->>'catalogRevision')::int) ORDER BY prop_id LOOP
   IF transition.before_object->'props'->property.prop_id::text IS DISTINCT FROM transition.after_object->'props'->property.prop_id::text THEN
    SELECT * INTO STRICT pin FROM truss.runtime_definition('property',transition.type_id,property.prop_id,(plan->>'catalogRevision')::int);
    expected_events:=expected_events||jsonb_build_array(jsonb_build_object('operation','property','propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,
     'before',CASE WHEN transition.before_object->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',transition.before_object->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END,
     'after',CASE WHEN transition.after_object->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',transition.after_object->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END));
   END IF;
  END LOOP;
  expected_events:=expected_events||jsonb_build_array(jsonb_build_object('operation','metadata','before',before_record,'after',after_record));
 ELSE expected_events:=jsonb_build_array(jsonb_build_object('operation','delete','before',before_record));END IF;
 IF jsonb_array_length(transition.journal)<>jsonb_array_length(expected_events) THEN RAISE EXCEPTION 'complete original object event inventory required' USING ERRCODE='55000';END IF;
 FOR journal IN SELECT value FROM jsonb_array_elements(transition.journal) LOOP
  event:=convert_from(decode(journal->'new_value'->>'bytesBase64','base64'),'UTF8')::jsonb;expected_event:=expected_events->ordinal;
  IF event-ARRAY['interfaceVersion','sourceEpoch','historyProfile','xid','seq','identity','eventVersion','eventCatalogRevision','origin','mutationGroup'] IS DISTINCT FROM expected_event
   OR event->>'historyProfile' IS DISTINCT FROM 'truss-native-owned-mutation/0.1' OR event->'identity' IS DISTINCT FROM identity
   OR event->>'eventVersion' IS DISTINCT FROM expected_version::text OR event->>'eventCatalogRevision' IS DISTINCT FROM plan->>'catalogRevision'
   OR event->>'xid' IS DISTINCT FROM attempt.writer_xid::text
   OR event->>'interfaceVersion' IS DISTINCT FROM 'truss-history-event/0.2.0-proposal'
   OR event->>'sourceEpoch' IS DISTINCT FROM attempt.context->>'sourceEpoch'
   OR event->'origin' IS DISTINCT FROM jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',plan->>'actorName')
   OR event->>'seq' IS DISTINCT FROM journal->>'seq'
   OR journal->>'xid' IS DISTINCT FROM attempt.writer_xid::text OR journal->>'ver' IS DISTINCT FROM expected_version::text
   OR journal->>'rev' IS DISTINCT FROM plan->>'catalogRevision'
   OR journal->>'entity_kind' IS DISTINCT FROM 'o' OR journal->>'entity_id' IS DISTINCT FROM transition.object_id::text
   OR journal->>'entity_type' IS DISTINCT FROM transition.type_id::text
   OR journal->>'op' IS DISTINCT FROM (CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END)
   OR journal->'prop_id' IS DISTINCT FROM coalesce(to_jsonb((event->>'propertyId')::int),'null'::jsonb)
   OR journal->'new_value' IS DISTINCT FROM truss.runtime_exact_wrapper('event',convert_to(event::text,'UTF8'))
   OR journal->'origin' IS DISTINCT FROM truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8')) THEN
   RAISE EXCEPTION 'exact original owned object event required' USING ERRCODE='55000';END IF;
  IF group_pin IS NULL THEN group_pin:=event->'mutationGroup';
  ELSIF group_pin IS DISTINCT FROM event->'mutationGroup' THEN RAISE EXCEPTION 'one original owned event group required' USING ERRCODE='55000';END IF;
  semantic_events:=semantic_events||jsonb_build_array(event-'mutationGroup');ordinal:=ordinal+1;
 END LOOP;
 IF group_pin IS DISTINCT FROM jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',ordinal::text,
  'orderedEventDigest',encode(sha256(convert_to(semantic_events::text,'UTF8')),'hex')) THEN
  RAISE EXCEPTION 'complete original owned event group required' USING ERRCODE='55000';END IF;
 IF authorize_read THEN
  PERFORM truss.runtime_history_ownership(before_record);
  IF after_record IS NOT NULL THEN PERFORM truss.runtime_history_ownership(after_record);END IF;
 ELSE
  PERFORM truss.runtime_module_writer(identity->'owner'->>'documentId',identity->'owner'->>'moduleId');
  IF NOT truss.runtime_object_values_readable(transition.type_id) THEN RAISE EXCEPTION 'current original property readers required' USING ERRCODE='42501';END IF;
  PERFORM truss.runtime_history_ownership(before_record);
  IF after_record IS NOT NULL THEN PERFORM truss.runtime_history_ownership(after_record);END IF;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_transition_validate(bigint,boolean) FROM PUBLIC;
