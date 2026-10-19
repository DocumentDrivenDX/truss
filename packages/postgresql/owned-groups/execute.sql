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
DECLARE result jsonb;invalid boolean;
BEGIN
 WITH coordinates AS MATERIALIZED (
  SELECT reference,ordinal-1 ordinal,false boundary FROM unnest(node_order) WITH ORDINALITY n(reference,ordinal)
  UNION ALL SELECT reference,cardinality(node_order)+ordinal-1,true FROM unnest(boundary_order) WITH ORDINALITY b(reference,ordinal)),
 live AS MATERIALIZED (
  SELECT key,value,row_number() OVER(ORDER BY key COLLATE "C")-1 ordinal
  FROM jsonb_each(edges) WHERE value->'deleted'='false'::jsonb),
 selected AS (
  SELECT e.ordinal,s.ordinal source,t.ordinal target,s.boundary source_boundary,t.boundary target_boundary
  FROM live e LEFT JOIN coordinates s ON s.reference=e.value->>'source'
  LEFT JOIN coordinates t ON t.reference=e.value->>'target'
  WHERE (e.value->>'lifecycle'='owned') IS NOT DISTINCT FROM owned)
 SELECT coalesce(bool_or(source IS NULL OR target IS NULL OR owned AND (source_boundary OR target_boundary)),false),
  coalesce(jsonb_agg(jsonb_build_object('edge',ordinal,'source',source,'target',target) ORDER BY ordinal),'[]'::jsonb)
 INTO invalid,result FROM selected;
 IF invalid THEN RAISE EXCEPTION 'complete typed endpoint scope required' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_local_edges(jsonb,text[],text[],boolean) FROM PUBLIC;

