-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Ordered simulation only. The executor supplies the complete current graph
-- after earlier operations; a later unlink cannot rescue this delete.
CREATE FUNCTION truss.owned_delete_projection(node_count int,owned_edges jsonb,
 independent_edges jsonb,delete_node int) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE entry jsonb;deleted int[];prior_count int;edge_number int;
 source_node int;target_node int;seen_edges int[]:='{}';deleted_edges jsonb;
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
   OR edge_number=ANY(seen_edges) THEN
   RAISE EXCEPTION 'unique local edge correspondence required' USING ERRCODE='22023';END IF;
  seen_edges:=array_append(seen_edges,edge_number);
 END LOOP;
 deleted:=ARRAY[delete_node];
 LOOP
  prior_count:=cardinality(deleted);
  SELECT array_agg(DISTINCT n ORDER BY n) INTO deleted FROM (
   SELECT unnest(deleted) AS n UNION ALL
   SELECT (value->>'target')::int FROM jsonb_array_elements(owned_edges)
    WHERE (value->>'source')::int=ANY(deleted)) expanded;
  EXIT WHEN cardinality(deleted)=prior_count;
 END LOOP;
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
   OR edge_number=ANY(seen_edges) THEN
   RAISE EXCEPTION 'unique local edge correspondence required' USING ERRCODE='22023';END IF;
  seen_edges:=array_append(seen_edges,edge_number);
  IF source_node=ANY(deleted) OR target_node=ANY(deleted) THEN
   RAISE EXCEPTION 'independent incident edge prevents owned deletion' USING ERRCODE='22023';END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg((value->>'edge')::int ORDER BY (value->>'edge')::int),'[]'::jsonb)
  INTO deleted_edges FROM jsonb_array_elements(owned_edges)
  WHERE (value->>'source')::int=ANY(deleted) OR (value->>'target')::int=ANY(deleted);
 RETURN jsonb_build_object('deletedNodes',to_jsonb(deleted),'deletedEdges',deleted_edges);
END;
$$;
REVOKE ALL ON FUNCTION truss.owned_delete_projection(int,jsonb,jsonb,int) FROM PUBLIC;
