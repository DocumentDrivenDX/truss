-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Advisory, condition-only observation. This path neither applies a group nor
-- acquires graph/key reservations and cannot issue a mutation receipt.
-- These preview companions are STABLE so their data reads share the calling
-- preview statement's snapshot. Authorization helpers remain VOLATILE and are
-- deliberately invoked at the original per-condition/release boundaries.
CREATE FUNCTION truss.runtime_condition_type_preview(identity jsonb) RETURNS truss.type_def
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected truss.type_def%ROWTYPE;pin text;type_number text;object_number text;
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
 SELECT d.definition_pin INTO STRICT pin FROM truss.runtime_definition_source d
  WHERE d.rev=selected.definition_rev AND d.ord=selected.definition_doc_ord AND d.doc_id=selected.definition_document_id
   AND d.module_id=selected.module AND d.element_id=selected.element AND d.kind='element' AND d.key_id='';
 IF identity->>'definitionPin' IS DISTINCT FROM pin OR identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module) THEN
  RAISE EXCEPTION 'current qualified condition definition required' USING ERRCODE='22023';END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_condition_type_preview(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_condition_key_tuple_preview(selected_type int,selected_key smallint,cells jsonb) RETURNS bytea
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE compiled jsonb;current_revision int;
BEGIN
 SELECT rev INTO STRICT current_revision FROM truss.schema_head WHERE id=1;
 SELECT metadata->'keyCodecs'->selected_key::text INTO compiled FROM truss.runtime_type_schema
  WHERE rev=current_revision AND type_id=selected_type
   AND NOT EXISTS(SELECT 1 FROM truss.schema_rev newer WHERE newer.rev>current_revision);
 IF compiled IS NULL THEN RAISE EXCEPTION 'selected compiled key codec required' USING ERRCODE='0A000';END IF;
 RETURN truss.runtime_owned_key_tuple_in_metadata(selected_type,selected_key,cells,compiled);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_condition_key_tuple_preview(int,smallint,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_condition_inventory_preview(input jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE conditions jsonb:=coalesce(input->'preconditions','[]');condition jsonb;selected truss.type_def%ROWTYPE;other truss.type_def%ROWTYPE;
 last_target jsonb;last_target_type truss.type_def%ROWTYPE;last_target_valid boolean:=false;
 relation truss.rel_def%ROWTYPE;property truss.prop_def%ROWTYPE;key_row truss.key_def%ROWTYPE;component record;owner record;pin text;
 inventory jsonb;inventory_entries jsonb[]:='{}';entry jsonb;objects jsonb;scopes jsonb;scope_entries jsonb[];scope_entry jsonb;identity jsonb;bound text;index int:=0;
BEGIN
 IF jsonb_typeof(conditions) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'condition array required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(conditions)>(CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN 3072 ELSE 128 END) THEN
  RAISE EXCEPTION 'condition count exceeds selected profile' USING ERRCODE='54000';END IF;
 IF jsonb_array_length(conditions)<>(SELECT count(DISTINCT value->>'id') FROM jsonb_array_elements(conditions)) THEN RAISE EXCEPTION 'unique condition IDs required' USING ERRCODE='22023';END IF;
 FOR condition IN SELECT value FROM jsonb_array_elements(conditions) LOOP
  IF jsonb_typeof(condition->'id') IS DISTINCT FROM 'string' OR octet_length(condition->>'id') NOT BETWEEN 1 AND 1024
   OR jsonb_typeof(condition->'reason') IS DISTINCT FROM 'string' OR octet_length(condition->>'reason')>4096 THEN RAISE EXCEPTION 'caller condition ID/reason required' USING ERRCODE='22023';END IF;
  objects:='[]';scope_entries:='{}';entry:=jsonb_build_object('index',index,'condition',condition);
  IF condition->>'condition' IN ('object_exists','property_equals') THEN
   IF condition-(CASE condition->>'condition' WHEN 'object_exists' THEN ARRAY['condition','id','reason','target'] ELSE ARRAY['condition','id','reason','target','name','value'] END)<>'{}'::jsonb THEN RAISE EXCEPTION 'closed object condition required' USING ERRCODE='22023';END IF;
   -- Repeated exact targets share immutable type metadata within this one
   -- inventory pass. Full identity equality retains the ID/owner/pin checks;
   -- authority is still checked for every condition below.
   IF last_target_valid AND last_target IS NOT DISTINCT FROM condition->'target' THEN selected:=last_target_type;
   ELSE
    selected:=truss.runtime_condition_type_preview(condition->'target');last_target:=condition->'target';last_target_type:=selected;last_target_valid:=true;
   END IF;
   objects:=jsonb_build_array(condition->'target');
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
   SELECT d.definition_pin INTO STRICT pin FROM truss.runtime_definition_source d
    WHERE d.rev=key_row.definition_rev AND d.ord=key_row.definition_doc_ord AND d.doc_id=key_row.definition_document_id
     AND d.module_id=selected.module AND d.element_id=selected.element AND d.kind='key' AND d.key_id=key_row.key_id;
   entry:=entry||jsonb_build_object('keyDefinitionPin',pin);
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
    selected:=truss.runtime_condition_type_preview(condition->'source');other:=truss.runtime_condition_type_preview(condition->'target');
    IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=selected.type_id AND target_type=other.type_id) THEN RAISE EXCEPTION 'admitted relationship endpoint types required' USING ERRCODE='22023';END IF;
    objects:=jsonb_build_array(condition->'source',condition->'target');
   ELSE
    IF condition-ARRAY['condition','id','reason','relationshipDefinitionPin','anchor','direction','minimum','maximum']<>'{}'::jsonb OR coalesce(condition->>'direction','') NOT IN ('outgoing','incoming') OR jsonb_typeof(condition->'minimum') IS DISTINCT FROM 'string' OR (condition ? 'maximum' AND jsonb_typeof(condition->'maximum') IS DISTINCT FROM 'string') THEN RAISE EXCEPTION 'closed relationship count required' USING ERRCODE='22023';END IF;
    selected:=truss.runtime_condition_type_preview(condition->'anchor');objects:=jsonb_build_array(condition->'anchor');
    IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND (condition->>'direction'='outgoing' AND source_type=selected.type_id OR condition->>'direction'='incoming' AND target_type=selected.type_id)) THEN RAISE EXCEPTION 'admitted count anchor required' USING ERRCODE='22023';END IF;
    FOREACH bound IN ARRAY ARRAY[condition->>'minimum',CASE WHEN condition ? 'maximum' THEN condition->>'maximum' ELSE '9223372036854775807' END] LOOP
     IF bound IS NULL OR bound !~ '^(0|[1-9][0-9]{0,18})$' OR length(bound)=19 AND bound COLLATE "C">'9223372036854775807' THEN RAISE EXCEPTION 'exact bounded counts required' USING ERRCODE='22023';END IF;
    END LOOP;
    IF condition ? 'maximum' AND (condition->>'minimum')::bigint>(condition->>'maximum')::bigint THEN RAISE EXCEPTION 'ordered count bounds required' USING ERRCODE='22023';END IF;
   END IF;
  ELSE RAISE EXCEPTION 'known condition required' USING ERRCODE='22023';END IF;
  SELECT coalesce(jsonb_agg(value ORDER BY ord),'[]'::jsonb) INTO scopes FROM unnest(scope_entries) WITH ORDINALITY s(value,ord);
  FOR owner IN SELECT DISTINCT value->>'documentId' AS document_id,value->>'moduleId' AS module_id FROM jsonb_array_elements(scopes) LOOP
   IF NOT truss.runtime_can_read(owner.document_id,owner.module_id) THEN RAISE EXCEPTION 'current predicate owner read authority required' USING ERRCODE='P1403';END IF;
  END LOOP;
  inventory_entries[cardinality(inventory_entries)+1]:=entry||jsonb_build_object('objects',objects,'scopes',scopes);index:=index+1;
 END LOOP;
 SELECT coalesce(jsonb_agg(value ORDER BY ord),'[]'::jsonb) INTO inventory FROM unnest(inventory_entries) WITH ORDINALITY i(value,ord);
 RETURN inventory;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_condition_inventory_preview(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_evaluate_preconditions_preview(input jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE inventory jsonb;entry jsonb;condition jsonb;owner record;target record;current_object truss.object%ROWTYPE;key_tuples bytea[];key_tuple bytea;
 installation truss.catalog_runtime_installation%ROWTYPE;pin record;ns bytea;transport bytea;tuple_bytes bytea;values_text text[];key_facets jsonb;observed record;passed boolean;counted bigint;
 failure_buffer jsonb[]:=ARRAY[]::jsonb[];condition_buffer jsonb[]:=ARRAY[]::jsonb[];failures jsonb;receipt jsonb;scope jsonb;
BEGIN
 inventory:=truss.runtime_condition_inventory_preview(input);
 IF jsonb_array_length(inventory)>0 THEN key_tuples:=array_fill(NULL::bytea,ARRAY[jsonb_array_length(inventory)]);ELSE key_tuples:=ARRAY[]::bytea[];END IF;
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation WHERE singleton;
 FOR entry IN SELECT value FROM jsonb_array_elements(inventory) WHERE value->'condition'->>'condition'='key_absent' LOOP
  tuple_bytes:=truss.runtime_condition_key_tuple_preview((entry->>'typeId')::int,(entry->>'keyNumber')::smallint,entry->'values');
  key_tuples[(entry->>'index')::int+1]:=tuple_bytes;
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
   ns:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,
    'typeId',entry->>'typeId','keyNumber',entry->>'keyNumber','definitionPin',entry->>'keyDefinitionPin','encoding','umf-key-tuple-v1')::text,'UTF8');
   transport:=convert_to('umf-key-tuple-v1:hex:'||encode(key_tuple,'hex'),'UTF8');
   passed:=cardinality(truss.runtime_peek_string_key_bucket(ns,transport))=0;
  ELSIF condition->>'condition'='relationship_absent' THEN
   passed:=EXISTS(SELECT 1 FROM truss.object WHERE id=(condition->'source'->>'id')::bigint AND type_id=(condition->'source'->>'typeId')::int)
    AND EXISTS(SELECT 1 FROM truss.object WHERE id=(condition->'target'->>'id')::bigint AND type_id=(condition->'target'->>'typeId')::int)
    AND NOT EXISTS(SELECT 1 FROM truss.edge WHERE rel_type_id=(entry->>'relationshipId')::int AND source_id=(condition->'source'->>'id')::bigint AND source_type=(condition->'source'->>'typeId')::int AND target_id=(condition->'target'->>'id')::bigint AND target_type=(condition->'target'->>'typeId')::int);
  ELSE
   IF EXISTS(SELECT 1 FROM truss.object WHERE id=(condition->'anchor'->>'id')::bigint AND type_id=(condition->'anchor'->>'typeId')::int) THEN
    -- Keep predicate witnesses bounded and each endpoint probe indexable.
    IF condition->>'direction'='outgoing' THEN
     SELECT count(*) INTO counted FROM (
      SELECT 1 FROM truss.edge WHERE rel_type_id=(entry->>'relationshipId')::int
       AND source_id=(condition->'anchor'->>'id')::bigint AND source_type=(condition->'anchor'->>'typeId')::int
      LIMIT CASE WHEN NOT condition ? 'maximum' OR (condition->>'maximum')::bigint=9223372036854775807 THEN (condition->>'minimum')::bigint ELSE (condition->>'maximum')::bigint+1 END
     ) matching_edges;
    ELSE
     SELECT count(*) INTO counted FROM (
      SELECT 1 FROM truss.edge WHERE rel_type_id=(entry->>'relationshipId')::int
       AND target_id=(condition->'anchor'->>'id')::bigint AND target_type=(condition->'anchor'->>'typeId')::int
      LIMIT CASE WHEN NOT condition ? 'maximum' OR (condition->>'maximum')::bigint=9223372036854775807 THEN (condition->>'minimum')::bigint ELSE (condition->>'maximum')::bigint+1 END
     ) matching_edges;
    END IF;
    passed:=counted>=(condition->>'minimum')::bigint AND (NOT condition ? 'maximum' OR counted<=(condition->>'maximum')::bigint);
   END IF;
  END IF;
  condition_buffer:=array_append(condition_buffer,jsonb_build_object('conditionId',condition->>'id','rule',condition->>'condition','passed',passed IS TRUE));
  IF passed IS NOT TRUE THEN failure_buffer:=array_append(failure_buffer,jsonb_build_object('conditionId',condition->>'id','reason',condition->>'reason','rule',condition->>'condition'));END IF;
 END LOOP;
 -- A lost predicate authority never returns a partial or complete failure list.
 PERFORM truss.runtime_condition_inventory_preview(input);
 failures:=to_jsonb(failure_buffer);
 RETURN jsonb_build_object('conditions',to_jsonb(condition_buffer),'failures',failures);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_evaluate_preconditions_preview(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_preview_truth_snapshot(input jsonb,documents jsonb,
 expected_release text,expected_digest text) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE selected truss.catalog_runtime_installation%ROWTYPE;inventory jsonb;observed jsonb;
 revision int;archive truss.schema_doc%ROWTYPE;original_source text;condition_entry jsonb;
BEGIN
 SELECT * INTO STRICT selected FROM truss.catalog_runtime_installation WHERE singleton;
 IF selected.release_id IS DISTINCT FROM expected_release OR selected.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected installed preview runtime required' USING ERRCODE='0A000';END IF;
 IF input-ARRAY['interfaceVersion','layoutProfile','mutationProfile','valueProfile','catalog','preconditions']<>'{}'::jsonb
  OR input->>'interfaceVersion' IS DISTINCT FROM 'truss-group-condition-preview/0.1.0'
  OR input->'catalog' IS DISTINCT FROM '{"selection":"current"}'::jsonb
  OR jsonb_typeof(input->'preconditions') IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'selected current condition preview profile required' USING ERRCODE='0A000';END IF;
 IF jsonb_array_length(input->'preconditions')<1 THEN
  RAISE EXCEPTION 'nonempty condition preview required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(input->'preconditions')>3072 THEN
  RAISE EXCEPTION 'condition preview exceeds limits' USING ERRCODE='54000';END IF;
 IF input->'layoutProfile' IS DISTINCT FROM selected.layout_profile
  OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_group_profiles()->'mutationProfile'
  OR input->'valueProfile' IS DISTINCT FROM truss.runtime_group_profiles()->'valueProfile' THEN
  RAISE EXCEPTION 'selected current condition preview profile required' USING ERRCODE='0A000';END IF;
 -- All catalog, source, and predicate reads below run under this one STABLE
 -- statement snapshot. Initial inventory keeps per-condition validation and
 -- authorization precedence; the VOLATILE wrapper rechecks the returned
 -- server-created scope inventory before exposing any result.
 inventory:=truss.runtime_condition_inventory_preview(input);
 FOR condition_entry IN SELECT value FROM jsonb_array_elements(input->'preconditions')
  WHERE value->>'condition'='key_absent' LOOP
  SELECT * INTO STRICT archive FROM truss.schema_doc
   WHERE doc_id=(SELECT selected_type.document_id FROM truss.type_def selected_type
    WHERE selected_type.type_id=(SELECT (entry.value->>'typeId')::int FROM jsonb_array_elements(inventory) entry
     WHERE entry.value->'condition'->>'id'=condition_entry->>'id'))
   ORDER BY rev DESC LIMIT 1;
  SELECT d.value->>'sourceText' INTO STRICT original_source FROM jsonb_array_elements(documents) d
   WHERE d.value->>'documentId'=archive.doc_id;
  IF convert_to(original_source,'UTF8') IS DISTINCT FROM convert_to(archive.document,'UTF8') THEN
   RAISE EXCEPTION 'exact original key condition source required' USING ERRCODE='22023';END IF;
 END LOOP;
 PERFORM truss.runtime_condition_inventory_preview(input);
 SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 IF revision<1 THEN RAISE EXCEPTION 'accepted preview catalog required' USING ERRCODE='0A000';END IF;
 observed:=truss.runtime_evaluate_preconditions_preview(input);
 RETURN jsonb_build_object('inventory',inventory,'conditions',observed->'conditions',
  'catalogRevision',revision::text,'snapshot',pg_current_snapshot()::text,
  'sourceEpoch',selected.source_epoch::text,'releaseId',selected.release_id,
  'releaseSha256',selected.release_sha256,'layoutProfile',selected.layout_profile);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_preview_truth_snapshot(jsonb,jsonb,text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_preview_recheck_authority(inventory jsonb,qualified_actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE entry jsonb;scope jsonb;
BEGIN
 IF jsonb_typeof(inventory) IS DISTINCT FROM 'array' OR qualified_actor IS NULL THEN
  RAISE EXCEPTION 'trusted preview inventory required' USING ERRCODE='55000';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(inventory) LOOP
  IF jsonb_typeof(entry->'scopes') IS DISTINCT FROM 'array' THEN
   RAISE EXCEPTION 'complete preview scopes required' USING ERRCODE='55000';END IF;
  FOR scope IN SELECT value FROM jsonb_array_elements(entry->'scopes') LOOP
   IF jsonb_typeof(scope) IS DISTINCT FROM 'object'
    OR scope-ARRAY['documentId','moduleId']<>'{}'::jsonb
    OR jsonb_typeof(scope->'documentId') IS DISTINCT FROM 'string'
    OR jsonb_typeof(scope->'moduleId') IS DISTINCT FROM 'string'
    OR octet_length(scope->>'documentId') NOT BETWEEN 1 AND 4096
    OR octet_length(scope->>'moduleId') NOT BETWEEN 1 AND 4096 THEN
    RAISE EXCEPTION 'complete preview scope required' USING ERRCODE='55000';END IF;
   IF NOT truss.runtime_can_read_qualified(scope->>'documentId',scope->>'moduleId',qualified_actor) THEN
    RAISE EXCEPTION 'current preview owner read authority required' USING ERRCODE='P1403';END IF;
  END LOOP;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_preview_recheck_authority(jsonb,oid) FROM PUBLIC;

CREATE FUNCTION truss.preview_group_conditions(original_input bytea,original_documents bytea,
 expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE input jsonb;documents jsonb;truth jsonb;actor oid;current_revision int;
 current_installation truss.catalog_runtime_installation%ROWTYPE;
BEGIN
 actor:=truss.runtime_person(false);
 IF original_input IS NULL OR octet_length(original_input)<1
  OR original_documents IS NULL OR octet_length(original_documents)<1 THEN
  RAISE EXCEPTION 'bounded original condition preview required' USING ERRCODE='22023';END IF;
 IF octet_length(original_input)>1048576 OR octet_length(original_documents)>4194304 THEN
  RAISE EXCEPTION 'condition preview source exceeds limits' USING ERRCODE='54000';END IF;
 IF (convert_from(original_input,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  OR (convert_from(original_documents,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'unique original condition preview JSON required' USING ERRCODE='22023';END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;documents:=convert_from(original_documents,'UTF8')::jsonb;
 IF jsonb_typeof(documents) IS DISTINCT FROM 'array' OR jsonb_array_length(documents)<1 THEN
  RAISE EXCEPTION 'original condition documents required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(documents)>512 THEN
  RAISE EXCEPTION 'original condition documents exceed limits' USING ERRCODE='54000';END IF;
 IF EXISTS(
  SELECT 1 FROM jsonb_array_elements(documents) d
   WHERE jsonb_typeof(d.value) IS DISTINCT FROM 'object'
    OR d.value-ARRAY['documentId','sourceText']<>'{}'::jsonb
    OR jsonb_typeof(d.value->'documentId') IS DISTINCT FROM 'string'
    OR octet_length(d.value->>'documentId') NOT BETWEEN 1 AND 4096
    OR jsonb_typeof(d.value->'sourceText') IS DISTINCT FROM 'string')
  OR jsonb_array_length(documents)<>(SELECT count(DISTINCT d.value->>'documentId') FROM jsonb_array_elements(documents) d) THEN
  RAISE EXCEPTION 'complete unique original preview documents required' USING ERRCODE='22023';END IF;
 -- The helper is one STABLE SQL statement: every metadata/source/data read and
 -- the reported snapshot token therefore share exactly one MVCC basis.
 SELECT truss.runtime_preview_truth_snapshot(input,documents,expected_release,expected_digest) INTO STRICT truth;
 PERFORM truss.runtime_preview_recheck_authority(truth->'inventory',actor);
 SELECT * INTO STRICT current_installation FROM truss.catalog_runtime_installation WHERE singleton;
 SELECT rev INTO STRICT current_revision FROM truss.schema_head WHERE id=1;
 IF current_installation.release_id IS DISTINCT FROM truth->>'releaseId'
  OR current_installation.release_sha256 IS DISTINCT FROM truth->>'releaseSha256'
  OR current_installation.source_epoch::text IS DISTINCT FROM truth->>'sourceEpoch'
  OR current_revision::text IS DISTINCT FROM truth->>'catalogRevision' THEN
  RAISE EXCEPTION 'observed preview basis changed before release' USING ERRCODE='55P03';END IF;
 IF truss.runtime_person(false) IS DISTINCT FROM actor THEN RAISE EXCEPTION 'current preview person required' USING ERRCODE='P1403';END IF;
 RETURN convert_to(jsonb_build_object('outcome','observed','conditions',truth->'conditions',
  'basis',jsonb_build_object('catalogRevision',truth->'catalogRevision','snapshot',truth->'snapshot',
   'sourceEpoch',truth->'sourceEpoch','releaseId',truth->'releaseId','releaseSha256',truth->'releaseSha256',
   'layoutProfile',truth->'layoutProfile'))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.preview_group_conditions(bytea,bytea,text,text) FROM PUBLIC;
