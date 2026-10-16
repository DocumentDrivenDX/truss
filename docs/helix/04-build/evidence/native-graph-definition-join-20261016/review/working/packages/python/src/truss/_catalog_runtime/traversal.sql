-- One-call live traversal. The bounded CTE counts attempted states (cycles
-- included) before filtering, terminal deduplication or output ordering.
CREATE FUNCTION truss.traverse_objects(start_identity jsonb,hops jsonb,maximum_objects int,maximum_states int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation record;start_type truss.type_def;relation truss.rel_def;hop jsonb;relations int[]:=ARRAY[]::int[];directions text[]:=ARRAY[]::text[];
 captured_revision int;scope record;scope_types int[];types jsonb:='{}';properties_by_type jsonb:='{}';pins jsonb:='{}';properties truss.prop_def[];
 selected_type truss.type_def;observation record;frozen_object truss.object;frozen_root truss.object;root_definition truss.type_def;root_identity jsonb;root_owners jsonb:='{}';root_owner jsonb;objects jsonb:='[]';rendered bytea;result bytea;index int:=0;
BEGIN
 PERFORM truss.runtime_person(false);
 IF maximum_objects IS NULL OR maximum_objects NOT BETWEEN 1 AND 1000 OR maximum_states IS NULL OR maximum_states NOT BETWEEN 1 AND 10000
 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 OR hops IS NULL OR jsonb_typeof(hops) IS DISTINCT FROM 'array'
 OR jsonb_array_length(hops) NOT BETWEEN 1 AND 3 OR octet_length(hops::text)>65536 THEN RAISE EXCEPTION 'bounded traversal required' USING ERRCODE='22023';END IF;
 IF current_setting('transaction_read_only')='on' THEN SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 ELSE SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN RAISE EXCEPTION 'selected runtime required' USING ERRCODE='0A000';END IF;
 start_type:=truss.runtime_condition_type(start_identity);scope_types:=ARRAY[start_type.type_id];
 FOR hop IN SELECT value FROM jsonb_array_elements(hops) LOOP
  IF jsonb_typeof(hop) IS DISTINCT FROM 'object' OR hop-ARRAY['relationship','direction']<>'{}'::jsonb OR hop->>'direction' NOT IN ('outgoing','incoming','both')
  OR hop->>'direction' IS NULL OR jsonb_typeof(hop->'relationship') IS DISTINCT FROM 'object'
  OR (hop->'relationship')-ARRAY['kind','definitionPin','owner','authoredIdentity','relationshipId']<>'{}'::jsonb
  OR hop->'relationship'->>'kind' IS DISTINCT FROM 'relationship'
  OR coalesce(hop->'relationship'->>'relationshipId','') !~ '^[1-9][0-9]{0,9}$'
  OR (hop->'relationship'->>'relationshipId')::numeric>2147483647 THEN RAISE EXCEPTION 'qualified traversal hop required' USING ERRCODE='22023';END IF;
  SELECT * INTO relation FROM truss.rel_def WHERE rel_type_id=(hop->'relationship'->>'relationshipId')::int AND retired_rev IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'current relationship required' USING ERRCODE='22023';END IF;
  IF hop->'relationship'->>'definitionPin' IS DISTINCT FROM truss.runtime_relationship_pin(relation.rel_type_id)
  OR hop->'relationship'->>'authoredIdentity' IS DISTINCT FROM relation.rel_id
  OR hop->'relationship'->'owner' IS DISTINCT FROM jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module) THEN RAISE EXCEPTION 'current relationship pin required' USING ERRCODE='22023';END IF;
  IF relation.lifecycle NOT IN ('independent','owned') OR NOT relation.directed OR relation.assoc_type_id IS NOT NULL OR relation.composition THEN RAISE EXCEPTION 'directed traversal required' USING ERRCODE='0A000';END IF;
  IF NOT truss.runtime_can_read(relation.document_id,relation.module) THEN RETURN NULL;END IF;
  relations:=array_append(relations,relation.rel_type_id);directions:=array_append(directions,hop->>'direction');
  FOR scope IN SELECT source_type AS type_id FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id UNION SELECT target_type FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id LOOP scope_types:=array_append(scope_types,scope.type_id);END LOOP;
 END LOOP;
 -- Authorize the full declared expansion scope before observing any edge.
 FOR selected_type IN SELECT * FROM truss.type_def WHERE type_id=ANY(scope_types) LOOP
  IF NOT truss.runtime_object_values_readable(selected_type.type_id) THEN RETURN NULL;END IF;
  FOR scope IN SELECT DISTINCT declaration_module FROM truss.prop_def WHERE type_id=selected_type.type_id AND retired_rev IS NULL LOOP
   IF NOT truss.runtime_can_read(selected_type.document_id,scope.declaration_module) THEN RETURN NULL;END IF;
  END LOOP;
  types:=types||jsonb_build_object(selected_type.type_id::text,to_jsonb(selected_type));
  properties_by_type:=properties_by_type||jsonb_build_object(selected_type.type_id::text,(SELECT coalesce(jsonb_agg(p ORDER BY p.prop_id),'[]') FROM truss.prop_def p WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL));
  pins:=pins||jsonb_build_object(selected_type.type_id::text,(SELECT definition_pin FROM truss.runtime_definition('type',selected_type.type_id)));
 END LOOP;
 IF octet_length(types::text)+octet_length(properties_by_type::text)+octet_length(pins::text)>maximum_bytes THEN result:=convert_to('{"outcome":"limited","reason":"retained_bytes"}','UTF8');END IF;
 IF result IS NULL THEN
 -- This single data statement freezes existence, all edges, terminal objects
 -- and row-home facts. No volatile row reader is invoked during rendering.
 FOR observation IN
  WITH RECURSIVE expansion(depth,type_id,id,visited,cycle) AS (
   SELECT 0,o.type_id,o.id,ARRAY[o.type_id::text||':'||o.id::text],false FROM truss.object o WHERE o.type_id=start_type.type_id AND o.id=(start_identity->>'id')::bigint
   UNION ALL
   SELECT p.depth+1,n.type_id,n.id,array_append(p.visited,n.type_id::text||':'||n.id::text),n.type_id::text||':'||n.id::text=ANY(p.visited)
   FROM expansion p JOIN truss.edge e ON e.rel_type_id=relations[p.depth+1]
    AND ((directions[p.depth+1] IN ('outgoing','both') AND e.source_type=p.type_id AND e.source_id=p.id)
     OR (directions[p.depth+1] IN ('incoming','both') AND e.target_type=p.type_id AND e.target_id=p.id))
   CROSS JOIN LATERAL (SELECT e.target_type AS type_id,e.target_id AS id WHERE directions[p.depth+1] IN ('outgoing','both') AND e.source_type=p.type_id AND e.source_id=p.id
    UNION SELECT e.source_type,e.source_id WHERE directions[p.depth+1] IN ('incoming','both') AND e.target_type=p.type_id AND e.target_id=p.id) next
   JOIN truss.object n ON n.type_id=next.type_id AND n.id=next.id
   WHERE p.depth<array_length(relations,1) AND NOT p.cycle
  ), bounded AS MATERIALIZED (SELECT * FROM expansion LIMIT maximum_states+1),
  summary AS (SELECT count(*) AS states FROM bounded),nodes AS (
   SELECT type_id,id,bool_or(depth=array_length(relations,1) AND NOT cycle) AS terminal FROM bounded GROUP BY type_id,id)
  SELECT summary.states,n.terminal,o AS object,ro AS root,rt AS root_definition,
   false AS row_home
  FROM summary LEFT JOIN nodes n ON true LEFT JOIN truss.object o ON o.type_id=n.type_id AND o.id=n.id
  LEFT JOIN truss.object ro ON ro.type_id=o.root_type AND ro.id=o.root_id
  LEFT JOIN truss.type_def rt ON rt.type_id=ro.type_id AND rt.retired_rev IS NULL
  ORDER BY n.type_id,n.id
 LOOP
  IF observation.states>maximum_states THEN result:=convert_to('{"outcome":"limited","reason":"path_states"}','UTF8');END IF;
  IF observation.states=0 THEN result:=convert_to('{"outcome":"not_found"}','UTF8');EXIT;END IF;
  frozen_object:=observation.object;
  IF frozen_object.id IS NULL THEN RAISE EXCEPTION 'captured traversal object required' USING ERRCODE='55000';END IF;
  IF frozen_object.rev>captured_revision THEN RAISE EXCEPTION 'traversal object catalog changed' USING ERRCODE='55P03';END IF;
  frozen_root:=observation.root;root_definition:=observation.root_definition;root_identity:=NULL;
  IF frozen_object.root_id IS NOT NULL OR frozen_object.root_type IS NOT NULL THEN
   IF frozen_object.root_id IS NULL OR frozen_object.root_type IS NULL OR frozen_root.id IS NULL OR root_definition.type_id IS NULL
    OR frozen_root.root_id IS NOT NULL OR frozen_root.root_type IS NOT NULL
    OR frozen_root.id=frozen_object.id AND frozen_root.type_id=frozen_object.type_id
    OR root_definition.kind<>'record' OR root_definition.provisional THEN RAISE EXCEPTION 'captured traversal aggregate root required' USING ERRCODE='55000';END IF;
   IF frozen_root.rev>captured_revision OR root_definition.since_rev>captured_revision THEN RAISE EXCEPTION 'traversal root catalog changed' USING ERRCODE='55P03';END IF;
   IF NOT truss.runtime_can_read(root_definition.document_id,root_definition.module) THEN RETURN NULL;END IF;
   root_owner:=jsonb_build_object('documentId',root_definition.document_id,'moduleId',root_definition.module);
   root_owners:=root_owners||jsonb_build_object(root_owner::text,root_owner);
   IF octet_length(root_owners::text)>16777216 THEN RAISE EXCEPTION 'bounded traversal authority context required' USING ERRCODE='54000';END IF;
   root_identity:=jsonb_build_object('id',frozen_root.id::text,'typeId',frozen_root.type_id::text,
    'definitionPin',(SELECT d.definition_pin FROM truss.runtime_definition('type',frozen_root.type_id) d),'owner',root_owner);
  END IF;
  IF NOT observation.terminal OR result IS NOT NULL THEN CONTINUE;END IF;
  index:=index+1;
  IF index>maximum_objects THEN result:=convert_to('{"outcome":"limited","reason":"result_limit"}','UTF8');CONTINUE;END IF;
  selected_type:=jsonb_populate_record(NULL::truss.type_def,types->frozen_object.type_id::text);
  SELECT coalesce(array_agg(p ORDER BY p.prop_id),ARRAY[]::truss.prop_def[]) INTO properties FROM jsonb_populate_recordset(NULL::truss.prop_def,properties_by_type->frozen_object.type_id::text) p;
  BEGIN
  rendered:=truss.render_logical_object(frozen_object,selected_type,properties,observation.row_home,pins->>frozen_object.type_id::text,captured_revision,maximum_bytes,expected_release,expected_digest,root_identity);
  EXCEPTION WHEN SQLSTATE '54000' THEN result:=convert_to('{"outcome":"limited","reason":"retained_bytes"}','UTF8');
  END;
  IF result IS NOT NULL THEN CONTINUE;END IF;
  objects:=objects||jsonb_build_array(convert_from(rendered,'UTF8')::jsonb);
  IF octet_length(objects::text)>maximum_bytes THEN result:=convert_to('{"outcome":"limited","reason":"retained_bytes"}','UTF8');END IF;
 END LOOP;
 END IF;
 FOR selected_type IN SELECT * FROM truss.type_def WHERE type_id=ANY(scope_types) LOOP
  IF NOT truss.runtime_object_values_readable(selected_type.type_id) THEN RETURN NULL;END IF;
  FOR scope IN SELECT DISTINCT declaration_module FROM truss.prop_def WHERE type_id=selected_type.type_id AND retired_rev IS NULL LOOP IF NOT truss.runtime_can_read(selected_type.document_id,scope.declaration_module) THEN RETURN NULL;END IF;END LOOP;
 END LOOP;
 FOR relation IN SELECT * FROM truss.rel_def WHERE rel_type_id=ANY(relations) LOOP IF NOT truss.runtime_can_read(relation.document_id,relation.module) THEN RETURN NULL;END IF;END LOOP;
 FOR root_owner IN SELECT value FROM jsonb_each(root_owners) LOOP
  IF NOT truss.runtime_can_read(root_owner->>'documentId',root_owner->>'moduleId') THEN RETURN NULL;END IF;
 END LOOP;
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN RAISE EXCEPTION 'catalog changed during traversal' USING ERRCODE='55P03';END IF;
 IF result IS NULL THEN result:=convert_to(jsonb_build_object('outcome','complete','catalogRevision',captured_revision::text,'objects',objects)::text,'UTF8');END IF;
 IF octet_length(result)>maximum_bytes THEN RETURN convert_to('{"outcome":"limited","reason":"retained_bytes"}','UTF8');END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.traverse_objects(jsonb,jsonb,int,int,int,text,text) FROM PUBLIC;
