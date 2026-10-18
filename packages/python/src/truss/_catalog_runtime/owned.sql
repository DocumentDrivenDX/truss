CREATE TABLE truss.runtime_owned_operation (attempt_id uuid NOT NULL REFERENCES truss.runtime_object_attempt (id), operation_index int NOT NULL CHECK (operation_index BETWEEN 0 AND 1023), writer_xid xid8 NOT NULL, plan jsonb NOT NULL, result jsonb, PRIMARY KEY (attempt_id, operation_index), CHECK (jsonb_typeof(plan) = 'object'), CHECK (octet_length(convert_to(plan::text, 'UTF8')) BETWEEN 1 AND 16777216), CHECK (result IS NULL OR (jsonb_typeof(result) = 'object' AND octet_length(convert_to(result::text, 'UTF8')) BETWEEN 1 AND 16777216)));

CREATE TRIGGER runtime_owned_operation_immutable AFTER UPDATE ON truss.runtime_owned_operation FOR EACH ROW
WHEN (OLD.result IS NOT NULL OR NEW.result IS NULL OR
 ROW(OLD.attempt_id,OLD.operation_index,OLD.writer_xid,OLD.plan) IS DISTINCT FROM
 ROW(NEW.attempt_id,NEW.operation_index,NEW.writer_xid,NEW.plan)) EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_owned_operation_no_delete BEFORE DELETE ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_owned_operation_no_truncate BEFORE TRUNCATE ON truss.runtime_owned_operation FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_owned_operation FROM PUBLIC;

