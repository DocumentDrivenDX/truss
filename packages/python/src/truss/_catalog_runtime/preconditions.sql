-- Caller predicates observe the locked group prestate, before effects.
CREATE FUNCTION truss.runtime_relationship_pin(selected_relationship int,historical_revision int DEFAULT NULL) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE relation truss.rel_def%ROWTYPE;archive truss.schema_doc%ROWTYPE;module_json json;fragment json;mi int;ri int;pointer text;original bytea;pin_input text;
BEGIN
 IF historical_revision IS NULL THEN
  SELECT * INTO STRICT relation FROM truss.rel_def WHERE rel_type_id=selected_relationship AND retired_rev IS NULL;
 ELSE
  SELECT r.* INTO relation FROM truss.rel_def r
   WHERE r.rel_type_id=selected_relationship
    AND historical_revision=(SELECT rev FROM truss.schema_head WHERE id=1)
    AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>historical_revision);
  IF NOT FOUND THEN
   SELECT * INTO STRICT relation FROM jsonb_populate_recordset(NULL::truss.rel_def,truss.catalog_all_expected_records(historical_revision)->'rel_def') r WHERE r.rel_type_id=selected_relationship;
  END IF;
 END IF;
 SELECT d.definition_pin INTO STRICT pin_input FROM truss.runtime_definition_source d
 WHERE d.rev=relation.definition_rev AND d.ord=relation.definition_doc_ord AND d.doc_id=relation.definition_document_id
  AND d.module_id=relation.module AND d.element_id=relation.rel_id AND d.kind='relationship' AND d.key_id='';
 RETURN pin_input;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_relationship_pin(int,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_condition_type(identity jsonb) RETURNS truss.type_def
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected truss.type_def%ROWTYPE;pin record;type_number text;object_number text;
BEGIN
 type_number:=identity->>'typeId';object_number:=identity->>'id';
 IF jsonb_typeof(identity) IS DISTINCT FROM 'object' OR identity-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb
 OR jsonb_typeof(identity->'typeId') IS DISTINCT FROM 'string' OR jsonb_typeof(identity->'id') IS DISTINCT FROM 'string'
 OR jsonb_typeof(identity->'definitionPin') IS DISTINCT FROM 'string'
 OR type_number !~ '^[1-9][0-9]{0,9}$' OR length(type_number)=10 AND type_number COLLATE "C">'2147483647'
 OR object_number !~ '^[1-9][0-9]{0,18}$' OR length(object_number)=19 AND object_number COLLATE "C">'9223372036854775807' THEN
  RAISE EXCEPTION 'qualified exact condition identity required' USING ERRCODE='22023';END IF;
 SELECT * INTO selected FROM truss.type_def WHERE type_id=type_number::int AND kind='record' AND NOT provisional AND retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'known condition type required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',selected.type_id);
 IF identity->>'definitionPin' IS DISTINCT FROM pin.definition_pin OR identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module) THEN
  RAISE EXCEPTION 'current qualified condition definition required' USING ERRCODE='22023';END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_condition_type(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_condition_inventory(input jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE conditions jsonb:=coalesce(input->'preconditions','[]');condition jsonb;selected truss.type_def%ROWTYPE;other truss.type_def%ROWTYPE;
 relation truss.rel_def%ROWTYPE;property truss.prop_def%ROWTYPE;key_row truss.key_def%ROWTYPE;component record;owner record;
 inventory jsonb;inventory_entries jsonb[]:='{}';entry jsonb;objects jsonb;scopes jsonb;scope_entries jsonb[];scope_entry jsonb;identity jsonb;bound text;index int:=0;
BEGIN
 IF jsonb_typeof(conditions) IS DISTINCT FROM 'array' OR jsonb_array_length(conditions)>128 THEN RAISE EXCEPTION 'bounded condition list required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(conditions)<>(SELECT count(DISTINCT value->>'id') FROM jsonb_array_elements(conditions)) THEN RAISE EXCEPTION 'unique condition IDs required' USING ERRCODE='22023';END IF;
 FOR condition IN SELECT value FROM jsonb_array_elements(conditions) LOOP
  IF jsonb_typeof(condition->'id') IS DISTINCT FROM 'string' OR octet_length(condition->>'id') NOT BETWEEN 1 AND 1024
   OR jsonb_typeof(condition->'reason') IS DISTINCT FROM 'string' OR octet_length(condition->>'reason')>4096 THEN RAISE EXCEPTION 'caller condition ID/reason required' USING ERRCODE='22023';END IF;
  objects:='[]';scope_entries:='{}';entry:=jsonb_build_object('index',index,'condition',condition);
  IF condition->>'condition' IN ('object_exists','property_equals') THEN
   IF condition-(CASE condition->>'condition' WHEN 'object_exists' THEN ARRAY['condition','id','reason','target'] ELSE ARRAY['condition','id','reason','target','name','value'] END)<>'{}'::jsonb THEN RAISE EXCEPTION 'closed object condition required' USING ERRCODE='22023';END IF;
   selected:=truss.runtime_condition_type(condition->'target');objects:=jsonb_build_array(condition->'target');
   scope_entries[cardinality(scope_entries)+1]:=jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module);
   IF condition->>'condition'='property_equals' THEN
    IF jsonb_typeof(condition->'name') IS DISTINCT FROM 'string' OR octet_length(condition->>'name') NOT BETWEEN 1 AND 4096 OR truss.valid_flat_cell(condition->'value') IS NOT TRUE THEN RAISE EXCEPTION 'exact scalar property equality required' USING ERRCODE='22023';END IF;
    SELECT * INTO property FROM truss.prop_def p WHERE p.type_id=selected.type_id AND p.name=condition->>'name' AND p.retired_rev IS NULL;
    IF FOUND THEN entry:=entry||jsonb_build_object('propertyId',property.prop_id::text);
     scope_entries[cardinality(scope_entries)+1]:=jsonb_build_object('documentId',selected.document_id,'moduleId',property.declaration_module);
     IF property.cardinality IN ('array','map') THEN
      FOR scope_entry IN SELECT jsonb_build_object('documentId',node.value->>'documentId','moduleId',node.value->'reference'->>'module')
       FROM jsonb_array_elements(jsonb_build_array(property.item)||coalesce(property.item->'descendants','[]'::jsonb)) WITH ORDINALITY node(value,ordinality)
       ORDER BY node.ordinality LOOP
       scope_entries[cardinality(scope_entries)+1]:=scope_entry;
      END LOOP;
     END IF;
    END IF;
   END IF;
  ELSIF condition->>'condition'='key_absent' THEN
   IF condition-ARRAY['condition','id','reason','typeDefinitionPin','keyId','values']<>'{}'::jsonb OR jsonb_typeof(condition->'values') IS DISTINCT FROM 'array'
    OR jsonb_array_length(condition->'values') NOT BETWEEN 1 AND 1024 THEN RAISE EXCEPTION 'closed key condition required' USING ERRCODE='22023';END IF;
   WITH pinned AS MATERIALIZED (
    SELECT rev,ord,doc_id,module_id,element_id FROM truss.runtime_definition_source
    WHERE definition_pin=condition->>'typeDefinitionPin' AND kind='element' AND key_id='')
   SELECT t.* INTO selected FROM pinned p JOIN truss.type_def t
    ON t.definition_rev=p.rev AND t.definition_doc_ord=p.ord AND t.definition_document_id=p.doc_id
     AND t.module=p.module_id AND t.element=p.element_id
    WHERE NOT t.provisional AND t.retired_rev IS NULL;
   IF NOT FOUND THEN RAISE EXCEPTION 'known predicate type required' USING ERRCODE='22023';END IF;
   SELECT * INTO key_row FROM truss.key_def WHERE type_id=selected.type_id AND key_id=condition->>'keyId' AND retired_rev IS NULL;
   IF NOT FOUND THEN RAISE EXCEPTION 'known predicate key required' USING ERRCODE='22023';END IF;
   IF cardinality(key_row.prop_ids)<>jsonb_array_length(condition->'values') OR EXISTS(SELECT 1 FROM jsonb_array_elements(condition->'values') v WHERE v.value->>'kind' NOT IN ('string','integer','decimal','boolean','binary') OR truss.valid_scalar_cell(v.value,NULL,false) IS NOT TRUE) THEN RAISE EXCEPTION 'complete exact key values required' USING ERRCODE='22023';END IF;
   scope_entries[cardinality(scope_entries)+1]:=jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module);
   FOR component IN SELECT p.*,i.ord AS component_ordinal FROM unnest(key_row.prop_ids) WITH ORDINALITY i(prop_id,ord) JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=selected.type_id ORDER BY i.ord LOOP
    IF component.scalar_type NOT IN ('string','integer','decimal','boolean','binary') OR component.nullability IS DISTINCT FROM 'required' OR component.retired_rev IS NOT NULL THEN RAISE EXCEPTION 'supported string key required' USING ERRCODE='0A000';END IF;
    IF truss.valid_scalar_property(condition->'values'->(component.component_ordinal::int-1),component.scalar_type,false,component.facets) IS NOT TRUE THEN RAISE EXCEPTION 'exact declared condition key cell required' USING ERRCODE='22023';END IF;
    scope_entries[cardinality(scope_entries)+1]:=jsonb_build_object('documentId',selected.document_id,'moduleId',component.declaration_module);
   END LOOP;
   entry:=entry||jsonb_build_object('typeId',selected.type_id::text,'documentId',selected.document_id,'moduleId',selected.module,'recordId',selected.element,'keyId',key_row.key_id,'keyNumber',key_row.key_num::text,'values',condition->'values');
  ELSIF condition->>'condition' IN ('relationship_absent','relationship_count') THEN
   -- Select the exact source pin before joining native coordinates. Evaluating
   -- the pin function for every unrelated relationship made bounded condition
   -- batches grow with the complete catalog instead of their selected pins.
   WITH pinned AS MATERIALIZED (
    SELECT rev,ord,doc_id,module_id,element_id FROM truss.runtime_definition_source
    WHERE definition_pin=condition->>'relationshipDefinitionPin' AND kind='relationship' AND key_id='')
   SELECT r.* INTO relation FROM pinned p JOIN truss.rel_def r
    ON r.definition_rev=p.rev AND r.definition_doc_ord=p.ord AND r.definition_document_id=p.doc_id
     AND r.module=p.module_id AND r.rel_id=p.element_id
    WHERE r.retired_rev IS NULL;
   IF NOT FOUND THEN RAISE EXCEPTION 'known predicate relationship required' USING ERRCODE='22023';END IF;
   scope_entries[cardinality(scope_entries)+1]:=jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module);
   FOR owner IN SELECT DISTINCT t.document_id,t.module FROM truss.rel_endpoint e JOIN truss.type_def t ON t.type_id=e.source_type OR t.type_id=e.target_type WHERE e.rel_type_id=relation.rel_type_id LOOP
    scope_entries[cardinality(scope_entries)+1]:=jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module);
   END LOOP;
   entry:=entry||jsonb_build_object('relationshipId',relation.rel_type_id::text);
   IF condition->>'condition'='relationship_absent' THEN
    IF condition-ARRAY['condition','id','reason','relationshipDefinitionPin','source','target']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed relationship condition required' USING ERRCODE='22023';END IF;
    selected:=truss.runtime_condition_type(condition->'source');other:=truss.runtime_condition_type(condition->'target');
    IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=selected.type_id AND target_type=other.type_id) THEN RAISE EXCEPTION 'admitted relationship endpoint types required' USING ERRCODE='22023';END IF;
    objects:=jsonb_build_array(condition->'source',condition->'target');
   ELSE
    IF condition-ARRAY['condition','id','reason','relationshipDefinitionPin','anchor','direction','minimum','maximum']<>'{}'::jsonb OR coalesce(condition->>'direction','') NOT IN ('outgoing','incoming') OR jsonb_typeof(condition->'minimum') IS DISTINCT FROM 'string' OR (condition ? 'maximum' AND jsonb_typeof(condition->'maximum') IS DISTINCT FROM 'string') THEN RAISE EXCEPTION 'closed relationship count required' USING ERRCODE='22023';END IF;
    selected:=truss.runtime_condition_type(condition->'anchor');objects:=jsonb_build_array(condition->'anchor');
    IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND (condition->>'direction'='outgoing' AND source_type=selected.type_id OR condition->>'direction'='incoming' AND target_type=selected.type_id)) THEN RAISE EXCEPTION 'admitted count anchor required' USING ERRCODE='22023';END IF;
    FOREACH bound IN ARRAY ARRAY[condition->>'minimum',CASE WHEN condition ? 'maximum' THEN condition->>'maximum' ELSE '9223372036854775807' END] LOOP
     IF bound IS NULL OR bound !~ '^(0|[1-9][0-9]{0,18})$' OR length(bound)=19 AND bound COLLATE "C">'9223372036854775807' THEN RAISE EXCEPTION 'exact bounded counts required' USING ERRCODE='22023';END IF;
    END LOOP;
    IF condition ? 'maximum' AND (condition->>'minimum')::bigint>(condition->>'maximum')::bigint THEN RAISE EXCEPTION 'ordered count bounds required' USING ERRCODE='22023';END IF;
   END IF;
  ELSE RAISE EXCEPTION 'known condition required' USING ERRCODE='22023';END IF;
  SELECT coalesce(jsonb_agg(value ORDER BY ord),'[]'::jsonb) INTO scopes FROM unnest(scope_entries) WITH ORDINALITY s(value,ord);
  FOR owner IN SELECT DISTINCT value->>'documentId' AS document_id,value->>'moduleId' AS module_id FROM jsonb_array_elements(scopes) LOOP
   IF NOT truss.runtime_can_read(owner.document_id,owner.module_id) THEN RAISE EXCEPTION 'current predicate owner read authority required' USING ERRCODE='42501';END IF;
  END LOOP;
  inventory_entries[cardinality(inventory_entries)+1]:=entry||jsonb_build_object('objects',objects,'scopes',scopes);index:=index+1;
 END LOOP;
 SELECT coalesce(jsonb_agg(value ORDER BY ord),'[]'::jsonb) INTO inventory FROM unnest(inventory_entries) WITH ORDINALITY i(value,ord);
 RETURN inventory;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_condition_inventory(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.group_condition_key_metadata(original_input bytea,original_documents bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE input jsonb;inventory jsonb;entry jsonb;archive truss.schema_doc%ROWTYPE;selected truss.type_def%ROWTYPE;source text;encoded bytea;
BEGIN
 PERFORM truss.group_context(expected_release,expected_digest);
 IF original_input IS NULL OR octet_length(original_input) NOT BETWEEN 1 AND 1048576 OR original_documents IS NULL OR octet_length(original_documents) NOT BETWEEN 1 AND 4194304 THEN RAISE EXCEPTION 'bounded condition source required' USING ERRCODE='54000';END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;inventory:=truss.runtime_condition_inventory(input);
 FOR entry IN SELECT value FROM jsonb_array_elements(inventory) WHERE value->'condition'->>'condition'='key_absent' LOOP
  SELECT * INTO STRICT selected FROM truss.type_def WHERE type_id=(entry->>'typeId')::int;
  SELECT * INTO STRICT archive FROM truss.schema_doc WHERE doc_id=selected.document_id ORDER BY rev DESC LIMIT 1;
  SELECT value->>'sourceText' INTO STRICT source FROM jsonb_array_elements(convert_from(original_documents,'UTF8')::jsonb) WHERE value->>'documentId'=archive.doc_id;
  IF convert_to(source,'UTF8') IS DISTINCT FROM convert_to(archive.document,'UTF8') THEN RAISE EXCEPTION 'original key document required' USING ERRCODE='22023';END IF;
 END LOOP;
 encoded:=convert_to((SELECT coalesce(jsonb_agg(value),'[]') FROM jsonb_array_elements(inventory) WHERE value->'condition'->>'condition'='key_absent')::text,'UTF8');
 PERFORM truss.runtime_condition_inventory(input);
 RETURN encoded;
END;
$$;
REVOKE ALL ON FUNCTION truss.group_condition_key_metadata(bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_evaluate_preconditions(input jsonb,original_keys bytea) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE inventory jsonb;entry jsonb;condition jsonb;owner record;target record;current_object truss.object%ROWTYPE;key_tuples bytea[];key_tuple bytea;
 installation truss.catalog_runtime_installation%ROWTYPE;pin record;ns bytea;transport bytea;tuple_bytes bytea;values_text text[];key_facets jsonb;observed record;passed boolean;counted bigint;
 failure_buffer jsonb[]:=ARRAY[]::jsonb[];failures jsonb;receipt jsonb;scope jsonb;
BEGIN
 inventory:=truss.runtime_condition_inventory(input);
 IF original_keys IS NULL OR octet_length(original_keys) NOT BETWEEN 1 AND 8388608 OR (convert_from(original_keys,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'original predicate key inventory required' USING ERRCODE='22023';END IF;
 IF convert_from(original_keys,'UTF8')::jsonb<>'[]'::jsonb THEN RAISE EXCEPTION 'client predicate key encoding is no longer accepted' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(inventory)>0 THEN key_tuples:=array_fill(NULL::bytea,ARRAY[jsonb_array_length(inventory)]);ELSE key_tuples:=ARRAY[]::bytea[];END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 -- Acquire the complete object cut before evaluating any predicate.
 FOR target IN SELECT DISTINCT (o.value->>'id')::bigint AS id,(o.value->>'typeId')::int AS type_id FROM jsonb_array_elements(inventory) e CROSS JOIN LATERAL jsonb_array_elements(e.value->'objects') o ORDER BY id,type_id LOOP
  PERFORM 1 FROM truss.object WHERE id=target.id AND type_id=target.type_id FOR UPDATE NOWAIT;
 END LOOP;
 FOR entry IN SELECT value FROM jsonb_array_elements(inventory) WHERE value->'condition'->>'condition'='key_absent' LOOP
  tuple_bytes:=truss.derive_catalog_key_tuple((entry->>'typeId')::int,(entry->>'keyNumber')::smallint,entry->'values');
  key_tuples[(entry->>'index')::int+1]:=tuple_bytes;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',(entry->>'typeId')::int,(entry->>'keyNumber')::int);
  ns:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,
   'typeId',entry->>'typeId','keyNumber',entry->>'keyNumber','definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
  transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');PERFORM truss.lock_string_key_bucket(ns,transport);
 END LOOP;
 FOR entry IN SELECT value FROM jsonb_array_elements(inventory) LOOP
  condition:=entry->'condition';passed:=false;
  IF condition->>'condition' IN ('object_exists','property_equals') THEN
   SELECT * INTO current_object FROM truss.object WHERE id=(condition->'target'->>'id')::bigint AND type_id=(condition->'target'->>'typeId')::int;
   IF FOUND THEN
    IF condition->>'condition'='object_exists' THEN passed:=true;
    ELSIF entry ? 'propertyId' THEN passed:=current_object.props ? (entry->>'propertyId') AND current_object.props->(entry->>'propertyId')=truss.canonical_flat_cell(condition->'value');
    ELSE passed:=coalesce(current_object.retained,'{}') ? (condition->>'name') AND current_object.retained->(condition->>'name')=truss.canonical_flat_cell(condition->'value');END IF;
   END IF;
  ELSIF condition->>'condition'='key_absent' THEN
   key_tuple:=key_tuples[(entry->>'index')::int+1];
   IF key_tuple IS NULL THEN RAISE EXCEPTION 'precondition key tuple missing' USING ERRCODE='55000';END IF;
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',(entry->>'typeId')::int,(entry->>'keyNumber')::int);
   ns:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,
    'typeId',entry->>'typeId','keyNumber',entry->>'keyNumber','definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   transport:=convert_to('umf-key-tuple-v1:hex:'||encode(key_tuple,'hex'),'UTF8');SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(ns,transport);
   passed:=cardinality(observed.member_ids)=0; -- Live absence; reservations remain an independent write rule.
  ELSIF condition->>'condition'='relationship_absent' THEN
   passed:=EXISTS(SELECT 1 FROM truss.object WHERE id=(condition->'source'->>'id')::bigint AND type_id=(condition->'source'->>'typeId')::int)
    AND EXISTS(SELECT 1 FROM truss.object WHERE id=(condition->'target'->>'id')::bigint AND type_id=(condition->'target'->>'typeId')::int)
    AND NOT EXISTS(SELECT 1 FROM truss.edge WHERE rel_type_id=(entry->>'relationshipId')::int AND source_id=(condition->'source'->>'id')::bigint AND source_type=(condition->'source'->>'typeId')::int AND target_id=(condition->'target'->>'id')::bigint AND target_type=(condition->'target'->>'typeId')::int);
  ELSE
   IF EXISTS(SELECT 1 FROM truss.object WHERE id=(condition->'anchor'->>'id')::bigint AND type_id=(condition->'anchor'->>'typeId')::int) THEN
    SELECT count(*) INTO counted FROM truss.edge WHERE rel_type_id=(entry->>'relationshipId')::int AND (condition->>'direction'='outgoing' AND source_id=(condition->'anchor'->>'id')::bigint AND source_type=(condition->'anchor'->>'typeId')::int OR condition->>'direction'='incoming' AND target_id=(condition->'anchor'->>'id')::bigint AND target_type=(condition->'anchor'->>'typeId')::int);
    passed:=counted>=(condition->>'minimum')::bigint AND (NOT condition ? 'maximum' OR counted<=(condition->>'maximum')::bigint);
   END IF;
  END IF;
  IF passed IS NOT TRUE THEN failure_buffer:=array_append(failure_buffer,jsonb_build_object('conditionId',condition->>'id','reason',condition->>'reason','rule',condition->>'condition'));END IF;
 END LOOP;
 -- A lost predicate authority never returns a partial or complete failure list.
 PERFORM truss.runtime_condition_inventory(input);
 failures:=to_jsonb(failure_buffer);
 IF failures<>'[]'::jsonb THEN RAISE EXCEPTION 'caller preconditions failed' USING ERRCODE='P1006',DETAIL=jsonb_build_object('outcome','failed','code','precondition_failed','failures',failures)::text;END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_evaluate_preconditions(jsonb,bytea) FROM PUBLIC;

CREATE FUNCTION truss.group_relationship_reference(selected_document text,selected_module text,selected_relationship text,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE relation truss.rel_def%ROWTYPE;owner record;pin text;encoded bytea;
BEGIN
 PERFORM truss.group_context(expected_release,expected_digest);
 IF selected_document IS NULL OR selected_module IS NULL OR selected_relationship IS NULL OR octet_length(selected_document) NOT BETWEEN 1 AND 4096 OR octet_length(selected_module) NOT BETWEEN 1 AND 4096 OR octet_length(selected_relationship) NOT BETWEEN 1 AND 4096 THEN RAISE EXCEPTION 'qualified bounded relationship selection required' USING ERRCODE='22023';END IF;
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 SELECT * INTO relation FROM truss.rel_def WHERE document_id=selected_document AND module=selected_module AND rel_id=selected_relationship AND retired_rev IS NULL;
 IF NOT FOUND THEN RETURN NULL;END IF;
 FOR owner IN SELECT DISTINCT t.document_id,t.module FROM truss.rel_endpoint e JOIN truss.type_def t ON t.type_id=e.source_type OR t.type_id=e.target_type WHERE e.rel_type_id=relation.rel_type_id LOOP
  IF NOT truss.runtime_can_read(owner.document_id,owner.module) THEN RETURN NULL;END IF;
 END LOOP;
 pin:=truss.runtime_relationship_pin(relation.rel_type_id);
 encoded:=convert_to(jsonb_build_object('kind','relationship','definitionPin',pin,'relationshipId',relation.rel_type_id::text,'authoredIdentity',relation.rel_id,
  'owner',jsonb_build_object('documentId',selected_document,'moduleId',selected_module))::text,'UTF8');
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 FOR owner IN SELECT DISTINCT t.document_id,t.module FROM truss.rel_endpoint e JOIN truss.type_def t ON t.type_id=e.source_type OR t.type_id=e.target_type WHERE e.rel_type_id=relation.rel_type_id LOOP
  IF NOT truss.runtime_can_read(owner.document_id,owner.module) THEN RETURN NULL;END IF;
 END LOOP;
 RETURN encoded;
END;
$$;
REVOKE ALL ON FUNCTION truss.group_relationship_reference(text,text,text,text,text) FROM PUBLIC;
