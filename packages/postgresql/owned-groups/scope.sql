-- Uninstalled observation component. One invocation uses one statement snapshot.
-- No locks, authority issuance or effects. Reobserve after the graph-write gate;
-- the executor must refuse newly required earlier guards before performing writes.
CREATE FUNCTION truss.owned_graph_scope(seeds jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE node_keys text[]:='{}';edge_keys text[]:='{}';boundary_keys text[]:='{}';owned_edge_order text[]:='{}';
 nodes jsonb:='{}';edges jsonb:='{}';boundary jsonb:='{}';types jsonb:='{}';relations jsonb:='{}';
 entry jsonb;image jsonb;relation_image jsonb;witness jsonb;definition jsonb;
 node_key text;other_key text;edge_key text;root_key text;selected_type int;selected_id bigint;
 selected_node int:=1;observed record;side text;projection jsonb;local_edges jsonb:='[]';local_index int:=0;
 result_json jsonb;used_bytes bigint:=0;head int;
BEGIN
 IF jsonb_typeof(seeds) IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'explicit typed scope seeds required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(seeds) NOT BETWEEN 0 AND 128 OR octet_length(convert_to(seeds::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'bounded scope seeds required' USING ERRCODE='54000';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(seeds) LOOP
  IF jsonb_typeof(entry) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'typed scope seed required' USING ERRCODE='22023';END IF;
  IF entry-ARRAY['typeId','id']<>'{}'::jsonb OR jsonb_typeof(entry->'typeId') IS DISTINCT FROM 'string'
   OR jsonb_typeof(entry->'id') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'exact typed seed fields required' USING ERRCODE='22023';END IF;
  IF entry->>'typeId' !~ '^[1-9][0-9]{0,9}$' OR entry->>'id' !~ '^[1-9][0-9]{0,18}$' THEN
   RAISE EXCEPTION 'positive exact native seed identities required' USING ERRCODE='22023';END IF;
  IF (entry->>'typeId')::bigint>2147483647 OR (entry->>'id')::numeric>9223372036854775807 THEN
   RAISE EXCEPTION 'native seed identity range exceeded' USING ERRCODE='22023';END IF;
  node_key:=(entry->>'typeId')||':'||(entry->>'id');
  IF node_key=ANY(node_keys) THEN RAISE EXCEPTION 'duplicate scope seed' USING ERRCODE='22023';END IF;
  node_keys:=array_append(node_keys,node_key);
 END LOOP;
 SELECT rev INTO STRICT head FROM truss.schema_head WHERE id=1;
 WHILE selected_node<=cardinality(node_keys) LOOP
  node_key:=node_keys[selected_node];selected_type:=split_part(node_key,':',1)::int;selected_id:=split_part(node_key,':',2)::bigint;
  SELECT to_jsonb(o) INTO STRICT image FROM truss.object o WHERE o.id=selected_id AND o.type_id=selected_type;
  SELECT to_jsonb(t) INTO STRICT definition FROM truss.type_def t WHERE t.type_id=selected_type;
  used_bytes:=used_bytes+octet_length(convert_to(image::text,'UTF8'))+octet_length(convert_to(definition::text,'UTF8'));
  IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
  nodes:=nodes||jsonb_build_object(node_key,image);types:=types||jsonb_build_object(selected_type::text,definition);
  FOR observed IN SELECT to_jsonb(e) AS edge_image,to_jsonb(r) AS relationship_image FROM truss.edge e
   JOIN truss.rel_def r ON r.rel_type_id=e.rel_type_id
   WHERE (e.source_id=selected_id AND e.source_type=selected_type) OR (e.target_id=selected_id AND e.target_type=selected_type)
   ORDER BY e.id LIMIT 1025 LOOP
   edge_key:=observed.edge_image->>'id';
   IF edge_key=ANY(edge_keys) THEN CONTINUE;END IF;
   IF cardinality(edge_keys)=1024 THEN RAISE EXCEPTION 'bounded incident edge image required' USING ERRCODE='54000';END IF;
   relation_image:=observed.relationship_image;
   IF relation_image->>'lifecycle' NOT IN ('owned','independent') OR relation_image->'retired_rev'<>'null'::jsonb THEN
    RAISE EXCEPTION 'supported current incident lifecycle required' USING ERRCODE='0A000';END IF;
   IF relation_image->>'lifecycle'='owned' AND (relation_image->'directed'<>'true'::jsonb
    OR relation_image->'composition'<>'false'::jsonb OR relation_image->'assoc_type_id'<>'null'::jsonb) THEN
    RAISE EXCEPTION 'selected parent to target ownership required' USING ERRCODE='0A000';END IF;
   used_bytes:=used_bytes+octet_length(convert_to(observed.edge_image::text,'UTF8'))+octet_length(convert_to(relation_image::text,'UTF8'));
   IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
   edge_keys:=array_append(edge_keys,edge_key);edges:=edges||jsonb_build_object(edge_key,observed.edge_image);
   relations:=relations||jsonb_build_object(relation_image->>'rel_type_id',relation_image);
   IF relation_image->>'lifecycle'='owned' THEN
    FOREACH side IN ARRAY ARRAY['source','target'] LOOP
     other_key:=(observed.edge_image->>(side||'_type'))||':'||(observed.edge_image->>(side||'_id'));
     IF NOT other_key=ANY(node_keys) THEN
      IF cardinality(node_keys)=128 THEN RAISE EXCEPTION 'bounded complete ownership component required' USING ERRCODE='54000';END IF;
      node_keys:=array_append(node_keys,other_key);
     END IF;
    END LOOP;
   END IF;
  END LOOP;
  selected_node:=selected_node+1;
 END LOOP;
 -- Outside independent endpoints are witnesses, not traversed components.
 FOREACH edge_key IN ARRAY edge_keys LOOP
  image:=edges->edge_key;relation_image:=relations->(image->>'rel_type_id');
  IF relation_image->>'lifecycle'='owned' THEN
   local_edges:=local_edges||jsonb_build_array(jsonb_build_object('edge',local_index,
    'source',array_position(node_keys,(image->>'source_type')||':'||(image->>'source_id'))-1,
    'target',array_position(node_keys,(image->>'target_type')||':'||(image->>'target_id'))-1));
   owned_edge_order:=array_append(owned_edge_order,edge_key);
   local_index:=local_index+1;
  ELSE
   FOREACH side IN ARRAY ARRAY['source','target'] LOOP
    other_key:=(image->>(side||'_type'))||':'||(image->>(side||'_id'));
    IF NOT other_key=ANY(node_keys) AND NOT other_key=ANY(boundary_keys) THEN
     IF cardinality(boundary_keys)=256 THEN RAISE EXCEPTION 'bounded boundary witnesses required' USING ERRCODE='54000';END IF;
     boundary_keys:=array_append(boundary_keys,other_key);
    END IF;
   END LOOP;
  END IF;
 END LOOP;
 IF cardinality(boundary_keys)>256 THEN RAISE EXCEPTION 'bounded boundary witnesses required' USING ERRCODE='54000';END IF;
 selected_node:=1;
 WHILE selected_node<=cardinality(boundary_keys) LOOP
  node_key:=boundary_keys[selected_node];selected_type:=split_part(node_key,':',1)::int;selected_id:=split_part(node_key,':',2)::bigint;
  SELECT jsonb_build_object('id',o.id,'type_id',o.type_id,'root_id',o.root_id,'root_type',o.root_type,'rev',o.rev,'ver',o.ver)
   INTO STRICT witness FROM truss.object o WHERE o.id=selected_id AND o.type_id=selected_type;
  SELECT to_jsonb(t) INTO STRICT definition FROM truss.type_def t WHERE t.type_id=selected_type;
  boundary:=boundary||jsonb_build_object(node_key,jsonb_build_object('object',witness,'definition',definition));
  used_bytes:=used_bytes+octet_length(convert_to(witness::text,'UTF8'))+octet_length(convert_to(definition::text,'UTF8'));
  IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
  IF witness->'root_id'<>'null'::jsonb THEN
   root_key:=(witness->>'root_type')||':'||(witness->>'root_id');
   IF NOT root_key=ANY(node_keys) AND NOT root_key=ANY(boundary_keys) THEN
    IF cardinality(boundary_keys)=256 THEN RAISE EXCEPTION 'bounded boundary root witnesses required' USING ERRCODE='54000';END IF;
    boundary_keys:=array_append(boundary_keys,root_key);
   END IF;
  END IF;
  selected_node:=selected_node+1;
 END LOOP;
 -- An aggregate root pointer without a connecting owned-edge path is corrupt
 -- membership, not permission to invent an edge or silently omit a cascade child.
 IF EXISTS(SELECT 1 FROM unnest(node_keys) n(node_key) JOIN truss.object o
   ON o.root_type=split_part(n.node_key,':',1)::int AND o.root_id=split_part(n.node_key,':',2)::bigint
   WHERE NOT (o.type_id::text||':'||o.id::text)=ANY(node_keys) LIMIT 1) THEN
  RAISE EXCEPTION 'complete stored aggregate membership correspondence required' USING ERRCODE='55000';
 END IF;
 projection:=truss.owned_forest_projection(cardinality(node_keys),local_edges);
 FOR entry IN SELECT value FROM jsonb_array_elements(projection) LOOP
  image:=nodes->node_keys[(entry->>'node')::int+1];
  IF entry->'root'='null'::jsonb THEN
   IF image->'root_id'<>'null'::jsonb OR image->'root_type'<>'null'::jsonb THEN RAISE EXCEPTION 'current rootless correspondence required' USING ERRCODE='55000';END IF;
  ELSE
   root_key:=node_keys[(entry->>'root')::int+1];
   IF (image->>'root_type')||':'||(image->>'root_id') IS DISTINCT FROM root_key THEN
    RAISE EXCEPTION 'current aggregate root correspondence required' USING ERRCODE='55000';END IF;
  END IF;
 END LOOP;
 result_json:=jsonb_build_object('catalogRevision',head,'nodeOrder',node_keys,'ownedEdgeOrder',owned_edge_order,'nodes',nodes,'edges',edges,
  'types',types,'relationships',relations,'boundary',boundary,'forest',projection);
 IF octet_length(convert_to(result_json::text,'UTF8'))>4194304 THEN RAISE EXCEPTION 'bounded complete graph image result required' USING ERRCODE='54000';END IF;
 RETURN result_json;
END;
$$;
REVOKE ALL ON FUNCTION truss.owned_graph_scope(jsonb) FROM PUBLIC;


-- Discover stored components from original operations before acquiring graph
-- locks. This grants no authority; the caller must authorize all discovered
-- owners, acquire the common gate, and compare a second observation.
CREATE FUNCTION truss.runtime_owned_input_scope(input jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE operation jsonb;object_references jsonb;reference jsonb;identity jsonb;
 seeds jsonb:='[]';seed jsonb;stored_edge truss.edge%ROWTYPE;reference_type truss.type_def%ROWTYPE;current_actor oid;
BEGIN
 IF jsonb_typeof(input->'operations') IS DISTINCT FROM 'array'
  OR jsonb_array_length(input->'operations') NOT BETWEEN 1 AND 128 THEN
  RAISE EXCEPTION 'bounded original operations required' USING ERRCODE='22023';END IF;
 FOR operation IN SELECT value FROM jsonb_array_elements(input->'operations') LOOP
  object_references:='[]';
  IF operation->>'operation' IN ('update_edge','delete_edge') THEN
   reference:=operation->'target';
   IF reference->>'state'='stored' THEN
    identity:=reference->'identity';
    SELECT * INTO stored_edge FROM truss.edge
     WHERE id=(identity->>'id')::bigint AND rel_type_id=(identity->>'typeId')::int;
    IF NOT FOUND THEN RAISE EXCEPTION 'target edge absent' USING ERRCODE='P1004';END IF;
    -- Native witnesses stay separate from all caller-authored references.
    FOR seed IN SELECT value FROM jsonb_array_elements(jsonb_build_array(
     jsonb_build_object('id',stored_edge.source_id::text,'typeId',stored_edge.source_type::text),
     jsonb_build_object('id',stored_edge.target_id::text,'typeId',stored_edge.target_type::text))) LOOP
     IF NOT seeds @> jsonb_build_array(seed) THEN seeds:=seeds||jsonb_build_array(seed);END IF;
    END LOOP;
   END IF;
  ELSIF operation->>'operation' IN ('update_object','delete_object') THEN
   object_references:=object_references||jsonb_build_array(operation->'target');
  END IF;
  IF operation->>'operation'='create_edge' THEN
   object_references:=object_references||jsonb_build_array(operation->'source',operation->'target');END IF;
  IF operation ? 'endpointChange' THEN
   object_references:=object_references||jsonb_build_array(operation->'endpointChange'->'source',operation->'endpointChange'->'target');END IF;
  IF operation->'ownership'->>'state'='owned' THEN
   object_references:=object_references||jsonb_build_array(operation->'ownership'->'root');END IF;
  IF operation->'ownershipChange'->>'state'='owned' THEN
   object_references:=object_references||jsonb_build_array(operation->'ownershipChange'->'root');END IF;
  FOR reference IN SELECT value FROM jsonb_array_elements(object_references) LOOP
   IF reference->>'state'='stored' THEN
    IF reference-ARRAY['state','identity']<>'{}'::jsonb THEN
     RAISE EXCEPTION 'closed caller object reference required' USING ERRCODE='22023';END IF;
    identity:=reference->'identity';reference_type:=truss.runtime_condition_type(identity);
    IF current_actor IS NULL THEN current_actor:=truss.runtime_person(false);END IF;
    IF NOT truss.runtime_can_read_qualified(reference_type.document_id,reference_type.module,current_actor) THEN
     RAISE EXCEPTION 'selected object reference reader required' USING ERRCODE='42501';END IF;
    IF NOT EXISTS(
     SELECT 1 FROM truss.object WHERE id=(identity->>'id')::bigint AND type_id=reference_type.type_id) THEN
     RAISE EXCEPTION 'target object absent' USING ERRCODE='P1004';END IF;
    seed:=jsonb_build_object('id',identity->'id','typeId',identity->'typeId');
    IF NOT seeds @> jsonb_build_array(seed) THEN seeds:=seeds||jsonb_build_array(seed);END IF;
   END IF;
  END LOOP;
 END LOOP;
 -- The scope observer checks exact native ranges and complete membership.
 RETURN truss.owned_graph_scope(seeds);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_input_scope(jsonb) FROM PUBLIC;