-- Ordered object-value simulation for the owned-group executor.
-- Uninstalled candidate. Caller supplies an admitted type and simulated prior image;
-- this function performs no graph write, allocation or authorization issuance.
CREATE FUNCTION truss.owned_object_values(selected_type int,operation jsonb,prior_props jsonb,prior_retained jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE authored jsonb;removed jsonb;props jsonb;retained jsonb;entry jsonb;unset_name text;
 property truss.prop_def%ROWTYPE;values_json jsonb;keys_json jsonb;result_json jsonb;
BEGIN
 IF jsonb_typeof(operation) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'explicit operation value projection required' USING ERRCODE='22023';END IF;
 IF octet_length(operation::text)>1048576 OR coalesce(octet_length(prior_props::text),0)+coalesce(octet_length(prior_retained::text),0)>1048576 THEN
  RAISE EXCEPTION 'bounded value simulation input required' USING ERRCODE='54000';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.type_def t WHERE t.type_id=selected_type AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL) THEN
  RAISE EXCEPTION 'current admitted Record required' USING ERRCODE='22023';END IF;
 IF operation->>'operation'='create_object' THEN
  IF prior_props IS NOT NULL OR prior_retained IS NOT NULL THEN RAISE EXCEPTION 'create has no prior image' USING ERRCODE='22023';END IF;
  authored:=operation->'values';removed:='[]';props:='{}';retained:='{}';
 ELSIF operation->>'operation'='update_object' THEN
  IF jsonb_typeof(prior_props) IS DISTINCT FROM 'object' OR (prior_retained IS NOT NULL AND jsonb_typeof(prior_retained) IS DISTINCT FROM 'object') THEN
   RAISE EXCEPTION 'complete simulated prior values required' USING ERRCODE='22023';END IF;
  authored:=operation->'set';removed:=operation->'unset';props:=prior_props;retained:=coalesce(prior_retained,'{}');
 ELSE RAISE EXCEPTION 'create or update value simulation required' USING ERRCODE='22023';END IF;
 IF jsonb_typeof(authored) IS DISTINCT FROM 'array' OR jsonb_typeof(removed) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'explicit authored arrays required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(authored)>1024 OR jsonb_array_length(removed)>1024 THEN RAISE EXCEPTION 'bounded authored values required' USING ERRCODE='54000';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(authored) v WHERE v.value-ARRAY['name','value']<>'{}'::jsonb
   OR jsonb_typeof(v.value->'name') IS DISTINCT FROM 'string' OR octet_length(v.value->>'name') NOT BETWEEN 1 AND 4096
   OR truss.valid_flat_cell(v.value->'value') IS NOT TRUE)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(removed) v WHERE jsonb_typeof(v.value) IS DISTINCT FROM 'string' OR octet_length(v.value#>>'{}') NOT BETWEEN 1 AND 4096)
  OR jsonb_array_length(authored)<>(SELECT count(DISTINCT v.value->>'name') FROM jsonb_array_elements(authored) v)
  OR jsonb_array_length(removed)<>(SELECT count(DISTINCT v.value) FROM jsonb_array_elements(removed) v)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(authored) a JOIN jsonb_array_elements(removed) r ON a.value->>'name'=r.value#>>'{}') THEN
  RAISE EXCEPTION 'unique disjoint exact authored values required' USING ERRCODE='22023';END IF;
 -- Refuse unknown physical cells rather than silently dropping them while planning.
 IF EXISTS(SELECT 1 FROM jsonb_object_keys(props) k WHERE NOT EXISTS(
   SELECT 1 FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.prop_id::text=k))
  OR EXISTS(SELECT 1 FROM jsonb_each(retained) e WHERE truss.valid_flat_cell(e.value) IS NOT TRUE) THEN
  RAISE EXCEPTION 'supported complete prior value representation required' USING ERRCODE='0A000';END IF;
 FOR unset_name IN SELECT value#>>'{}' FROM jsonb_array_elements(removed) LOOP
  SELECT p.* INTO property FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.name=unset_name;
  IF FOUND THEN props:=props-property.prop_id::text;ELSE retained:=retained-unset_name;END IF;
 END LOOP;
 FOR entry IN SELECT value FROM jsonb_array_elements(authored) LOOP
  SELECT p.* INTO property FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.name=entry->>'name';
  IF FOUND THEN props:=props||jsonb_build_object(property.prop_id::text,truss.canonical_flat_cell(entry->'value'));
  ELSE retained:=retained||jsonb_build_object(entry->>'name',truss.canonical_flat_cell(entry->'value'));END IF;
 END LOOP;
 FOR property IN SELECT p.* FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL LOOP
  IF truss.valid_property_definition(property) IS NOT TRUE THEN RAISE EXCEPTION 'supported exact property definition required' USING ERRCODE='0A000';END IF;
  IF NOT props ? property.prop_id::text THEN
   IF property.nullability='required' THEN RAISE EXCEPTION 'missing required value' USING ERRCODE='22023';END IF;
  ELSIF truss.valid_property_value(props->property.prop_id::text,property) IS NOT TRUE THEN
   RAISE EXCEPTION 'exact declared value required' USING ERRCODE='22023';END IF;
 END LOOP;
 IF octet_length(convert_to(jsonb_build_object('props',props,'retained',retained)::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'bounded complete object values required' USING ERRCODE='54000';END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',v.name,'value',v.value) ORDER BY v.name COLLATE "C"),'[]'::jsonb) INTO values_json FROM (
  SELECT p.name,props->p.prop_id::text AS value FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND props ? p.prop_id::text
  UNION ALL SELECT key,value FROM jsonb_each(retained)) v;
 SELECT coalesce(jsonb_agg(jsonb_build_object('keyNumber',k.key_num::text,'keyId',k.key_id,'names',
  (SELECT jsonb_agg(p.name ORDER BY i.ord) FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ord)
   JOIN truss.prop_def p ON p.type_id=k.type_id AND p.prop_id=i.prop_id)) ORDER BY k.key_num),'[]'::jsonb)
  INTO keys_json FROM truss.key_def k WHERE k.type_id=selected_type AND k.retired_rev IS NULL;
 result_json:=jsonb_build_object('props',props,'retained',retained,'values',values_json,'keys',keys_json);
 IF octet_length(convert_to(result_json::text,'UTF8'))>4194304 THEN RAISE EXCEPTION 'bounded complete value simulation result required' USING ERRCODE='54000';END IF;
 RETURN result_json;
END;
$$;
REVOKE ALL ON FUNCTION truss.owned_object_values(int,jsonb,jsonb,jsonb) FROM PUBLIC;

-- Private valid-forest projection, not installed by the public runtime.
-- Ordinals refer to the executor's complete scoped simulation, never native IDs.
-- The executor retains and authenticates its original identity/alias map separately.
-- Invoke only at states requiring forest validity; final checks remain deferred.
CREATE FUNCTION truss.owned_forest_projection(node_count int,owned_edges jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE parents int[];seen_edges boolean[];entry jsonb;edge_number int;source_node int;target_node int;
 node_number int;ancestor int;path int[];roots int[];result_json jsonb;
BEGIN
 IF node_count IS NULL OR node_count NOT BETWEEN 0 AND 2048 THEN
  RAISE EXCEPTION 'bounded local node count required' USING ERRCODE='54000';END IF;
 IF jsonb_typeof(owned_edges) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'explicit local owned edges required' USING ERRCODE='22023';END IF;
 IF octet_length(convert_to(owned_edges::text,'UTF8'))>1048576 OR jsonb_array_length(owned_edges)>1024 THEN
  RAISE EXCEPTION 'bounded local owned edges required' USING ERRCODE='54000';END IF;
 parents:=array_fill(-1,ARRAY[node_count]);roots:=array_fill(-1,ARRAY[node_count]);seen_edges:=array_fill(false,ARRAY[1024]);
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
  roots[node_number+1]:=CASE WHEN ancestor=node_number THEN -1 ELSE ancestor END;
 END LOOP;
 -- Assemble once after the unchanged validation and root walk. Repeated JSONB
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

-- Uninstalled observation component. One invocation uses one statement snapshot.
-- No locks, authority issuance or effects. Reobserve after the graph-write gate;
-- the executor must refuse newly required earlier guards before performing writes.
CREATE FUNCTION truss.owned_graph_scope(seeds jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE node_keys text[]:='{}';edge_keys text[]:='{}';boundary_keys text[]:='{}';owned_edge_order text[]:='{}';
 nodes jsonb:='{}';node_images jsonb[]:='{}';edges jsonb:='{}';edge_images jsonb[]:='{}';boundary jsonb:='{}';types jsonb:='{}';relations jsonb:='{}';
 entry jsonb;image jsonb;relation_image jsonb;witness jsonb;definition jsonb;
 node_key text;other_key text;edge_key text;root_key text;selected_type int;selected_id bigint;
 selected_node int:=1;observed record;side text;projection jsonb;local_edges jsonb:='[]';local_index int:=0;
 result_json jsonb;used_bytes bigint:=0;head int;
BEGIN
 IF jsonb_typeof(seeds) IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'explicit typed scope seeds required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(seeds) NOT BETWEEN 0 AND 1024 OR octet_length(convert_to(seeds::text,'UTF8'))>1048576 THEN
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
  node_images:=array_append(node_images,image);types:=types||jsonb_build_object(selected_type::text,definition);
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
   edge_keys:=array_append(edge_keys,edge_key);edge_images:=array_append(edge_images,observed.edge_image);
   relations:=relations||jsonb_build_object(relation_image->>'rel_type_id',relation_image);
   IF relation_image->>'lifecycle'='owned' THEN
    FOREACH side IN ARRAY ARRAY['source','target'] LOOP
     other_key:=(observed.edge_image->>(side||'_type'))||':'||(observed.edge_image->>(side||'_id'));
     IF NOT other_key=ANY(node_keys) THEN
      IF cardinality(node_keys)=1024 THEN RAISE EXCEPTION 'bounded complete ownership component required' USING ERRCODE='54000';END IF;
      node_keys:=array_append(node_keys,other_key);
     END IF;
    END LOOP;
   END IF;
  END LOOP;
  selected_node:=selected_node+1;
 END LOOP;
 -- Traversal observes each node once in node_keys order. Assemble the output
 -- map once; it is only consumed after complete component discovery.
 SELECT coalesce(jsonb_object_agg(c.node_key,c.image),'{}'::jsonb) INTO nodes
 FROM unnest(node_keys,node_images) AS c(node_key,image);
 -- Traversal only reads edge membership above. Materialize original edge
 -- images once instead of recopying the complete growing JSONB map per edge.
 SELECT coalesce(jsonb_object_agg(c.edge_key,c.image),'{}'::jsonb) INTO edges
 FROM unnest(edge_keys,edge_images) AS c(edge_key,image);
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
 seeds jsonb;seed_items jsonb[]:='{}';seed jsonb;lean_nodes jsonb;lean_types jsonb;lean_order jsonb;lean_forest jsonb;lean_count int;stored_edge truss.edge%ROWTYPE;reference_type truss.type_def%ROWTYPE;current_actor oid;
BEGIN
 IF jsonb_typeof(input->'operations') IS DISTINCT FROM 'array'
  OR jsonb_array_length(input->'operations') NOT BETWEEN 1 AND 1024 THEN
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
     seed_items:=array_append(seed_items,seed);
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
    seed_items:=array_append(seed_items,seed);
   END IF;
  END LOOP;
 END LOOP;
 -- Deduplicate once, preserving the original first-discovery order. Every
 -- authored reference above is still independently validated and authorized.
 SELECT coalesce(jsonb_agg(seed_value ORDER BY first_ordinal),'[]'::jsonb) INTO seeds
 FROM (SELECT item seed_value,min(ordinality) first_ordinal
  FROM unnest(seed_items) WITH ORDINALITY entries(item,ordinality) GROUP BY item) distinct_seeds;
 -- Pure value updates and independent edge creates have no ownership edits.
 -- When the catalog has no owned relationships and every observed row is
 -- rootless, incident independent edge images cannot affect these operations.
 -- Read each explicit endpoint once; native final constraints still inspect
 -- actual relationship cardinalities and current reader/writer authority.
 IF NOT EXISTS(SELECT 1 FROM truss.rel_def WHERE retired_rev IS NULL AND lifecycle='owned')
  AND (NOT EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
       WHERE o.value->>'operation'<>'update_object' OR o.value ? 'ownershipChange' OR o.value->'target'->>'state'<>'stored')
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
       WHERE o.value->>'operation'<>'create_edge' OR o.value->'source'->>'state'<>'stored' OR o.value->'target'->>'state'<>'stored'))
  AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(seeds) s JOIN truss.object o
    ON o.id=(s.value->>'id')::bigint AND o.type_id=(s.value->>'typeId')::int
    WHERE o.root_id IS NOT NULL OR o.root_type IS NOT NULL) THEN
  SELECT count(*),coalesce(jsonb_agg(to_jsonb(o.type_id::text||':'||o.id::text) ORDER BY s.ordinality),'[]'::jsonb),
   coalesce(jsonb_object_agg(o.type_id::text||':'||o.id::text,to_jsonb(o)),'{}'::jsonb),
   coalesce(jsonb_object_agg(t.type_id::text,to_jsonb(t)),'{}'::jsonb),
   coalesce(jsonb_agg(jsonb_build_object('node',s.ordinality-1,'parent',NULL,'root',NULL,'incomingEdges','[]'::jsonb) ORDER BY s.ordinality),'[]'::jsonb)
   INTO lean_count,lean_order,lean_nodes,lean_types,lean_forest
   FROM jsonb_array_elements(seeds) WITH ORDINALITY s JOIN truss.object o
    ON o.id=(s.value->>'id')::bigint AND o.type_id=(s.value->>'typeId')::int
   JOIN truss.type_def t ON t.type_id=o.type_id;
  IF lean_count<>jsonb_array_length(seeds) OR lean_count>2048
   OR octet_length(lean_nodes::text)+octet_length(lean_types::text)>4194304 THEN
   RAISE EXCEPTION 'bounded complete explicit rootless rows required' USING ERRCODE='54000';END IF;
  RETURN jsonb_build_object('catalogRevision',(SELECT rev FROM truss.schema_head WHERE id=1),
   'independentEndpointScope',true,'nodeOrder',lean_order,'ownedEdgeOrder','[]'::jsonb,'nodes',lean_nodes,'edges','{}'::jsonb,
   'types',lean_types,'relationships','{}'::jsonb,'boundary','{}'::jsonb,'forest',lean_forest);
 END IF;
 -- The scope observer checks exact native ranges and complete membership.
 RETURN truss.owned_graph_scope(seeds);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_input_scope(jsonb) FROM PUBLIC;

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
 FOR entry IN SELECT key,value,
  count(*) FILTER (WHERE value->'deleted'='false'::jsonb) OVER (
   ORDER BY key COLLATE "C" ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) preceding_live
  FROM jsonb_each(edges) ORDER BY key COLLATE "C" LOOP
  IF entry.value->'deleted'='true'::jsonb THEN CONTINUE;END IF;
  IF (entry.value->>'lifecycle'='owned') IS DISTINCT FROM owned THEN CONTINUE;END IF;
  source_node:=array_position(node_order,entry.value->>'source')-1;
  target_node:=array_position(node_order,entry.value->>'target')-1;
  IF source_node IS NULL THEN source_node:=cardinality(node_order)+array_position(boundary_order,entry.value->>'source')-1;END IF;
  IF target_node IS NULL THEN target_node:=cardinality(node_order)+array_position(boundary_order,entry.value->>'target')-1;END IF;
  IF source_node IS NULL OR target_node IS NULL OR owned AND (source_node>=cardinality(node_order) OR target_node>=cardinality(node_order)) THEN
   RAISE EXCEPTION 'complete typed endpoint scope required' USING ERRCODE='55000';END IF;
  -- Ordinals count all live edges so the two lifecycle arrays stay disjoint.
  ordinal:=entry.preceding_live;
  result:=result||jsonb_build_array(jsonb_build_object('edge',ordinal,'source',source_node,'target',target_node));
 END LOOP;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_local_edges(jsonb,text[],text[],boolean) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_prepare(input jsonb,scope jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE input_operations jsonb;
 nodes jsonb:='{}';edges jsonb:='{}';aliases jsonb:='{}';plans jsonb[]:='{}';
 node_order text[]:='{}';boundary_order text[]:='{}';entry record;selected text;source_ref text;target_ref text;root_ref text;
 operation jsonb;before_nodes jsonb;before_edges jsonb;state jsonb;prior jsonb;image jsonb;values_image jsonb;ownership jsonb;
 selected_type truss.type_def%ROWTYPE;relation truss.rel_def%ROWTYPE;pin record;identity jsonb;revision int;
 index int:=0;before_count int;descendants text[];descendant text;projection jsonb;deleted jsonb;local_owned jsonb;local_independent jsonb;
 unset_name text;authored jsonb;retained jsonb;order_key jsonb;selected_source_type int;selected_target_type int;plan jsonb;outgoing bigint;incoming bigint;
 retained_nodes text[];retained_edges text[];changed_nodes text[];changed_edges text[];plans_bytes bigint:=2;current_actor oid;resolved_creates jsonb:='{}';
 rootless_creates boolean;created_states jsonb[]:='{}';
 edge_creates boolean;created_edge_states jsonb[]:='{}';initial_edge_count int;
 value_updates boolean;updated_states jsonb[]:='{}';updated_references text[]:='{}';
 scope_node_states jsonb[]:='{}';scope_edge_states jsonb[]:='{}';
 scope_node_type int;scope_edge_type int;scope_edge_pin text;outgoing_counts jsonb;incoming_counts jsonb;
BEGIN
 current_actor:=truss.runtime_person(false);
 input_operations:=input->'operations';
 IF jsonb_typeof(input_operations) IS DISTINCT FROM 'array' OR jsonb_array_length(input_operations) NOT BETWEEN 1 AND 1024
  OR jsonb_typeof(scope->'nodes') IS DISTINCT FROM 'object' OR jsonb_typeof(scope->'edges') IS DISTINCT FROM 'object'
  OR octet_length(convert_to(scope::text,'UTF8'))>4194304 THEN
  RAISE EXCEPTION 'complete bounded original group scope required' USING ERRCODE='54000';END IF;
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
 FOR operation IN SELECT value FROM jsonb_array_elements(input_operations) LOOP
  before_nodes:=nodes;before_edges:=edges;changed_nodes:=ARRAY[]::text[];changed_edges:=ARRAY[]::text[];
  IF operation ? 'alias' AND (jsonb_typeof(operation->'alias') IS DISTINCT FROM 'string'
   OR octet_length(operation->>'alias') NOT BETWEEN 1 AND 1024 OR aliases ? (operation->>'alias')) THEN
   RAISE EXCEPTION 'unique bounded original alias required' USING ERRCODE='22023';END IF;
  IF operation->>'operation' IN ('create_object','update_object','delete_object') THEN
   IF operation->>'operation'='create_object' AND resolved_creates ? (operation->>'typeDefinitionPin') THEN
    selected_type:=jsonb_populate_record(NULL::truss.type_def,resolved_creates->(operation->>'typeDefinitionPin'));
    IF NOT truss.runtime_object_values_readable_qualified(selected_type.type_id,current_actor) THEN
     RAISE EXCEPTION 'current property and item interpretation reader required' USING ERRCODE='42501';END IF;
   ELSE
    -- Only alias resolution reads earlier operations; stored/create targets do not.
    selected_type:=truss.runtime_owned_operation_type_qualified(operation,
     CASE WHEN operation->'target'->>'state'='alias' THEN input_operations END,index,current_actor);
    IF operation->>'operation'='create_object' THEN
     resolved_creates:=resolved_creates||jsonb_build_object(operation->>'typeDefinitionPin',to_jsonb(selected_type));
    END IF;
   END IF;
   IF operation->>'operation'='create_object' THEN
    IF operation-ARRAY['operation','typeDefinitionPin','values','ownership','alias']<>'{}'::jsonb
     OR jsonb_typeof(operation->'ownership') IS DISTINCT FROM 'object' THEN
     RAISE EXCEPTION 'closed original object create required' USING ERRCODE='22023';END IF;
    IF cardinality(node_order)>=1024 THEN RAISE EXCEPTION 'bounded complete group objects required' USING ERRCODE='54000';END IF;
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
     changed_nodes:=array_append(changed_nodes,descendant);
     nodes:=jsonb_set(nodes,ARRAY[descendant,'deleted'],'true'::jsonb);
    END LOOP;
    FOR entry IN SELECT key,value FROM jsonb_each(edges) WHERE value->'deleted'='false'::jsonb LOOP
     IF nodes->(entry.value->>'source')->'deleted'='true'::jsonb OR nodes->(entry.value->>'target')->'deleted'='true'::jsonb THEN
      IF (entry.value->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
      changed_edges:=array_append(changed_edges,entry.key);
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
       ELSE changed_nodes:=array_append(changed_nodes,descendant);nodes:=jsonb_set(nodes,ARRAY[descendant,'root'],coalesce(to_jsonb(coalesce(root_ref,selected)),'null'::jsonb));END IF;
      END LOOP;
     END IF;
    END IF;
    changed_nodes:=array_append(changed_nodes,selected);
    IF rootless_creates THEN created_states:=array_append(created_states,state);
    -- Ordinary updates install their final versioned member below; no-op
    -- updates already have that exact state in the working graph.
    ELSIF operation->>'operation'<>'update_object' OR operation ? 'ownershipChange' THEN
     nodes:=nodes||jsonb_build_object(selected,state);END IF;
    IF operation->>'operation'='update_object' AND NOT (operation ? 'ownershipChange') THEN
     IF state IS DISTINCT FROM before_nodes->selected THEN
      IF (state->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'object version exhausted' USING ERRCODE='54000';END IF;
      state:=jsonb_set(state,'{image,ver}',to_jsonb((state->'image'->>'ver')::bigint+1));
      IF value_updates THEN state:=jsonb_set(state,'{image,rev}',to_jsonb(revision));
      ELSE nodes:=jsonb_set(nodes,ARRAY[selected],jsonb_set(state,'{image,rev}',to_jsonb(revision)));END IF;
     END IF;
     IF value_updates THEN
      updated_references:=array_append(updated_references,selected);
      updated_states:=array_append(updated_states,state);
     END IF;
    ELSIF operation->>'operation'<>'create_object' THEN
    FOR entry IN SELECT reference key,nodes->reference value FROM (SELECT DISTINCT unnest(changed_nodes) reference) touched LOOP
     IF before_nodes ? entry.key AND entry.value IS DISTINCT FROM before_nodes->entry.key THEN
      IF (entry.value->'image'->>'ver')::bigint=9223372036854775807 THEN RAISE EXCEPTION 'object version exhausted' USING ERRCODE='54000';END IF;
      state:=jsonb_set(entry.value,'{image,ver}',to_jsonb((entry.value->'image'->>'ver')::bigint+1));
      nodes:=jsonb_set(nodes,ARRAY[entry.key],jsonb_set(state,'{image,rev}',to_jsonb(revision)));
     END IF;
    END LOOP;
    END IF;
   END IF;
  ELSIF operation->>'operation' IN ('create_edge','update_edge','delete_edge') THEN
   relation:=truss.runtime_operation_relationship(operation,input_operations,index);
   IF relation.lifecycle NOT IN ('owned','independent') OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL THEN
    RAISE EXCEPTION 'supported directed relationship required' USING ERRCODE='0A000';END IF;
   IF operation->>'operation'='create_edge' THEN
    IF operation-ARRAY['operation','relationshipDefinitionPin','source','target','values','orderKey','alias']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge create required' USING ERRCODE='22023';END IF;
    IF (CASE WHEN edge_creates THEN initial_edge_count+index ELSE (SELECT count(*) FROM jsonb_each(edges)) END)>=1024 THEN RAISE EXCEPTION 'bounded complete group edges required' USING ERRCODE='54000';END IF;
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
     changed_edges:=array_append(changed_edges,selected);
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
    changed_edges:=array_append(changed_edges,selected);
    IF edge_creates THEN created_edge_states:=array_append(created_edge_states,state);
    ELSE edges:=edges||jsonb_build_object(selected,state);END IF;
   END IF;
  ELSE RAISE EXCEPTION 'supported original graph operation required' USING ERRCODE='0A000';END IF;
  IF operation ? 'alias' THEN aliases:=aliases||jsonb_build_object(operation->>'alias',selected);END IF;
  -- Keep one working graph for ordered simulation. Persist only this step's
  -- changed members and identity witnesses; final settlement keeps one full frame.
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
  IF index=jsonb_array_length(input_operations)-1 THEN
   plan:=jsonb_build_object('beforeNodes',before_nodes,'afterNodes',nodes,
    'beforeEdges',before_edges,'afterEdges',edges);
  ELSIF value_updates THEN
   plan:=jsonb_build_object('beforeNodes',jsonb_build_object(selected,before_nodes->selected),
    'afterNodes',jsonb_build_object(selected,state),'beforeEdges','{}'::jsonb,'afterEdges','{}'::jsonb);
  ELSIF rootless_creates THEN
   plan:=jsonb_build_object('beforeNodes','{}'::jsonb,'afterNodes',jsonb_build_object(selected,state),
    'beforeEdges','{}'::jsonb,'afterEdges','{}'::jsonb);
  ELSIF edge_creates THEN
   SELECT array_agg(DISTINCT reference) INTO retained_nodes FROM unnest(ARRAY[
    source_ref,target_ref,nodes->source_ref->>'root',nodes->target_ref->>'root']) r(reference) WHERE reference IS NOT NULL;
   SELECT coalesce(jsonb_object_agg(r.reference,nodes->r.reference),'{}'::jsonb) INTO before_nodes
    FROM unnest(retained_nodes) r(reference) WHERE nodes ? r.reference;
   plan:=jsonb_build_object('beforeNodes',before_nodes,'afterNodes',before_nodes,
    'beforeEdges','{}'::jsonb,'afterEdges',jsonb_build_object(selected,state));
  ELSIF operation->>'operation'='create_object'
   OR (operation->>'operation'='update_object' AND NOT (operation ? 'ownershipChange')) THEN
   -- These operations change one object only. Use point lookups for its root
   -- witnesses instead of rescanning the complete growing working graph.
   SELECT array_agg(DISTINCT reference) INTO retained_nodes FROM unnest(ARRAY[
    selected,before_nodes->selected->>'root',nodes->selected->>'root']) r(reference) WHERE reference IS NOT NULL;
   plan:=jsonb_build_object(
    'beforeNodes',(SELECT coalesce(jsonb_object_agg(r.reference,before_nodes->r.reference),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE before_nodes ? r.reference),
    'afterNodes',(SELECT coalesce(jsonb_object_agg(r.reference,nodes->r.reference),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE nodes ? r.reference),
    'beforeEdges','{}'::jsonb,'afterEdges','{}'::jsonb);
  ELSE
   SELECT coalesce(array_agg(reference),'{}'::text[]) INTO retained_edges FROM (
    SELECT reference FROM unnest(changed_edges) e(reference)
     WHERE before_edges->reference IS DISTINCT FROM edges->reference
    UNION SELECT selected WHERE operation->>'operation' IN ('create_edge','update_edge','delete_edge')
   ) changed;
   SELECT coalesce(array_agg(reference),'{}'::text[]) INTO retained_nodes FROM (
    SELECT reference FROM unnest(changed_nodes) n(reference)
     WHERE before_nodes->reference IS DISTINCT FROM nodes->reference
    UNION SELECT selected WHERE operation->>'operation' IN ('create_object','update_object','delete_object')
    UNION SELECT before_edges->reference->>'source' FROM unnest(retained_edges) e(reference)
    UNION SELECT before_edges->reference->>'target' FROM unnest(retained_edges) e(reference)
    UNION SELECT edges->reference->>'source' FROM unnest(retained_edges) e(reference)
    UNION SELECT edges->reference->>'target' FROM unnest(retained_edges) e(reference)
   ) changed WHERE reference IS NOT NULL;
   SELECT coalesce(array_agg(reference),'{}'::text[]) INTO retained_nodes FROM (
    SELECT unnest(retained_nodes) reference
    UNION SELECT before_nodes->reference->>'root' FROM unnest(retained_nodes) n(reference)
    UNION SELECT nodes->reference->>'root' FROM unnest(retained_nodes) n(reference)
   ) witnesses WHERE reference IS NOT NULL;
   plan:=jsonb_build_object(
    'beforeNodes',(SELECT coalesce(jsonb_object_agg(reference,before_nodes->reference),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE before_nodes ? reference),
    'afterNodes',(SELECT coalesce(jsonb_object_agg(reference,nodes->reference),'{}'::jsonb) FROM unnest(retained_nodes) r(reference) WHERE nodes ? reference),
    'beforeEdges',(SELECT coalesce(jsonb_object_agg(reference,before_edges->reference),'{}'::jsonb) FROM unnest(retained_edges) r(reference) WHERE before_edges ? reference),
    'afterEdges',(SELECT coalesce(jsonb_object_agg(reference,edges->reference),'{}'::jsonb) FROM unnest(retained_edges) r(reference) WHERE edges ? reference));
  END IF;
  plan:=plan||jsonb_build_object('profile','truss-owned-operation-plan/0.2',
   'operationIndex',index,'operation',operation,'primary',selected);
  plans_bytes:=plans_bytes+octet_length(convert_to(plan::text,'UTF8'))+CASE WHEN index=0 THEN 0 ELSE 2 END;
  IF plans_bytes>16777216 THEN RAISE EXCEPTION 'bounded whole group execution inventory required' USING ERRCODE='54000';END IF;
  plans:=array_append(plans,plan);
  index:=index+1;
 END LOOP;
 SELECT coalesce(array_agg(reference ORDER BY ordinal),'{}'::text[]) INTO node_order FROM unnest(node_order) WITH ORDINALITY n(reference,ordinal) WHERE nodes->reference->'deleted'='false'::jsonb;
 local_owned:=truss.runtime_owned_local_edges(edges,node_order,boundary_order,true);
 projection:=truss.owned_forest_projection(cardinality(node_order),local_owned);
 FOR entry IN SELECT value FROM jsonb_array_elements(projection) LOOP
  selected:=node_order[(entry.value->>'node')::int+1];root_ref:=CASE WHEN entry.value->'root'='null'::jsonb THEN NULL ELSE node_order[(entry.value->>'root')::int+1] END;
  IF nodes->selected->'root' IS DISTINCT FROM coalesce(to_jsonb(root_ref),'null'::jsonb) THEN RAISE EXCEPTION 'final ownership graph requires explicit root change' USING ERRCODE='22023';END IF;
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
 FOREACH selected IN ARRAY node_order LOOP
  selected_source_type:=(nodes->selected->'identity'->>'typeId')::int;
  FOR relation IN SELECT r.* FROM truss.rel_def r WHERE r.retired_rev IS NULL AND EXISTS(
   SELECT 1 FROM truss.rel_endpoint ep WHERE ep.rel_type_id=r.rel_type_id AND selected_source_type IN(ep.source_type,ep.target_type)) LOOP
   IF EXISTS(SELECT 1 FROM truss.rel_endpoint ep WHERE ep.rel_type_id=relation.rel_type_id AND ep.source_type=selected_source_type) THEN
    outgoing:=coalesce((outgoing_counts->>jsonb_build_array(relation.rel_type_id::text,selected)::text)::bigint,0);
    IF outgoing<relation.target_min OR relation.target_max IS NOT NULL AND outgoing>relation.target_max THEN RAISE EXCEPTION 'final outgoing multiplicity failed' USING ERRCODE='P1005';END IF;
   END IF;
   IF EXISTS(SELECT 1 FROM truss.rel_endpoint ep WHERE ep.rel_type_id=relation.rel_type_id AND ep.target_type=selected_source_type) THEN
    incoming:=coalesce((incoming_counts->>jsonb_build_array(relation.rel_type_id::text,selected)::text)::bigint,0);
    IF incoming<relation.source_min OR relation.source_max IS NOT NULL AND incoming>relation.source_max THEN RAISE EXCEPTION 'final incoming multiplicity failed' USING ERRCODE='P1005';END IF;
   END IF;
  END LOOP;
 END LOOP;
 plan:=jsonb_build_object('profile','truss-owned-group-plan/0.1','catalogRevision',revision,
  'initialScope',scope,'operations',to_jsonb(plans),'aliases',aliases);
 IF octet_length(convert_to(plan::text,'UTF8'))>16777216 THEN RAISE EXCEPTION 'bounded complete group execution inventory required' USING ERRCODE='54000';END IF;
 RETURN plan;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_prepare(jsonb,jsonb) FROM PUBLIC;


-- This is the execution entry's native preflight, not a caller-supplied plan.
-- Admission is before predicate/key/row locks. No canonical graph rows change.
CREATE FUNCTION truss.runtime_owned_capture(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE input_operations jsonb;
 attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;observed jsonb;locked jsonb;
 inventory jsonb;entry jsonb;expected_operation jsonb;actual_operation jsonb;owner record;selected_type int;relation truss.rel_def%ROWTYPE;endpoint_owner record;retained_bytes bigint:=0;current_actor oid;
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
  FOR relation IN SELECT r.* FROM truss.rel_def r WHERE r.retired_rev IS NULL AND EXISTS(
   SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=r.rel_type_id AND selected_type IN(e.source_type,e.target_type))
   ORDER BY r.rel_type_id LOOP
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
 inventory:=truss.runtime_owned_prepare(input,locked);
 PERFORM truss.runtime_owned_key_preflight(inventory);
 -- Retain all immutable plans with one INSERT, preserving exact row images.
 WITH plans AS (
  SELECT value||jsonb_build_object('actorName',session_user::text,'mutationProfile',input->'mutationProfile',
   'catalogRevision',inventory->'catalogRevision')||CASE WHEN value->>'operationIndex'='0'
    THEN jsonb_build_object('initialScope',inventory->'initialScope') ELSE '{}'::jsonb END plan
  FROM jsonb_array_elements(inventory->'operations'))
 SELECT sum(octet_length(convert_to(plan::text,'UTF8'))),
  jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(plan->>'operationIndex')::int,
   'writer_xid',attempt.writer_xid::text,'plan',plan,'result',NULL) ORDER BY (plan->>'operationIndex')::int)
 INTO retained_bytes,expected_operation FROM plans;
 IF retained_bytes>16777216 THEN RAISE EXCEPTION 'bounded retained whole group inventory required' USING ERRCODE='54000';END IF;
 WITH inserted AS (
  INSERT INTO truss.runtime_owned_operation(attempt_id,operation_index,writer_xid,plan)
  SELECT r.attempt_id,r.operation_index,r.writer_xid,r.plan
  FROM jsonb_populate_recordset(NULL::truss.runtime_owned_operation,expected_operation) r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted) ORDER BY operation_index) INTO actual_operation FROM inserted;
 IF actual_operation IS DISTINCT FROM expected_operation THEN
  RAISE EXCEPTION 'exact prepared operation insert required' USING ERRCODE='55000';END IF;
 SELECT jsonb_agg(to_jsonb(o) ORDER BY operation_index) INTO actual_operation
 FROM truss.runtime_owned_operation o WHERE o.attempt_id=attempt.id;
 IF actual_operation IS DISTINCT FROM expected_operation THEN
  RAISE EXCEPTION 'exact stored prepared operation required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_capture(uuid) FROM PUBLIC;

-- Reuse original operation evidence after rows move or disappear. Identity-only
-- matching never attributes a descendant transition to an unrelated operation.
CREATE FUNCTION truss.runtime_owned_plan(selected_attempt uuid,selected_index int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original record;
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
 endpoint_reference text;endpoint_image jsonb;relation truss.rel_def%ROWTYPE;current_actor oid;
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
  IF physical-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_edge_image(selected_attempt,selected_index,reference,'before',plan,attempt) THEN
   RAISE EXCEPTION 'original edge prestate required' USING ERRCODE='55000';END IF;
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
  SELECT to_jsonb(o) INTO STRICT endpoint_image FROM truss.object o
   WHERE id=(endpoint_identity->>'id')::bigint AND type_id=(endpoint_identity->>'typeId')::int;
  IF endpoint_image-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(selected_attempt,selected_index,endpoint_reference,'before',plan,attempt) THEN
   RAISE EXCEPTION 'original endpoint prestate required' USING ERRCODE='55000';END IF;
 END LOOP;
 PERFORM truss.runtime_lock_edge_business_key(truss.runtime_edge_business_key(relation.rel_type_id,source_identity,target_identity));
 IF old_source IS NOT NULL THEN PERFORM truss.runtime_lock_edge_business_key(truss.runtime_edge_business_key(relation.rel_type_id,old_source,old_target));END IF;
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
 installation truss.catalog_runtime_installation%ROWTYPE;property truss.prop_def%ROWTYPE;pin record;
 events jsonb:='[]';event_refs jsonb:='[]';journals jsonb:='[]';event jsonb;entry jsonb;journal truss.journal%ROWTYPE;
 keys jsonb;version bigint;revision int;event_digest text;ordinal int;mode text;result jsonb;actual_deleted jsonb;current_actor oid;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() THEN
  RAISE EXCEPTION 'current original object effect required' USING ERRCODE='55000';END IF;
 current_actor:=coalesce(qualified_actor,truss.runtime_person(false));
 IF attempt.actor_oid IS DISTINCT FROM current_actor
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index THEN
  RAISE EXCEPTION 'current original object effect required' USING ERRCODE='55000';END IF;
 plan:=truss.runtime_owned_plan(selected_attempt,selected_index);input:=coalesce(prepared_input,convert_from(attempt.input_bytes,'UTF8')::jsonb);
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
 IF old_image-ARRAY['created_at','updated_at'] IS DISTINCT FROM truss.runtime_owned_object_image(selected_attempt,selected_index,reference,'before',plan,attempt) THEN
  RAISE EXCEPTION 'original complete object prestate required' USING ERRCODE='55000';END IF;
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
   rev=object_row.rev,ver=object_row.ver,updated_at=object_row.updated_at WHERE id=object_row.id AND type_id=object_row.type_id
   RETURNING to_jsonb(object) INTO STRICT new_image;
  IF new_image-ARRAY['created_at','updated_at'] IS DISTINCT FROM expected_image OR new_image->'created_at' IS DISTINCT FROM old_image->'created_at' THEN
   RAISE EXCEPTION 'original planned object update required' USING ERRCODE='55000';END IF;
  after_record:=truss.runtime_object_history(new_image,identity);
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=object_row.type_id AND retired_rev IS NULL ORDER BY prop_id LOOP
   IF old_image->'props'->property.prop_id::text IS DISTINCT FROM new_image->'props'->property.prop_id::text THEN
    SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',object_row.type_id,property.prop_id);
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
  INSERT INTO truss.journal SELECT (journal).*;
  journals:=journals||jsonb_build_array(to_jsonb(journal));event_refs:=event_refs||jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',journal.seq::text));
 END LOOP;
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
 primary_reference text;metadata jsonb;effect jsonb;primary_result jsonb;events jsonb:='[]';deleted jsonb:='[]';result jsonb;selected_transition bigint;current_actor oid;stored_result jsonb;progress record;closing_actor oid;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 current_actor:=coalesce(qualified_actor,truss.runtime_person(false));
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM selected_index
  OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR (SELECT count(*) FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.result IS NOT NULL)<>selected_index THEN
  RAISE EXCEPTION 'current ordered owned operation required' USING ERRCODE='55000';END IF;
 IF prepared_input IS NOT NULL AND attempt.input_bytes IS DISTINCT FROM prepared_original THEN
  RAISE EXCEPTION 'original owned step input required' USING ERRCODE='55000';END IF;
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
  events:=events||(effect->'events');deleted:=deleted||coalesce(effect->'deleted','[]'::jsonb);
  IF entry.key=primary_reference THEN primary_result:=effect;END IF;
 END LOOP;
 -- Aggregate-root FKs are immediate: remove nonroots before their root.
 before_nodes:=plan->'beforeNodes';
 FOR entry IN SELECT key,value FROM jsonb_each(plan->'afterNodes') n WHERE
  before_nodes ? n.key AND (n.value IS DISTINCT FROM before_nodes->n.key OR n.key=primary_reference AND mode='update_object')
  ORDER BY CASE WHEN before_nodes->n.key->'root'='null'::jsonb THEN 1 ELSE 0 END,key COLLATE "C" LOOP
  IF before_nodes->entry.key->'deleted'='true'::jsonb THEN CONTINUE;END IF;
  effect:=truss.runtime_owned_object_effect(selected_attempt,selected_index,entry.key,prepared_input,current_actor);
  events:=events||(effect->'events');deleted:=deleted||coalesce(effect->'deleted','[]'::jsonb);
  IF entry.key=primary_reference THEN primary_result:=effect;END IF;
 END LOOP;
 IF primary_result IS NULL OR primary_result->>'operation' IS DISTINCT FROM mode THEN RAISE EXCEPTION 'one original primary result required' USING ERRCODE='55000';END IF;
 result:=jsonb_set(primary_result,'{events}',events);
 IF mode IN ('delete_object','delete_edge') THEN result:=jsonb_set(result,'{deleted}',deleted);END IF;
 IF octet_length(convert_to(result::text,'UTF8'))>16777216 THEN RAISE EXCEPTION 'bounded complete original result required' USING ERRCODE='54000';END IF;
 UPDATE truss.runtime_owned_operation p SET result=owned_step_body.result
  WHERE p.attempt_id=selected_attempt AND p.operation_index=selected_index
   AND p.writer_xid=attempt.writer_xid AND p.plan=owned_step_body.plan AND p.result IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'one original owned result slot required' USING ERRCODE='55000';END IF;
 SELECT p.result INTO STRICT stored_result FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=selected_attempt AND p.operation_index=selected_index;
 IF stored_result IS DISTINCT FROM result THEN RAISE EXCEPTION 'exact sealed owned result required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt a SET next_index=a.next_index+1
  WHERE a.id=selected_attempt AND a.writer_xid=attempt.writer_xid AND a.actor_oid=current_actor
   AND NOT a.complete AND a.next_index=selected_index AND a.results='[]'::jsonb AND a.aliases='[]'::jsonb;
 IF NOT FOUND THEN RAISE EXCEPTION 'one ordered owned progress advance required' USING ERRCODE='55000';END IF;
 SELECT a.actor_oid,a.writer_xid,a.next_index,a.results,a.aliases,a.complete INTO STRICT progress
  FROM truss.runtime_object_attempt a WHERE a.id=selected_attempt;
 IF ROW(progress.actor_oid,progress.writer_xid,progress.next_index,progress.results,progress.aliases,progress.complete)
  IS DISTINCT FROM ROW(current_actor,attempt.writer_xid,selected_index+1,'[]'::jsonb,'[]'::jsonb,false) THEN
  RAISE EXCEPTION 'exact stored owned progress required' USING ERRCODE='55000';END IF;
 -- New edge IDs are now backed by their genuine original parent result.
 FOR selected_transition IN SELECT transition_id FROM truss.runtime_edge_transition WHERE attempt_id=selected_attempt AND operation_index=selected_index LOOP
  IF closing_actor IS NULL THEN closing_actor:=truss.runtime_person(false);END IF;
  PERFORM truss.runtime_owned_edge_transition_validate(selected_transition,false,closing_actor);
 END LOOP;
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
   namespace_key:=definition.type_id::text||':'||definition.key_num::text;
   codec:=codecs->namespace_key;
   IF codec IS NULL THEN
    codec:=truss.runtime_owned_key_codec_metadata(definition.type_id,definition.key_num);
    IF codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+octet_length(namespace_key)+8<=4194304 THEN
     codecs:=codecs||jsonb_build_object(namespace_key,codec);
     codec_bytes:=codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+octet_length(namespace_key)+8;
    END IF;
   END IF;
   tuple_bytes:=truss.runtime_owned_key_tuple_in_metadata(definition.type_id,definition.key_num,cells,codec);
   -- Source metadata is constant under the admitted catalog-head lock. Reuse
   -- only the namespace bytes within this preflight invocation; every tuple,
   -- bucket, membership and reservation check below still runs for every row.
   namespace_key:=definition.type_id::text||':'||definition.key_num::text;
   namespace_hex:=namespaces->>namespace_key;
   IF namespace_hex IS NULL THEN
    SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',definition.type_id,definition.key_num);
    namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
     'sourceEpoch',installation.source_epoch::text,'typeId',definition.type_id::text,'keyNumber',definition.key_num::text,
     'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
    namespaces:=namespaces||jsonb_build_object(namespace_key,encode(namespace,'hex'));
   ELSE namespace:=decode(namespace_hex,'hex');END IF;
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
 routes:=to_jsonb(route_items);lock_routes:=to_jsonb(lock_route_items);
 FOR route IN SELECT DISTINCT decode(value->>'namespace','hex') route_namespace,decode(value->>'transport','hex') route_transport FROM jsonb_array_elements(routes||lock_routes)
  ORDER BY route_namespace,route_transport LOOP
  PERFORM truss.lock_string_key_bucket(route.route_namespace,route.route_transport);
 END LOOP;
 -- The preceding route for exactly these bytes is the original seen-map value.
 -- Compute it once in route order instead of rebuilding an expanding JSON map.
 FOR route IN SELECT r.value entry,
  lag(r.value->>'reference') OVER route_history previous_reference,
  lag(r.ordinality) OVER route_history previous_ordinal
  FROM jsonb_array_elements(routes) WITH ORDINALITY r(value,ordinality)
  WINDOW route_history AS (PARTITION BY (r.value->>'namespace') COLLATE "C",(r.value->>'transport') COLLATE "C" ORDER BY r.ordinality)
  ORDER BY r.ordinality LOOP
  entry:=route.entry;
  namespace:=decode(entry->>'namespace','hex');transport:=decode(entry->>'transport','hex');
  reference:=entry->>'reference';
  SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(namespace,transport);
  IF entry->>'phase'='initial' THEN
   IF cardinality(observed.member_ids)<>1 THEN RAISE EXCEPTION 'one original live key member required' USING ERRCODE='55000';END IF;
   SELECT * INTO STRICT member FROM truss.object_key_bucket WHERE storage_row_id=observed.member_ids[1];
   IF member.object_id::text IS DISTINCT FROM entry->>'objectId' OR member.type_id IS DISTINCT FROM (entry->>'typeId')::int
    OR member.key_num IS DISTINCT FROM (entry->>'keyNumber')::smallint
    OR NOT truss.verify_object_string_key(member.object_id,member.type_id,member.key_num,decode(entry->>'tuple','hex')) THEN
    RAISE EXCEPTION 'original key membership and values required' USING ERRCODE='55000';END IF;
  ELSIF entry->'unchanged'='true'::jsonb THEN
   IF route.previous_reference IS DISTINCT FROM reference THEN RAISE EXCEPTION 'original unchanged key owner required' USING ERRCODE='55000';END IF;
  ELSE
   IF route.previous_ordinal IS NOT NULL OR cardinality(observed.member_ids)>0 OR cardinality(observed.reservation_ids)>0 THEN
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
 expected_events jsonb:='[]';expected_event jsonb;journal jsonb;event jsonb;ordinal int:=0;
 before_record jsonb;after_record jsonb;semantic_events jsonb:='[]';group_pin jsonb;input jsonb;history_key text;history_metadata jsonb;completed_slots bigint;
BEGIN
 IF authorize_read IS NULL THEN RAISE EXCEPTION 'explicit object validation mode required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT transition FROM truss.runtime_object_transition WHERE transition_id=selected_transition;
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
 input:=coalesce(prepared_input,convert_from(attempt.input_bytes,'UTF8')::jsonb);
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
    expected_events:=expected_events||jsonb_build_array(jsonb_build_object('operation','property','propertyId',property.prop_id::text,'definitionPin',expected_property_pin,
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

-- Independent rootless creates have no order-dependent reads. Lower their
-- already admitted native plans to INSERT ... SELECT, retaining the ordinary
-- transitions, original journals, permanent key reservations and settlement.
CREATE FUNCTION truss.runtime_owned_create_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;objects jsonb;keys jsonb;journals jsonb;transitions jsonb;results jsonb;
 expected jsonb;actual jsonb;dictionary jsonb:='{}';namespaces jsonb:='{}';metadata jsonb;
 selected_type int;property record;definition record;pin record;type_pin text;property_pins jsonb;property_order jsonb;
 group_id uuid:=gen_random_uuid();actor oid;counted int;total int;compiled_namespace bytea;route record;
 slot_results jsonb;
 codecs jsonb:='{}';codec jsonb;codec_bytes bigint:=2;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 total:=jsonb_array_length(input->'operations');
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.complete OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR total NOT BETWEEN 1 AND 1024 OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_object'
    OR o.value->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb)
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
  OR EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND
   (p.writer_xid IS DISTINCT FROM attempt.writer_xid OR p.result IS NOT NULL
    OR p.plan->'operation' IS DISTINCT FROM input->'operations'->p.operation_index
    OR p.plan->>'primary' IS DISTINCT FROM 'create:'||p.operation_index::text
    OR (p.plan->'beforeNodes') ? (p.plan->>'primary') OR p.plan->'beforeEdges'<>'{}'::jsonb
    OR p.plan->'afterEdges'<>'{}'::jsonb
    OR p.plan->'afterNodes'->(p.plan->>'primary')->'root' IS DISTINCT FROM 'null'::jsonb)) THEN
  RAISE EXCEPTION 'independent original rootless create batch required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF (SELECT value FROM truss.setting WHERE key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb
  OR (SELECT value FROM truss.setting WHERE key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
  RAISE EXCEPTION 'selected engine key/history settings required' USING ERRCODE='0A000';END IF;
 -- Catalog interpretation is compiled once per type, not once per object.
 FOR selected_type IN SELECT DISTINCT (p.plan->'afterNodes'->(p.plan->>'primary')->'image'->>'type_id')::int
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt LOOP
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',selected_type);
  type_pin:=pin.definition_pin;
  PERFORM truss.runtime_module_writer_qualified(pin.document_id,pin.module_id,actor);
  IF NOT truss.runtime_object_values_readable_qualified(selected_type,actor) THEN
   RAISE EXCEPTION 'current property and item readers required' USING ERRCODE='42501';END IF;
  property_pins:='{}';property_order:='[]';
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=selected_type AND retired_rev IS NULL ORDER BY prop_id LOOP
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',selected_type,property.prop_id);
   property_pins:=property_pins||jsonb_build_object(property.prop_id::text,pin.definition_pin);
   property_order:=property_order||to_jsonb(property.prop_id::text);
  END LOOP;
  dictionary:=dictionary||jsonb_build_object(selected_type::text,jsonb_build_object('typeId',selected_type::text,
   'revision',(SELECT rev::text FROM truss.schema_head WHERE id=1),'typePin',type_pin,'propertyOrder',property_order,'propertyPins',property_pins));
  FOR definition IN SELECT * FROM truss.key_def WHERE type_id=selected_type AND retired_rev IS NULL ORDER BY key_num LOOP
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',selected_type,definition.key_num);
   codec:=truss.runtime_owned_key_codec_metadata(selected_type,definition.key_num);
   IF codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32<=4194304 THEN
    codecs:=codecs||jsonb_build_object(selected_type::text||':'||definition.key_num::text,codec);
    codec_bytes:=codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32;
   END IF;
   compiled_namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected_type::text,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   namespaces:=namespaces||jsonb_build_object(selected_type::text||':'||definition.key_num::text,encode(compiled_namespace,'hex'));
  END LOOP;
 END LOOP;
 WITH allocated AS MATERIALIZED (
  SELECT p.operation_index,p.plan->'operation' operation,
   p.plan->'afterNodes'->(p.plan->>'primary') state,nextval('truss.id_seq') id,clock_timestamp() created_at
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt ORDER BY p.operation_index),
 rows AS (
  SELECT operation_index,operation,jsonb_build_object('id',id,'type_id',(state->'image'->>'type_id')::int,
   'root_id',NULL,'root_type',NULL,'rev',(state->'image'->>'rev')::int,'ver',1,
   'props',state->'image'->'props','retained',nullif(state->'image'->'retained','{}'::jsonb),
   'created_at',created_at,'updated_at',created_at) image,
   (state->'identity')||jsonb_build_object('id',id::text) identity FROM allocated)
 SELECT jsonb_agg(jsonb_build_object('index',operation_index,'operation',operation,'object',image,'identity',identity) ORDER BY operation_index)
 INTO objects FROM rows;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(objects) o WHERE (o.value->'object'->>'id')::bigint<=0) THEN
  RAISE EXCEPTION 'positive native object ids required' USING ERRCODE='54000';END IF;
 -- One canonical object INSERT for the whole batch. Compare returned rows and
 -- the stored rows so BEFORE/AFTER triggers cannot silently change an image.
 SELECT jsonb_agg(value->'object' ORDER BY (value->'object'->>'id')::bigint) INTO expected FROM jsonb_array_elements(objects);
 WITH inserted AS (
  INSERT INTO truss.object SELECT r.* FROM jsonb_array_elements(objects) o
   CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object,o.value->'object') r
  RETURNING *) SELECT jsonb_agg(to_jsonb(inserted) ORDER BY id) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected OR expected IS DISTINCT FROM
  (SELECT jsonb_agg(to_jsonb(t) ORDER BY t.id) FROM truss.object t JOIN jsonb_array_elements(objects) o
   ON t.id=(o.value->'object'->>'id')::bigint AND t.type_id=(o.value->'object'->>'type_id')::int) THEN
  RAISE EXCEPTION 'exact batch object insert required' USING ERRCODE='55000';END IF;
 WITH cells AS MATERIALIZED (
  SELECT o.value object,k.key_num,k.prop_ids,decode(namespaces->>((o.value->'object'->>'type_id')||':'||k.key_num::text),'hex') namespace,
   truss.runtime_owned_key_tuple_in_metadata(k.type_id,k.key_num,
    (SELECT jsonb_agg(o.value->'object'->'props'->i.prop_id::text ORDER BY i.ordinal)
     FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ordinal)),
    coalesce(codecs->(k.type_id::text||':'||k.key_num::text),truss.runtime_owned_key_codec_metadata(k.type_id,k.key_num))) tuple
  FROM jsonb_array_elements(objects) o JOIN truss.key_def k ON k.type_id=(o.value->'object'->>'type_id')::int AND k.retired_rev IS NULL),
 encoded AS MATERIALIZED (
  SELECT *,convert_to('umf-key-tuple-v1:hex:'||encode(tuple,'hex'),'UTF8') transport,
   convert_to(jsonb_build_object('profile','truss-created-key-context/0.2','groupId',group_id::text,
    'sourceEpoch',installation.source_epoch::text,'xid',attempt.writer_xid::text,'actorOid',actor::text,
    'actor',session_user::text,'operationIndex',object->>'index','derivation','postgresql-umf-key-tuple-v1')::text,'UTF8') context
  FROM cells),
 rows AS (
  SELECT object->'index' index,jsonb_build_object('storage_row_id',nextval('truss.key_storage_row_seq'),
   'type_id',(object->'object'->>'type_id')::int,'key_num',key_num,'object_id',(object->'object'->>'id')::bigint,
   'namespace_bytes',namespace,'key_bytes',transport,'original_context_bytes',context,
   'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport)) membership,
   jsonb_build_object('storage_row_id',nextval('truss.key_storage_row_seq'),'namespace_bytes',namespace,'key_bytes',transport,
    'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport),
    'original_reservation_bytes',convert_to(jsonb_build_object('profile','truss-created-key-reservation/0.1',
     'groupId',group_id::text,'sourceEpoch',installation.source_epoch::text,'xid',attempt.writer_xid::text,
     'objectId',object->'object'->>'id','typeId',object->'object'->>'type_id','keyNumber',key_num::text,
     'contextBase64',replace(encode(context,'base64'),chr(10),''))::text,'UTF8')) reservation
  FROM encoded)
 SELECT coalesce(jsonb_agg(to_jsonb(rows) ORDER BY (index#>>'{}')::int,(membership->>'key_num')::int),'[]'::jsonb) INTO keys FROM rows;
 -- Capture already acquired these exact key routes in canonical order. Recheck
 -- every bucket after object triggers and before writing membership/reservation.
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(keys) e
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,e.value->'membership') r
  WHERE NOT EXISTS(SELECT 1 FROM truss.key_bucket_guard g WHERE g.namespace_sha256=r.namespace_sha256 AND g.key_sha256=r.key_sha256)
   OR EXISTS(SELECT 1 FROM truss.object_key_bucket b WHERE b.namespace_sha256=r.namespace_sha256 AND b.key_sha256=r.key_sha256 AND b.namespace_bytes=r.namespace_bytes AND b.key_bytes=r.key_bytes)
   OR EXISTS(SELECT 1 FROM truss.object_key_reservation_bucket b WHERE b.namespace_sha256=r.namespace_sha256 AND b.key_sha256=r.key_sha256 AND b.namespace_bytes=r.namespace_bytes AND b.key_bytes=r.key_bytes)) THEN
  RAISE EXCEPTION 'key already allocated or reserved' USING ERRCODE='23505';END IF;
 SELECT coalesce(jsonb_agg(value->'membership' ORDER BY (value->'membership'->>'storage_row_id')::bigint),'[]') INTO expected FROM jsonb_array_elements(keys);
 WITH inserted AS (
  INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
  SELECT r.storage_row_id,r.type_id,r.key_num,r.object_id,r.namespace_bytes,r.key_bytes,r.original_context_bytes
  FROM jsonb_array_elements(keys) o CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,o.value->'membership') r
  RETURNING *) SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch key membership required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(value->'reservation' ORDER BY (value->'reservation'->>'storage_row_id')::bigint),'[]') INTO expected FROM jsonb_array_elements(keys);
 WITH inserted AS (
  INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes)
  SELECT r.storage_row_id,r.namespace_bytes,r.key_bytes,r.original_reservation_bytes
  FROM jsonb_array_elements(keys) o CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_reservation_bucket,o.value->'reservation') r
  RETURNING *) SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch key reservation required' USING ERRCODE='55000';END IF;
 UPDATE truss.key_bucket_guard g SET generation=g.generation+r.advances
 FROM (SELECT k.namespace_sha256,k.key_sha256,count(*) advances FROM jsonb_array_elements(keys) o
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,o.value->'membership') k
  GROUP BY k.namespace_sha256,k.key_sha256) r WHERE g.namespace_sha256=r.namespace_sha256 AND g.key_sha256=r.key_sha256;
 WITH events AS MATERIALIZED (
  SELECT o.value object,nextval('truss.journal_seq') seq,clock_timestamp() at,
   truss.runtime_owned_history_record_in_metadata(o.value->'object',o.value->'identity',dictionary->(o.value->'object'->>'type_id')) image
  FROM jsonb_array_elements(objects) o),
 payloads AS MATERIALIZED (
  SELECT *,jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-create/0.1','xid',attempt.writer_xid::text,'seq',seq::text,'identity',object->'identity',
   'eventVersion','1','eventCatalogRevision',object->'object'->>'rev','operation','create','after',image,
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text)) event FROM events),
 grouped AS (
  SELECT *,event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0',
   'eventCount','1','orderedEventDigest',encode(sha256(convert_to(jsonb_build_array(event)::text,'UTF8')),'hex'))) payload FROM payloads)
 SELECT jsonb_agg(jsonb_build_object('index',object->'index','journal',jsonb_build_object('seq',seq,'at',at,'xid',attempt.writer_xid::text,
  'entity_kind','o','entity_id',(object->'object'->>'id')::bigint,'entity_type',(object->'object'->>'type_id')::int,
  'ver',1,'op','create','prop_id',NULL,'old_value',NULL,'rev',(object->'object'->>'rev')::int,
  'new_value',truss.runtime_exact_wrapper('event',convert_to(payload::text,'UTF8')),
  'origin',truss.runtime_exact_wrapper('origin',convert_to((payload->'origin')::text,'UTF8')))) ORDER BY seq) INTO journals FROM grouped;
 SELECT jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint) INTO expected FROM jsonb_array_elements(journals);
 WITH inserted AS (
  INSERT INTO truss.journal SELECT r.* FROM jsonb_array_elements(journals) o
   CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.journal,o.value->'journal') r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted) ORDER BY seq) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch journal append required' USING ERRCODE='55000';END IF;
 WITH key_sets AS MATERIALIZED (
  SELECT (value->>'index')::int index,jsonb_agg(value->'membership' ORDER BY (value->'membership'->>'key_num')::int) members
  FROM jsonb_array_elements(keys) GROUP BY (value->>'index')::int)
 SELECT jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(o.value->>'index')::int,
  'writer_xid',attempt.writer_xid::text,'object_id',(o.value->'object'->>'id')::bigint,'type_id',(o.value->'object'->>'type_id')::int,
  'before_object',NULL,'after_object',o.value->'object','after_keys',coalesce(k.members,'[]'::jsonb),
  'journal',jsonb_build_array(j.value->'journal')) ORDER BY (o.value->>'index')::int) INTO transitions
 FROM jsonb_array_elements(objects) o JOIN jsonb_array_elements(journals) j ON (j.value->>'index')::int=(o.value->>'index')::int
 LEFT JOIN key_sets k ON k.index=(o.value->>'index')::int;
 WITH inserted AS (
  INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
  SELECT r.attempt_id,r.operation_index,r.writer_xid,r.object_id,r.type_id,r.before_object,r.after_object,r.after_keys,r.journal
  FROM jsonb_populate_recordset(NULL::truss.runtime_object_transition,transitions) r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted)-'transition_id' ORDER BY operation_index) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM transitions THEN RAISE EXCEPTION 'exact batch transitions required' USING ERRCODE='55000';END IF;
 WITH slots AS (
  SELECT (o.value->>'index')::int index,jsonb_build_object('operation','create_object','outcome','created','identity',o.value->'identity','version','1',
   'events',jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-owned-create/0.1',
    'xid',attempt.writer_xid::text,'seq',j.value->'journal'->>'seq')))
   ||CASE WHEN (o.value->'operation') ? 'alias' THEN jsonb_build_object('alias',o.value->'operation'->>'alias') ELSE '{}'::jsonb END result
  FROM jsonb_array_elements(objects) o JOIN jsonb_array_elements(journals) j ON j.value->'index'=o.value->'index')
 SELECT jsonb_object_agg(index::text,result) INTO slot_results FROM slots;
 WITH updated AS (
  UPDATE truss.runtime_owned_operation p SET result=slot_results->p.operation_index::text
  WHERE p.attempt_id=selected_attempt AND p.result IS NULL AND slot_results ? p.operation_index::text
  RETURNING p.operation_index,p.result)
 SELECT count(*) INTO counted FROM updated;
 IF counted<>total THEN RAISE EXCEPTION 'complete sealed batch result slots required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch progress advance required' USING ERRCODE='55000';END IF;
 -- Ordinary finish/commit independently compare every native row, original
 -- input, result slot, reservation and journal. No validation cache is issued.
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_create_batch(uuid) FROM PUBLIC;

