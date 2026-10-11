-- Private bounded physical forest validation; no complete-scope or seal authority.
CREATE FUNCTION truss.row_image_forest_original(original_scope bytea) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE scope jsonb; item jsonb; state truss.row_home_state; node truss.row_home_node;
 nodes truss.row_home_node[]:=ARRAY[]::truss.row_home_node[]; roots text[] COLLATE pg_catalog."C":=ARRAY[]::text[];
 payloads text[] COLLATE pg_catalog."C":=ARRAY[]::text[]; keys text[] COLLATE pg_catalog."C":=ARRAY[]::text[]; slots text[] COLLATE pg_catalog."C":=ARRAY[]::text[];
 pending text[] COLLATE pg_catalog."C":=ARRAY[]::text[]; seen text[] COLLATE pg_catalog."C":=ARRAY[]::text[]; key text COLLATE pg_catalog."C"; slot text COLLATE pg_catalog."C";
 parent_index int; i int; count_children bigint; next_key text COLLATE pg_catalog."C";
BEGIN
 scope:=truss.row_touch_scope_original(original_scope);
 FOR item IN SELECT value FROM jsonb_array_elements(scope->'images') LOOP
  CASE item->>'kind'
  WHEN 'state' THEN
   state:=truss.row_touch_state_from_image_original(decode(item->>'imageHex','hex'));
   roots:=array_append(roots,state.state_id::text||'/'||state.root_node_id::text);
  WHEN 'node' THEN
   node:=truss.row_touch_node_from_image_original(decode(item->>'imageHex','hex'));
   nodes:=array_append(nodes,node);keys:=array_append(keys,node.state_id::text||'/'||node.node_id::text);
  WHEN 'scalar' THEN
   payloads:=array_append(payloads,truss.row_touch_integer_original((truss.row_touch_image_cells_original('scalar',decode(item->>'imageHex','hex')))[1])::text||'/'||truss.row_touch_integer_original((truss.row_touch_image_cells_original('scalar',decode(item->>'imageHex','hex')))[2])::text);
  END CASE;
 END LOOP;
 FOREACH key IN ARRAY roots LOOP
  IF NOT key=ANY(keys) THEN RAISE EXCEPTION 'declared physical root required' USING ERRCODE='22023';END IF;
 END LOOP;
 FOR i IN 1..cardinality(nodes) LOOP
  node:=nodes[i];key:=keys[i];
  IF node.value_kind COLLATE pg_catalog."C" NOT IN ('scalar','null','sequence','map','record','structured')
   OR (key=ANY(payloads)) IS DISTINCT FROM (node.value_kind COLLATE pg_catalog."C"='scalar') THEN
   RAISE EXCEPTION 'physical node payload parity required' USING ERRCODE='22023';
  END IF;
  IF node.parent_node_id IS NULL THEN
   IF NOT key=ANY(roots) OR node.slot_kind COLLATE pg_catalog."C"<>'root' OR node.sequence_ordinal IS NOT NULL
    OR node.map_key IS NOT NULL OR node.record_field_identity_bytes IS NOT NULL THEN
    RAISE EXCEPTION 'exact parentless declared root required' USING ERRCODE='22023';
   END IF;
  ELSE
   parent_index:=array_position(keys,node.state_id::text||'/'||node.parent_node_id::text);
   IF parent_index IS NULL OR parent_index=i OR key=ANY(roots) THEN
    RAISE EXCEPTION 'same-state physical parent required' USING ERRCODE='22023';
   END IF;
   CASE node.slot_kind COLLATE pg_catalog."C"
   WHEN 'sequence' THEN
    IF (nodes[parent_index]).value_kind COLLATE pg_catalog."C"<>'sequence' OR node.sequence_ordinal IS NULL
     OR node.sequence_ordinal<0 OR node.map_key IS NOT NULL OR node.record_field_identity_bytes IS NOT NULL THEN
     RAISE EXCEPTION 'physical sequence slot required' USING ERRCODE='22023';END IF;
    SELECT count(*) INTO count_children FROM unnest(nodes) n WHERE n.state_id=node.state_id AND n.parent_node_id=node.parent_node_id;
    IF node.sequence_ordinal>=count_children THEN RAISE EXCEPTION 'contiguous sequence required' USING ERRCODE='22023';END IF;
    slot:='sequence/'||node.sequence_ordinal::text;
   WHEN 'map' THEN
    IF (nodes[parent_index]).value_kind COLLATE pg_catalog."C"<>'map' OR node.map_key IS NULL
     OR node.sequence_ordinal IS NOT NULL OR node.record_field_identity_bytes IS NOT NULL THEN
     RAISE EXCEPTION 'physical map slot required' USING ERRCODE='22023';END IF;
    slot:='map/'||encode(convert_to(node.map_key,'UTF8'),'hex');
   WHEN 'record' THEN
    IF (nodes[parent_index]).value_kind COLLATE pg_catalog."C" NOT IN ('record','structured') OR node.record_field_identity_bytes IS NULL
     OR octet_length(node.record_field_identity_bytes)=0 OR node.sequence_ordinal IS NOT NULL OR node.map_key IS NOT NULL THEN
     RAISE EXCEPTION 'physical record slot required' USING ERRCODE='22023';END IF;
    slot:='record/'||encode(node.record_field_identity_bytes,'hex');
   ELSE RAISE EXCEPTION 'physical child slot required' USING ERRCODE='22023';
   END CASE;
   slot:=node.state_id::text||'/'||node.parent_node_id::text||'/'||slot;
   IF slot=ANY(slots) THEN RAISE EXCEPTION 'unique physical child slot required' USING ERRCODE='22023';END IF;
   slots:=array_append(slots,slot);
  END IF;
 END LOOP;
 pending:=roots;
 WHILE cardinality(pending)>0 LOOP
  key:=pending[cardinality(pending)];pending:=pending[1:cardinality(pending)-1];
  IF key=ANY(seen) THEN RAISE EXCEPTION 'acyclic physical forest required' USING ERRCODE='22023';END IF;
  seen:=array_append(seen,key);
  FOR i IN 1..cardinality(nodes) LOOP
   node:=nodes[i];
   IF node.parent_node_id IS NOT NULL AND node.state_id::text||'/'||node.parent_node_id::text=key THEN
    next_key:=keys[i];pending:=array_append(pending,next_key);
   END IF;
  END LOOP;
 END LOOP;
 IF cardinality(seen)<>cardinality(nodes) THEN
  RAISE EXCEPTION 'complete physical reachability required' USING ERRCODE='22023';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_forest_original(bytea) FROM PUBLIC;
