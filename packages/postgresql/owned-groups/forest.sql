-- Private valid-forest projection, not installed by the public runtime.
-- Ordinals refer to the executor's complete scoped simulation, never native IDs.
-- The executor retains and authenticates its original identity/alias map separately.
-- Invoke only at states requiring forest validity; final checks remain deferred.
CREATE FUNCTION truss.owned_forest_projection(node_count int,owned_edges jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE parents int[];seen_edges boolean[];entry jsonb;edge_number int;source_node int;target_node int;
 node_number int;ancestor int;path int[];incoming jsonb;result_json jsonb:='[]';
BEGIN
 IF node_count IS NULL OR node_count NOT BETWEEN 0 AND 1024 THEN
  RAISE EXCEPTION 'bounded local node count required' USING ERRCODE='54000';END IF;
 IF jsonb_typeof(owned_edges) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'explicit local owned edges required' USING ERRCODE='22023';END IF;
 IF octet_length(convert_to(owned_edges::text,'UTF8'))>1048576 OR jsonb_array_length(owned_edges)>1024 THEN
  RAISE EXCEPTION 'bounded local owned edges required' USING ERRCODE='54000';END IF;
 parents:=array_fill(-1,ARRAY[node_count]);seen_edges:=array_fill(false,ARRAY[1024]);
 FOR entry IN SELECT value FROM jsonb_array_elements(owned_edges) LOOP
  IF jsonb_typeof(entry) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'exact local edge required' USING ERRCODE='22023';END IF;
  IF entry-ARRAY['edge','source','target']<>'{}'::jsonb
   OR jsonb_typeof(entry->'edge') IS DISTINCT FROM 'number'
   OR jsonb_typeof(entry->'source') IS DISTINCT FROM 'number'
   OR jsonb_typeof(entry->'target') IS DISTINCT FROM 'number' THEN
   RAISE EXCEPTION 'closed local edge fields required' USING ERRCODE='22023';END IF;
  IF (entry->>'edge') !~ '^(0|[1-9][0-9]{0,3})$'
   OR (entry->>'source') !~ '^(0|[1-9][0-9]{0,3})$'
   OR (entry->>'target') !~ '^(0|[1-9][0-9]{0,3})$' THEN
   RAISE EXCEPTION 'bounded integer local references required' USING ERRCODE='22023';END IF;
  edge_number:=(entry->>'edge')::int;source_node:=(entry->>'source')::int;target_node:=(entry->>'target')::int;
  IF edge_number>=1024 OR source_node>=node_count OR target_node>=node_count THEN
   RAISE EXCEPTION 'local reference outside complete simulation' USING ERRCODE='22023';END IF;
  IF seen_edges[edge_number+1] THEN
   RAISE EXCEPTION 'duplicate local edge reference' USING ERRCODE='22023';END IF;
  seen_edges[edge_number+1]:=true;
  IF parents[target_node+1]<>-1 AND parents[target_node+1]<>source_node THEN
   RAISE EXCEPTION 'multiple ownership parents' USING ERRCODE='22023';END IF;
  parents[target_node+1]:=source_node;
 END LOOP;
 FOR node_number IN 0..node_count-1 LOOP
  ancestor:=node_number;path:='{}';
  LOOP
   IF ancestor=ANY(path) THEN RAISE EXCEPTION 'ownership cycle' USING ERRCODE='22023';END IF;
   path:=array_append(path,ancestor);
   EXIT WHEN parents[ancestor+1]=-1;
   ancestor:=parents[ancestor+1];
  END LOOP;
  SELECT coalesce(jsonb_agg((value->>'edge')::int ORDER BY (value->>'edge')::int),'[]'::jsonb)
   INTO incoming FROM jsonb_array_elements(owned_edges) WHERE (value->>'target')::int=node_number;
  result_json:=result_json||jsonb_build_array(jsonb_build_object('node',node_number,
   'parent',nullif(parents[node_number+1],-1),'root',CASE WHEN ancestor=node_number THEN NULL ELSE ancestor END,
   'incomingEdges',incoming));
 END LOOP;
 IF octet_length(convert_to(result_json::text,'UTF8'))>4194304 THEN
  RAISE EXCEPTION 'bounded complete forest result required' USING ERRCODE='54000';END IF;
 RETURN result_json;
END;
$$;
REVOKE ALL ON FUNCTION truss.owned_forest_projection(int,jsonb) FROM PUBLIC;
