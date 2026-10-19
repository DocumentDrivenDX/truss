-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Ordered simulation only. The executor supplies the complete current graph
-- after earlier operations; a later unlink cannot rescue this delete.
CREATE FUNCTION truss.owned_delete_projection(node_count int,owned_edges jsonb,
 independent_edges jsonb,delete_node int) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE entry jsonb;deleted int[];edge_number int;
 source_node int;target_node int;seen_edges boolean[]:=array_fill(false,ARRAY[1024]);deleted_edges jsonb;
 children jsonb[];visited boolean[];queue int[];head int:=1;tail int:=1;child int;adjacency record;
BEGIN
 IF node_count IS NULL OR node_count NOT BETWEEN 0 AND 1024 THEN
  RAISE EXCEPTION 'bounded local node count required' USING ERRCODE='54000';END IF;
 IF delete_node IS NULL OR delete_node<0 OR delete_node>=node_count THEN
  RAISE EXCEPTION 'existing local delete node required' USING ERRCODE='22023';END IF;
 IF jsonb_typeof(independent_edges) IS DISTINCT FROM 'array'
  OR jsonb_typeof(owned_edges) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'explicit independent incident edges required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(independent_edges)+jsonb_array_length(owned_edges)>1024
  OR octet_length(convert_to(independent_edges::text,'UTF8'))>1048576
  OR octet_length(convert_to(owned_edges::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'bounded complete incident edges required' USING ERRCODE='54000';END IF;
 -- Shape admission only: cycles/multiple parents can exist between ordered
 -- operations. Their final-state validation belongs to the executor.
 FOR entry IN SELECT value FROM jsonb_array_elements(owned_edges) LOOP
  IF jsonb_typeof(entry) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'exact owned edge required' USING ERRCODE='22023';END IF;
  IF entry-ARRAY['edge','source','target']<>'{}'::jsonb
   OR jsonb_typeof(entry->'edge') IS DISTINCT FROM 'number'
   OR jsonb_typeof(entry->'source') IS DISTINCT FROM 'number'
   OR jsonb_typeof(entry->'target') IS DISTINCT FROM 'number'
   OR (entry->>'edge') !~ '^(0|[1-9][0-9]{0,3})$'
   OR (entry->>'source') !~ '^(0|[1-9][0-9]{0,3})$'
   OR (entry->>'target') !~ '^(0|[1-9][0-9]{0,3})$' THEN
   RAISE EXCEPTION 'closed bounded owned edge required' USING ERRCODE='22023';END IF;
  edge_number:=(entry->>'edge')::int;
  source_node:=(entry->>'source')::int;target_node:=(entry->>'target')::int;
  IF edge_number>=1024 OR source_node>=node_count OR target_node>=node_count
   OR seen_edges[edge_number+1] THEN
   RAISE EXCEPTION 'unique local edge correspondence required' USING ERRCODE='22023';END IF;
  seen_edges[edge_number+1]:=true;
 END LOOP;
 -- Build adjacency once and visit each reachable vertex/edge once, even
 -- when intermediate ordered states contain a cycle or multiple parents.
 children:=array_fill('[]'::jsonb,ARRAY[node_count]);
 FOR adjacency IN SELECT (value->>'source')::int source,
  jsonb_agg((value->>'target')::int) targets FROM jsonb_array_elements(owned_edges)
  GROUP BY (value->>'source')::int LOOP
  children[adjacency.source+1]:=adjacency.targets;
 END LOOP;
 visited:=array_fill(false,ARRAY[node_count]);visited[delete_node+1]:=true;queue:=ARRAY[delete_node];
 WHILE head<=tail LOOP
  source_node:=queue[head];head:=head+1;
  FOR child IN SELECT value::int FROM jsonb_array_elements_text(children[source_node+1]) LOOP
   IF NOT visited[child+1] THEN
    visited[child+1]:=true;tail:=tail+1;queue[tail]:=child;
   END IF;
  END LOOP;
 END LOOP;
 SELECT array_agg(n ORDER BY n) INTO deleted FROM generate_series(0,node_count-1) n WHERE visited[n+1];
 FOR entry IN SELECT value FROM jsonb_array_elements(independent_edges) LOOP
  IF jsonb_typeof(entry) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'exact independent edge required' USING ERRCODE='22023';END IF;
  IF entry-ARRAY['edge','source','target']<>'{}'::jsonb
   OR jsonb_typeof(entry->'edge') IS DISTINCT FROM 'number'
   OR jsonb_typeof(entry->'source') IS DISTINCT FROM 'number'
   OR jsonb_typeof(entry->'target') IS DISTINCT FROM 'number'
   OR (entry->>'edge') !~ '^(0|[1-9][0-9]{0,3})$'
   OR (entry->>'source') !~ '^(0|[1-9][0-9]{0,3})$'
   OR (entry->>'target') !~ '^(0|[1-9][0-9]{0,3})$' THEN
   RAISE EXCEPTION 'closed bounded independent edge required' USING ERRCODE='22023';END IF;
  edge_number:=(entry->>'edge')::int;
  source_node:=(entry->>'source')::int;target_node:=(entry->>'target')::int;
  -- Boundary witnesses occupy the following 256 ordinals. They cannot be
  -- selected for deletion or reached through owned_edges.
  IF edge_number>=1024 OR source_node>=node_count+256 OR target_node>=node_count+256
   OR seen_edges[edge_number+1] THEN
   RAISE EXCEPTION 'unique local edge correspondence required' USING ERRCODE='22023';END IF;
  seen_edges[edge_number+1]:=true;
  IF coalesce(visited[source_node+1],false) OR coalesce(visited[target_node+1],false) THEN
   RAISE EXCEPTION 'independent incident edge prevents owned deletion' USING ERRCODE='22023';END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg((value->>'edge')::int ORDER BY (value->>'edge')::int),'[]'::jsonb)
  INTO deleted_edges FROM jsonb_array_elements(owned_edges)
  WHERE visited[(value->>'source')::int+1] OR visited[(value->>'target')::int+1];
 RETURN jsonb_build_object('deletedNodes',to_jsonb(deleted),'deletedEdges',deleted_edges);
END;
$$;
REVOKE ALL ON FUNCTION truss.owned_delete_projection(int,jsonb,jsonb,int) FROM PUBLIC;