-- Reconstruct independent creates as a relation, rather than repeatedly
-- opening each complete attempt/plan/history through the general graph walker.
-- Row and journal constraint triggers remain independent commit obligations.
CREATE FUNCTION truss.runtime_owned_create_batch_validate(attempt truss.runtime_object_attempt,input jsonb,history_dictionary jsonb,check_final boolean,actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE total int:=attempt.next_index;last_plan jsonb;expected_nodes jsonb;before_nodes jsonb;problem boolean;owner record;
BEGIN
 IF (SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=attempt.id)<>total
  OR EXISTS(SELECT 1 FROM truss.runtime_edge_transition WHERE attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'complete original create effect inventory required' USING ERRCODE='55000';END IF;
 SELECT plan INTO STRICT last_plan FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=total-1;
 SELECT jsonb_object_agg('create:'||p.operation_index::text,p.plan->'afterNodes'->(p.plan->>'primary')),
  coalesce(jsonb_object_agg('create:'||p.operation_index::text,p.plan->'afterNodes'->(p.plan->>'primary'))
   FILTER(WHERE p.operation_index<total-1),'{}'::jsonb)
 INTO expected_nodes,before_nodes FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id;
 IF last_plan->'beforeNodes' IS DISTINCT FROM before_nodes OR last_plan->'afterNodes' IS DISTINCT FROM expected_nodes THEN
  RAISE EXCEPTION 'complete original independent create graph required' USING ERRCODE='55000';END IF;
 FOR owner IN SELECT DISTINCT t.type_id,t.document_id,t.module FROM truss.runtime_object_transition x JOIN truss.type_def t USING(type_id)
  WHERE x.attempt_id=attempt.id LOOP
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,actor);
  IF NOT truss.runtime_object_values_readable_qualified(owner.type_id,actor) THEN
   RAISE EXCEPTION 'current original property readers required' USING ERRCODE='42501';END IF;
 END LOOP;
 WITH members AS MATERIALIZED (
  SELECT p.operation_index,p.plan,p.result,p.plan->'operation' operation,
   p.plan->'afterNodes'->(p.plan->>'primary') state,t.transition_id,t.writer_xid,t.object_id,t.type_id,
   t.before_object,t.after_object,t.after_keys,t.journal,t.journal->0 entry
  FROM truss.runtime_owned_operation p LEFT JOIN truss.runtime_object_transition t
   ON t.attempt_id=p.attempt_id AND t.operation_index=p.operation_index
  WHERE p.attempt_id=attempt.id),
 images AS MATERIALIZED (
  SELECT m.*,m.state->'identity'||jsonb_build_object('id',m.object_id::text) identity,
   decode(m.entry->'new_value'->>'bytesBase64','base64') original,
   (m.entry->>'seq')::bigint seq,(m.entry->>'at')::timestamptz at
  FROM members m),
 events AS MATERIALIZED (
  SELECT m.*,jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal',
   'sourceEpoch',attempt.context->>'sourceEpoch','historyProfile','truss-native-owned-create/0.1',
   'xid',attempt.writer_xid::text,'seq',m.seq::text,'identity',m.identity,'eventVersion','1',
   'eventCatalogRevision',m.after_object->>'rev','operation','create',
   'after',truss.runtime_owned_history_record_in_metadata(m.after_object,m.identity,
    history_dictionary->jsonb_build_array((m.after_object->>'rev')::int,m.type_id)::text),
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text)) event
  FROM images m),
 checked AS MATERIALIZED (
  SELECT m.*,m.event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0',
   'eventCount','1','orderedEventDigest',encode(sha256(convert_to(jsonb_build_array(m.event)::text,'UTF8')),'hex'))) payload
  FROM events m)
 SELECT EXISTS(SELECT 1 FROM checked m LEFT JOIN truss.journal j ON j.at=m.at AND j.seq=m.seq WHERE
  m.transition_id IS NULL OR m.writer_xid IS DISTINCT FROM attempt.writer_xid
  OR m.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
  OR m.plan->'operationIndex' IS DISTINCT FROM to_jsonb(m.operation_index)
  OR m.plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
  OR m.operation IS DISTINCT FROM input->'operations'->m.operation_index
  OR m.plan->>'primary' IS DISTINCT FROM 'create:'||m.operation_index::text
  OR m.plan->'beforeEdges'<>'{}'::jsonb OR m.plan->'afterEdges'<>'{}'::jsonb
  OR m.operation_index<total-1 AND (m.plan->'beforeNodes'<>'{}'::jsonb
   OR m.plan->'afterNodes' IS DISTINCT FROM jsonb_build_object(m.plan->>'primary',m.state))
  OR m.state->'root' IS DISTINCT FROM 'null'::jsonb OR m.state->'deleted' IS DISTINCT FROM 'false'::jsonb
  OR m.before_object IS NOT NULL OR m.after_object IS NULL
  OR m.object_id<=0 OR m.type_id IS DISTINCT FROM (m.state->'image'->>'type_id')::int
  OR m.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM
   ((m.state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',m.object_id,'root_id',NULL,'root_type',NULL)
  OR jsonb_array_length(m.journal)<>1 OR to_jsonb(j) IS DISTINCT FROM m.entry
  OR m.entry->>'entity_kind' IS DISTINCT FROM 'o' OR m.entry->>'entity_id' IS DISTINCT FROM m.object_id::text
  OR m.entry->>'entity_type' IS DISTINCT FROM m.type_id::text OR m.entry->>'xid' IS DISTINCT FROM attempt.writer_xid::text
  OR m.entry->>'ver' IS DISTINCT FROM '1' OR m.entry->>'op' IS DISTINCT FROM 'create'
  OR m.entry->>'prop_id' IS NOT NULL OR m.entry->>'old_value' IS NOT NULL
  OR m.entry->>'rev' IS DISTINCT FROM m.after_object->>'rev'
  OR m.entry->'new_value' IS DISTINCT FROM truss.runtime_exact_wrapper('event',convert_to(m.payload::text,'UTF8'))
  OR m.entry->'origin' IS DISTINCT FROM truss.runtime_exact_wrapper('origin',convert_to((m.event->'origin')::text,'UTF8'))
  OR m.result IS DISTINCT FROM jsonb_build_object('operation','create_object','outcome','created','identity',m.identity,'version','1',
    'events',jsonb_build_array(jsonb_build_object('sourceEpoch',attempt.context->>'sourceEpoch',
     'historyProfile','truss-native-owned-create/0.1','xid',attempt.writer_xid::text,'seq',m.seq::text)))
    ||CASE WHEN m.operation ? 'alias' THEN jsonb_build_object('alias',m.operation->>'alias') ELSE '{}'::jsonb END
  OR (SELECT count(*) FROM truss.journal x WHERE x.entity_kind='o' AND x.entity_id=m.object_id
    AND x.entity_type=m.type_id AND x.xid=attempt.writer_xid AND x.ver=1)<>1) INTO problem;
 IF problem THEN RAISE EXCEPTION 'original batch create source, result, image and journal correspondence required' USING ERRCODE='55000';END IF;
 -- Hashes route the join; original bytes determine the permanent reservation.
 IF EXISTS(SELECT 1 FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.after_keys) k
  LEFT JOIN truss.object_key_reservation_bucket r
   ON r.namespace_sha256=decode(substring(k.value->>'namespace_sha256' FROM 3),'hex')
    AND r.key_sha256=decode(substring(k.value->>'key_sha256' FROM 3),'hex')
    AND r.namespace_bytes=decode(substring(k.value->>'namespace_bytes' FROM 3),'hex')
    AND r.key_bytes=decode(substring(k.value->>'key_bytes' FROM 3),'hex')
  WHERE t.attempt_id=attempt.id AND (r.storage_row_id IS NULL
   OR convert_from(r.original_reservation_bytes,'UTF8')::jsonb->>'objectId' IS DISTINCT FROM t.object_id::text
   OR convert_from(r.original_reservation_bytes,'UTF8')::jsonb->>'typeId' IS DISTINCT FROM t.type_id::text
   OR convert_from(r.original_reservation_bytes,'UTF8')::jsonb->>'keyNumber' IS DISTINCT FROM k.value->>'key_num'
   OR decode(convert_from(r.original_reservation_bytes,'UTF8')::jsonb->>'contextBase64','base64')
     IS DISTINCT FROM decode(substring(k.value->>'original_context_bytes' FROM 3),'hex'))) THEN
  RAISE EXCEPTION 'permanent batch create key reservation required' USING ERRCODE='55000';END IF;
 IF check_final AND EXISTS(SELECT 1 FROM truss.runtime_object_transition t JOIN truss.edge e
  ON (e.source_id=t.object_id AND e.source_type=t.type_id) OR (e.target_id=t.object_id AND e.target_type=t.type_id)
  WHERE t.attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'complete final incident edge inventory required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_create_batch_validate(truss.runtime_object_attempt,jsonb,jsonb,boolean,oid) FROM PUBLIC;

-- Independent edges between stored endpoints do not read earlier operations.
-- Keep ownership-changing/alias/mixed groups on the ordered graph path.
CREATE FUNCTION truss.runtime_owned_edge_create_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;last_plan jsonb;edges jsonb;journals jsonb;transitions jsonb;expected jsonb;actual jsonb;
 endpoints jsonb;contexts jsonb;actor oid;total int;counted int;revision int;owner record;
 slot_results jsonb;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;total:=jsonb_array_length(input->'operations');
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.complete OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR total NOT BETWEEN 1 AND 1024 OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_edge'
    OR o.value->'source'->>'state' IS DISTINCT FROM 'stored' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored')
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total THEN
  RAISE EXCEPTION 'independent original edge create batch required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 SELECT plan INTO STRICT last_plan FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt AND operation_index=total-1;
 FOR owner IN SELECT DISTINCT r.* FROM truss.runtime_owned_operation p JOIN truss.rel_def r
  ON r.rel_type_id=(p.plan->'afterEdges'->(p.plan->>'primary')->'identity'->>'typeId')::int
  WHERE p.attempt_id=selected_attempt LOOP
  IF owner.lifecycle<>'independent' OR NOT owner.directed OR owner.composition OR owner.assoc_type_id IS NOT NULL OR owner.retired_rev IS NOT NULL THEN
   RAISE EXCEPTION 'selected independent relationship required' USING ERRCODE='0A000';END IF;
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,actor);
 END LOOP;
 -- Resolve each distinct stored endpoint/root context once before edge writes.
 WITH endpoint_refs AS MATERIALIZED (
  SELECT p.plan->'afterEdges'->(p.plan->>'primary')->>'source' reference FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt
  UNION SELECT p.plan->'afterEdges'->(p.plan->>'primary')->>'target' FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt)
 SELECT jsonb_object_agg(reference,truss.runtime_owned_identity(selected_attempt,total-1,reference,'object',last_plan,attempt)) INTO endpoints FROM endpoint_refs;
 SELECT jsonb_object_agg(key,truss.runtime_endpoint_ownership(value,revision)) INTO contexts FROM jsonb_each(endpoints);
 IF EXISTS(SELECT 1 FROM jsonb_each(endpoints) e LEFT JOIN truss.object o
  ON o.id=(e.value->>'id')::bigint AND o.type_id=(e.value->>'typeId')::int
  WHERE to_jsonb(o)-ARRAY['created_at','updated_at'] IS DISTINCT FROM
   truss.runtime_owned_object_image(selected_attempt,total-1,e.key,'before',last_plan,attempt)) THEN
  RAISE EXCEPTION 'original batch endpoint prestate required' USING ERRCODE='55000';END IF;
 WITH planned AS MATERIALIZED (
  SELECT p.operation_index,p.plan->'operation' operation,p.plan->'afterEdges'->(p.plan->>'primary') state,
   nextval('truss.id_seq') id,clock_timestamp() created_at FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=selected_attempt ORDER BY p.operation_index),
 images AS (
  SELECT *,state->'image'||jsonb_build_object('id',id,
   'source_id',(endpoints->(state->>'source')->>'id')::bigint,'source_type',(endpoints->(state->>'source')->>'typeId')::int,
   'target_id',(endpoints->(state->>'target')->>'id')::bigint,'target_type',(endpoints->(state->>'target')->>'typeId')::int,
   'order_key',state->'orderKey'->>'text','created_at',created_at,'updated_at',created_at) image,
   state->'identity'||jsonb_build_object('id',id::text) identity FROM planned)
 SELECT jsonb_agg(jsonb_build_object('index',operation_index,'operation',operation,'edge',image,'identity',identity,
  'source',endpoints->(state->>'source'),'target',endpoints->(state->>'target'),
  'endpointOwnership',jsonb_build_object('profile','truss-edge-endpoint-ownership/0.1','captureCatalogRevision',revision::text,
   'before',NULL,'after',jsonb_build_object('source',contexts->(state->>'source'),'target',contexts->(state->>'target'))))
  ORDER BY operation_index) INTO edges FROM images;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(edges) e WHERE (e.value->'edge'->>'id')::bigint<=0) THEN
  RAISE EXCEPTION 'positive native edge ids required' USING ERRCODE='54000';END IF;
 PERFORM truss.runtime_lock_edge_business_key(routes.k) FROM (
  SELECT truss.runtime_edge_business_key((value->'edge'->>'rel_type_id')::int,value->'source',value->'target') k
  FROM jsonb_array_elements(edges)) routes ORDER BY routes.k COLLATE "C";
 SELECT jsonb_agg(value->'edge' ORDER BY (value->'edge'->>'id')::bigint) INTO expected FROM jsonb_array_elements(edges);
 WITH inserted AS (INSERT INTO truss.edge SELECT r.* FROM jsonb_array_elements(edges) e
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.edge,e.value->'edge') r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted) ORDER BY id) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected OR expected IS DISTINCT FROM
  (SELECT jsonb_agg(to_jsonb(t) ORDER BY t.id) FROM truss.edge t JOIN jsonb_array_elements(edges) e ON t.id=(e.value->'edge'->>'id')::bigint) THEN
  RAISE EXCEPTION 'exact batch edge insert required' USING ERRCODE='55000';END IF;
 WITH allocated AS MATERIALIZED (
  SELECT value edge,nextval('truss.journal_seq') seq,clock_timestamp() at FROM jsonb_array_elements(edges)),
 events AS MATERIALIZED (
  SELECT *,jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-edge-mutation/0.1','xid',attempt.writer_xid::text,'seq',seq::text,'identity',edge->'identity',
   'eventVersion','1','eventCatalogRevision',revision::text,'operation','create',
   'after',truss.runtime_edge_history(edge->'edge',edge->'identity',edge->'source',edge->'target'),
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text)) event FROM allocated),
 grouped AS (
  SELECT *,event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount','1',
   'orderedEventDigest',encode(sha256(convert_to(jsonb_build_array(event)::text,'UTF8')),'hex'))) payload FROM events)
 SELECT jsonb_agg(jsonb_build_object('index',edge->'index','journal',jsonb_build_object('seq',seq,'at',at,'xid',attempt.writer_xid::text,
  'entity_kind','e','entity_id',(edge->'edge'->>'id')::bigint,'entity_type',(edge->'edge'->>'rel_type_id')::int,
  'ver',1,'op','create','prop_id',NULL,'old_value',NULL,'rev',revision,
  'new_value',truss.runtime_exact_wrapper('event',convert_to(payload::text,'UTF8')),
  'origin',truss.runtime_exact_wrapper('origin',convert_to((payload->'origin')::text,'UTF8')))) ORDER BY seq) INTO journals FROM grouped;
 SELECT jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint) INTO expected FROM jsonb_array_elements(journals);
 WITH inserted AS (INSERT INTO truss.journal SELECT r.* FROM jsonb_array_elements(journals) e
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.journal,e.value->'journal') r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted) ORDER BY seq) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch edge journal append required' USING ERRCODE='55000';END IF;
 SELECT jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(e.value->>'index')::int,'writer_xid',attempt.writer_xid::text,
  'edge_id',(e.value->'edge'->>'id')::bigint,'rel_type_id',(e.value->'edge'->>'rel_type_id')::int,'before_edge',NULL,'after_edge',e.value->'edge',
  'journal',jsonb_build_array(j.value->'journal'),'old_source',NULL,'old_target',NULL,
  'source_identity',e.value->'source','target_identity',e.value->'target','endpoint_ownership',e.value->'endpointOwnership')
  ORDER BY (e.value->>'index')::int) INTO transitions
 FROM jsonb_array_elements(edges) e JOIN jsonb_array_elements(journals) j ON (j.value->>'index')::int=(e.value->>'index')::int;
 WITH inserted AS (
  INSERT INTO truss.runtime_edge_transition(attempt_id,operation_index,writer_xid,edge_id,rel_type_id,before_edge,after_edge,journal,old_source,old_target,source_identity,target_identity,endpoint_ownership)
  SELECT r.attempt_id,r.operation_index,r.writer_xid,r.edge_id,r.rel_type_id,r.before_edge,r.after_edge,r.journal,r.old_source,r.old_target,r.source_identity,r.target_identity,r.endpoint_ownership
  FROM jsonb_populate_recordset(NULL::truss.runtime_edge_transition,transitions) r RETURNING *)
 SELECT jsonb_agg(to_jsonb(inserted)-'transition_id' ORDER BY operation_index) INTO actual FROM inserted;
 IF actual IS DISTINCT FROM transitions THEN RAISE EXCEPTION 'exact batch edge transitions required' USING ERRCODE='55000';END IF;
 WITH slots AS (
  SELECT (e.value->>'index')::int index,jsonb_build_object('operation','create_edge','outcome','created','identity',e.value->'identity','version','1',
   'events',jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-owned-edge-mutation/0.1',
    'xid',attempt.writer_xid::text,'seq',j.value->'journal'->>'seq')))
   ||CASE WHEN (e.value->'operation') ? 'alias' THEN jsonb_build_object('alias',e.value->'operation'->>'alias') ELSE '{}'::jsonb END result
  FROM jsonb_array_elements(edges) e JOIN jsonb_array_elements(journals) j ON (j.value->>'index')::int=(e.value->>'index')::int)
 SELECT jsonb_object_agg(index::text,result) INTO slot_results FROM slots;
 WITH updated AS (
  UPDATE truss.runtime_owned_operation p SET result=slot_results->p.operation_index::text
  WHERE p.attempt_id=selected_attempt AND p.result IS NULL AND slot_results ? p.operation_index::text
  RETURNING p.operation_index,p.result)
 SELECT count(*) INTO counted FROM updated;
 IF counted<>total THEN RAISE EXCEPTION 'complete sealed edge batch results required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch edge progress advance required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_create_batch(uuid) FROM PUBLIC;