-- Trusted application preparation resolves fields and validates supplied values
-- against one immutable schema index. Native admission separately binds its
-- exact input, current revision, source basis and actor before this projection.
CREATE FUNCTION truss.runtime_owned_application_values(selected_type int,operation_index int,prepared jsonb,prior_props jsonb,prior_retained jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE patch jsonb;props jsonb;retained jsonb;result jsonb;removed_props text[];removed_retained text[];
BEGIN
 patch:=prepared;
 IF patch->'operationIndex' IS DISTINCT FROM to_jsonb(operation_index)
  OR patch->>'typeId' IS DISTINCT FROM selected_type::text
  OR jsonb_typeof(patch->'propsSet') IS DISTINCT FROM 'object'
  OR jsonb_typeof(patch->'retainedSet') IS DISTINCT FROM 'object'
  OR jsonb_typeof(patch->'propsUnset') IS DISTINCT FROM 'array'
  OR jsonb_typeof(patch->'retainedUnset') IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'exact application prepared value inventory required' USING ERRCODE='55000';END IF;
 SELECT coalesce(array_agg(value),ARRAY[]::text[]) INTO removed_props FROM jsonb_array_elements_text(patch->'propsUnset');
 SELECT coalesce(array_agg(value),ARRAY[]::text[]) INTO removed_retained FROM jsonb_array_elements_text(patch->'retainedUnset');
 props:=(coalesce(prior_props,'{}'::jsonb)-removed_props)||(patch->'propsSet');
 retained:=(coalesce(prior_retained,'{}'::jsonb)-removed_retained)||(patch->'retainedSet');
 result:=jsonb_build_object('props',props,'retained',retained);
 IF octet_length(convert_to(result::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'bounded complete object values required' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_application_values(int,int,jsonb,jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_prepare_application(input jsonb,scope jsonb,application_prepared jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE input_operations jsonb;application_operations jsonb;
 nodes jsonb:='{}';edges jsonb:='{}';aliases jsonb:='{}';plans jsonb[]:='{}';
 node_order text[]:='{}';boundary_order text[]:='{}';entry record;selected text;source_ref text;target_ref text;root_ref text;
 operation jsonb;before_nodes jsonb;before_edges jsonb;state jsonb;descendant_state jsonb;prior jsonb;image jsonb;values_image jsonb;ownership jsonb;
 selected_type truss.type_def%ROWTYPE;relation truss.rel_def%ROWTYPE;pin record;identity jsonb;revision int;
 index int:=0;before_count int;descendants text[];descendant text;projection jsonb;deleted jsonb;local_owned jsonb;local_independent jsonb;
 unset_name text;authored jsonb;retained jsonb;order_key jsonb;selected_source_type int;selected_target_type int;plan jsonb;outgoing bigint;incoming bigint;
 retained_nodes text[];retained_edges text[];changed_nodes text[];changed_edges text[];plans_bytes bigint:=2;current_actor oid;resolved_creates jsonb:='{}';
 alias_names text[]:='{}';alias_values text[]:='{}';duplicate_alias_index int;alias_operations jsonb:='{}';
 rootless_creates boolean;created_states jsonb[]:='{}';
 edge_creates boolean;created_edge_states jsonb[]:='{}';initial_edge_count int;edge_member_count int;
 value_updates boolean;updated_states jsonb[]:='{}';updated_references text[]:='{}';
 scope_node_states jsonb[]:='{}';scope_edge_states jsonb[]:='{}';
 scope_node_type int;scope_edge_type int;scope_edge_pin text;outgoing_counts jsonb;incoming_counts jsonb;
 indexed_workspace boolean:=false;workspace_name text;workspace_index_name text;multiplicity_failure text;
BEGIN
 current_actor:=truss.runtime_person(false);
 input_operations:=input->'operations';
 application_operations:=application_prepared->'operations';
 IF jsonb_typeof(input_operations) IS DISTINCT FROM 'array' OR jsonb_array_length(input_operations) NOT BETWEEN 1 AND 1024
  OR jsonb_typeof(scope->'nodes') IS DISTINCT FROM 'object' OR jsonb_typeof(scope->'edges') IS DISTINCT FROM 'object'
  OR octet_length(convert_to(scope::text,'UTF8'))>(CASE WHEN scope->'independentEndpointScope'='true'::jsonb THEN 16777216 ELSE 4194304 END) THEN
  RAISE EXCEPTION 'complete bounded original group scope required' USING ERRCODE='54000';END IF;
 SELECT min(ordered_aliases.operation_index) INTO duplicate_alias_index FROM (
  SELECT valid_aliases.operation_index,row_number() OVER(PARTITION BY valid_aliases.alias_text COLLATE "C" ORDER BY valid_aliases.operation_index) duplicate_ordinal FROM (
   SELECT ordinal-1 operation_index,value->>'alias' alias_text FROM jsonb_array_elements(input_operations) WITH ORDINALITY operations(value,ordinal)
   WHERE value ? 'alias' AND jsonb_typeof(value->'alias')='string'
    AND octet_length(value->>'alias') BETWEEN 1 AND 1024
  ) valid_aliases
 ) ordered_aliases WHERE duplicate_ordinal=2;
 SELECT coalesce(jsonb_object_agg(alias_name,alias_operation),'{}'::jsonb) INTO alias_operations FROM (
  SELECT DISTINCT ON ((value->>'alias') COLLATE "C") value->>'alias' alias_name,
   jsonb_build_object('operation',value->>'operation','operationIndex',ordinal-1,
    'typeDefinitionPin',value->'typeDefinitionPin','relationshipDefinitionPin',value->'relationshipDefinitionPin') alias_operation
  FROM jsonb_array_elements(input_operations) WITH ORDINALITY operations(value,ordinal)
  WHERE jsonb_typeof(value->'alias')='string' AND octet_length(value->>'alias') BETWEEN 1 AND 1024
  ORDER BY (value->>'alias') COLLATE "C",ordinal
 ) original_aliases;
 -- Buffer independent new roots; no operation in this closed shape reads an
 -- earlier node. Keep the same ordered plans and complete final graph checks.
 rootless_creates:=coalesce(scope->'nodes'='{}'::jsonb AND scope->'edges'='{}'::jsonb
  AND scope->'boundary'='{}'::jsonb AND NOT EXISTS(
   SELECT 1 FROM jsonb_array_elements(input_operations) o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_object'
    OR o.value->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb),false);
 -- Pure edge creates cannot read an earlier newly-created edge. Buffer them
 -- and build the complete final map once, avoiding growing JSONB copies/counts.
 edge_creates:=NOT EXISTS(SELECT 1 FROM jsonb_array_elements(input_operations) o
  WHERE o.value->>'operation' IS DISTINCT FROM 'create_edge');
 -- Distinct stored rootless targets cannot observe one another's value edits.
 -- Keep ordinary validation in order; malformed shapes use the general path.
 value_updates:=NOT EXISTS(
  SELECT 1 FROM jsonb_array_elements(input_operations) o
  WHERE o.value->>'operation' IS DISTINCT FROM 'update_object'
   OR o.value ? 'ownershipChange'
   OR o.value->'target'->>'state' IS DISTINCT FROM 'stored'
   OR jsonb_typeof(o.value->'target'->'identity'->'typeId') IS DISTINCT FROM 'string'
   OR jsonb_typeof(o.value->'target'->'identity'->'id') IS DISTINCT FROM 'string')
  AND NOT EXISTS(SELECT 1 FROM jsonb_each(scope->'nodes') n
   WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb
    OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb)
  AND (SELECT count(*)=count(DISTINCT 'stored:'||(o.value->'target'->'identity'->>'typeId')||':'||(o.value->'target'->'identity'->>'id'))
   FROM jsonb_array_elements(input_operations) o);
 revision:=(scope->>'catalogRevision')::int;
 IF revision IS NULL OR revision<1 OR revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1) THEN
  RAISE EXCEPTION 'current admitted group catalog required' USING ERRCODE='55P03';END IF;
 WITH requested AS MATERIALIZED (
  SELECT DISTINCT (value->>'typeDefinitionPin') COLLATE "C" definition_pin FROM jsonb_array_elements(input_operations) operations(value)
  WHERE value->>'operation'='create_object' AND jsonb_typeof(value->'typeDefinitionPin')='string'
 ), matched AS MATERIALIZED (
  SELECT requested.definition_pin,to_jsonb(t) native_type,
   count(*) OVER(PARTITION BY requested.definition_pin) match_count
  FROM requested JOIN truss.runtime_definition_source d ON d.definition_pin COLLATE "C"=requested.definition_pin COLLATE "C"
   AND d.kind='element' AND d.key_id=''
  JOIN truss.type_def t ON t.definition_rev=d.rev AND t.definition_doc_ord=d.ord
   AND t.definition_document_id=d.doc_id AND t.module=d.module_id AND t.element=d.element_id
  WHERE t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL
 )
 SELECT coalesce(jsonb_object_agg(definition_pin,native_type) FILTER(WHERE match_count=1),'{}'::jsonb)
  INTO resolved_creates FROM matched;
 FOR entry IN SELECT key,value FROM jsonb_each(scope->'nodes') ORDER BY (value->>'type_id')::int,(value->>'id')::bigint LOOP
  selected:='stored:'||entry.key;image:=entry.value;
  -- Ordered initial rows share immutable catalog meaning; permissions and
  -- per-object state are still checked on their original paths.
  IF scope_node_type IS NULL OR scope_node_type IS DISTINCT FROM (image->>'type_id')::int THEN
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(image->>'type_id')::int);
   scope_node_type:=(image->>'type_id')::int;
  END IF;
  identity:=jsonb_build_object('id',image->>'id','typeId',image->>'type_id','definitionPin',pin.definition_pin,
   'owner',jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id));
  root_ref:=CASE WHEN image->'root_id'='null'::jsonb THEN NULL ELSE 'stored:'||(image->>'root_type')||':'||(image->>'root_id') END;
  scope_node_states:=array_append(scope_node_states,jsonb_build_object(selected,jsonb_build_object('identity',identity,'image',image-ARRAY['root_id','root_type','updated_at'],
   'root',root_ref,'deleted',false)));node_order:=array_append(node_order,selected);
 END LOOP;
 -- No initial member reads these maps while they are built. Materialize once
 -- instead of copying every previously captured member on each append.
 SELECT coalesce(jsonb_object_agg(member.key,member.value ORDER BY n.ordinal),'{}'::jsonb) INTO nodes
  FROM unnest(scope_node_states) WITH ORDINALITY n(state,ordinal) CROSS JOIN LATERAL jsonb_each(n.state) member;
 FOR entry IN SELECT key,value FROM jsonb_each(scope->'boundary') ORDER BY key COLLATE "C" LOOP
  boundary_order:=array_append(boundary_order,'stored:'||entry.key);
 END LOOP;
 FOR entry IN SELECT key,value FROM jsonb_each(scope->'edges') ORDER BY (value->>'rel_type_id')::int,(value->>'id')::bigint LOOP
  image:=entry.value;
  IF scope_edge_type IS NULL OR scope_edge_type IS DISTINCT FROM (image->>'rel_type_id')::int THEN
   SELECT * INTO STRICT relation FROM truss.rel_def WHERE rel_type_id=(image->>'rel_type_id')::int;
   scope_edge_pin:=truss.runtime_relationship_pin(relation.rel_type_id);
   scope_edge_type:=relation.rel_type_id;
  END IF;
  identity:=jsonb_build_object('id',image->>'id','typeId',image->>'rel_type_id','definitionPin',scope_edge_pin,
   'owner',jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module));
  selected:='stored:'||(image->>'rel_type_id')||':'||(image->>'id');
  scope_edge_states:=array_append(scope_edge_states,jsonb_build_object(selected,jsonb_build_object('identity',identity,'image',image-ARRAY['source_id','source_type','target_id','target_type','order_key','updated_at'],
   'source','stored:'||(image->>'source_type')||':'||(image->>'source_id'),
   'target','stored:'||(image->>'target_type')||':'||(image->>'target_id'),'lifecycle',relation.lifecycle,'deleted',false,
   'orderKey',CASE WHEN image->'order_key'='null'::jsonb THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',image->>'order_key') END)));
 END LOOP;
 SELECT coalesce(jsonb_object_agg(member.key,member.value ORDER BY e.ordinal),'{}'::jsonb) INTO edges
  FROM unnest(scope_edge_states) WITH ORDINALITY e(state,ordinal) CROSS JOIN LATERAL jsonb_each(e.state) member;
 SELECT count(*) INTO initial_edge_count FROM jsonb_each(edges);
 edge_member_count:=initial_edge_count;
 indexed_workspace:=NOT rootless_creates AND NOT value_updates AND NOT edge_creates;
 IF indexed_workspace THEN
  workspace_name:='truss_owned_plan_'||replace(gen_random_uuid()::text,'-','');
  workspace_index_name:=workspace_name||'_source_idx';
  EXECUTE format('CREATE TEMP TABLE %I (member_kind char(1) NOT NULL,member_ref text NOT NULL,member_ordinal integer NOT NULL,created_operation integer,before_operation integer,before_state jsonb,state jsonb,deleted boolean NOT NULL DEFAULT false,root_ref text,source_ref text,target_ref text,lifecycle text,PRIMARY KEY(member_kind,member_ref)) ON COMMIT DROP',workspace_name);
  EXECUTE format('CREATE INDEX %I ON pg_temp.%I(source_ref) WHERE member_kind=''e'' AND NOT deleted',workspace_index_name,workspace_name);
  workspace_index_name:=workspace_name||'_target_idx';
  EXECUTE format('CREATE INDEX %I ON pg_temp.%I(target_ref) WHERE member_kind=''e'' AND NOT deleted',workspace_index_name,workspace_name);
  EXECUTE format('INSERT INTO pg_temp.%I(member_kind,member_ref,member_ordinal,state,deleted,root_ref) SELECT ''n'',r.member_ref,r.ordinal::int,j.value,coalesce((j.value->>''deleted'')::boolean,false),j.value->>''root'' FROM unnest($1::text[]) WITH ORDINALITY r(member_ref,ordinal) JOIN jsonb_each($2) j ON j.key=r.member_ref',workspace_name) USING node_order,nodes;
  EXECUTE format('INSERT INTO pg_temp.%I(member_kind,member_ref,member_ordinal,state,deleted,source_ref,target_ref,lifecycle) SELECT ''e'',key,row_number() OVER(ORDER BY key COLLATE "C")::int,value,coalesce((value->>''deleted'')::boolean,false),value->>''source'',value->>''target'',value->>''lifecycle'' FROM jsonb_each($1)',workspace_name) USING edges;
  EXECUTE format('INSERT INTO pg_temp.%I(member_kind,member_ref,member_ordinal,state,deleted) SELECT ''b'',r.member_ref,r.ordinal::int,j.value,false FROM unnest($1::text[]) WITH ORDINALITY r(member_ref,ordinal) JOIN jsonb_each($2) j ON ''stored:''||j.key=r.member_ref',workspace_name) USING boundary_order,scope->'boundary';
  nodes:='{}'::jsonb;edges:='{}'::jsonb;aliases:='{}'::jsonb;
 END IF;
 FOR operation IN SELECT value FROM jsonb_array_elements(input_operations) LOOP
  IF indexed_workspace THEN before_nodes:='{}'::jsonb;before_edges:='{}'::jsonb;
  ELSE before_nodes:=nodes;before_edges:=edges;END IF;
  changed_nodes:=ARRAY[]::text[];changed_edges:=ARRAY[]::text[];
  IF application_prepared IS NOT NULL AND octet_length(operation::text)>1048576 THEN
   RAISE EXCEPTION 'bounded value simulation input required' USING ERRCODE='54000';END IF;
  IF operation ? 'alias' AND (jsonb_typeof(operation->'alias') IS DISTINCT FROM 'string'
   OR octet_length(operation->>'alias') NOT BETWEEN 1 AND 1024 OR duplicate_alias_index=index) THEN
   RAISE EXCEPTION 'unique bounded original alias required' USING ERRCODE='22023';END IF;
  IF operation->>'operation' IN ('create_object','update_object','delete_object') THEN
   IF operation->>'operation'='create_object' AND resolved_creates ? (operation->>'typeDefinitionPin') THEN
    selected_type:=jsonb_populate_record(NULL::truss.type_def,resolved_creates->(operation->>'typeDefinitionPin'));
    IF NOT truss.runtime_object_values_readable_qualified(selected_type.type_id,current_actor) THEN
     RAISE EXCEPTION 'current property and item interpretation reader required' USING ERRCODE='42501';END IF;
   ELSE
    -- Only alias resolution reads earlier operations; stored/create targets do not.
    selected_type:=truss.runtime_owned_operation_type_qualified(operation,
     CASE WHEN operation->'target'->>'state'='alias' THEN alias_operations END,index,current_actor);
   END IF;
   IF operation->>'operation'='create_object' THEN
    IF operation-ARRAY['operation','typeDefinitionPin','values','ownership','alias']<>'{}'::jsonb
     OR jsonb_typeof(operation->'ownership') IS DISTINCT FROM 'object' THEN
     RAISE EXCEPTION 'closed original object create required' USING ERRCODE='22023';END IF;
    IF cardinality(node_order)>=1024 THEN RAISE EXCEPTION 'bounded complete group objects required' USING ERRCODE='54000';END IF;
    selected:='create:'||index;node_order:=array_append(node_order,selected);
    IF application_prepared IS NOT NULL THEN
     values_image:=truss.runtime_owned_application_values(selected_type.type_id,index,application_operations->index,NULL,NULL);
    ELSE values_image:=truss.owned_object_values(selected_type.type_id,operation,NULL,NULL);END IF;
    state:=jsonb_build_object('identity',jsonb_build_object('id',NULL,'typeId',selected_type.type_id::text,
     'definitionPin',operation->>'typeDefinitionPin','owner',jsonb_build_object('documentId',selected_type.document_id,'moduleId',selected_type.module)),
     'image',jsonb_build_object('id',NULL,'type_id',selected_type.type_id,'props',values_image->'props',
      'retained',nullif(values_image->'retained','{}'::jsonb),'rev',revision,'ver',1),
     'createIndex',index,'root',NULL,'deleted',false);
    IF indexed_workspace THEN PERFORM truss.runtime_owned_workspace_insert(workspace_name,'n',selected,cardinality(node_order),index,state);END IF;
    ownership:=operation->'ownership';
   ELSE
    IF indexed_workspace THEN selected:=truss.runtime_owned_workspace_reference(operation->'target',workspace_name,'n',index);
     state:=truss.runtime_owned_workspace_state(workspace_name,'n',selected);
    ELSE selected:=truss.runtime_owned_reference(operation->'target',aliases,nodes);state:=truss.runtime_owned_workspace_state_or(workspace_name,'n',selected,nodes);END IF;
    IF state->'identity'->>'typeId' IS DISTINCT FROM selected_type.type_id::text THEN RAISE EXCEPTION 'original object reference type required' USING ERRCODE='22023';END IF;
    IF operation ? 'expectedVersion' AND (jsonb_typeof(operation->'expectedVersion') IS DISTINCT FROM 'string'
     OR operation->>'expectedVersion' IS DISTINCT FROM state->'image'->>'ver') THEN
     RAISE EXCEPTION 'expected object version failed' USING ERRCODE='P1003';END IF;
    ownership:=operation->'ownershipChange';
   END IF;
   IF operation->>'operation'='delete_object' THEN
    IF operation-ARRAY['operation','target','expectedVersion']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed object delete required' USING ERRCODE='22023';END IF;
     IF indexed_workspace THEN
      deleted:=truss.runtime_owned_workspace_delete_plan(workspace_name,selected);
     ELSE
      local_owned:=truss.runtime_owned_local_edges(edges,node_order,boundary_order,true);
      local_independent:=truss.runtime_owned_local_edges(edges,node_order,boundary_order,false);
      deleted:=truss.owned_delete_projection(cardinality(node_order),local_owned,local_independent,array_position(node_order,selected)-1);
     END IF;
    FOR entry IN SELECT value FROM jsonb_array_elements(deleted->'deletedNodes') LOOP
      descendant:=CASE WHEN indexed_workspace THEN entry.value#>>'{}' ELSE node_order[(entry.value#>>'{}')::int+1] END;
      state:=CASE WHEN indexed_workspace THEN truss.runtime_owned_workspace_state_or(workspace_name,'n',descendant,nodes) ELSE nodes->descendant END;
      IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'object version exhausted' USING ERRCODE='54000';END IF;
     changed_nodes:=array_append(changed_nodes,descendant);
      state:=jsonb_set(state,'{deleted}','true'::jsonb);
      nodes:=truss.runtime_owned_workspace_write(workspace_name,'n',descendant,index,state,nodes);
    END LOOP;
     IF indexed_workspace THEN
      FOR entry IN SELECT value FROM jsonb_array_elements_text(deleted->'deletedEdges') LOOP
       descendant:=entry.value;state:=truss.runtime_owned_workspace_state_or(workspace_name,'e',descendant,edges);
       IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
       changed_edges:=array_append(changed_edges,descendant);state:=jsonb_set(state,'{deleted}','true'::jsonb);
       edges:=truss.runtime_owned_workspace_write(workspace_name,'e',descendant,index,state,edges);
      END LOOP;
     ELSE
      FOR entry IN SELECT key,value FROM jsonb_each(edges) WHERE value->'deleted'='false'::jsonb LOOP
       IF nodes->(entry.value->>'source')->'deleted'='true'::jsonb OR nodes->(entry.value->>'target')->'deleted'='true'::jsonb THEN
        IF (entry.value->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
        changed_edges:=array_append(changed_edges,entry.key);edges:=jsonb_set(edges,ARRAY[entry.key,'deleted'],'true'::jsonb);
       END IF;
      END LOOP;
     END IF;
   ELSE
    IF operation->>'operation'='update_object' THEN
     IF operation-ARRAY['operation','target','set','unset','expectedVersion','ownershipChange']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed object update required' USING ERRCODE='22023';END IF;
     IF application_prepared IS NOT NULL AND state->'image'->>'rev'=revision::text THEN
      values_image:=truss.runtime_owned_application_values(selected_type.type_id,index,application_operations->index,
       state->'image'->'props',nullif(state->'image'->'retained','null'::jsonb));
     ELSE values_image:=truss.runtime_owned_object_value_delta(selected_type.type_id,operation,state->'image'->'props',nullif(state->'image'->'retained','null'::jsonb),(state->'image'->>'id')::bigint);END IF;
     state:=jsonb_set(state,'{image,props}',values_image->'props');
     state:=jsonb_set(state,'{image,retained}',coalesce(nullif(values_image->'retained','{}'::jsonb),'null'::jsonb));
    END IF;
    IF ownership IS NOT NULL THEN
     IF ownership='{"state":"rootless"}'::jsonb THEN root_ref:=NULL;
     ELSIF ownership->>'state'='owned' AND ownership-ARRAY['state','root']='{}'::jsonb THEN
      IF indexed_workspace THEN root_ref:=truss.runtime_owned_workspace_reference(ownership->'root',workspace_name,'n',index);
      ELSE root_ref:=truss.runtime_owned_reference(ownership->'root',aliases,nodes);END IF;
      IF root_ref=selected OR truss.runtime_owned_workspace_state_or(workspace_name,'n',root_ref,nodes)->'root'<>'null'::jsonb THEN RAISE EXCEPTION 'selected live rootless aggregate root required' USING ERRCODE='22023';END IF;
     ELSE RAISE EXCEPTION 'explicit exact ownership selection required' USING ERRCODE='22023';END IF;
     IF state->'root' IS DISTINCT FROM coalesce(to_jsonb(root_ref),'null'::jsonb) THEN
      IF indexed_workspace THEN descendants:=truss.runtime_owned_workspace_descendants(workspace_name,selected);
      ELSE
       descendants:=ARRAY[selected];
       LOOP
        before_count:=cardinality(descendants);
        SELECT array_agg(DISTINCT reference COLLATE "C" ORDER BY reference COLLATE "C") INTO descendants FROM (
         SELECT unnest(descendants) AS reference UNION ALL SELECT value->>'target' FROM jsonb_each(edges)
          WHERE value->'deleted'='false'::jsonb AND value->>'lifecycle'='owned' AND value->>'source'=ANY(descendants)) expanded;
        EXIT WHEN cardinality(descendants)=before_count;
       END LOOP;
      END IF;
      IF root_ref=ANY(descendants) THEN RAISE EXCEPTION 'aggregate root outside moved subtree required' USING ERRCODE='22023';END IF;
      FOR descendant IN SELECT unnest(descendants) LOOP
        IF descendant=selected THEN state:=jsonb_set(state,'{root}',coalesce(to_jsonb(root_ref),'null'::jsonb));
        ELSE changed_nodes:=array_append(changed_nodes,descendant);descendant_state:=truss.runtime_owned_workspace_state_or(workspace_name,'n',descendant,nodes);
         descendant_state:=jsonb_set(descendant_state,'{root}',coalesce(to_jsonb(coalesce(root_ref,selected)),'null'::jsonb));
         nodes:=truss.runtime_owned_workspace_write(workspace_name,'n',descendant,index,descendant_state,nodes);END IF;
      END LOOP;
     END IF;
    END IF;
    changed_nodes:=array_append(changed_nodes,selected);
    IF rootless_creates THEN created_states:=array_append(created_states,state);
    -- Ordinary updates install their final versioned member below; no-op
    -- updates already have that exact state in the working graph.
     ELSIF operation->>'operation'<>'update_object' OR operation ? 'ownershipChange' THEN
      nodes:=truss.runtime_owned_workspace_write(workspace_name,'n',selected,index,state,nodes);END IF;
    IF operation->>'operation'='update_object' AND NOT (operation ? 'ownershipChange') THEN
     IF state IS DISTINCT FROM truss.runtime_owned_workspace_state_at_or(workspace_name,'n',selected,index,true,before_nodes) THEN
      IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'object version exhausted' USING ERRCODE='54000';END IF;
      state:=jsonb_set(state,'{image,ver}',to_jsonb((state->'image'->>'ver')::bigint+1));
      IF value_updates THEN state:=jsonb_set(state,'{image,rev}',to_jsonb(revision));
      ELSE state:=jsonb_set(state,'{image,rev}',to_jsonb(revision));nodes:=truss.runtime_owned_workspace_write(workspace_name,'n',selected,index,state,nodes);END IF;
     END IF;
     IF value_updates THEN
      updated_references:=array_append(updated_references,selected);
      updated_states:=array_append(updated_states,state);
     END IF;
    ELSIF operation->>'operation'<>'create_object' THEN
    FOR entry IN SELECT reference key,truss.runtime_owned_workspace_state_or(workspace_name,'n',reference,nodes) value FROM (SELECT DISTINCT unnest(changed_nodes) reference) touched LOOP
     IF truss.runtime_owned_workspace_state_at_or(workspace_name,'n',entry.key,index,true,before_nodes) IS NOT NULL
      AND entry.value IS DISTINCT FROM truss.runtime_owned_workspace_state_at_or(workspace_name,'n',entry.key,index,true,before_nodes) THEN
      IF (entry.value->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'object version exhausted' USING ERRCODE='54000';END IF;
      state:=jsonb_set(entry.value,'{image,ver}',to_jsonb((entry.value->'image'->>'ver')::bigint+1));
      state:=jsonb_set(state,'{image,rev}',to_jsonb(revision));nodes:=truss.runtime_owned_workspace_write(workspace_name,'n',entry.key,index,state,nodes);
     END IF;
    END LOOP;
    END IF;
   END IF;
  ELSIF operation->>'operation' IN ('create_edge','update_edge','delete_edge') THEN
   relation:=truss.runtime_operation_relationship(operation,alias_operations,index);
   IF relation.lifecycle NOT IN ('owned','independent') OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL THEN
    RAISE EXCEPTION 'supported directed relationship required' USING ERRCODE='0A000';END IF;
   IF operation->>'operation'='create_edge' THEN
    IF operation-ARRAY['operation','relationshipDefinitionPin','source','target','values','orderKey','alias']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge create required' USING ERRCODE='22023';END IF;
    IF (CASE WHEN edge_creates THEN initial_edge_count+index ELSE edge_member_count END)>=1024 THEN RAISE EXCEPTION 'bounded complete group edges required' USING ERRCODE='54000';END IF;
    selected:='create:'||index;
    IF indexed_workspace THEN
     source_ref:=truss.runtime_owned_workspace_reference(operation->'source',workspace_name,'n',index);
     target_ref:=truss.runtime_owned_workspace_reference(operation->'target',workspace_name,'n',index);
    ELSE
     source_ref:=truss.runtime_owned_reference(operation->'source',aliases,nodes);
     target_ref:=truss.runtime_owned_reference(operation->'target',aliases,nodes);
    END IF;
    retained:='{}';authored:=operation->'values';order_key:=operation->'orderKey';
    state:=jsonb_build_object('identity',jsonb_build_object('id',NULL,'typeId',relation.rel_type_id::text,
     'definitionPin',operation->>'relationshipDefinitionPin','owner',jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module)),
     'image',jsonb_build_object('id',NULL,'rel_type_id',relation.rel_type_id,'props','{}'::jsonb,'retained',NULL,'ver',1,'rev',revision),
     'createIndex',index,'lifecycle',relation.lifecycle,'deleted',false);
    IF indexed_workspace THEN PERFORM truss.runtime_owned_workspace_insert(workspace_name,'e',selected,edge_member_count+1,index,state);edge_member_count:=edge_member_count+1;END IF;
   ELSE
    IF indexed_workspace THEN selected:=truss.runtime_owned_workspace_reference(operation->'target',workspace_name,'e',index);
     state:=truss.runtime_owned_workspace_state(workspace_name,'e',selected);
    ELSE selected:=truss.runtime_owned_reference(operation->'target',aliases,edges);state:=edges->selected;END IF;
    IF state->'identity'->>'typeId' IS DISTINCT FROM relation.rel_type_id::text THEN RAISE EXCEPTION 'original edge reference type required' USING ERRCODE='22023';END IF;
    IF operation ? 'expectedVersion' AND (jsonb_typeof(operation->'expectedVersion') IS DISTINCT FROM 'string'
     OR operation->>'expectedVersion' IS DISTINCT FROM state->'image'->>'ver') THEN RAISE EXCEPTION 'expected edge version failed' USING ERRCODE='P1003';END IF;
    source_ref:=state->>'source';target_ref:=state->>'target';retained:=coalesce(nullif(state->'image'->'retained','null'::jsonb),'{}');
    order_key:=state->'orderKey';
    IF order_key IS NULL THEN order_key:=CASE WHEN state->'image'->'order_key'='null'::jsonb THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',state->'image'->>'order_key') END;END IF;
    IF operation->>'operation'='delete_edge' THEN
     IF operation-ARRAY['operation','target','expectedVersion']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge delete required' USING ERRCODE='22023';END IF;
     IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
     changed_edges:=array_append(changed_edges,selected);
     state:=jsonb_set(state,'{deleted}','true'::jsonb);edges:=truss.runtime_owned_workspace_write(workspace_name,'e',selected,index,state,edges);
    ELSE
     IF operation-ARRAY['operation','target','set','unset','expectedVersion','endpointChange','orderKeyChange']<>'{}'::jsonb
      OR jsonb_typeof(operation->'unset') IS DISTINCT FROM 'array' OR jsonb_array_length(operation->'unset')>1024
      OR EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'unset') u WHERE jsonb_typeof(value) IS DISTINCT FROM 'string' OR octet_length(value#>>'{}') NOT BETWEEN 1 AND 4096)
      OR jsonb_array_length(operation->'unset')<>(SELECT count(DISTINCT value) FROM jsonb_array_elements(operation->'unset')) THEN RAISE EXCEPTION 'closed edge update required' USING ERRCODE='22023';END IF;
     retained:=retained-ARRAY(SELECT value#>>'{}' FROM jsonb_array_elements(operation->'unset'));
     authored:=operation->'set';
     IF operation ? 'endpointChange' THEN
      IF jsonb_typeof(operation->'endpointChange') IS DISTINCT FROM 'object' OR (operation->'endpointChange')-ARRAY['source','target']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed endpoint change required' USING ERRCODE='22023';END IF;
      IF indexed_workspace THEN
       source_ref:=truss.runtime_owned_workspace_reference(operation->'endpointChange'->'source',workspace_name,'n',index);
       target_ref:=truss.runtime_owned_workspace_reference(operation->'endpointChange'->'target',workspace_name,'n',index);
      ELSE
       source_ref:=truss.runtime_owned_reference(operation->'endpointChange'->'source',aliases,nodes);
       target_ref:=truss.runtime_owned_reference(operation->'endpointChange'->'target',aliases,nodes);
      END IF;
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
    SELECT retained||coalesce(jsonb_object_agg(v.value->>'name',truss.canonical_flat_cell(v.value->'value')),'{}'::jsonb)
     INTO retained FROM jsonb_array_elements(authored) v;
    IF octet_length(convert_to(retained::text,'UTF8'))>1048576 THEN RAISE EXCEPTION 'bounded edge values required' USING ERRCODE='54000';END IF;
    IF (order_key='{"state":"null"}'::jsonb OR order_key->>'state'='text' AND jsonb_typeof(order_key->'text')='string'
     AND order_key-ARRAY['state','text']='{}'::jsonb AND octet_length(order_key->>'text')<=4096) IS NOT TRUE THEN RAISE EXCEPTION 'exact bounded order key required' USING ERRCODE='22023';END IF;
    selected_source_type:=(truss.runtime_owned_workspace_state_or(workspace_name,'n',source_ref,nodes)->'identity'->>'typeId')::int;selected_target_type:=(truss.runtime_owned_workspace_state_or(workspace_name,'n',target_ref,nodes)->'identity'->>'typeId')::int;
    IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=selected_source_type AND target_type=selected_target_type) THEN RAISE EXCEPTION 'admitted endpoint pair required' USING ERRCODE='22023';END IF;
    state:=state||jsonb_build_object('source',source_ref,'target',target_ref,'orderKey',order_key);
    state:=jsonb_set(state,'{image,retained}',coalesce(nullif(retained,'{}'::jsonb),'null'::jsonb));
    IF truss.runtime_owned_workspace_state_at_or(workspace_name,'e',selected,index,true,before_edges) IS NOT NULL
     AND state IS DISTINCT FROM truss.runtime_owned_workspace_state_at_or(workspace_name,'e',selected,index,true,before_edges) THEN
     IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
     state:=jsonb_set(state,'{image,ver}',to_jsonb((state->'image'->>'ver')::bigint+1));state:=jsonb_set(state,'{image,rev}',to_jsonb(revision));
    END IF;
    changed_edges:=array_append(changed_edges,selected);
    IF edge_creates THEN created_edge_states:=array_append(created_edge_states,state);
    ELSE edges:=truss.runtime_owned_workspace_write(workspace_name,'e',selected,index,state,edges);END IF;
   END IF;
  ELSE RAISE EXCEPTION 'supported original graph operation required' USING ERRCODE='0A000';END IF;
  IF operation ? 'alias' THEN
   IF indexed_workspace THEN PERFORM truss.runtime_owned_workspace_insert(workspace_name,'a',operation->>'alias',index,index,
    jsonb_build_object('source',selected,'deleted',false));
   ELSE alias_names:=array_append(alias_names,operation->>'alias');alias_values:=array_append(alias_values,selected);END IF;
  END IF;
  IF indexed_workspace THEN
   SELECT coalesce(array_agg(DISTINCT reference),'{}'::text[]) INTO retained_nodes FROM (
    SELECT unnest(changed_nodes) reference
    UNION SELECT selected WHERE operation->>'operation' IN ('create_object','update_object','delete_object')
    UNION SELECT truss.runtime_owned_workspace_state_at(workspace_name,'e',reference,index,true)->>'source' FROM unnest(changed_edges) c(reference)
    UNION SELECT truss.runtime_owned_workspace_state_at(workspace_name,'e',reference,index,true)->>'target' FROM unnest(changed_edges) c(reference)
    UNION SELECT truss.runtime_owned_workspace_state(workspace_name,'e',reference)->>'source' FROM unnest(changed_edges) c(reference)
    UNION SELECT truss.runtime_owned_workspace_state(workspace_name,'e',reference)->>'target' FROM unnest(changed_edges) c(reference)
   ) refs WHERE reference IS NOT NULL;
   SELECT coalesce(array_agg(DISTINCT reference),'{}'::text[]) INTO retained_nodes FROM (
    SELECT unnest(retained_nodes) reference
    UNION SELECT truss.runtime_owned_workspace_state_at(workspace_name,'n',reference,index,true)->>'root' FROM unnest(retained_nodes) n(reference)
    UNION SELECT truss.runtime_owned_workspace_state(workspace_name,'n',reference)->>'root' FROM unnest(retained_nodes) n(reference)
   ) roots WHERE reference IS NOT NULL;
   before_nodes:=truss.runtime_owned_workspace_map(workspace_name,'n',index,retained_nodes,true);
   nodes:=truss.runtime_owned_workspace_map(workspace_name,'n',index,retained_nodes,false);
   before_edges:=truss.runtime_owned_workspace_map(workspace_name,'e',index,changed_edges,true);
   edges:=truss.runtime_owned_workspace_map(workspace_name,'e',index,changed_edges,false);
  END IF;
  -- Keep one working graph for ordered simulation. Persist only this step's
  -- changed members and identity witnesses; full graph projection is ephemeral
  -- after the ordered operation plans have been assembled.
  IF rootless_creates AND index=jsonb_array_length(input_operations)-1 THEN
   SELECT jsonb_object_agg(node_order[n.ordinal::int],n.state) INTO nodes
    FROM unnest(created_states) WITH ORDINALITY n(state,ordinal);
   before_nodes:=nodes-selected;
  ELSIF value_updates AND index=jsonb_array_length(input_operations)-1 THEN
   SELECT nodes||coalesce(jsonb_object_agg(updated_references[n.ordinal::int],n.state)
     FILTER (WHERE n.ordinal<cardinality(updated_states)),'{}'::jsonb),
    nodes||jsonb_object_agg(updated_references[n.ordinal::int],n.state)
    INTO before_nodes,nodes FROM unnest(updated_states) WITH ORDINALITY n(state,ordinal);
  END IF;
  IF edge_creates AND index=jsonb_array_length(input_operations)-1 THEN
   SELECT edges||jsonb_object_agg('create:'||(e.ordinal-1)::text,e.state) INTO edges
    FROM unnest(created_edge_states) WITH ORDINALITY e(state,ordinal);
   before_edges:=edges-selected;
  END IF;
  IF value_updates THEN
   plan:=jsonb_build_object('beforeNodes',jsonb_build_object(selected,truss.runtime_owned_workspace_state_at_or(workspace_name,'n',selected,index,true,before_nodes)),
    'afterNodes',jsonb_build_object(selected,state),'beforeEdges','{}'::jsonb,'afterEdges','{}'::jsonb);
  ELSIF rootless_creates THEN
   plan:=jsonb_build_object('beforeNodes','{}'::jsonb,'afterNodes',jsonb_build_object(selected,state),
    'beforeEdges','{}'::jsonb,'afterEdges','{}'::jsonb);
  ELSIF edge_creates THEN
   SELECT array_agg(DISTINCT reference) INTO retained_nodes FROM unnest(ARRAY[
    source_ref,target_ref,truss.runtime_owned_workspace_state_or(workspace_name,'n',source_ref,nodes)->>'root',truss.runtime_owned_workspace_state_or(workspace_name,'n',target_ref,nodes)->>'root']) r(reference) WHERE reference IS NOT NULL;
   SELECT coalesce(jsonb_object_agg(r.reference,nodes->r.reference),'{}'::jsonb) INTO before_nodes
    FROM unnest(retained_nodes) r(reference) WHERE nodes ? r.reference;
   plan:=jsonb_build_object('beforeNodes',before_nodes,'afterNodes',before_nodes,
    'beforeEdges','{}'::jsonb,'afterEdges',jsonb_build_object(selected,state));
  ELSIF operation->>'operation'='create_object'
   OR (operation->>'operation'='update_object' AND NOT (operation ? 'ownershipChange')) THEN
   -- These operations change one object only. Use point lookups for its root
   -- witnesses instead of rescanning the complete growing working graph.
   SELECT array_agg(DISTINCT reference) INTO retained_nodes FROM unnest(ARRAY[
    selected,truss.runtime_owned_workspace_state_at_or(workspace_name,'n',selected,index,true,before_nodes)->>'root',truss.runtime_owned_workspace_state_or(workspace_name,'n',selected,nodes)->>'root']) r(reference) WHERE reference IS NOT NULL;
   plan:=jsonb_build_object(
    'beforeNodes',(SELECT coalesce(jsonb_object_agg(r.reference,before_nodes->r.reference),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE before_nodes ? r.reference),
    'afterNodes',(SELECT coalesce(jsonb_object_agg(r.reference,nodes->r.reference),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE nodes ? r.reference),
    'beforeEdges','{}'::jsonb,'afterEdges','{}'::jsonb);
  ELSE
   SELECT coalesce(array_agg(reference),'{}'::text[]) INTO retained_edges FROM (
    SELECT reference FROM unnest(changed_edges) e(reference)
     WHERE truss.runtime_owned_workspace_state_at_or(workspace_name,'e',reference,index,true,before_edges) IS DISTINCT FROM truss.runtime_owned_workspace_state_or(workspace_name,'e',reference,edges)
    UNION SELECT selected WHERE operation->>'operation' IN ('create_edge','update_edge','delete_edge')
   ) changed;
   SELECT coalesce(array_agg(reference),'{}'::text[]) INTO retained_nodes FROM (
    SELECT reference FROM unnest(changed_nodes) n(reference)
     WHERE truss.runtime_owned_workspace_state_at_or(workspace_name,'n',reference,index,true,before_nodes) IS DISTINCT FROM truss.runtime_owned_workspace_state_or(workspace_name,'n',reference,nodes)
    UNION SELECT selected WHERE operation->>'operation' IN ('create_object','update_object','delete_object')
    UNION SELECT truss.runtime_owned_workspace_state_at_or(workspace_name,'e',reference,index,true,before_edges)->>'source' FROM unnest(retained_edges) e(reference)
    UNION SELECT truss.runtime_owned_workspace_state_at_or(workspace_name,'e',reference,index,true,before_edges)->>'target' FROM unnest(retained_edges) e(reference)
    UNION SELECT truss.runtime_owned_workspace_state_or(workspace_name,'e',reference,edges)->>'source' FROM unnest(retained_edges) e(reference)
    UNION SELECT truss.runtime_owned_workspace_state_or(workspace_name,'e',reference,edges)->>'target' FROM unnest(retained_edges) e(reference)
   ) changed WHERE reference IS NOT NULL;
   SELECT coalesce(array_agg(reference),'{}'::text[]) INTO retained_nodes FROM (
    SELECT unnest(retained_nodes) reference
    UNION SELECT truss.runtime_owned_workspace_state_at_or(workspace_name,'n',reference,index,true,before_nodes)->>'root' FROM unnest(retained_nodes) n(reference)
    UNION SELECT truss.runtime_owned_workspace_state_or(workspace_name,'n',reference,nodes)->>'root' FROM unnest(retained_nodes) n(reference)
   ) witnesses WHERE reference IS NOT NULL;
   plan:=jsonb_build_object(
    'beforeNodes',(SELECT coalesce(jsonb_object_agg(reference,truss.runtime_owned_workspace_state_at_or(workspace_name,'n',reference,index,true,before_nodes)),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE before_nodes ? reference),
    'afterNodes',(SELECT coalesce(jsonb_object_agg(reference,truss.runtime_owned_workspace_state_or(workspace_name,'n',reference,nodes)),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE nodes ? reference),
    'beforeEdges',(SELECT coalesce(jsonb_object_agg(reference,truss.runtime_owned_workspace_state_at_or(workspace_name,'e',reference,index,true,before_edges)),'{}'::jsonb) FROM unnest(retained_edges) r(reference) WHERE before_edges ? reference),
    'afterEdges',(SELECT coalesce(jsonb_object_agg(reference,truss.runtime_owned_workspace_state_or(workspace_name,'e',reference,edges)),'{}'::jsonb) FROM unnest(retained_edges) r(reference) WHERE edges ? reference));
  END IF;
  plan:=plan||jsonb_build_object('profile','truss-owned-operation-plan/0.2',
   'operationIndex',index,'operation',operation,'primary',selected);
  plans_bytes:=plans_bytes+octet_length(convert_to(plan::text,'UTF8'))+CASE WHEN index=0 THEN 0 ELSE 2 END;
  IF plans_bytes>33554432 THEN RAISE EXCEPTION 'bounded whole group execution inventory required' USING ERRCODE='54000';END IF;
  plans:=array_append(plans,plan);
  index:=index+1;
 END LOOP;
 IF indexed_workspace THEN aliases:=truss.runtime_owned_workspace_aliases(workspace_name);
 ELSIF cardinality(alias_names)>0 THEN
  SELECT jsonb_object_agg(alias_name,alias_value ORDER BY ordinal) INTO aliases
   FROM unnest(alias_names,alias_values) WITH ORDINALITY pairs(alias_name,alias_value,ordinal);
 END IF;
 IF indexed_workspace THEN
  nodes:=truss.runtime_owned_workspace_map(workspace_name,'n',index,NULL,false);
  edges:=truss.runtime_owned_workspace_map(workspace_name,'e',index,NULL,false);
 END IF;
 SELECT coalesce(array_agg(reference ORDER BY ordinal),'{}'::text[]) INTO node_order FROM unnest(node_order) WITH ORDINALITY n(reference,ordinal) WHERE truss.runtime_owned_workspace_state_or(workspace_name,'n',reference,nodes)->'deleted'='false'::jsonb;
 local_owned:=truss.runtime_owned_local_edges(edges,node_order,boundary_order,true);
 projection:=truss.owned_forest_projection(cardinality(node_order),local_owned);
 FOR entry IN SELECT value FROM jsonb_array_elements(projection) LOOP
  selected:=node_order[(entry.value->>'node')::int+1];root_ref:=CASE WHEN entry.value->'root'='null'::jsonb THEN NULL ELSE node_order[(entry.value->>'root')::int+1] END;
  IF truss.runtime_owned_workspace_state_or(workspace_name,'n',selected,nodes)->'root' IS DISTINCT FROM coalesce(to_jsonb(root_ref),'null'::jsonb) THEN RAISE EXCEPTION 'final ownership graph requires explicit root change' USING ERRCODE='22023';END IF;
 END LOOP;
 -- The final simulated edges are immutable here. Count each live edge once
 -- per direction rather than scanning the full map for every node/relation.
 WITH counts AS (
  SELECT e.value->'identity'->>'typeId' relation_id,endpoint.direction,endpoint.reference,count(*) amount
  FROM jsonb_each(edges) e CROSS JOIN LATERAL
   (VALUES ('outgoing',e.value->>'source'),('incoming',e.value->>'target')) endpoint(direction,reference)
  WHERE e.value->'deleted'='false'::jsonb
  GROUP BY e.value->'identity'->>'typeId',endpoint.direction,endpoint.reference)
 SELECT coalesce(jsonb_object_agg(jsonb_build_array(relation_id,reference)::text,amount)
   FILTER(WHERE direction='outgoing'),'{}'::jsonb),
  coalesce(jsonb_object_agg(jsonb_build_array(relation_id,reference)::text,amount)
   FILTER(WHERE direction='incoming'),'{}'::jsonb)
 INTO outgoing_counts,incoming_counts FROM counts;
 -- Maximums apply only to actual nonempty endpoint groups. Zero-edge
 -- checks are necessary only for positive minimums; do not cross every node
 -- with every unbounded or max-only relationship in the catalog.
 WITH live_nodes AS MATERIALIZED (
  SELECT n.reference,(nodes->n.reference->'identity'->>'typeId')::int type_id FROM unnest(node_order) n(reference)),
 actual_counts AS (
  SELECT c.key::jsonb coordinate,c.value::bigint amount,'outgoing'::text direction FROM jsonb_each_text(outgoing_counts) c
  UNION ALL SELECT c.key::jsonb,c.value::bigint,'incoming'::text FROM jsonb_each_text(incoming_counts) c),
 violations AS (
  SELECT 'final '||c.direction||' multiplicity failed' reason FROM actual_counts c
   JOIN live_nodes n ON n.reference=c.coordinate->>1
   JOIN truss.rel_def r ON r.rel_type_id=(c.coordinate->>0)::int AND r.retired_rev IS NULL
   WHERE c.amount>CASE c.direction WHEN 'outgoing' THEN r.target_max ELSE r.source_max END
  UNION ALL
  SELECT 'final outgoing multiplicity failed' FROM live_nodes n JOIN truss.rel_endpoint e ON e.source_type=n.type_id
   JOIN truss.rel_def r USING(rel_type_id) WHERE r.retired_rev IS NULL AND r.target_min>0
    AND coalesce((outgoing_counts->>jsonb_build_array(r.rel_type_id::text,n.reference)::text)::bigint,0)<r.target_min
  UNION ALL
  SELECT 'final incoming multiplicity failed' FROM live_nodes n JOIN truss.rel_endpoint e ON e.target_type=n.type_id
   JOIN truss.rel_def r USING(rel_type_id) WHERE r.retired_rev IS NULL AND r.source_min>0
    AND coalesce((incoming_counts->>jsonb_build_array(r.rel_type_id::text,n.reference)::text)::bigint,0)<r.source_min)
 SELECT reason INTO multiplicity_failure FROM violations LIMIT 1;
 IF FOUND THEN RAISE EXCEPTION '%',multiplicity_failure USING ERRCODE='P1005';END IF;
 plan:=jsonb_build_object('profile','truss-owned-group-plan/0.1','catalogRevision',revision,
  'initialScope',scope,'operations',to_jsonb(plans),'aliases',aliases);
 IF octet_length(convert_to(plan::text,'UTF8'))>33554432 THEN RAISE EXCEPTION 'bounded complete group execution inventory required' USING ERRCODE='54000';END IF;
 IF indexed_workspace THEN EXECUTE format('DROP TABLE pg_temp.%I',workspace_name);END IF;
 RETURN plan;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_prepare_application(jsonb,jsonb,jsonb) FROM PUBLIC;

-- The independently supported SQL/general route retains its original validator.
CREATE FUNCTION truss.runtime_owned_prepare(input jsonb,scope jsonb) RETURNS jsonb
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT truss.runtime_owned_prepare_application(input,scope,NULL);
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_prepare(jsonb,jsonb) FROM PUBLIC;


-- This is the execution entry's native preflight, not a caller-supplied plan.
-- Admission is before predicate/key/row locks. No canonical graph rows change.
CREATE FUNCTION truss.runtime_owned_capture_application(selected_attempt uuid,application_prepared jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE observed_operation_count int;input_operations jsonb;
 attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;observed jsonb;locked jsonb;
 inventory jsonb;entry jsonb;expected_operation jsonb;actual_operation jsonb;owner record;selected_type int;relation truss.rel_def%ROWTYPE;endpoint_owner record;retained_bytes bigint:=0;current_actor oid;
 original_projection_problem boolean;compact_updates boolean;application_operations jsonb;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 input_operations:=input->'operations';
 current_actor:=truss.runtime_person(false);
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
  OR attempt.actor_oid IS DISTINCT FROM current_actor OR attempt.complete
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
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module_id,current_actor);
 END LOOP;
 FOR owner IN SELECT document_id,module_id FROM (SELECT DISTINCT value->'definition'->>'document_id' document_id,
  value->'definition'->>'module' module_id FROM jsonb_each(observed->'boundary')) distinct_owners
  ORDER BY document_id COLLATE "C",module_id COLLATE "C" LOOP
  IF NOT truss.runtime_can_read_qualified(owner.document_id,owner.module_id,current_actor) THEN
   RAISE EXCEPTION 'current outside endpoint reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 -- Implicit descendant values and zero-edge multiplicity checks require the
 -- same original readers as explicit operations, before graph exclusion.
 FOR selected_type IN SELECT type_id FROM (
  SELECT DISTINCT (value->>'type_id')::int type_id FROM jsonb_each(observed->'types')
  -- Stored update/delete targets are already in observed.types; alias targets
  -- come from the CREATE pins below. Original reference admission remains in
  -- input_scope and the ordered planner, so this type-set pass adds no new type.
  -- This is a type set, not operation admission. Resolve each exact CREATE pin
  -- once using its first original operation; all per-operation admission,
  -- execution and settlement checks remain on their original paths.
  UNION SELECT (truss.runtime_owned_operation_type_qualified(value,input_operations,(ordinal-1)::int,current_actor)).type_id
   FROM (SELECT DISTINCT ON ((value->>'typeDefinitionPin') COLLATE "C") value,ordinal
    FROM jsonb_array_elements(input_operations) WITH ORDINALITY o(value,ordinal)
    WHERE value->>'operation'='create_object'
    ORDER BY (value->>'typeDefinitionPin') COLLATE "C",ordinal) creations
 ) affected_types ORDER BY type_id LOOP
  IF truss.runtime_object_values_readable_qualified(selected_type,current_actor) IS NOT TRUE THEN
   RAISE EXCEPTION 'complete affected property and item readers required' USING ERRCODE='42501';END IF;
  FOR relation IN WITH selected_relations AS MATERIALIZED (
   SELECT DISTINCT rel_type_id FROM truss.rel_endpoint WHERE source_type=selected_type OR target_type=selected_type)
   SELECT r.* FROM selected_relations s JOIN truss.rel_def r USING(rel_type_id)
   WHERE r.retired_rev IS NULL ORDER BY r.rel_type_id LOOP
   IF relation.source_min=0 AND relation.source_max IS NULL AND relation.target_min=0 AND relation.target_max IS NULL THEN CONTINUE;END IF;
   IF NOT truss.runtime_can_read_qualified(relation.document_id,relation.module,current_actor) THEN
    RAISE EXCEPTION 'counted relationship reader required' USING ERRCODE='42501';END IF;
   FOR endpoint_owner IN SELECT DISTINCT t.document_id,t.module FROM truss.rel_endpoint e
    JOIN truss.type_def t ON t.type_id IN(e.source_type,e.target_type) WHERE e.rel_type_id=relation.rel_type_id LOOP
    IF NOT truss.runtime_can_read_qualified(endpoint_owner.document_id,endpoint_owner.module,current_actor) THEN
     RAISE EXCEPTION 'counted relationship endpoint reader required' USING ERRCODE='42501';END IF;
   END LOOP;
  END LOOP;
 END LOOP;
 -- Every graph writer joins this same exclusion in object/edge order. NOWAIT
 -- gives one refusal; it does not hide a retry loop in the embedded library.
 -- Join the same gate as every native row writer. SHARE ROW EXCLUSIVE table
 -- locks conflict with routine autovacuum and caused spurious observation refusals.
 IF NOT pg_try_advisory_xact_lock(1953658227,1735549296) THEN
  RAISE EXCEPTION 'graph writer in flight' USING ERRCODE='55P03';END IF;
 LOCK TABLE truss.object IN ROW EXCLUSIVE MODE NOWAIT;
 LOCK TABLE truss.edge IN ROW EXCLUSIVE MODE NOWAIT;
 locked:=truss.runtime_owned_input_scope(input);
 IF locked IS DISTINCT FROM observed THEN
  RAISE EXCEPTION 'graph changed before write exclusion' USING ERRCODE='55P03';END IF;
 inventory:=truss.runtime_owned_prepare_application(input,locked,application_prepared);
 PERFORM truss.runtime_owned_key_preflight(inventory);
 -- The shared original scope owns one before snapshot. Trusted independent
 -- updates need only scalar plan custody and their exact mapped patch after
 -- preflight; the producer binds actual rows and emits the full transition.
 compact_updates:=application_prepared IS NOT NULL
  AND locked->'independentEndpointScope'='true'::jsonb
  AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(input_operations) o
   WHERE o.value->>'operation' IS DISTINCT FROM 'update_object'
    OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange')
  AND (SELECT count(DISTINCT value->>'primary') FROM jsonb_array_elements(inventory->'operations'))=jsonb_array_length(input_operations)
  AND NOT EXISTS(SELECT 1 FROM jsonb_each(locked->'nodes') n
   WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb
    OR n.value->'rev' IS DISTINCT FROM inventory->'catalogRevision');
 application_operations:=application_prepared->'operations';
 -- Retain all immutable plans with one INSERT, preserving exact row images.
 WITH selected_plans AS MATERIALIZED (
  SELECT CASE WHEN compact_updates THEN v.value||jsonb_build_object(
   'compactProfile','truss-application-value-plan/0.1',
   'applicationPatch',application_operations->(v.value->>'operationIndex')::int,
   'desiredImageSha256',encode(sha256(convert_to(((v.value->'afterNodes'->(v.value->>'primary')->'image')-ARRAY['created_at','updated_at']||
    jsonb_build_object('id',(v.value->'afterNodes'->(v.value->>'primary')->'identity'->>'id')::bigint,
     'root_id',NULL,'root_type',NULL))::text,'UTF8')),'hex'),
   'beforeNodes',(SELECT jsonb_object_agg(n.key,jsonb_set(n.value,'{image}',(n.value->'image')-ARRAY['props','retained'])) FROM jsonb_each(v.value->'beforeNodes') n),
   'afterNodes',(SELECT jsonb_object_agg(n.key,jsonb_set(n.value,'{image}',(n.value->'image')-ARRAY['props','retained'])) FROM jsonb_each(v.value->'afterNodes') n))
   ELSE v.value END value
  FROM jsonb_array_elements(inventory->'operations') v),
 plans AS MATERIALIZED (
  SELECT value||jsonb_build_object('actorName',session_user::text,'mutationProfile',input->'mutationProfile',
   'catalogRevision',inventory->'catalogRevision')||CASE WHEN value->>'operationIndex'='0'
    THEN jsonb_build_object('initialScope',inventory->'initialScope') ELSE '{}'::jsonb END plan
  FROM selected_plans)
 SELECT sum(octet_length(convert_to(plan::text,'UTF8'))),
  jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(plan->>'operationIndex')::int,
   'writer_xid',attempt.writer_xid::text,'plan',plan,'result',NULL) ORDER BY (plan->>'operationIndex')::int)
 INTO retained_bytes,expected_operation FROM plans;
 IF retained_bytes>33554432 THEN RAISE EXCEPTION 'bounded retained whole group inventory required' USING ERRCODE='54000';END IF;
 INSERT INTO truss.runtime_owned_operation(attempt_id,operation_index,writer_xid,plan)
 SELECT r.attempt_id,r.operation_index,r.writer_xid,r.plan
 FROM jsonb_populate_recordset(NULL::truss.runtime_owned_operation,expected_operation) r;
 GET DIAGNOSTICS observed_operation_count=ROW_COUNT;
 IF observed_operation_count<>jsonb_array_length(expected_operation) THEN
  RAISE EXCEPTION 'complete prepared operation insert required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_capture_application(uuid,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_capture(selected_attempt uuid) RETURNS void
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT truss.runtime_owned_capture_application(selected_attempt,NULL);
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_capture(uuid) FROM PUBLIC;

-- Reuse original operation evidence after rows move or disappear. Identity-only
-- matching never attributes a descendant transition to an unrelated operation.
CREATE FUNCTION truss.runtime_owned_plan(selected_attempt uuid,selected_index int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original record;scope_image jsonb;before_state jsonb;after_state jsonb;after_image jsonb;reference text;
BEGIN
 SELECT plan INTO STRICT original FROM truss.runtime_owned_operation
  WHERE attempt_id=selected_attempt AND operation_index=selected_index;
 -- Both source bytes and prepared operations are immutable after capture.
 -- Full source correspondence is checked once at each group settlement.
 IF selected_index<0
  OR original.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
  OR original.plan->'operationIndex' IS DISTINCT FROM to_jsonb(selected_index)
  OR original.plan->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() THEN
  RAISE EXCEPTION 'original owned operation correspondence required' USING ERRCODE='55000';END IF;
 IF original.plan->>'compactProfile'='truss-application-value-plan/0.1' THEN
  -- Historical/general readers reconstruct the former virtual frame lazily.
  -- No-op updates have no transition; their one original scope image remains
  -- sufficient even if a later operation or catalog acceptance changed the row.
  reference:=original.plan->>'primary';
  before_state:=original.plan->'beforeNodes'->reference;after_state:=original.plan->'afterNodes'->reference;
  SELECT p.plan->'initialScope'->'nodes'->((before_state->'identity'->>'typeId')||':'||(before_state->'identity'->>'id'))
   INTO STRICT scope_image FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=0;
  IF scope_image IS NULL THEN RAISE EXCEPTION 'original compact update scope required' USING ERRCODE='55000';END IF;
  before_state:=jsonb_set(before_state,'{image}',scope_image-ARRAY['root_id','root_type','updated_at']);
  IF before_state->'image'->'ver' IS DISTINCT FROM after_state->'image'->'ver' THEN
   SELECT t.after_object INTO STRICT after_image FROM truss.runtime_object_transition t
    WHERE t.attempt_id=selected_attempt AND t.operation_index=selected_index;
   IF encode(sha256(convert_to((after_image-ARRAY['created_at','updated_at'])::text,'UTF8')),'hex')
    IS DISTINCT FROM original.plan->>'desiredImageSha256' THEN
    RAISE EXCEPTION 'original compact update desired image required' USING ERRCODE='55000';END IF;
  ELSE after_image:=scope_image;END IF;
  after_state:=jsonb_set(after_state,'{image}',after_image-ARRAY['root_id','root_type','updated_at']);
  original.plan:=jsonb_set(jsonb_set(original.plan,ARRAY['beforeNodes',reference],before_state),ARRAY['afterNodes',reference],after_state);
 END IF;
 RETURN original.plan;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_plan(uuid,int) FROM PUBLIC;


-- Actual identities come only from the admitted stored state or the genuine
-- original create result. Local create ordinals never stand in for native IDs.
CREATE FUNCTION truss.runtime_owned_identity(selected_attempt uuid,selected_index int,reference text,entity_kind text,prepared_plan jsonb DEFAULT NULL,prepared_attempt truss.runtime_object_attempt DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;attempt truss.runtime_object_attempt%ROWTYPE;
 creation_index int;result jsonb;creation_plan jsonb;operation jsonb;witness jsonb;pin record;
BEGIN
 IF entity_kind NOT IN ('object','edge') OR entity_kind IS NULL OR reference IS NULL THEN
  RAISE EXCEPTION 'explicit original entity reference required' USING ERRCODE='55000';END IF;
 plan:=coalesce(prepared_plan,truss.runtime_owned_plan(selected_attempt,selected_index));
 state:=coalesce(jsonb_extract_path(plan,CASE entity_kind WHEN 'object' THEN 'afterNodes' ELSE 'afterEdges' END,reference),
  jsonb_extract_path(plan,CASE entity_kind WHEN 'object' THEN 'beforeNodes' ELSE 'beforeEdges' END,reference));
 IF state IS NULL AND entity_kind='object' AND reference LIKE 'stored:%' THEN
  SELECT jsonb_extract_path(p.plan,'initialScope','boundary',substring(reference FROM 8)) INTO witness
   FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=0;
  IF witness IS NOT NULL THEN
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(witness->'object'->>'type_id')::int,NULL,(plan->>'catalogRevision')::int);
   state:=jsonb_build_object('identity',jsonb_build_object('id',witness->'object'->>'id','typeId',witness->'object'->>'type_id',
    'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id)));
  END IF;
 END IF;
 IF state IS NULL THEN RAISE EXCEPTION 'original operation member required' USING ERRCODE='55000';END IF;
 identity:=state->'identity';
 IF reference LIKE 'stored:%' THEN
  IF reference IS DISTINCT FROM 'stored:'||(identity->>'typeId')||':'||(identity->>'id') THEN
   RAISE EXCEPTION 'original stored identity correspondence required' USING ERRCODE='55000';END IF;
 ELSIF reference ~ '^create:(0|[1-9][0-9]{0,2}|10[01][0-9]|102[0-3])$' THEN
  creation_index:=substring(reference FROM 8)::int;
  IF prepared_attempt.id IS NOT NULL THEN
   IF prepared_attempt.id IS DISTINCT FROM selected_attempt THEN RAISE EXCEPTION 'original checked attempt required' USING ERRCODE='55000';END IF;
   attempt:=prepared_attempt;
  ELSE SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;END IF;
  IF creation_index>selected_index OR creation_index>=attempt.next_index THEN
   RAISE EXCEPTION 'prior original create progress required' USING ERRCODE='55000';END IF;
  SELECT p.result,p.plan INTO STRICT result,creation_plan FROM truss.runtime_owned_operation p
   WHERE p.attempt_id=selected_attempt AND p.operation_index=creation_index AND p.writer_xid=attempt.writer_xid;
  IF result IS NULL THEN RAISE EXCEPTION 'sealed original create result required' USING ERRCODE='55000';END IF;
  -- The sealed result and immutable source plan are the same original slot.
  -- Keep the standalone plan reader's checks after the result refusal.
  IF creation_index<0
   OR creation_plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
   OR creation_plan->'operationIndex' IS DISTINCT FROM to_jsonb(creation_index)
   OR creation_plan->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() THEN
   RAISE EXCEPTION 'original owned operation correspondence required' USING ERRCODE='55000';END IF;
  operation:=creation_plan->'operation';
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
REVOKE ALL ON FUNCTION truss.runtime_owned_identity(uuid,int,text,text,jsonb,truss.runtime_object_attempt) FROM PUBLIC;

-- Compare semantic simulation with realized transitions. Physical timestamps
-- remain in the original member/transition; this is not their replacement.
CREATE FUNCTION truss.runtime_owned_object_image(selected_attempt uuid,selected_index int,reference text,phase text,prepared_plan jsonb DEFAULT NULL,prepared_attempt truss.runtime_object_attempt DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;root_identity jsonb;root_reference text;
BEGIN
 IF phase IS NULL OR phase NOT IN ('before','after') THEN RAISE EXCEPTION 'explicit image phase required' USING ERRCODE='55000';END IF;
 plan:=coalesce(prepared_plan,truss.runtime_owned_plan(selected_attempt,selected_index));state:=jsonb_extract_path(plan,phase||'Nodes',reference);
 IF state IS NULL OR state->'deleted'='true'::jsonb THEN RETURN NULL;END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'object',plan,prepared_attempt);
 root_reference:=state->>'root';
 IF root_reference IS NOT NULL THEN root_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,root_reference,'object',plan,prepared_attempt);END IF;
 RETURN ((state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(identity->>'id')::bigint,
  'root_id',(root_identity->>'id')::bigint,'root_type',(root_identity->>'typeId')::int);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_image(uuid,int,text,text,jsonb,truss.runtime_object_attempt) FROM PUBLIC;


CREATE FUNCTION truss.runtime_owned_edge_image(selected_attempt uuid,selected_index int,reference text,phase text,prepared_plan jsonb DEFAULT NULL,prepared_attempt truss.runtime_object_attempt DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;source_identity jsonb;target_identity jsonb;
BEGIN
 IF phase IS NULL OR phase NOT IN ('before','after') THEN RAISE EXCEPTION 'explicit edge image phase required' USING ERRCODE='55000';END IF;
 plan:=coalesce(prepared_plan,truss.runtime_owned_plan(selected_attempt,selected_index));state:=jsonb_extract_path(plan,phase||'Edges',reference);
 IF state IS NULL OR state->'deleted'='true'::jsonb THEN RETURN NULL;END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'edge',plan,prepared_attempt);
 source_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,state->>'source','object',plan,prepared_attempt);
 target_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,state->>'target','object',plan,prepared_attempt);
 RETURN ((state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(identity->>'id')::bigint,
  'source_id',(source_identity->>'id')::bigint,'source_type',(source_identity->>'typeId')::int,
  'target_id',(target_identity->>'id')::bigint,'target_type',(target_identity->>'typeId')::int,
  'order_key',state->'orderKey'->>'text');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_image(uuid,int,text,text,jsonb,truss.runtime_object_attempt) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_edge_metadata(selected_attempt uuid,selected_index int,reference text,qualified_actor oid DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;plan jsonb;prior jsonb;desired jsonb;identity jsonb;physical jsonb;
 source_identity jsonb;target_identity jsonb;old_source jsonb;old_target jsonb;endpoint_identity jsonb;
 endpoint_reference text;relation truss.rel_def%ROWTYPE;current_actor oid;new_key text;old_key text;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 current_actor:=coalesce(qualified_actor,truss.runtime_person(false));
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index THEN
  RAISE EXCEPTION 'current original owned effect required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);prior:=plan->'beforeEdges'->reference;desired:=plan->'afterEdges'->reference;
 IF desired IS NULL OR prior->'deleted'='true'::jsonb THEN RAISE EXCEPTION 'original live edge effect required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT relation FROM truss.rel_def WHERE rel_type_id=(desired->'identity'->>'typeId')::int AND retired_rev IS NULL;
 PERFORM truss.runtime_module_writer_qualified(relation.document_id,relation.module,current_actor);
 IF relation.lifecycle NOT IN ('independent','owned') OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL THEN
  RAISE EXCEPTION 'selected owned or independent relationship required' USING ERRCODE='0A000';END IF;
 IF prior IS NOT NULL THEN
  identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'edge',plan,attempt);
  SELECT to_jsonb(e) INTO STRICT physical FROM truss.edge e WHERE id=(identity->>'id')::bigint AND rel_type_id=relation.rel_type_id;
  IF physical->>'ver' IS DISTINCT FROM prior->'image'->>'ver' THEN
   RAISE EXCEPTION 'original planned edge version required' USING ERRCODE='55000';END IF;
  old_source:=truss.runtime_owned_identity(selected_attempt,selected_index,prior->>'source','object',plan,attempt);
  old_target:=truss.runtime_owned_identity(selected_attempt,selected_index,prior->>'target','object',plan,attempt);
 END IF;
 source_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,desired->>'source','object',plan,attempt);
 target_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,desired->>'target','object',plan,attempt);
 FOR endpoint_reference IN SELECT DISTINCT value#>>'{}' FROM jsonb_array_elements(jsonb_build_array(
  desired->'source',desired->'target',prior->'source',prior->'target')) WHERE value<>'null'::jsonb LOOP
  endpoint_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,endpoint_reference,'object',plan,attempt);
  IF NOT truss.runtime_can_read_qualified(endpoint_identity->'owner'->>'documentId',endpoint_identity->'owner'->>'moduleId',current_actor) THEN
   RAISE EXCEPTION 'original endpoint reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 new_key:=truss.runtime_edge_business_key(relation.rel_type_id,source_identity,target_identity);
 PERFORM truss.runtime_lock_edge_business_key(new_key);
 IF old_source IS NOT NULL THEN
  old_key:=truss.runtime_edge_business_key(relation.rel_type_id,old_source,old_target);
  IF old_key IS DISTINCT FROM new_key THEN PERFORM truss.runtime_lock_edge_business_key(old_key);END IF;
 END IF;
 RETURN jsonb_build_object('ownedReference',reference,'documentId',relation.document_id,'moduleId',relation.module,'typeId',relation.rel_type_id::text,
  'identity',identity,'prior',physical,'source',source_identity,'target',target_identity,'oldSource',old_source,'oldTarget',old_target,
  'retained',coalesce(nullif(desired->'image'->'retained','null'::jsonb),'{}'::jsonb),'orderKey',desired->'orderKey','keys','[]'::jsonb,'values','[]'::jsonb);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_metadata(uuid,int,text,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_edge_effect_selection(selected_attempt uuid,selected_index int,metadata jsonb,effect_operation text,qualified_actor oid DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;reference text:=metadata->>'ownedReference';prior jsonb;desired jsonb;derived_operation text;original_operation text;
BEGIN
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);prior:=plan->'beforeEdges'->reference;desired:=plan->'afterEdges'->reference;
 original_operation:=plan->'operation'->>'operation';
 derived_operation:=CASE WHEN prior IS NULL THEN 'create_edge' WHEN desired->'deleted'='true'::jsonb THEN 'delete_edge' ELSE 'update_edge' END;
 IF desired IS NULL OR prior->'deleted'='true'::jsonb OR effect_operation IS DISTINCT FROM derived_operation
  OR (original_operation='delete_object' AND (derived_operation<>'delete_edge' OR prior IS NULL))
  OR (original_operation<>'delete_object' AND (original_operation IS DISTINCT FROM derived_operation OR reference IS DISTINCT FROM plan->>'primary'))
  OR metadata IS DISTINCT FROM truss.runtime_owned_edge_metadata(selected_attempt,selected_index,reference,qualified_actor) THEN
  RAISE EXCEPTION 'original planned edge effect required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_effect_selection(uuid,int,jsonb,text,oid) FROM PUBLIC;


-- Original operation-time endpoint roots; no live endpoint/root lookup.
CREATE FUNCTION truss.runtime_owned_endpoint_at(selected_attempt uuid,selected_index int,reference text,phase text,prepared_plan jsonb DEFAULT NULL,prepared_attempt truss.runtime_object_attempt DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb;state jsonb;identity jsonb;ownership jsonb;root_identity jsonb;
BEGIN
 IF phase IS NULL OR phase NOT IN ('before','after') THEN RAISE EXCEPTION 'explicit endpoint phase required' USING ERRCODE='55000';END IF;
 plan:=coalesce(prepared_plan,truss.runtime_owned_plan(selected_attempt,selected_index));state:=jsonb_extract_path(plan,phase||'Nodes',reference);
 IF state IS NULL OR state->'deleted'='true'::jsonb THEN RAISE EXCEPTION 'original live endpoint context required' USING ERRCODE='55000';END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'object',plan,prepared_attempt);ownership:='{"state":"rootless"}'::jsonb;
 IF state->>'root' IS NOT NULL THEN
  root_identity:=truss.runtime_owned_identity(selected_attempt,selected_index,state->>'root','object',plan,prepared_attempt);
  ownership:=jsonb_build_object('state','owned','root',root_identity);
 END IF;
 RETURN jsonb_build_object('identity',identity,'ownership',ownership);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_endpoint_at(uuid,int,text,text,jsonb,truss.runtime_object_attempt) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_edge_transition_validate_qualified(selected_transition bigint,authorize_read boolean,qualified_actor oid,prepared_input jsonb DEFAULT NULL,source_bytes bytea DEFAULT NULL,prepared_attempt truss.runtime_object_attempt DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE transition truss.runtime_edge_transition%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;
 plan jsonb;reference text;candidate text;candidate_state jsonb;catalog_revision jsonb;identity jsonb;prior jsonb;desired jsonb;expected_context jsonb;
 before_context jsonb;after_context jsonb;context jsonb;previous_image jsonb;has_previous boolean;
 expected_mode text;original_mode text;expected_version bigint;journal jsonb;event jsonb;matches int:=0;current_actor oid;
BEGIN
 IF authorize_read IS NULL THEN RAISE EXCEPTION 'explicit validation authority mode required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT transition FROM truss.runtime_edge_transition WHERE transition_id=selected_transition;
 IF prepared_attempt.id IS NOT NULL THEN
  IF prepared_attempt.id IS DISTINCT FROM transition.attempt_id THEN RAISE EXCEPTION 'original checked attempt required' USING ERRCODE='55000';END IF;
  attempt:=prepared_attempt;
 ELSE SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=transition.attempt_id;END IF;
 IF prepared_input IS NOT NULL AND (source_bytes IS NULL OR source_bytes IS DISTINCT FROM attempt.input_bytes) THEN
  RAISE EXCEPTION 'original checked transition input required' USING ERRCODE='55000';END IF;
 -- Only group settlement supplies the original attempt and input after its
 -- complete immutable result-slot census. Per-step and history calls recount.
 current_actor:=coalesce(qualified_actor,truss.runtime_person(false));
 IF attempt.writer_xid IS DISTINCT FROM transition.writer_xid OR transition.operation_index<0 OR transition.operation_index>=attempt.next_index
  OR (CASE WHEN NOT authorize_read AND prepared_attempt.id IS NOT NULL AND prepared_input IS NOT NULL
   THEN attempt.next_index ELSE (SELECT count(*) FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.result IS NOT NULL) END)<>attempt.next_index
  OR (authorize_read AND NOT attempt.complete)
  OR (NOT authorize_read AND (attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor)) THEN
  RAISE EXCEPTION 'original completed edge operation progress required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(attempt.id,transition.operation_index);
 catalog_revision:=plan->'catalogRevision';
 FOR candidate,candidate_state IN SELECT key,value FROM jsonb_each(plan->'afterEdges') LOOP
  identity:=truss.runtime_owned_identity(attempt.id,transition.operation_index,candidate,'edge',
   jsonb_build_object('catalogRevision',catalog_revision,'afterEdges',jsonb_build_object(candidate,candidate_state)),attempt);
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
  OR transition.before_edge-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_edge_image(attempt.id,transition.operation_index,reference,'before',plan,attempt)
  OR transition.after_edge-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_edge_image(attempt.id,transition.operation_index,reference,'after',plan,attempt) THEN
  RAISE EXCEPTION 'original edge plan and transition images required' USING ERRCODE='55000';END IF;
 -- Exact physical prestate chains back to the original captured scope, including
 -- timestamps, rather than being reconstructed from the semantic projection.
 SELECT after_edge INTO previous_image FROM truss.runtime_edge_transition
  WHERE attempt_id=attempt.id AND edge_id=transition.edge_id AND rel_type_id=transition.rel_type_id
   AND operation_index<transition.operation_index ORDER BY operation_index DESC LIMIT 1;
 has_previous:=FOUND;
 IF NOT has_previous THEN
  SELECT jsonb_extract_path(p.plan,'initialScope','edges',transition.edge_id::text) INTO STRICT previous_image
   FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.operation_index=0;
 END IF;
 IF transition.before_edge IS DISTINCT FROM previous_image THEN RAISE EXCEPTION 'original physical edge prestate chain required' USING ERRCODE='55000';END IF;
 IF prior IS NOT NULL THEN
  before_context:=jsonb_build_object('source',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,prior->>'source','before',plan,attempt),
   'target',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,prior->>'target','before',plan,attempt));
 END IF;
 IF desired->'deleted'='false'::jsonb THEN
  after_context:=jsonb_build_object('source',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,desired->>'source','after',plan,attempt),
   'target',truss.runtime_owned_endpoint_at(attempt.id,transition.operation_index,desired->>'target','after',plan,attempt));
 END IF;
 expected_context:=jsonb_build_object('profile','truss-edge-endpoint-ownership/0.1','captureCatalogRevision',plan->>'catalogRevision',
  'before',before_context,'after',after_context);
 IF transition.endpoint_ownership IS DISTINCT FROM expected_context
  OR nullif(transition.old_source,'null'::jsonb) IS DISTINCT FROM before_context->'source'->'identity'
  OR nullif(transition.old_target,'null'::jsonb) IS DISTINCT FROM before_context->'target'->'identity'
  OR transition.source_identity IS DISTINCT FROM truss.runtime_owned_identity(attempt.id,transition.operation_index,desired->>'source','object',plan,attempt)
  OR transition.target_identity IS DISTINCT FROM truss.runtime_owned_identity(attempt.id,transition.operation_index,desired->>'target','object',plan,attempt) THEN
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
   OR event->'identity' IS DISTINCT FROM truss.runtime_owned_identity(attempt.id,transition.operation_index,reference,'edge',plan,attempt) THEN
   RAISE EXCEPTION 'original owned edge event required' USING ERRCODE='55000';END IF;
 END IF;
 IF authorize_read THEN
  FOR context IN SELECT value FROM jsonb_array_elements(jsonb_build_array(before_context->'source',before_context->'target',after_context->'source',after_context->'target')) WHERE value<>'null'::jsonb LOOP
   IF NOT truss.runtime_can_read_qualified(context->'identity'->'owner'->>'documentId',context->'identity'->'owner'->>'moduleId',current_actor) THEN
    RAISE EXCEPTION 'current original endpoint reader required' USING ERRCODE='42501';END IF;
   PERFORM truss.runtime_history_ownership_qualified(jsonb_build_object('identity',context->'identity','catalogRevision',plan->>'catalogRevision','ownership',context->'ownership'),current_actor);
  END LOOP;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_transition_validate_qualified(bigint,boolean,oid,jsonb,bytea,truss.runtime_object_attempt) FROM PUBLIC;
CREATE FUNCTION truss.runtime_owned_edge_transition_validate(selected_transition bigint,authorize_read boolean,qualified_actor oid DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_owned_edge_transition_validate_qualified(selected_transition,authorize_read,qualified_actor);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_transition_validate(bigint,boolean,oid) FROM PUBLIC;


-- Apply one object member of an original operation. The outer step alone emits
-- its public result and advances progress; descendants are never child groups.
CREATE FUNCTION truss.runtime_owned_object_effect(selected_attempt uuid,selected_index int,reference text,prepared_input jsonb DEFAULT NULL,qualified_actor oid DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;plan jsonb;input jsonb;prior jsonb;desired jsonb;identity jsonb;
 object_row truss.object%ROWTYPE;old_image jsonb;new_image jsonb;expected_image jsonb;before_record jsonb;after_record jsonb;
 installation truss.catalog_runtime_installation%ROWTYPE;property truss.prop_def%ROWTYPE;pin record;changed_rows bigint;
 events jsonb:='[]';event_refs jsonb:='[]';journals jsonb:='[]';base_events jsonb[]:='{}'::jsonb[];final_events jsonb[]:='{}'::jsonb[];
 journal_items jsonb[]:='{}'::jsonb[];event_ref_items jsonb[]:='{}'::jsonb[];event jsonb;entry record;journal truss.journal%ROWTYPE;
 keys jsonb;version bigint;revision int;event_digest text;ordinal int;mode text;result jsonb;current_actor oid;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() THEN
  RAISE EXCEPTION 'current original object effect required' USING ERRCODE='55000';END IF;
 current_actor:=coalesce(qualified_actor,truss.runtime_person(false));
 IF attempt.actor_oid IS DISTINCT FROM current_actor
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index THEN
  RAISE EXCEPTION 'current original object effect required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);
 input:=CASE WHEN attempt.context ? 'originalAssertedOrigin' THEN jsonb_build_object('assertedOrigin',attempt.context->'originalAssertedOrigin')
  ELSE coalesce(prepared_input,convert_from(attempt.input_bytes,'UTF8')::jsonb) END;
 prior:=plan->'beforeNodes'->reference;desired:=plan->'afterNodes'->reference;mode:=plan->'operation'->>'operation';
 IF mode NOT IN ('update_object','delete_object') OR prior IS NULL OR desired IS NULL OR prior->'deleted'='true'::jsonb
  OR (mode='update_object' AND desired->'deleted'='true'::jsonb)
  OR (mode='delete_object' AND desired->'deleted' IS DISTINCT FROM 'true'::jsonb)
  OR (reference IS DISTINCT FROM plan->>'primary' AND prior IS NOT DISTINCT FROM desired) THEN
  RAISE EXCEPTION 'original primary or affected descendant required' USING ERRCODE='55000';END IF;
 identity:=truss.runtime_owned_identity(selected_attempt,selected_index,reference,'object',plan,attempt);
 PERFORM truss.runtime_module_writer_qualified(identity->'owner'->>'documentId',identity->'owner'->>'moduleId',current_actor);
 IF NOT truss.runtime_object_values_readable_qualified((identity->>'typeId')::int,current_actor) THEN RAISE EXCEPTION 'current original property/item readers required' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT object_row FROM truss.object WHERE id=(identity->>'id')::bigint AND type_id=(identity->>'typeId')::int FOR UPDATE NOWAIT;
 old_image:=to_jsonb(object_row);
 IF old_image->>'ver' IS DISTINCT FROM prior->'image'->>'ver' THEN
  RAISE EXCEPTION 'original planned object version required' USING ERRCODE='55000';END IF;
 IF prior IS NOT DISTINCT FROM desired THEN
  RETURN jsonb_build_object('outcome','unchanged','operation','update_object','identity',identity,'version',object_row.ver::text,'events','[]'::jsonb);
 END IF;
 IF object_row.ver=9223372036854775807 THEN RAISE EXCEPTION 'record version exhausted' USING ERRCODE='54000';END IF;
 version:=object_row.ver+1;revision:=(plan->>'catalogRevision')::int;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 before_record:=truss.runtime_object_history(old_image,identity);
 IF mode='update_object' THEN
  expected_image:=truss.runtime_owned_object_image(selected_attempt,selected_index,reference,'after',plan,attempt);
  IF expected_image->>'ver' IS DISTINCT FROM version::text THEN RAISE EXCEPTION 'one original version advance required' USING ERRCODE='55000';END IF;
  IF object_row.props IS DISTINCT FROM expected_image->'props' THEN
   PERFORM truss.runtime_object_update_keys(object_row.id,object_row.type_id,expected_image->'props',convert_to('[]','UTF8'),selected_attempt,selected_index);
  END IF;
  object_row.props:=expected_image->'props';object_row.retained:=nullif(expected_image->'retained','null'::jsonb);
  object_row.root_id:=(expected_image->>'root_id')::bigint;object_row.root_type:=(expected_image->>'root_type')::int;
  object_row.rev:=revision;object_row.ver:=version;object_row.updated_at:=clock_timestamp();
  UPDATE truss.object SET props=object_row.props,retained=object_row.retained,root_id=object_row.root_id,root_type=object_row.root_type,
   rev=object_row.rev,ver=object_row.ver,updated_at=object_row.updated_at
   WHERE id=object_row.id AND type_id=object_row.type_id AND ver=(old_image->>'ver')::bigint
   RETURNING to_jsonb(object) INTO new_image;
  GET DIAGNOSTICS changed_rows=ROW_COUNT;
  IF changed_rows<>1 THEN RAISE EXCEPTION 'original planned object update required' USING ERRCODE='55000';END IF;
  after_record:=truss.runtime_object_history(new_image,identity);
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=object_row.type_id AND retired_rev IS NULL ORDER BY prop_id LOOP
   IF old_image->'props'->property.prop_id::text IS DISTINCT FROM new_image->'props'->property.prop_id::text THEN
    SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',object_row.type_id,property.prop_id);
    base_events[cardinality(base_events)+1]:=jsonb_build_object('operation','property','propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,
     'before',CASE WHEN old_image->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',old_image->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END,
     'after',CASE WHEN new_image->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',new_image->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END);
   END IF;
  END LOOP;
  base_events[cardinality(base_events)+1]:=jsonb_build_object('operation','metadata','before',before_record,'after',after_record);
 ELSE
  FOR entry IN SELECT k.namespace_bytes,k.key_bytes,k.namespace_sha256,k.key_sha256 FROM truss.object_key_bucket k
   WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id ORDER BY k.namespace_bytes,k.key_bytes LOOP
   PERFORM truss.lock_string_key_bucket(entry.namespace_bytes,entry.key_bytes);
   UPDATE truss.key_bucket_guard SET generation=generation+1 WHERE namespace_sha256=entry.namespace_sha256 AND key_sha256=entry.key_sha256;
  END LOOP;
  DELETE FROM truss.object WHERE id=object_row.id AND type_id=object_row.type_id AND ver=(old_image->>'ver')::bigint;
  GET DIAGNOSTICS changed_rows=ROW_COUNT;
  IF changed_rows<>1 THEN RAISE EXCEPTION 'original planned deletion required' USING ERRCODE='55000';END IF;
  base_events[cardinality(base_events)+1]:=jsonb_build_object('operation','delete','before',before_record);
 END IF;
 FOR ordinal IN 1..cardinality(base_events) LOOP
  event:=base_events[ordinal];event:=event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',nextval('truss.journal_seq')::text,
   'identity',identity,'eventVersion',version::text,'eventCatalogRevision',revision::text,
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text));
  final_events[cardinality(final_events)+1]:=event;
 END LOOP;
 SELECT coalesce(jsonb_agg(item.value ORDER BY item.ordinality),'[]'::jsonb) INTO events
  FROM unnest(final_events) WITH ORDINALITY AS item(value,ordinality);
 event_digest:=encode(sha256(convert_to(events::text,'UTF8')),'hex');
 FOREACH event IN ARRAY final_events LOOP
  event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',jsonb_array_length(events)::text,'orderedEventDigest',event_digest));
  journal.seq:=(event->>'seq')::bigint;journal.at:=clock_timestamp();journal.xid:=attempt.writer_xid;journal.entity_kind:='o';journal.entity_id:=object_row.id;journal.entity_type:=object_row.type_id;
  journal.ver:=version;journal.op:=CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END;journal.prop_id:=(event->>'propertyId')::int;
  journal.old_value:=NULL;journal.new_value:=truss.runtime_exact_wrapper('event',convert_to(event::text,'UTF8'));journal.rev:=revision;
  journal.origin:=truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8'));
  INSERT INTO truss.journal SELECT (journal).*;
  journal_items[cardinality(journal_items)+1]:=to_jsonb(journal);
  event_ref_items[cardinality(event_ref_items)+1]:=jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',journal.seq::text);
 END LOOP;
 SELECT coalesce(jsonb_agg(item.value ORDER BY item.ordinality),'[]'::jsonb) INTO journals
  FROM unnest(journal_items) WITH ORDINALITY AS item(value,ordinality);
 SELECT coalesce(jsonb_agg(item.value ORDER BY item.ordinality),'[]'::jsonb) INTO event_refs
  FROM unnest(event_ref_items) WITH ORDINALITY AS item(value,ordinality);
 SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]'::jsonb) INTO keys FROM truss.object_key_bucket k WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id;
 INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
 VALUES(selected_attempt,selected_index,attempt.writer_xid,object_row.id,object_row.type_id,old_image,new_image,keys,journals);
 current_actor:=truss.runtime_person(false);
 PERFORM truss.runtime_module_writer_qualified(identity->'owner'->>'documentId',identity->'owner'->>'moduleId',current_actor);
 IF NOT truss.runtime_object_values_readable_qualified((identity->>'typeId')::int,current_actor) THEN RAISE EXCEPTION 'current final property/item readers required' USING ERRCODE='42501';END IF;
 IF mode='update_object' THEN RETURN jsonb_build_object('outcome','changed','operation','update_object','identity',identity,'version',version::text,'events',event_refs);END IF;
 RETURN jsonb_build_object('outcome','deleted','operation','delete_object','identity',identity,'deletionVersion',version::text,
  'deleted',jsonb_build_array(jsonb_build_object('identity',identity,'deletionVersion',version::text)),'events',event_refs);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_effect(uuid,int,text,jsonb,oid) FROM PUBLIC;


CREATE FUNCTION truss.runtime_owned_step(selected_attempt uuid,selected_index int,prepared_input jsonb DEFAULT NULL,prepared_original bytea DEFAULT NULL,qualified_actor oid DEFAULT NULL) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
<<owned_step_body>>
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;plan jsonb;before_edges jsonb;before_nodes jsonb;mode text;entry record;prior jsonb;effect_mode text;
 primary_reference text;metadata jsonb;effect jsonb;primary_result jsonb;events jsonb:='[]';deleted jsonb:='[]';event_chunks jsonb[]:='{}'::jsonb[];deleted_chunks jsonb[]:='{}'::jsonb[];result jsonb;current_actor oid;changed_rows bigint;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 current_actor:=coalesce(qualified_actor,truss.runtime_person(false));
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index
  OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb THEN
  RAISE EXCEPTION 'current ordered owned operation required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);mode:=plan->'operation'->>'operation';primary_reference:=plan->>'primary';
 IF mode NOT IN ('create_edge','update_edge','delete_edge','update_object','delete_object') THEN
  RAISE EXCEPTION 'selected original owned operation required' USING ERRCODE='55000';END IF;
 -- Cascade edges precede every endpoint deletion. No child effect advances the
 -- original attempt or adds a synthetic operation/result to its input.
 -- Extract each immutable before-map once; the final slot can contain the
 -- complete graph even when only one member changes.
 before_edges:=plan->'beforeEdges';
 FOR entry IN SELECT key,value FROM jsonb_each(plan->'afterEdges') e WHERE e.value IS DISTINCT FROM before_edges->e.key
  OR e.key=primary_reference AND mode='update_edge' ORDER BY key COLLATE "C" LOOP
  prior:=before_edges->entry.key;
  IF prior->'deleted'='true'::jsonb THEN CONTINUE;END IF;
  effect_mode:=CASE WHEN prior IS NULL THEN 'create_edge' WHEN entry.value->'deleted'='true'::jsonb THEN 'delete_edge' ELSE 'update_edge' END;
  metadata:=truss.runtime_owned_edge_metadata(selected_attempt,selected_index,entry.key,current_actor);
  effect:=convert_from(truss.runtime_edge_effect(selected_attempt,selected_index,metadata,effect_mode,false,current_actor,prepared_input,prepared_original),'UTF8')::jsonb;
  event_chunks[cardinality(event_chunks)+1]:=coalesce(effect->'events','[]'::jsonb);
  deleted_chunks[cardinality(deleted_chunks)+1]:=coalesce(effect->'deleted','[]'::jsonb);
  IF entry.key=primary_reference THEN primary_result:=effect;END IF;
 END LOOP;
 -- Aggregate-root FKs are immediate: remove nonroots before their root.
 before_nodes:=plan->'beforeNodes';
 FOR entry IN SELECT key,value FROM jsonb_each(plan->'afterNodes') n WHERE
  before_nodes ? n.key AND (n.value IS DISTINCT FROM before_nodes->n.key OR n.key=primary_reference AND mode='update_object')
  ORDER BY CASE WHEN before_nodes->n.key->'root'='null'::jsonb THEN 1 ELSE 0 END,key COLLATE "C" LOOP
  IF before_nodes->entry.key->'deleted'='true'::jsonb THEN CONTINUE;END IF;
  effect:=truss.runtime_owned_object_effect(selected_attempt,selected_index,entry.key,prepared_input,current_actor);
  event_chunks[cardinality(event_chunks)+1]:=coalesce(effect->'events','[]'::jsonb);
  deleted_chunks[cardinality(deleted_chunks)+1]:=coalesce(effect->'deleted','[]'::jsonb);
  IF entry.key=primary_reference THEN primary_result:=effect;END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(event.value ORDER BY chunk.ordinality,event.ordinality),'[]'::jsonb) INTO events
  FROM unnest(event_chunks) WITH ORDINALITY AS chunk(items,ordinality)
  CROSS JOIN LATERAL jsonb_array_elements(chunk.items) WITH ORDINALITY AS event(value,ordinality);
 SELECT coalesce(jsonb_agg(item.value ORDER BY chunk.ordinality,item.ordinality),'[]'::jsonb) INTO deleted
  FROM unnest(deleted_chunks) WITH ORDINALITY AS chunk(items,ordinality)
  CROSS JOIN LATERAL jsonb_array_elements(chunk.items) WITH ORDINALITY AS item(value,ordinality);
 IF primary_result IS NULL OR primary_result->>'operation' IS DISTINCT FROM mode THEN RAISE EXCEPTION 'one original primary result required' USING ERRCODE='55000';END IF;
 result:=jsonb_set(primary_result,'{events}',events);
 IF mode IN ('delete_object','delete_edge') THEN result:=jsonb_set(result,'{deleted}',deleted);END IF;
 IF octet_length(convert_to(result::text,'UTF8'))>16777216 THEN RAISE EXCEPTION 'bounded complete original result required' USING ERRCODE='54000';END IF;
 UPDATE truss.runtime_owned_operation p SET result=owned_step_body.result
  WHERE p.attempt_id=selected_attempt AND p.operation_index=selected_index
   AND p.writer_xid=attempt.writer_xid AND p.result IS NULL;
 GET DIAGNOSTICS changed_rows=ROW_COUNT;
 IF changed_rows<>1 THEN RAISE EXCEPTION 'one original owned result slot required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt a SET next_index=a.next_index+1
  WHERE a.id=selected_attempt AND a.writer_xid=attempt.writer_xid AND a.actor_oid=current_actor
   AND NOT a.complete AND a.next_index=selected_index AND a.results='[]'::jsonb AND a.aliases='[]'::jsonb;
 GET DIAGNOSTICS changed_rows=ROW_COUNT;
 IF changed_rows<>1 THEN RAISE EXCEPTION 'one ordered owned progress advance required' USING ERRCODE='55000';END IF;
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_step(uuid,int,jsonb,bytea,oid) FROM PUBLIC;


-- Lock the complete initial/planned key union before allocating an identity or
-- writing a graph row. Reservation simulation preserves key_reuse=forbid even
-- when an earlier operation in this same group changes or deletes its object.
CREATE FUNCTION truss.runtime_owned_key_preflight(inventory jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;candidate jsonb;definition truss.key_def%ROWTYPE;
 component int;cells jsonb;before_cells jsonb;tuple_bytes bytea;namespace bytea;transport bytea;pin record;
 routes jsonb:='[]';lock_routes jsonb:='[]';entry jsonb;route record;observed record;member truss.object_key_bucket%ROWTYPE;
 reference text;unchanged boolean;
 namespaces jsonb:='{}';namespace_key text;namespace_hex text;codecs jsonb:='{}';codec jsonb;codec_bytes bigint:=2;
 route_items jsonb[]:='{}';lock_route_items jsonb[]:='{}';route_bytes bigint:=2;lock_route_bytes bigint:=2;
 metadata_keys text[]:='{}';namespace_values text[]:='{}';codec_keys text[]:='{}';codec_values jsonb[]:='{}';
 all_routes jsonb;guard_rows jsonb;route_observations jsonb;
BEGIN
 IF inventory->>'profile' IS DISTINCT FROM 'truss-owned-group-plan/0.1'
  OR (inventory->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR (SELECT value FROM truss.setting WHERE key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb THEN
  RAISE EXCEPTION 'original current forbid-reuse inventory required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 -- Build immutable key metadata maps once per distinct selected type/key.
 -- Their entries do not depend on record values or authorization decisions.
 FOR definition IN
  WITH selected_types AS (
   SELECT DISTINCT (n.value->>'type_id')::int type_id FROM jsonb_each(inventory->'initialScope'->'nodes') n
   UNION SELECT (n.value->'image'->>'type_id')::int FROM jsonb_array_elements(inventory->'operations') p
    CROSS JOIN LATERAL jsonb_each(p.value->'afterNodes') n)
  SELECT k.* FROM selected_types t JOIN truss.key_def k USING(type_id) WHERE k.retired_rev IS NULL ORDER BY k.type_id,k.key_num
 LOOP
  namespace_key:=definition.type_id::text||':'||definition.key_num::text;
  codec:=truss.runtime_owned_key_codec_metadata(definition.type_id,definition.key_num);
  IF codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+octet_length(namespace_key)+8<=4194304 THEN
   codec_keys[cardinality(codec_keys)+1]:=namespace_key;codec_values[cardinality(codec_values)+1]:=codec;
   codec_bytes:=codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+octet_length(namespace_key)+8;
  END IF;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',definition.type_id,definition.key_num);
  namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
   'sourceEpoch',installation.source_epoch::text,'typeId',definition.type_id::text,'keyNumber',definition.key_num::text,
   'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
  metadata_keys[cardinality(metadata_keys)+1]:=namespace_key;namespace_values[cardinality(namespace_values)+1]:=encode(namespace,'hex');
 END LOOP;
 SELECT coalesce(jsonb_object_agg(key,value),'{}'::jsonb) INTO codecs FROM unnest(codec_keys,codec_values) m(key,value);
 SELECT coalesce(jsonb_object_agg(key,value),'{}'::jsonb) INTO namespaces FROM unnest(metadata_keys,namespace_values) m(key,value);
 FOR candidate IN SELECT value FROM (
  SELECT -1 ordinal,n.key reference,jsonb_build_object('phase','initial','reference','stored:'||n.key,'image',n.value) value
   FROM jsonb_each(inventory->'initialScope'->'nodes') n
  UNION ALL SELECT (p.value->>'operationIndex')::int,n.key,jsonb_build_object('phase','after','reference',n.key,
   'image',n.value->'image','before',p.value->'beforeNodes'->n.key->'image')
   FROM jsonb_array_elements(inventory->'operations') p CROSS JOIN LATERAL jsonb_each(p.value->'afterNodes') n
   WHERE n.value->'deleted'='false'::jsonb AND n.value IS DISTINCT FROM p.value->'beforeNodes'->n.key
 ) candidates ORDER BY candidates.ordinal,candidates.reference COLLATE "C" LOOP
  FOR definition IN SELECT k.* FROM truss.key_def k WHERE k.type_id=(candidate->'image'->>'type_id')::int AND k.retired_rev IS NULL ORDER BY k.key_num LOOP
   SELECT jsonb_agg(candidate->'image'->'props'->i.prop_id::text ORDER BY i.ordinal),
    jsonb_agg(candidate->'before'->'props'->i.prop_id::text ORDER BY i.ordinal)
   INTO cells,before_cells FROM unnest(definition.prop_ids) WITH ORDINALITY i(prop_id,ordinal);
   namespace_key:=definition.type_id::text||':'||definition.key_num::text;
   codec:=coalesce(codecs->namespace_key,truss.runtime_owned_key_codec_metadata(definition.type_id,definition.key_num));
   tuple_bytes:=truss.runtime_owned_key_tuple_in_metadata(definition.type_id,definition.key_num,cells,codec);
   namespace:=decode(namespaces->>namespace_key,'hex');
   transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');
   entry:=jsonb_build_object('phase',candidate->>'phase','reference',candidate->>'reference',
    'objectId',candidate->'image'->>'id','typeId',definition.type_id,'keyNumber',definition.key_num,
    'namespace',encode(namespace,'hex'),'transport',encode(transport,'hex'),'tuple',encode(tuple_bytes,'hex'),
    -- Identical cells have already passed this exact derivation above.
    -- Keep the original before-image condition and derive unequal cells so
    -- canonical equivalence and invalid prior values retain their behavior.
    'unchanged',CASE WHEN candidate->'before' IS NOT NULL AND candidate->'before'<>'null'::jsonb
     THEN CASE WHEN before_cells=cells THEN true
      ELSE truss.runtime_owned_key_tuple_in_metadata(definition.type_id,definition.key_num,before_cells,codec)=tuple_bytes END
     ELSE false END);
   route_bytes:=route_bytes+octet_length(convert_to(entry::text,'UTF8'))+CASE WHEN cardinality(route_items)=0 THEN 0 ELSE 2 END;
   route_items:=array_append(route_items,entry);
   IF cardinality(route_items)>16384 OR route_bytes>16777216 THEN
    RAISE EXCEPTION 'bounded whole-group key footprint required' USING ERRCODE='54000';END IF;
  END LOOP;
 END LOOP;
 -- Retired definitions may still have original live memberships. Deletion
 -- touches these bytes too; include them without reinterpreting retired keys.
 FOR member IN
  WITH planned_routes AS MATERIALIZED (
   SELECT DISTINCT decode(r.value->>'namespace','hex') AS namespace_bytes,
    decode(r.value->>'transport','hex') AS key_bytes FROM unnest(route_items) r(value))
  SELECT k.* FROM truss.object_key_bucket k JOIN jsonb_each(inventory->'initialScope'->'nodes') n
   ON k.object_id=(n.value->>'id')::bigint AND k.type_id=(n.value->>'type_id')::int
  LEFT JOIN planned_routes p ON p.namespace_bytes=k.namespace_bytes AND p.key_bytes=k.key_bytes
  WHERE p.namespace_bytes IS NULL LOOP
  entry:=jsonb_build_object('namespace',encode(member.namespace_bytes,'hex'),'transport',encode(member.key_bytes,'hex'));
  lock_route_bytes:=lock_route_bytes+octet_length(convert_to(entry::text,'UTF8'))+CASE WHEN cardinality(lock_route_items)=0 THEN 0 ELSE 2 END;
  lock_route_items:=array_append(lock_route_items,entry);
  IF cardinality(lock_route_items)+cardinality(route_items)>16384 OR lock_route_bytes+route_bytes>16777216 THEN
   RAISE EXCEPTION 'bounded whole-group key footprint required' USING ERRCODE='54000';END IF;
 END LOOP;
 IF cardinality(lock_route_items)+cardinality(route_items)>16384 OR lock_route_bytes+route_bytes>16777216 THEN
  RAISE EXCEPTION 'bounded whole-group key footprint required' USING ERRCODE='54000';END IF;
 routes:=to_jsonb(route_items);lock_routes:=to_jsonb(lock_route_items);all_routes:=routes||lock_routes;
 -- execute.sql already owns the global graph-writer gate. Recheck that same
 -- gate once here, then acquire all key-row guards in deterministic hash order.
 -- The scalar helper remains available to non-batch callers.
 IF jsonb_array_length(all_routes)>0 THEN
  IF current_setting('transaction_isolation')<>'read committed' THEN
   RAISE EXCEPTION 'current key observation requires READ COMMITTED' USING ERRCODE='0A000';END IF;
  IF NOT pg_try_advisory_xact_lock(1953658227,1735549296) THEN
   RAISE EXCEPTION 'key route is in flight' USING ERRCODE='55P03';END IF;
 END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(all_routes) r
  WHERE octet_length(decode(r.value->>'namespace','hex')) NOT BETWEEN 1 AND 65536
   OR octet_length(decode(r.value->>'transport','hex')) NOT BETWEEN 1 AND 1048576
   OR convert_from(decode(r.value->>'transport','hex'),'UTF8') !~ '^umf-key-tuple-v1:hex:([0-9a-f]{2})+$') THEN
  RAISE EXCEPTION 'bounded original key routing bytes required' USING ERRCODE='22023';END IF;
 -- Build the distinct exact routes once. Creating absent zero-generation rows
 -- setwise is safe under the graph gate; the ordered guard read below verifies
 -- every route and takes each row lock exactly once.
 WITH exact_routes AS MATERIALIZED (
  SELECT DISTINCT decode(value->>'namespace','hex') namespace_bytes,decode(value->>'transport','hex') key_bytes
  FROM jsonb_array_elements(all_routes)), hashes AS MATERIALIZED (
  SELECT DISTINCT sha256(namespace_bytes) namespace_sha256,sha256(key_bytes) key_sha256 FROM exact_routes)
 INSERT INTO truss.key_bucket_guard(namespace_sha256,key_sha256,generation)
 SELECT h.namespace_sha256,h.key_sha256,0 FROM hashes h
 LEFT JOIN truss.key_bucket_guard g USING(namespace_sha256,key_sha256)
 WHERE g.namespace_sha256 IS NULL ORDER BY h.namespace_sha256,h.key_sha256
 ON CONFLICT(namespace_sha256,key_sha256) DO NOTHING;
 WITH exact_routes AS MATERIALIZED (
  SELECT DISTINCT decode(value->>'namespace','hex') namespace_bytes,decode(value->>'transport','hex') key_bytes
  FROM jsonb_array_elements(all_routes)), hashes AS MATERIALIZED (
  SELECT DISTINCT sha256(namespace_bytes) namespace_sha256,sha256(key_bytes) key_sha256 FROM exact_routes)
 SELECT coalesce(jsonb_agg(jsonb_build_object('namespaceHash',encode(locked.namespace_sha256,'hex'),
  'keyHash',encode(locked.key_sha256,'hex'),'generation',locked.generation)
  ORDER BY locked.namespace_sha256,locked.key_sha256),'[]'::jsonb)
 INTO guard_rows FROM (
  SELECT g.namespace_sha256,g.key_sha256,g.generation FROM truss.key_bucket_guard g JOIN hashes h USING(namespace_sha256,key_sha256)
  ORDER BY g.namespace_sha256,g.key_sha256 FOR UPDATE OF g NOWAIT) locked;
 IF jsonb_array_length(guard_rows)<>(SELECT count(*) FROM (SELECT DISTINCT sha256(decode(value->>'namespace','hex')) ns,
   sha256(decode(value->>'transport','hex')) ky FROM jsonb_array_elements(all_routes)) h) THEN
  RAISE EXCEPTION 'complete native key guard inventory required' USING ERRCODE='55000';END IF;
 -- One bounded scan per hash bucket computes collision-budget statistics;
 -- exact byte membership is aggregated separately for each original route.
 WITH exact_routes AS MATERIALIZED (
  SELECT DISTINCT decode(value->>'namespace','hex') namespace_bytes,decode(value->>'transport','hex') key_bytes
  FROM jsonb_array_elements(all_routes)), hashes AS MATERIALIZED (
  SELECT DISTINCT sha256(namespace_bytes) namespace_sha256,sha256(key_bytes) key_sha256 FROM exact_routes),
 stats AS MATERIALIZED (
  SELECT h.namespace_sha256,h.key_sha256,b.candidate_count,b.candidate_bytes
  FROM hashes h CROSS JOIN LATERAL (
   SELECT count(*) candidate_count,coalesce(sum(c.size),0) candidate_bytes FROM (
    (SELECT octet_length(g.namespace_bytes)::bigint+octet_length(g.key_bytes) size
     FROM truss.object_key_bucket g WHERE g.namespace_sha256=h.namespace_sha256 AND g.key_sha256=h.key_sha256 LIMIT 10001)
    UNION ALL
    (SELECT octet_length(g.namespace_bytes)::bigint+octet_length(g.key_bytes) size
     FROM truss.object_key_reservation_bucket g WHERE g.namespace_sha256=h.namespace_sha256 AND g.key_sha256=h.key_sha256 LIMIT 10001)
   ) c
  ) b),
 memberships AS (SELECT r.namespace_bytes,r.key_bytes,
  coalesce(jsonb_agg(jsonb_build_object('storage_row_id',m.storage_row_id,'object_id',m.object_id,'type_id',m.type_id,
   'key_num',m.key_num,'namespaceExact',m.namespace_bytes=r.namespace_bytes,'keyExact',m.key_bytes=r.key_bytes)
   ORDER BY m.storage_row_id) FILTER(WHERE m.storage_row_id IS NOT NULL),'[]'::jsonb) member_rows
  FROM exact_routes r JOIN stats s ON s.namespace_sha256=sha256(r.namespace_bytes) AND s.key_sha256=sha256(r.key_bytes)
   AND s.candidate_count<=10000 AND s.candidate_bytes<=16777216
  LEFT JOIN truss.object_key_bucket m ON m.namespace_sha256=sha256(r.namespace_bytes)
   AND m.key_sha256=sha256(r.key_bytes) AND m.namespace_bytes=r.namespace_bytes AND m.key_bytes=r.key_bytes
  GROUP BY r.namespace_bytes,r.key_bytes),
 reservations AS (SELECT r.namespace_bytes,r.key_bytes,
  coalesce(jsonb_agg(q.storage_row_id ORDER BY q.storage_row_id) FILTER(WHERE q.storage_row_id IS NOT NULL),'[]'::jsonb) reservation_ids
  FROM exact_routes r JOIN stats s ON s.namespace_sha256=sha256(r.namespace_bytes) AND s.key_sha256=sha256(r.key_bytes)
   AND s.candidate_count<=10000 AND s.candidate_bytes<=16777216
  LEFT JOIN truss.object_key_reservation_bucket q ON q.namespace_sha256=sha256(r.namespace_bytes)
   AND q.key_sha256=sha256(r.key_bytes) AND q.namespace_bytes=r.namespace_bytes AND q.key_bytes=r.key_bytes
  GROUP BY r.namespace_bytes,r.key_bytes), observed_routes AS (
  SELECT r.namespace_bytes,r.key_bytes,(g.value->>'generation')::bigint generation,coalesce(s.candidate_count,0) candidate_count,
   coalesce(s.candidate_bytes,0) candidate_bytes,m.member_rows,q.reservation_ids
  FROM exact_routes r JOIN jsonb_array_elements(guard_rows) g(value) ON g.value->>'namespaceHash'=encode(sha256(r.namespace_bytes),'hex')
   AND g.value->>'keyHash'=encode(sha256(r.key_bytes),'hex')
  JOIN stats s ON s.namespace_sha256=sha256(r.namespace_bytes) AND s.key_sha256=sha256(r.key_bytes)
  LEFT JOIN memberships m USING(namespace_bytes,key_bytes) LEFT JOIN reservations q USING(namespace_bytes,key_bytes))
 SELECT coalesce(jsonb_agg(jsonb_build_object('namespace',encode(namespace_bytes,'hex'),'transport',encode(key_bytes,'hex'),
  'generation',generation,'candidateCount',candidate_count,'candidateBytes',candidate_bytes,
  'memberRows',coalesce(member_rows,'[]'::jsonb),'reservationIds',coalesce(reservation_ids,'[]'::jsonb))),'[]'::jsonb)
 INTO route_observations FROM observed_routes;
 IF jsonb_array_length(route_observations)<>(SELECT count(*) FROM (SELECT DISTINCT decode(value->>'namespace','hex') ns,
   decode(value->>'transport','hex') ky FROM jsonb_array_elements(all_routes)) r) THEN
  RAISE EXCEPTION 'complete native key observation inventory required' USING ERRCODE='55000';END IF;
 -- Retired live memberships are locked/checked before current active routes,
 -- matching the former two-phase ordering. Their bytes are not reinterpreted.
 FOR route IN SELECT DISTINCT ON ((r.value->>'namespace') COLLATE "C",(r.value->>'transport') COLLATE "C") r.value entry,o.value observation FROM jsonb_array_elements(lock_routes) r
  JOIN jsonb_array_elements(route_observations) o ON o.value->>'namespace'=r.value->>'namespace'
   AND o.value->>'transport'=r.value->>'transport'
  ORDER BY (r.value->>'namespace') COLLATE "C",(r.value->>'transport') COLLATE "C" LOOP
  IF (route.observation->>'candidateCount')::bigint>10000 OR (route.observation->>'candidateBytes')::bigint>16777216 THEN
   RAISE EXCEPTION 'complete collision bucket exceeds limits' USING ERRCODE='54000';END IF;
  IF (route.observation->>'generation')::bigint=9223372036854775807 THEN
   RAISE EXCEPTION 'key guard generation exhausted' USING ERRCODE='54000';END IF;
 END LOOP;
 -- Preserve operation-order error selection while all exact bucket observations
 -- and guard locks are shared by every repeated route.
 FOR route IN SELECT r.value entry,
  lag(r.value->>'reference') OVER route_history previous_reference,
  lag(r.ordinality) OVER route_history previous_ordinal,o.value observation
  FROM jsonb_array_elements(routes) WITH ORDINALITY r(value,ordinality)
  JOIN jsonb_array_elements(route_observations) o ON o.value->>'namespace'=r.value->>'namespace'
   AND o.value->>'transport'=r.value->>'transport'
  WINDOW route_history AS (PARTITION BY (r.value->>'namespace') COLLATE "C",(r.value->>'transport') COLLATE "C" ORDER BY r.ordinality)
  ORDER BY r.ordinality LOOP
  entry:=route.entry;namespace:=decode(entry->>'namespace','hex');transport:=decode(entry->>'transport','hex');reference:=entry->>'reference';
  IF (route.observation->>'candidateCount')::bigint>10000 OR (route.observation->>'candidateBytes')::bigint>16777216 THEN
   RAISE EXCEPTION 'complete collision bucket exceeds limits' USING ERRCODE='54000';END IF;
  IF (route.observation->>'generation')::bigint=9223372036854775807 THEN
   RAISE EXCEPTION 'key guard generation exhausted' USING ERRCODE='54000';END IF;
  IF entry->>'phase'='initial' THEN
   IF jsonb_array_length(route.observation->'memberRows')<>1 THEN RAISE EXCEPTION 'one original live key member required' USING ERRCODE='55000';END IF;
   member:=jsonb_populate_record(NULL::truss.object_key_bucket,route.observation->'memberRows'->0);
   IF member.object_id::text IS DISTINCT FROM entry->>'objectId' OR member.type_id IS DISTINCT FROM (entry->>'typeId')::int
    OR member.key_num IS DISTINCT FROM (entry->>'keyNumber')::smallint
    OR route.observation->'memberRows'->0->>'namespaceExact' IS DISTINCT FROM 'true'
    OR route.observation->'memberRows'->0->>'keyExact' IS DISTINCT FROM 'true' THEN
    RAISE EXCEPTION 'original key membership and values required' USING ERRCODE='55000';END IF;
  ELSIF entry->'unchanged'='true'::jsonb THEN
   IF route.previous_reference IS DISTINCT FROM reference THEN RAISE EXCEPTION 'original unchanged key owner required' USING ERRCODE='55000';END IF;
  ELSE
   IF route.previous_ordinal IS NOT NULL OR jsonb_array_length(route.observation->'memberRows')>0
    OR jsonb_array_length(route.observation->'reservationIds')>0 THEN
    RAISE EXCEPTION 'key already allocated or reserved' USING ERRCODE='23505';END IF;
  END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_key_preflight(jsonb) FROM PUBLIC;

-- Check each changed object against its original operation, including descendants.
-- Physical before-images chain to the captured scope or an earlier original step.
CREATE FUNCTION truss.runtime_owned_object_transition_validate_qualified(selected_transition bigint,authorize_read boolean,qualified_actor oid,prepared_input jsonb DEFAULT NULL,source_bytes bytea DEFAULT NULL,prepared_attempt truss.runtime_object_attempt DEFAULT NULL,compiled_history jsonb DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE transition truss.runtime_object_transition%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;
 plan jsonb;reference text;candidate text;identity jsonb;prior jsonb;desired jsonb;previous_image jsonb;
 original_mode text;expected_version bigint;matches int:=0;has_previous boolean;property truss.prop_def;pin record;expected_property_pin text;
 expected_events jsonb;expected_event_buffer jsonb[]:=ARRAY[]::jsonb[];expected_event jsonb;journal jsonb;event jsonb;ordinal int:=0;
 before_record jsonb;after_record jsonb;semantic_events jsonb;semantic_event_buffer jsonb[]:=ARRAY[]::jsonb[];group_pin jsonb;input jsonb;history_key text;history_metadata jsonb;completed_slots bigint;
BEGIN
 IF authorize_read IS NULL THEN RAISE EXCEPTION 'explicit object validation mode required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT transition FROM truss.runtime_object_transition WHERE transition_id=selected_transition;
 -- Independent updates retain versioned journal references. Resolve the sole
 -- physical payload owner before the unchanged semantic and wrapper checks.
 transition.journal:=truss.runtime_owned_journal_materialize(transition.journal);
 IF prepared_attempt.id IS NOT NULL THEN
   IF prepared_attempt.id IS DISTINCT FROM transition.attempt_id THEN RAISE EXCEPTION 'original checked attempt required' USING ERRCODE='55000';END IF;
   attempt:=prepared_attempt;
  ELSE SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=transition.attempt_id;END IF;
 IF prepared_input IS NOT NULL AND (source_bytes IS NULL OR source_bytes IS DISTINCT FROM attempt.input_bytes) THEN
  RAISE EXCEPTION 'original checked transition input required' USING ERRCODE='55000';END IF;
 -- Only the existing private settlement call supplies all checked context.
 -- Its complete immutable slot census is already closed by group_validate;
 -- standalone and history validation retain their independent census.
 IF NOT authorize_read AND prepared_attempt.id IS NOT NULL AND prepared_input IS NOT NULL AND compiled_history IS NOT NULL THEN
  completed_slots:=attempt.next_index;
 ELSE
  SELECT count(*) INTO completed_slots FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.result IS NOT NULL;
 END IF;
 IF attempt.writer_xid IS DISTINCT FROM transition.writer_xid OR transition.operation_index<0 OR transition.operation_index>=attempt.next_index
  OR completed_slots<>attempt.next_index OR (authorize_read AND NOT attempt.complete)
  OR (NOT authorize_read AND (attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM qualified_actor)) THEN
  RAISE EXCEPTION 'original completed object operation progress required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(attempt.id,transition.operation_index);
 FOR candidate IN SELECT key FROM jsonb_each(plan->'afterNodes') LOOP
  identity:=truss.runtime_owned_identity(attempt.id,transition.operation_index,candidate,'object',plan,attempt);
  IF identity->>'id'=transition.object_id::text AND identity->>'typeId'=transition.type_id::text THEN reference:=candidate;matches:=matches+1;END IF;
 END LOOP;
 IF matches<>1 THEN RAISE EXCEPTION 'one original object plan member required' USING ERRCODE='55000';END IF;
 identity:=truss.runtime_owned_identity(attempt.id,transition.operation_index,reference,'object',plan,attempt);
 prior:=plan->'beforeNodes'->reference;desired:=plan->'afterNodes'->reference;original_mode:=plan->'operation'->>'operation';
 IF transition.before_object IS NULL THEN
  IF original_mode IS DISTINCT FROM 'create_object' OR reference IS DISTINCT FROM plan->>'primary'
   OR transition.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(attempt.id,transition.operation_index,reference,'after',plan,attempt) THEN
   RAISE EXCEPTION 'original object creation required' USING ERRCODE='55000';END IF;
  IF NOT authorize_read THEN
   IF compiled_history IS NOT NULL THEN
    history_key:=jsonb_build_array((transition.after_object->>'rev')::int,(transition.after_object->>'type_id')::int)::text;
    history_metadata:=compiled_history->history_key;
    IF history_metadata IS NULL THEN RAISE EXCEPTION 'complete compiled creation history required' USING ERRCODE='55000';END IF;
   END IF;
   PERFORM truss.runtime_create_transition_validate_qualified(selected_transition,qualified_actor,prepared_input,source_bytes,attempt,history_metadata);
  END IF;
  RETURN;
 END IF;
 input:=CASE WHEN authorize_read AND attempt.context ? 'originalAssertedOrigin'
  THEN jsonb_build_object('assertedOrigin',attempt.context->'originalAssertedOrigin')
  ELSE coalesce(prepared_input,convert_from(attempt.input_bytes,'UTF8')::jsonb) END;
 IF original_mode NOT IN ('update_object','delete_object') OR prior IS NULL OR desired IS NULL
  OR prior->'deleted'='true'::jsonb OR prior IS NOT DISTINCT FROM desired
  OR (original_mode='update_object' AND desired->'deleted' IS DISTINCT FROM 'false'::jsonb)
  OR (original_mode='delete_object' AND desired->'deleted' IS DISTINCT FROM 'true'::jsonb)
  OR transition.before_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(attempt.id,transition.operation_index,reference,'before',plan,attempt)
  OR transition.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(attempt.id,transition.operation_index,reference,'after',plan,attempt) THEN
  RAISE EXCEPTION 'original changed object plan and images required' USING ERRCODE='55000';END IF;
 SELECT after_object INTO previous_image FROM truss.runtime_object_transition WHERE attempt_id=attempt.id
  AND object_id=transition.object_id AND type_id=transition.type_id AND operation_index<transition.operation_index ORDER BY operation_index DESC LIMIT 1;
 has_previous:=FOUND;
 IF NOT has_previous THEN
  SELECT jsonb_extract_path(p.plan,'initialScope','nodes',transition.type_id::text||':'||transition.object_id::text) INTO STRICT previous_image
   FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id AND p.operation_index=0;
 END IF;
 IF transition.before_object IS DISTINCT FROM previous_image THEN RAISE EXCEPTION 'original physical object prestate chain required' USING ERRCODE='55000';END IF;
 expected_version:=(transition.before_object->>'ver')::bigint+1;
 IF compiled_history IS NULL THEN before_record:=truss.runtime_object_history(transition.before_object,identity);
 ELSE
  history_key:=jsonb_build_array((transition.before_object->>'rev')::int,(transition.before_object->>'type_id')::int)::text;
  history_metadata:=compiled_history->history_key;
  IF history_metadata IS NULL THEN RAISE EXCEPTION 'complete compiled history census required' USING ERRCODE='55000';END IF;
  before_record:=truss.runtime_owned_history_record_in_metadata(transition.before_object,identity,history_metadata);
 END IF;
 IF transition.after_object IS NOT NULL THEN
  IF transition.after_object->>'ver' IS DISTINCT FROM expected_version::text
   OR transition.after_object->'created_at' IS DISTINCT FROM transition.before_object->'created_at' THEN
   RAISE EXCEPTION 'one object version advance and original creation time required' USING ERRCODE='55000';END IF;
  IF compiled_history IS NULL THEN after_record:=truss.runtime_object_history(transition.after_object,identity);
 ELSE
  history_key:=jsonb_build_array((transition.after_object->>'rev')::int,(transition.after_object->>'type_id')::int)::text;
  history_metadata:=compiled_history->history_key;
  IF history_metadata IS NULL THEN RAISE EXCEPTION 'complete compiled history census required' USING ERRCODE='55000';END IF;
  after_record:=truss.runtime_owned_history_record_in_metadata(transition.after_object,identity,history_metadata);
 END IF;
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=transition.type_id AND since_rev<=(plan->>'catalogRevision')::int
   AND (retired_rev IS NULL OR retired_rev>(plan->>'catalogRevision')::int) ORDER BY prop_id LOOP
   IF transition.before_object->'props'->property.prop_id::text IS DISTINCT FROM transition.after_object->'props'->property.prop_id::text THEN
    -- The settlement dictionary was independently resolved for this invocation.
    -- Reuse only its exact type/revision/property pin; absent entries (including
    -- removals across revisions) retain the original STRICT reconstruction.
    IF compiled_history IS NOT NULL AND history_metadata->>'typeId'=transition.type_id::text
     AND history_metadata->>'revision'=plan->>'catalogRevision'
     AND jsonb_typeof(history_metadata->'propertyPins'->property.prop_id::text)='string' THEN
     expected_property_pin:=history_metadata->'propertyPins'->>property.prop_id::text;
    ELSE
     SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',transition.type_id,property.prop_id,(plan->>'catalogRevision')::int);
     expected_property_pin:=pin.definition_pin;
    END IF;
    expected_event_buffer:=array_append(expected_event_buffer,jsonb_build_object('operation','property','propertyId',property.prop_id::text,'definitionPin',expected_property_pin,
     'before',CASE WHEN transition.before_object->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',transition.before_object->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END,
     'after',CASE WHEN transition.after_object->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',transition.after_object->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END));
   END IF;
  END LOOP;
  expected_event_buffer:=array_append(expected_event_buffer,jsonb_build_object('operation','metadata','before',before_record,'after',after_record));
 ELSE expected_event_buffer:=array_append(expected_event_buffer,jsonb_build_object('operation','delete','before',before_record));END IF;
 expected_events:=to_jsonb(expected_event_buffer);
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
  semantic_event_buffer:=array_append(semantic_event_buffer,event-'mutationGroup');ordinal:=ordinal+1;
 END LOOP;
 semantic_events:=to_jsonb(semantic_event_buffer);
 IF group_pin IS DISTINCT FROM jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',ordinal::text,
  'orderedEventDigest',encode(sha256(convert_to(semantic_events::text,'UTF8')),'hex')) THEN
  RAISE EXCEPTION 'complete original owned event group required' USING ERRCODE='55000';END IF;
 IF authorize_read THEN
  PERFORM truss.runtime_history_ownership(before_record);
  IF after_record IS NOT NULL THEN PERFORM truss.runtime_history_ownership(after_record);END IF;
 ELSE
  PERFORM truss.runtime_module_writer_qualified(identity->'owner'->>'documentId',identity->'owner'->>'moduleId',qualified_actor);
  IF NOT truss.runtime_object_values_readable_qualified(transition.type_id,qualified_actor) THEN RAISE EXCEPTION 'current original property readers required' USING ERRCODE='42501';END IF;
  PERFORM truss.runtime_history_ownership_qualified(before_record,qualified_actor);
  IF after_record IS NOT NULL THEN PERFORM truss.runtime_history_ownership_qualified(after_record,qualified_actor);END IF;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_transition_validate_qualified(bigint,boolean,oid,jsonb,bytea,truss.runtime_object_attempt,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_object_transition_validate(selected_transition bigint,authorize_read boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_owned_object_transition_validate_qualified(selected_transition,authorize_read,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_transition_validate(bigint,boolean) FROM PUBLIC;
