-- The trusted engine has already planned and written the group. Settlement
-- checks current custody, completeness and authority; it does not execute a
-- second semantic/history program over private immutable plans and effects.
CREATE FUNCTION truss.runtime_owned_group_validate(selected_attempt uuid,check_final boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;current_actor oid;initial_scope jsonb;
 owner record;source_cut record;history_basis jsonb;root_type int;selected_revision int;
 operation_count int;missing_results int;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 current_actor:=truss.runtime_person(false);
 IF check_final IS NULL OR NOT attempt.complete
  OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR attempt.result_count IS DISTINCT FROM attempt.next_index THEN
  RAISE EXCEPTION 'complete current owned group required' USING ERRCODE='55000';END IF;
 SELECT count(*),count(*) FILTER(WHERE result IS NULL)
 INTO operation_count,missing_results FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt;
 IF operation_count<>attempt.next_index OR missing_results<>0 THEN
  RAISE EXCEPTION 'complete owned operation results required' USING ERRCODE='55000';END IF;
 SELECT plan->'initialScope',(plan->>'catalogRevision')::int INTO STRICT initial_scope,selected_revision
 FROM truss.runtime_owned_operation WHERE attempt_id=selected_attempt AND operation_index=0;
 -- At finish this is the executing revision. A later accepted revision in the
 -- same outer transaction may supersede it; commit retains historical readers.
 IF check_final AND selected_revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1) THEN
  RAISE EXCEPTION 'current finishing catalog revision required' USING ERRCODE='55000';END IF;
 -- Include original component owners and actual selected resources. No-op
 -- results have no transition but still require their original current writer.
 FOR owner IN
  SELECT DISTINCT document_id,module_id FROM (
   SELECT r.value->'identity'->'owner'->>'documentId' document_id,r.value->'identity'->'owner'->>'moduleId' module_id
    FROM jsonb_array_elements(attempt.results) r
   UNION ALL SELECT d.document_id,d.module FROM truss.runtime_object_transition t JOIN truss.type_def d USING(type_id)
    WHERE t.attempt_id=selected_attempt
   UNION ALL SELECT d.document_id,d.module FROM truss.runtime_edge_transition t JOIN truss.rel_def d USING(rel_type_id)
    WHERE t.attempt_id=selected_attempt
  ) dependencies
 LOOP
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module_id,current_actor);
 END LOOP;
 FOR owner IN SELECT DISTINCT document_id,module_id FROM (
  SELECT value->'definition'->>'document_id' document_id,value->'definition'->>'module' module_id FROM jsonb_each(initial_scope->'boundary')
  UNION ALL SELECT d.document_id,d.module FROM jsonb_each(initial_scope->'nodes') n JOIN truss.type_def d ON d.type_id=(n.value->>'type_id')::int
  UNION ALL SELECT d.document_id,d.module FROM jsonb_each(initial_scope->'edges') e JOIN truss.rel_def d ON d.rel_type_id=(e.value->>'rel_type_id')::int
 ) observed_readers LOOP
  IF NOT truss.runtime_can_read_qualified(owner.document_id,owner.module_id,current_actor) THEN
   RAISE EXCEPTION 'current boundary reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 -- Executed object types (including no-ops) use the compiled dependency
 -- union once per revision/type, rather than one authorization program per row.
 FOR owner IN
  WITH selected_types AS (
   SELECT DISTINCT (r.value->'identity'->>'typeId')::int type_id FROM jsonb_array_elements(attempt.results) r
    WHERE r.value->>'operation' IN ('create_object','update_object','delete_object')
   UNION SELECT type_id FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt)
  SELECT DISTINCT r.value->>'documentId' document_id,r.value->>'moduleId' module_id
  FROM selected_types t JOIN truss.runtime_type_schema s ON s.type_id=t.type_id AND s.rev=selected_revision
  CROSS JOIN LATERAL jsonb_array_elements(s.value_readers) r
 LOOP
  IF NOT truss.runtime_can_read_qualified(owner.document_id,owner.module_id,current_actor) THEN
   RAISE EXCEPTION 'current executed property/item reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 -- Check historical property/item dependencies from actual captured images,
 -- including no-op sources, without reconstructing any history payload.
 FOR source_cut IN
  WITH selected_types AS MATERIALIZED (
   SELECT DISTINCT (r.value->'identity'->>'typeId')::int type_id FROM jsonb_array_elements(attempt.results) r
    WHERE r.value->>'operation' IN ('create_object','update_object','delete_object')
   UNION SELECT type_id FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt),
  images AS (
   SELECT value image FROM jsonb_each(initial_scope->'nodes')
   UNION ALL SELECT before_object FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt AND before_object IS NOT NULL
   UNION ALL SELECT after_object FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt AND after_object IS NOT NULL)
  SELECT (image->>'type_id')::int type_id,(image->>'rev')::int revision,
   coalesce(array_agg(DISTINCT p.name) FILTER(WHERE p.name IS NOT NULL),'{}'::text[]) present_names
  FROM images LEFT JOIN selected_types t ON t.type_id=(image->>'type_id')::int
  LEFT JOIN LATERAL jsonb_object_keys(image->'props') p(name) ON true
  WHERE (image->>'rev')::int<>selected_revision OR t.type_id IS NULL
  GROUP BY (image->>'type_id')::int,(image->>'rev')::int
 LOOP
  SELECT metadata INTO STRICT history_basis FROM truss.runtime_type_schema
   WHERE rev=source_cut.revision AND type_id=source_cut.type_id;
  IF EXISTS(SELECT 1 FROM jsonb_each(history_basis->'propertyAccess') p
   WHERE p.key=ANY(source_cut.present_names) AND p.value->'itemsValid' IS DISTINCT FROM 'true'::jsonb) THEN
   RAISE EXCEPTION 'current historical property/item readers required' USING ERRCODE='42501';END IF;
  FOR owner IN SELECT DISTINCT r.value->>'documentId' document_id,r.value->>'moduleId' module_id
   FROM jsonb_each(history_basis->'propertyAccess') p CROSS JOIN LATERAL jsonb_array_elements(p.value->'readers') r
   WHERE p.key=ANY(source_cut.present_names) LOOP
   IF NOT truss.runtime_can_read_qualified(owner.document_id,owner.module_id,current_actor) THEN
    RAISE EXCEPTION 'current historical property/item readers required' USING ERRCODE='42501';END IF;
  END LOOP;
 END LOOP;
 -- Root identity authorization is independent of reading an endpoint's type.
 FOR root_type IN
  SELECT DISTINCT roots.root_type FROM (
   SELECT (value->>'root_type')::int root_type FROM jsonb_each(initial_scope->'nodes')
   UNION ALL SELECT (image->>'root_type')::int FROM truss.runtime_object_transition t
    CROSS JOIN LATERAL (VALUES(t.before_object),(t.after_object)) v(image) WHERE t.attempt_id=selected_attempt
  ) roots WHERE roots.root_type IS NOT NULL
 LOOP
  SELECT document_id,module AS module_id INTO STRICT owner FROM truss.type_def WHERE type_id=root_type;
  IF NOT truss.runtime_can_read_qualified(owner.document_id,owner.module_id,current_actor) THEN
   RAISE EXCEPTION 'current captured root reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 PERFORM truss.runtime_edge_authorize(selected_attempt);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_group_validate(uuid,boolean) FROM PUBLIC;