-- Distinct stored-object value updates with unchanged ownership
-- have no order-dependent effects. The original planner, key preflight and
-- finish/commit validators still establish their complete source correspondence.
CREATE FUNCTION truss.runtime_owned_update_batch(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 input jsonb;objects jsonb;journals jsonb;transitions jsonb;results jsonb;expected jsonb;actual jsonb;
 dictionary jsonb:='{}';history_basis jsonb;image_revision int;selected_type int;property record;pin record;type_pin text;
 property_pins jsonb;property_order jsonb;source record;actor oid;total int;counted int;
 namespaces jsonb:='{}';compiled_namespace bytea;definition record;keys jsonb;route record;
 slot_results jsonb;
 codecs jsonb:='{}';codec jsonb;codec_bytes bigint:=2;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt FOR UPDATE NOWAIT;
 actor:=truss.runtime_person(false);input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 total:=jsonb_array_length(input->'operations');
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.complete OR attempt.next_index<>0 OR attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() OR total NOT BETWEEN 1 AND 1024
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored'
    OR o.value ? 'ownershipChange')
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
  OR (SELECT count(DISTINCT plan->>'primary') FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>total
  OR EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND
   (p.writer_xid IS DISTINCT FROM attempt.writer_xid OR p.result IS NOT NULL
    OR p.plan->'operation' IS DISTINCT FROM input->'operations'->p.operation_index
    OR p.plan->'beforeNodes'->(p.plan->>'primary') IS NULL
    OR p.plan->'afterNodes'->(p.plan->>'primary') IS NULL
    OR p.plan->'beforeNodes'->(p.plan->>'primary')->'deleted' IS DISTINCT FROM 'false'::jsonb
    OR p.plan->'afterNodes'->(p.plan->>'primary')->'deleted' IS DISTINCT FROM 'false'::jsonb
    OR p.plan->'beforeNodes'->(p.plan->>'primary')->'root' IS DISTINCT FROM p.plan->'afterNodes'->(p.plan->>'primary')->'root')) THEN
  RAISE EXCEPTION 'independent original value update batch required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 -- Bind every physical before-image before the single UPDATE. The initial
 -- scope has already locked these rows; duplicate targets use ordered execution.
 WITH members AS MATERIALIZED (
  SELECT p.operation_index,p.plan,p.plan->'beforeNodes'->(p.plan->>'primary') prior,
   p.plan->'afterNodes'->(p.plan->>'primary') desired,
   truss.runtime_owned_identity(selected_attempt,p.operation_index,p.plan->>'primary','object',p.plan,attempt) identity
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt),
 checked AS MATERIALIZED (
  SELECT m.*,to_jsonb(o) physical,
   truss.runtime_owned_object_image(selected_attempt,m.operation_index,m.plan->>'primary','before',m.plan,attempt) before_image,
   truss.runtime_owned_object_image(selected_attempt,m.operation_index,m.plan->>'primary','after',m.plan,attempt) after_image
  FROM members m LEFT JOIN truss.object o ON o.id=(m.identity->>'id')::bigint AND o.type_id=(m.identity->>'typeId')::int)
 SELECT jsonb_agg(jsonb_build_object('index',operation_index,'identity',identity,'before',physical,
  'after',CASE WHEN prior=desired THEN physical ELSE after_image||jsonb_build_object(
   'created_at',physical->'created_at','updated_at',clock_timestamp()) END,
  'beforeMatches',physical-ARRAY['created_at','updated_at'] IS NOT DISTINCT FROM before_image,
  'changed',prior IS DISTINCT FROM desired) ORDER BY operation_index) INTO objects FROM checked;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(objects) o WHERE o.value->'beforeMatches' IS DISTINCT FROM 'true'::jsonb
  OR o.value->'before'='null'::jsonb
  OR o.value->'changed'='true'::jsonb AND ((o.value->'before'->>'ver')::bigint=9223372036854775807
   OR (o.value->'after'->>'ver')::bigint<>(o.value->'before'->>'ver')::bigint+1)) THEN
  RAISE EXCEPTION 'original batch object prestate and version required' USING ERRCODE='55000';END IF;
 -- Resolve native history metadata once per type and image revision.
 FOR source IN SELECT DISTINCT (image->>'type_id')::int type_id,(image->>'rev')::int revision
  FROM jsonb_array_elements(objects) o CROSS JOIN LATERAL (VALUES(o.value->'before'),(o.value->'after')) v(image)
  WHERE o.value->'changed'='true'::jsonb LOOP
  selected_type:=source.type_id;image_revision:=source.revision;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',selected_type,NULL,image_revision);type_pin:=pin.definition_pin;
  PERFORM truss.runtime_module_writer_qualified(pin.document_id,pin.module_id,actor);
  IF NOT truss.runtime_object_values_readable_qualified(selected_type,actor) THEN
   RAISE EXCEPTION 'current property and item readers required' USING ERRCODE='42501';END IF;
  property_pins:='{}';property_order:='[]';
  IF image_revision=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>image_revision) THEN
   SELECT jsonb_build_object('prop_def',coalesce(jsonb_agg(to_jsonb(p)),'[]'::jsonb)) INTO history_basis
    FROM truss.prop_def p WHERE p.type_id=selected_type;
  ELSE history_basis:=truss.catalog_all_expected_records(image_revision);END IF;
  FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,history_basis->'prop_def') p
   WHERE p.type_id=selected_type ORDER BY prop_id LOOP
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',selected_type,property.prop_id,image_revision);
   property_pins:=property_pins||jsonb_build_object(property.prop_id::text,pin.definition_pin);
   property_order:=property_order||jsonb_build_array(property.prop_id::text);
  END LOOP;
  dictionary:=dictionary||jsonb_build_object(jsonb_build_array(image_revision,selected_type)::text,jsonb_build_object(
   'typeId',selected_type::text,'revision',image_revision::text,'typePin',type_pin,
   'propertyOrder',property_order,'propertyPins',property_pins));
 END LOOP;
 -- Preserve the preflight's complete ordered key simulation and locks. Lower
 -- only the already admitted physical key changes; unchanged memberships keep
 -- their original bytes and permanent reservations are never removed.
 FOR selected_type IN SELECT DISTINCT (value->'after'->>'type_id')::int FROM jsonb_array_elements(objects) LOOP
  FOR definition IN SELECT * FROM truss.key_def WHERE type_id=selected_type AND retired_rev IS NULL ORDER BY key_num LOOP
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',selected_type,definition.key_num);
   codec:=truss.runtime_owned_key_codec_metadata(selected_type,definition.key_num);
   IF codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32<=4194304 THEN
    codecs:=codecs||jsonb_build_object(selected_type::text||':'||definition.key_num::text,codec);
    codec_bytes:=codec_bytes+octet_length(convert_to(codec::text,'UTF8'))+32;
   END IF;
   compiled_namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected_type::text,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   namespaces:=namespaces||jsonb_build_object(selected_type::text||':'||definition.key_num::text,encode(compiled_namespace,'hex'));
  END LOOP;
 END LOOP;
 WITH cells AS MATERIALIZED (
  SELECT o.value object,k.key_num,decode(namespaces->>((o.value->'after'->>'type_id')||':'||k.key_num::text),'hex') namespace,
   truss.runtime_owned_key_tuple_in_metadata(k.type_id,k.key_num,
    (SELECT jsonb_agg(o.value->'after'->'props'->i.prop_id::text ORDER BY i.ordinal)
     FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ordinal)),
    coalesce(codecs->(k.type_id::text||':'||k.key_num::text),truss.runtime_owned_key_codec_metadata(k.type_id,k.key_num))) tuple,to_jsonb(old) old
  FROM jsonb_array_elements(objects) o CROSS JOIN LATERAL (
   SELECT k.* FROM truss.key_def k WHERE k.type_id=(o.value->'after'->>'type_id')::int AND k.retired_rev IS NULL OFFSET 0) k
  LEFT JOIN LATERAL (SELECT old.* FROM truss.object_key_bucket old WHERE old.object_id=(o.value->'after'->>'id')::bigint
   AND old.type_id=k.type_id AND old.key_num=k.key_num OFFSET 0) old ON true
  WHERE o.value->'changed'='true'::jsonb),
 encoded AS MATERIALIZED (
  SELECT *,convert_to('umf-key-tuple-v1:hex:'||encode(tuple,'hex'),'UTF8') transport FROM cells),
 checked AS MATERIALIZED (
  SELECT *,namespace IS DISTINCT FROM decode(substring(old->>'namespace_bytes' FROM 3),'hex')
   OR transport IS DISTINCT FROM decode(substring(old->>'key_bytes' FROM 3),'hex') changed FROM encoded),
 allocated AS MATERIALIZED (
  SELECT *,CASE WHEN changed THEN nextval('truss.key_storage_row_seq') END member_id,
   CASE WHEN changed THEN nextval('truss.key_storage_row_seq') END reservation_id FROM checked)
 SELECT coalesce(jsonb_agg(jsonb_build_object('old',old,'changed',changed,'namespace',encode(namespace,'hex'),'transport',encode(transport,'hex'),
  'membership',jsonb_build_object('storage_row_id',member_id,'type_id',(object->'after'->>'type_id')::int,'key_num',key_num,
   'object_id',(object->'after'->>'id')::bigint,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport),
   'original_context_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-context/0.2','attemptId',selected_attempt::text,
    'operationIndex',object->>'index','objectId',object->'after'->>'id','xid',attempt.writer_xid::text,'derivation','postgresql-umf-key-tuple-v1')::text,'UTF8')),
  'reservation',jsonb_build_object('storage_row_id',reservation_id,'namespace_bytes',namespace,'key_bytes',transport,
   'namespace_sha256',sha256(namespace),'key_sha256',sha256(transport),
   'original_reservation_bytes',convert_to(jsonb_build_object('profile','truss-updated-key-reservation/0.1','attemptId',selected_attempt::text,
    'operationIndex',object->>'index','objectId',object->'after'->>'id','typeId',object->'after'->>'type_id',
    'keyNumber',key_num::text,'xid',attempt.writer_xid::text)::text,'UTF8')))),'[]') INTO keys FROM allocated;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(keys) k WHERE k.value->'old'='null'::jsonb) THEN
  RAISE EXCEPTION 'original live batch key membership required' USING ERRCODE='55000';END IF;
 FOR route IN SELECT k.value,observed.member_ids,observed.reservation_ids FROM jsonb_array_elements(keys) k
  CROSS JOIN LATERAL truss.lock_string_key_bucket(decode(k.value->>'namespace','hex'),decode(k.value->>'transport','hex')) observed LOOP
  IF route.value->'changed'='true'::jsonb THEN
   IF cardinality(route.member_ids)>0 OR cardinality(route.reservation_ids)>0 THEN
    RAISE EXCEPTION 'key allocated or reserved' USING ERRCODE='23505';END IF;
  ELSIF cardinality(route.member_ids)<>1 OR route.member_ids[1]<>(route.value->'old'->>'storage_row_id')::bigint THEN
   RAISE EXCEPTION 'owned unchanged batch key required' USING ERRCODE='55000';END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(value->'old' ORDER BY (value->'old'->>'storage_row_id')::bigint),'[]') INTO expected
  FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb;
 WITH deleted AS (
  DELETE FROM truss.object_key_bucket old USING jsonb_array_elements(keys) k
  WHERE k.value->'changed'='true'::jsonb AND old.storage_row_id=(k.value->'old'->>'storage_row_id')::bigint RETURNING old.*)
 SELECT coalesce(jsonb_agg(to_jsonb(deleted) ORDER BY storage_row_id),'[]') INTO actual FROM deleted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch old key removal required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(value->'membership' ORDER BY (value->'membership'->>'storage_row_id')::bigint),'[]') INTO expected
  FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb;
 WITH inserted AS (
  INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
  SELECT r.storage_row_id,r.type_id,r.key_num,r.object_id,r.namespace_bytes,r.key_bytes,r.original_context_bytes
  FROM jsonb_array_elements(keys) k CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_bucket,k.value->'membership') r
  WHERE k.value->'changed'='true'::jsonb RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch updated key memberships required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(value->'reservation' ORDER BY (value->'reservation'->>'storage_row_id')::bigint),'[]') INTO expected
  FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb;
 WITH inserted AS (
  INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes)
  SELECT r.storage_row_id,r.namespace_bytes,r.key_bytes,r.original_reservation_bytes FROM jsonb_array_elements(keys) k
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object_key_reservation_bucket,k.value->'reservation') r
  WHERE k.value->'changed'='true'::jsonb RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY storage_row_id),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch updated key reservations required' USING ERRCODE='55000';END IF;
 UPDATE truss.key_bucket_guard g SET generation=g.generation+routes.advances FROM (
  SELECT decode(entry->>'namespace_sha256','hex') namespace_sha256,decode(entry->>'key_sha256','hex') key_sha256,count(*) advances
  FROM (SELECT jsonb_build_object('namespace_sha256',substring(value->'old'->>'namespace_sha256' FROM 3),
   'key_sha256',substring(value->'old'->>'key_sha256' FROM 3)) entry FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb
   UNION ALL SELECT jsonb_build_object('namespace_sha256',substring(value->'membership'->>'namespace_sha256' FROM 3),
   'key_sha256',substring(value->'membership'->>'key_sha256' FROM 3)) FROM jsonb_array_elements(keys) WHERE value->'changed'='true'::jsonb) all_routes
  GROUP BY entry->>'namespace_sha256',entry->>'key_sha256') routes
 WHERE g.namespace_sha256=routes.namespace_sha256 AND g.key_sha256=routes.key_sha256;
 SELECT coalesce(jsonb_agg(value->'after' ORDER BY (value->'after'->>'id')::bigint),'[]') INTO expected
 FROM jsonb_array_elements(objects) WHERE value->'changed'='true'::jsonb;
 WITH updated AS (
  UPDATE truss.object o SET props=r.props,retained=r.retained,root_id=r.root_id,root_type=r.root_type,
   rev=r.rev,ver=r.ver,updated_at=r.updated_at
  FROM jsonb_array_elements(objects) v CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.object,v.value->'after') r
  WHERE v.value->'changed'='true'::jsonb AND o.id=r.id AND o.type_id=r.type_id RETURNING o.*)
 SELECT coalesce(jsonb_agg(to_jsonb(updated) ORDER BY id),'[]') INTO actual FROM updated;
 IF actual IS DISTINCT FROM expected OR EXISTS(SELECT 1 FROM jsonb_array_elements(objects) v LEFT JOIN truss.object o
  ON o.id=(v.value->'after'->>'id')::bigint AND o.type_id=(v.value->'after'->>'type_id')::int
  WHERE to_jsonb(o) IS DISTINCT FROM v.value->'after') THEN
  RAISE EXCEPTION 'exact batch object updates required' USING ERRCODE='55000';END IF;
 WITH semantic AS MATERIALIZED (
  SELECT (o.value->>'index')::int operation_index,o.value object,p.prop_id ordinal,
   jsonb_build_object('operation','property','propertyId',p.prop_id::text,
    'definitionPin',dictionary->jsonb_build_array((o.value->'after'->>'rev')::int,p.type_id)::text->'propertyPins'->>p.prop_id::text,
    'before',CASE WHEN o.value->'before'->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',o.value->'before'->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END,
    'after',CASE WHEN o.value->'after'->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',o.value->'after'->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END) event
  FROM jsonb_array_elements(objects) o JOIN truss.prop_def p ON p.type_id=(o.value->'after'->>'type_id')::int
   AND p.since_rev<=(o.value->'after'->>'rev')::int AND (p.retired_rev IS NULL OR p.retired_rev>(o.value->'after'->>'rev')::int)
  WHERE o.value->'changed'='true'::jsonb AND o.value->'before'->'props'->p.prop_id::text IS DISTINCT FROM o.value->'after'->'props'->p.prop_id::text
  UNION ALL SELECT (o.value->>'index')::int,o.value,2147483648,jsonb_build_object('operation','metadata',
   'before',truss.runtime_owned_history_record_in_metadata(o.value->'before',o.value->'identity',dictionary->jsonb_build_array((o.value->'before'->>'rev')::int,(o.value->'before'->>'type_id')::int)::text),
   'after',truss.runtime_owned_history_record_in_metadata(o.value->'after',o.value->'identity',dictionary->jsonb_build_array((o.value->'after'->>'rev')::int,(o.value->'after'->>'type_id')::int)::text))
  FROM jsonb_array_elements(objects) o WHERE o.value->'changed'='true'::jsonb),
 allocated AS MATERIALIZED (
  SELECT *,nextval('truss.journal_seq') seq,clock_timestamp() at FROM semantic ORDER BY operation_index,ordinal),
 events AS MATERIALIZED (
  SELECT *,event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',seq::text,'identity',object->'identity',
   'eventVersion',object->'after'->>'ver','eventCatalogRevision',object->'after'->>'rev',
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text)) payload FROM allocated),
 digests AS MATERIALIZED (
  SELECT operation_index,count(*) amount,encode(sha256(convert_to(jsonb_agg(payload ORDER BY ordinal)::text,'UTF8')),'hex') digest
  FROM events GROUP BY operation_index)
 SELECT coalesce(jsonb_agg(jsonb_build_object('index',e.operation_index,'journal',jsonb_build_object(
  'seq',e.seq,'at',e.at,'xid',attempt.writer_xid::text,'entity_kind','o','entity_id',(e.object->'after'->>'id')::bigint,
  'entity_type',(e.object->'after'->>'type_id')::int,'ver',(e.object->'after'->>'ver')::bigint,
  'op',CASE e.event->>'operation' WHEN 'property' THEN 'update' ELSE 'metadata' END,'prop_id',(e.event->>'propertyId')::int,
  'old_value',NULL,'rev',(e.object->'after'->>'rev')::int,
  'new_value',truss.runtime_exact_wrapper('event',convert_to((e.payload||jsonb_build_object('mutationGroup',
   jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',d.amount::text,'orderedEventDigest',d.digest)))::text,'UTF8')),
  'origin',truss.runtime_exact_wrapper('origin',convert_to((e.payload->'origin')::text,'UTF8')))) ORDER BY e.seq),'[]') INTO journals
 FROM events e JOIN digests d ON d.operation_index=e.operation_index;
 SELECT coalesce(jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint),'[]') INTO expected FROM jsonb_array_elements(journals);
 WITH inserted AS (INSERT INTO truss.journal SELECT r.* FROM jsonb_array_elements(journals) j
  CROSS JOIN LATERAL jsonb_populate_record(NULL::truss.journal,j.value->'journal') r RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted) ORDER BY seq),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact batch update journals required' USING ERRCODE='55000';END IF;
 WITH journal_sets AS MATERIALIZED (
  SELECT (value->>'index')::int operation_index,jsonb_agg(value->'journal' ORDER BY (value->'journal'->>'seq')::bigint) rows
  FROM jsonb_array_elements(journals) GROUP BY (value->>'index')::int)
 SELECT coalesce(jsonb_agg(jsonb_build_object('attempt_id',attempt.id,'operation_index',(o.value->>'index')::int,
  'writer_xid',attempt.writer_xid::text,'object_id',(o.value->'after'->>'id')::bigint,'type_id',(o.value->'after'->>'type_id')::int,
  'before_object',o.value->'before','after_object',o.value->'after',
  'after_keys',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]') FROM truss.object_key_bucket k
   WHERE k.object_id=(o.value->'after'->>'id')::bigint AND k.type_id=(o.value->'after'->>'type_id')::int),
  'journal',j.rows) ORDER BY (o.value->>'index')::int),'[]') INTO transitions
 FROM jsonb_array_elements(objects) o JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int;
 WITH inserted AS (
  INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
  SELECT r.attempt_id,r.operation_index,r.writer_xid,r.object_id,r.type_id,r.before_object,r.after_object,r.after_keys,r.journal
  FROM jsonb_populate_recordset(NULL::truss.runtime_object_transition,transitions) r RETURNING *)
 SELECT coalesce(jsonb_agg(to_jsonb(inserted)-'transition_id' ORDER BY operation_index),'[]') INTO actual FROM inserted;
 IF actual IS DISTINCT FROM transitions THEN RAISE EXCEPTION 'exact batch update transitions required' USING ERRCODE='55000';END IF;
 WITH journal_sets AS MATERIALIZED (
  SELECT (value->>'index')::int operation_index,jsonb_agg(jsonb_build_object('sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',value->'journal'->>'seq')
    ORDER BY (value->'journal'->>'seq')::bigint) events FROM jsonb_array_elements(journals) GROUP BY (value->>'index')::int),
 slots AS (
  SELECT (o.value->>'index')::int operation_index,jsonb_build_object('operation','update_object',
   'outcome',CASE WHEN o.value->'changed'='true'::jsonb THEN 'changed' ELSE 'unchanged' END,'identity',o.value->'identity',
   'version',o.value->'after'->>'ver','events',coalesce(j.events,'[]'::jsonb)) result
  FROM jsonb_array_elements(objects) o LEFT JOIN journal_sets j ON j.operation_index=(o.value->>'index')::int)
 SELECT jsonb_object_agg(operation_index::text,result) INTO slot_results FROM slots;
 WITH updated AS (
  UPDATE truss.runtime_owned_operation p SET result=slot_results->p.operation_index::text
  WHERE p.attempt_id=selected_attempt AND p.result IS NULL AND slot_results ? p.operation_index::text
  RETURNING p.operation_index,p.result)
 SELECT count(*) INTO counted FROM updated;
 IF counted<>total THEN RAISE EXCEPTION 'complete sealed batch update slots required' USING ERRCODE='55000';END IF;
 UPDATE truss.runtime_object_attempt SET next_index=total WHERE id=selected_attempt AND next_index=0 AND NOT complete;
 IF NOT FOUND THEN RAISE EXCEPTION 'one batch update progress advance required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch(uuid) FROM PUBLIC;

