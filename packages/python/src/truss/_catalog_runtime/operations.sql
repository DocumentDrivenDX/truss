-- Public scalar object operations. Progress is internal to one host savepoint.
CREATE TABLE truss.runtime_object_attempt (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),writer_xid xid8 NOT NULL,actor_oid oid NOT NULL,
 input_bytes bytea NOT NULL,documents_bytes bytea NOT NULL,request_bytes bytea NOT NULL,
 context jsonb NOT NULL,next_index int NOT NULL DEFAULT 0,results jsonb NOT NULL DEFAULT '[]',aliases jsonb NOT NULL DEFAULT '[]',
 complete boolean NOT NULL DEFAULT false,receipt_id bigint,expected_receipt jsonb,position_bytes bytea,
 result_count int GENERATED ALWAYS AS (pg_catalog.jsonb_array_length(results)) STORED,
 CHECK(octet_length(input_bytes) BETWEEN 1 AND 1048576),CHECK(octet_length(documents_bytes) BETWEEN 1 AND 4194304),
 CHECK(octet_length(request_bytes) BETWEEN 1 AND 65536),CHECK(next_index BETWEEN 0 AND 1024));
CREATE INDEX runtime_object_attempt_writer ON truss.runtime_object_attempt(writer_xid);
CREATE UNIQUE INDEX runtime_object_attempt_receipt ON truss.runtime_object_attempt(receipt_id) WHERE receipt_id IS NOT NULL;
CREATE SEQUENCE truss.runtime_object_transition_seq;
CREATE TABLE truss.runtime_object_transition (transition_id bigint PRIMARY KEY DEFAULT nextval('truss.runtime_object_transition_seq'), attempt_id uuid NOT NULL REFERENCES truss.runtime_object_attempt (id), operation_index int NOT NULL, writer_xid xid8 NOT NULL, object_id bigint NOT NULL, type_id int NOT NULL, before_object jsonb, after_object jsonb, after_keys jsonb NOT NULL, journal jsonb NOT NULL, UNIQUE (attempt_id, operation_index, object_id, type_id));
CREATE INDEX runtime_object_transition_owner ON truss.runtime_object_transition(object_id,type_id,transition_id DESC);
CREATE INDEX runtime_object_transition_writer ON truss.runtime_object_transition(writer_xid);
CREATE TRIGGER runtime_object_transition_immutable BEFORE UPDATE OR DELETE ON truss.runtime_object_transition
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();

