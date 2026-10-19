-- Private valid-forest projection used by the installed owned runtime.
-- Ordinals refer to the executor's complete scoped simulation, never native IDs.
-- The executor retains its original identity/alias mapping separately.
-- Invoke only at states requiring forest validity; final checks remain deferred.
CREATE FUNCTION truss.owned_forest_projection(node_count int,owned_edges jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE parents int[];seen_edges boolean[];entry jsonb;edge_number int;source_node int;target_node int;
 node_number int;ancestor int;path int[];path_count int;path_index int;root_node int;
 marks int[];roots int[];result_json jsonb;
BEGIN
 IF node_count IS NULL OR node_count NOT BETWEEN 0 AND 2048 THEN
  RAISE EXCEPTION 'bounded local node count required' USING ERRCODE='54000';END IF;
 IF jsonb_typeof(owned_edges) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'explicit local owned edges required' USING ERRCODE='22023';END IF;
 IF octet_length(convert_to(owned_edges::text,'UTF8'))>1048576 OR jsonb_array_length(owned_edges)>1024 THEN
  RAISE EXCEPTION 'bounded local owned edges required' USING ERRCODE='54000';END IF;
 parents:=array_fill(-1,ARRAY[node_count]);roots:=array_fill(-1,ARRAY[node_count]);seen_edges:=array_fill(false,ARRAY[1024]);
 marks:=array_fill(0,ARRAY[node_count]);path:=array_fill(-1,ARRAY[node_count]);
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
 -- Resolve each parent chain once. A visiting node belongs to this walk;
 -- completed chains already retain the root for every member on their path.
 FOR node_number IN 0..node_count-1 LOOP
  IF marks[node_number+1]=2 THEN CONTINUE;END IF;
  ancestor:=node_number;path_count:=0;
  LOOP
   IF marks[ancestor+1]=2 THEN
    root_node:=CASE WHEN roots[ancestor+1]=-1 THEN ancestor ELSE roots[ancestor+1] END;
    EXIT;
   END IF;
   IF marks[ancestor+1]=1 THEN RAISE EXCEPTION 'ownership cycle' USING ERRCODE='22023';END IF;
   marks[ancestor+1]:=1;path_count:=path_count+1;path[path_count]:=ancestor;
   IF parents[ancestor+1]=-1 THEN root_node:=ancestor;EXIT;END IF;
   ancestor:=parents[ancestor+1];
  END LOOP;
  FOR path_index IN 1..path_count LOOP
   ancestor:=path[path_index];
   roots[ancestor+1]:=CASE WHEN ancestor=root_node THEN -1 ELSE root_node END;
   marks[ancestor+1]:=2;
  END LOOP;
 END LOOP;
 -- Assemble once after validation and the memoized root walk. Repeated JSONB
 -- concatenation and one full edge scan per node made this projection quadratic.
 SELECT coalesce(jsonb_agg(jsonb_build_object('node',n.node,
  'parent',nullif(parents[n.node+1],-1),'root',nullif(roots[n.node+1],-1),
  'incomingEdges',coalesce(incoming.edges,'[]'::jsonb)) ORDER BY n.node),'[]'::jsonb)
 INTO result_json FROM generate_series(0,node_count-1) n(node)
 LEFT JOIN (SELECT (value->>'target')::int target,
  jsonb_agg((value->>'edge')::int ORDER BY (value->>'edge')::int) edges
  FROM jsonb_array_elements(owned_edges) GROUP BY (value->>'target')::int) incoming
 ON incoming.target=n.node;
 IF octet_length(convert_to(result_json::text,'UTF8'))>4194304 THEN
  RAISE EXCEPTION 'bounded complete forest result required' USING ERRCODE='54000';END IF;
 RETURN result_json;
END;
$$;
REVOKE ALL ON FUNCTION truss.owned_forest_projection(int,jsonb) FROM PUBLIC;