-- Independent rootless value updates close their immutable source/result,
-- transition and journal correspondence as relations. Full final graph checks
-- remain in group_validate; row/journal constraint triggers remain independent.
CREATE FUNCTION truss.runtime_owned_update_batch_validate(attempt truss.runtime_object_attempt,input jsonb,history_dictionary jsonb,actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE initial_scope jsonb;last_plan jsonb;initial_nodes jsonb;initial_edges jsonb;final_nodes jsonb;before_nodes jsonb;
 states jsonb;event_dictionary jsonb;owner record;problem boolean;changed_count int;
BEGIN
 SELECT plan->'initialScope' INTO STRICT initial_scope FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=0;
 SELECT plan INTO STRICT last_plan FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id AND operation_index=attempt.next_index-1;
 IF (last_plan->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>(last_plan->>'catalogRevision')::int)
  OR attempt.aliases<>'[]'::jsonb OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'operations') o
   WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange')
  OR (SELECT count(DISTINCT plan->>'primary') FROM truss.runtime_owned_operation WHERE attempt_id=attempt.id)<>attempt.next_index
  OR EXISTS(SELECT 1 FROM jsonb_each(initial_scope->'nodes') n WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb
   OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb) THEN
  RAISE EXCEPTION 'independent original rootless update inventory required' USING ERRCODE='55000';END IF;
 WITH types AS MATERIALIZED (
  SELECT DISTINCT (value->>'type_id')::int type_id FROM jsonb_each(initial_scope->'nodes')),
 pins AS MATERIALIZED (
  SELECT t.type_id,d.* FROM types t CROSS JOIN LATERAL truss.runtime_owned_definition_metadata('type',t.type_id,NULL,(last_plan->>'catalogRevision')::int) d)
 SELECT coalesce(jsonb_object_agg('stored:'||n.key,jsonb_build_object('identity',jsonb_build_object(
  'id',n.value->>'id','typeId',n.value->>'type_id','definitionPin',p.definition_pin,
  'owner',jsonb_build_object('documentId',p.document_id,'moduleId',p.module_id)),
  'image',n.value-ARRAY['root_id','root_type','updated_at'],'root',NULL,'deleted',false)),'{}') INTO initial_nodes
 FROM jsonb_each(initial_scope->'nodes') n JOIN pins p ON p.type_id=(n.value->>'type_id')::int;
 WITH relations AS MATERIALIZED (
  SELECT r.*,truss.runtime_relationship_pin(r.rel_type_id) pin FROM truss.rel_def r JOIN
   (SELECT DISTINCT (value->>'rel_type_id')::int rel_type_id FROM jsonb_each(initial_scope->'edges')) e USING(rel_type_id))
 SELECT coalesce(jsonb_object_agg('stored:'||(e.value->>'rel_type_id')||':'||(e.value->>'id'),jsonb_build_object(
  'identity',jsonb_build_object('id',e.value->>'id','typeId',e.value->>'rel_type_id','definitionPin',r.pin,
   'owner',jsonb_build_object('documentId',r.document_id,'moduleId',r.module)),
  'image',e.value-ARRAY['source_id','source_type','target_id','target_type','order_key','updated_at'],
  'source','stored:'||(e.value->>'source_type')||':'||(e.value->>'source_id'),
  'target','stored:'||(e.value->>'target_type')||':'||(e.value->>'target_id'),
  'lifecycle',r.lifecycle,'deleted',false,'orderKey',CASE WHEN e.value->'order_key'='null'::jsonb
   THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',e.value->>'order_key') END)),'{}') INTO initial_edges
 FROM jsonb_each(initial_scope->'edges') e JOIN relations r ON r.rel_type_id=(e.value->>'rel_type_id')::int;
 SELECT jsonb_object_agg(p.plan->>'primary',p.plan->'afterNodes'->(p.plan->>'primary')),
  coalesce(jsonb_object_agg(p.plan->>'primary',p.plan->'afterNodes'->(p.plan->>'primary')) FILTER(WHERE p.operation_index<attempt.next_index-1),'{}')
 INTO states,before_nodes FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id;
 final_nodes:=initial_nodes||states;before_nodes:=initial_nodes||before_nodes;
 IF last_plan->'afterNodes' IS DISTINCT FROM final_nodes OR last_plan->'beforeNodes' IS DISTINCT FROM before_nodes
  OR last_plan->'beforeEdges' IS DISTINCT FROM initial_edges OR last_plan->'afterEdges' IS DISTINCT FROM initial_edges THEN
  RAISE EXCEPTION 'complete original independent update graph required' USING ERRCODE='55000';END IF;
 FOR owner IN SELECT DISTINCT t.type_id,t.document_id,t.module FROM truss.type_def t JOIN
  (SELECT DISTINCT (p.plan->'afterNodes'->(p.plan->>'primary')->'identity'->>'typeId')::int type_id
   FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id) members USING(type_id) LOOP
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,actor);
  IF NOT truss.runtime_object_values_readable_qualified(owner.type_id,actor) THEN
   RAISE EXCEPTION 'current original update value readers required' USING ERRCODE='42501';END IF;
 END LOOP;
 WITH frames AS MATERIALIZED (
  SELECT p.operation_index,p.plan,p.plan->'beforeNodes'->(p.plan->>'primary') prior,
   p.plan->'afterNodes'->(p.plan->>'primary') desired
  FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id),
 members AS MATERIALIZED (
  SELECT f.*,f.desired->'identity' identity,f.prior IS DISTINCT FROM f.desired changed,t.transition_id,t.writer_xid,t.object_id,t.type_id,
   t.before_object,t.after_object
  FROM frames f LEFT JOIN LATERAL (
   SELECT t.* FROM truss.runtime_object_transition t WHERE t.attempt_id=attempt.id AND t.operation_index=f.operation_index OFFSET 0) t ON true)
 SELECT EXISTS(SELECT 1 FROM members m WHERE
  m.plan->>'profile' IS DISTINCT FROM 'truss-owned-operation-plan/0.2'
  OR m.plan->'operationIndex' IS DISTINCT FROM to_jsonb(m.operation_index)
  OR m.plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
  OR m.plan->'operation' IS DISTINCT FROM input->'operations'->m.operation_index
  OR m.plan->>'actorName' IS DISTINCT FROM session_user::text
  OR m.plan->>'primary' IS DISTINCT FROM 'stored:'||(m.identity->>'typeId')||':'||(m.identity->>'id')
  OR m.identity IS DISTINCT FROM m.plan->'operation'->'target'->'identity'
  OR m.prior IS DISTINCT FROM initial_nodes->(m.plan->>'primary')
  OR m.desired->'identity' IS DISTINCT FROM m.prior->'identity'
  OR m.desired->'root' IS DISTINCT FROM 'null'::jsonb OR m.desired->'deleted' IS DISTINCT FROM 'false'::jsonb
  OR m.operation_index<attempt.next_index-1 AND
   (m.plan->'beforeNodes' IS DISTINCT FROM jsonb_build_object(m.plan->>'primary',m.prior)
    OR m.plan->'afterNodes' IS DISTINCT FROM jsonb_build_object(m.plan->>'primary',m.desired)
    OR m.plan->'beforeEdges' IS DISTINCT FROM '{}'::jsonb OR m.plan->'afterEdges' IS DISTINCT FROM '{}'::jsonb)
  OR CASE WHEN m.changed THEN m.transition_id IS NULL OR m.writer_xid IS DISTINCT FROM attempt.writer_xid
   OR m.object_id::text IS DISTINCT FROM m.identity->>'id' OR m.type_id::text IS DISTINCT FROM m.identity->>'typeId'
   OR m.before_object IS DISTINCT FROM initial_scope->'nodes'->((m.identity->>'typeId')||':'||(m.identity->>'id'))
   OR m.after_object IS NULL OR m.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM
    ((m.desired->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',m.object_id,'root_id',NULL,'root_type',NULL)
   OR m.after_object->'created_at' IS DISTINCT FROM m.before_object->'created_at'
   OR (m.after_object->>'ver')::bigint IS DISTINCT FROM (m.before_object->>'ver')::bigint+1
   ELSE m.transition_id IS NOT NULL END) INTO problem;
 IF problem THEN RAISE EXCEPTION 'original batch update plan and transition correspondence required' USING ERRCODE='55000';END IF;
 SELECT count(*) INTO changed_count FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id
  AND p.plan->'beforeNodes'->(p.plan->>'primary') IS DISTINCT FROM p.plan->'afterNodes'->(p.plan->>'primary');
 IF (SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=attempt.id)<>changed_count
  OR EXISTS(SELECT 1 FROM truss.runtime_edge_transition WHERE attempt_id=attempt.id) THEN
  RAISE EXCEPTION 'complete original batch update effect inventory required' USING ERRCODE='55000';END IF;
 -- Reconstruct semantic property/metadata events from the original physical
 -- transition and independently compiled source dictionary. Never trust the
 -- journal payload to supply its own meaning or group digest.
 WITH members AS MATERIALIZED (
  SELECT t.operation_index,t.object_id,t.type_id,t.before_object,t.after_object,t.journal,
   p.plan->>'catalogRevision' capture_revision,p.plan->>'actorName' actor_name,
   p.plan->'afterNodes'->(p.plan->>'primary')->'identity' identity
  FROM truss.runtime_object_transition t CROSS JOIN LATERAL (
   SELECT p.plan FROM truss.runtime_owned_operation p WHERE p.attempt_id=t.attempt_id AND p.operation_index=t.operation_index OFFSET 0) p
  WHERE t.attempt_id=attempt.id),
 semantics AS MATERIALIZED (
  SELECT m.operation_index,m.object_id,m.type_id,m.after_object->>'ver' expected_version,m.capture_revision,m.actor_name,m.identity,
   jsonb_array_length(m.journal) journal_count,s.event_index,s.event_count,m.journal->s.event_index::int entry,s.event
  FROM members m CROSS JOIN LATERAL (
   SELECT e.event,row_number() OVER(ORDER BY e.metadata,e.ordinal)-1 event_index,count(*) OVER() event_count FROM (
    SELECT false metadata,p.prop_id::bigint ordinal,jsonb_build_object('operation','property','propertyId',p.prop_id::text,
     'definitionPin',coalesce(history_dictionary->jsonb_build_array((m.after_object->>'rev')::int,m.type_id)::text->'propertyPins'->>p.prop_id::text,
      (SELECT d.definition_pin FROM truss.runtime_owned_definition_metadata('property',m.type_id,p.prop_id,m.capture_revision::int) d)),
     'before',CASE WHEN m.before_object->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',m.before_object->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END,
     'after',CASE WHEN m.after_object->'props' ? p.prop_id::text THEN jsonb_build_object('present',true,'value',m.after_object->'props'->p.prop_id::text) ELSE '{"present":false}'::jsonb END) event
    FROM truss.prop_def p WHERE p.type_id=m.type_id AND p.since_rev<=m.capture_revision::int
     AND (p.retired_rev IS NULL OR p.retired_rev>m.capture_revision::int)
     AND m.before_object->'props'->p.prop_id::text IS DISTINCT FROM m.after_object->'props'->p.prop_id::text
    UNION ALL SELECT true,0::bigint,jsonb_build_object('operation','metadata',
     'before',truss.runtime_owned_history_record_in_metadata(m.before_object,m.identity,history_dictionary->jsonb_build_array((m.before_object->>'rev')::int,m.type_id)::text),
     'after',truss.runtime_owned_history_record_in_metadata(m.after_object,m.identity,history_dictionary->jsonb_build_array((m.after_object->>'rev')::int,m.type_id)::text))
   ) e) s),
 payloads AS MATERIALIZED (
  SELECT s.*,s.event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',attempt.context->>'sourceEpoch',
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,
   'seq',s.entry->>'seq','identity',s.identity,'eventVersion',s.expected_version,
   'eventCatalogRevision',s.capture_revision,'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',s.actor_name)) payload
  FROM semantics s),
 digests AS MATERIALIZED (
  SELECT p.*,CASE WHEN event_index=0 THEN encode(sha256(convert_to((jsonb_agg(payload) OVER (
   PARTITION BY operation_index ORDER BY event_index ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING))::text,'UTF8')),'hex') END digest
  FROM payloads p),
 complete AS MATERIALIZED (
  SELECT d.*,d.payload||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0',
   'eventCount',d.event_count::text,'orderedEventDigest',first_value(digest) OVER(PARTITION BY operation_index ORDER BY event_index))) expected_payload
  FROM digests d)
 SELECT EXISTS(SELECT 1 FROM complete p LEFT JOIN LATERAL (
  SELECT j.* FROM truss.journal j WHERE j.seq=(p.entry->>'seq')::bigint AND j.at=(p.entry->>'at')::timestamptz OFFSET 0) j ON true WHERE
  p.journal_count IS DISTINCT FROM p.event_count OR to_jsonb(j) IS DISTINCT FROM p.entry
  OR p.entry IS DISTINCT FROM jsonb_build_object('seq',(p.entry->>'seq')::bigint,'at',p.entry->'at','xid',attempt.writer_xid::text,
   'entity_kind','o','entity_id',p.object_id,'entity_type',p.type_id,'ver',p.expected_version::bigint,
   'op',CASE p.expected_payload->>'operation' WHEN 'property' THEN 'update' ELSE 'metadata' END,
   'prop_id',(p.expected_payload->>'propertyId')::int,'old_value',NULL,'rev',p.capture_revision::int,
   'new_value',truss.runtime_exact_wrapper('event',convert_to(p.expected_payload::text,'UTF8')),
   'origin',truss.runtime_exact_wrapper('origin',convert_to((p.payload->'origin')::text,'UTF8')))) INTO problem;
 IF problem THEN RAISE EXCEPTION 'exact original batch update journals required' USING ERRCODE='55000';END IF;
 -- A local event map avoids joining two materialized batch relations whose
 -- row estimates can collapse to one after ANALYZE of retained attempt history.
 WITH event_sets AS MATERIALIZED (
  SELECT t.operation_index,jsonb_agg(jsonb_build_object('sourceEpoch',attempt.context->>'sourceEpoch',
   'historyProfile','truss-native-owned-mutation/0.1','xid',attempt.writer_xid::text,'seq',j.value->>'seq')
    ORDER BY (j.value->>'seq')::bigint) events
  FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
  WHERE t.attempt_id=attempt.id GROUP BY t.operation_index)
 SELECT coalesce(jsonb_object_agg(operation_index::text,events),'{}'::jsonb) INTO event_dictionary FROM event_sets;
 SELECT EXISTS(SELECT 1 FROM truss.runtime_owned_operation p
  WHERE p.attempt_id=attempt.id AND p.result IS DISTINCT FROM jsonb_build_object('operation','update_object',
   'outcome',CASE WHEN p.plan->'beforeNodes'->(p.plan->>'primary') IS DISTINCT FROM p.plan->'afterNodes'->(p.plan->>'primary') THEN 'changed' ELSE 'unchanged' END,
   'identity',p.plan->'afterNodes'->(p.plan->>'primary')->'identity',
   'version',p.plan->'afterNodes'->(p.plan->>'primary')->'image'->>'ver','events',coalesce(event_dictionary->p.operation_index::text,'[]'::jsonb))) INTO problem;
 IF problem THEN RAISE EXCEPTION 'exact original batch update results required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_update_batch_validate(truss.runtime_object_attempt,jsonb,jsonb,oid) FROM PUBLIC;