CREATE FUNCTION truss.runtime_owned_operation_type_qualified(operation jsonb,operations jsonb,operation_index int,qualified_actor oid) RETURNS truss.type_def
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE pin text;identity jsonb;creation jsonb;selected truss.type_def%ROWTYPE;
BEGIN
 IF operation->>'operation'='create_object' THEN pin:=operation->>'typeDefinitionPin';
 ELSIF operation->>'operation' IN ('update_object','delete_object') THEN
  IF operation->'target'->>'state'='stored' THEN
   identity:=operation->'target'->'identity';pin:=identity->>'definitionPin';
  ELSIF operation->'target'->>'state'='alias' THEN
   SELECT value INTO STRICT creation FROM jsonb_array_elements(operations) WITH ORDINALITY x(value,ord)
    WHERE ord<=operation_index AND value->>'operation'='create_object' AND value->>'alias'=operation->'target'->>'alias';
   pin:=creation->>'typeDefinitionPin';
  ELSE RAISE EXCEPTION 'stored or prior alias target required' USING ERRCODE='22023';END IF;
 ELSE RAISE EXCEPTION 'selected object operation required' USING ERRCODE='0A000';END IF;
 -- Stored targets already carry their exact native type coordinate. Resolve
 -- that candidate before deriving pins for unrelated catalog records.
 IF identity IS NOT NULL THEN
  WITH pinned AS MATERIALIZED (
   SELECT rev,ord,doc_id,module_id,element_id FROM truss.runtime_definition_source
   WHERE definition_pin=pin AND kind='element' AND key_id='')
  SELECT t.* INTO selected FROM pinned p JOIN truss.type_def t
    ON t.definition_rev=p.rev AND t.definition_doc_ord=p.ord AND t.definition_document_id=p.doc_id
     AND t.module=p.module_id AND t.element=p.element_id
   WHERE t.type_id::text=identity->>'typeId'
    AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL;
 END IF;
 IF selected.type_id IS NULL THEN
  -- Preserve original CREATE/alias lookup and stored-identity refusal precedence.
  WITH pinned AS MATERIALIZED (
   SELECT rev,ord,doc_id,module_id,element_id FROM truss.runtime_definition_source
   WHERE definition_pin=pin AND kind='element' AND key_id='')
  SELECT t.* INTO STRICT selected FROM pinned p JOIN truss.type_def t
    ON t.definition_rev=p.rev AND t.definition_doc_ord=p.ord AND t.definition_document_id=p.doc_id
     AND t.module=p.module_id AND t.element=p.element_id
   WHERE t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL;
 END IF;
 IF identity IS NOT NULL AND (identity->>'typeId' IS DISTINCT FROM selected.type_id::text
  OR identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module)
  OR identity-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb
  OR jsonb_typeof(identity->'id') IS DISTINCT FROM 'string' OR identity->>'id' !~ '^[1-9][0-9]{0,18}$'
  OR length(identity->>'id')=19 AND (identity->>'id') COLLATE "C">'9223372036854775807') THEN
  RAISE EXCEPTION 'qualified exact object identity required' USING ERRCODE='22023';END IF;
 IF NOT truss.runtime_object_values_readable_qualified(selected.type_id,qualified_actor) THEN RAISE EXCEPTION 'current property and item interpretation reader required' USING ERRCODE='42501';END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_operation_type_qualified(jsonb,jsonb,int,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_operation_type(operation jsonb,operations jsonb,operation_index int) RETURNS truss.type_def
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN truss.runtime_owned_operation_type_qualified(operation,operations,operation_index,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_operation_type(jsonb,jsonb,int) FROM PUBLIC;

-- Edge identities are relationship-qualified, never record-type-qualified.
CREATE FUNCTION truss.runtime_operation_relationship(operation jsonb,operations jsonb,operation_index int) RETURNS truss.rel_def
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE pin text;identity jsonb;creation jsonb;selected truss.rel_def%ROWTYPE;
BEGIN
 IF operation->>'operation'='create_edge' THEN pin:=operation->>'relationshipDefinitionPin';
 ELSIF operation->>'operation' IN ('update_edge','delete_edge') THEN
  IF operation->'target'->>'state'='stored' THEN
   identity:=operation->'target'->'identity';pin:=identity->>'definitionPin';
  ELSIF operation->'target'->>'state'='alias' THEN
   IF (SELECT count(*) FROM jsonb_array_elements(operations) WITH ORDINALITY x(value,ord)
    WHERE ord<=operation_index AND value->>'operation'='create_edge' AND value->>'alias'=operation->'target'->>'alias')<>1 THEN
    RAISE EXCEPTION 'one prior edge alias required' USING ERRCODE='22023';END IF;
   SELECT value INTO STRICT creation FROM jsonb_array_elements(operations) WITH ORDINALITY x(value,ord)
    WHERE ord<=operation_index AND value->>'operation'='create_edge' AND value->>'alias'=operation->'target'->>'alias';
   pin:=creation->>'relationshipDefinitionPin';
  ELSE RAISE EXCEPTION 'stored or prior edge alias target required' USING ERRCODE='22023';END IF;
 ELSE RAISE EXCEPTION 'selected edge operation required' USING ERRCODE='22023';END IF;
 -- Resolve the exact pin before joining source coordinates. Without this
 -- boundary a cold catalog plan can scan every relationship and repeatedly
 -- probe all source rows from the same document for each candidate.
 WITH pinned AS MATERIALIZED (
  SELECT rev,ord,doc_id,module_id,element_id FROM truss.runtime_definition_source
  WHERE definition_pin=pin AND kind='relationship' AND key_id='')
 SELECT r.* INTO STRICT selected FROM pinned p JOIN truss.rel_def r
  ON r.definition_rev=p.rev AND r.definition_doc_ord=p.ord AND r.definition_document_id=p.doc_id
   AND r.module=p.module_id AND r.rel_id=p.element_id
  WHERE r.retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'accepted relationship pin required' USING ERRCODE='22023';END IF;
 IF identity IS NOT NULL AND (jsonb_typeof(identity->'typeId') IS DISTINCT FROM 'string'
  OR jsonb_typeof(identity->'definitionPin') IS DISTINCT FROM 'string'
  OR identity->>'typeId' IS DISTINCT FROM selected.rel_type_id::text
  OR identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',selected.document_id,'moduleId',selected.module)
  OR identity-ARRAY['id','typeId','definitionPin','owner']<>'{}'::jsonb
  OR jsonb_typeof(identity->'id') IS DISTINCT FROM 'string' OR identity->>'id' !~ '^[1-9][0-9]{0,18}$'
  OR length(identity->>'id')=19 AND (identity->>'id') COLLATE "C">'9223372036854775807') THEN
  RAISE EXCEPTION 'qualified exact edge identity required' USING ERRCODE='22023';END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_operation_relationship(jsonb,jsonb,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_operation_owner_qualified(operation jsonb,operations jsonb,operation_index int,qualified_actor oid)
RETURNS TABLE(document_id text,module text,definition_rev int,definition_doc_ord int,definition_document_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE object_type truss.type_def%ROWTYPE;relationship truss.rel_def%ROWTYPE;
BEGIN
 IF operation->>'operation' IN ('create_object','update_object','delete_object') THEN
  object_type:=truss.runtime_owned_operation_type_qualified(operation,operations,operation_index,qualified_actor);
  RETURN QUERY SELECT object_type.document_id,object_type.module,object_type.definition_rev,object_type.definition_doc_ord,object_type.definition_document_id;
 ELSE
  relationship:=truss.runtime_operation_relationship(operation,operations,operation_index);
  RETURN QUERY SELECT relationship.document_id,relationship.module,relationship.definition_rev,relationship.definition_doc_ord,relationship.definition_document_id;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_operation_owner_qualified(jsonb,jsonb,int,oid) FROM PUBLIC;
CREATE FUNCTION truss.runtime_operation_owner(operation jsonb,operations jsonb,operation_index int)
RETURNS TABLE(document_id text,module text,definition_rev int,definition_doc_ord int,definition_document_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE object_type truss.type_def%ROWTYPE;relationship truss.rel_def%ROWTYPE;
BEGIN
 IF operation->>'operation' IN ('create_object','update_object','delete_object') THEN
  object_type:=truss.runtime_operation_type(operation,operations,operation_index);
  RETURN QUERY SELECT object_type.document_id,object_type.module,object_type.definition_rev,object_type.definition_doc_ord,object_type.definition_document_id;
 ELSE
  relationship:=truss.runtime_operation_relationship(operation,operations,operation_index);
  RETURN QUERY SELECT relationship.document_id,relationship.module,relationship.definition_rev,relationship.definition_doc_ord,relationship.definition_document_id;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_operation_owner(jsonb,jsonb,int) FROM PUBLIC;

-- Original completed results retain operation ownership across definition updates.
-- Invocation-local decoded replay frame; no retained authority or public input.
CREATE FUNCTION truss.runtime_owned_retained_operation_frame(operation jsonb,result jsonb,original_revision text,original_basis jsonb,qualified_actor oid)
RETURNS TABLE(document_id text,module text,historical_basis jsonb)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE identity jsonb;owner_document text;owner_module text;revision int;basis jsonb:=original_basis;property truss.prop_def%ROWTYPE;
BEGIN
 identity:=result->'identity';
 IF result->>'operation' IS DISTINCT FROM operation->>'operation' OR jsonb_typeof(identity->'typeId') IS DISTINCT FROM 'string'
  THEN RAISE EXCEPTION 'retained operation identity required' USING ERRCODE='55000';END IF;
 IF operation->>'operation' IN ('create_object','update_object','delete_object') THEN
  SELECT t.document_id,t.module INTO STRICT owner_document,owner_module FROM truss.type_def t WHERE t.type_id=(identity->>'typeId')::int AND t.kind='record';
  revision:=original_revision::int;
  IF revision IS NULL OR revision<1 THEN RAISE EXCEPTION 'positive original executed revision required' USING ERRCODE='55000';END IF;
  IF basis IS NULL THEN basis:=truss.catalog_all_expected_records(revision);END IF;
  FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=(identity->>'typeId')::int AND p.retired_rev IS NULL LOOP
   IF NOT truss.runtime_can_read_qualified(property.definition_document_id,property.declaration_module,qualified_actor) OR (property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable_qualified(property.item,qualified_actor) IS NOT TRUE) THEN RAISE EXCEPTION 'current retained property/item reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 ELSIF operation->>'operation' IN ('create_edge','update_edge','delete_edge') THEN
  SELECT r.document_id,r.module INTO STRICT owner_document,owner_module FROM truss.rel_def r WHERE r.rel_type_id=(identity->>'typeId')::int;
 ELSE RAISE EXCEPTION 'retained operation category required' USING ERRCODE='55000';END IF;
 IF identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',owner_document,'moduleId',owner_module) THEN
  RAISE EXCEPTION 'retained owner correspondence required' USING ERRCODE='55000';END IF;
 RETURN QUERY SELECT owner_document,owner_module,basis;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_retained_operation_frame(jsonb,jsonb,text,jsonb,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_retained_operation_owner(selected_attempt uuid,operation_index int)
RETURNS TABLE(document_id text,module text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;operation jsonb;result jsonb;identity jsonb;owner_document text;owner_module text;revision int;basis jsonb;property truss.prop_def%ROWTYPE;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 IF NOT attempt.complete OR operation_index<0 OR operation_index>=attempt.next_index
  OR jsonb_array_length(attempt.results)<>attempt.next_index THEN RAISE EXCEPTION 'complete retained operation required' USING ERRCODE='55000';END IF;
 operation:=convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations'->operation_index;
 result:=attempt.results->operation_index;identity:=result->'identity';
 IF result->>'operation' IS DISTINCT FROM operation->>'operation' OR jsonb_typeof(identity->'typeId') IS DISTINCT FROM 'string'
  THEN RAISE EXCEPTION 'retained operation identity required' USING ERRCODE='55000';END IF;
 IF operation->>'operation' IN ('create_object','update_object','delete_object') THEN
  SELECT t.document_id,t.module INTO STRICT owner_document,owner_module FROM truss.type_def t WHERE t.type_id=(identity->>'typeId')::int AND t.kind='record';
  revision:=((convert_from(decode(substr(attempt.expected_receipt->>'original_receipt_bytes',3),'hex'),'UTF8')::jsonb)->'semantic'->>'executedCatalogRevision')::int;
  IF attempt.expected_receipt IS NULL AND operation->>'operation'='create_object' THEN
   IF attempt.context->'creationTransitionProfile'='{"identity":"truss-unified-create-transition","version":"0.2","sha256":"073782e2517f2a7e26c8d6479c6266ececf68963681ccfb6a380e9cd16f2e11b"}'::jsonb THEN
    SELECT (t.after_object->>'rev')::int INTO STRICT revision FROM truss.runtime_object_transition t
     WHERE t.attempt_id=attempt.id AND t.operation_index=runtime_retained_operation_owner.operation_index AND t.before_object IS NULL;
   ELSE
   SELECT (g.expected_members->m.operation_index->'object'->>'rev')::int INTO STRICT revision FROM truss.runtime_create_member m JOIN truss.runtime_create_group g ON g.group_id=m.group_id WHERE m.object_id=(identity->>'id')::bigint AND m.type_id=(identity->>'typeId')::int AND g.writer_xid=attempt.writer_xid;
   END IF;
  END IF;
  IF revision IS NULL OR revision<1 THEN RAISE EXCEPTION 'positive original executed revision required' USING ERRCODE='55000';END IF;
  basis:=truss.catalog_all_expected_records(revision);
  FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=(identity->>'typeId')::int AND p.retired_rev IS NULL LOOP
   IF NOT truss.runtime_can_read(property.definition_document_id,property.declaration_module) OR (property.cardinality IN ('array','map') AND truss.runtime_item_chain_readable(property.item) IS NOT TRUE) THEN RAISE EXCEPTION 'current retained property/item reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 ELSIF operation->>'operation' IN ('create_edge','update_edge','delete_edge') THEN
  SELECT r.document_id,r.module INTO STRICT owner_document,owner_module FROM truss.rel_def r WHERE r.rel_type_id=(identity->>'typeId')::int;
 ELSE RAISE EXCEPTION 'retained operation category required' USING ERRCODE='55000';END IF;
 IF identity->'owner' IS DISTINCT FROM jsonb_build_object('documentId',owner_document,'moduleId',owner_module) THEN
  RAISE EXCEPTION 'retained owner correspondence required' USING ERRCODE='55000';END IF;
 RETURN QUERY SELECT owner_document,owner_module;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_retained_operation_owner(uuid,int) FROM PUBLIC;

CREATE FUNCTION truss.object_group_begin_prepared(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text,original_condition_keys bytea,replay_only boolean,app_prepared jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE input_operations jsonb;
 input jsonb;documents jsonb;request jsonb;context jsonb;selected record;archive truss.schema_doc%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;head_revision int;head_registration uuid;
 operation jsonb;admission record;source_text text;person oid;writer xid8;ns bytea;rk bytea;route bigint;prior_generation bigint;receipt truss.request_receipt%ROWTYPE;
 raw jsonb;observation bytea;attempt truss.runtime_object_attempt%ROWTYPE;index int:=0;failure_detail text;retained_basis jsonb;retained_count int;
BEGIN
 IF replay_only IS NULL THEN RAISE EXCEPTION 'explicit replay probe required' USING ERRCODE='22023';END IF;
 context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;person:=truss.runtime_person(false);writer:=pg_current_xact_id();
 IF original_input IS NULL OR octet_length(original_input) NOT BETWEEN 1 AND 1048576 OR original_documents IS NULL OR octet_length(original_documents) NOT BETWEEN 1 AND 4194304
  OR original_request IS NULL OR octet_length(original_request) NOT BETWEEN 1 AND 65536 THEN RAISE EXCEPTION 'bounded group required' USING ERRCODE='54000';END IF;
 IF (convert_from(original_input,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
 OR (convert_from(original_documents,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE
 OR (convert_from(original_request,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'unique original JSON members required' USING ERRCODE='22023';END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;documents:=convert_from(original_documents,'UTF8')::jsonb;request:=convert_from(original_request,'UTF8')::jsonb;
 input_operations:=input->'operations';
 IF replay_only AND request->>'state' IS DISTINCT FROM 'present' THEN RAISE EXCEPTION 'request-present replay probe required' USING ERRCODE='22023';END IF;
 IF input-ARRAY['interfaceVersion','layoutProfile','mutationProfile','valueProfile','catalog','operations','assertedOrigin','preconditions']<>'{}'::jsonb
 OR input->>'interfaceVersion' IS DISTINCT FROM 'truss-group-input/0.1.0' OR input->'catalog' IS DISTINCT FROM '{"selection":"current"}'::jsonb
 OR jsonb_typeof(input_operations) IS DISTINCT FROM 'array'
 OR jsonb_array_length(input_operations) NOT BETWEEN 1 AND (CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN 1024 ELSE 128 END) OR jsonb_typeof(documents) IS DISTINCT FROM 'array'
 OR jsonb_array_length(documents) NOT BETWEEN 1 AND 512 THEN RAISE EXCEPTION 'selected bounded object group required' USING ERRCODE='0A000';END IF;
 IF input->'assertedOrigin'->>'kind' IS DISTINCT FROM 'map' OR (input->'assertedOrigin')-ARRAY['kind','entries']<>'{}'::jsonb
 OR jsonb_typeof(input->'assertedOrigin'->'entries') IS DISTINCT FROM 'array'
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e WHERE jsonb_typeof(e.value->'key') IS DISTINCT FROM 'string'
 OR e.value-ARRAY['key','value']<>'{}'::jsonb OR (e.value->'value'='{"kind":"null"}'::jsonb OR (e.value->'value'->>'kind'='string'
 AND jsonb_typeof(e.value->'value'->'text')='string' AND (e.value->'value')-ARRAY['kind','text']='{}'::jsonb)) IS NOT TRUE)
 OR (SELECT count(*) FROM jsonb_array_elements(input->'assertedOrigin'->'entries'))<>(SELECT count(DISTINCT e.value->>'key') FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e)
 THEN RAISE EXCEPTION 'closed scalar asserted origin required' USING ERRCODE='22023';END IF;
 IF (SELECT count(*) FROM jsonb_array_elements(input_operations) o WHERE o.value ? 'alias')
 <>(SELECT count(DISTINCT o.value->>'alias') FROM jsonb_array_elements(input_operations) o WHERE o.value ? 'alias') THEN RAISE EXCEPTION 'unique aliases required' USING ERRCODE='22023';END IF;
 IF request<>'{"state":"none"}'::jsonb THEN
  IF request->>'state' IS DISTINCT FROM 'present' OR request-ARRAY['state','identity']<>'{}'::jsonb
   OR request->'identity'->>'inputProfile' IS DISTINCT FROM 'truss-group-input/0.1.0'
   OR request->'identity'->>'interfaceVersion' IS DISTINCT FROM 'truss-request-identity/0.1.0'
   OR request->'identity'->>'authorizedScopeIdentity' IS DISTINCT FROM context->>'authorizedScopeIdentity'
   OR jsonb_typeof(request->'identity'->'requestId') IS DISTINCT FROM 'string' OR octet_length(request->'identity'->>'requestId') NOT BETWEEN 1 AND 1024
   OR (request->'identity')-ARRAY['authorizedScopeIdentity','requestId','claimedSha256','inputProfile','interfaceVersion']<>'{}'::jsonb
   OR (request->'identity' ? 'claimedSha256' AND request->'identity'->>'claimedSha256' IS DISTINCT FROM encode(sha256(original_input),'hex')) THEN
   RAISE EXCEPTION 'original request identity required' USING ERRCODE='22023';END IF;
  ns:=convert_to(context->>'authorizedScopeIdentity','UTF8');rk:=convert_to(request->'identity'->>'requestId','UTF8');
  route:=('x'||substr(encode(sha256(convert_to('group-request','UTF8')||sha256(ns)||sha256(rk)),'hex'),1,16))::bit(64)::bigint;
  IF NOT pg_try_advisory_xact_lock(route) THEN RAISE EXCEPTION 'request in flight' USING ERRCODE='55P03';END IF;
  SELECT generation INTO prior_generation FROM truss.request_receipt_route_guard WHERE namespace_sha256=sha256(ns) AND request_sha256=sha256(rk) FOR UPDATE NOWAIT;
  IF NOT FOUND AND NOT replay_only THEN INSERT INTO truss.request_receipt_route_guard VALUES(sha256(ns),sha256(rk),0);END IF;
  IF (SELECT count(*) FROM truss.request_receipt WHERE namespace_sha256=sha256(ns) AND request_sha256=sha256(rk))>10000 THEN RAISE EXCEPTION 'bounded receipt route required' USING ERRCODE='54000';END IF;
  IF (SELECT count(*) FROM truss.request_receipt WHERE namespace_sha256=sha256(ns) AND request_sha256=sha256(rk) AND namespace_identity_utf8=ns AND request_id_utf8=rk)>1 THEN RAISE EXCEPTION 'unique exact receipt required' USING ERRCODE='55000';END IF;
  IF EXISTS(SELECT 1 FROM truss.runtime_object_attempt a WHERE a.writer_xid=writer AND NOT a.complete AND a.context->>'authorizedScopeIdentity'=convert_from(ns,'UTF8')
   AND convert_from(a.request_bytes,'UTF8')::jsonb->'identity'->>'requestId'=request->'identity'->>'requestId') THEN RAISE EXCEPTION 'request already unfinished' USING ERRCODE='55P03';END IF;
  SELECT * INTO receipt FROM truss.request_receipt WHERE namespace_sha256=sha256(ns) AND request_sha256=sha256(rk) AND namespace_identity_utf8=ns AND request_id_utf8=rk;
  IF FOUND THEN
   IF receipt.payload_state<>'complete' THEN RETURN convert_to('{"outcome":"unavailable","reason":"receipt_expired"}','UTF8');END IF;
   raw:=convert_from(receipt.original_receipt_bytes,'UTF8')::jsonb;
   IF raw->>'profile' IS DISTINCT FROM 'truss-object-group-receipt/0.1' THEN RAISE EXCEPTION 'selected receipt required' USING ERRCODE='0A000';END IF;
   IF decode(raw->>'inputBase64','base64') IS DISTINCT FROM original_input THEN RAISE EXCEPTION 'request input changed' USING ERRCODE='P1001';END IF;
   SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=(raw->>'attemptId')::uuid;
   IF NOT attempt.complete OR attempt.receipt_id IS DISTINCT FROM receipt.storage_row_id OR attempt.writer_xid IS DISTINCT FROM receipt.original_writer_xid
    OR to_jsonb(receipt) IS DISTINCT FROM attempt.expected_receipt OR attempt.input_bytes IS DISTINCT FROM original_input
    OR attempt.position_bytes IS DISTINCT FROM truss.runtime_receipt_position(attempt.context,receipt.storage_row_id,receipt.original_writer_xid)
    OR raw->'semantic' IS DISTINCT FROM jsonb_build_object('interfaceVersion','truss-group-result/0.1.0','executedCatalogRevision',raw->'semantic'->>'executedCatalogRevision',
     'layoutProfile',input->'layoutProfile','mutationProfile',input->'mutationProfile','results',attempt.results,'aliases',attempt.aliases) THEN RAISE EXCEPTION 'original receipt position correspondence required' USING ERRCODE='55000';END IF;
   retained_count:=jsonb_array_length(attempt.results);
   index:=0;FOR operation IN SELECT value FROM jsonb_array_elements(input_operations) LOOP
    IF NOT attempt.complete OR index<0 OR index>=attempt.next_index OR retained_count<>attempt.next_index THEN
     RAISE EXCEPTION 'complete retained operation required' USING ERRCODE='55000';END IF;
    SELECT * INTO STRICT selected FROM truss.runtime_owned_retained_operation_frame(operation,attempt.results->index,
     raw->'semantic'->>'executedCatalogRevision',retained_basis,person);
    retained_basis:=selected.historical_basis;
    PERFORM truss.runtime_module_writer(selected.document_id,selected.module);index:=index+1;
   END LOOP;
   PERFORM truss.runtime_edge_authorize((raw->>'attemptId')::uuid);
   observation:=convert_to(jsonb_build_object('profile','truss-native-create-replay-observation/0.1','sourceEpoch',context->>'sourceEpoch',
    'observingXid',writer::text,'originalWriterXid',receipt.original_writer_xid::text,'receiptStorageId',receipt.storage_row_id::text,
    'receiptGeneration',receipt.lifecycle_generation::text,'receiptSha256',encode(sha256(receipt.original_receipt_bytes),'hex'),
    'actorOid',person::text,'actor',session_user::text,'scopeIdentity',context->>'authorizedScopeIdentity',
    'releaseId',expected_release,'releaseSha256',expected_digest,'basis',CASE WHEN writer=receipt.original_writer_xid THEN 'same_transaction' ELSE 'committed_receipt' END)::text,'UTF8');
   RETURN convert_to(jsonb_build_object('outcome','success','disposition','replayed','durability',CASE WHEN writer=receipt.original_writer_xid THEN 'pending' ELSE 'committed' END,
    'semantic',raw->'semantic','receiptToken',truss.runtime_receipt_token(attempt.position_bytes),'observationBase64',replace(encode(observation,'base64'),chr(10),''),'observationSha256',encode(sha256(observation),'hex'))::text,'UTF8');
  END IF;
 END IF;
 IF input->'layoutProfile' IS DISTINCT FROM context->'layoutProfile' OR input->'mutationProfile' IS DISTINCT FROM context->'mutationProfile' OR input->'valueProfile' IS DISTINCT FROM context->'valueProfile' THEN RAISE EXCEPTION 'current group profile required on receipt miss' USING ERRCODE='0A000';END IF;
 IF replay_only THEN RETURN convert_to('{"outcome":"miss"}','UTF8');END IF;
 -- Authorize the full original owner inventory without requiring live targets.
 person:=truss.runtime_person(false);
 -- CREATE source/owner meaning is constant for each exact definition pin
 -- during this read-only admission phase. Retain every original ordinal for
 -- alias-dependent operations; value/shape admission still checks every row.
 FOR admission IN
  SELECT * FROM (
   SELECT value operation,(ordinal-1)::int operation_index
   FROM jsonb_array_elements(input_operations) WITH ORDINALITY o(value,ordinal)
   WHERE (value->>'operation' IS NULL OR value->>'operation' NOT IN ('create_object','create_edge'))
    AND NOT (coalesce(value->>'operation'='update_object' AND value->'target'->>'state'='stored',false)
     AND NOT (value ? 'ownershipChange'))
   UNION ALL
   SELECT creates.operation,creates.operation_index FROM (
    SELECT DISTINCT ON (value->>'operation',value->>'typeDefinitionPin',value->>'relationshipDefinitionPin',
     CASE WHEN value->>'operation'='update_object' THEN (value->'target'->'identity')-'id' END)
     value operation,(ordinal-1)::int operation_index
    FROM jsonb_array_elements(input_operations) WITH ORDINALITY o(value,ordinal)
    WHERE value->>'operation' IN ('create_object','create_edge')
     OR value->>'operation'='update_object' AND value->'target'->>'state'='stored' AND NOT (value ? 'ownershipChange')
    ORDER BY value->>'operation',value->>'typeDefinitionPin',value->>'relationshipDefinitionPin',
     CASE WHEN value->>'operation'='update_object' THEN (value->'target'->'identity')-'id' END,ordinal) creates
  ) original_owners ORDER BY operation_index
 LOOP
  operation:=admission.operation;index:=admission.operation_index;
  SELECT * INTO STRICT selected FROM truss.runtime_owned_operation_owner_qualified(operation,input_operations,index,person);PERFORM truss.runtime_module_writer_qualified(selected.document_id,selected.module,person);
  SELECT * INTO STRICT archive FROM truss.schema_doc WHERE doc_id=selected.document_id ORDER BY rev DESC LIMIT 1;
  SELECT d.value->>'sourceText' INTO STRICT source_text FROM jsonb_array_elements(documents) d WHERE d.value->>'documentId'=archive.doc_id;
  IF convert_to(source_text,'UTF8') IS DISTINCT FROM convert_to(archive.document,'UTF8') THEN RAISE EXCEPTION 'exact original source required' USING ERRCODE='22023';END IF;
  index:=index+1;
 END LOOP;
 -- Predicate owners can differ from all operation owners. Preserve exact
 -- original-source correspondence inside the database before evaluating them.
 IF input ? 'preconditions' THEN
  PERFORM truss.group_condition_key_metadata(original_input,original_documents,expected_release,expected_digest);
 END IF;
 -- Conditions observe the locked prestate before operation planning can fail.
 -- Receipt replay and complete owner/source admission above retain their order.
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  IF NOT pg_try_advisory_xact_lock(1953658227,1735549296) THEN
   RAISE EXCEPTION 'graph writer in flight' USING ERRCODE='55P03';END IF;
  LOCK TABLE truss.object IN ROW EXCLUSIVE MODE NOWAIT;
  LOCK TABLE truss.edge IN ROW EXCLUSIVE MODE NOWAIT;
 ELSE
  LOCK TABLE truss.object IN SHARE ROW EXCLUSIVE MODE NOWAIT;
  LOCK TABLE truss.edge IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 END IF;
 PERFORM truss.runtime_evaluate_preconditions(input,original_condition_keys);
 -- Preserve precondition outcome precedence; a stale cache identity is checked
 -- only after the native group has completed the same current admission steps.
 IF app_prepared IS NOT NULL THEN
  SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
  SELECT rev INTO STRICT head_revision FROM truss.schema_head WHERE id=1;
  SELECT r.registration_id INTO STRICT head_registration FROM truss.catalog_registration_request r WHERE r.revision=head_revision;
  IF app_prepared->>'profile' IS DISTINCT FROM 'truss-application-record-preparation/0.1'
   OR app_prepared->'basis' IS DISTINCT FROM jsonb_build_object('installationId',installation.installation_id::text,
    'releaseSha256',installation.release_sha256,'sourceEpoch',installation.source_epoch::text,
    'catalogRevision',head_revision,'registrationId',head_registration::text,'documentsSha256',encode(sha256(original_documents),'hex'))
   OR app_prepared->>'inputSha256' IS DISTINCT FROM encode(sha256(original_input),'hex')
   OR jsonb_typeof(app_prepared->'schemas') IS DISTINCT FROM 'object'
   OR jsonb_typeof(app_prepared->'operations') IS DISTINCT FROM 'array' THEN
   RAISE EXCEPTION 'prepared application basis changed' USING ERRCODE='55P03';END IF;
 END IF;
 INSERT INTO truss.runtime_object_attempt(writer_xid,actor_oid,input_bytes,documents_bytes,request_bytes,context)
 VALUES(writer,person,original_input,original_documents,original_request,
  context||jsonb_build_object('originalAssertedOrigin',input->'assertedOrigin')) RETURNING * INTO attempt;
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  IF app_prepared IS NULL THEN PERFORM truss.runtime_owned_capture(attempt.id);
  ELSE PERFORM truss.runtime_owned_capture_application(attempt.id,app_prepared);END IF;
 END IF;
 RETURN convert_to(jsonb_build_object('outcome','execute','attemptId',attempt.id::text)::text,'UTF8');
EXCEPTION WHEN SQLSTATE 'P1006' THEN
 GET STACKED DIAGNOSTICS failure_detail=PG_EXCEPTION_DETAIL;
 -- The function subtransaction rolls back guard setup and all other effects.
 RETURN convert_to(failure_detail,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.object_group_begin_prepared(bytea,bytea,bytea,text,text,bytea,boolean,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.object_group_begin(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text,original_condition_keys bytea DEFAULT convert_to('[]','UTF8'),replay_only boolean DEFAULT false) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 RETURN truss.object_group_begin_prepared(original_input,original_documents,original_request,expected_release,expected_digest,original_condition_keys,replay_only,NULL);
END;
$$;
REVOKE ALL ON FUNCTION truss.object_group_begin(bytea,bytea,bytea,text,text,bytea,boolean) FROM PUBLIC;

CREATE FUNCTION truss.runtime_object_metadata(attempt_id uuid,operation_index int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;operation jsonb;selected truss.type_def%ROWTYPE;identity jsonb;prior truss.object%ROWTYPE;
 property truss.prop_def%ROWTYPE;entry jsonb;unset_name text;props jsonb;retained jsonb;values jsonb;keys jsonb;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id FOR UPDATE NOWAIT;
 IF attempt.writer_xid<>pg_current_xact_id() OR attempt.actor_oid<>truss.runtime_person(false) OR attempt.complete OR attempt.next_index<>operation_index THEN
  RAISE EXCEPTION 'current ordered attempt required' USING ERRCODE='55000';END IF;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;operation:=input->'operations'->operation_index;
 IF operation->>'operation' IN ('create_edge','update_edge','delete_edge') THEN RETURN truss.runtime_edge_metadata(attempt_id,operation_index);END IF;
 selected:=truss.runtime_operation_type(operation,input->'operations',operation_index);PERFORM truss.runtime_module_writer(selected.document_id,selected.module);
 IF operation->>'operation'='create_object' THEN
  -- Reject malformed key cells natively before calling the external UMF
  -- producer, so caller input failures remain GroupFailed rather than host errors.
  IF jsonb_typeof(operation->'values') IS DISTINCT FROM 'array' OR jsonb_array_length(operation->'values')>1024 THEN RAISE EXCEPTION 'bounded authored create values required' USING ERRCODE='22023';END IF;
  FOR property IN SELECT DISTINCT p.* FROM truss.key_def k CROSS JOIN LATERAL unnest(k.prop_ids) i(prop_id)
   JOIN truss.prop_def p ON p.type_id=k.type_id AND p.prop_id=i.prop_id WHERE k.type_id=selected.type_id AND k.retired_rev IS NULL LOOP
   IF property.scalar_type NOT IN ('string','integer','decimal','boolean','binary') OR property.scalar_type IS NULL
    OR property.nullability IS DISTINCT FROM 'required' OR property.cardinality IS DISTINCT FROM 'one' OR property.home IS DISTINCT FROM 'json'
    OR property.retired_rev IS NOT NULL OR (property.scalar_type='decimal' AND (truss.valid_decimal_facets(property.facets)) IS DISTINCT FROM TRUE) THEN
    RAISE EXCEPTION 'supported required scalar key property required' USING ERRCODE='0A000';END IF;
   IF (SELECT count(*) FROM jsonb_array_elements(operation->'values') v WHERE v.value->>'name'=property.name)<>1 THEN RAISE EXCEPTION 'complete unique key values required' USING ERRCODE='22023';END IF;
   SELECT v.value->'value' INTO entry FROM jsonb_array_elements(operation->'values') v WHERE v.value->>'name'=property.name;
   IF truss.valid_scalar_property(entry,property.scalar_type,false,property.facets) IS NOT TRUE THEN RAISE EXCEPTION 'exact declared key cell required' USING ERRCODE='22023';END IF;
  END LOOP;
  RETURN convert_from(truss.group_create_metadata(convert_to(jsonb_set(input-'preconditions','{operations}',jsonb_build_array(operation))::text,'UTF8'),attempt.documents_bytes,
   (SELECT release_id FROM truss.runtime_current_installation()),(SELECT release_sha256 FROM truss.runtime_current_installation())),'UTF8')::jsonb->0
   ||jsonb_build_object('values',operation->'values');
 END IF;
 IF operation->'target'->>'state'='stored' THEN identity:=operation->'target'->'identity';
 ELSE SELECT value->'identity' INTO STRICT identity FROM jsonb_array_elements(attempt.aliases) WHERE value->>'alias'=operation->'target'->>'alias';END IF;
 SELECT * INTO prior FROM truss.object WHERE id=(identity->>'id')::bigint AND type_id=selected.type_id FOR UPDATE NOWAIT;
 IF NOT FOUND THEN RAISE EXCEPTION 'target absent' USING ERRCODE='P1004';END IF;
 IF prior.root_id IS NOT NULL THEN RAISE EXCEPTION 'rootless scalar object required' USING ERRCODE='0A000';END IF;
 IF operation ? 'expectedVersion' AND (jsonb_typeof(operation->'expectedVersion') IS DISTINCT FROM 'string' OR operation->>'expectedVersion' IS DISTINCT FROM prior.ver::text) THEN
  RAISE EXCEPTION 'expected version failed' USING ERRCODE='P1003';END IF;
 IF operation->>'operation'='delete_object' THEN
  IF operation-ARRAY['operation','target','expectedVersion']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed delete required' USING ERRCODE='22023';END IF;
  IF EXISTS(SELECT 1 FROM truss.edge WHERE source_id=prior.id AND source_type=prior.type_id OR target_id=prior.id AND target_type=prior.type_id)
   OR EXISTS(SELECT 1 FROM truss.object WHERE root_id=prior.id AND root_type=prior.type_id) THEN RAISE EXCEPTION 'delete dependencies exist' USING ERRCODE='P1005';END IF;
  RETURN jsonb_build_object('typeId',selected.type_id::text,'documentId',selected.document_id,'moduleId',selected.module,'recordId',selected.element,
   'identity',identity,'prior',to_jsonb(prior),'keys','[]'::jsonb,'values','[]'::jsonb);
 END IF;
 IF operation-ARRAY['operation','target','set','unset','expectedVersion']<>'{}'::jsonb OR jsonb_typeof(operation->'set') IS DISTINCT FROM 'array'
 OR jsonb_typeof(operation->'unset') IS DISTINCT FROM 'array' OR jsonb_array_length(operation->'set')>1024 OR jsonb_array_length(operation->'unset')>1024 THEN
  RAISE EXCEPTION 'closed bounded scalar update required' USING ERRCODE='22023';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'set') s WHERE s.value-ARRAY['name','value']<>'{}'::jsonb
  OR jsonb_typeof(s.value->'name') IS DISTINCT FROM 'string' OR octet_length(s.value->>'name') NOT BETWEEN 1 AND 4096 OR truss.valid_flat_cell(s.value->'value') IS NOT TRUE)
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'unset') u WHERE jsonb_typeof(u.value) IS DISTINCT FROM 'string' OR octet_length(u.value#>>'{}') NOT BETWEEN 1 AND 4096)
 OR jsonb_array_length(operation->'set')<>(SELECT count(DISTINCT s.value->>'name') FROM jsonb_array_elements(operation->'set') s)
 OR jsonb_array_length(operation->'unset')<>(SELECT count(DISTINCT u.value) FROM jsonb_array_elements(operation->'unset') u)
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'set') s JOIN jsonb_array_elements(operation->'unset') u ON s.value->>'name'=u.value#>>'{}') THEN
  RAISE EXCEPTION 'unique disjoint update names required' USING ERRCODE='22023';END IF;
 props:=prior.props;retained:=coalesce(prior.retained,'{}');
 FOR unset_name IN SELECT value#>>'{}' FROM jsonb_array_elements(operation->'unset') LOOP
  SELECT p.* INTO property FROM truss.prop_def p WHERE p.type_id=selected.type_id AND p.name=unset_name AND retired_rev IS NULL;
  IF FOUND THEN props:=props-property.prop_id::text;ELSE retained:=retained-unset_name;END IF;
 END LOOP;
 FOR entry IN SELECT value FROM jsonb_array_elements(operation->'set') LOOP
  SELECT * INTO property FROM truss.prop_def WHERE type_id=selected.type_id AND name=entry->>'name' AND retired_rev IS NULL;
  IF FOUND THEN props:=props||jsonb_build_object(property.prop_id::text,truss.canonical_flat_cell(entry->'value'));ELSE retained:=retained||jsonb_build_object(entry->>'name',truss.canonical_flat_cell(entry->'value'));END IF;
 END LOOP;
 FOR property IN SELECT * FROM truss.prop_def WHERE type_id=selected.type_id AND retired_rev IS NULL LOOP
  IF truss.valid_property_definition(property) IS NOT TRUE THEN
   RAISE EXCEPTION 'supported scalar definition required' USING ERRCODE='0A000';END IF;
  IF NOT props ? property.prop_id::text THEN
   IF property.nullability='required' THEN RAISE EXCEPTION 'missing required value' USING ERRCODE='22023';END IF;
  ELSIF truss.valid_property_value(props->property.prop_id::text,property) IS NOT TRUE THEN RAISE EXCEPTION 'exact family required' USING ERRCODE='22023';END IF;
 END LOOP;
 IF octet_length(convert_to(jsonb_build_object('props',props,'retained',retained)::text,'UTF8'))>1048576 THEN RAISE EXCEPTION 'bounded object values required' USING ERRCODE='54000';END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',v.name,'value',v.value) ORDER BY v.name COLLATE "C"),'[]'::jsonb) INTO values FROM (
  SELECT p.name,props->p.prop_id::text AS value FROM truss.prop_def p WHERE p.type_id=selected.type_id AND p.retired_rev IS NULL AND props ? p.prop_id::text
  UNION ALL SELECT key,value FROM jsonb_each(retained)) v;
 SELECT coalesce(jsonb_agg(jsonb_build_object('keyNumber',k.key_num::text,'keyId',k.key_id,'names',
  (SELECT jsonb_agg(p.name ORDER BY i.ord) FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ord) JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=k.type_id)) ORDER BY k.key_num),'[]'::jsonb)
 INTO keys FROM truss.key_def k WHERE k.type_id=selected.type_id AND k.retired_rev IS NULL;
 RETURN jsonb_build_object('typeId',selected.type_id::text,'documentId',selected.document_id,'moduleId',selected.module,'recordId',selected.element,
  'identity',identity,'prior',to_jsonb(prior),'props',props,'retained',retained,'keys',keys,'values',values);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_metadata(uuid,int) FROM PUBLIC;
CREATE FUNCTION truss.object_group_metadata(attempt_id uuid,operation_index int) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE metadata jsonb;encoded bytea;entry jsonb;
BEGIN
 metadata:=truss.runtime_object_metadata(attempt_id,operation_index);encoded:=convert_to(metadata::text,'UTF8');
 PERFORM truss.runtime_module_writer(metadata->>'documentId',metadata->>'moduleId');
 IF NOT metadata ? 'source' AND NOT truss.runtime_object_values_readable((metadata->>'typeId')::int) THEN RAISE EXCEPTION 'current buffered property/item reader required' USING ERRCODE='42501';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(jsonb_build_array(metadata->'oldSource',metadata->'oldTarget',metadata->'source',metadata->'target')) WHERE value<>'null'::jsonb LOOP
  IF NOT truss.runtime_can_read(entry->'owner'->>'documentId',entry->'owner'->>'moduleId') THEN RAISE EXCEPTION 'current endpoint metadata reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 RETURN encoded;
END;
$$;
REVOKE ALL ON FUNCTION truss.object_group_metadata(uuid,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_object_history(object_image jsonb,identity jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE properties jsonb:='[]';retained jsonb;property truss.prop_def%ROWTYPE;pin record;basis jsonb;written_revision int:=(object_image->>'rev')::int;compiled jsonb;
BEGIN
 SELECT metadata-'propertyAccess' INTO compiled FROM truss.runtime_type_schema
  WHERE rev=written_revision AND type_id=(object_image->>'type_id')::int;
 IF FOUND AND NOT EXISTS(SELECT 1 FROM jsonb_object_keys(object_image->'props') n(name)
  WHERE NOT ((compiled->'propertyPins') ? n.name)) THEN
  RETURN truss.runtime_owned_history_record_in_metadata(object_image,identity,compiled);
 END IF;
 SELECT CASE WHEN written_revision=(SELECT rev FROM truss.schema_head WHERE id=1)
  AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>written_revision)
 THEN jsonb_build_object(
   'type_def',(SELECT coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) FROM truss.type_def t WHERE t.type_id=(object_image->>'type_id')::int),
   'prop_def',(SELECT coalesce(jsonb_agg(to_jsonb(p)),'[]'::jsonb) FROM truss.prop_def p WHERE p.type_id=(object_image->>'type_id')::int)) END INTO basis;
 IF basis IS NULL THEN basis:=truss.catalog_all_expected_records(written_revision);END IF;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata_in_basis('type',(object_image->>'type_id')::int,NULL,written_revision,basis);
 identity:=jsonb_set(identity,'{definitionPin}',to_jsonb(pin.definition_pin));
 FOR property IN SELECT * FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=(object_image->>'type_id')::int ORDER BY prop_id LOOP
  IF object_image->'props' ? property.prop_id::text THEN
   SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata_in_basis('property',property.type_id,property.prop_id,written_revision,basis);
   properties:=properties||jsonb_build_array(jsonb_build_object('propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,'value',object_image->'props'->property.prop_id::text));
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',key,'value',value) ORDER BY key COLLATE "C"),'[]'::jsonb) INTO retained FROM jsonb_each(coalesce(nullif(object_image->'retained','null'::jsonb),'{}'));
 RETURN jsonb_build_object('interfaceVersion','truss-history-record/0.1.0','kind','object','identity',identity,
  'recordVersion',object_image->>'ver','catalogRevision',object_image->>'rev',
  'createdAt',to_char((object_image->>'created_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'updatedAt',to_char((object_image->>'updated_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'properties',properties,'retained',retained,'ownership',truss.runtime_object_ownership_at(object_image));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_history(jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_history_record_in_metadata(object_image jsonb,identity jsonb,metadata jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE properties jsonb:='[]';retained jsonb;missing_pin boolean;
 object_properties jsonb:=object_image->'props';property_pins jsonb:=metadata->'propertyPins';
BEGIN
 IF metadata->>'typeId' IS DISTINCT FROM object_image->>'type_id'
  OR metadata->>'revision' IS DISTINCT FROM object_image->>'rev'
  OR jsonb_typeof(metadata->'typePin') IS DISTINCT FROM 'string'
  OR jsonb_typeof(metadata->'propertyOrder') IS DISTINCT FROM 'array'
  OR jsonb_typeof(property_pins) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original compiled history metadata required' USING ERRCODE='55000';END IF;
 identity:=jsonb_set(identity,'{definitionPin}',metadata->'typePin');
 SELECT coalesce(jsonb_agg(jsonb_build_object('propertyId',property_id,
    'definitionPin',property_pins->property_id,'value',object_properties->property_id)
    ORDER BY ordinality),'[]'::jsonb),
  coalesce(bool_or(NOT ((property_pins) ? property_id)),false)
 INTO properties,missing_pin
 FROM (SELECT entry#>>'{}' property_id,ordinality
  FROM jsonb_array_elements(metadata->'propertyOrder') WITH ORDINALITY ordered(entry,ordinality)) selected
 WHERE object_properties ? property_id;
 IF missing_pin THEN
  RAISE EXCEPTION 'complete original history property pins required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',key,'value',value) ORDER BY key COLLATE "C"),'[]'::jsonb) INTO retained FROM jsonb_each(coalesce(nullif(object_image->'retained','null'::jsonb),'{}'));
 RETURN jsonb_build_object('interfaceVersion','truss-history-record/0.1.0','kind','object','identity',identity,
  'recordVersion',object_image->>'ver','catalogRevision',object_image->>'rev',
  'createdAt',to_char((object_image->>'created_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'updatedAt',to_char((object_image->>'updated_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'properties',properties,'retained',retained,'ownership',truss.runtime_object_ownership_at(object_image));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_history_record_in_metadata(jsonb,jsonb,jsonb) FROM PUBLIC;


CREATE FUNCTION truss.runtime_object_update_keys(object_id bigint,selected_type int,desired_props jsonb,original_keys bytea,attempt_id uuid,operation_index int) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;key_definition truss.key_def%ROWTYPE;component record;values_text text[];values_cells jsonb;key_facets jsonb;
 keys jsonb;key_input jsonb;tuple_bytes bytea;owner_receipt jsonb;pin record;ns bytea;transport bytea;planned jsonb:='[]';entry jsonb;
 old truss.object_key_bucket%ROWTYPE;members bigint[];reservations bigint[];observed record;unchanged boolean;route record;
BEGIN
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF original_keys IS NULL OR octet_length(original_keys) NOT BETWEEN 1 AND 8388608 OR (convert_from(original_keys,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'bounded original key inventory required' USING ERRCODE='22023';END IF;
 keys:=convert_from(original_keys,'UTF8')::jsonb;
 IF keys<>'[]'::jsonb THEN RAISE EXCEPTION 'client key encoding is no longer accepted' USING ERRCODE='22023';END IF;
 FOR key_definition IN SELECT * FROM truss.key_def WHERE type_id=selected_type AND retired_rev IS NULL ORDER BY key_num LOOP
  values_text:=ARRAY[]::text[];values_cells:='[]';key_facets:='[]';
  FOR component IN SELECT p.* FROM unnest(key_definition.prop_ids) WITH ORDINALITY i(prop_id,ord) JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=selected_type ORDER BY i.ord LOOP
   IF component.scalar_type NOT IN ('string','integer','decimal','boolean','binary') OR component.nullability IS DISTINCT FROM 'required'
    OR truss.valid_scalar_property(desired_props->component.prop_id::text,component.scalar_type,false,component.facets) IS NOT TRUE THEN
    RAISE EXCEPTION 'required exact key components required' USING ERRCODE='0A000';END IF;
   values_cells:=values_cells||jsonb_build_array(desired_props->component.prop_id::text);
   key_facets:=key_facets||jsonb_build_array(coalesce(component.facets,'{}'::jsonb));
  END LOOP;
  tuple_bytes:=truss.derive_catalog_key_tuple(selected_type,key_definition.key_num,values_cells);
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('key',selected_type,key_definition.key_num);
  ns:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
   'sourceEpoch',installation.source_epoch::text,'typeId',selected_type::text,'keyNumber',key_definition.key_num::text,
   'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
  transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');
  SELECT * INTO STRICT old FROM truss.object_key_bucket k WHERE k.object_id=runtime_object_update_keys.object_id AND k.type_id=selected_type AND k.key_num=key_definition.key_num;
  planned:=planned||jsonb_build_array(jsonb_build_object('keyNumber',key_definition.key_num,'ns',encode(ns,'hex'),'transport',encode(transport,'hex'),
   'oldId',old.storage_row_id,'oldNs',encode(old.namespace_bytes,'hex'),'oldTransport',encode(old.key_bytes,'hex')));
 END LOOP;
 FOR route IN SELECT DISTINCT routes.ns,routes.transport FROM (
  SELECT decode(value->>'ns','hex') ns,decode(value->>'transport','hex') transport FROM jsonb_array_elements(planned)
  UNION ALL SELECT decode(value->>'oldNs','hex'),decode(value->>'oldTransport','hex') FROM jsonb_array_elements(planned)) routes
  ORDER BY routes.ns,routes.transport LOOP PERFORM truss.lock_string_key_bucket(route.ns,route.transport);END LOOP;
 FOR entry IN SELECT value FROM jsonb_array_elements(planned) LOOP
  ns:=decode(entry->>'ns','hex');transport:=decode(entry->>'transport','hex');
  unchanged:=entry->>'ns'=entry->>'oldNs' AND entry->>'transport'=entry->>'oldTransport';
  SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(ns,transport);
  IF unchanged THEN
   IF cardinality(observed.member_ids)<>1 OR observed.member_ids[1]<>(entry->>'oldId')::bigint THEN RAISE EXCEPTION 'owned unchanged key required' USING ERRCODE='55000';END IF;
   CONTINUE;
  END IF;
  IF cardinality(observed.member_ids)>0 OR cardinality(observed.reservation_ids)>0 THEN RAISE EXCEPTION 'key allocated or reserved' USING ERRCODE='23505';END IF;
  DELETE FROM truss.object_key_bucket WHERE storage_row_id=(entry->>'oldId')::bigint;
  UPDATE truss.key_bucket_guard SET generation=generation+1 WHERE namespace_sha256=sha256(decode(entry->>'oldNs','hex')) AND key_sha256=sha256(decode(entry->>'oldTransport','hex'));
  INSERT INTO truss.object_key_bucket(type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
  VALUES(selected_type,(entry->>'keyNumber')::smallint,object_id,ns,transport,
   convert_to(jsonb_build_object('profile','truss-updated-key-context/0.2','attemptId',attempt_id::text,'operationIndex',operation_index::text,
    'objectId',object_id::text,'xid',pg_current_xact_id()::text,'derivation','postgresql-umf-key-tuple-v1')::text,'UTF8'));
  INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes) VALUES(ns,transport,
   convert_to(jsonb_build_object('profile','truss-updated-key-reservation/0.1','attemptId',attempt_id::text,'operationIndex',operation_index::text,
    'objectId',object_id::text,'typeId',selected_type::text,'keyNumber',entry->>'keyNumber','xid',pg_current_xact_id()::text)::text,'UTF8'));
  UPDATE truss.key_bucket_guard SET generation=generation+1 WHERE namespace_sha256=sha256(ns) AND key_sha256=sha256(transport);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_update_keys(bigint,int,jsonb,bytea,uuid,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_group_step_in_input(attempt_id uuid,operation_index int,original_keys bytea,original_input bytea,parsed_input jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
<<ordered_group_step>>
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;operation jsonb;metadata jsonb;raw jsonb;result jsonb;identity jsonb;
 old_image jsonb;new_image jsonb;object_row truss.object%ROWTYPE;keys jsonb;entry jsonb;property truss.prop_def%ROWTYPE;pin record;
 events jsonb:='[]';event_refs jsonb:='[]';journals jsonb:='[]';event jsonb;journal truss.journal%ROWTYPE;event_digest text;native_state text;
 current_actor oid;revision int;version bigint;installation truss.catalog_runtime_installation%ROWTYPE;before_record jsonb;after_record jsonb;
BEGIN
 current_actor:=truss.runtime_person(false);
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor OR attempt.complete OR attempt.next_index IS DISTINCT FROM operation_index THEN RAISE EXCEPTION 'current ordered object attempt required' USING ERRCODE='55000';END IF;
 IF attempt.input_bytes IS DISTINCT FROM original_input THEN RAISE EXCEPTION 'original step input required' USING ERRCODE='55000';END IF;
 input:=parsed_input;operation:=jsonb_extract_path(input,'operations',operation_index::text);
 IF input->'mutationProfile'=truss.runtime_owned_profile() AND operation->>'operation'<>'create_object' THEN
  RETURN truss.runtime_owned_step(attempt_id,operation_index,input,attempt.input_bytes,current_actor);
 END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 IF operation->>'operation'='create_object' THEN
  raw:=convert_from(truss.apply_create_group_qualified(convert_to(((input-ARRAY['preconditions','operations'])||jsonb_build_object('operations',jsonb_build_array(operation)))::text,'UTF8'),attempt.documents_bytes,
   original_keys,convert_to('{"state":"none"}','UTF8'),installation.release_id,installation.release_sha256,current_actor,attempt_id,original_input,input),'UTF8')::jsonb;
  IF raw->>'outcome'<>'success' THEN
   native_state:=coalesce(raw->>'nativeState',CASE raw->>'reason' WHEN 'resource' THEN '54000' WHEN 'observation' THEN '55P03' ELSE '0A000' END);
   RAISE EXCEPTION 'create operation refused' USING ERRCODE=native_state;
  END IF;
  result:=raw->'semantic'->'results'->0;
  -- The create leaf owns insertion AND one-shot outer progress advancement.
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_object_attempt a WHERE a.id=attempt_id
   AND a.next_index=operation_index+1 AND CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN
    a.results='[]'::jsonb AND a.aliases='[]'::jsonb AND EXISTS(
     SELECT 1 FROM truss.runtime_owned_operation p WHERE p.attempt_id=a.id AND p.operation_index=runtime_owned_group_step_in_input.operation_index AND p.result=ordered_group_step.result)
    ELSE a.results->operation_index=result END) THEN
   RAISE EXCEPTION 'original atomic create progress required' USING ERRCODE='55000';END IF;
  RETURN convert_to(result::text,'UTF8');
 END IF;
 metadata:=truss.runtime_object_metadata(attempt_id,operation_index);
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;operation:=input->'operations'->operation_index;
 IF operation->>'operation' IN ('create_edge','update_edge','delete_edge') THEN RETURN truss.runtime_edge_step(attempt_id,operation_index,metadata);END IF;
 identity:=metadata->'identity';old_image:=metadata->'prior';
 object_row:=(jsonb_populate_record(NULL::truss.object,old_image));
 IF operation->>'operation'='update_object' AND object_row.props IS NOT DISTINCT FROM metadata->'props' AND coalesce(object_row.retained,'{}') IS NOT DISTINCT FROM metadata->'retained' THEN
  result:=jsonb_build_object('outcome','unchanged','operation','update_object','identity',identity,'version',object_row.ver::text,'events','[]'::jsonb);
 ELSE
  IF object_row.ver=9223372036854775807 THEN RAISE EXCEPTION 'record version exhausted' USING ERRCODE='54000';END IF;
  version:=object_row.ver+1;before_record:=truss.runtime_object_history(old_image,identity);
  IF operation->>'operation'='update_object' THEN
   PERFORM truss.runtime_object_update_keys(object_row.id,object_row.type_id,metadata->'props',original_keys,attempt_id,operation_index);
   object_row.props:=metadata->'props';object_row.retained:=nullif(metadata->'retained','{}'::jsonb);object_row.rev:=revision;object_row.ver:=version;object_row.updated_at:=clock_timestamp();new_image:=to_jsonb(object_row);
   UPDATE truss.object SET props=object_row.props,retained=object_row.retained,rev=object_row.rev,ver=object_row.ver,updated_at=object_row.updated_at WHERE id=object_row.id AND type_id=object_row.type_id;
   after_record:=truss.runtime_object_history(new_image,identity);
   FOR property IN SELECT * FROM truss.prop_def WHERE type_id=object_row.type_id AND retired_rev IS NULL ORDER BY prop_id LOOP
    IF old_image->'props'->property.prop_id::text IS DISTINCT FROM object_row.props->property.prop_id::text THEN
     SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('property',object_row.type_id,property.prop_id);
     events:=events||jsonb_build_array(jsonb_build_object('operation','property','propertyId',property.prop_id::text,'definitionPin',pin.definition_pin,
      'before',CASE WHEN old_image->'props' ? property.prop_id::text THEN jsonb_build_object('present',true,'value',old_image->'props'->property.prop_id::text) ELSE '{"present":false}'::jsonb END,
      'after',CASE WHEN object_row.props ? property.prop_id::text THEN jsonb_build_object('present',true,'value',object_row.props->property.prop_id::text) ELSE '{"present":false}'::jsonb END));
    END IF;
   END LOOP;
   events:=events||jsonb_build_array(jsonb_build_object('operation','metadata','before',before_record,'after',after_record));
  ELSE
   FOR entry IN SELECT to_jsonb(k) FROM truss.object_key_bucket k WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id LOOP
    PERFORM truss.lock_string_key_bucket(decode(substring(entry->>'namespace_bytes' FROM 3),'hex'),decode(substring(entry->>'key_bytes' FROM 3),'hex'));
    UPDATE truss.key_bucket_guard SET generation=generation+1 WHERE namespace_sha256=decode(substring(entry->>'namespace_sha256' FROM 3),'hex') AND key_sha256=decode(substring(entry->>'key_sha256' FROM 3),'hex');
   END LOOP;
   DELETE FROM truss.object WHERE id=object_row.id AND type_id=object_row.type_id;new_image:=NULL;
   events:=jsonb_build_array(jsonb_build_object('operation','delete','before',before_record));
  END IF;
  FOR index IN 0..jsonb_array_length(events)-1 LOOP
   event:=events->index;event:=event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
    'historyProfile','truss-native-scalar-mutation/0.1','xid',attempt.writer_xid::text,'seq',nextval('truss.journal_seq')::text,
    'identity',identity,'eventVersion',version::text,'eventCatalogRevision',revision::text,'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text));
   events:=jsonb_set(events,ARRAY[index::text],event);
  END LOOP;
  event_digest:=encode(sha256(convert_to(events::text,'UTF8')),'hex');
  FOR event IN SELECT value FROM jsonb_array_elements(events) LOOP
   event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount',jsonb_array_length(events)::text,'orderedEventDigest',event_digest));
   journal.seq:=(event->>'seq')::bigint;journal.at:=clock_timestamp();journal.xid:=attempt.writer_xid;journal.entity_kind:='o';journal.entity_id:=object_row.id;journal.entity_type:=object_row.type_id;
   journal.ver:=version;journal.op:=CASE event->>'operation' WHEN 'property' THEN 'update' ELSE event->>'operation' END;journal.prop_id:=(event->>'propertyId')::int;
   journal.old_value:=NULL;journal.new_value:=truss.runtime_exact_wrapper('event',convert_to(event::text,'UTF8'));journal.rev:=revision;
   journal.origin:=truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8'));
   INSERT INTO truss.journal SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(journal))).*;
   journals:=journals||jsonb_build_array(to_jsonb(journal));event_refs:=event_refs||jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-scalar-mutation/0.1','xid',attempt.writer_xid::text,'seq',journal.seq::text));
  END LOOP;
  SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]'::jsonb) INTO keys FROM truss.object_key_bucket k WHERE k.object_id=object_row.id AND k.type_id=object_row.type_id;
  INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
  VALUES(attempt_id,operation_index,attempt.writer_xid,object_row.id,object_row.type_id,old_image,new_image,keys,journals);
  IF operation->>'operation'='update_object' THEN result:=jsonb_build_object('outcome','changed','operation','update_object','identity',identity,'version',version::text,'events',event_refs);
  ELSE result:=jsonb_build_object('outcome','deleted','operation','delete_object','identity',identity,'deletionVersion',version::text,
   'deleted',jsonb_build_array(jsonb_build_object('identity',identity,'deletionVersion',version::text)),'events',event_refs);END IF;
 END IF;
 UPDATE truss.runtime_object_attempt SET next_index=next_index+1,results=results||jsonb_build_array(result) WHERE id=attempt_id;
 PERFORM truss.runtime_module_writer(metadata->>'documentId',metadata->>'moduleId');
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_group_step_in_input(uuid,int,bytea,bytea,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.object_group_step(attempt_id uuid,operation_index int,original_keys bytea) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;current_actor oid;
BEGIN
 current_actor:=truss.runtime_person(false);
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id;
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor OR attempt.complete OR attempt.next_index IS DISTINCT FROM operation_index THEN RAISE EXCEPTION 'current ordered object attempt required' USING ERRCODE='55000';END IF;
 RETURN truss.runtime_owned_group_step_in_input(attempt_id,operation_index,original_keys,attempt.input_bytes,convert_from(attempt.input_bytes,'UTF8')::jsonb);
END;
$$;
REVOKE ALL ON FUNCTION truss.object_group_step(uuid,int,bytea) FROM PUBLIC;

-- Legacy0.1 creation evidence remains in the inner group. Atomic0.2 retains
-- its actual journal in the transition; both formats preserve original history.
CREATE FUNCTION truss.runtime_create_transition_validate_qualified(selected_transition bigint,qualified_actor oid,prepared_input jsonb DEFAULT NULL,source_bytes bytea DEFAULT NULL,prepared_attempt truss.runtime_object_attempt DEFAULT NULL,compiled_metadata jsonb DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE transition truss.runtime_object_transition%ROWTYPE;attempt truss.runtime_object_attempt%ROWTYPE;
 member truss.runtime_create_member%ROWTYPE;creation truss.runtime_create_group%ROWTYPE;
 input jsonb;operation jsonb;result jsonb;expected jsonb;semantic jsonb;keys jsonb;key_expected jsonb;
 actual jsonb;generation bigint;entry jsonb;event jsonb;identity jsonb;original_origin jsonb;
BEGIN
 SELECT * INTO STRICT transition FROM truss.runtime_object_transition WHERE transition_id=selected_transition;
 IF prepared_attempt.id IS NOT NULL THEN
   IF prepared_attempt.id IS DISTINCT FROM transition.attempt_id THEN RAISE EXCEPTION 'original checked attempt required' USING ERRCODE='55000';END IF;
   attempt:=prepared_attempt;
  ELSE SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=transition.attempt_id;END IF;
 IF prepared_input IS NOT NULL AND (source_bytes IS NULL OR source_bytes IS DISTINCT FROM attempt.input_bytes) THEN
  RAISE EXCEPTION 'original checked creation input required' USING ERRCODE='55000';END IF;
 IF attempt.context->'creationTransitionProfile'='{"identity":"truss-unified-create-transition","version":"0.2","sha256":"073782e2517f2a7e26c8d6479c6266ececf68963681ccfb6a380e9cd16f2e11b"}'::jsonb THEN
  IF transition.before_object IS NOT NULL OR transition.after_object IS NULL
   OR transition.writer_xid IS DISTINCT FROM attempt.writer_xid OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
   OR attempt.actor_oid IS DISTINCT FROM qualified_actor
   OR transition.operation_index<0 OR transition.operation_index>=attempt.next_index
   OR jsonb_array_length(attempt.results)<>attempt.next_index OR jsonb_array_length(transition.journal)<>1 THEN
   RAISE EXCEPTION 'current atomic create transition required' USING ERRCODE='55000';END IF;
  input:=coalesce(prepared_input,convert_from(attempt.input_bytes,'UTF8')::jsonb);operation:=input->'operations'->transition.operation_index;
  result:=attempt.results->transition.operation_index;identity:=result->'identity';entry:=transition.journal->0;
  event:=convert_from(decode(entry->'new_value'->>'bytesBase64','base64'),'UTF8')::jsonb;
  original_origin:=jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text);
  IF operation->>'operation' IS DISTINCT FROM 'create_object' OR result->>'operation' IS DISTINCT FROM 'create_object'
   OR result->>'outcome' IS DISTINCT FROM 'created' OR result->>'version' IS DISTINCT FROM '1'
   OR identity->>'id' IS DISTINCT FROM transition.object_id::text OR identity->>'typeId' IS DISTINCT FROM transition.type_id::text
   OR identity->>'definitionPin' IS DISTINCT FROM operation->>'typeDefinitionPin'
   OR transition.after_object->>'id' IS DISTINCT FROM transition.object_id::text
   OR transition.after_object->>'type_id' IS DISTINCT FROM transition.type_id::text
   OR transition.after_object->>'ver' IS DISTINCT FROM '1'
   OR input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile()
   OR transition.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM
    truss.runtime_owned_object_image(attempt.id,transition.operation_index,'create:'||transition.operation_index::text,'after',NULL,attempt)
   OR event->>'operation' IS DISTINCT FROM 'create' OR event->'identity' IS DISTINCT FROM identity
   OR event->'origin' IS DISTINCT FROM original_origin
   OR event->'after' IS DISTINCT FROM (CASE WHEN compiled_metadata IS NULL
    THEN truss.runtime_object_history(transition.after_object,identity)
    ELSE truss.runtime_owned_history_record_in_metadata(transition.after_object,identity,compiled_metadata) END)
   OR entry->>'entity_kind' IS DISTINCT FROM 'o' OR entry->>'entity_id' IS DISTINCT FROM transition.object_id::text
   OR entry->>'entity_type' IS DISTINCT FROM transition.type_id::text OR entry->>'xid' IS DISTINCT FROM attempt.writer_xid::text
   OR entry->>'ver' IS DISTINCT FROM '1' OR entry->>'op' IS DISTINCT FROM 'create'
   OR result->'events' IS DISTINCT FROM jsonb_build_array(jsonb_build_object('sourceEpoch',event->>'sourceEpoch',
    'historyProfile',event->>'historyProfile','xid',event->>'xid','seq',event->>'seq')) THEN
   RAISE EXCEPTION 'atomic create result, image and journal correspondence required' USING ERRCODE='55000';END IF;
  SELECT to_jsonb(j) INTO actual FROM truss.journal j WHERE j.at=(entry->>'at')::timestamptz AND j.seq=(entry->>'seq')::bigint;
  IF actual IS DISTINCT FROM entry THEN RAISE EXCEPTION 'actual create journal required' USING ERRCODE='55000';END IF;
  PERFORM truss.runtime_history_group_qualified(jsonb_build_object('kind','object','id',identity->>'id','typeId',identity->>'typeId',
   'documentId',identity->'owner'->>'documentId','moduleId',identity->'owner'->>'moduleId',
   'sourceEpoch',attempt.context->>'sourceEpoch'),attempt.writer_xid,1,1,16777216,qualified_actor);
  FOR key_expected IN SELECT value FROM jsonb_array_elements(transition.after_keys) LOOP
   SELECT convert_from(r.original_reservation_bytes,'UTF8')::jsonb INTO STRICT actual
    FROM truss.object_key_reservation_bucket r
    -- Generated hashes route the lookup; original bytes establish equality.
    WHERE r.namespace_sha256=decode(substring(key_expected->>'namespace_sha256' FROM 3),'hex')
     AND r.key_sha256=decode(substring(key_expected->>'key_sha256' FROM 3),'hex')
     AND r.namespace_bytes=decode(substring(key_expected->>'namespace_bytes' FROM 3),'hex')
     AND r.key_bytes=decode(substring(key_expected->>'key_bytes' FROM 3),'hex');
   IF actual->>'objectId' IS DISTINCT FROM transition.object_id::text OR actual->>'typeId' IS DISTINCT FROM transition.type_id::text
    OR actual->>'keyNumber' IS DISTINCT FROM key_expected->>'key_num'
    OR decode(actual->>'contextBase64','base64') IS DISTINCT FROM decode(substring(key_expected->>'original_context_bytes' FROM 3),'hex') THEN
    RAISE EXCEPTION 'permanent create key reservation required' USING ERRCODE='55000';END IF;
  END LOOP;
  RETURN;
 END IF;

 IF attempt.context->'creationTransitionProfile' IS DISTINCT FROM '{"identity":"truss-unified-create-transition","version":"0.1","sha256":"765d7def5e677dba5d3ed5cdc841b1aa43eb2f4a493f1d2603ff3698536a5396"}'::jsonb
  OR transition.before_object IS NOT NULL OR transition.after_object IS NULL OR transition.journal IS DISTINCT FROM '[]'::jsonb
  OR attempt.writer_xid IS DISTINCT FROM transition.writer_xid OR attempt.writer_xid IS DISTINCT FROM pg_current_xact_id()
  OR attempt.actor_oid IS DISTINCT FROM qualified_actor
  OR transition.operation_index<0 OR transition.operation_index>=attempt.next_index
  OR jsonb_array_length(attempt.results)<>attempt.next_index THEN
  RAISE EXCEPTION 'original native creation transition profile and progress required' USING ERRCODE='55000';END IF;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 operation:=input->'operations'->transition.operation_index;result:=attempt.results->transition.operation_index;
 SELECT * INTO STRICT member FROM truss.runtime_create_member
  WHERE object_id=transition.object_id AND type_id=transition.type_id;
 SELECT * INTO STRICT creation FROM truss.runtime_create_group WHERE group_id=member.group_id;
 expected:=creation.expected_members->0;semantic:=convert_from(creation.semantic_bytes,'UTF8')::jsonb;
 IF member.operation_index<>0 OR jsonb_array_length(creation.expected_members)<>1
  OR creation.writer_xid IS DISTINCT FROM attempt.writer_xid OR creation.actor_oid IS DISTINCT FROM attempt.actor_oid
  OR creation.actor_name IS DISTINCT FROM session_user::text
  OR creation.original_document_bytes IS DISTINCT FROM attempt.documents_bytes
  OR creation.original_input_bytes IS DISTINCT FROM convert_to(jsonb_set(input-'preconditions','{operations}',jsonb_build_array(operation))::text,'UTF8')
  OR creation.original_key_bytes IS DISTINCT FROM convert_to('[]','UTF8') OR creation.receipt_storage_row_id IS NOT NULL
  OR operation->>'operation' IS DISTINCT FROM 'create_object' OR result->>'operation' IS DISTINCT FROM 'create_object'
  OR result->>'outcome' IS DISTINCT FROM 'created' OR result->>'version' IS DISTINCT FROM '1'
  OR result->'identity'->>'id' IS DISTINCT FROM transition.object_id::text
  OR result->'identity'->>'typeId' IS DISTINCT FROM transition.type_id::text
  OR semantic->'results' IS DISTINCT FROM jsonb_build_array(result)
  OR semantic->'mutationProfile' IS DISTINCT FROM input->'mutationProfile'
  OR semantic->'layoutProfile' IS DISTINCT FROM input->'layoutProfile'
  OR transition.after_object IS DISTINCT FROM expected->'object'
  OR transition.after_object->>'ver' IS DISTINCT FROM '1'
  OR transition.after_object->>'id' IS DISTINCT FROM transition.object_id::text
  OR transition.after_object->>'type_id' IS DISTINCT FROM transition.type_id::text THEN
  RAISE EXCEPTION 'exact original inner and outer creation correspondence required' USING ERRCODE='55000';END IF;
 IF input->'mutationProfile'=truss.runtime_owned_profile() AND
  transition.after_object-ARRAY['created_at','updated_at'] IS DISTINCT FROM
   truss.runtime_owned_object_image(attempt.id,transition.operation_index,'create:'||transition.operation_index::text,'after',NULL,attempt) THEN
  RAISE EXCEPTION 'original owned creation plan and physical image required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(k.value->'membership' ORDER BY (k.value->'membership'->>'key_num')::int),'[]'::jsonb)
  INTO keys FROM jsonb_array_elements(expected->'keys') k;
 IF transition.after_keys IS DISTINCT FROM keys THEN RAISE EXCEPTION 'original creation key image required' USING ERRCODE='55000';END IF;
 -- Validate original reservations even if later same-transaction changes/deletes
 -- have superseded the original live key memberships and object image.
 FOR key_expected IN SELECT value FROM jsonb_array_elements(expected->'keys') LOOP
  SELECT to_jsonb(r) INTO actual FROM truss.object_key_reservation_bucket r
   WHERE storage_row_id=(key_expected->'reservation'->>'storage_row_id')::bigint;
  SELECT g.generation INTO generation FROM truss.key_bucket_guard g
   WHERE namespace_sha256=decode(substring(key_expected->'membership'->>'namespace_sha256' FROM 3),'hex')
    AND key_sha256=decode(substring(key_expected->'membership'->>'key_sha256' FROM 3),'hex');
  IF actual IS DISTINCT FROM key_expected->'reservation' OR generation IS NULL
   OR generation<(key_expected->>'generation')::bigint THEN
   RAISE EXCEPTION 'original creation reservation and generation required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_create_transition_validate_qualified(bigint,oid,jsonb,bytea,truss.runtime_object_attempt,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_create_transition_validate(selected_transition bigint) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_create_transition_validate_qualified(selected_transition,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_create_transition_validate(bigint) FROM PUBLIC;

-- Reuse plans for repeated private point lookups; function-local settings
-- restore the caller policy on return, including exceptional return.
-- Independent value-update transitions retain references to the one immutable
-- physical journal payload. The producer verifies actual INSERT bytes before
-- issuing these references; digest fields here do not authorize raw SQL writes.
CREATE FUNCTION truss.runtime_owned_journal_reference(physical truss.journal) RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
 SELECT jsonb_build_object('referenceProfile','truss-native-journal-reference/0.1',
  'seq',(physical).seq,'at',(physical).at,'xid',(physical).xid,
  'entity_kind',(physical).entity_kind,'entity_id',(physical).entity_id,'entity_type',(physical).entity_type,
  'ver',(physical).ver,'op',(physical).op,'prop_id',(physical).prop_id,'old_value',(physical).old_value,'rev',(physical).rev,
  'eventSha256',(physical).new_value->'bytesSha256','originSha256',(physical).origin->'bytesSha256');
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_journal_reference(truss.journal) FROM PUBLIC;

-- Only semantic history consumers materialize payloads. Native settlement
-- compares compact references, while old full-row transition arrays stay valid.
CREATE FUNCTION truss.runtime_owned_journal_materialize(entries jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE entry jsonb;physical truss.journal%ROWTYPE;resolved jsonb[]:='{}';
BEGIN
 IF jsonb_typeof(entries) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'original transition journal array required' USING ERRCODE='55000';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(entries) LOOP
  IF entry ? 'referenceProfile' THEN
   IF entry->>'referenceProfile' IS DISTINCT FROM 'truss-native-journal-reference/0.1'
    OR jsonb_typeof(entry->'at') IS DISTINCT FROM 'string'
    OR jsonb_typeof(entry->'seq') IS DISTINCT FROM 'number' THEN
    RAISE EXCEPTION 'original typed journal reference required' USING ERRCODE='55000';END IF;
   BEGIN
    SELECT * INTO physical FROM truss.journal j WHERE j.at=(entry->>'at')::timestamptz AND j.seq=(entry->>'seq')::bigint;
   EXCEPTION WHEN invalid_datetime_format OR datetime_field_overflow OR invalid_text_representation OR numeric_value_out_of_range THEN
    RAISE EXCEPTION 'original typed journal reference required' USING ERRCODE='55000';
   END;
   IF NOT FOUND THEN RAISE EXCEPTION 'retained physical history unavailable' USING ERRCODE='P1010';END IF;
   IF entry IS DISTINCT FROM truss.runtime_owned_journal_reference(physical) THEN
    RAISE EXCEPTION 'exact original journal reference required' USING ERRCODE='55000';END IF;
   resolved:=array_append(resolved,to_jsonb(physical));
  ELSE resolved:=array_append(resolved,entry);END IF;
 END LOOP;
 RETURN to_jsonb(resolved);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_journal_materialize(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_row_validate_qualified(selected_id bigint,selected_type int,qualified_actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex SET plan_cache_mode='force_generic_plan' AS $$
DECLARE latest record;rebind record;actual jsonb;keys jsonb;entry jsonb;current_actor oid;creation_transition bigint;owned_transition record;owner record;root_type int;physical_journal truss.journal%ROWTYPE;
BEGIN
 current_actor:=qualified_actor;
 -- Owned creation semantics settle with the complete group and mandatory
 -- attempt trigger. Keep the legacy creation path; current owned authority and
 -- actual row/key closure are independently checked below on every row event.
 FOR creation_transition IN SELECT t.transition_id FROM truss.runtime_object_transition t
  JOIN truss.runtime_object_attempt a ON a.id=t.attempt_id
  WHERE t.object_id=selected_id AND t.type_id=selected_type AND t.writer_xid=pg_current_xact_id()
   AND t.before_object IS NULL
   AND a.context->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() LOOP
  PERFORM truss.runtime_create_transition_validate(creation_transition);
 END LOOP;
 -- Immutable transition semantics are checked at final group settlement and
 -- attempt commit. Row settlement independently rechecks current authority.
 FOR owned_transition IN
  SELECT t.operation_index,t.before_object,t.after_object,
   a.actor_oid AS original_actor,a.writer_xid AS original_writer,
   a.next_index AS original_next,
   CASE WHEN a.actor_oid IS NOT DISTINCT FROM current_actor
    AND a.writer_xid IS NOT DISTINCT FROM pg_current_xact_id()
    AND t.operation_index>=0 AND t.operation_index<a.next_index
    THEN a.result_count END AS original_result_count
  FROM truss.runtime_object_transition t JOIN truss.runtime_object_attempt a ON a.id=t.attempt_id
  WHERE t.object_id=selected_id AND t.type_id=selected_type AND t.writer_xid=pg_current_xact_id()
   AND a.context->'mutationProfile'=truss.runtime_owned_profile()
 LOOP
  IF owned_transition.original_actor IS DISTINCT FROM current_actor
   OR owned_transition.original_writer IS DISTINCT FROM pg_current_xact_id()
   OR owned_transition.operation_index<0 OR owned_transition.operation_index>=owned_transition.original_next
   OR owned_transition.original_result_count<>owned_transition.original_next THEN
   RAISE EXCEPTION 'original object operation progress and actor required' USING ERRCODE='55000';END IF;
  SELECT t.document_id,t.module INTO STRICT owner FROM truss.type_def t WHERE t.type_id=selected_type;
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,current_actor);
  IF NOT truss.runtime_object_values_readable_qualified(selected_type,current_actor) THEN RAISE EXCEPTION 'current original property readers required' USING ERRCODE='42501';END IF;
  FOR root_type IN SELECT DISTINCT (image->>'root_type')::int
   FROM jsonb_array_elements(jsonb_build_array(owned_transition.before_object,owned_transition.after_object)) images(image)
   WHERE image->>'root_type' IS NOT NULL LOOP
   SELECT t.document_id,t.module INTO STRICT owner FROM truss.type_def t WHERE t.type_id=root_type;
   IF NOT truss.runtime_can_read_qualified(owner.document_id,owner.module,current_actor) THEN RAISE EXCEPTION 'current historical root reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 END LOOP;
 -- Later ordinary mutations cannot suppress original registration dependencies.
 FOR rebind IN SELECT * FROM truss.runtime_catalog_rebind_transition t WHERE t.object_id=selected_id AND t.type_id=selected_type AND t.writer_xid=pg_current_xact_id() LOOP
  IF rebind.actor_oid IS DISTINCT FROM current_actor OR NOT EXISTS(SELECT 1 FROM truss.catalog_registration_request r
   WHERE r.registration_id=rebind.registration_id AND r.revision=rebind.revision AND r.writer_xid=rebind.writer_xid
    AND r.actor_oid=current_actor AND r.actor_name=session_user::text) THEN RAISE EXCEPTION 'current original rebind registration required' USING ERRCODE='55000';END IF;
  PERFORM truss.runtime_module_writer((SELECT document_id FROM truss.type_def WHERE type_id=selected_type),(SELECT module FROM truss.type_def WHERE type_id=selected_type));
  PERFORM truss.catalog_rebind_transition_reader((SELECT t FROM truss.runtime_catalog_rebind_transition t WHERE t.transition_id=rebind.transition_id));
 END LOOP;
 FOR rebind IN SELECT * FROM truss.runtime_catalog_key_backfill t WHERE t.object_id=selected_id AND t.type_id=selected_type AND t.writer_xid=pg_current_xact_id() LOOP
  IF rebind.actor_oid IS DISTINCT FROM current_actor OR NOT EXISTS(SELECT 1 FROM truss.catalog_registration_request r
   WHERE r.registration_id=rebind.registration_id AND r.revision=rebind.revision AND r.writer_xid=rebind.writer_xid
    AND r.actor_oid=current_actor AND r.actor_name=session_user::text) THEN RAISE EXCEPTION 'current original key registration required' USING ERRCODE='55000';END IF;
  PERFORM truss.runtime_module_writer((SELECT document_id FROM truss.type_def WHERE type_id=selected_type),(SELECT module FROM truss.type_def WHERE type_id=selected_type));
  PERFORM truss.catalog_key_backfill_transition_reader((SELECT t FROM truss.runtime_catalog_key_backfill t WHERE t.transition_id=rebind.transition_id));
 END LOOP;
 SELECT * INTO latest FROM (
  SELECT transition_id,writer_xid,after_object,after_keys,attempt_id,NULL::uuid registration_id,'ordinary'::text transition_kind FROM truss.runtime_object_transition WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()
  UNION ALL SELECT transition_id,writer_xid,after_object,after_keys,NULL::uuid,registration_id,'rebind'::text FROM truss.runtime_catalog_rebind_transition WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()
  UNION ALL SELECT transition_id,writer_xid,object_image,after_keys,NULL::uuid,registration_id,'key_backfill'::text FROM truss.runtime_catalog_key_backfill WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()) t ORDER BY transition_id DESC LIMIT 1;
 IF NOT FOUND THEN RAISE EXCEPTION 'current registered object transition required' USING ERRCODE='55000';END IF;
 IF latest.registration_id IS NOT NULL THEN
  IF NOT EXISTS(SELECT 1 FROM truss.catalog_registration_request r WHERE r.registration_id=latest.registration_id AND r.writer_xid=latest.writer_xid AND r.actor_oid=current_actor AND r.actor_name=session_user::text) THEN RAISE EXCEPTION 'current original registration owner required' USING ERRCODE='55000';END IF;
  PERFORM truss.runtime_module_writer((SELECT document_id FROM truss.type_def WHERE type_id=selected_type),(SELECT module FROM truss.type_def WHERE type_id=selected_type));
  IF latest.transition_kind='key_backfill' THEN
   PERFORM truss.catalog_key_backfill_transition_reader((SELECT t FROM truss.runtime_catalog_key_backfill t WHERE t.transition_id=latest.transition_id));
  ELSE PERFORM truss.catalog_rebind_transition_reader((SELECT t FROM truss.runtime_catalog_rebind_transition t WHERE t.transition_id=latest.transition_id));END IF;
 ELSIF NOT EXISTS(SELECT 1 FROM truss.runtime_object_attempt WHERE id=latest.attempt_id AND writer_xid=latest.writer_xid AND actor_oid=current_actor) THEN RAISE EXCEPTION 'current mutation owner required' USING ERRCODE='55000';END IF;
 SELECT to_jsonb(o) INTO actual FROM truss.object o WHERE id=selected_id AND type_id=selected_type;
 SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]'::jsonb) INTO keys FROM truss.object_key_bucket k WHERE k.object_id=selected_id AND k.type_id=selected_type;
 IF actual IS DISTINCT FROM latest.after_object OR keys IS DISTINCT FROM latest.after_keys THEN RAISE EXCEPTION 'exact final object/key state required' USING ERRCODE='55000';END IF;
 FOR entry IN SELECT j.value FROM (SELECT journal FROM truss.runtime_object_transition WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id() UNION ALL SELECT journal FROM truss.runtime_catalog_rebind_transition WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()) t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j LOOP
  SELECT * INTO physical_journal FROM truss.journal j WHERE j.at=(entry->>'at')::timestamptz AND j.seq=(entry->>'seq')::bigint;
  IF NOT FOUND OR (CASE WHEN entry ? 'referenceProfile'
   THEN entry IS DISTINCT FROM truss.runtime_owned_journal_reference(physical_journal)
   ELSE entry IS DISTINCT FROM to_jsonb(physical_journal) END) THEN
   RAISE EXCEPTION 'exact mutation journal required' USING ERRCODE='55000';END IF;
 END LOOP;
 -- Key encoding belongs to the trusted producer. Its exact checked rows are
 -- retained in after_keys and compared with current native membership above.
 -- Re-encoding every key at finish and again for each deferred row event repeats
 -- the producer's semantic work without adding a new relational guarantee.
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_row_validate_qualified(bigint,int,oid) FROM PUBLIC;
CREATE FUNCTION truss.runtime_object_validate(selected_id bigint,selected_type int) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.runtime_owned_row_validate_qualified(selected_id,selected_type,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_validate(bigint,int) FROM PUBLIC;

CREATE FUNCTION truss.object_group_finish(attempt_id uuid) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE input_operations jsonb;
 attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;request jsonb;semantic jsonb;bytes bytea;receipt_bytes bytea;receipt truss.request_receipt%ROWTYPE;
 ns bytea;rk bytea;operation jsonb;selected record;index int:=0;owner record;current_actor oid;sealed record;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id FOR UPDATE NOWAIT;
 IF attempt.writer_xid<>pg_current_xact_id() OR attempt.actor_oid<>truss.runtime_person(false) OR attempt.complete THEN RAISE EXCEPTION 'current unfinished group required' USING ERRCODE='55000';END IF;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;request:=convert_from(attempt.request_bytes,'UTF8')::jsonb;
 input_operations:=input->'operations';
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  IF attempt.results<>'[]'::jsonb OR attempt.aliases<>'[]'::jsonb THEN
   RAISE EXCEPTION 'unassembled original owned attempt required' USING ERRCODE='55000';END IF;
  SELECT coalesce(jsonb_agg(p.result ORDER BY p.operation_index),'[]'::jsonb) results,
   coalesce(jsonb_agg(jsonb_build_object('alias',p.plan->'operation'->>'alias','identity',p.result->'identity') ORDER BY p.operation_index)
    FILTER(WHERE (p.plan->'operation') ? 'alias'),'[]'::jsonb) aliases,
   array_agg(p.operation_index ORDER BY p.operation_index) ordinals,
   count(*) FILTER(WHERE p.result IS NULL) missing,bool_and(p.writer_xid=attempt.writer_xid) writer_matches
  INTO sealed FROM truss.runtime_owned_operation p WHERE p.attempt_id=attempt.id;
  IF sealed.missing<>0 OR sealed.writer_matches IS DISTINCT FROM true
   OR sealed.ordinals IS DISTINCT FROM ARRAY(SELECT generate_series(0,attempt.next_index-1)) THEN
   RAISE EXCEPTION 'complete ordered sealed owned results required' USING ERRCODE='55000';END IF;
  attempt.results:=sealed.results;attempt.aliases:=sealed.aliases;
 END IF;
 IF attempt.next_index<>jsonb_array_length(input_operations) OR jsonb_array_length(attempt.results)<>attempt.next_index THEN RAISE EXCEPTION 'complete ordered results required' USING ERRCODE='55000';END IF;
 IF attempt.context ? 'creationTransitionProfile' THEN
  IF attempt.context->'creationTransitionProfile' IS DISTINCT FROM '{"identity":"truss-unified-create-transition","version":"0.1","sha256":"765d7def5e677dba5d3ed5cdc841b1aa43eb2f4a493f1d2603ff3698536a5396"}'::jsonb AND attempt.context->'creationTransitionProfile' IS DISTINCT FROM '{"identity":"truss-unified-create-transition","version":"0.2","sha256":"073782e2517f2a7e26c8d6479c6266ececf68963681ccfb6a380e9cd16f2e11b"}'::jsonb THEN
   RAISE EXCEPTION 'known original creation storage profile required' USING ERRCODE='55000';END IF;
  IF EXISTS(
   SELECT 1 FROM jsonb_array_elements(input_operations) WITH ORDINALITY o(operation,ordinal)
   LEFT JOIN truss.runtime_object_transition t ON t.attempt_id=attempt.id AND t.operation_index=o.ordinal-1
    AND t.before_object IS NULL AND t.object_id::text=attempt.results->(o.ordinal-1)::int->'identity'->>'id'
    AND t.type_id::text=attempt.results->(o.ordinal-1)::int->'identity'->>'typeId'
   WHERE o.operation->>'operation'='create_object' GROUP BY o.ordinal HAVING count(t.transition_id)<>1) THEN
   RAISE EXCEPTION 'one original transition for every completed create required' USING ERRCODE='55000';END IF;
 ELSIF EXISTS(SELECT 1 FROM truss.runtime_object_transition WHERE runtime_object_transition.attempt_id=attempt.id AND before_object IS NULL) THEN
  RAISE EXCEPTION 'historical attempts have no synthetic creation transitions' USING ERRCODE='55000';END IF;
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  PERFORM truss.runtime_owned_graph_validate_attempt(attempt.id,true);
 ELSE PERFORM truss.runtime_graph_validate(true);END IF;
 PERFORM truss.runtime_edge_authorize(attempt_id);
 -- Marker refresh above can fire triggers. Recheck mutable progress before
 -- reusing the already closed immutable owned result-slot census.
 IF input->'mutationProfile'=truss.runtime_owned_profile() AND NOT EXISTS(
  SELECT 1 FROM truss.runtime_object_attempt a WHERE a.id=attempt.id
   AND a.actor_oid=attempt.actor_oid AND a.writer_xid=attempt.writer_xid
   AND a.next_index=attempt.next_index AND NOT a.complete
   AND a.results='[]'::jsonb AND a.aliases='[]'::jsonb
   AND (SELECT count(*) FROM truss.runtime_owned_operation p
    WHERE p.attempt_id=a.id AND p.result IS NOT NULL)=a.next_index) THEN
  RAISE EXCEPTION 'original unfinished owned settlement progress required' USING ERRCODE='55000';END IF;
 -- Marker refresh and authorization above may execute write triggers. Issue
 -- identity only after them, for this read-only final-edge validation phase.
 -- Each edge still resolves live module policy/membership independently.
 current_actor:=truss.runtime_person(false);
 IF current_actor IS DISTINCT FROM attempt.actor_oid THEN RAISE EXCEPTION 'original current finishing actor required' USING ERRCODE='42501';END IF;
 FOR owner IN SELECT DISTINCT edge_id,rel_type_id FROM truss.runtime_edge_transition WHERE runtime_edge_transition.attempt_id=object_group_finish.attempt_id LOOP
  IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
   PERFORM truss.runtime_owned_edge_validate_in_input_qualified(owner.edge_id,owner.rel_type_id,input,attempt.input_bytes,attempt,current_actor);
  ELSE PERFORM truss.runtime_edge_validate(owner.edge_id,owner.rel_type_id);END IF;
 END LOOP;
 semantic:=jsonb_build_object('interfaceVersion','truss-group-result/0.1.0','executedCatalogRevision',(SELECT rev::text FROM truss.schema_head WHERE id=1),
  'layoutProfile',input->'layoutProfile','mutationProfile',input->'mutationProfile','results',attempt.results,'aliases',attempt.aliases);
 bytes:=convert_to(semantic::text,'UTF8');IF octet_length(bytes)>16777216 THEN RAISE EXCEPTION 'bounded complete results required' USING ERRCODE='54000';END IF;
 IF request<>'{"state":"none"}'::jsonb THEN
  ns:=convert_to(attempt.context->>'authorizedScopeIdentity','UTF8');rk:=convert_to(request->'identity'->>'requestId','UTF8');
  IF EXISTS(SELECT 1 FROM truss.request_receipt WHERE namespace_sha256=sha256(ns) AND request_sha256=sha256(rk) AND namespace_identity_utf8=ns AND request_id_utf8=rk) THEN RAISE EXCEPTION 'exact request already settled' USING ERRCODE='P1001';END IF;
  IF (SELECT count(*) FROM truss.runtime_object_attempt a WHERE a.writer_xid=attempt.writer_xid AND NOT a.complete
   AND a.context->>'authorizedScopeIdentity'=attempt.context->>'authorizedScopeIdentity'
   AND convert_from(a.request_bytes,'UTF8')::jsonb->'identity'->>'requestId'=request->'identity'->>'requestId')<>1 THEN RAISE EXCEPTION 'one original request attempt required' USING ERRCODE='55000';END IF;
  receipt_bytes:=convert_to(jsonb_build_object('profile','truss-object-group-receipt/0.1','attemptId',attempt_id::text,
   'inputBase64',replace(encode(attempt.input_bytes,'base64'),chr(10),''),'semantic',semantic)::text,'UTF8');
  INSERT INTO truss.request_receipt(namespace_identity_utf8,request_id_utf8,original_writer_xid,original_writer_context_bytes,lifecycle_generation,payload_state,original_receipt_bytes)
  VALUES(ns,rk,attempt.writer_xid,convert_to(jsonb_build_object('profile','truss-object-group-writer/0.1','attemptId',attempt_id::text,
   'xid',attempt.writer_xid::text,'actorOid',attempt.actor_oid::text,'actor',session_user::text)::text,'UTF8'),0,'complete',receipt_bytes) RETURNING * INTO receipt;
  IF NOT FOUND OR receipt.storage_row_id IS NULL
   OR receipt.namespace_identity_utf8 IS DISTINCT FROM ns OR receipt.request_id_utf8 IS DISTINCT FROM rk
   OR receipt.original_writer_xid IS DISTINCT FROM attempt.writer_xid OR receipt.payload_state IS DISTINCT FROM 'complete'
   OR receipt.original_receipt_bytes IS DISTINCT FROM receipt_bytes THEN
   RAISE EXCEPTION 'exact original request receipt required' USING ERRCODE='55000';END IF;
  UPDATE truss.request_receipt_route_guard SET generation=generation+1 WHERE namespace_sha256=sha256(ns) AND request_sha256=sha256(rk);
 END IF;
 UPDATE truss.runtime_object_attempt SET results=attempt.results,aliases=attempt.aliases,complete=true,receipt_id=receipt.storage_row_id,expected_receipt=CASE WHEN receipt.storage_row_id IS NOT NULL THEN to_jsonb(receipt) END,
  position_bytes=CASE WHEN receipt.storage_row_id IS NOT NULL THEN truss.runtime_receipt_position(attempt.context,receipt.storage_row_id,attempt.writer_xid) END WHERE id=attempt_id;
 current_actor:=truss.runtime_person(false);
 IF current_actor IS DISTINCT FROM attempt.actor_oid THEN RAISE EXCEPTION 'original current finishing actor required' USING ERRCODE='42501';END IF;
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  -- Close final native object/key images as one relation. Deferred row/journal
  -- guards still observe later caller work and current permission changes.
  IF EXISTS(WITH latest AS MATERIALIZED (
   SELECT DISTINCT ON(t.object_id,t.type_id) t.object_id,t.type_id,t.after_object,t.after_keys
   FROM truss.runtime_object_transition t WHERE t.attempt_id=attempt.id
   ORDER BY t.object_id,t.type_id,t.transition_id DESC)
   SELECT 1 FROM latest l LEFT JOIN truss.object o ON o.id=l.object_id AND o.type_id=l.type_id
   LEFT JOIN LATERAL (SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]'::jsonb) image
    FROM truss.object_key_bucket k WHERE k.object_id=l.object_id AND k.type_id=l.type_id) keys ON true
   WHERE to_jsonb(o) IS DISTINCT FROM l.after_object OR keys.image IS DISTINCT FROM l.after_keys) THEN
   RAISE EXCEPTION 'exact final object/key state required' USING ERRCODE='55000';END IF;
 ELSE
  FOR owner IN SELECT DISTINCT object_id,type_id FROM truss.runtime_object_transition WHERE runtime_object_transition.attempt_id=object_group_finish.attempt_id LOOP
   PERFORM truss.runtime_owned_row_validate_qualified(owner.object_id,owner.type_id,current_actor);
  END LOOP;
 END IF;
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  -- Group settlement rechecks the complete distinct owner/type set. Repeating
  -- the same policy/schema lookup for every operation adds no authority.
  PERFORM truss.runtime_owned_group_validate(attempt.id,true);
 ELSE
  FOR operation IN SELECT value FROM jsonb_array_elements(input_operations) LOOP
   SELECT * INTO STRICT selected FROM truss.runtime_owned_operation_owner_qualified(operation,input_operations,index,current_actor);PERFORM truss.runtime_module_writer_qualified(selected.document_id,selected.module,current_actor);index:=index+1;
  END LOOP;
 END IF;
 RETURN convert_to(jsonb_build_object('outcome','success','disposition','applied','durability','pending','semantic',semantic,
  'receiptToken',CASE WHEN receipt.storage_row_id IS NOT NULL THEN truss.runtime_receipt_token(truss.runtime_receipt_position(attempt.context,receipt.storage_row_id,attempt.writer_xid)) END)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.object_group_finish(uuid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_object_attempt_guard() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_OP='DELETE' OR OLD.complete THEN RAISE EXCEPTION 'settled attempt immutable' USING ERRCODE='55000';END IF;
 IF ROW(OLD.id,OLD.writer_xid,OLD.actor_oid,OLD.input_bytes,OLD.documents_bytes,OLD.request_bytes,OLD.context)
  IS DISTINCT FROM ROW(NEW.id,NEW.writer_xid,NEW.actor_oid,NEW.input_bytes,NEW.documents_bytes,NEW.request_bytes,NEW.context)
 THEN RAISE EXCEPTION 'original attempt immutable' USING ERRCODE='55000';END IF;
 RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_attempt_guard() FROM PUBLIC;
CREATE TRIGGER runtime_object_attempt_guard BEFORE UPDATE OR DELETE ON truss.runtime_object_attempt FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_attempt_guard();

CREATE FUNCTION truss.runtime_object_commit_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;actual jsonb;expected jsonb;endpoint record;selected_edge bigint;selected_relation int;journal_kind text;journal_id bigint;journal_type int;current_actor oid;journal_problem boolean;expected_count bigint;distinct_expected bigint;actual_count bigint;
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=session_user AND rolsuper) THEN RETURN NULL;END IF;
 -- One fresh actor per constraint-trigger event. Resource authorization stays
 -- live below; this identity is never retained across events or commands.
 IF TG_TABLE_NAME IN ('object','runtime_object_transition','runtime_catalog_rebind_transition','runtime_catalog_key_backfill','edge','runtime_edge_transition') THEN
  current_actor:=truss.runtime_person(false);END IF;
 IF TG_TABLE_NAME='runtime_object_attempt' THEN
  SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=NEW.id;
  IF NOT attempt.complete OR attempt.writer_xid<>pg_current_xact_id() OR attempt.actor_oid<>truss.runtime_person(false)
   OR attempt.next_index<>jsonb_array_length(convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations')
   OR jsonb_array_length(attempt.results)<>attempt.next_index THEN RAISE EXCEPTION 'complete current mutation attempt required' USING ERRCODE='55000';END IF;
  IF convert_from(attempt.input_bytes,'UTF8')::jsonb->'mutationProfile'=truss.runtime_owned_profile() THEN PERFORM truss.runtime_owned_group_validate(attempt.id,false);END IF;
  IF attempt.receipt_id IS NOT NULL THEN
   SELECT to_jsonb(r) INTO actual FROM truss.request_receipt r WHERE storage_row_id=attempt.receipt_id;
   IF actual IS DISTINCT FROM attempt.expected_receipt THEN RAISE EXCEPTION 'exact original group receipt required' USING ERRCODE='55000';END IF;
   IF attempt.position_bytes IS DISTINCT FROM truss.runtime_receipt_position(attempt.context,attempt.receipt_id,attempt.writer_xid) THEN RAISE EXCEPTION 'exact original receipt position required' USING ERRCODE='55000';END IF;
  END IF;
 ELSIF TG_TABLE_NAME='object' THEN
  IF TG_OP='DELETE' THEN PERFORM truss.runtime_owned_row_validate_qualified(OLD.id,OLD.type_id,current_actor);ELSE PERFORM truss.runtime_owned_row_validate_qualified(NEW.id,NEW.type_id,current_actor);END IF;
 ELSIF TG_TABLE_NAME IN ('runtime_object_transition','runtime_catalog_rebind_transition','runtime_catalog_key_backfill') THEN PERFORM truss.runtime_owned_row_validate_qualified(NEW.object_id,NEW.type_id,current_actor);
 ELSIF TG_TABLE_NAME='edge' THEN
  IF TG_OP='DELETE' THEN PERFORM truss.runtime_owned_edge_validate_in_input_qualified(OLD.id,OLD.rel_type_id,NULL,NULL,NULL,current_actor);ELSE PERFORM truss.runtime_owned_edge_validate_in_input_qualified(NEW.id,NEW.rel_type_id,NULL,NULL,NULL,current_actor);END IF;
 ELSIF TG_TABLE_NAME='runtime_edge_transition' THEN PERFORM truss.runtime_owned_edge_validate_in_input_qualified(NEW.edge_id,NEW.rel_type_id,NULL,NULL,NULL,current_actor);
 ELSE RAISE EXCEPTION 'registered mutation commit event required' USING ERRCODE='55000';END IF;
 -- Attempt and catalog settlement still validate the complete affected graph.
 -- Row events recheck every endpoint they can change, avoiding a complete
 -- transaction scan for each row. No validation cache survives later writes.
 IF TG_TABLE_NAME='runtime_object_attempt' THEN
  IF attempt.context->'mutationProfile'=truss.runtime_owned_profile() THEN
   PERFORM truss.runtime_owned_graph_validate_attempt(attempt.id,false);
  ELSE PERFORM truss.runtime_graph_validate(false);END IF;
 ELSIF TG_TABLE_NAME='object' THEN
  -- Values/version/timestamps cannot change topology or multiplicity. Every
  -- actual edge/ownership/catalog change still queues its own structural check.
  IF TG_OP='DELETE' THEN PERFORM truss.runtime_graph_validate_object_qualified(OLD.id,OLD.type_id,false,current_actor);
  ELSIF TG_OP<>'UPDATE' OR ROW(OLD.id,OLD.type_id,OLD.root_id,OLD.root_type,OLD.rev)
    IS DISTINCT FROM ROW(NEW.id,NEW.type_id,NEW.root_id,NEW.root_type,NEW.rev) THEN
   PERFORM truss.runtime_graph_validate_object_qualified(NEW.id,NEW.type_id,false,current_actor);END IF;
 ELSIF TG_TABLE_NAME='runtime_object_transition' THEN
  IF (NEW.before_object-ARRAY['props','retained','ver','created_at','updated_at'])
    IS DISTINCT FROM (NEW.after_object-ARRAY['props','retained','ver','created_at','updated_at']) THEN
   PERFORM truss.runtime_graph_validate_object_qualified(NEW.object_id,NEW.type_id,false,current_actor);END IF;
 ELSIF TG_TABLE_NAME IN ('runtime_catalog_rebind_transition','runtime_catalog_key_backfill') THEN
  PERFORM truss.runtime_graph_validate_object_qualified(NEW.object_id,NEW.type_id,false,current_actor);
 ELSE
  -- Include old and new endpoints of every transition for this edge in this
  -- transaction, including retargets and deletion. Final-edge endpoints alone
  -- would miss a formerly connected object's minimum multiplicity.
  IF TG_TABLE_NAME='runtime_edge_transition' THEN selected_edge:=NEW.edge_id;selected_relation:=NEW.rel_type_id;
  ELSIF TG_OP='DELETE' THEN selected_edge:=OLD.id;selected_relation:=OLD.rel_type_id;
  ELSE selected_edge:=NEW.id;selected_relation:=NEW.rel_type_id;END IF;
  FOR endpoint IN SELECT DISTINCT (i.value->>'id')::bigint id,(i.value->>'typeId')::int type_id
   FROM truss.runtime_edge_transition t
   CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(t.old_source,t.old_target,t.source_identity,t.target_identity)) i
   WHERE t.writer_xid=pg_current_xact_id() AND i.value<>'null'::jsonb
    AND t.edge_id=selected_edge
    AND t.rel_type_id=selected_relation
  LOOP
   PERFORM truss.runtime_graph_validate_object_qualified(endpoint.id,endpoint.type_id,false,current_actor);
  END LOOP;
 END IF;
 -- Ordinary entity events compare the complete journal for their typed owner.
 -- Mandatory attempt, catalog and legacy settlement keep transaction closure.
 IF TG_TABLE_NAME='object' THEN
  journal_kind:='o';
  IF TG_OP='DELETE' THEN journal_id:=OLD.id;journal_type:=OLD.type_id;
  ELSE journal_id:=NEW.id;journal_type:=NEW.type_id;END IF;
 ELSIF TG_TABLE_NAME='runtime_object_transition' THEN
  journal_kind:='o';journal_id:=NEW.object_id;journal_type:=NEW.type_id;
 ELSIF TG_TABLE_NAME='edge' THEN
  journal_kind:='e';
  IF TG_OP='DELETE' THEN journal_id:=OLD.id;journal_type:=OLD.rel_type_id;
  ELSE journal_id:=NEW.id;journal_type:=NEW.rel_type_id;END IF;
 ELSIF TG_TABLE_NAME='runtime_edge_transition' THEN
  journal_kind:='e';journal_id:=NEW.edge_id;journal_type:=NEW.rel_type_id;
 END IF;
 -- Match each claim to its indexed physical row without aggregating event
 -- payloads. Keep entity and transaction statements separate so generic plans
 -- retain the entity index instead of scanning the whole xid for every object.
 IF journal_kind IS NOT NULL THEN
  WITH expected(value) AS MATERIALIZED (
   SELECT g.expected_members->m.operation_index->'journal'
   FROM truss.runtime_create_member m JOIN truss.runtime_create_group g USING(group_id)
   WHERE g.writer_xid=pg_current_xact_id() AND journal_kind='o' AND m.object_id=journal_id AND m.type_id=journal_type
   UNION ALL SELECT j.value FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
   WHERE t.writer_xid=pg_current_xact_id() AND journal_kind='o' AND t.object_id=journal_id AND t.type_id=journal_type
   UNION ALL SELECT j.value FROM truss.runtime_catalog_rebind_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
   WHERE t.writer_xid=pg_current_xact_id() AND journal_kind='o' AND t.object_id=journal_id AND t.type_id=journal_type
   UNION ALL SELECT j.value FROM truss.runtime_edge_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
   WHERE t.writer_xid=pg_current_xact_id() AND journal_kind='e' AND t.edge_id=journal_id AND t.rel_type_id=journal_type)
  SELECT count(*),count(DISTINCT ROW((e.value->>'at')::timestamptz,(e.value->>'seq')::bigint)),
   coalesce(bool_or((p.physical).seq IS NULL OR CASE WHEN e.value ? 'referenceProfile'
    THEN e.value IS DISTINCT FROM truss.runtime_owned_journal_reference(p.physical)
    ELSE e.value IS DISTINCT FROM to_jsonb(p.physical) END),false)
  INTO expected_count,distinct_expected,journal_problem
  FROM expected e LEFT JOIN LATERAL (
   SELECT j physical FROM truss.journal j WHERE j.at=(e.value->>'at')::timestamptz AND j.seq=(e.value->>'seq')::bigint
    AND j.xid=pg_current_xact_id() AND j.entity_kind=journal_kind AND j.entity_id=journal_id AND j.entity_type=journal_type OFFSET 0) p ON true;
  SELECT count(*) INTO actual_count FROM truss.journal j WHERE j.xid=pg_current_xact_id() AND j.entity_kind=journal_kind AND j.entity_id=journal_id AND j.entity_type=journal_type;
 ELSE
  WITH expected(value) AS MATERIALIZED (
   SELECT g.expected_members->m.operation_index->'journal'
   FROM truss.runtime_create_member m JOIN truss.runtime_create_group g USING(group_id)
   WHERE g.writer_xid=pg_current_xact_id()
   UNION ALL SELECT j.value FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
   WHERE t.writer_xid=pg_current_xact_id()
   UNION ALL SELECT j.value FROM truss.runtime_catalog_rebind_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
   WHERE t.writer_xid=pg_current_xact_id()
   UNION ALL SELECT j.value FROM truss.runtime_edge_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
   WHERE t.writer_xid=pg_current_xact_id())
  SELECT count(*),count(DISTINCT ROW((e.value->>'at')::timestamptz,(e.value->>'seq')::bigint)),
   coalesce(bool_or((p.physical).seq IS NULL OR CASE WHEN e.value ? 'referenceProfile'
    THEN e.value IS DISTINCT FROM truss.runtime_owned_journal_reference(p.physical)
    ELSE e.value IS DISTINCT FROM to_jsonb(p.physical) END),false)
  INTO expected_count,distinct_expected,journal_problem
  FROM expected e LEFT JOIN LATERAL (
   SELECT j physical FROM truss.journal j WHERE j.at=(e.value->>'at')::timestamptz AND j.seq=(e.value->>'seq')::bigint
    AND j.xid=pg_current_xact_id() OFFSET 0) p ON true;
  SELECT count(*) INTO actual_count FROM truss.journal j WHERE j.xid=pg_current_xact_id();
 END IF;
 IF journal_problem OR expected_count<>distinct_expected OR expected_count<>actual_count THEN
  RAISE EXCEPTION 'complete mutation journal required' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_commit_check() FROM PUBLIC;
CREATE CONSTRAINT TRIGGER runtime_object_changed_commit AFTER UPDATE OR DELETE ON truss.object DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check();
CREATE CONSTRAINT TRIGGER runtime_object_attempt_commit AFTER INSERT ON truss.runtime_object_attempt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check();
CREATE CONSTRAINT TRIGGER runtime_object_transition_commit AFTER INSERT ON truss.runtime_object_transition DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check();
ALTER TABLE truss.object ENABLE ALWAYS TRIGGER runtime_object_changed_commit;
ALTER TABLE truss.runtime_object_attempt ENABLE ALWAYS TRIGGER runtime_object_attempt_commit;
ALTER TABLE truss.runtime_object_transition ENABLE ALWAYS TRIGGER runtime_object_transition_commit;

-- Resolve endpoints as objects, retaining the object/edge alias category.
CREATE FUNCTION truss.runtime_edge_endpoint(reference jsonb,attempt_id uuid,operation_index int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;operations jsonb;identity jsonb;selected truss.type_def%ROWTYPE;object_row truss.object%ROWTYPE;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id;
 operations:=convert_from(attempt.input_bytes,'UTF8')::jsonb->'operations';
 IF reference->>'state'='stored' AND reference-ARRAY['state','identity']='{}'::jsonb THEN identity:=reference->'identity';
 ELSIF reference->>'state'='alias' AND reference-ARRAY['state','alias']='{}'::jsonb THEN
  IF (SELECT count(*) FROM jsonb_array_elements(operations) WITH ORDINALITY o(value,ord)
   WHERE ord<=operation_index AND value->>'operation'='create_object' AND value->>'alias'=reference->>'alias')<>1 THEN
   RAISE EXCEPTION 'prior object endpoint alias required' USING ERRCODE='22023';END IF;
  SELECT value->'identity' INTO STRICT identity FROM jsonb_array_elements(attempt.aliases) WHERE value->>'alias'=reference->>'alias';
 ELSE RAISE EXCEPTION 'qualified object endpoint required' USING ERRCODE='22023';END IF;
 IF jsonb_typeof(identity->'typeId') IS DISTINCT FROM 'string' OR jsonb_typeof(identity->'definitionPin') IS DISTINCT FROM 'string' THEN
  RAISE EXCEPTION 'exact object endpoint identity required' USING ERRCODE='22023';END IF;
 selected:=truss.runtime_condition_type(identity);IF NOT truss.runtime_can_read(selected.document_id,selected.module) THEN RAISE EXCEPTION 'endpoint reader required' USING ERRCODE='42501';END IF;
 SELECT * INTO object_row FROM truss.object WHERE id=(identity->>'id')::bigint AND type_id=selected.type_id FOR UPDATE NOWAIT;
 IF NOT FOUND THEN RAISE EXCEPTION 'endpoint absent' USING ERRCODE='P1004';END IF;
 IF object_row.root_id IS NOT NULL THEN
  RAISE EXCEPTION 'rootless endpoint required' USING ERRCODE='0A000';END IF;
 RETURN identity;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_endpoint(jsonb,uuid,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_edge_metadata(attempt_id uuid,operation_index int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;operation jsonb;relation truss.rel_def%ROWTYPE;
 identity jsonb;prior truss.edge%ROWTYPE;source_identity jsonb;target_identity jsonb;old_source jsonb;old_target jsonb;
 values jsonb;retained jsonb;entry jsonb;name text;order_key jsonb;endpoint truss.type_def%ROWTYPE;pin record;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id FOR UPDATE NOWAIT;
 IF attempt.writer_xid<>pg_current_xact_id() OR attempt.actor_oid<>truss.runtime_person(false) OR attempt.complete OR attempt.next_index<>operation_index THEN
  RAISE EXCEPTION 'current ordered edge attempt required' USING ERRCODE='55000';END IF;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;operation:=input->'operations'->operation_index;
 IF operation->>'operation'<>'create_edge' AND ((operation->'target'->>'state'='stored' AND (operation->'target')-ARRAY['state','identity']<>'{}'::jsonb)
  OR (operation->'target'->>'state'='alias' AND ((operation->'target')-ARRAY['state','alias']<>'{}'::jsonb OR jsonb_typeof(operation->'target'->'alias') IS DISTINCT FROM 'string'))) THEN
  RAISE EXCEPTION 'closed exact edge reference required' USING ERRCODE='22023';END IF;
 relation:=truss.runtime_operation_relationship(operation,input->'operations',operation_index);
 PERFORM truss.runtime_module_writer(relation.document_id,relation.module);
 IF relation.lifecycle<>'independent' OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL THEN
  RAISE EXCEPTION 'directed independent relationship required' USING ERRCODE='0A000';END IF;
 IF operation->>'operation'='create_edge' THEN
  IF operation-ARRAY['operation','relationshipDefinitionPin','source','target','values','orderKey','alias']<>'{}'::jsonb
   OR operation ? 'alias' AND (jsonb_typeof(operation->'alias') IS DISTINCT FROM 'string' OR octet_length(operation->>'alias') NOT BETWEEN 1 AND 1024) THEN
   RAISE EXCEPTION 'closed edge create required' USING ERRCODE='22023';END IF;
  retained:='{}';values:=operation->'values';order_key:=operation->'orderKey';
  source_identity:=truss.runtime_edge_endpoint(operation->'source',attempt_id,operation_index);
  target_identity:=truss.runtime_edge_endpoint(operation->'target',attempt_id,operation_index);
 ELSE
  IF operation->'target'->>'state'='stored' THEN identity:=operation->'target'->'identity';
  ELSE SELECT value->'identity' INTO STRICT identity FROM jsonb_array_elements(attempt.aliases) WHERE value->>'alias'=operation->'target'->>'alias';END IF;
  SELECT * INTO prior FROM truss.edge WHERE id=(identity->>'id')::bigint AND rel_type_id=relation.rel_type_id FOR UPDATE NOWAIT;
  IF NOT FOUND THEN RAISE EXCEPTION 'edge absent' USING ERRCODE='P1004';END IF;
  IF operation ? 'expectedVersion' AND (jsonb_typeof(operation->'expectedVersion') IS DISTINCT FROM 'string' OR operation->>'expectedVersion' IS DISTINCT FROM prior.ver::text) THEN
   RAISE EXCEPTION 'expected edge version failed' USING ERRCODE='P1003';END IF;
  SELECT * INTO STRICT endpoint FROM truss.type_def WHERE type_id=prior.source_type;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',endpoint.type_id);
  old_source:=jsonb_build_object('id',prior.source_id::text,'typeId',prior.source_type::text,'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',endpoint.document_id,'moduleId',endpoint.module));
  SELECT * INTO STRICT endpoint FROM truss.type_def WHERE type_id=prior.target_type;
  SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',endpoint.type_id);
  old_target:=jsonb_build_object('id',prior.target_id::text,'typeId',prior.target_type::text,'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',endpoint.document_id,'moduleId',endpoint.module));
  source_identity:=truss.runtime_edge_endpoint(jsonb_build_object('state','stored','identity',old_source),attempt_id,operation_index);
  target_identity:=truss.runtime_edge_endpoint(jsonb_build_object('state','stored','identity',old_target),attempt_id,operation_index);
  IF prior.props<>'{}'::jsonb THEN RAISE EXCEPTION 'untyped retained edge values required' USING ERRCODE='0A000';END IF;
  retained:=coalesce(prior.retained,'{}');order_key:=CASE WHEN prior.order_key IS NULL THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',prior.order_key) END;
  IF operation->>'operation'='delete_edge' THEN
   IF operation-ARRAY['operation','target','expectedVersion']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge delete required' USING ERRCODE='22023';END IF;
   values:='[]';
  ELSE
   IF operation-ARRAY['operation','target','set','unset','expectedVersion','endpointChange','orderKeyChange']<>'{}'::jsonb
    OR jsonb_typeof(operation->'unset') IS DISTINCT FROM 'array' OR jsonb_array_length(operation->'unset')>1024
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'unset') u WHERE jsonb_typeof(value) IS DISTINCT FROM 'string' OR octet_length(value#>>'{}') NOT BETWEEN 1 AND 4096)
    OR jsonb_array_length(operation->'unset')<>(SELECT count(DISTINCT value) FROM jsonb_array_elements(operation->'unset')) THEN
    RAISE EXCEPTION 'closed bounded edge update required' USING ERRCODE='22023';END IF;
   values:=operation->'set';
   FOR name IN SELECT value#>>'{}' FROM jsonb_array_elements(operation->'unset') LOOP retained:=retained-name;END LOOP;
   IF operation ? 'endpointChange' THEN
    IF (operation->'endpointChange')-ARRAY['source','target']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed endpoint change required' USING ERRCODE='22023';END IF;
    source_identity:=truss.runtime_edge_endpoint(operation->'endpointChange'->'source',attempt_id,operation_index);
    target_identity:=truss.runtime_edge_endpoint(operation->'endpointChange'->'target',attempt_id,operation_index);
   END IF;
   IF operation ? 'orderKeyChange' THEN order_key:=operation->'orderKeyChange';END IF;
  END IF;
 END IF;
 IF jsonb_typeof(values) IS DISTINCT FROM 'array' OR jsonb_array_length(values)>1024
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(values) v WHERE value-ARRAY['name','value']<>'{}'::jsonb
   OR jsonb_typeof(value->'name') IS DISTINCT FROM 'string' OR octet_length(value->>'name') NOT BETWEEN 1 AND 4096 OR truss.valid_scalar_cell(value->'value') IS NOT TRUE)
  OR jsonb_array_length(values)<>(SELECT count(DISTINCT value->>'name') FROM jsonb_array_elements(values))
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(values) v JOIN jsonb_array_elements(coalesce(operation->'unset','[]')) u ON v.value->>'name'=u.value#>>'{}') THEN
  RAISE EXCEPTION 'unique disjoint exact edge values required' USING ERRCODE='22023';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(values) LOOP retained:=retained||jsonb_build_object(entry->>'name',truss.canonical_flat_cell(entry->'value'));END LOOP;
 IF (order_key='{"state":"null"}'::jsonb OR order_key->>'state'='text' AND jsonb_typeof(order_key->'text')='string'
  AND order_key-ARRAY['state','text']='{}'::jsonb AND octet_length(order_key->>'text')<=4096) IS NOT TRUE THEN
  RAISE EXCEPTION 'exact bounded order key required' USING ERRCODE='22023';END IF;
 PERFORM truss.runtime_lock_edge_business_key(truss.runtime_edge_business_key(relation.rel_type_id,source_identity,target_identity));
 IF old_source IS NOT NULL THEN PERFORM truss.runtime_lock_edge_business_key(truss.runtime_edge_business_key(relation.rel_type_id,old_source,old_target));END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=(source_identity->>'typeId')::int AND target_type=(target_identity->>'typeId')::int) THEN
  RAISE EXCEPTION 'admitted endpoint pair required' USING ERRCODE='22023';END IF;
 IF octet_length(convert_to(retained::text,'UTF8'))>1048576 THEN RAISE EXCEPTION 'bounded edge values required' USING ERRCODE='54000';END IF;
 RETURN jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module,'typeId',relation.rel_type_id::text,
  'identity',identity,'prior',CASE WHEN prior.id IS NULL THEN NULL ELSE to_jsonb(prior) END,
  'source',source_identity,'target',target_identity,'oldSource',old_source,'oldTarget',old_target,
  'retained',retained,'orderKey',order_key,'keys','[]'::jsonb,'values','[]'::jsonb);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_metadata(uuid,int) FROM PUBLIC;

CREATE SEQUENCE truss.runtime_edge_transition_seq;
CREATE TABLE truss.runtime_edge_transition (transition_id bigint PRIMARY KEY DEFAULT nextval('truss.runtime_edge_transition_seq'), attempt_id uuid NOT NULL REFERENCES truss.runtime_object_attempt (id), operation_index int NOT NULL, writer_xid xid8 NOT NULL, edge_id bigint NOT NULL, rel_type_id int NOT NULL, before_edge jsonb, after_edge jsonb, journal jsonb NOT NULL, old_source jsonb, old_target jsonb, source_identity jsonb NOT NULL, target_identity jsonb NOT NULL, UNIQUE (attempt_id, operation_index, edge_id, rel_type_id), endpoint_ownership jsonb);
CREATE INDEX runtime_edge_transition_owner ON truss.runtime_edge_transition(edge_id,rel_type_id,transition_id DESC);
CREATE INDEX runtime_edge_transition_writer ON truss.runtime_edge_transition(writer_xid);
CREATE TRIGGER runtime_edge_transition_immutable BEFORE UPDATE OR DELETE ON truss.runtime_edge_transition
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();

-- Stored history defaults to its last-written catalog; direct reads pass their current read catalog.
CREATE FUNCTION truss.runtime_edge_history(image jsonb,identity jsonb,source_identity jsonb,target_identity jsonb,interpretation_revision int DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected_revision int:=coalesce(interpretation_revision,(image->>'rev')::int);pin record;
BEGIN
 identity:=jsonb_set(identity,'{definitionPin}',to_jsonb(truss.runtime_relationship_pin((image->>'rel_type_id')::int,selected_revision)));
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(source_identity->>'typeId')::int,NULL,selected_revision);
 source_identity:=jsonb_set(source_identity,'{definitionPin}',to_jsonb(pin.definition_pin));
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',(target_identity->>'typeId')::int,NULL,selected_revision);
 target_identity:=jsonb_set(target_identity,'{definitionPin}',to_jsonb(pin.definition_pin));
 RETURN jsonb_build_object('interfaceVersion','truss-history-record/0.1.0','kind','edge','identity',identity,
  'recordVersion',image->>'ver','catalogRevision',image->>'rev',
  'createdAt',to_char((image->>'created_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'updatedAt',to_char((image->>'updated_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'properties','[]'::jsonb,'retained',(SELECT coalesce(jsonb_agg(jsonb_build_object('name',key,'value',value) ORDER BY key COLLATE "C"),'[]'::jsonb)
    FROM jsonb_each(coalesce(nullif(image->'retained','null'::jsonb),'{}'))),
  'source',source_identity,'target',target_identity,'orderKey',CASE WHEN image->>'order_key' IS NULL THEN '{"state":"null"}'::jsonb ELSE jsonb_build_object('state','text','text',image->>'order_key') END);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_history(jsonb,jsonb,jsonb,jsonb,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_edge_effect(attempt_id uuid,operation_index int,metadata jsonb,effect_operation text,advance boolean,qualified_actor oid DEFAULT NULL,prepared_input jsonb DEFAULT NULL,source_bytes bytea DEFAULT NULL) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;operation jsonb;input jsonb;row_image truss.edge%ROWTYPE;
 identity jsonb;before_image jsonb;after_image jsonb;before_record jsonb;after_record jsonb;result jsonb;event jsonb;
 installation truss.catalog_runtime_installation%ROWTYPE;journal truss.journal%ROWTYPE;event_refs jsonb;revision int;version bigint;entry jsonb;ownership_context jsonb;selected_history text;current_actor oid;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id;
 current_actor:=coalesce(qualified_actor,truss.runtime_person(false));
 IF attempt.writer_xid IS DISTINCT FROM pg_current_xact_id() OR attempt.actor_oid IS DISTINCT FROM current_actor
  OR attempt.complete OR attempt.next_index IS DISTINCT FROM operation_index THEN
  RAISE EXCEPTION 'current original edge effect progress required' USING ERRCODE='55000';END IF;
 IF prepared_input IS NOT NULL AND (source_bytes IS NULL OR source_bytes IS DISTINCT FROM attempt.input_bytes) THEN
  RAISE EXCEPTION 'original checked edge input required' USING ERRCODE='55000';END IF;
 input:=coalesce(prepared_input,convert_from(attempt.input_bytes,'UTF8')::jsonb);operation:=input->'operations'->operation_index;
 IF effect_operation IS NULL OR effect_operation NOT IN ('create_edge','update_edge','delete_edge') OR advance IS NULL THEN
  RAISE EXCEPTION 'explicit native edge effect required' USING ERRCODE='55000';END IF;
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  IF advance THEN RAISE EXCEPTION 'owned parent alone advances original progress' USING ERRCODE='55000';END IF;
  PERFORM truss.runtime_owned_edge_effect_selection(attempt_id,operation_index,metadata,effect_operation,current_actor);
 ELSE
  IF NOT advance OR effect_operation IS DISTINCT FROM operation->>'operation' OR metadata ? 'ownedReference' THEN
   RAISE EXCEPTION 'original independent edge operation required' USING ERRCODE='55000';END IF;
 END IF;
 selected_history:=CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN 'truss-native-owned-edge-mutation/0.1' ELSE 'truss-native-edge-mutation/0.1' END;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 before_image:=nullif(metadata->'prior','null'::jsonb);identity:=metadata->'identity';
 ownership_context:=jsonb_build_object('profile','truss-edge-endpoint-ownership/0.1','captureCatalogRevision',revision::text,
  'before',CASE WHEN before_image IS NULL THEN NULL ELSE jsonb_build_object('source',truss.runtime_endpoint_ownership(metadata->'oldSource',revision),'target',truss.runtime_endpoint_ownership(metadata->'oldTarget',revision)) END,
  'after',NULL);
 IF effect_operation='create_edge' THEN
  row_image.id:=nextval('truss.id_seq');row_image.rel_type_id:=(metadata->>'typeId')::int;row_image.props:='{}';
  row_image.ver:=1;row_image.created_at:=clock_timestamp();
  identity:=jsonb_build_object('id',row_image.id::text,'typeId',row_image.rel_type_id::text,'definitionPin',operation->>'relationshipDefinitionPin',
   'owner',jsonb_build_object('documentId',metadata->>'documentId','moduleId',metadata->>'moduleId'));
 ELSE row_image:=jsonb_populate_record(NULL::truss.edge,before_image);END IF;
 IF effect_operation='update_edge' AND row_image.source_id::text=metadata->'source'->>'id'
  AND row_image.source_type::text=metadata->'source'->>'typeId' AND row_image.target_id::text=metadata->'target'->>'id'
  AND row_image.target_type::text=metadata->'target'->>'typeId' AND coalesce(row_image.retained,'{}')=metadata->'retained'
  AND row_image.order_key IS NOT DISTINCT FROM metadata->'orderKey'->>'text' THEN
  result:=jsonb_build_object('outcome','unchanged','operation','update_edge','identity',identity,'version',row_image.ver::text,'events','[]'::jsonb);
  ownership_context:=jsonb_set(ownership_context,'{after}',CASE WHEN effect_operation='delete_edge' THEN 'null'::jsonb ELSE jsonb_build_object('source',truss.runtime_endpoint_ownership(metadata->'source',revision),'target',truss.runtime_endpoint_ownership(metadata->'target',revision)) END);
  INSERT INTO truss.runtime_edge_transition(attempt_id,operation_index,writer_xid,edge_id,rel_type_id,before_edge,after_edge,journal,old_source,old_target,source_identity,target_identity,endpoint_ownership)
   VALUES(attempt_id,operation_index,attempt.writer_xid,row_image.id,row_image.rel_type_id,before_image,before_image,'[]'::jsonb,metadata->'oldSource',metadata->'oldTarget',metadata->'source',metadata->'target',ownership_context);
 ELSE
  IF before_image IS NOT NULL THEN
   IF row_image.ver=9223372036854775807 THEN RAISE EXCEPTION 'edge version exhausted' USING ERRCODE='54000';END IF;
   before_record:=truss.runtime_edge_history(before_image,identity,metadata->'oldSource',metadata->'oldTarget');row_image.ver:=row_image.ver+1;
  END IF;
  version:=row_image.ver;row_image.rev:=revision;row_image.updated_at:=clock_timestamp();
  IF before_image IS NOT NULL AND (effect_operation='delete_edge' OR metadata->'source' IS DISTINCT FROM metadata->'oldSource' OR metadata->'target' IS DISTINCT FROM metadata->'oldTarget') THEN
   INSERT INTO truss.key_tombstone(entity_kind,type_id,key_num,k,entity_id,ver) VALUES('e',row_image.rel_type_id,0,truss.runtime_edge_business_key(row_image.rel_type_id,metadata->'oldSource',metadata->'oldTarget'),row_image.id,version) ON CONFLICT DO NOTHING;
  END IF;
  row_image.source_id:=(metadata->'source'->>'id')::bigint;row_image.source_type:=(metadata->'source'->>'typeId')::int;
  row_image.target_id:=(metadata->'target'->>'id')::bigint;row_image.target_type:=(metadata->'target'->>'typeId')::int;
  row_image.retained:=nullif(metadata->'retained','{}'::jsonb);row_image.order_key:=metadata->'orderKey'->>'text';
  IF effect_operation='delete_edge' THEN
   DELETE FROM truss.edge WHERE id=row_image.id;
   event:=jsonb_build_object('operation','delete','before',before_record);
  ELSE
   after_image:=to_jsonb(row_image);after_record:=truss.runtime_edge_history(after_image,identity,metadata->'source',metadata->'target');
   IF before_image IS NULL THEN
    INSERT INTO truss.edge SELECT (row_image).*;
    event:=jsonb_build_object('operation','create','after',after_record);
   ELSE
    UPDATE truss.edge SET source_id=row_image.source_id,source_type=row_image.source_type,target_id=row_image.target_id,target_type=row_image.target_type,
     retained=row_image.retained,order_key=row_image.order_key,rev=row_image.rev,ver=row_image.ver,updated_at=row_image.updated_at WHERE id=row_image.id;
    event:=jsonb_build_object('operation','metadata','before',before_record,'after',after_record);
   END IF;
  END IF;
  event:=event||jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile',selected_history,'xid',attempt.writer_xid::text,'seq',nextval('truss.journal_seq')::text,
   'identity',identity,'eventVersion',version::text,'eventCatalogRevision',revision::text,
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text));
  event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount','1',
   'orderedEventDigest',encode(sha256(convert_to(jsonb_build_array(event)::text,'UTF8')),'hex')));
  journal.seq:=(event->>'seq')::bigint;journal.at:=clock_timestamp();journal.xid:=attempt.writer_xid;journal.entity_kind:='e';journal.entity_id:=row_image.id;
  journal.entity_type:=row_image.rel_type_id;journal.ver:=version;journal.op:=event->>'operation';journal.prop_id:=NULL;journal.old_value:=NULL;
  journal.new_value:=truss.runtime_exact_wrapper('event',convert_to(event::text,'UTF8'));journal.rev:=revision;
  journal.origin:=truss.runtime_exact_wrapper('origin',convert_to((event->'origin')::text,'UTF8'));
  INSERT INTO truss.journal SELECT (journal).*;
  ownership_context:=jsonb_set(ownership_context,'{after}',CASE WHEN effect_operation='delete_edge' THEN 'null'::jsonb ELSE jsonb_build_object('source',truss.runtime_endpoint_ownership(metadata->'source',revision),'target',truss.runtime_endpoint_ownership(metadata->'target',revision)) END);
  INSERT INTO truss.runtime_edge_transition(attempt_id,operation_index,writer_xid,edge_id,rel_type_id,before_edge,after_edge,journal,old_source,old_target,source_identity,target_identity,endpoint_ownership)
   VALUES(attempt_id,operation_index,attempt.writer_xid,row_image.id,row_image.rel_type_id,before_image,after_image,jsonb_build_array(to_jsonb(journal)),
    metadata->'oldSource',metadata->'oldTarget',metadata->'source',metadata->'target',ownership_context);
  event_refs:=jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile',selected_history,'xid',attempt.writer_xid::text,'seq',journal.seq::text));
  IF effect_operation='create_edge' THEN result:=jsonb_build_object('outcome','created','operation','create_edge','identity',identity,'version',version::text,'events',event_refs);
   IF operation ? 'alias' THEN result:=result||jsonb_build_object('alias',operation->>'alias');END IF;
  ELSIF effect_operation='update_edge' THEN result:=jsonb_build_object('outcome','changed','operation','update_edge','identity',identity,'version',version::text,'events',event_refs);
  ELSE result:=jsonb_build_object('outcome','deleted','operation','delete_edge','identity',identity,'deletionVersion',version::text,
   'deleted',jsonb_build_array(jsonb_build_object('identity',identity,'deletionVersion',version::text)),'events',event_refs);END IF;
 END IF;
 -- Requalify after all trigger-capable edge/journal/transition writes.
 current_actor:=truss.runtime_person(false);
 PERFORM truss.runtime_module_writer_qualified(metadata->>'documentId',metadata->>'moduleId',current_actor);
 FOR entry IN SELECT value FROM jsonb_array_elements(jsonb_build_array(metadata->'oldSource',metadata->'oldTarget',metadata->'source',metadata->'target')) WHERE value<>'null'::jsonb LOOP
  IF NOT truss.runtime_can_read_qualified(entry->'owner'->>'documentId',entry->'owner'->>'moduleId',current_actor) THEN RAISE EXCEPTION 'endpoint reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF advance THEN
 UPDATE truss.runtime_object_attempt SET next_index=next_index+1,results=results||jsonb_build_array(result),
  aliases=aliases||CASE WHEN effect_operation='create_edge' AND operation ? 'alias' THEN jsonb_build_array(jsonb_build_object('alias',operation->>'alias','identity',identity)) ELSE '[]'::jsonb END WHERE id=attempt_id;
 END IF;
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_effect(uuid,int,jsonb,text,boolean,oid,jsonb,bytea) FROM PUBLIC;

-- Historical three-argument edge path retains its original one-step progress.
CREATE FUNCTION truss.runtime_edge_step(attempt_id uuid,operation_index int,metadata jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE operation text;
BEGIN
 SELECT convert_from(input_bytes,'UTF8')::jsonb->'operations'->operation_index->>'operation'
  INTO STRICT operation FROM truss.runtime_object_attempt WHERE id=attempt_id;
 RETURN truss.runtime_edge_effect(attempt_id,operation_index,metadata,operation,true);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_step(uuid,int,jsonb) FROM PUBLIC;


CREATE FUNCTION truss.runtime_owned_edge_validate_in_input_qualified(selected_id bigint,selected_type int,prepared_input jsonb,source_bytes bytea,prepared_attempt truss.runtime_object_attempt,qualified_actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE latest truss.runtime_edge_transition%ROWTYPE;actual jsonb;entry jsonb;selected_transition bigint;transition_attempt_id uuid;current_actor oid;owner record;
BEGIN
 SELECT * INTO latest FROM truss.runtime_edge_transition WHERE edge_id=selected_id AND rel_type_id=selected_type AND writer_xid=pg_current_xact_id() ORDER BY transition_id DESC LIMIT 1;
 IF NOT FOUND THEN RAISE EXCEPTION 'registered current edge mutation required' USING ERRCODE='55000';END IF;
 current_actor:=qualified_actor;
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_object_attempt WHERE id=latest.attempt_id AND writer_xid=latest.writer_xid AND actor_oid=current_actor) THEN
  RAISE EXCEPTION 'registered current edge mutation required' USING ERRCODE='55000';END IF;
 -- Row/transition events remain queued after an early attempt-constraint flush.
 SELECT document_id,module INTO STRICT owner FROM truss.rel_def WHERE rel_type_id=selected_type;
 PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,current_actor);
 FOR selected_transition,transition_attempt_id IN SELECT t.transition_id,t.attempt_id FROM truss.runtime_edge_transition t JOIN truss.runtime_object_attempt a ON a.id=t.attempt_id
  WHERE t.edge_id=selected_id AND t.rel_type_id=selected_type AND t.writer_xid=pg_current_xact_id()
   AND a.context->'mutationProfile'=truss.runtime_owned_profile() LOOP
  -- The sole non-NULL caller is object_group_finish, after its complete
  -- runtime_edge_authorize pass following marker refresh. That pass already
  -- reconstructed every current-attempt transition, including ordinal bounds.
  -- This loop has no writes. Keep current module and physical checks here;
  -- standalone calls and other attempts still reconstruct their transitions.
  -- Mandatory owned-group finish and commit reconstruction remain independent.
  IF prepared_attempt.id IS NULL OR transition_attempt_id IS DISTINCT FROM prepared_attempt.id THEN
   PERFORM truss.runtime_owned_edge_transition_validate(selected_transition,false,current_actor);
  END IF;
 END LOOP;
 SELECT to_jsonb(e) INTO actual FROM truss.edge e WHERE id=selected_id AND rel_type_id=selected_type;
 IF actual IS DISTINCT FROM latest.after_edge THEN RAISE EXCEPTION 'exact final edge required' USING ERRCODE='55000';END IF;
 FOR entry IN SELECT j.value FROM truss.runtime_edge_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j WHERE t.edge_id=selected_id AND t.rel_type_id=selected_type AND t.writer_xid=pg_current_xact_id() LOOP
  SELECT to_jsonb(j) INTO actual FROM truss.journal j WHERE j.at=(entry->>'at')::timestamptz AND j.seq=(entry->>'seq')::bigint;
  IF actual IS DISTINCT FROM entry THEN RAISE EXCEPTION 'exact edge journal required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_validate_in_input_qualified(bigint,int,jsonb,bytea,truss.runtime_object_attempt,oid) FROM PUBLIC;

-- Standalone and deferred settlement always issue a fresh native actor.
CREATE FUNCTION truss.runtime_owned_edge_validate_in_input(selected_id bigint,selected_type int,prepared_input jsonb,source_bytes bytea,prepared_attempt truss.runtime_object_attempt) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.runtime_owned_edge_validate_in_input_qualified(selected_id,selected_type,prepared_input,source_bytes,prepared_attempt,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_edge_validate_in_input(bigint,int,jsonb,bytea,truss.runtime_object_attempt) FROM PUBLIC;

CREATE FUNCTION truss.runtime_edge_validate(selected_id bigint,selected_type int) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.runtime_owned_edge_validate_in_input(selected_id,selected_type,NULL,NULL,NULL);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_validate(bigint,int) FROM PUBLIC;

-- Reuse plans for repeated private point lookups; function-local settings
-- restore the caller policy on return, including exceptional return.
CREATE FUNCTION truss.runtime_graph_validate_object_qualified(selected_id bigint,selected_type int,refresh_markers boolean,qualified_actor oid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET plan_cache_mode='force_generic_plan' AS $$
DECLARE phase int;relation truss.rel_def%ROWTYPE;owner record;outgoing bigint;incoming bigint;expected jsonb;actual jsonb;
BEGIN
  PERFORM 1 FROM truss.object WHERE id=selected_id AND type_id=selected_type FOR UPDATE NOWAIT;
  IF NOT FOUND THEN RETURN;END IF;
  FOR phase IN 1..2 LOOP
   FOR owner IN
    SELECT DISTINCT document_id,module_id FROM (
     SELECT r.document_id,r.module AS module_id FROM truss.rel_def r WHERE r.retired_rev IS NULL
      AND EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=r.rel_type_id AND (e.source_type=selected_type OR e.target_type=selected_type))
     UNION ALL
     SELECT t.document_id,t.module FROM truss.rel_def r JOIN truss.rel_endpoint e ON e.rel_type_id=r.rel_type_id
      JOIN truss.type_def t ON t.type_id IN(e.source_type,e.target_type) WHERE r.retired_rev IS NULL
      AND EXISTS(SELECT 1 FROM truss.rel_endpoint selected WHERE selected.rel_type_id=r.rel_type_id AND (selected.source_type=selected_type OR selected.target_type=selected_type))
    ) dependencies
   LOOP
    IF NOT truss.runtime_can_read_qualified(owner.document_id,owner.module_id,qualified_actor) THEN RAISE EXCEPTION 'complete relationship and endpoint count reader required' USING ERRCODE='42501';END IF;
   END LOOP;
   IF phase=1 THEN
  FOR relation IN SELECT r.* FROM truss.rel_def r WHERE r.retired_rev IS NULL
   AND EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=r.rel_type_id AND (e.source_type=selected_type OR e.target_type=selected_type)) ORDER BY rel_type_id LOOP
   outgoing:=NULL;incoming:=NULL;
   IF EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND source_type=selected_type) THEN
    SELECT count(*) INTO outgoing FROM truss.edge WHERE rel_type_id=relation.rel_type_id AND source_id=selected_id AND source_type=selected_type;
    IF outgoing<relation.target_min OR relation.target_max IS NOT NULL AND outgoing>relation.target_max THEN RAISE EXCEPTION 'outgoing multiplicity failed' USING ERRCODE='P1005';END IF;
   END IF;
   IF EXISTS(SELECT 1 FROM truss.rel_endpoint WHERE rel_type_id=relation.rel_type_id AND target_type=selected_type) THEN
    SELECT count(*) INTO incoming FROM truss.edge WHERE rel_type_id=relation.rel_type_id AND target_id=selected_id AND target_type=selected_type;
    IF incoming<relation.source_min OR relation.source_max IS NOT NULL AND incoming>relation.source_max THEN RAISE EXCEPTION 'incoming multiplicity failed' USING ERRCODE='P1005';END IF;
   END IF;
   SELECT coalesce(jsonb_agg(v ORDER BY v->>'side'),'[]'::jsonb) INTO expected FROM (
    SELECT jsonb_build_object('rel_type_id',relation.rel_type_id,'side','s','endpoint_id',selected_id,'edge_id',id) v FROM truss.edge
     WHERE relation.target_max=1 AND rel_type_id=relation.rel_type_id AND source_id=selected_id AND source_type=selected_type
    UNION ALL SELECT jsonb_build_object('rel_type_id',relation.rel_type_id,'side','t','endpoint_id',selected_id,'edge_id',id) FROM truss.edge
     WHERE relation.source_max=1 AND rel_type_id=relation.rel_type_id AND target_id=selected_id AND target_type=selected_type) markers;
   IF refresh_markers THEN
    DELETE FROM truss.edge_limit WHERE rel_type_id=relation.rel_type_id AND endpoint_id=selected_id;
    INSERT INTO truss.edge_limit SELECT (jsonb_populate_record(NULL::truss.edge_limit,value)).* FROM jsonb_array_elements(expected);
   END IF;
   SELECT coalesce(jsonb_agg(to_jsonb(m) ORDER BY m.side),'[]'::jsonb) INTO actual FROM truss.edge_limit m WHERE m.rel_type_id=relation.rel_type_id AND m.endpoint_id=selected_id;
   IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'exact final multiplicity markers required' USING ERRCODE='55000';END IF;
  END LOOP;
   END IF;
  END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_graph_validate_object_qualified(bigint,int,boolean,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_graph_validate_object(selected_id bigint,selected_type int,refresh_markers boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 PERFORM truss.runtime_graph_validate_object_qualified(selected_id,selected_type,refresh_markers,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_graph_validate_object(bigint,int,boolean) FROM PUBLIC;

CREATE FUNCTION truss.runtime_graph_validate(refresh_markers boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE affected record;current_actor oid;
BEGIN
 current_actor:=truss.runtime_person(false);
 FOR affected IN
  SELECT DISTINCT object_id,type_id FROM (
   SELECT m.object_id,m.type_id FROM truss.runtime_create_member m JOIN truss.runtime_create_group g USING(group_id) WHERE g.writer_xid=pg_current_xact_id()
   UNION ALL SELECT object_id,type_id FROM truss.runtime_object_transition WHERE writer_xid=pg_current_xact_id()
   UNION ALL SELECT object_id,type_id FROM truss.runtime_catalog_rebind_transition WHERE writer_xid=pg_current_xact_id()
   UNION ALL SELECT object_id,type_id FROM truss.runtime_catalog_key_backfill WHERE writer_xid=pg_current_xact_id()
   UNION ALL SELECT o.id,o.type_id FROM truss.object o
    JOIN truss.rel_endpoint e ON o.type_id IN(e.source_type,e.target_type)
    JOIN (SELECT rel_type_id,since_rev rev FROM truss.rel_def
     UNION SELECT def_id,rev FROM truss.schema_change WHERE kind='rel') c ON c.rel_type_id=e.rel_type_id
    JOIN truss.catalog_registration_request r ON r.revision=c.rev
    WHERE r.writer_xid=pg_current_xact_id()
   UNION ALL SELECT (i.value->>'id')::bigint,(i.value->>'typeId')::int FROM truss.runtime_edge_transition t
    CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(t.old_source,t.old_target,t.source_identity,t.target_identity)) i
    WHERE t.writer_xid=pg_current_xact_id() AND i.value<>'null'::jsonb) o ORDER BY object_id,type_id LOOP
  PERFORM truss.runtime_graph_validate_object_qualified(affected.object_id,affected.type_id,refresh_markers,current_actor);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_graph_validate(boolean) FROM PUBLIC;

-- Group and deferred settlement recheck actual current state for this attempt,
-- including every old/new edge endpoint. Catalog-wide evolution remains global.
CREATE FUNCTION truss.runtime_owned_graph_validate_attempt(selected_attempt uuid,refresh_markers boolean) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE affected record;current_actor oid;
BEGIN
 current_actor:=truss.runtime_person(false);
 IF refresh_markers IS NULL OR NOT EXISTS(SELECT 1 FROM truss.runtime_object_attempt a
  WHERE a.id=selected_attempt AND a.writer_xid=pg_current_xact_id() AND a.actor_oid=current_actor) THEN
  RAISE EXCEPTION 'current original graph attempt required' USING ERRCODE='55000';END IF;
 FOR affected IN
  SELECT DISTINCT object_id,type_id FROM (
   SELECT object_id,type_id FROM truss.runtime_object_transition WHERE attempt_id=selected_attempt
    AND (before_object-ARRAY['props','retained','ver','created_at','updated_at'])
      IS DISTINCT FROM (after_object-ARRAY['props','retained','ver','created_at','updated_at'])
   UNION ALL SELECT (i.value->>'id')::bigint,(i.value->>'typeId')::int
    FROM truss.runtime_edge_transition t CROSS JOIN LATERAL
     jsonb_array_elements(jsonb_build_array(t.old_source,t.old_target,t.source_identity,t.target_identity)) i
    WHERE t.attempt_id=selected_attempt AND i.value<>'null'::jsonb) members
  ORDER BY object_id,type_id LOOP
  PERFORM truss.runtime_graph_validate_object_qualified(affected.object_id,affected.type_id,refresh_markers,current_actor);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_graph_validate_attempt(uuid,boolean) FROM PUBLIC;

CREATE CONSTRAINT TRIGGER runtime_edge_commit AFTER INSERT OR UPDATE OR DELETE ON truss.edge DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check();
CREATE CONSTRAINT TRIGGER runtime_edge_transition_commit AFTER INSERT ON truss.runtime_edge_transition DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check();
ALTER TABLE truss.edge ENABLE ALWAYS TRIGGER runtime_edge_commit;
ALTER TABLE truss.runtime_edge_transition ENABLE ALWAYS TRIGGER runtime_edge_transition_commit;

CREATE FUNCTION truss.runtime_edge_authorize(selected_attempt uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE entry jsonb;selected_transition bigint;completed boolean;context jsonb;revision text;current_actor oid;
BEGIN
 SELECT complete INTO STRICT completed FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 current_actor:=truss.runtime_person(false);
 FOR selected_transition IN SELECT t.transition_id FROM truss.runtime_edge_transition t JOIN truss.runtime_object_attempt a ON a.id=t.attempt_id
  WHERE a.id=selected_attempt AND a.context->'mutationProfile'=truss.runtime_owned_profile() LOOP
  PERFORM truss.runtime_owned_edge_transition_validate(selected_transition,completed,current_actor);
 END LOOP;
 FOR context,revision IN SELECT i.value,t.endpoint_ownership->>'captureCatalogRevision' FROM truss.runtime_edge_transition t
  CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(t.endpoint_ownership->'before'->'source',t.endpoint_ownership->'before'->'target',
   t.endpoint_ownership->'after'->'source',t.endpoint_ownership->'after'->'target')) i
  WHERE t.attempt_id=selected_attempt AND i.value<>'null'::jsonb LOOP
  IF NOT truss.runtime_can_read_qualified(context->'identity'->'owner'->>'documentId',context->'identity'->'owner'->>'moduleId',current_actor) THEN
   RAISE EXCEPTION 'original endpoint context reader required' USING ERRCODE='42501';END IF;
  PERFORM truss.runtime_history_ownership_qualified(jsonb_build_object('identity',context->'identity','catalogRevision',revision,'ownership',context->'ownership'),current_actor);
 END LOOP;
 FOR entry IN SELECT DISTINCT i.value FROM truss.runtime_edge_transition t
  CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(t.old_source,t.old_target,t.source_identity,t.target_identity)) i
  WHERE t.attempt_id=selected_attempt AND i.value<>'null'::jsonb LOOP
  IF NOT truss.runtime_can_read_qualified(entry->'owner'->>'documentId',entry->'owner'->>'moduleId',current_actor) THEN RAISE EXCEPTION 'original endpoint reader required' USING ERRCODE='42501';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_authorize(uuid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_edge_read(selected_document text,selected_module text,selected_relationship text,selected_id bigint,maximum_bytes int,expected_release text,expected_digest text) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE relation truss.rel_def%ROWTYPE;edge_row truss.edge%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 source_identity jsonb;target_identity jsonb;endpoint truss.type_def%ROWTYPE;frozen record;entry jsonb;obj jsonb;root_row jsonb;root_def jsonb;root_owners jsonb:='[]';pin record;identity jsonb;result bytea;captured_revision int;
BEGIN
 PERFORM truss.runtime_person(false);
 IF selected_id IS NULL OR selected_id<1 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 THEN RAISE EXCEPTION 'bounded edge selection required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN RAISE EXCEPTION 'selected edge runtime required' USING ERRCODE='0A000';END IF;
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 SELECT * INTO relation FROM truss.rel_def WHERE document_id=selected_document AND module=selected_module AND rel_id=selected_relationship AND retired_rev IS NULL;
 IF NOT FOUND THEN RETURN NULL;END IF;
 -- Freeze the edge, endpoint rows and their aggregate roots in one statement snapshot.
 SELECT e AS edge,s AS source,t AS target,st AS source_definition,tt AS target_definition,
  sr AS source_root,tr AS target_root,srt AS source_root_definition,trt AS target_root_definition
 INTO frozen FROM truss.edge e
 JOIN truss.object s ON s.id=e.source_id AND s.type_id=e.source_type
 JOIN truss.object t ON t.id=e.target_id AND t.type_id=e.target_type
 JOIN truss.type_def st ON st.type_id=s.type_id AND st.retired_rev IS NULL
 JOIN truss.type_def tt ON tt.type_id=t.type_id AND tt.retired_rev IS NULL
 LEFT JOIN truss.object sr ON sr.id=s.root_id AND sr.type_id=s.root_type
 LEFT JOIN truss.object tr ON tr.id=t.root_id AND tr.type_id=t.root_type
 LEFT JOIN truss.type_def srt ON srt.type_id=sr.type_id AND srt.retired_rev IS NULL
 LEFT JOIN truss.type_def trt ON trt.type_id=tr.type_id AND trt.retired_rev IS NULL
 WHERE e.id=selected_id AND e.rel_type_id=relation.rel_type_id;
 IF NOT FOUND THEN RETURN NULL;END IF;
 edge_row:=frozen.edge;
 IF relation.lifecycle NOT IN ('independent','owned') OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL OR edge_row.props<>'{}'::jsonb THEN RAISE EXCEPTION 'selected directed scalar edge required' USING ERRCODE='0A000';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(jsonb_build_array(
  jsonb_build_object('object',to_jsonb(frozen.source),'definition',to_jsonb(frozen.source_definition),'root',to_jsonb(frozen.source_root),'rootDefinition',to_jsonb(frozen.source_root_definition)),
  jsonb_build_object('object',to_jsonb(frozen.target),'definition',to_jsonb(frozen.target_definition),'root',to_jsonb(frozen.target_root),'rootDefinition',to_jsonb(frozen.target_root_definition)))) LOOP
  obj:=entry->'object';endpoint:=jsonb_populate_record(NULL::truss.type_def,entry->'definition');
  IF endpoint.kind<>'record' OR endpoint.provisional OR (obj->>'rev')::int>captured_revision OR endpoint.since_rev>captured_revision THEN RAISE EXCEPTION 'current endpoint catalog required' USING ERRCODE='55P03';END IF;
  IF NOT truss.runtime_can_read(endpoint.document_id,endpoint.module) THEN RETURN NULL;END IF;
  IF obj->>'root_id' IS NOT NULL OR obj->>'root_type' IS NOT NULL THEN
   root_row:=entry->'root';root_def:=entry->'rootDefinition';
   IF obj->>'root_id' IS NULL OR obj->>'root_type' IS NULL OR root_row->>'id' IS NULL OR root_def->>'type_id' IS NULL
    OR root_row->>'root_id' IS NOT NULL OR root_row->>'root_type' IS NOT NULL
    OR root_row->>'id'=obj->>'id' AND root_row->>'type_id'=obj->>'type_id'
    OR root_def->>'kind'<>'record' OR (root_def->>'provisional')::boolean THEN RAISE EXCEPTION 'current endpoint aggregate root required' USING ERRCODE='55000';END IF;
   IF (root_row->>'rev')::int>captured_revision OR (root_def->>'since_rev')::int>captured_revision THEN RAISE EXCEPTION 'endpoint root catalog changed' USING ERRCODE='55P03';END IF;
   IF NOT truss.runtime_can_read(root_def->>'document_id',root_def->>'module') THEN RETURN NULL;END IF;
   root_owners:=root_owners||jsonb_build_array(jsonb_build_object('documentId',root_def->>'document_id','moduleId',root_def->>'module'));
  END IF;
 END LOOP;
 endpoint:=frozen.source_definition;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',endpoint.type_id);
 source_identity:=jsonb_build_object('id',edge_row.source_id::text,'typeId',endpoint.type_id::text,'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',endpoint.document_id,'moduleId',endpoint.module));
 endpoint:=frozen.target_definition;
 SELECT * INTO STRICT pin FROM truss.runtime_owned_definition_metadata('type',endpoint.type_id);
 target_identity:=jsonb_build_object('id',edge_row.target_id::text,'typeId',endpoint.type_id::text,'definitionPin',pin.definition_pin,'owner',jsonb_build_object('documentId',endpoint.document_id,'moduleId',endpoint.module));
 identity:=jsonb_build_object('id',edge_row.id::text,'typeId',relation.rel_type_id::text,'definitionPin',truss.runtime_relationship_pin(relation.rel_type_id),'owner',jsonb_build_object('documentId',relation.document_id,'moduleId',relation.module));
 result:=convert_to((truss.runtime_edge_history(to_jsonb(edge_row),identity,source_identity,target_identity,captured_revision)||jsonb_build_object('executedCatalogRevision',captured_revision::text))::text,'UTF8');
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'bounded complete edge required' USING ERRCODE='54000';END IF;
 IF NOT truss.runtime_can_read(relation.document_id,relation.module) OR NOT truss.runtime_can_read(source_identity->'owner'->>'documentId',source_identity->'owner'->>'moduleId')
  OR NOT truss.runtime_can_read(target_identity->'owner'->>'documentId',target_identity->'owner'->>'moduleId') THEN RAISE EXCEPTION 'current edge reader required' USING ERRCODE='42501';END IF;
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN RAISE EXCEPTION 'edge catalog changed' USING ERRCODE='55P03';END IF;
 FOR entry IN SELECT value FROM jsonb_array_elements(root_owners) LOOP
  IF NOT truss.runtime_can_read(entry->>'documentId',entry->>'moduleId') THEN RAISE EXCEPTION 'current endpoint root reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 RETURN jsonb_build_object('edge',convert_from(result,'UTF8')::jsonb,'rootOwners',root_owners);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_edge_read(text,text,text,bigint,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.get_edge(selected_document text,selected_module text,selected_relationship text,selected_id bigint,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
 SELECT convert_to((truss.runtime_edge_read(selected_document,selected_module,selected_relationship,selected_id,maximum_bytes,expected_release,expected_digest)->'edge')::text,'UTF8');
$$;
REVOKE ALL ON FUNCTION truss.get_edge(text,text,text,bigint,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.page_edges(selected_document text,selected_module text,selected_relationship text,anchor jsonb,direction text,page_limit int,maximum_bytes int,original_cursor bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE relation truss.rel_def%ROWTYPE;selected truss.type_def%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;
 frozen record;anchor_object truss.object;anchor_root truss.object;anchor_root_definition truss.type_def;root_owners jsonb:='[]';edge_context jsonb;root_owner jsonb;
 context jsonb;continuation jsonb;cursor_value jsonb;candidate record;edge_value jsonb;lookahead jsonb;edges jsonb:='[]';last_key text;last_id bigint;result bytea;revision int;
BEGIN
 PERFORM truss.runtime_person(false);
 IF page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 1000 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 OR direction NOT IN ('outgoing','incoming') OR direction IS NULL THEN RAISE EXCEPTION 'bounded directed page required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN RAISE EXCEPTION 'selected edge page runtime required' USING ERRCODE='0A000';END IF;
 SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 SELECT * INTO relation FROM truss.rel_def WHERE document_id=selected_document AND module=selected_module AND rel_id=selected_relationship AND retired_rev IS NULL;
 IF NOT FOUND THEN RETURN NULL;END IF;
 IF relation.lifecycle NOT IN ('independent','owned') OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL THEN RAISE EXCEPTION 'selected directed scalar relationship required' USING ERRCODE='0A000';END IF;
 selected:=truss.runtime_condition_type(anchor);
 IF NOT truss.runtime_can_read(selected.document_id,selected.module) THEN RETURN NULL;END IF;
 SELECT o AS object,ro AS root,rt AS root_definition INTO frozen FROM truss.object o
 LEFT JOIN truss.object ro ON ro.id=o.root_id AND ro.type_id=o.root_type
 LEFT JOIN truss.type_def rt ON rt.type_id=ro.type_id AND rt.retired_rev IS NULL
 WHERE o.id=(anchor->>'id')::bigint AND o.type_id=selected.type_id;
 IF NOT FOUND THEN RETURN NULL;END IF;
 anchor_object:=frozen.object;anchor_root:=frozen.root;anchor_root_definition:=frozen.root_definition;
 IF anchor_object.rev>revision THEN RAISE EXCEPTION 'anchor catalog changed' USING ERRCODE='55P03';END IF;
 IF anchor_object.root_id IS NOT NULL OR anchor_object.root_type IS NOT NULL THEN
  IF anchor_object.root_id IS NULL OR anchor_object.root_type IS NULL OR anchor_root.id IS NULL OR anchor_root_definition.type_id IS NULL
   OR anchor_root.root_id IS NOT NULL OR anchor_root.root_type IS NOT NULL
   OR anchor_root.id=anchor_object.id AND anchor_root.type_id=anchor_object.type_id
   OR anchor_root_definition.kind<>'record' OR anchor_root_definition.provisional THEN RAISE EXCEPTION 'current anchor aggregate root required' USING ERRCODE='55000';END IF;
  IF anchor_root.rev>revision OR anchor_root_definition.since_rev>revision THEN RAISE EXCEPTION 'anchor root catalog changed' USING ERRCODE='55P03';END IF;
  IF NOT truss.runtime_can_read(anchor_root_definition.document_id,anchor_root_definition.module) THEN RETURN NULL;END IF;
  root_owners:=jsonb_build_array(jsonb_build_object('documentId',anchor_root_definition.document_id,'moduleId',anchor_root_definition.module));
 END IF;
 context:=jsonb_build_object('profile','truss-python-edge-page/0.1','installationId',installation.installation_id::text,'releaseSha256',expected_digest,
  'catalogRevision',revision::text,'relationshipPin',truss.runtime_relationship_pin(relation.rel_type_id),'anchor',anchor,'direction',direction);
 IF original_cursor IS NOT NULL THEN
  IF octet_length(original_cursor) NOT BETWEEN 1 AND 65536 OR (convert_from(original_cursor,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'bounded exact edge cursor required' USING ERRCODE='22023';END IF;
  cursor_value:=convert_from(original_cursor,'UTF8')::jsonb;
  IF cursor_value-ARRAY['afterId','afterKey'] IS DISTINCT FROM context THEN RAISE EXCEPTION 'current edge cursor context required' USING ERRCODE='P1002';END IF;
  IF jsonb_typeof(cursor_value->'afterId') IS DISTINCT FROM 'string' OR cursor_value->>'afterId' !~ '^[1-9][0-9]{0,18}$'
   OR length(cursor_value->>'afterId')=19 AND (cursor_value->>'afterId') COLLATE "C">'9223372036854775807'
   OR jsonb_typeof(cursor_value->'afterKey') NOT IN ('string','null') OR NOT cursor_value ? 'afterKey' THEN RAISE EXCEPTION 'exact paired edge cursor required' USING ERRCODE='22023';END IF;
  last_id:=(cursor_value->>'afterId')::bigint;last_key:=cursor_value->>'afterKey';
 END IF;
 FOR candidate IN SELECT e.id,e.order_key,s.document_id source_document,s.module source_module,t.document_id target_document,t.module target_module FROM truss.edge e JOIN truss.type_def s ON s.type_id=e.source_type JOIN truss.type_def t ON t.type_id=e.target_type
  WHERE e.rel_type_id=relation.rel_type_id AND CASE direction WHEN 'outgoing' THEN e.source_id=(anchor->>'id')::bigint AND e.source_type=selected.type_id ELSE e.target_id=(anchor->>'id')::bigint AND e.target_type=selected.type_id END
   AND truss.runtime_can_read(s.document_id,s.module) AND truss.runtime_can_read(t.document_id,t.module)
   AND (original_cursor IS NULL OR last_key IS NULL AND e.order_key IS NULL AND e.id>last_id
    OR last_key IS NOT NULL AND (e.order_key IS NULL OR e.order_key COLLATE "C">last_key COLLATE "C" OR e.order_key=last_key AND e.id>last_id))
  ORDER BY e.order_key COLLATE "C" NULLS LAST,e.id LIMIT page_limit+1 LOOP
  edge_context:=truss.runtime_edge_read(selected_document,selected_module,selected_relationship,candidate.id,16777216,expected_release,expected_digest);
  edge_value:=edge_context->'edge';
  IF edge_value IS NULL THEN RAISE EXCEPTION 'edge page authority changed' USING ERRCODE='55P03';END IF;
  SELECT coalesce(jsonb_agg(DISTINCT value),'[]'::jsonb) INTO root_owners FROM jsonb_array_elements(root_owners||(edge_context->'rootOwners'));
  IF octet_length(root_owners::text)>16777216 THEN RAISE EXCEPTION 'bounded edge page authority context required' USING ERRCODE='54000';END IF;
  IF edge_value->'identity'->>'id' IS DISTINCT FROM candidate.id::text OR edge_value->'identity'->>'typeId' IS DISTINCT FROM relation.rel_type_id::text
   OR (CASE direction WHEN 'outgoing' THEN edge_value->'source' ELSE edge_value->'target' END) IS DISTINCT FROM anchor
   OR edge_value->'orderKey'->>'text' IS DISTINCT FROM candidate.order_key THEN RAISE EXCEPTION 'edge page selection changed' USING ERRCODE='55P03';END IF;
  IF jsonb_array_length(edges)=page_limit THEN continuation:=context||jsonb_build_object('afterId',last_id::text,'afterKey',last_key);
   lookahead:=jsonb_build_object('sourceDocument',edge_value->'source'->'owner'->>'documentId','sourceModule',edge_value->'source'->'owner'->>'moduleId','targetDocument',edge_value->'target'->'owner'->>'documentId','targetModule',edge_value->'target'->'owner'->>'moduleId');EXIT;END IF;
  edges:=edges||jsonb_build_array(edge_value);last_id:=candidate.id;last_key:=candidate.order_key;
  IF octet_length(edges::text)>maximum_bytes THEN RAISE EXCEPTION 'bounded complete edge page required' USING ERRCODE='54000';END IF;
 END LOOP;
 FOR edge_value IN SELECT value FROM jsonb_array_elements(edges) LOOP
  IF NOT truss.runtime_can_read(edge_value->'source'->'owner'->>'documentId',edge_value->'source'->'owner'->>'moduleId') OR NOT truss.runtime_can_read(edge_value->'target'->'owner'->>'documentId',edge_value->'target'->'owner'->>'moduleId') THEN RAISE EXCEPTION 'current endpoint page reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF lookahead IS NOT NULL AND (NOT truss.runtime_can_read(lookahead->>'sourceDocument',lookahead->>'sourceModule') OR NOT truss.runtime_can_read(lookahead->>'targetDocument',lookahead->>'targetModule')) THEN RAISE EXCEPTION 'lookahead page authority changed' USING ERRCODE='55P03';END IF;
 IF NOT truss.runtime_can_read(selected_document,selected_module) OR NOT truss.runtime_can_read(selected.document_id,selected.module) THEN RAISE EXCEPTION 'current relationship and anchor page reader required' USING ERRCODE='42501';END IF;
 FOR root_owner IN SELECT value FROM jsonb_array_elements(root_owners) LOOP
  IF NOT truss.runtime_can_read(root_owner->>'documentId',root_owner->>'moduleId') THEN RAISE EXCEPTION 'current endpoint page root reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM revision THEN RAISE EXCEPTION 'edge page catalog changed' USING ERRCODE='55P03';END IF;
 result:=convert_to(jsonb_build_object('edges',edges,'catalogRevision',revision,'continuation',continuation)::text,'UTF8');
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'bounded complete edge page required' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.page_edges(text,text,text,jsonb,text,int,int,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_receipt_position(context jsonb,receipt_id bigint,writer xid8) RETURNS bytea
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT convert_to(format('{"interfaceVersion":"truss-receipt-position/0.1.0","positionProfile":{"identity":%s,"version":%s,"sha256":%s},"installationId":%s,"sourceEpoch":%s,"receiptStorageRowId":%s,"writerXid":%s}',
  to_json(context->'positionProfile'->>'identity')::text,to_json(context->'positionProfile'->>'version')::text,to_json(context->'positionProfile'->>'sha256')::text,
  to_json(context->>'installationId')::text,to_json(context->>'sourceEpoch')::text,to_json(receipt_id::text)::text,to_json(writer::text)::text),'UTF8');
$$;
REVOKE ALL ON FUNCTION truss.runtime_receipt_position(jsonb,bigint,xid8) FROM PUBLIC;
CREATE FUNCTION truss.runtime_receipt_token(locator_bytes bytea) RETURNS text
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT rtrim(translate(replace(encode(locator_bytes,'base64'),chr(10),''),'+/','-_'),'=');
$$;
REVOKE ALL ON FUNCTION truss.runtime_receipt_token(bytea) FROM PUBLIC;

CREATE FUNCTION truss.runtime_receipt_can_read(selected_attempt uuid) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE attempt truss.runtime_object_attempt%ROWTYPE;input jsonb;operation jsonb;owner record;entry jsonb;index int:=0;
BEGIN
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=selected_attempt;
 input:=convert_from(attempt.input_bytes,'UTF8')::jsonb;
 FOR operation IN SELECT value FROM jsonb_array_elements(input->'operations') LOOP
  BEGIN
   SELECT * INTO STRICT owner FROM truss.runtime_retained_operation_owner(selected_attempt,index);
  EXCEPTION WHEN insufficient_privilege THEN RETURN false;
  END;
  IF NOT truss.runtime_can_read(owner.document_id,owner.module) THEN RETURN false;END IF;
  index:=index+1;
 END LOOP;
 FOR entry IN SELECT DISTINCT i.value FROM truss.runtime_edge_transition t
  CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(t.old_source,t.old_target,t.source_identity,t.target_identity)) i
  WHERE t.attempt_id=selected_attempt AND i.value<>'null'::jsonb LOOP
  IF NOT truss.runtime_can_read(entry->'owner'->>'documentId',entry->'owner'->>'moduleId') THEN RETURN false;END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_receipt_can_read(uuid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_receipt_refusal(selected_attempt uuid,reason text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF NOT truss.runtime_receipt_can_read(selected_attempt) THEN RETURN convert_to('{"outcome":"unavailable","reason":"observation_integrity"}','UTF8');END IF;
 RETURN convert_to(jsonb_build_object('outcome','unavailable','reason',reason)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_receipt_refusal(uuid,text) FROM PUBLIC;

CREATE FUNCTION truss.reached(original_position bytea,maximum_evidence_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET bytea_output=hex AS $$
DECLARE locator jsonb;installation truss.catalog_runtime_installation%ROWTYPE;receipt truss.request_receipt%ROWTYPE;
 attempt truss.runtime_object_attempt%ROWTYPE;payload jsonb;included boolean;actual jsonb;
BEGIN
 PERFORM truss.runtime_person(false);
 IF pg_is_in_recovery() THEN RETURN convert_to('{"outcome":"unavailable","reason":"epoch_profile"}','UTF8');END IF;
 IF current_setting('transaction_read_only')<>'on' THEN RAISE EXCEPTION 'read-only receipt observation required' USING ERRCODE='0A000';END IF;
 IF original_position IS NULL OR octet_length(original_position) NOT BETWEEN 1 AND 16384 OR maximum_evidence_bytes IS NULL OR maximum_evidence_bytes NOT BETWEEN 1 AND 16777216 THEN
  RETURN convert_to('{"outcome":"unavailable","reason":"resource"}','UTF8');END IF;
 IF (convert_from(original_position,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RETURN convert_to('{"outcome":"unavailable","reason":"invalid_token"}','UTF8');END IF;
 locator:=convert_from(original_position,'UTF8')::jsonb;
 IF locator-ARRAY['interfaceVersion','positionProfile','installationId','sourceEpoch','receiptStorageRowId','writerXid']<>'{}'::jsonb
  OR locator->>'interfaceVersion' IS DISTINCT FROM 'truss-receipt-position/0.1.0'
  OR jsonb_typeof(locator->'receiptStorageRowId') IS DISTINCT FROM 'string' OR locator->>'receiptStorageRowId' !~ '^[1-9][0-9]{0,18}$'
  OR length(locator->>'receiptStorageRowId')=19 AND (locator->>'receiptStorageRowId') COLLATE "C">'9223372036854775807' THEN
  RETURN convert_to('{"outcome":"unavailable","reason":"invalid_token"}','UTF8');END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest
  OR locator->>'installationId' IS DISTINCT FROM installation.installation_id::text OR locator->>'sourceEpoch' IS DISTINCT FROM installation.source_epoch::text
  OR locator->'positionProfile' IS DISTINCT FROM truss.runtime_group_profiles()->'positionProfile' THEN RETURN convert_to('{"outcome":"unavailable","reason":"epoch_profile"}','UTF8');END IF;
 -- Admit original retained scope before any receipt-derived disclosure.
 SELECT * INTO attempt FROM truss.runtime_object_attempt WHERE receipt_id=(locator->>'receiptStorageRowId')::bigint;
 -- A well-formed token whose rows are not in this snapshot is not yet included.
 -- Rollback leaves it that way; the caller supplies its own wait bound.
 IF NOT FOUND THEN RETURN convert_to('{"outcome":"unavailable","reason":"not_yet"}','UTF8');END IF;
 IF attempt.position_bytes IS DISTINCT FROM original_position THEN RETURN convert_to('{"outcome":"unavailable","reason":"observation_integrity"}','UTF8');END IF;
 IF NOT truss.runtime_receipt_can_read(attempt.id) THEN RETURN convert_to('{"outcome":"unavailable","reason":"observation_integrity"}','UTF8');END IF;
 -- Receipt and snapshot come from one original native statement.
 SELECT to_jsonb(r),pg_visible_in_snapshot(r.original_writer_xid,pg_current_snapshot()) INTO actual,included FROM truss.request_receipt r WHERE storage_row_id=attempt.receipt_id;
 IF NOT FOUND THEN RETURN truss.runtime_receipt_refusal(attempt.id,'retention');END IF;
 receipt:=jsonb_populate_record(NULL::truss.request_receipt,actual);
 IF receipt.payload_state<>'complete' THEN RETURN truss.runtime_receipt_refusal(attempt.id,'retention');END IF;
 IF octet_length(attempt.input_bytes)+octet_length(receipt.original_receipt_bytes)+octet_length(original_position)>maximum_evidence_bytes THEN RETURN truss.runtime_receipt_refusal(attempt.id,'resource');END IF;
 payload:=convert_from(receipt.original_receipt_bytes,'UTF8')::jsonb;
 IF payload->>'profile' IS DISTINCT FROM 'truss-object-group-receipt/0.1' THEN RETURN truss.runtime_receipt_refusal(attempt.id,'epoch_profile');END IF;
 IF payload->>'attemptId' IS DISTINCT FROM attempt.id::text THEN RETURN convert_to('{"outcome":"unavailable","reason":"observation_integrity"}','UTF8');END IF;
 IF NOT attempt.complete OR receipt.original_writer_xid IS NOT DISTINCT FROM pg_current_xact_id_if_assigned()
  OR attempt.receipt_id IS DISTINCT FROM receipt.storage_row_id OR attempt.writer_xid IS DISTINCT FROM receipt.original_writer_xid
  OR to_jsonb(receipt) IS DISTINCT FROM attempt.expected_receipt OR attempt.position_bytes IS DISTINCT FROM original_position
  OR original_position IS DISTINCT FROM truss.runtime_receipt_position(attempt.context,receipt.storage_row_id,receipt.original_writer_xid)
  OR decode(payload->>'inputBase64','base64') IS DISTINCT FROM attempt.input_bytes
  OR payload->'semantic' IS DISTINCT FROM jsonb_build_object('interfaceVersion','truss-group-result/0.1.0','executedCatalogRevision',payload->'semantic'->>'executedCatalogRevision',
    'layoutProfile',convert_from(attempt.input_bytes,'UTF8')::jsonb->'layoutProfile','mutationProfile',convert_from(attempt.input_bytes,'UTF8')::jsonb->'mutationProfile','results',attempt.results,'aliases',attempt.aliases) THEN
  RETURN convert_to('{"outcome":"unavailable","reason":"observation_integrity"}','UTF8');END IF;
 SELECT to_jsonb(r) INTO actual FROM truss.request_receipt r WHERE storage_row_id=receipt.storage_row_id;
 IF actual IS DISTINCT FROM attempt.expected_receipt THEN RETURN convert_to('{"outcome":"unavailable","reason":"observation_integrity"}','UTF8');END IF;
 IF NOT truss.runtime_receipt_can_read(attempt.id) THEN RETURN convert_to('{"outcome":"unavailable","reason":"observation_integrity"}','UTF8');END IF;
 IF included IS NOT TRUE THEN RETURN convert_to('{"outcome":"unavailable","reason":"not_yet"}','UTF8');END IF;
 RETURN convert_to(jsonb_build_object('outcome','available','included',included,'comparisonProfile',attempt.context->'positionProfile')::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.reached(bytea,int,text,text) FROM PUBLIC;

-- The ordinary SQL write boundary accepts one entire group. Helpers are private;
-- a caller cannot leave execution between begin/step/finish. The caller still
-- owns the outer transaction and decides whether to commit or roll back.
CREATE FUNCTION truss.apply_group_prepared(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text,app_prepared jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE opened jsonb;attempt_id uuid;operation_index int:=0;operation_count int;result jsonb;
 native_state text;failure_code text;unavailable_reason text;parsed_input jsonb;
BEGIN
 opened:=convert_from(truss.object_group_begin_prepared(original_input,original_documents,original_request,expected_release,expected_digest,convert_to('[]','UTF8'),false,app_prepared),'UTF8')::jsonb;
 IF opened->>'outcome'<>'execute' THEN RETURN convert_to(opened::text,'UTF8');END IF;
 attempt_id:=(opened->>'attemptId')::uuid;
 parsed_input:=convert_from(original_input,'UTF8')::jsonb;
 operation_count:=jsonb_array_length(parsed_input->'operations');
 IF parsed_input->'mutationProfile'=truss.runtime_owned_profile() AND NOT EXISTS(
  SELECT 1 FROM jsonb_array_elements(parsed_input->'operations') o
  WHERE o.value->>'operation' IS DISTINCT FROM 'create_object'
   OR o.value->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb) THEN
  PERFORM truss.runtime_owned_create_batch(attempt_id);
 ELSIF parsed_input->'mutationProfile'=truss.runtime_owned_profile() AND NOT EXISTS(
  SELECT 1 FROM jsonb_array_elements(parsed_input->'operations') o
  WHERE o.value->>'operation' IS DISTINCT FROM 'create_edge'
   OR o.value->'source'->>'state' IS DISTINCT FROM 'stored'
   OR o.value->'target'->>'state' IS DISTINCT FROM 'stored') AND NOT EXISTS(
  SELECT 1 FROM truss.runtime_owned_operation p JOIN truss.rel_def r
   ON r.rel_type_id=(p.plan->'afterEdges'->(p.plan->>'primary')->'identity'->>'typeId')::int
  WHERE p.attempt_id=(opened->>'attemptId')::uuid AND r.lifecycle<>'independent') THEN
  PERFORM truss.runtime_owned_edge_create_batch(attempt_id);
 ELSIF parsed_input->'mutationProfile'=truss.runtime_owned_profile() AND NOT EXISTS(
  SELECT 1 FROM jsonb_array_elements(parsed_input->'operations') o
  WHERE o.value->>'operation' IS DISTINCT FROM 'update_object'
   OR o.value->'target'->>'state' IS DISTINCT FROM 'stored' OR o.value ? 'ownershipChange')
  AND (SELECT count(DISTINCT plan->>'primary') FROM truss.runtime_owned_operation p WHERE p.attempt_id=(opened->>'attemptId')::uuid)=operation_count THEN
  PERFORM truss.runtime_owned_update_batch(attempt_id);
 ELSE
 FOR step_index IN 0..operation_count-1 LOOP
  operation_index:=step_index;
  PERFORM truss.runtime_owned_group_step_in_input(attempt_id,operation_index,convert_to('[]','UTF8'),original_input,parsed_input);
 END LOOP;
 END IF;
 operation_index:=operation_count-1;
 result:=convert_from(truss.object_group_finish(attempt_id),'UTF8')::jsonb;
 -- Internal import provenance attaches to the same completed attempt. This field
 -- is outside the public semantic result and does not alter receipt bytes.
 RETURN convert_to((result||jsonb_build_object('attemptId',attempt_id::text))::text,'UTF8');
EXCEPTION WHEN SQLSTATE '22023' OR SQLSTATE '23505' OR SQLSTATE 'P1001' OR SQLSTATE 'P1003'
 OR SQLSTATE 'P1004' OR SQLSTATE 'P1005' OR SQLSTATE '42501' OR SQLSTATE '0A000'
 OR SQLSTATE '54000' OR SQLSTATE '55P03' THEN
 GET STACKED DIAGNOSTICS native_state=RETURNED_SQLSTATE;
 -- This exception block has rolled back admission, every step and finalization.
 -- Cancellation, deadlock and serialization errors propagate to host settlement.
 unavailable_reason:=CASE native_state WHEN '0A000' THEN 'profile' WHEN '54000' THEN 'resource' WHEN '55P03' THEN 'observation' END;
 IF unavailable_reason IS NOT NULL THEN
  RETURN convert_to(jsonb_build_object('outcome','unavailable','reason',unavailable_reason)::text,'UTF8');END IF;
 failure_code:=CASE native_state WHEN '22023' THEN 'invalid_input' WHEN '23505' THEN 'key_conflict'
  WHEN 'P1001' THEN 'request_conflict' WHEN 'P1003' THEN 'expected_version' WHEN 'P1004' THEN 'not_found'
  WHEN 'P1005' THEN 'dependencies' WHEN '42501' THEN 'unauthorized_person' END;
 RETURN convert_to(jsonb_build_object('outcome','failed','code',failure_code,'operationIndex',operation_index::text,'nativeState',native_state)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.apply_group_prepared(bytea,bytea,bytea,text,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.apply_group(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 RETURN truss.apply_group_prepared(original_input,original_documents,original_request,expected_release,expected_digest,NULL);
END;
$$;
REVOKE ALL ON FUNCTION truss.apply_group(bytea,bytea,bytea,text,text) FROM PUBLIC;

-- Each physical journal insert queues its own check, including after earlier
-- attempt/row constraints have already fired. No validation state is cached.
CREATE FUNCTION truss.runtime_owned_journal_insert_check() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE physical truss.journal%ROWTYPE;claims bigint;matching bigint;
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=session_user AND rolsuper) THEN RETURN NULL;END IF;
 IF NEW.xid IS DISTINCT FROM pg_current_xact_id() OR NEW.entity_kind NOT IN ('o','e') THEN
  RAISE EXCEPTION 'complete mutation journal required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT physical FROM truss.journal j WHERE j.at=NEW.at AND j.seq=NEW.seq;
 WITH expected(value) AS (
  SELECT g.expected_members->m.operation_index->'journal'
  FROM truss.runtime_create_member m JOIN truss.runtime_create_group g USING(group_id)
  WHERE NEW.entity_kind='o' AND m.object_id=NEW.entity_id AND m.type_id=NEW.entity_type AND g.writer_xid=pg_current_xact_id()
  UNION ALL
  SELECT j.value FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
  WHERE NEW.entity_kind='o' AND t.object_id=NEW.entity_id AND t.type_id=NEW.entity_type AND t.writer_xid=pg_current_xact_id()
  UNION ALL
  SELECT j.value FROM truss.runtime_catalog_rebind_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
  WHERE NEW.entity_kind='o' AND t.object_id=NEW.entity_id AND t.type_id=NEW.entity_type AND t.writer_xid=pg_current_xact_id()
  UNION ALL
  SELECT j.value FROM truss.runtime_edge_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j
  WHERE NEW.entity_kind='e' AND t.edge_id=NEW.entity_id AND t.rel_type_id=NEW.entity_type AND t.writer_xid=pg_current_xact_id()
 )
 SELECT count(*),count(*) FILTER(WHERE CASE WHEN value ? 'referenceProfile'
  THEN value=truss.runtime_owned_journal_reference(physical) ELSE value=to_jsonb(physical) END) INTO claims,matching FROM expected
 WHERE (value->>'at')::timestamptz=NEW.at AND (value->>'seq')::bigint=NEW.seq;
 IF claims<>1 OR matching<>1 THEN RAISE EXCEPTION 'complete mutation journal required' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_journal_insert_check() FROM PUBLIC;
CREATE CONSTRAINT TRIGGER runtime_owned_journal_insert_commit AFTER INSERT ON truss.journal DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_owned_journal_insert_check();
ALTER TABLE truss.journal ENABLE ALWAYS TRIGGER runtime_owned_journal_insert_commit;
