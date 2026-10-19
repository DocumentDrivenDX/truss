-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Uninstalled observation component. One invocation uses one statement snapshot.
-- No locks, authority issuance or effects. Reobserve after the graph-write gate;
-- the executor must refuse newly required earlier guards before performing writes.
CREATE FUNCTION truss.owned_graph_scope(seeds jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE node_keys text[]:='{}';edge_keys text[]:='{}';boundary_keys text[]:='{}';owned_edge_order text[]:='{}';
 nodes jsonb:='{}';node_images jsonb[]:='{}';edges jsonb:='{}';edge_images jsonb[]:='{}';boundary jsonb:='{}';boundary_images jsonb[]:='{}';
 types jsonb:='{}';type_images jsonb[]:='{}';relations jsonb:='{}';relation_images jsonb[]:='{}';node_positions jsonb;
 entry jsonb;image jsonb;relation_image jsonb;witness jsonb;definition jsonb;
 node_key text;edge_key text;root_key text;selected_type int;selected_id bigint;
 selected_node int:=1;projection jsonb;local_edges jsonb:='[]';seed_ordinal int:=0;duplicate_seed_ordinal bigint;
 result_json jsonb;used_bytes bigint:=0;head int;
BEGIN
 IF jsonb_typeof(seeds) IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'explicit typed scope seeds required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(seeds) NOT BETWEEN 0 AND 1024 OR octet_length(convert_to(seeds::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'bounded scope seeds required' USING ERRCODE='54000';END IF;
 SELECT min(ordinal) INTO duplicate_seed_ordinal FROM (
  SELECT ordinal,row_number() OVER(PARTITION BY value->>'typeId',value->>'id' ORDER BY ordinal) occurrence
  FROM jsonb_array_elements(seeds) WITH ORDINALITY s(value,ordinal)) repeated WHERE occurrence>1;
 FOR entry IN SELECT value FROM jsonb_array_elements(seeds) WITH ORDINALITY s(value,ordinal) ORDER BY ordinal LOOP
  seed_ordinal:=seed_ordinal+1;
  IF jsonb_typeof(entry) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'typed scope seed required' USING ERRCODE='22023';END IF;
  IF entry-ARRAY['typeId','id']<>'{}'::jsonb OR jsonb_typeof(entry->'typeId') IS DISTINCT FROM 'string'
   OR jsonb_typeof(entry->'id') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'exact typed seed fields required' USING ERRCODE='22023';END IF;
  IF entry->>'typeId' !~ '^[1-9][0-9]{0,9}$' OR entry->>'id' !~ '^[1-9][0-9]{0,18}$' THEN
   RAISE EXCEPTION 'positive exact native seed identities required' USING ERRCODE='22023';END IF;
  IF (entry->>'typeId')::bigint>2147483647 OR (entry->>'id')::numeric>9223372036854775807 THEN
   RAISE EXCEPTION 'native seed identity range exceeded' USING ERRCODE='22023';END IF;
  IF seed_ordinal=duplicate_seed_ordinal THEN RAISE EXCEPTION 'duplicate scope seed' USING ERRCODE='22023';END IF;
 END LOOP;
 SELECT rev INTO STRICT head FROM truss.schema_head WHERE id=1;
 -- UNION owns the visited set. Nodes discover incident edge identities and
 -- owned edges discover both endpoints, without copying growing image maps.
 -- A valid component has at most 1024 nodes plus 1024 incident edges.
 WITH RECURSIVE seed_positions AS MATERIALIZED (
  SELECT (s.value->>'typeId')::int type_id,(s.value->>'id')::bigint object_id,s.ordinal
  FROM jsonb_array_elements(seeds) WITH ORDINALITY s(value,ordinal)),
 members(kind,member_type,member_id) AS (
  SELECT 'n'::text,s.type_id,s.object_id FROM seed_positions s
  UNION
  SELECT next_member.kind,next_member.member_type,next_member.member_id FROM members current_member
  CROSS JOIN LATERAL (
   (SELECT 'e'::text kind,e.rel_type_id member_type,e.id member_id FROM truss.edge e
    WHERE current_member.kind='n' AND
     ((e.source_id=current_member.member_id AND e.source_type=current_member.member_type)
      OR (e.target_id=current_member.member_id AND e.target_type=current_member.member_type))
    ORDER BY e.id LIMIT 1025)
   UNION ALL
   SELECT 'n'::text,endpoint.type_id,endpoint.object_id FROM truss.edge e
    JOIN truss.rel_def r ON r.rel_type_id=e.rel_type_id
    CROSS JOIN LATERAL (VALUES(e.source_type,e.source_id),(e.target_type,e.target_id)) endpoint(type_id,object_id)
    WHERE current_member.kind='e' AND e.id=current_member.member_id AND e.rel_type_id=current_member.member_type
     AND r.lifecycle='owned'
  ) next_member),
 bounded AS MATERIALIZED (SELECT * FROM members LIMIT 2049)
 SELECT coalesce(array_agg(b.member_type::text||':'||b.member_id::text
   ORDER BY coalesce(s.ordinal,2147483647),b.member_type,b.member_id) FILTER(WHERE b.kind='n'),'{}'::text[]),
  coalesce(array_agg(b.member_id::text ORDER BY b.member_id) FILTER(WHERE b.kind='e'),'{}'::text[])
 INTO node_keys,edge_keys FROM bounded b LEFT JOIN seed_positions s
  ON b.kind='n' AND s.type_id=b.member_type AND s.object_id=b.member_id;
 IF cardinality(node_keys)>1024 OR cardinality(edge_keys)>1024 THEN
  RAISE EXCEPTION 'bounded complete ownership component required' USING ERRCODE='54000';END IF;
 SELECT coalesce(jsonb_object_agg(n.key,n.ordinal-1),'{}'::jsonb) INTO node_positions
 FROM unnest(node_keys) WITH ORDINALITY n(key,ordinal);
 FOREACH node_key IN ARRAY node_keys LOOP
  selected_type:=split_part(node_key,':',1)::int;selected_id:=split_part(node_key,':',2)::bigint;
  SELECT to_jsonb(o) INTO STRICT image FROM truss.object o WHERE o.id=selected_id AND o.type_id=selected_type;
  used_bytes:=used_bytes+octet_length(convert_to(image::text,'UTF8'));
  IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
  node_images[selected_node]:=image;
  selected_node:=selected_node+1;
 END LOOP;
 FOR selected_type IN SELECT DISTINCT split_part(n.key,':',1)::int FROM unnest(node_keys) n(key) ORDER BY 1 LOOP
  SELECT to_jsonb(t) INTO STRICT definition FROM truss.type_def t WHERE t.type_id=selected_type;
  used_bytes:=used_bytes+octet_length(convert_to(definition::text,'UTF8'));
  IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
  type_images[cardinality(type_images)+1]:=definition;
 END LOOP;
 FOREACH edge_key IN ARRAY edge_keys LOOP
  SELECT to_jsonb(e) INTO STRICT image FROM truss.edge e WHERE e.id=edge_key::bigint;
  used_bytes:=used_bytes+octet_length(convert_to(image::text,'UTF8'));
  IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
  edge_images[cardinality(edge_images)+1]:=image;
 END LOOP;
 FOR selected_type IN SELECT DISTINCT (e.image->>'rel_type_id')::int FROM unnest(edge_images) e(image) ORDER BY 1 LOOP
  SELECT to_jsonb(r) INTO STRICT relation_image FROM truss.rel_def r WHERE r.rel_type_id=selected_type;
  IF relation_image->>'lifecycle' NOT IN ('owned','independent') OR relation_image->'retired_rev'<>'null'::jsonb THEN
   RAISE EXCEPTION 'supported current incident lifecycle required' USING ERRCODE='0A000';END IF;
  IF relation_image->>'lifecycle'='owned' AND (relation_image->'directed'<>'true'::jsonb
   OR relation_image->'composition'<>'false'::jsonb OR relation_image->'assoc_type_id'<>'null'::jsonb) THEN
   RAISE EXCEPTION 'selected parent to target ownership required' USING ERRCODE='0A000';END IF;
  used_bytes:=used_bytes+octet_length(convert_to(relation_image::text,'UTF8'));
  IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
  relation_images[cardinality(relation_images)+1]:=relation_image;
 END LOOP;
 SELECT coalesce(jsonb_object_agg(c.node_key,c.image),'{}'::jsonb) INTO nodes
 FROM unnest(node_keys,node_images) AS c(node_key,image);
 SELECT coalesce(jsonb_object_agg(c.edge_key,c.image),'{}'::jsonb) INTO edges
 FROM unnest(edge_keys,edge_images) AS c(edge_key,image);
 SELECT coalesce(jsonb_object_agg(t.image->>'type_id',t.image),'{}'::jsonb) INTO types FROM unnest(type_images) t(image);
 SELECT coalesce(jsonb_object_agg(r.image->>'rel_type_id',r.image),'{}'::jsonb) INTO relations FROM unnest(relation_images) r(image);
 WITH owned AS (
  SELECT e.image,row_number() OVER(ORDER BY (e.image->>'id')::bigint)-1 ordinal
  FROM unnest(edge_images) e(image) JOIN truss.rel_def r ON r.rel_type_id=(e.image->>'rel_type_id')::int WHERE r.lifecycle='owned')
 SELECT coalesce(jsonb_agg(jsonb_build_object('edge',o.ordinal,
   'source',(node_positions->>((o.image->>'source_type')||':'||(o.image->>'source_id')))::int,
   'target',(node_positions->>((o.image->>'target_type')||':'||(o.image->>'target_id')))::int) ORDER BY o.ordinal),'[]'::jsonb),
  coalesce(array_agg(o.image->>'id' ORDER BY o.ordinal),'{}'::text[])
 INTO local_edges,owned_edge_order FROM owned o;
 -- Independent endpoints and their roots are witnesses, not traversed nodes.
 WITH RECURSIVE witnesses(type_id,object_id) AS (
  SELECT endpoint.type_id,endpoint.object_id FROM unnest(edge_images) e(image)
   JOIN truss.rel_def r ON r.rel_type_id=(e.image->>'rel_type_id')::int
   CROSS JOIN LATERAL (VALUES((e.image->>'source_type')::int,(e.image->>'source_id')::bigint),
    ((e.image->>'target_type')::int,(e.image->>'target_id')::bigint)) endpoint(type_id,object_id)
   WHERE r.lifecycle='independent' AND NOT (node_positions ? (endpoint.type_id::text||':'||endpoint.object_id::text))
  UNION
  SELECT o.root_type,o.root_id FROM witnesses w JOIN truss.object o ON o.id=w.object_id AND o.type_id=w.type_id
   WHERE o.root_id IS NOT NULL AND NOT (node_positions ? (o.root_type::text||':'||o.root_id::text)))
 SELECT coalesce(array_agg(w.type_id::text||':'||w.object_id::text ORDER BY w.type_id,w.object_id),'{}'::text[])
 INTO boundary_keys FROM (SELECT * FROM witnesses LIMIT 257) w;
 IF cardinality(boundary_keys)>256 THEN RAISE EXCEPTION 'bounded boundary witnesses required' USING ERRCODE='54000';END IF;
 FOREACH node_key IN ARRAY boundary_keys LOOP
  selected_type:=split_part(node_key,':',1)::int;selected_id:=split_part(node_key,':',2)::bigint;
  SELECT jsonb_build_object('id',o.id,'type_id',o.type_id,'root_id',o.root_id,'root_type',o.root_type,'rev',o.rev,'ver',o.ver)
   INTO STRICT witness FROM truss.object o WHERE o.id=selected_id AND o.type_id=selected_type;
  SELECT to_jsonb(t) INTO STRICT definition FROM truss.type_def t WHERE t.type_id=selected_type;
  boundary_images[cardinality(boundary_images)+1]:=jsonb_build_object('object',witness,'definition',definition);
  used_bytes:=used_bytes+octet_length(convert_to(witness::text,'UTF8'))+octet_length(convert_to(definition::text,'UTF8'));
  IF used_bytes>4194304 THEN RAISE EXCEPTION 'bounded complete graph image required' USING ERRCODE='54000';END IF;
 END LOOP;
 SELECT coalesce(jsonb_object_agg(b.key,b.image),'{}'::jsonb) INTO boundary
 FROM unnest(boundary_keys,boundary_images) b(key,image);
 -- An aggregate root pointer without a connecting owned-edge path is corrupt
 -- membership, not permission to invent an edge or silently omit a cascade child.
 IF EXISTS(SELECT 1 FROM unnest(node_keys) n(node_key) JOIN truss.object o
   ON o.root_type=split_part(n.node_key,':',1)::int AND o.root_id=split_part(n.node_key,':',2)::bigint
   WHERE NOT (node_positions ? (o.type_id::text||':'||o.id::text)) LIMIT 1) THEN
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
   OR octet_length(lean_nodes::text)+octet_length(lean_types::text)>16777216 THEN
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