-- Close the original plan against every actual effect. The final image check is
-- performed at group finish; commit rechecks custody and authority after later
-- groups may legitimately have superseded those images in the same transaction.
CREATE FUNCTION truss.runtime_owned_group_validate(selected_attempt uuid,check_final boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;plan jsonb;last_plan jsonb;initial_scope jsonb;
 operations jsonb;before_nodes jsonb;after_nodes jsonb;before_edges jsonb;after_edges jsonb;
 operation jsonb;result jsonb;entry record;owner record;transition_id bigint;identity jsonb;actual jsonb;
 reference text;mode text;expected_objects int;expected_edges int;events jsonb;deleted jsonb;aliases jsonb:='[]';
 primary_before jsonb;primary_after jsonb;expected_outcome text;expected_version text;
 node_order text[];projection jsonb;local_owned jsonb;root_reference text;index int;current_actor oid;live_edges jsonb;final_nodes jsonb;final_edges jsonb;final_problem text;
 history_dictionary jsonb:='{}';historical_basis jsonb;historical_revision int;history_group record;history_basis jsonb;
 history_property truss.prop_def%ROWTYPE;history_pin record;history_pins jsonb;history_order jsonb;history_key text;history_type_pin text;sealed record;
 independent_updates boolean;independent_endpoints boolean;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 operations:=input->'operations';
 current_actor:=truss.runtime_person(false);
 IF check_final IS NULL OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
  OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
  OR attempt.next_index<>jsonb_array_length(operations) OR jsonb_array_length(attempt.results)<>attempt.next_index
  OR (SELECT count(*) FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt)<>attempt.next_index THEN
  RAISE EXCEPTION 'complete original owned group required' USING ERRCODE='55000';END IF;
 -- Both finish and mandatory commit close the retained arrays against every
 -- immutable result slot, including no-ops and aggregate cascade results.
 SELECT coalesce(jsonb_agg(p.result ORDER BY p.operation_index),'[]'::jsonb) results,
  coalesce(jsonb_agg(jsonb_build_object('alias',p.plan->'operation'->>'alias','identity',p.result->'identity') ORDER BY p.operation_index)
   FILTER(WHERE (p.plan->'operation') ? 'alias'),'[]'::jsonb) aliases,
  array_agg(p.operation_index ORDER BY p.operation_index) ordinals,
  count(*) FILTER(WHERE p.result IS NULL) missing,bool_and(p.writer_xid=attempt.writer_xid) writer_matches
 INTO sealed FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt;
 IF sealed.missing<>0 OR sealed.writer_matches IS DISTINCT FROM true
  OR sealed.ordinals IS DISTINCT FROM ARRAY(SELECT generate_series(0,attempt.next_index-1))
  OR sealed.results IS DISTINCT FROM attempt.results OR sealed.aliases IS DISTINCT FROM attempt.aliases THEN
  RAISE EXCEPTION 'exact complete retained owned result slots required' USING ERRCODE='55000';END IF;
 -- Compile source metadata for created and changed object images. Each
 -- independent settlement invocation resolves its own historical source cut.
 FOR history_group IN
  WITH frames AS MATERIALIZED (
   SELECT o.plan->'beforeNodes' before_nodes,o.plan->'afterNodes' after_nodes
   FROM truss.runtime_owned_operation o WHERE o.attempt_id=selected_attempt),
  changes AS MATERIALIZED (
   SELECT f.before_nodes->n.key before_state,n.value after_state
   FROM frames f CROSS JOIN LATERAL jsonb_each(f.after_nodes) n
   WHERE f.before_nodes->n.key IS NULL OR (f.before_nodes->n.key->'deleted'='false'::jsonb
    AND n.value IS DISTINCT FROM f.before_nodes->n.key)),
  images AS MATERIALIZED (
   SELECT member.state->'image' image FROM changes c
   CROSS JOIN LATERAL (VALUES(c.before_state),(c.after_state)) member(state)
   WHERE member.state->'deleted'='false'::jsonb)
  SELECT (image->>'rev')::int revision,(image->>'type_id')::int type_id,
   coalesce(array_agg(DISTINCT property_names.name) FILTER(WHERE property_names.name IS NOT NULL),'{}'::text[]) present_names
  FROM images LEFT JOIN LATERAL jsonb_object_keys(image->'props') property_names(name) ON true
  GROUP BY (image->>'rev')::int,(image->>'type_id')::int
  ORDER BY (image->>'rev')::int,(image->>'type_id')::int
 LOOP
  SELECT CASE WHEN history_group.revision=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>history_group.revision)
  THEN jsonb_build_object(
   'type_def',(SELECT coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) FROM truss.type_def t WHERE t.type_id=history_group.type_id),
   'prop_def',(SELECT coalesce(jsonb_agg(to_jsonb(p)),'[]'::jsonb) FROM truss.prop_def p WHERE p.type_id=history_group.type_id)) END INTO history_basis;
  IF history_basis IS NULL THEN
   IF historical_revision IS DISTINCT FROM history_group.revision THEN
    historical_basis:=truss.catalog_all_expected_records(history_group.revision);
    historical_revision:=history_group.revision;
   END IF;
   history_basis:=historical_basis;
  END IF;
  SELECT * INTO STRICT history_pin FROM truss.runtime_owned_definition_metadata_in_basis('type',history_group.type_id,NULL,history_group.revision,history_basis);
  history_type_pin:=history_pin.definition_pin;
  history_pins:='{}';history_order:='[]';
  FOR history_property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,history_basis->'prop_def') p
   WHERE p.type_id=history_group.type_id ORDER BY prop_id LOOP
   IF history_property.prop_id::text=ANY(history_group.present_names) THEN
    history_order:=history_order||jsonb_build_array(history_property.prop_id::text);
    SELECT * INTO STRICT history_pin FROM truss.runtime_owned_definition_metadata_in_basis('property',history_property.type_id,history_property.prop_id,history_group.revision,history_basis);
    history_pins:=history_pins||jsonb_build_object(history_property.prop_id::text,history_pin.definition_pin);
    IF NOT truss.runtime_can_read_qualified(history_property.definition_document_id,history_property.declaration_module,current_actor)
     OR history_property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable_qualified(history_property.item,current_actor) IS NOT TRUE THEN
     RAISE EXCEPTION 'current historical property and item readers required' USING ERRCODE='42501';END IF;
   END IF;
  END LOOP;
  history_key:=jsonb_build_array(history_group.revision,history_group.type_id)::text;
  history_dictionary:=history_dictionary||jsonb_build_object(history_key,jsonb_build_object(
   'typeId',history_group.type_id::text,'revision',history_group.revision::text,'typePin',history_type_pin,
   'propertyOrder',history_order,'propertyPins',history_pins));
 END LOOP;
 -- The closed independent-create shape has a set-based reconstruction.
 -- Mixed/owned operations keep the general ordered graph validator.
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
  WHERE o.value->>'operation' IS DISTINCT FROM 'create_object'
   OR o.value->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb) THEN
  PERFORM truss.runtime_owned_create_batch_validate(attempt,input,history_dictionary,check_final,current_actor);
  RETURN;
 END IF;
 independent_updates:=NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
  WHERE o.value->>'operation' IS DISTINCT FROM 'update_object' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange')
  AND (SELECT count(DISTINCT p.plan->>'primary') FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt)=attempt.next_index
  AND EXISTS(SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=0
   AND (p.plan->>'catalogRevision')::int=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>(p.plan->>'catalogRevision')::int))
  AND NOT EXISTS(SELECT 1 FROM truss.runtime_owned_operation p CROSS JOIN LATERAL jsonb_each(p.plan->'initialScope'->'nodes') n
   WHERE p.attempt_id=selected_attempt AND p.operation_index=0 AND
    (n.value->'root_id' IS DISTINCT FROM 'null'::jsonb OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb));
 IF independent_updates THEN
  PERFORM truss.runtime_owned_update_batch_validate(attempt,input,history_dictionary,current_actor);
  SELECT p.plan->'initialScope' INTO STRICT initial_scope FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=0;
  SELECT p.plan INTO STRICT last_plan FROM truss.runtime_owned_operation p WHERE p.attempt_id=selected_attempt AND p.operation_index=attempt.next_index-1;
 ELSE
 FOR index IN 0..attempt.next_index-1 LOOP
  plan:=truss.runtime_owned_plan(selected_attempt,index);operation:=plan->'operation';
  IF operation IS DISTINCT FROM jsonb_extract_path(operations,index::text)
   OR plan->'mutationProfile' IS DISTINCT FROM input->'mutationProfile' THEN
   RAISE EXCEPTION 'original owned operation source correspondence required' USING ERRCODE='55000';END IF;
  before_nodes:=plan->'beforeNodes';after_nodes:=plan->'afterNodes';
  before_edges:=plan->'beforeEdges';after_edges:=plan->'afterEdges';
  mode:=operation->>'operation';result:=attempt.results->index;
  IF index=0 THEN initial_scope:=plan->'initialScope';END IF;
  expected_objects:=0;expected_edges:=0;
  FOR entry IN SELECT key,value FROM jsonb_each(after_nodes) n WHERE n.value IS DISTINCT FROM jsonb_extract_path(before_nodes,n.key)
   AND (jsonb_extract_path(before_nodes,n.key) IS NULL OR jsonb_extract_path(before_nodes,n.key)->'deleted'='false'::jsonb) LOOP
   identity:=truss.runtime_owned_identity(selected_attempt,index,entry.key,'object',plan,attempt);
   SELECT t.transition_id INTO STRICT transition_id FROM truss.runtime_object_transition t WHERE t.attempt_id=selected_attempt
    AND t.operation_index=index AND t.object_id=(identity->>'id')::bigint AND t.type_id=(identity->>'typeId')::int;
   PERFORM truss.runtime_owned_object_transition_validate_qualified(transition_id,false,current_actor,input,attempt.input_bytes,attempt,history_dictionary);expected_objects:=expected_objects+1;
  END LOOP;
  FOR entry IN SELECT key,value FROM jsonb_each(after_edges) e WHERE
   (e.value IS DISTINCT FROM jsonb_extract_path(before_edges,e.key) OR e.key=plan->>'primary' AND mode='update_edge')
   AND (jsonb_extract_path(before_edges,e.key) IS NULL OR jsonb_extract_path(before_edges,e.key)->'deleted'='false'::jsonb) LOOP
   identity:=truss.runtime_owned_identity(selected_attempt,index,entry.key,'edge',plan,attempt);
   SELECT t.transition_id INTO STRICT transition_id FROM truss.runtime_edge_transition t WHERE t.attempt_id=selected_attempt
    AND t.operation_index=index AND t.edge_id=(identity->>'id')::bigint AND t.rel_type_id=(identity->>'typeId')::int;
   PERFORM truss.runtime_owned_edge_transition_validate_qualified(transition_id,false,current_actor,input,attempt.input_bytes,attempt);expected_edges:=expected_edges+1;
  END LOOP;
  IF expected_objects<>(SELECT count(*) FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt AND operation_index=index)
   OR expected_edges<>(SELECT count(*) FROM truss.runtime_edge_transition WHERE attempt_id=selected_attempt AND operation_index=index) THEN
   RAISE EXCEPTION 'complete original effect inventory required' USING ERRCODE='55000';END IF;
  identity:=truss.runtime_owned_identity(selected_attempt,index,plan->>'primary',CASE WHEN mode LIKE '%object' THEN 'object' ELSE 'edge' END,plan,attempt);
  IF result->'identity' IS DISTINCT FROM identity OR result->>'operation' IS DISTINCT FROM mode THEN
   RAISE EXCEPTION 'original primary result identity required' USING ERRCODE='55000';END IF;
  primary_before:=jsonb_extract_path(plan,CASE WHEN mode LIKE '%object' THEN 'beforeNodes' ELSE 'beforeEdges' END,plan->>'primary');
  primary_after:=jsonb_extract_path(plan,CASE WHEN mode LIKE '%object' THEN 'afterNodes' ELSE 'afterEdges' END,plan->>'primary');
  expected_outcome:=CASE WHEN mode LIKE 'create_%' THEN 'created' WHEN mode LIKE 'delete_%' THEN 'deleted'
   WHEN primary_before IS NOT DISTINCT FROM primary_after THEN 'unchanged' ELSE 'changed' END;
  expected_version:=CASE WHEN mode LIKE 'delete_%' THEN ((primary_before->'image'->>'ver')::bigint+1)::text ELSE primary_after->'image'->>'ver' END;
  IF result->>'outcome' IS DISTINCT FROM expected_outcome
   OR result->>(CASE WHEN mode LIKE 'delete_%' THEN 'deletionVersion' ELSE 'version' END) IS DISTINCT FROM expected_version THEN
   RAISE EXCEPTION 'original primary outcome and version required' USING ERRCODE='55000';END IF;
  IF mode LIKE 'delete_%' THEN
   SELECT coalesce(jsonb_agg(v ORDER BY v::text COLLATE "C"),'[]'::jsonb) INTO deleted FROM (
    SELECT jsonb_build_object('identity',truss.runtime_owned_identity(selected_attempt,index,p.key,'object',plan,attempt),
     'deletionVersion',((p.value->'image'->>'ver')::bigint+1)::text) v
    FROM jsonb_each(before_nodes) p WHERE p.value->'deleted'='false'::jsonb AND jsonb_extract_path(after_nodes,p.key)->'deleted'='true'::jsonb
    UNION ALL SELECT jsonb_build_object('identity',truss.runtime_owned_identity(selected_attempt,index,p.key,'edge',plan,attempt),
     'deletionVersion',((p.value->'image'->>'ver')::bigint+1)::text)
    FROM jsonb_each(before_edges) p WHERE p.value->'deleted'='false'::jsonb AND plan->'afterEdges'->p.key->'deleted'='true'::jsonb) members;
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
 END IF;
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
 -- Resolve each final member once. The private projection carries its exact
 -- checked state; genuine create identities still check the original result and
 -- creation-index plan independently inside runtime_owned_identity.
 WITH resolved AS MATERIALIZED (
  SELECT n.reference,n.ordinal,CASE WHEN n.reference='stored:'||(n.state->'identity'->>'typeId')||':'||(n.state->'identity'->>'id')
   THEN n.state->'identity' ELSE truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,n.reference,'object',
   jsonb_build_object('catalogRevision',last_plan->'catalogRevision','afterNodes',jsonb_build_object(n.reference,n.state)),attempt) END identity
  FROM jsonb_each(last_plan->'afterNodes') WITH ORDINALITY n(reference,state,ordinal))
 SELECT coalesce(jsonb_object_agg(resolved.reference,resolved.identity ORDER BY resolved.ordinal),'{}'::jsonb) INTO final_nodes FROM resolved;
 WITH resolved AS MATERIALIZED (
  SELECT e.reference,e.ordinal,CASE WHEN e.reference='stored:'||(e.state->'identity'->>'typeId')||':'||(e.state->'identity'->>'id')
   THEN e.state->'identity' ELSE truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,e.reference,'edge',
   jsonb_build_object('catalogRevision',last_plan->'catalogRevision','afterEdges',jsonb_build_object(e.reference,e.state)),attempt) END identity
  FROM jsonb_each(last_plan->'afterEdges') WITH ORDINALITY e(reference,state,ordinal))
 SELECT coalesce(jsonb_object_agg(resolved.reference,resolved.identity ORDER BY resolved.ordinal),'{}'::jsonb) INTO final_edges FROM resolved;
 SELECT coalesce(jsonb_object_agg(jsonb_build_array(e.value->>'typeId',e.value->>'id')::text,true),'{}'::jsonb)
  INTO live_edges FROM jsonb_each(final_edges) e WHERE jsonb_extract_path(last_plan,'afterEdges',e.key,'deleted')='false'::jsonb;
 -- A lean endpoint scope intentionally omits unrelated independent edges.
 -- Recheck its closed operation shape and ownership conditions independently.
 independent_endpoints:=initial_scope->'independentEndpointScope'='true'::jsonb
  AND NOT EXISTS(SELECT 1 FROM truss.rel_def WHERE retired_rev IS NULL AND lifecycle='owned')
  AND (NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
   WHERE o.value->>'operation' IS DISTINCT FROM 'create_edge'
    OR o.value->'source'->>'state' IS DISTINCT FROM 'stored' OR o.value->'target'->>'state' IS DISTINCT FROM 'stored')
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(operations) o
    WHERE o.value->>'operation' IS DISTINCT FROM 'update_object'
     OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange'))
  AND NOT EXISTS(SELECT 1 FROM jsonb_each(initial_scope->'nodes') n
   WHERE n.value->'root_id' IS DISTINCT FROM 'null'::jsonb OR n.value->'root_type' IS DISTINCT FROM 'null'::jsonb);
 -- Preserve node order and image-before-incident refusal priority. Deleted
 -- members remain in the identity and incident inventories with a NULL image.
 WITH members AS MATERIALIZED (
  SELECT n.reference,n.state,n.ordinal,final_nodes->n.reference identity,
   CASE WHEN n.state->'deleted' IS DISTINCT FROM 'true'::jsonb AND n.state->>'root' IS NOT NULL
    THEN coalesce(final_nodes->(n.state->>'root'),
     truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,n.state->>'root','object',last_plan,attempt)) END root_identity
  FROM jsonb_each(last_plan->'afterNodes') WITH ORDINALITY n(reference,state,ordinal)),
 problems AS MATERIALIZED (
  SELECT n.ordinal,CASE WHEN (to_jsonb(o)-ARRAY['created_at','updated_at']) IS DISTINCT FROM
   CASE WHEN n.state->'deleted'='true'::jsonb THEN NULL ELSE
    ((n.state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(n.identity->>'id')::bigint,
     'root_id',(n.root_identity->>'id')::bigint,'root_type',(n.root_identity->>'typeId')::int) END THEN 'object'
   WHEN (EXISTS(SELECT 1 FROM truss.edge e WHERE
    e.source_id=(n.identity->>'id')::bigint AND e.source_type=(n.identity->>'typeId')::int
    AND NOT (live_edges ? jsonb_build_array(e.rel_type_id::text,e.id::text)::text)
    AND (NOT coalesce(independent_endpoints,false) OR to_jsonb(e) IS DISTINCT FROM
     (SELECT t.after_edge FROM truss.runtime_edge_transition t WHERE t.edge_id=e.id AND t.rel_type_id=e.rel_type_id
      ORDER BY t.transition_id DESC LIMIT 1)))
   OR EXISTS(SELECT 1 FROM truss.edge e WHERE
    e.target_id=(n.identity->>'id')::bigint AND e.target_type=(n.identity->>'typeId')::int
    AND NOT (live_edges ? jsonb_build_array(e.rel_type_id::text,e.id::text)::text)
    AND (NOT coalesce(independent_endpoints,false) OR to_jsonb(e) IS DISTINCT FROM
     (SELECT t.after_edge FROM truss.runtime_edge_transition t WHERE t.edge_id=e.id AND t.rel_type_id=e.rel_type_id
      ORDER BY t.transition_id DESC LIMIT 1)))) THEN 'incident' END problem
  FROM members n LEFT JOIN truss.object o ON o.id=(n.identity->>'id')::bigint AND o.type_id=(n.identity->>'typeId')::int)
 SELECT problem INTO final_problem FROM problems WHERE problem IS NOT NULL ORDER BY ordinal LIMIT 1;
 IF final_problem='object' THEN RAISE EXCEPTION 'actual final owned object required' USING ERRCODE='55000';END IF;
 IF final_problem='incident' THEN RAISE EXCEPTION 'complete final incident edge inventory required' USING ERRCODE='55000';END IF;
 WITH members AS MATERIALIZED (
  SELECT e.state,e.ordinal,final_edges->e.reference identity,
   CASE WHEN e.state->'deleted' IS DISTINCT FROM 'true'::jsonb THEN coalesce(final_nodes->(e.state->>'source'),
    truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,e.state->>'source','object',last_plan,attempt)) END source_identity,
   CASE WHEN e.state->'deleted' IS DISTINCT FROM 'true'::jsonb THEN coalesce(final_nodes->(e.state->>'target'),
    truss.runtime_owned_identity(selected_attempt,attempt.next_index-1,e.state->>'target','object',last_plan,attempt)) END target_identity
  FROM jsonb_each(last_plan->'afterEdges') WITH ORDINALITY e(reference,state,ordinal))
 SELECT 'edge' INTO final_problem FROM members m LEFT JOIN truss.edge e
  ON e.id=(m.identity->>'id')::bigint AND e.rel_type_id=(m.identity->>'typeId')::int
 WHERE (to_jsonb(e)-ARRAY['created_at','updated_at']) IS DISTINCT FROM
  CASE WHEN m.state->'deleted'='true'::jsonb THEN NULL ELSE
   ((m.state->'image')-ARRAY['created_at','updated_at'])||jsonb_build_object('id',(m.identity->>'id')::bigint,
    'source_id',(m.source_identity->>'id')::bigint,'source_type',(m.source_identity->>'typeId')::int,
    'target_id',(m.target_identity->>'id')::bigint,'target_type',(m.target_identity->>'typeId')::int,
    'order_key',m.state->'orderKey'->>'text') END ORDER BY m.ordinal LIMIT 1;
 IF final_problem='edge' THEN RAISE EXCEPTION 'actual final owned edge required' USING ERRCODE='55000';END IF;
 SELECT coalesce(array_agg(key ORDER BY key COLLATE "C"),'{}'::text[]) INTO node_order FROM jsonb_each(last_plan->'afterNodes') WHERE value->'deleted'='false'::jsonb;
 local_owned:=truss.runtime_owned_local_edges(last_plan->'afterEdges',node_order,'{}'::text[],true);
 projection:=truss.owned_forest_projection(cardinality(node_order),local_owned);
 FOR entry IN SELECT value FROM jsonb_array_elements(projection) LOOP
  reference:=node_order[(entry.value->>'node')::int+1];
  root_reference:=CASE WHEN entry.value->'root'='null'::jsonb THEN NULL ELSE node_order[(entry.value->>'root')::int+1] END;
  IF jsonb_extract_path(last_plan,'afterNodes',reference,'root') IS DISTINCT FROM coalesce(to_jsonb(root_reference),'null'::jsonb) THEN
   RAISE EXCEPTION 'actual final forest and explicit root correspondence required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_group_validate(uuid,boolean) FROM PUBLIC;

