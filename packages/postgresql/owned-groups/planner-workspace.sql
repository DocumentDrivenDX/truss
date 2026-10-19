-- Per-invocation mutable planner helpers.  The executor passes the identifier
-- of its uniquely named pg_temp relation; these helpers never retain state.
CREATE FUNCTION truss.runtime_owned_workspace_state(workspace text,member_kind char,member_ref text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;
BEGIN
 EXECUTE format('SELECT state FROM pg_temp.%I WHERE member_kind=$1 AND member_ref=$2',workspace) INTO result USING member_kind,member_ref;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_state(text,char,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_state_or(workspace text,member_kind char,member_ref text,fallback_map jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;
BEGIN
 IF workspace IS NULL THEN RETURN fallback_map->member_ref;END IF;
 EXECUTE format('SELECT state FROM pg_temp.%I WHERE member_kind=$1 AND member_ref=$2',workspace) INTO result USING member_kind,member_ref;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_state_or(text,char,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_state_at(workspace text,member_kind char,member_ref text,operation_index int,before_image boolean DEFAULT false) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;
BEGIN
 EXECUTE format('SELECT CASE WHEN $4 AND created_operation=$3 THEN NULL WHEN $4 AND before_operation=$3 THEN before_state ELSE state END FROM pg_temp.%I WHERE member_kind=$1 AND member_ref=$2',workspace)
  INTO result USING member_kind,member_ref,operation_index,before_image;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_state_at(text,char,text,int,boolean) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_state_at_or(workspace text,member_kind char,member_ref text,operation_index int,before_image boolean,fallback_map jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF workspace IS NULL THEN RETURN fallback_map->member_ref;END IF;
 RETURN truss.runtime_owned_workspace_state_at(workspace,member_kind,member_ref,operation_index,before_image);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_state_at_or(text,char,text,int,boolean,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_put(workspace text,member_kind char,member_ref text,operation_index int,new_state jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 EXECUTE format('UPDATE pg_temp.%I SET before_state=CASE WHEN before_operation IS DISTINCT FROM $3 THEN state ELSE before_state END,before_operation=$3,state=$4,deleted=coalesce(($4->>''deleted'')::boolean,false),root_ref=$4->>''root'',source_ref=$4->>''source'',target_ref=$4->>''target'',lifecycle=$4->>''lifecycle'' WHERE member_kind=$1 AND member_ref=$2',workspace)
  USING member_kind,member_ref,operation_index,new_state;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_put(text,char,text,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_write(workspace text,member_kind char,member_ref text,operation_index int,new_state jsonb,fallback_map jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF workspace IS NULL THEN RETURN coalesce(fallback_map,'{}'::jsonb)||jsonb_build_object(member_ref,new_state);END IF;
 PERFORM truss.runtime_owned_workspace_put(workspace,member_kind,member_ref,operation_index,new_state);
 RETURN fallback_map;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_write(text,char,text,int,jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_insert(workspace text,member_kind char,member_ref text,member_ordinal int,operation_index int,new_state jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 EXECUTE format('INSERT INTO pg_temp.%I(member_kind,member_ref,member_ordinal,created_operation,state,deleted,root_ref,source_ref,target_ref,lifecycle) VALUES($1,$2,$3,$5,$4,coalesce(($4->>''deleted'')::boolean,false),$4->>''root'',$4->>''source'',$4->>''target'',$4->>''lifecycle'')',workspace)
  USING member_kind,member_ref,member_ordinal,new_state,operation_index;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_insert(text,char,text,int,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_reference(reference jsonb,workspace text,member_kind char,operation_index int) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected text;identity jsonb;selected_state jsonb;alias_operation int;
BEGIN
 IF jsonb_typeof(reference) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'explicit graph reference required' USING ERRCODE='22023';END IF;
 IF reference->>'state'='alias' THEN
  IF reference-ARRAY['state','alias']<>'{}'::jsonb OR jsonb_typeof(reference->'alias') IS DISTINCT FROM 'string' THEN
   RAISE EXCEPTION 'closed prior alias required' USING ERRCODE='22023';END IF;
   EXECUTE format('SELECT source_ref,member_ordinal FROM pg_temp.%I WHERE member_kind=''a'' AND member_ref=$1',workspace)
   INTO selected,alias_operation USING reference->>'alias';
  IF selected IS NULL OR alias_operation>=operation_index THEN RAISE EXCEPTION 'existing reference of the correct kind required' USING ERRCODE='22023';END IF;
 ELSIF reference->>'state'='stored' THEN
  identity:=reference->'identity';
  IF reference-ARRAY['state','identity']<>'{}'::jsonb OR jsonb_typeof(identity) IS DISTINCT FROM 'object'
   OR identity-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb THEN
   RAISE EXCEPTION 'closed original stored reference required' USING ERRCODE='22023';END IF;
  selected:='stored:'||(identity->>'typeId')||':'||(identity->>'id');
 ELSE RAISE EXCEPTION 'stored or prior alias required' USING ERRCODE='22023';END IF;
 selected_state:=truss.runtime_owned_workspace_state(workspace,member_kind,selected);
 IF selected_state IS NULL THEN RAISE EXCEPTION 'existing reference of the correct kind required' USING ERRCODE='22023';END IF;
 IF selected_state->'deleted'='true'::jsonb THEN RAISE EXCEPTION 'referenced graph member deleted' USING ERRCODE='P1004';END IF;
 IF identity IS NOT NULL AND identity IS DISTINCT FROM selected_state->'identity' THEN
  RAISE EXCEPTION 'original qualified identity correspondence required' USING ERRCODE='22023';END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_reference(jsonb,text,char,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_map(workspace text,member_kind char,operation_index int,member_refs text[],before_image boolean DEFAULT false) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;
BEGIN
 EXECUTE format('SELECT coalesce(jsonb_object_agg(w.member_ref,CASE WHEN $4 AND w.before_operation=$3 THEN w.before_state ELSE w.state END),''{}''::jsonb) FROM pg_temp.%I w WHERE w.member_kind=$1 AND ($2 IS NULL OR w.member_ref=ANY($2)) AND (NOT $4 OR w.created_operation IS DISTINCT FROM $3)',workspace)
  INTO result USING member_kind,member_refs,operation_index,before_image;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_map(text,char,int,text[],boolean) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_aliases(workspace text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;
BEGIN
 EXECUTE format('SELECT coalesce(jsonb_object_agg(member_ref,source_ref),''{}''::jsonb) FROM pg_temp.%I WHERE member_kind=''a''',workspace)
  INTO result;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_aliases(text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_descendants(workspace text,selected_ref text) RETURNS text[]
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result text[];
BEGIN
 EXECUTE format($q$
  WITH RECURSIVE reached(member_ref) AS (
   SELECT $1::text
   UNION
   SELECT e.target_ref FROM pg_temp.%I e JOIN reached r ON e.source_ref=r.member_ref
    WHERE e.member_kind='e' AND NOT e.deleted AND e.lifecycle='owned'
  ) SELECT coalesce(array_agg(member_ref ORDER BY member_ref COLLATE "C"),'{}'::text[]) FROM reached
 $q$,workspace) INTO result USING selected_ref;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_descendants(text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_workspace_delete_plan(workspace text,selected_ref text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;has_independent boolean;
BEGIN
 EXECUTE format($q$
  WITH RECURSIVE reached(member_ref) AS (
   SELECT $1::text
   UNION
   SELECT e.target_ref FROM pg_temp.%I e JOIN reached r ON e.source_ref=r.member_ref
    WHERE e.member_kind='e' AND NOT e.deleted AND e.lifecycle='owned'
  ), incident_independent AS MATERIALIZED (
   SELECT 1 FROM pg_temp.%I e JOIN reached s ON s.member_ref=e.source_ref
    WHERE e.member_kind='e' AND NOT e.deleted AND e.lifecycle='independent'
   UNION ALL
   SELECT 1 FROM pg_temp.%I e JOIN reached t ON t.member_ref=e.target_ref
    WHERE e.member_kind='e' AND NOT e.deleted AND e.lifecycle='independent'
  ), deleted_nodes AS (
   SELECT n.member_ref,n.member_ordinal FROM pg_temp.%I n JOIN reached r USING(member_ref)
    WHERE n.member_kind='n' AND NOT n.deleted
  ), deleted_edges AS (
   SELECT member_ref FROM (
    SELECT e.member_ref FROM reached r JOIN pg_temp.%I e ON e.source_ref=r.member_ref
     WHERE e.member_kind='e' AND NOT e.deleted
    UNION
    SELECT e.member_ref FROM reached r JOIN pg_temp.%I e ON e.target_ref=r.member_ref
     WHERE e.member_kind='e' AND NOT e.deleted
   ) incident
  )
  SELECT EXISTS(SELECT 1 FROM incident_independent),
   jsonb_build_object('deletedNodes',coalesce((SELECT jsonb_agg(member_ref ORDER BY member_ordinal) FROM deleted_nodes),'[]'::jsonb),
    'deletedEdges',coalesce((SELECT jsonb_agg(member_ref ORDER BY member_ref COLLATE "C") FROM deleted_edges),'[]'::jsonb))
 $q$,workspace,workspace,workspace,workspace,workspace,workspace) INTO has_independent,result USING selected_ref;
 IF has_independent THEN RAISE EXCEPTION 'independent incident edge prevents owned deletion' USING ERRCODE='22023';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_workspace_delete_plan(text,text) FROM PUBLIC;

