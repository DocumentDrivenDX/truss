-- This separate audit grant authorizes metadata-only disclosure over the full
-- retained owner union; it does not grant ordinary data reads.
CREATE FUNCTION truss.grant_import_audit_access(selected_document text,selected_module text,
 selected_auditor_role text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' AS $$
DECLARE actor record;installation truss.catalog_runtime_installation%ROWTYPE;auditor oid;has_owner boolean;
BEGIN
 SELECT r.oid,r.rolcanlogin,r.rolsuper,r.rolcreaterole,r.rolcreatedb,r.rolreplication,r.rolbypassrls,
  current_setting('role')='none' AS original_role INTO STRICT actor
  FROM pg_catalog.pg_roles r WHERE r.rolname=session_user;
 IF selected_document IS NULL OR selected_module IS NULL OR selected_auditor_role IS NULL
  OR octet_length(selected_document) NOT BETWEEN 1 AND 65536
  OR octet_length(selected_module) NOT BETWEEN 1 AND 65536
  OR octet_length(selected_auditor_role) NOT BETWEEN 1 AND 256
  OR actor.rolcanlogin IS NOT TRUE OR actor.original_role IS NOT TRUE
  OR NOT actor.rolsuper AND (NOT actor.rolcreaterole OR actor.rolcreatedb
   OR actor.rolreplication OR actor.rolbypassrls) THEN
  RAISE EXCEPTION 'qualified direct installation administrator and audit role required' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation WHERE singleton;
 IF NOT actor.rolsuper THEN
  WITH RECURSIVE inherited(role_oid) AS (
   SELECT actor.oid UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m
    JOIN inherited i ON m.member=i.role_oid WHERE m.inherit_option)
  SELECT EXISTS(SELECT 1 FROM inherited WHERE role_oid=installation.owner_oid) INTO has_owner;
  IF has_owner IS NOT TRUE THEN RAISE EXCEPTION 'installation owner administration required' USING ERRCODE='42501';END IF;
 END IF;
 SELECT r.oid INTO auditor FROM pg_catalog.pg_roles r WHERE r.rolname=selected_auditor_role
  AND NOT r.rolcanlogin AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole
  AND NOT r.rolreplication AND NOT r.rolbypassrls AND NOT r.rolinherit;
 IF auditor IS NULL OR NOT EXISTS(SELECT 1 FROM truss.module_access m
  WHERE m.document_id=selected_document AND m.module=selected_module
   AND m.reader_role IS DISTINCT FROM selected_auditor_role
   AND m.writer_role IS DISTINCT FROM selected_auditor_role) THEN
  RAISE EXCEPTION 'configured module audit role required' USING ERRCODE='22023';END IF;
 INSERT INTO truss.runtime_import_audit_access(document_id,module,auditor_oid,granted_by)
  VALUES(selected_document,selected_module,auditor,actor.oid)
  ON CONFLICT(document_id,module) DO UPDATE SET auditor_oid=EXCLUDED.auditor_oid,granted_by=EXCLUDED.granted_by;
 RETURN convert_to('{"outcome":"granted"}','UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.grant_import_audit_access(text,text,text) FROM PUBLIC;

-- `original_records` is rederived by the native chunk processor from the exact
-- original envelope. Only identity, source digests and the complete owner union
-- are retained; payload bytes are never copied into this audit relation.
CREATE FUNCTION truss.runtime_record_import_load(invocation uuid,chunk_no int,total_no int,
 selected_load_id text,origin_value jsonb,input_sha text,original_count int,
 original_records jsonb,chunk_records jsonb,chunk_outcomes jsonb,
 expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' AS $$
DECLARE actor oid;actor_name text;installation truss.catalog_runtime_installation%ROWTYPE;
 record_entry jsonb;record_value jsonb;outcome_entry jsonb;index_value text;kind_value text;
 owners jsonb:='[]'::jsonb;owner_entry jsonb;all_entries jsonb:='[]'::jsonb;identity_value jsonb;
 payload_digest text;payload_profile jsonb;group_attempt uuid;count_entries int;ordinal int:=0;
 origin_sha text;projected_identity jsonb;owner_inventory_complete boolean:=true;
 selected_type truss.type_def%ROWTYPE;selected_property truss.prop_def%ROWTYPE;type_metadata jsonb;
 prior truss.runtime_import_load_chunk%ROWTYPE;existing boolean;
BEGIN
 actor:=truss.runtime_person(false);
 SELECT r.rolname INTO actor_name FROM pg_catalog.pg_roles r WHERE r.oid=actor;
 IF actor_name IS NULL THEN RAISE EXCEPTION 'original native initiator name unavailable' USING ERRCODE='P1010';END IF;
 origin_sha:=encode(sha256(convert_to(origin_value::text,'UTF8')),'hex');
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest
  OR invocation IS NULL OR chunk_no IS NULL OR total_no IS NULL OR chunk_no<0 OR total_no NOT BETWEEN 1 AND 1024 OR chunk_no>=total_no
  OR selected_load_id IS NULL OR octet_length(selected_load_id) NOT BETWEEN 1 AND 4096
  OR origin_value IS NULL OR jsonb_typeof(origin_value) IS DISTINCT FROM 'object'
  OR input_sha IS NULL OR input_sha !~ '^[0-9a-f]{64}$'
  OR original_count IS NULL OR original_count NOT BETWEEN 0 AND 1024
  OR jsonb_typeof(original_records) IS DISTINCT FROM 'array'
  OR jsonb_array_length(original_records)<>original_count
  OR jsonb_typeof(chunk_records) IS DISTINCT FROM 'array'
  OR jsonb_typeof(chunk_outcomes) IS DISTINCT FROM 'array'
  OR jsonb_array_length(chunk_records)<>jsonb_array_length(chunk_outcomes)
  OR jsonb_array_length(chunk_records)>128 THEN
  RAISE EXCEPTION 'bounded exact original import load required' USING ERRCODE='22023';END IF;
 IF octet_length(convert_to(origin_value::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'original asserted import origin exceeds retained limit' USING ERRCODE='54000';END IF;

 -- Derive owner scope from every exact original record, including rejected or
 -- skipped records and siblings in later chunks. Unknown/malformed scope blocks
 -- audit rather than authorizing a partial prefix.
 FOR record_value IN SELECT value FROM jsonb_array_elements(original_records) LOOP
  BEGIN
  IF jsonb_typeof(record_value) IS DISTINCT FROM 'object' OR record_value-ARRAY['kind','identity','payload','payloadProfile']<>'{}'::jsonb
   OR record_value->>'kind' NOT IN ('object','edge') OR jsonb_typeof(record_value->'identity') IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'complete original load identity required' USING ERRCODE='22023';END IF;
  kind_value:=record_value->>'kind';identity_value:=record_value->'identity';
  IF kind_value='object' THEN
   IF jsonb_typeof(identity_value->'type') IS DISTINCT FROM 'object'
    OR jsonb_typeof(identity_value->'type'->'typeId') IS DISTINCT FROM 'string'
    OR jsonb_typeof(identity_value->'type'->'definitionPin') IS DISTINCT FROM 'string'
    OR jsonb_typeof(identity_value->'type'->'owner') IS DISTINCT FROM 'object'
    OR identity_value->'type'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
    OR length(identity_value->'type'->>'typeId')=10
      AND identity_value->'type'->>'typeId' COLLATE pg_catalog."C">'2147483647' THEN
    RAISE EXCEPTION 'complete original object owner required' USING ERRCODE='22023';END IF;
   owner_entry:=identity_value->'type'->'owner';
   IF owner_entry-ARRAY['documentId','moduleId']<>'{}'::jsonb OR jsonb_typeof(owner_entry->'documentId') IS DISTINCT FROM 'string'
    OR jsonb_typeof(owner_entry->'moduleId') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'complete qualified object owner required' USING ERRCODE='22023';END IF;
   SELECT t.* INTO selected_type FROM truss.type_def t JOIN truss.runtime_definition_source d
    ON d.rev=t.definition_rev AND d.ord=t.definition_doc_ord AND d.doc_id=t.definition_document_id
     AND d.module_id=t.module AND d.element_id=t.element AND d.kind='element' AND d.key_id=''
    WHERE t.type_id=(identity_value->'type'->>'typeId')::int AND t.kind='record' AND NOT t.provisional
     AND t.retired_rev IS NULL AND d.definition_pin=identity_value->'type'->>'definitionPin';
   IF NOT FOUND OR owner_entry IS DISTINCT FROM jsonb_build_object('documentId',selected_type.document_id,'moduleId',selected_type.module) THEN
    RAISE EXCEPTION 'exact original type owner required' USING ERRCODE='22023';END IF;
   owners:=owners||jsonb_build_array(owner_entry);
   -- Include all declaration/item owners reachable through this type. This is
   -- a conservative historical union and prevents metadata disclosure when an
   -- imported value depends on a hidden property module.
   FOR owner_entry IN SELECT DISTINCT jsonb_build_object('documentId',selected_type.document_id,'moduleId',p.declaration_module)
    FROM truss.prop_def p WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL LOOP
    owners:=owners||jsonb_build_array(owner_entry);
   END LOOP;
   FOR owner_entry IN SELECT DISTINCT jsonb_build_object('documentId',node.value->>'documentId',
     'moduleId',node.value->'reference'->>'module')
    FROM truss.prop_def p CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(p.item)||coalesce(p.item->'descendants','[]'::jsonb)) node(value)
    WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL AND node.value ? 'reference' LOOP
    IF owner_entry->>'documentId' IS NULL OR owner_entry->>'moduleId' IS NULL THEN
     RAISE EXCEPTION 'complete item owner required' USING ERRCODE='22023';END IF;
    owners:=owners||jsonb_build_array(owner_entry);
   END LOOP;
   SELECT s.metadata INTO type_metadata FROM truss.runtime_type_schema s
    WHERE s.rev=(SELECT rev FROM truss.schema_head WHERE id=1) AND s.type_id=selected_type.type_id;
   IF NOT FOUND OR jsonb_typeof(type_metadata->'propertyAccess') IS DISTINCT FROM 'object' THEN
    RAISE EXCEPTION 'complete original object property scope required' USING ERRCODE='22023';END IF;
   FOR owner_entry IN SELECT reader.value FROM jsonb_each(type_metadata->'propertyAccess') property
    CROSS JOIN LATERAL jsonb_array_elements(property.value->'readers') reader(value) LOOP
    IF jsonb_typeof(owner_entry) IS DISTINCT FROM 'object' OR owner_entry-ARRAY['documentId','moduleId']<>'{}'::jsonb THEN
     RAISE EXCEPTION 'complete original object reader required' USING ERRCODE='22023';END IF;
    owners:=owners||jsonb_build_array(owner_entry);
   END LOOP;
  ELSE
   FOR ordinal IN 1..2 LOOP
    IF ordinal=1 THEN owner_entry:=identity_value->'source'->'owner';
    ELSE owner_entry:=identity_value->'target'->'owner';END IF;
    IF jsonb_typeof(owner_entry) IS DISTINCT FROM 'object' OR owner_entry-ARRAY['documentId','moduleId']<>'{}'::jsonb
     OR jsonb_typeof(owner_entry->'documentId') IS DISTINCT FROM 'string' OR jsonb_typeof(owner_entry->'moduleId') IS DISTINCT FROM 'string' THEN
     RAISE EXCEPTION 'complete edge endpoint owner required' USING ERRCODE='22023';END IF;
    IF ordinal=1 AND (jsonb_typeof(identity_value->'source'->'typeId') IS DISTINCT FROM 'string'
      OR identity_value->'source'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
      OR length(identity_value->'source'->>'typeId')=10
       AND identity_value->'source'->>'typeId' COLLATE pg_catalog."C">'2147483647')
     OR ordinal=2 AND (jsonb_typeof(identity_value->'target'->'typeId') IS DISTINCT FROM 'string'
      OR identity_value->'target'->>'typeId' !~ '^[1-9][0-9]{0,9}$'
      OR length(identity_value->'target'->>'typeId')=10
       AND identity_value->'target'->>'typeId' COLLATE pg_catalog."C">'2147483647') THEN
     RAISE EXCEPTION 'bounded original edge endpoint type id required' USING ERRCODE='22023';END IF;
    IF ordinal=1 THEN SELECT t.* INTO selected_type FROM truss.type_def t JOIN truss.runtime_definition_source d
      ON d.rev=t.definition_rev AND d.ord=t.definition_doc_ord AND d.doc_id=t.definition_document_id AND d.module_id=t.module AND d.element_id=t.element
       AND d.kind='element' AND d.key_id='' WHERE t.type_id=(identity_value->'source'->'typeId')::int
       AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL AND d.definition_pin=identity_value->'source'->>'definitionPin';
    ELSE SELECT t.* INTO selected_type FROM truss.type_def t JOIN truss.runtime_definition_source d
      ON d.rev=t.definition_rev AND d.ord=t.definition_doc_ord AND d.doc_id=t.definition_document_id AND d.module_id=t.module AND d.element_id=t.element
       AND d.kind='element' AND d.key_id='' WHERE t.type_id=(identity_value->'target'->'typeId')::int
       AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL AND d.definition_pin=identity_value->'target'->>'definitionPin';END IF;
    IF NOT FOUND OR owner_entry IS DISTINCT FROM jsonb_build_object('documentId',selected_type.document_id,'moduleId',selected_type.module) THEN
     RAISE EXCEPTION 'exact original edge endpoint owner required' USING ERRCODE='22023';END IF;
    owners:=owners||jsonb_build_array(owner_entry);
    FOR owner_entry IN SELECT DISTINCT jsonb_build_object('documentId',selected_type.document_id,'moduleId',p.declaration_module)
     FROM truss.prop_def p WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL LOOP
     owners:=owners||jsonb_build_array(owner_entry);
    END LOOP;
    SELECT s.metadata INTO type_metadata FROM truss.runtime_type_schema s
     WHERE s.rev=(SELECT rev FROM truss.schema_head WHERE id=1) AND s.type_id=selected_type.type_id;
    IF NOT FOUND OR jsonb_typeof(type_metadata->'propertyAccess') IS DISTINCT FROM 'object' THEN
     RAISE EXCEPTION 'complete original endpoint property scope required' USING ERRCODE='22023';END IF;
    FOR owner_entry IN SELECT reader.value FROM jsonb_each(type_metadata->'propertyAccess') property
     CROSS JOIN LATERAL jsonb_array_elements(property.value->'readers') reader(value) LOOP
     IF jsonb_typeof(owner_entry) IS DISTINCT FROM 'object' OR owner_entry-ARRAY['documentId','moduleId']<>'{}'::jsonb THEN
      RAISE EXCEPTION 'complete original endpoint reader required' USING ERRCODE='22023';END IF;
     owners:=owners||jsonb_build_array(owner_entry);
    END LOOP;
   END LOOP;
   SELECT t.* INTO selected_type
    FROM truss.runtime_definition_source d JOIN truss.rel_def r
     ON r.definition_rev=d.rev AND r.definition_doc_ord=d.ord AND r.definition_document_id=d.doc_id
      AND r.module=d.module_id AND r.rel_id=d.element_id
    JOIN truss.type_def t ON t.type_id=r.assoc_type_id
    WHERE d.definition_pin=identity_value->>'relationshipDefinitionPin' AND d.kind='relationship'
     AND r.retired_rev IS NULL;
   IF NOT FOUND THEN RAISE EXCEPTION 'complete original relationship owner required' USING ERRCODE='22023';END IF;
   owner_entry:=jsonb_build_object('documentId',selected_type.document_id,'moduleId',selected_type.module);
   owners:=owners||jsonb_build_array(owner_entry);
   FOR owner_entry IN SELECT DISTINCT jsonb_build_object('documentId',selected_type.document_id,'moduleId',p.declaration_module)
    FROM truss.prop_def p WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL LOOP
    owners:=owners||jsonb_build_array(owner_entry);
   END LOOP;
   SELECT s.metadata INTO type_metadata FROM truss.runtime_type_schema s
    WHERE s.rev=(SELECT rev FROM truss.schema_head WHERE id=1) AND s.type_id=selected_type.type_id;
   IF NOT FOUND OR jsonb_typeof(type_metadata->'propertyAccess') IS DISTINCT FROM 'object' THEN
    RAISE EXCEPTION 'complete original association property scope required' USING ERRCODE='22023';END IF;
   FOR owner_entry IN SELECT reader.value FROM jsonb_each(type_metadata->'propertyAccess') property
    CROSS JOIN LATERAL jsonb_array_elements(property.value->'readers') reader(value) LOOP
    IF jsonb_typeof(owner_entry) IS DISTINCT FROM 'object' OR owner_entry-ARRAY['documentId','moduleId']<>'{}'::jsonb THEN
     RAISE EXCEPTION 'complete original association reader required' USING ERRCODE='22023';END IF;
    owners:=owners||jsonb_build_array(owner_entry);
   END LOOP;
  END IF;
  EXCEPTION WHEN SQLSTATE '22023' OR SQLSTATE '22P02' THEN
   owner_inventory_complete:=false;
  END;
 END LOOP;
 SELECT coalesce(jsonb_agg(value ORDER BY value->>'documentId',value->>'moduleId'),'[]'::jsonb) INTO owners
  FROM (SELECT DISTINCT value FROM jsonb_array_elements(owners)) unique_owner;
 IF jsonb_array_length(owners)>4096 THEN RAISE EXCEPTION 'load owner scope resource limit' USING ERRCODE='54000';END IF;

 FOR record_entry,outcome_entry IN SELECT r.value,o.value FROM jsonb_array_elements(chunk_records) WITH ORDINALITY r(value,ord)
  JOIN jsonb_array_elements(chunk_outcomes) WITH ORDINALITY o(value,ord) USING(ord) LOOP
  IF jsonb_typeof(record_entry) IS DISTINCT FROM 'object' OR record_entry-ARRAY['inputIndex','record']<>'{}'::jsonb
   OR jsonb_typeof(record_entry->'inputIndex') IS DISTINCT FROM 'string' OR jsonb_typeof(record_entry->'record') IS DISTINCT FROM 'object'
   OR jsonb_typeof(outcome_entry) IS DISTINCT FROM 'object' OR outcome_entry-ARRAY['inputIndex','outcome','groupAttemptId','identity','version','reason','code','path']<>'{}'::jsonb
   OR outcome_entry->>'inputIndex' IS DISTINCT FROM record_entry->>'inputIndex'
   OR outcome_entry->>'outcome' NOT IN ('created','skipped','rejected') THEN
   RAISE EXCEPTION 'exact chunk record and outcome pair required' USING ERRCODE='22023';END IF;
  index_value:=record_entry->>'inputIndex';
  IF index_value !~ '^(0|[1-9][0-9]{0,3})$' OR index_value::int>1023 OR index_value::int>=original_count THEN RAISE EXCEPTION 'canonical original load index required' USING ERRCODE='22023';END IF;
  record_value:=record_entry->'record';kind_value:=record_value->>'kind';identity_value:=record_value->'identity';
  payload_digest:=record_value->'payload'->>'sha256';payload_profile:=record_value->'payloadProfile';
  IF kind_value NOT IN ('object','edge') OR jsonb_typeof(identity_value) IS DISTINCT FROM 'object'
   OR jsonb_typeof(record_value->'payload') IS DISTINCT FROM 'object'
   OR jsonb_typeof(payload_profile) IS DISTINCT FROM 'object'
   OR payload_digest IS NULL OR payload_digest !~ '^[0-9a-f]{64}$'
   OR payload_profile-ARRAY['identity','version','sha256']<>'{}'::jsonb
   OR jsonb_typeof(payload_profile->'identity') IS DISTINCT FROM 'string' OR jsonb_typeof(payload_profile->'version') IS DISTINCT FROM 'string'
   OR jsonb_typeof(payload_profile->'sha256') IS DISTINCT FROM 'string' THEN
   owner_inventory_complete:=false;kind_value:='unknown';payload_digest:='';payload_profile:='{}'::jsonb;
   identity_value:=jsonb_build_object('kind','unknown');
  END IF;
  group_attempt:=NULL;
  IF outcome_entry->>'outcome'='created' THEN
   IF jsonb_typeof(outcome_entry->'groupAttemptId') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'created import attempt reference required' USING ERRCODE='22023';END IF;
   group_attempt:=(outcome_entry->>'groupAttemptId')::uuid;
   IF NOT EXISTS(SELECT 1 FROM truss.runtime_object_attempt a WHERE a.id=group_attempt AND a.complete)
    OR NOT EXISTS(SELECT 1 FROM truss.runtime_import_source s WHERE s.group_attempt_id=group_attempt) THEN
    RAISE EXCEPTION 'created native source ledger reference required' USING ERRCODE='22023';END IF;
  ELSIF outcome_entry ? 'groupAttemptId' THEN RAISE EXCEPTION 'only created outcomes have attempt reference' USING ERRCODE='22023';END IF;
  IF kind_value='object' THEN
   projected_identity:=jsonb_build_object('kind','object','typeId',identity_value->'type'->>'typeId',
    'definitionPin',identity_value->'type'->>'definitionPin','owner',identity_value->'type'->'owner',
    'keyNumber',identity_value->>'keyNumber','keyDefinitionPin',identity_value->>'keyDefinitionPin');
  ELSIF kind_value='edge' THEN
   projected_identity:=jsonb_build_object('kind','edge','relationshipDefinitionPin',identity_value->>'relationshipDefinitionPin',
    'source',jsonb_build_object('id',identity_value->'source'->>'id','typeId',identity_value->'source'->>'typeId',
     'definitionPin',identity_value->'source'->>'definitionPin','owner',identity_value->'source'->'owner'),
    'target',jsonb_build_object('id',identity_value->'target'->>'id','typeId',identity_value->'target'->>'typeId',
     'definitionPin',identity_value->'target'->>'definitionPin','owner',identity_value->'target'->'owner'));
  ELSE
   projected_identity:=jsonb_build_object('kind','unknown');
  END IF;
  all_entries:=all_entries||jsonb_build_array(jsonb_build_object(
   'inputIndex',index_value,'outcome',outcome_entry->>'outcome','recordKind',kind_value,
   'identity',projected_identity,'payloadProfile',payload_profile,'payloadSha256',payload_digest,
   'groupAttemptId',group_attempt));
 END LOOP;
 count_entries:=jsonb_array_length(all_entries);
 IF count_entries<>jsonb_array_length(chunk_records) THEN RAISE EXCEPTION 'complete chunk audit report required' USING ERRCODE='22023';END IF;
 SELECT * INTO prior FROM truss.runtime_import_load_chunk WHERE invocation_id=runtime_record_import_load.invocation
  ORDER BY chunk_index LIMIT 1;
  IF FOUND AND (prior.load_id IS DISTINCT FROM selected_load_id OR prior.original_asserted_origin IS DISTINCT FROM origin_value
  OR prior.asserted_origin_sha256 IS DISTINCT FROM origin_sha
  OR prior.input_sha256 IS DISTINCT FROM input_sha OR prior.input_count IS DISTINCT FROM original_count
  OR prior.total_chunks IS DISTINCT FROM total_no OR prior.native_actor IS DISTINCT FROM actor
  OR prior.native_actor_name IS DISTINCT FROM actor_name
  OR prior.original_owners IS DISTINCT FROM owners OR prior.owner_inventory_complete IS DISTINCT FROM owner_inventory_complete) THEN
  RAISE EXCEPTION 'conflicting original load invocation' USING ERRCODE='23505';END IF;
 SELECT * INTO prior FROM truss.runtime_import_load_chunk WHERE invocation_id=runtime_record_import_load.invocation
  AND chunk_index=chunk_no;
 IF FOUND THEN
  IF prior.total_chunks IS DISTINCT FROM total_no OR prior.load_id IS DISTINCT FROM selected_load_id
   OR prior.original_asserted_origin IS DISTINCT FROM origin_value
   OR prior.asserted_origin_sha256 IS DISTINCT FROM origin_sha OR prior.input_sha256 IS DISTINCT FROM input_sha
   OR prior.input_count IS DISTINCT FROM original_count OR prior.original_owners IS DISTINCT FROM owners
   OR prior.owner_inventory_complete IS DISTINCT FROM owner_inventory_complete
   OR prior.entries IS DISTINCT FROM all_entries OR prior.native_actor IS DISTINCT FROM actor
   OR prior.native_actor_name IS DISTINCT FROM actor_name THEN
   RAISE EXCEPTION 'conflicting repeated import load chunk' USING ERRCODE='23505';END IF;
 ELSE
  INSERT INTO truss.runtime_import_load_chunk(invocation_id,chunk_index,total_chunks,load_id,original_asserted_origin,asserted_origin_sha256,input_sha256,
   input_count,original_owners,owner_inventory_complete,entries,native_actor,native_actor_name,writer_xid)
  VALUES(invocation,chunk_no,total_no,selected_load_id,origin_value,origin_sha,input_sha,original_count,owners,owner_inventory_complete,all_entries,actor,actor_name,pg_current_xact_id());
 END IF;
 PERFORM truss.runtime_person(false);
 RETURN convert_to(jsonb_build_object('outcome','recorded','chunkIndex',chunk_no::text)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_record_import_load(uuid,int,int,text,jsonb,text,int,jsonb,jsonb,jsonb,text,text) FROM PUBLIC;