-- Owned-provider history implementation; installed with the complete provider.
-- Root interpretation comes from the original image revision, never a live root.
CREATE FUNCTION truss.runtime_object_ownership_at(object_image jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE revision int;root_id bigint;root_type int;pin record;
BEGIN
 IF jsonb_typeof(object_image) IS DISTINCT FROM 'object'
  OR NOT (object_image ?& ARRAY['id','type_id','root_id','root_type','rev']) THEN
  RAISE EXCEPTION 'original complete object root fields required' USING ERRCODE='55000';END IF;
 IF (object_image->'root_id'='null'::jsonb) IS DISTINCT FROM (object_image->'root_type'='null'::jsonb) THEN
  RAISE EXCEPTION 'complete original root pair required' USING ERRCODE='55000';END IF;
 IF object_image->'root_id'='null'::jsonb THEN RETURN '{"state":"rootless"}'::jsonb;END IF;
 revision:=(object_image->>'rev')::int;root_id:=(object_image->>'root_id')::bigint;root_type:=(object_image->>'root_type')::int;
 IF revision IS NULL OR revision<1 OR root_id IS NULL OR root_id<1 OR root_type IS NULL OR root_type<1
  OR root_id=(object_image->>'id')::bigint AND root_type=(object_image->>'type_id')::int THEN
  RAISE EXCEPTION 'original aggregate root identity required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',root_type,NULL,revision);
 RETURN jsonb_build_object('state','owned','root',jsonb_build_object('id',root_id::text,
  'typeId',root_type::text,'definitionPin',pin.definition_pin,
  'owner',jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id)));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_ownership_at(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_ownership_qualified(image jsonb,qualified_actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE ownership jsonb:=image->'ownership';root jsonb;pin record;revision int;
BEGIN
 IF ownership='{"state":"rootless"}'::jsonb THEN RETURN;END IF;
 IF ownership->>'state' IS DISTINCT FROM 'owned' OR ownership-ARRAY['state','root']<>'{}'::jsonb
  OR jsonb_typeof(ownership->'root') IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original explicit ownership selection required' USING ERRCODE='55000';END IF;
 root:=ownership->'root';revision:=(image->>'catalogRevision')::int;
 IF root-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb
  OR jsonb_typeof(root->'id') IS DISTINCT FROM 'string' OR root->>'id' !~ '^[1-9][0-9]{0,18}$'
  OR length(root->>'id')=19 AND (root->>'id') COLLATE "C">'9223372036854775807'
  OR jsonb_typeof(root->'typeId') IS DISTINCT FROM 'string' OR root->>'typeId' !~ '^[1-9][0-9]{0,9}$'
  OR (root->>'typeId')::bigint>2147483647
  OR root->>'id'=image->'identity'->>'id' AND root->>'typeId'=image->'identity'->>'typeId'
  OR revision IS NULL OR revision<1 THEN
  RAISE EXCEPTION 'exact historical aggregate root required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(root->>'typeId')::int,NULL,revision);
 IF root->>'definitionPin' IS DISTINCT FROM pin.definition_pin
  OR root->'owner' IS DISTINCT FROM jsonb_build_object('documentId',pin.document_id,'moduleId',pin.module_id) THEN
  RAISE EXCEPTION 'original aggregate root interpretation required' USING ERRCODE='55000';END IF;
 IF NOT truss.runtime_can_read_qualified(pin.document_id,pin.module_id,qualified_actor) THEN
  RAISE EXCEPTION 'current historical root reader required' USING ERRCODE='42501';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_ownership_qualified(jsonb,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_history_ownership(image jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_history_ownership_qualified(image,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_history_ownership(jsonb) FROM PUBLIC;
