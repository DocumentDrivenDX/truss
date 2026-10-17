-- Connected rootless scalar-string create group runtime. Feed stays unavailable.
ALTER TABLE truss.catalog_runtime_installation ADD COLUMN source_epoch uuid NOT NULL DEFAULT pg_catalog.gen_random_uuid();

-- Match the existing original-definition pin recipe without reserializing source.
CREATE FUNCTION truss.runtime_definition_in_basis(selected_kind text,selected_type int,selected_number int,historical_revision int,basis jsonb)
RETURNS TABLE(definition_pin text,original_fragment bytea,original_pointer text,document_id text,module_id text,element_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE source_kind text;source_revision int;source_ordinal int;source_document text;source_key text; archive truss.schema_doc%ROWTYPE; native_type truss.type_def%ROWTYPE;
 source_module text;source_element text;module_json json;document_lookup jsonb;module_lookup jsonb;element_lookup jsonb;module_index int;element_json json;element_index int;
 key_json json;key_index int;fragment json;pointer text;pin_input text;
BEGIN
 IF historical_revision IS NULL THEN
  SELECT * INTO STRICT native_type FROM truss.type_def WHERE type_id=selected_type AND NOT provisional AND retired_rev IS NULL;
 ELSE
  IF basis IS NULL THEN RAISE EXCEPTION 'resolved historical catalog required' USING ERRCODE='22023'; END IF;
  SELECT * INTO STRICT native_type FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t WHERE t.type_id=selected_type;
 END IF;
 IF selected_kind='type' THEN
  source_kind:=native_type.definition_source_kind;source_revision:=native_type.definition_rev;
  source_ordinal:=native_type.definition_doc_ord;source_document:=native_type.definition_document_id;
  source_module:=native_type.module;source_element:=native_type.element;
 ELSIF selected_kind='property' THEN
  IF historical_revision IS NULL THEN
   SELECT p.definition_source_kind,p.definition_rev,p.definition_doc_ord,p.definition_document_id,p.declaration_module,p.element INTO STRICT source_kind,source_revision,source_ordinal,source_document,source_module,source_element FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=selected_number AND p.retired_rev IS NULL;
  ELSE
   SELECT p.definition_source_kind,p.definition_rev,p.definition_doc_ord,p.definition_document_id,p.declaration_module,p.element INTO STRICT source_kind,source_revision,source_ordinal,source_document,source_module,source_element FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=selected_type AND p.prop_id=selected_number;
  END IF;
 ELSIF selected_kind='key' THEN
  IF historical_revision IS NULL THEN
   SELECT k.definition_source_kind,k.definition_rev,k.definition_doc_ord,k.definition_document_id,k.key_id INTO STRICT source_kind,source_revision,source_ordinal,source_document,source_key FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_num=selected_number AND k.retired_rev IS NULL;
  ELSE
   SELECT k.definition_source_kind,k.definition_rev,k.definition_doc_ord,k.definition_document_id,k.key_id INTO STRICT source_kind,source_revision,source_ordinal,source_document,source_key FROM jsonb_populate_recordset(NULL::truss.key_def,basis->'key_def') k WHERE k.type_id=selected_type AND k.key_num=selected_number;
  END IF;
  source_module:=native_type.module;source_element:=native_type.element;
 ELSE RAISE EXCEPTION 'supported definition kind required' USING ERRCODE='22023'; END IF;
 IF source_kind<>'accepted_document' OR source_revision<1 THEN
  RAISE EXCEPTION 'original accepted definition source required' USING ERRCODE='0A000'; END IF;
 SELECT * INTO STRICT archive FROM truss.schema_doc d WHERE d.rev=source_revision AND d.ord=source_ordinal
  AND d.doc_id=source_document;
 -- Binary JSON is used only to locate coordinates, never for source bytes.
 BEGIN
  document_lookup:=archive.document::jsonb;
 EXCEPTION WHEN untranslatable_character OR numeric_value_out_of_range THEN
  -- Unknown JSON content may be valid source but outside JSONB's value domain.
  document_lookup:=NULL;
 END;
 IF document_lookup IS NULL THEN
  SELECT m.value,m.ordinality::int-1 INTO STRICT module_json,module_index
   FROM json_array_elements(archive.document::json->'modules') WITH ORDINALITY m WHERE m.value->>'id'=source_module;
  SELECT e.value,e.ordinality::int-1 INTO STRICT element_json,element_index
   FROM json_array_elements(module_json->'elements') WITH ORDINALITY e WHERE e.value->>'id'=source_element;
 ELSE
 SELECT m.value,m.ordinality::int-1 INTO STRICT module_lookup,module_index
  FROM jsonb_array_elements(document_lookup->'modules') WITH ORDINALITY m WHERE m.value->>'id'=source_module;
 SELECT e.value,e.ordinality::int-1 INTO STRICT element_lookup,element_index
  FROM jsonb_array_elements(module_lookup->'elements') WITH ORDINALITY e WHERE e.value->>'id'=source_element;
 element_json:=json_extract_path(archive.document::json,'modules',module_index::text,'elements',element_index::text);
 END IF;
 fragment:=element_json;pointer:='/modules/'||module_index||'/elements/'||element_index;
 IF selected_kind='key' THEN
  IF document_lookup IS NULL THEN
   SELECT k.value,k.ordinality::int-1 INTO STRICT key_json,key_index
    FROM json_array_elements(element_json->'keys') WITH ORDINALITY k WHERE k.value->>'id'=source_key;
  ELSE
   SELECT k.ordinality::int-1 INTO STRICT key_index
    FROM jsonb_array_elements(element_lookup->'keys') WITH ORDINALITY k WHERE k.value->>'id'=source_key;
   key_json:=json_extract_path(element_json,'keys',key_index::text);
  END IF;
  fragment:=key_json;pointer:=pointer||'/keys/'||key_index;
 END IF;
 original_fragment:=convert_to(fragment::text,'UTF8');original_pointer:=pointer;
 pin_input:='['||archive.rev||','||archive.ord||',"'||archive.content_sha256||'","'||pointer
  ||'",{"identity":"truss-original-json-definition","sha256":"08c2ec8c520b39ded40f270be0b26812db1d240d5bac1a00339b437200a2f58d","version":"0.1"},"'
  ||encode(sha256(original_fragment),'hex')||'"]';
 definition_pin:=encode(sha256(convert_to(pin_input,'UTF8')),'hex');
 document_id:=native_type.document_id;module_id:=native_type.module;element_id:=native_type.element;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_definition_in_basis(text,int,int,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_definition(selected_kind text,selected_type int,selected_number int DEFAULT NULL,historical_revision int DEFAULT NULL)
RETURNS TABLE(definition_pin text,original_fragment bytea,original_pointer text,document_id text,module_id text,element_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE basis jsonb;
BEGIN
 IF historical_revision IS NOT NULL THEN
  -- The accepted head already contains these exact definition coordinates.
  -- Older revisions still reconstruct their original accepted catalog.
  SELECT CASE WHEN historical_revision=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>historical_revision)
  THEN jsonb_build_object(
   'type_def',(SELECT coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) FROM truss.type_def t WHERE t.type_id=selected_type),
   'prop_def',(SELECT coalesce(jsonb_agg(to_jsonb(p)),'[]'::jsonb) FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=selected_number),
   'key_def',(SELECT coalesce(jsonb_agg(to_jsonb(k)),'[]'::jsonb) FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_num=selected_number)) END INTO basis;
  IF basis IS NULL THEN basis:=truss.catalog_all_expected_records(historical_revision);END IF;
 END IF;
 RETURN QUERY SELECT * FROM truss.runtime_definition_in_basis(selected_kind,selected_type,selected_number,historical_revision,basis);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_definition(text,int,int,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_group_profiles() RETURNS jsonb LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ SELECT jsonb_build_object(
'creationTransitionProfile','{"identity":"truss-unified-create-transition","version":"0.2","sha256":"073782e2517f2a7e26c8d6479c6266ececf68963681ccfb6a380e9cd16f2e11b"}'::jsonb,
'mutationProfile',jsonb_build_object('identity','truss-owned-scalar-graph','version','0.1','sha256','5f5badaa3b0beb01fef08d48883395eabc8499155d4c31f7ef802e63d49a6dde'),
'valueProfile','{"identity":"truss-scalar-string-values","version":"0.6","sha256":"ca49b4e13a55be8e23d44d4b00ef07332b6249d4f5ae16e5b82c8881061e22ce"}'::jsonb,
'canonicalizationProfile',jsonb_build_object('identity','truss-pg18-jsonb-text','version','0.1','sha256','e5eec0aa3dfd5195250bb2e781626c6229f645d71a5c21095ee3d10008aadc97'),
'requestFingerprintProfile',jsonb_build_object('identity','truss-python-create-request-bytes','version','0.1','sha256','69974e716b09892428ce6f3fe5c4b01825bad35104b25dcd861152da60965baa'),
'adapterProfile',jsonb_build_object('identity','truss-psycopg-create-provider','version','0.1','sha256','f20735a94e87213d77f713cbbabd2bdf2e4f2b459041c53bb984f5b706112ba9'),
'positionProfile',jsonb_build_object('identity','truss-authority-receipt-visibility','version','0.1','sha256','97d54f46af687510fd3ae10aaa37c761d17d6b371d12171ea15a0d402b8855e9'),
'policyProfile',jsonb_build_object('identity','truss-qualified-module-writer','version','0.2','sha256','f0f41d6dfa0cc38f1340fd1516679ff985824f9cb79034923330b16c2fb3ec4f')); $$;
REVOKE ALL ON FUNCTION truss.runtime_group_profiles() FROM PUBLIC;

-- Private actor is issued by the current native invocation, never retained
-- or accepted from a public caller. Module policy/membership checks stay live.
CREATE FUNCTION truss.runtime_module_writer_qualified(selected_document text,selected_module text,qualified_actor oid) RETURNS oid
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE person oid;policy truss.module_access%ROWTYPE;
BEGIN
 person:=qualified_actor;
 SELECT * INTO policy FROM truss.module_access WHERE document_id=selected_document AND module=selected_module FOR SHARE NOWAIT;
 IF NOT FOUND OR NOT EXISTS(WITH RECURSIVE memberships(role_oid) AS (
  SELECT person UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
  SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid WHERE r.rolname::text=policy.writer_role) THEN
  RAISE EXCEPTION 'current qualified module writer required' USING ERRCODE='42501'; END IF;
 RETURN person;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_module_writer_qualified(text,text,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_module_writer(selected_document text,selected_module text) RETURNS oid
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN truss.runtime_module_writer_qualified(selected_document,selected_module,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_module_writer(text,text) FROM PUBLIC;

CREATE FUNCTION truss.group_context_qualified(expected_release text,expected_digest text,qualified_actor oid) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE person oid;installation truss.catalog_runtime_installation%ROWTYPE;revision int;
BEGIN
 person:=qualified_actor;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected installed group runtime required' USING ERRCODE='0A000'; END IF;
 SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 IF revision<1 THEN RAISE EXCEPTION 'accepted catalog required' USING ERRCODE='0A000'; END IF;
 RETURN convert_to((truss.runtime_group_profiles()||jsonb_build_object('layoutProfile',installation.layout_profile,
  'authorizedScopeIdentity','truss-person:'||installation.installation_id||':'||person::text,
  'installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,'historyProfile',
   CASE WHEN truss.runtime_group_profiles()->'mutationProfile'=truss.runtime_owned_profile() THEN 'truss-native-owned-create/0.1' ELSE 'truss-native-scalar-create/0.2' END))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.group_context_qualified(text,text,oid) FROM PUBLIC;

CREATE FUNCTION truss.group_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 RETURN truss.group_context_qualified(expected_release,expected_digest,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.group_context(text,text) FROM PUBLIC;

-- Resolve only requested, currently writable definitions. Original whole documents
-- are caller-supplied, independently compared in full to the retained archive.
CREATE FUNCTION truss.group_create_metadata_qualified(original_input bytea,original_documents bytea,expected_release text,expected_digest text,qualified_actor oid) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE input jsonb;documents jsonb;operation jsonb;context jsonb;selected_type truss.type_def%ROWTYPE;
 source_pin record;archive truss.schema_doc%ROWTYPE;metadata jsonb:='[]';counted int:=0;source_text text;
BEGIN
 context:=convert_from(truss.group_context_qualified(expected_release,expected_digest,qualified_actor),'UTF8')::jsonb;
 IF original_input IS NULL OR octet_length(original_input) NOT BETWEEN 1 AND 1048576
 OR original_documents IS NULL OR octet_length(original_documents) NOT BETWEEN 1 AND 4194304 THEN
  RAISE EXCEPTION 'bounded group source required' USING ERRCODE='54000'; END IF;
 IF (convert_from(original_input,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE OR (convert_from(original_documents,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'unique original JSON members required' USING ERRCODE='22023'; END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;documents:=convert_from(original_documents,'UTF8')::jsonb;
 IF input->>'interfaceVersion' IS DISTINCT FROM 'truss-group-input/0.1.0'
 OR input->'layoutProfile' IS DISTINCT FROM context->'layoutProfile'
 OR input->'mutationProfile' IS DISTINCT FROM context->'mutationProfile'
 OR input->'valueProfile' IS DISTINCT FROM context->'valueProfile'
 OR input->'catalog' IS DISTINCT FROM '{"selection":"current"}'::jsonb
 OR jsonb_typeof(input->'operations') IS DISTINCT FROM 'array' OR jsonb_array_length(input->'operations') NOT BETWEEN 1 AND 128
 OR jsonb_typeof(documents) IS DISTINCT FROM 'array' OR jsonb_array_length(documents) NOT BETWEEN 1 AND 512 THEN
  RAISE EXCEPTION 'selected create group profile required' USING ERRCODE='0A000'; END IF;
 FOR operation IN SELECT value FROM jsonb_array_elements(input->'operations') LOOP
  IF operation->>'operation' IS DISTINCT FROM 'create_object' OR
   (operation->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb AND
    (input->'mutationProfile'=truss.runtime_owned_profile() AND operation->'ownership'->>'state'='owned'
     AND (operation->'ownership')-ARRAY['state','root']='{}'::jsonb) IS NOT TRUE) THEN
   RAISE EXCEPTION 'explicit selected create ownership required' USING ERRCODE='0A000'; END IF;
  SELECT t.* INTO STRICT selected_type FROM truss.type_def t CROSS JOIN LATERAL truss.runtime_definition('type',t.type_id) p
   WHERE t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL AND p.definition_pin=operation->>'typeDefinitionPin';
  PERFORM truss.runtime_module_writer_qualified(selected_type.document_id,selected_type.module,qualified_actor);
  IF NOT truss.runtime_object_values_readable_qualified(selected_type.type_id,qualified_actor) THEN RAISE EXCEPTION 'current property and item interpretation reader required' USING ERRCODE='42501';END IF;
  SELECT * INTO STRICT archive FROM truss.schema_doc d WHERE d.doc_id=selected_type.document_id ORDER BY d.rev DESC LIMIT 1;
  SELECT d.value->>'sourceText' INTO STRICT source_text FROM jsonb_array_elements(documents) d
   WHERE d.value->>'documentId'=archive.doc_id;
  IF convert_to(source_text,'UTF8') IS DISTINCT FROM convert_to(archive.document,'UTF8') THEN
   RAISE EXCEPTION 'complete original accepted source required' USING ERRCODE='22023'; END IF;
  counted:=counted+1;
  metadata:=metadata||jsonb_build_array(jsonb_build_object('operationIndex',counted-1,'typeId',selected_type.type_id::text,
   'documentId',selected_type.document_id,'moduleId',selected_type.module,'recordId',selected_type.element,
   'keys',(SELECT coalesce(jsonb_agg(jsonb_build_object('keyNumber',k.key_num::text,'keyId',k.key_id,
    'names',(SELECT jsonb_agg(p.name ORDER BY i.ord) FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ord)
      JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=k.type_id)) ORDER BY k.key_num),'[]'::jsonb)
    FROM truss.key_def k WHERE k.type_id=selected_type.type_id AND k.retired_rev IS NULL)));
 END LOOP;
 RETURN convert_to(metadata::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.group_create_metadata_qualified(bytea,bytea,text,text,oid) FROM PUBLIC;

CREATE FUNCTION truss.group_create_metadata(original_input bytea,original_documents bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 RETURN truss.group_create_metadata_qualified(original_input,original_documents,expected_release,expected_digest,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.group_create_metadata(bytea,bytea,text,text) FROM PUBLIC;

-- A finite selected native horizon; no default partition hides expiry.
DO $$
DECLARE lower_bound timestamptz:=date_trunc('month',clock_timestamp())-interval '1 month';
 upper_bound timestamptz:=date_trunc('month',clock_timestamp())+interval '13 months';
BEGIN
 EXECUTE format('CREATE TABLE truss.journal_runtime_horizon PARTITION OF truss.journal FOR VALUES FROM (%L) TO (%L)',lower_bound,upper_bound);
END;
$$;

CREATE TABLE truss.runtime_create_group (
 group_id uuid PRIMARY KEY,writer_xid xid8 NOT NULL,actor_oid oid NOT NULL,actor_name text NOT NULL,
 original_input_bytes bytea NOT NULL,original_document_bytes bytea NOT NULL,original_key_bytes bytea NOT NULL,
 semantic_bytes bytea NOT NULL,expected_members jsonb NOT NULL,
 receipt_storage_row_id bigint REFERENCES truss.request_receipt(storage_row_id),expected_receipt jsonb,
 CHECK(octet_length(original_input_bytes) BETWEEN 1 AND 1048576),
 CHECK(octet_length(original_document_bytes) BETWEEN 1 AND 4194304),
 CHECK(octet_length(original_key_bytes) BETWEEN 1 AND 8388608),
 CHECK(octet_length(semantic_bytes) BETWEEN 1 AND 16777216),
 CHECK(jsonb_typeof(expected_members)='array' AND jsonb_array_length(expected_members) BETWEEN 1 AND 128),
 CHECK((receipt_storage_row_id IS NULL)=(expected_receipt IS NULL)));
CREATE INDEX runtime_create_group_writer ON truss.runtime_create_group(writer_xid);
CREATE TABLE truss.runtime_create_member (
 object_id bigint NOT NULL,type_id int NOT NULL,group_id uuid NOT NULL REFERENCES truss.runtime_create_group(group_id),
 operation_index int NOT NULL CHECK(operation_index BETWEEN 0 AND 127),
 PRIMARY KEY(object_id,type_id),UNIQUE(group_id,operation_index));

CREATE TRIGGER runtime_create_group_immutable BEFORE UPDATE OR DELETE ON truss.runtime_create_group
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_create_member_immutable BEFORE UPDATE OR DELETE ON truss.runtime_create_member
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_receipt_immutable BEFORE UPDATE OR DELETE ON truss.request_receipt
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_journal_immutable BEFORE UPDATE OR DELETE ON truss.journal
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_key_reservation_immutable BEFORE UPDATE OR DELETE ON truss.object_key_reservation_bucket
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();

CREATE FUNCTION truss.runtime_exact_wrapper(component text,original_bytes bytea) RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT jsonb_build_object('interfaceVersion','truss-journal-exact-bytes/0.2.0-proposal',
 'eventInterfaceVersion','truss-history-event/0.2.0-proposal','component',component,
 'canonicalizationProfile',truss.runtime_group_profiles()->'canonicalizationProfile',
 'bytesBase64',replace(encode(original_bytes,'base64'),chr(10),''),'bytesSha256',encode(sha256(original_bytes),'hex'));
$$;
REVOKE ALL ON FUNCTION truss.runtime_exact_wrapper(text,bytea) FROM PUBLIC;

CREATE FUNCTION truss.runtime_create_validate_member(selected_id bigint,selected_type int) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE member truss.runtime_create_member%ROWTYPE;group_row truss.runtime_create_group%ROWTYPE;
 expected jsonb;actual_object jsonb;actual_journal jsonb;key_expected jsonb;actual_key jsonb;actual_reservation jsonb;current_generation bigint;
BEGIN
 SELECT * INTO STRICT member FROM truss.runtime_create_member WHERE object_id=selected_id AND type_id=selected_type;
 SELECT * INTO STRICT group_row FROM truss.runtime_create_group WHERE group_id=member.group_id;
 IF group_row.writer_xid<>pg_current_xact_id() OR group_row.actor_name<>session_user::text OR group_row.actor_oid IS DISTINCT FROM (SELECT oid FROM pg_roles WHERE rolname=session_user) THEN
  RAISE EXCEPTION 'current actual group member required' USING ERRCODE='55000'; END IF;
 expected:=group_row.expected_members->member.operation_index;
 IF (SELECT count(*) FROM truss.runtime_object_transition t
  WHERE t.object_id=selected_id AND t.type_id=selected_type AND t.writer_xid=group_row.writer_xid
   AND t.before_object IS NULL)<>1 THEN
  RAISE EXCEPTION 'one original outer creation transition required' USING ERRCODE='55000';END IF;
 IF EXISTS(SELECT 1 FROM truss.runtime_object_transition WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()) OR EXISTS(SELECT 1 FROM truss.runtime_catalog_rebind_transition WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()) OR EXISTS(SELECT 1 FROM truss.runtime_catalog_key_backfill WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()) THEN
  PERFORM truss.runtime_object_validate(selected_id,selected_type);
  SELECT to_jsonb(j) INTO actual_journal FROM truss.journal j WHERE j.at=(expected->'journal'->>'at')::timestamptz AND j.seq=(expected->'journal'->>'seq')::bigint;
  IF actual_journal IS DISTINCT FROM expected->'journal' THEN RAISE EXCEPTION 'original creation journal required' USING ERRCODE='55000';END IF;
  FOR key_expected IN SELECT value FROM jsonb_array_elements(expected->'keys') LOOP
   SELECT to_jsonb(r) INTO actual_reservation FROM truss.object_key_reservation_bucket r WHERE storage_row_id=(key_expected->'reservation'->>'storage_row_id')::bigint;
   IF actual_reservation IS DISTINCT FROM key_expected->'reservation' THEN RAISE EXCEPTION 'original creation reservation required' USING ERRCODE='55000';END IF;
   SELECT generation INTO current_generation FROM truss.key_bucket_guard
    WHERE namespace_sha256=decode(substring(key_expected->'membership'->>'namespace_sha256' FROM 3),'hex')
     AND key_sha256=decode(substring(key_expected->'membership'->>'key_sha256' FROM 3),'hex');
   IF current_generation IS NULL OR current_generation<(key_expected->>'generation')::bigint THEN
    RAISE EXCEPTION 'original creation key generation required' USING ERRCODE='55000';END IF;
  END LOOP;
  RETURN;
 END IF;
 IF (expected->'object'->>'id')::bigint<>selected_id OR (expected->'object'->>'type_id')::int<>selected_type THEN
  RAISE EXCEPTION 'exact operation member required' USING ERRCODE='55000'; END IF;
 SELECT to_jsonb(o) INTO actual_object FROM truss.object o WHERE id=selected_id AND type_id=selected_type;
 IF actual_object IS DISTINCT FROM expected->'object' THEN
  RAISE EXCEPTION 'complete created object changed or missing' USING ERRCODE='55000'; END IF;
 SELECT to_jsonb(j) INTO actual_journal FROM truss.journal j WHERE j.at=(expected->'journal'->>'at')::timestamptz
  AND j.seq=(expected->'journal'->>'seq')::bigint;
 IF actual_journal IS DISTINCT FROM expected->'journal' OR (SELECT count(*) FROM truss.journal WHERE entity_kind='o' AND entity_id=selected_id AND entity_type=selected_type AND xid=group_row.writer_xid)<>1 THEN
  RAISE EXCEPTION 'complete create journal changed or missing' USING ERRCODE='55000'; END IF;
 IF (SELECT count(*) FROM truss.object_key_bucket WHERE object_id=selected_id AND type_id=selected_type)
  <>jsonb_array_length(expected->'keys') THEN
  RAISE EXCEPTION 'complete created key membership required' USING ERRCODE='55000'; END IF;
 FOR key_expected IN SELECT value FROM jsonb_array_elements(expected->'keys') LOOP
  SELECT to_jsonb(k) INTO actual_key FROM truss.object_key_bucket k WHERE storage_row_id=(key_expected->'membership'->>'storage_row_id')::bigint;
  SELECT to_jsonb(r) INTO actual_reservation FROM truss.object_key_reservation_bucket r WHERE storage_row_id=(key_expected->'reservation'->>'storage_row_id')::bigint;
  SELECT generation INTO current_generation FROM truss.key_bucket_guard WHERE namespace_sha256=decode(substring(actual_key->>'namespace_sha256' FROM 3),'hex') AND key_sha256=decode(substring(actual_key->>'key_sha256' FROM 3),'hex');
  IF current_generation IS NULL OR current_generation<(key_expected->>'generation')::bigint OR actual_key IS DISTINCT FROM key_expected->'membership' OR actual_reservation IS DISTINCT FROM key_expected->'reservation'
   OR NOT truss.verify_object_string_key(selected_id,selected_type,(actual_key->>'key_num')::smallint,
     decode(substring(convert_from(decode(substring(actual_key->>'key_bytes' FROM 3),'hex'),'UTF8') FROM 22),'hex')) THEN
   RAISE EXCEPTION 'exact created key or reservation required' USING ERRCODE='55000'; END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_create_validate_member(bigint,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_create_validate_group(selected_group uuid) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE group_row truss.runtime_create_group%ROWTYPE;actual_receipt jsonb;semantic jsonb;entry jsonb;member record;
BEGIN
 SELECT * INTO STRICT group_row FROM truss.runtime_create_group WHERE group_id=selected_group;
 semantic:=convert_from(group_row.semantic_bytes,'UTF8')::jsonb;
 IF group_row.writer_xid<>pg_current_xact_id() OR group_row.actor_name<>session_user::text OR group_row.actor_oid IS DISTINCT FROM (SELECT oid FROM pg_roles WHERE rolname=session_user)
 OR jsonb_array_length(semantic->'results')<>jsonb_array_length(group_row.expected_members)
 OR (SELECT count(*) FROM truss.runtime_create_member WHERE group_id=selected_group)<>jsonb_array_length(group_row.expected_members) THEN
  RAISE EXCEPTION 'complete actual create group required' USING ERRCODE='55000'; END IF;
 IF group_row.receipt_storage_row_id IS NOT NULL THEN
  SELECT to_jsonb(r) INTO actual_receipt FROM truss.request_receipt r WHERE storage_row_id=group_row.receipt_storage_row_id;
  IF actual_receipt IS DISTINCT FROM group_row.expected_receipt THEN
   RAISE EXCEPTION 'exact durable group receipt required' USING ERRCODE='55000'; END IF;
 END IF;
 -- Caller-controlled settings cannot authorize skipping integrity checks.
 IF (SELECT coalesce(jsonb_agg(to_jsonb(j) ORDER BY j.at,j.seq),'[]'::jsonb)
     FROM truss.journal j WHERE j.xid=group_row.writer_xid)
 IS DISTINCT FROM (SELECT coalesce(jsonb_agg(e.value ORDER BY (e.value->>'at')::timestamptz,(e.value->>'seq')::bigint),'[]'::jsonb) FROM (
     SELECT e.value->'journal' AS value FROM truss.runtime_create_group g CROSS JOIN LATERAL jsonb_array_elements(g.expected_members) e(value) WHERE g.writer_xid=group_row.writer_xid
     UNION ALL SELECT j.value FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j WHERE t.writer_xid=group_row.writer_xid
     UNION ALL SELECT j.value FROM truss.runtime_catalog_rebind_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j WHERE t.writer_xid=group_row.writer_xid
     UNION ALL SELECT j.value FROM truss.runtime_edge_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j WHERE t.writer_xid=group_row.writer_xid) e) THEN
  RAISE EXCEPTION 'complete transaction create journal required' USING ERRCODE='55000'; END IF;
 FOR member IN SELECT * FROM truss.runtime_create_member WHERE group_id=selected_group ORDER BY operation_index LOOP
  entry:=semantic->'results'->member.operation_index;
  IF (entry->'identity'->>'id')::bigint<>member.object_id OR (entry->'identity'->>'typeId')::int<>member.type_id THEN
   RAISE EXCEPTION 'ordered native group result required' USING ERRCODE='55000'; END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_create_validate_group(uuid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_create_commit_check() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 -- Trusted administrators may seed private read fixtures; they cannot call the
 -- ordinary-person mutation facade. This is not an ordinary-caller bypass.
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=session_user AND rolsuper) THEN RETURN NULL; END IF;
 IF TG_TABLE_NAME='object' THEN
  IF EXISTS(SELECT 1 FROM truss.runtime_object_transition t JOIN truss.runtime_object_attempt a ON a.id=t.attempt_id
   WHERE t.object_id=NEW.id AND t.type_id=NEW.type_id AND t.before_object IS NULL
    AND t.writer_xid=pg_current_xact_id() AND a.context->'creationTransitionProfile'='{"identity":"truss-unified-create-transition","version":"0.2","sha256":"073782e2517f2a7e26c8d6479c6266ececf68963681ccfb6a380e9cd16f2e11b"}'::jsonb) THEN
   PERFORM truss.runtime_object_validate(NEW.id,NEW.type_id);
  ELSE PERFORM truss.runtime_create_validate_member(NEW.id,NEW.type_id);END IF;
 ELSIF TG_TABLE_NAME='runtime_create_group' THEN PERFORM truss.runtime_create_validate_group(NEW.group_id);
 ELSE RAISE EXCEPTION 'registered create commit event required' USING ERRCODE='55000'; END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_create_commit_check() FROM PUBLIC;
CREATE CONSTRAINT TRIGGER runtime_created_object_commit AFTER INSERT ON truss.object
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_create_commit_check();
CREATE CONSTRAINT TRIGGER runtime_created_group_commit AFTER INSERT ON truss.runtime_create_group
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_create_commit_check();
ALTER TABLE truss.object ENABLE ALWAYS TRIGGER runtime_created_object_commit;
ALTER TABLE truss.runtime_create_group ENABLE ALWAYS TRIGGER runtime_created_group_commit;

CREATE FUNCTION truss.apply_create_group_qualified(original_input bytea,original_documents bytea,original_keys bytea,original_request bytea,expected_release text,expected_digest text,qualified_actor oid,selected_attempt uuid DEFAULT NULL,selected_original bytea DEFAULT NULL,selected_input jsonb DEFAULT NULL) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
<<creation_leaf>>
DECLARE input jsonb;request jsonb;key_inputs jsonb;metadata jsonb;context jsonb;installation truss.catalog_runtime_installation%ROWTYPE;
 source_pin record;actor_oid oid;writer xid8;group_uuid uuid:=gen_random_uuid();current_index int:=0;operation jsonb;operation_meta jsonb;
 selected_type truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;key_definition truss.key_def%ROWTYPE;
 supplied_value jsonb;props jsonb;retained jsonb;planned jsonb:='[]';planned_keys jsonb:='[]';key_plan jsonb;key_input jsonb;
 values_text text[];values_cells jsonb;key_facets jsonb;component record;namespace bytea;transport bytea;tuple_bytes bytea;owner_receipt jsonb;
 route record;observed record;planned_row jsonb;actual_row jsonb;object_row truss.object%ROWTYPE;
 object_identity jsonb;properties_json jsonb;retained_json jsonb;after_record jsonb;event jsonb;event_bytes bytea;origin_bytes bytea;
 journal_row truss.journal%ROWTYPE;expected_journal jsonb;actual_journal jsonb;event_digest text;
 expected_transition jsonb;actual_transition jsonb;actual_progress record;physical_journal jsonb;stored_result jsonb;
 results jsonb:='[]';aliases jsonb:='[]';members jsonb:='[]';member_keys jsonb;
 membership truss.object_key_bucket%ROWTYPE;reservation truss.object_key_reservation_bucket%ROWTYPE;
 semantic jsonb;semantic_bytes bytea;new_generation bigint;
 captured_revision int;outcome jsonb;outer_attempt record;
 owned_plan jsonb;owned_state jsonb;root_reference text;root_identity jsonb;root_object truss.object%ROWTYPE;selected_history text;
BEGIN
 -- Private create execution: request admission, replay and rollback belong to
 -- the outer group. Keep its one public exception boundary around all operations.
 IF original_input IS NULL OR octet_length(original_input) NOT BETWEEN 1 AND 1048576
  OR original_documents IS NULL OR octet_length(original_documents) NOT BETWEEN 1 AND 4194304 THEN
  RAISE EXCEPTION 'bounded original create source required' USING ERRCODE='54000';END IF;
 IF (convert_from(original_input,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  OR (convert_from(original_documents,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'unique original create source required' USING ERRCODE='22023';END IF;
 context:=convert_from(truss.group_context_qualified(expected_release,expected_digest,qualified_actor),'UTF8')::jsonb;
 actor_oid:=qualified_actor;writer:=pg_current_xact_id();
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF original_keys IS NULL OR octet_length(original_keys) NOT BETWEEN 1 AND 8388608
 OR original_request IS NULL OR octet_length(original_request) NOT BETWEEN 1 AND 65536 THEN
  RAISE EXCEPTION 'bounded group keys and request required' USING ERRCODE='54000'; END IF;
 IF (convert_from(original_keys,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE OR (convert_from(original_request,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'unique key/request JSON members required' USING ERRCODE='22023'; END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;request:=convert_from(original_request,'UTF8')::jsonb;
 key_inputs:=convert_from(original_keys,'UTF8')::jsonb;
 IF key_inputs<>'[]'::jsonb THEN RAISE EXCEPTION 'client key encoding is no longer accepted' USING ERRCODE='22023';END IF;
 IF input-ARRAY['interfaceVersion','layoutProfile','mutationProfile','valueProfile','catalog','operations','assertedOrigin']<>'{}'::jsonb
 OR input->'assertedOrigin'->>'kind' IS DISTINCT FROM 'map' OR jsonb_typeof(input->'assertedOrigin'->'entries') IS DISTINCT FROM 'array'
 OR (input->'assertedOrigin')-ARRAY['kind','entries']<>'{}'::jsonb THEN
  RAISE EXCEPTION 'closed selected group and origin required' USING ERRCODE='22023'; END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e
  WHERE jsonb_typeof(e.value->'key') IS DISTINCT FROM 'string' OR e.value-ARRAY['key','value']<>'{}'::jsonb
  OR (e.value->'value'='{"kind":"null"}'::jsonb OR (e.value->'value'->>'kind'='string'
   AND jsonb_typeof(e.value->'value'->'text')='string' AND (e.value->'value')-ARRAY['kind','text']='{}'::jsonb)) IS NOT TRUE)
 OR (SELECT count(*) FROM jsonb_array_elements(input->'assertedOrigin'->'entries'))
  <>(SELECT count(DISTINCT e.value->>'key') FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e) THEN
  RAISE EXCEPTION 'exact unique scalar asserted origin required' USING ERRCODE='22023'; END IF;
 IF request IS DISTINCT FROM '{"state":"none"}'::jsonb THEN
  RAISE EXCEPTION 'outer group owns request identity and replay' USING ERRCODE='22023';END IF;
 metadata:=convert_from(truss.group_create_metadata_qualified(original_input,original_documents,expected_release,expected_digest,qualified_actor),'UTF8')::jsonb;
 selected_history:=CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN 'truss-native-owned-create/0.1' ELSE 'truss-native-scalar-create/0.2' END;
 -- New writes belong to one native-issued outer operation.
 -- The leaf advances progress atomically.
 SELECT a.id,a.next_index,a.actor_oid,a.writer_xid,a.results,a.aliases INTO STRICT outer_attempt FROM truss.runtime_object_attempt a
 WHERE a.writer_xid=writer AND a.actor_oid=creation_leaf.actor_oid AND NOT a.complete
  AND a.context->'creationTransitionProfile'=creation_leaf.context->'creationTransitionProfile'
  AND a.documents_bytes=original_documents
  AND CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN
   a.results='[]'::jsonb AND a.aliases='[]'::jsonb AND
   (SELECT count(*) FROM truss.runtime_owned_operation p WHERE p.attempt_id=a.id AND p.result IS NOT NULL)=a.next_index
   ELSE jsonb_array_length(a.results)=a.next_index END
  AND ((selected_attempt IS NULL AND
   convert_to(jsonb_set(convert_from(a.input_bytes,'UTF8')::jsonb-'preconditions',
      '{operations}',jsonb_build_array(convert_from(a.input_bytes,'UTF8')::jsonb->'operations'->a.next_index))::text,'UTF8')=original_input
   AND convert_from(a.input_bytes,'UTF8')::jsonb->'operations'->a.next_index->>'operation'='create_object')
   -- The sole selected-path caller, runtime_owned_group_step_in_input,
   -- checked this attempt's exact input bytes immediately before invocation.
   -- Its intervening registered calls are read-only; retain all leaf scope,
   -- progress and original-operation reconstruction checks without detoasting
   -- the same complete batch a second time. NULL selectors keep the old path.
   OR (selected_attempt IS NOT NULL AND a.id=selected_attempt AND selected_original IS NOT NULL
    AND jsonb_extract_path(selected_input,'operations',a.next_index::text)->>'operation'='create_object'
    AND convert_to(((selected_input-ARRAY['preconditions','operations'])||jsonb_build_object('operations',
      jsonb_build_array(jsonb_extract_path(selected_input,'operations',a.next_index::text))))::text,'UTF8')=original_input))
  AND request='{"state":"none"}'::jsonb
 FOR UPDATE NOWAIT;
 LOCK TABLE truss.object IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 LOCK TABLE truss.edge IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  owned_plan:=truss.runtime_owned_plan(outer_attempt.id,outer_attempt.next_index);
  IF owned_plan->'operation' IS DISTINCT FROM input->'operations'->0
   OR owned_plan->>'primary' IS DISTINCT FROM 'create:'||outer_attempt.next_index::text
   OR (owned_plan->'beforeNodes') ? (owned_plan->>'primary') THEN
   RAISE EXCEPTION 'original ordered create plan required' USING ERRCODE='55000';END IF;
  owned_state:=owned_plan->'afterNodes'->(owned_plan->>'primary');root_reference:=owned_state->>'root';
  IF owned_state IS NULL OR owned_state->'deleted' IS DISTINCT FROM 'false'::jsonb THEN
   RAISE EXCEPTION 'original live create state required' USING ERRCODE='55000';END IF;
  IF root_reference IS NOT NULL THEN
   root_identity:=truss.runtime_owned_identity(outer_attempt.id,outer_attempt.next_index,root_reference,'object');
   SELECT * INTO STRICT root_object FROM truss.object WHERE id=(root_identity->>'id')::bigint AND type_id=(root_identity->>'typeId')::int;
   IF root_object.root_id IS NOT NULL OR root_object.root_type IS NOT NULL
    OR to_jsonb(root_object)-ARRAY['created_at','updated_at'] IS DISTINCT FROM
     truss.runtime_owned_object_image(outer_attempt.id,outer_attempt.next_index,root_reference,'before') THEN
    RAISE EXCEPTION 'original live rootless aggregate root state required' USING ERRCODE='55000';END IF;
  END IF;
 END IF;
 -- Modern creates are bounded by their admitted immutable outer attempt.
 -- Retain the published legacy transaction ceiling on its original profile.
 IF input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() THEN
 IF (SELECT count(*) FROM (SELECT 1 FROM truss.runtime_object_transition WHERE writer_xid=writer AND before_object IS NULL LIMIT 129) g)>=128 THEN
  RAISE EXCEPTION 'bounded groups per transaction required' USING ERRCODE='54000'; END IF;
 END IF;
 IF jsonb_typeof(key_inputs) IS DISTINCT FROM 'array' OR jsonb_array_length(key_inputs)>512 THEN
  RAISE EXCEPTION 'bounded original key inventory required' USING ERRCODE='54000'; END IF;
 IF (SELECT value FROM truss.setting WHERE key='key_reuse') IS DISTINCT FROM '"forbid"'::jsonb
 OR (SELECT value FROM truss.setting WHERE key='journal_mode') IS DISTINCT FROM '"engine"'::jsonb THEN
  RAISE EXCEPTION 'selected engine key/history settings required' USING ERRCODE='0A000'; END IF;
 -- Complete all logical plans before native IDs or canonical writes.
 FOR operation IN SELECT value FROM jsonb_array_elements(input->'operations') LOOP
  operation_meta:=metadata->current_index;
  SELECT * INTO STRICT selected_type FROM truss.type_def WHERE type_id=(operation_meta->>'typeId')::int;
  IF operation-ARRAY['operation','typeDefinitionPin','values','ownership','alias']<>'{}'::jsonb
   OR jsonb_typeof(operation->'values') IS DISTINCT FROM 'array' OR jsonb_array_length(operation->'values')>1024
   OR (operation ? 'alias' AND (jsonb_typeof(operation->'alias')<>'string' OR octet_length(operation->>'alias') NOT BETWEEN 1 AND 1024)) THEN
   RAISE EXCEPTION 'closed bounded create operation required' USING ERRCODE='22023'; END IF;
  IF EXISTS(SELECT 1 FROM truss.rel_endpoint e JOIN truss.rel_def r USING(rel_type_id)
   WHERE r.retired_rev IS NULL AND ((e.source_type=selected_type.type_id AND r.target_min>0)
    OR (e.target_type=selected_type.type_id AND r.source_min>0))) AND NOT EXISTS(
    SELECT 1 FROM truss.runtime_object_attempt a WHERE a.writer_xid=writer AND a.actor_oid=qualified_actor AND NOT a.complete
    AND convert_from(a.input_bytes,'UTF8')::jsonb->'operations'->a.next_index=operation
    AND a.documents_bytes=original_documents) THEN
   RAISE EXCEPTION 'mandatory relationship unsupported by create-only profile' USING ERRCODE='0A000'; END IF;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'values') v WHERE jsonb_typeof(v.value->'name') IS DISTINCT FROM 'string'
   OR octet_length(v.value->>'name') NOT BETWEEN 1 AND 4096 OR v.value-ARRAY['name','value']<>'{}'::jsonb
   OR truss.valid_flat_cell(v.value->'value') IS NOT TRUE)
   OR jsonb_array_length(operation->'values')<>(SELECT count(DISTINCT v.value->>'name') FROM jsonb_array_elements(operation->'values') v) THEN
   RAISE EXCEPTION 'unique exact scalar authored values required' USING ERRCODE='22023'; END IF;
  IF owned_state IS NOT NULL THEN
   -- Native capture already validated and canonicalized this immutable image.
   -- Retain source/actor/key checks and final settlement; do not replan values.
   props:=owned_state->'image'->'props';
   retained:=coalesce(nullif(owned_state->'image'->'retained','null'::jsonb),'{}'::jsonb);
  ELSE
  props:='{}';retained:='{}';
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=selected_type.type_id AND retired_rev IS NULL ORDER BY prop_id LOOP
   IF truss.valid_property_definition(property) IS NOT TRUE THEN
    RAISE EXCEPTION 'selected scalar property profile required' USING ERRCODE='0A000'; END IF;
   SELECT v.value->'value' INTO supplied_value FROM jsonb_array_elements(operation->'values') v WHERE v.value->>'name'=property.name;
   IF NOT FOUND THEN
    IF property.nullability='required' THEN RAISE EXCEPTION 'missing required value' USING ERRCODE='22023'; END IF;
   ELSE
    IF truss.valid_property_value(supplied_value,property) IS NOT TRUE THEN
     RAISE EXCEPTION 'exact property family and value required' USING ERRCODE='22023'; END IF;
    props:=props||jsonb_build_object(property.prop_id::text,truss.canonical_flat_cell(supplied_value));
   END IF;
  END LOOP;
  SELECT coalesce(jsonb_object_agg(v.value->>'name',truss.canonical_flat_cell(v.value->'value')),'{}'::jsonb) INTO retained
   FROM jsonb_array_elements(operation->'values') v WHERE NOT EXISTS(SELECT 1 FROM truss.prop_def p
    WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL AND p.name=v.value->>'name');
  END IF;
  planned:=planned||jsonb_build_array(jsonb_build_object('typeId',selected_type.type_id,'props',props,'retained',retained));
  FOR key_definition IN SELECT * FROM truss.key_def WHERE type_id=selected_type.type_id AND retired_rev IS NULL ORDER BY key_num LOOP
   values_text:=ARRAY[]::text[];values_cells:='[]';key_facets:='[]';
   FOR component IN SELECT p.* FROM unnest(key_definition.prop_ids) WITH ORDINALITY i(prop_id,ord)
    JOIN truss.prop_def p ON p.type_id=selected_type.type_id AND p.prop_id=i.prop_id ORDER BY i.ord LOOP
    IF component.scalar_type NOT IN ('string','integer','decimal','boolean','binary') OR component.nullability IS DISTINCT FROM 'required'
     OR component.retired_rev IS NOT NULL OR truss.valid_scalar_property(props->component.prop_id::text,component.scalar_type,false,component.facets) IS NOT TRUE THEN
     RAISE EXCEPTION 'required present exact key component required' USING ERRCODE='0A000'; END IF;
    values_cells:=values_cells||jsonb_build_array(props->component.prop_id::text);
    key_facets:=key_facets||jsonb_build_array(coalesce(component.facets,'{}'::jsonb));
   END LOOP;
   IF jsonb_array_length(values_cells)<>cardinality(key_definition.prop_ids) THEN RAISE EXCEPTION 'complete key components required' USING ERRCODE='55000'; END IF;
   tuple_bytes:=truss.derive_catalog_key_tuple(selected_type.type_id,key_definition.key_num,values_cells);
   SELECT * INTO STRICT source_pin FROM truss.runtime_definition('key',selected_type.type_id,key_definition.key_num);
   namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected_type.type_id::text,'keyNumber',key_definition.key_num::text,
    'definitionPin',source_pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');
   planned_keys:=planned_keys||jsonb_build_array(jsonb_build_object('operationIndex',current_index,'typeId',selected_type.type_id,
    'keyNumber',key_definition.key_num,'namespace',encode(namespace,'hex'),'transport',encode(transport,'hex'),
    'tupleHex',encode(tuple_bytes,'hex')));
  END LOOP;
  current_index:=current_index+1;
 END LOOP;
 IF jsonb_array_length(planned_keys)<>(SELECT count(DISTINCT (k.value->>'namespace',k.value->>'transport')) FROM jsonb_array_elements(planned_keys) k)
  OR (SELECT count(*) FROM jsonb_array_elements(input->'operations') o WHERE o.value ? 'alias')
   <>(SELECT count(DISTINCT o.value->>'alias') FROM jsonb_array_elements(input->'operations') o WHERE o.value ? 'alias') THEN
  RAISE EXCEPTION 'unique complete group keys and aliases required' USING ERRCODE='22023'; END IF;
 -- Canonical route order precedes all canonical object creation.
 FOR route IN SELECT k.value FROM jsonb_array_elements(planned_keys) k
  ORDER BY sha256(decode(k.value->>'namespace','hex')),sha256(decode(k.value->>'transport','hex')),
   decode(k.value->>'namespace','hex'),decode(k.value->>'transport','hex') LOOP
  current_index:=(route.value->>'operationIndex')::int;
  SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(decode(route.value->>'namespace','hex'),decode(route.value->>'transport','hex'));
  planned_keys:=jsonb_set(planned_keys,ARRAY[(SELECT (k.ordinality-1)::text FROM jsonb_array_elements(planned_keys) WITH ORDINALITY k(value,ordinality) WHERE k.value=route.value),'priorGeneration'],to_jsonb(observed.generation));
  IF cardinality(observed.member_ids)>0 OR cardinality(observed.reservation_ids)>0 THEN
   RAISE EXCEPTION 'key already allocated or reserved' USING ERRCODE='23505'; END IF;
 END LOOP;
 current_index:=0;
 FOR operation IN SELECT value FROM jsonb_array_elements(input->'operations') LOOP
  operation_meta:=metadata->current_index;key_plan:=planned->current_index;
  SELECT * INTO STRICT selected_type FROM truss.type_def WHERE type_id=(operation_meta->>'typeId')::int;
  object_row.id:=nextval('truss.id_seq');object_row.type_id:=selected_type.type_id;
  IF object_row.id<=0 THEN RAISE EXCEPTION 'positive native object id required' USING ERRCODE='54000'; END IF;
  object_row.props:=key_plan->'props';object_row.retained:=NULLIF(key_plan->'retained','{}'::jsonb);
  object_row.root_id:=(root_identity->>'id')::bigint;object_row.root_type:=(root_identity->>'typeId')::int;
  object_row.rev:=captured_revision;object_row.ver:=1;
  IF owned_state IS NOT NULL AND
   ((owned_state->'image')-ARRAY['id','created_at','updated_at']) IS DISTINCT FROM
   (to_jsonb(object_row)-ARRAY['id','root_id','root_type','created_at','updated_at']) THEN
   RAISE EXCEPTION 'original planned create values required' USING ERRCODE='55000';END IF;
  object_row.created_at:=clock_timestamp();object_row.updated_at:=object_row.created_at;
  planned_row:=to_jsonb(object_row);
  INSERT INTO truss.object SELECT (object_row).* RETURNING to_jsonb(object) INTO actual_row;
  IF actual_row IS DISTINCT FROM planned_row THEN RAISE EXCEPTION 'exact object insert required' USING ERRCODE='55000'; END IF;
  member_keys:='[]';
  FOR key_plan IN SELECT k.value FROM jsonb_array_elements(planned_keys) k WHERE k.value->>'operationIndex'=current_index::text
   ORDER BY (k.value->>'keyNumber')::int LOOP
   namespace:=decode(key_plan->>'namespace','hex');transport:=decode(key_plan->>'transport','hex');tuple_bytes:=decode(key_plan->>'tupleHex','hex');
   IF NOT truss.verify_object_string_key(object_row.id,object_row.type_id,(key_plan->>'keyNumber')::smallint,tuple_bytes) THEN
    RAISE EXCEPTION 'stored key values disagree' USING ERRCODE='55000'; END IF;
   membership.storage_row_id:=nextval('truss.key_storage_row_seq');membership.type_id:=object_row.type_id;
   membership.key_num:=(key_plan->>'keyNumber')::smallint;membership.object_id:=object_row.id;
   membership.namespace_bytes:=namespace;membership.key_bytes:=transport;
   membership.original_context_bytes:=convert_to(jsonb_build_object('profile','truss-created-key-context/0.2',
    'groupId',group_uuid::text,'sourceEpoch',installation.source_epoch::text,'xid',writer::text,
    'actorOid',actor_oid::text,'actor',session_user::text,'operationIndex',current_index::text,
    'derivation','postgresql-umf-key-tuple-v1')::text,'UTF8');
   membership.namespace_sha256:=sha256(namespace);membership.key_sha256:=sha256(transport);
   planned_row:=to_jsonb(membership);
   INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
    VALUES(membership.storage_row_id,membership.type_id,membership.key_num,membership.object_id,namespace,transport,membership.original_context_bytes)
    RETURNING to_jsonb(object_key_bucket) INTO actual_row;
   IF actual_row IS DISTINCT FROM planned_row THEN RAISE EXCEPTION 'exact key membership insert required' USING ERRCODE='55000'; END IF;
   reservation.storage_row_id:=nextval('truss.key_storage_row_seq');reservation.namespace_bytes:=namespace;reservation.key_bytes:=transport;
   reservation.original_reservation_bytes:=convert_to(jsonb_build_object('profile','truss-created-key-reservation/0.1',
    'groupId',group_uuid::text,'sourceEpoch',installation.source_epoch::text,'xid',writer::text,'objectId',object_row.id::text,
    'typeId',object_row.type_id::text,'keyNumber',membership.key_num::text,'contextBase64',replace(encode(membership.original_context_bytes,'base64'),chr(10),''))::text,'UTF8');
   reservation.namespace_sha256:=sha256(namespace);reservation.key_sha256:=sha256(transport);
   planned_row:=to_jsonb(reservation);
   INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes)
    VALUES(reservation.storage_row_id,namespace,transport,reservation.original_reservation_bytes) RETURNING to_jsonb(object_key_reservation_bucket) INTO actual_row;
   IF actual_row IS DISTINCT FROM planned_row THEN RAISE EXCEPTION 'exact persistent key reservation required' USING ERRCODE='55000'; END IF;
   UPDATE truss.key_bucket_guard SET generation=generation+1 WHERE namespace_sha256=sha256(namespace) AND key_sha256=sha256(transport)
    RETURNING generation INTO new_generation;
   IF NOT FOUND OR new_generation IS DISTINCT FROM (key_plan->>'priorGeneration')::bigint+1 THEN RAISE EXCEPTION 'actual key generation advance required' USING ERRCODE='55000'; END IF;
   member_keys:=member_keys||jsonb_build_array(jsonb_build_object('membership',to_jsonb(membership),'reservation',to_jsonb(reservation),'generation',new_generation));
  END LOOP;
  object_identity:=jsonb_build_object('id',object_row.id::text,'typeId',object_row.type_id::text,'definitionPin',operation->>'typeDefinitionPin',
   'owner',jsonb_build_object('documentId',selected_type.document_id,'moduleId',selected_type.module));
  after_record:=truss.runtime_object_history(to_jsonb(object_row),object_identity);
  journal_row.seq:=nextval('truss.journal_seq');journal_row.at:=clock_timestamp();journal_row.xid:=writer;
  journal_row.entity_kind:='o';journal_row.entity_id:=object_row.id;journal_row.entity_type:=object_row.type_id;
  journal_row.ver:=1;journal_row.op:='create';journal_row.prop_id:=NULL;journal_row.old_value:=NULL;journal_row.rev:=captured_revision;
  event:=jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile',selected_history,'xid',writer::text,'seq',journal_row.seq::text,'identity',object_identity,
   'eventVersion','1','eventCatalogRevision',captured_revision::text,'operation','create','after',after_record,
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text));
  event_digest:=encode(sha256(convert_to(jsonb_build_array(event)::text,'UTF8')),'hex');
  event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount','1','orderedEventDigest',event_digest));
  event_bytes:=convert_to(event::text,'UTF8');origin_bytes:=convert_to((event->'origin')::text,'UTF8');
  journal_row.new_value:=truss.runtime_exact_wrapper('event',event_bytes);journal_row.origin:=truss.runtime_exact_wrapper('origin',origin_bytes);
  expected_journal:=to_jsonb(journal_row);
  INSERT INTO truss.journal SELECT (journal_row).* RETURNING to_jsonb(journal) INTO actual_journal;
  IF actual_journal IS DISTINCT FROM expected_journal THEN RAISE EXCEPTION 'exact complete journal append required' USING ERRCODE='55000'; END IF;
  members:=members||jsonb_build_array(jsonb_build_object('object',to_jsonb(object_row),'keys',member_keys,'journal',expected_journal));
  outcome:=jsonb_build_object('operation','create_object','outcome','created','identity',object_identity,'version','1',
   'events',jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile',selected_history,
    'xid',writer::text,'seq',journal_row.seq::text)));
  IF operation ? 'alias' THEN outcome:=outcome||jsonb_build_object('alias',operation->>'alias');
   aliases:=aliases||jsonb_build_array(jsonb_build_object('alias',operation->>'alias','identity',object_identity)); END IF;
  results:=results||jsonb_build_array(outcome);current_index:=current_index+1;
 END LOOP;
 semantic:=jsonb_build_object('interfaceVersion','truss-group-result/0.1.0','executedCatalogRevision',captured_revision::text,
  'layoutProfile',input->'layoutProfile','mutationProfile',input->'mutationProfile','results',results,'aliases',aliases);
 semantic_bytes:=convert_to(semantic::text,'UTF8');
 IF octet_length(semantic_bytes)>16777216 THEN RAISE EXCEPTION 'bounded group result required' USING ERRCODE='54000'; END IF;
 IF jsonb_array_length(members)<>1 THEN RAISE EXCEPTION 'one original inner create member required' USING ERRCODE='55000';END IF;
 expected_transition:=jsonb_build_object('attempt_id',outer_attempt.id,'operation_index',outer_attempt.next_index,
  'writer_xid',writer::text,'object_id',(members->0->'object'->>'id')::bigint,
  'type_id',(members->0->'object'->>'type_id')::int,'before_object',NULL,'after_object',members->0->'object',
  'after_keys',(SELECT coalesce(jsonb_agg(k.value->'membership' ORDER BY (k.value->'membership'->>'key_num')::int),'[]'::jsonb)
   FROM jsonb_array_elements(members->0->'keys') k),'journal',jsonb_build_array(members->0->'journal'));
 INSERT INTO truss.runtime_object_transition(attempt_id,operation_index,writer_xid,object_id,type_id,before_object,after_object,after_keys,journal)
 SELECT r.attempt_id,r.operation_index,r.writer_xid,r.object_id,r.type_id,r.before_object,r.after_object,r.after_keys,r.journal
 FROM jsonb_populate_record(NULL::truss.runtime_object_transition,expected_transition) r
 RETURNING to_jsonb(runtime_object_transition)-'transition_id' INTO actual_transition;
 IF actual_transition IS DISTINCT FROM expected_transition THEN
  RAISE EXCEPTION 'exact atomic create transition insert required' USING ERRCODE='55000';END IF;
 IF input->'mutationProfile'=truss.runtime_owned_profile() THEN
  UPDATE truss.runtime_owned_operation p SET result=semantic->'results'->0
   WHERE p.attempt_id=outer_attempt.id AND p.operation_index=outer_attempt.next_index
    AND p.writer_xid=writer AND p.plan->'operation'=input->'operations'->0 AND p.result IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'one original create result slot required' USING ERRCODE='55000';END IF;
  SELECT p.result INTO STRICT stored_result FROM truss.runtime_owned_operation p
   WHERE p.attempt_id=outer_attempt.id AND p.operation_index=outer_attempt.next_index;
  IF stored_result IS DISTINCT FROM semantic->'results'->0 THEN
   RAISE EXCEPTION 'exact sealed create result required' USING ERRCODE='55000';END IF;
  UPDATE truss.runtime_object_attempt a SET next_index=a.next_index+1
   WHERE a.id=outer_attempt.id AND a.next_index=outer_attempt.next_index AND NOT a.complete
    AND a.actor_oid=creation_leaf.actor_oid AND a.writer_xid=writer AND a.results='[]'::jsonb AND a.aliases='[]'::jsonb;
 ELSE
 UPDATE truss.runtime_object_attempt a SET next_index=a.next_index+1,
  results=a.results||jsonb_build_array(results_of_create.value),aliases=a.aliases||(semantic->'aliases')
 FROM (SELECT semantic->'results'->0 AS value) results_of_create
 WHERE a.id=outer_attempt.id AND a.next_index=outer_attempt.next_index AND NOT a.complete;
 -- Read the stored row once below; an UPDATE RETURNING image here would be
 -- immediately overwritten and repeatedly copy the growing complete result.
 END IF;
 IF NOT FOUND THEN RAISE EXCEPTION 'one atomic outer create progress required' USING ERRCODE='55000';END IF;
 SELECT a.actor_oid,a.writer_xid,a.next_index,a.results,a.aliases,a.complete INTO actual_progress
 FROM truss.runtime_object_attempt a WHERE a.id=outer_attempt.id;
 SELECT to_jsonb(t)-'transition_id' INTO STRICT actual_transition FROM truss.runtime_object_transition t
 WHERE t.attempt_id=outer_attempt.id AND t.operation_index=outer_attempt.next_index;
 IF actual_transition IS DISTINCT FROM expected_transition THEN
  RAISE EXCEPTION 'exact stored atomic create transition required' USING ERRCODE='55000';END IF;
 IF ROW(actual_progress.actor_oid,actual_progress.writer_xid,actual_progress.next_index,
  actual_progress.results,actual_progress.aliases,actual_progress.complete) IS DISTINCT FROM
  ROW(outer_attempt.actor_oid,outer_attempt.writer_xid,outer_attempt.next_index+1,
   CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN '[]'::jsonb
    ELSE outer_attempt.results||jsonb_build_array(semantic->'results'->0) END,
   CASE WHEN input->'mutationProfile'=truss.runtime_owned_profile() THEN '[]'::jsonb
    ELSE outer_attempt.aliases||(semantic->'aliases') END,false) THEN
  RAISE EXCEPTION 'exact atomic outer create progress required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(j.row ORDER BY j.seq),'[]'::jsonb) INTO physical_journal FROM
  (SELECT to_jsonb(j) AS row,j.seq FROM truss.journal j WHERE j.entity_kind='o'
   AND j.entity_id=object_row.id AND j.entity_type=object_row.type_id AND j.xid=writer AND j.ver=1
   ORDER BY j.seq LIMIT 2) j;
 IF jsonb_array_length(physical_journal)>1 THEN
  RAISE EXCEPTION 'whole history group exceeds event limit' USING ERRCODE='54000';END IF;
 IF physical_journal IS DISTINCT FROM jsonb_build_array(expected_journal) THEN
  RAISE EXCEPTION 'exact physical atomic create journal required' USING ERRCODE='55000';END IF;
 FOR key_plan IN SELECT value FROM jsonb_array_elements(member_keys) LOOP
  SELECT coalesce(jsonb_agg(r.row),'[]'::jsonb) INTO actual_row FROM
   (SELECT to_jsonb(r) AS row FROM truss.object_key_reservation_bucket r
    WHERE r.namespace_sha256=decode(substring(key_plan->'membership'->>'namespace_sha256' FROM 3),'hex')
     AND r.key_sha256=decode(substring(key_plan->'membership'->>'key_sha256' FROM 3),'hex')
     AND r.namespace_bytes=decode(substring(key_plan->'membership'->>'namespace_bytes' FROM 3),'hex')
     AND r.key_bytes=decode(substring(key_plan->'membership'->>'key_bytes' FROM 3),'hex') LIMIT 2) r;
  IF actual_row IS DISTINCT FROM jsonb_build_array(key_plan->'reservation') THEN
   RAISE EXCEPTION 'exact retained create key reservation required' USING ERRCODE='55000';END IF;
 END LOOP;
 -- The owned leaf has checked exact native object, key, reservation, journal
 -- and transition writes. Full semantic reconstruction remains at group finish
 -- and mandatory attempt settlement; legacy creation retains its leaf check.
 IF input->'mutationProfile' IS DISTINCT FROM truss.runtime_owned_profile() THEN
  PERFORM truss.runtime_create_transition_validate_qualified((SELECT transition_id FROM truss.runtime_object_transition WHERE attempt_id=outer_attempt.id AND operation_index=outer_attempt.next_index AND before_object IS NULL),qualified_actor);
 END IF;
 FOR operation_meta IN SELECT value FROM jsonb_array_elements(metadata) LOOP
  IF truss.runtime_module_writer_qualified(operation_meta->>'documentId',operation_meta->>'moduleId',qualified_actor) IS DISTINCT FROM outer_attempt.actor_oid THEN
   RAISE EXCEPTION 'original current create actor required' USING ERRCODE='42501';END IF;
  IF NOT truss.runtime_object_values_readable_qualified((operation_meta->>'typeId')::int,qualified_actor) THEN RAISE EXCEPTION 'current property and item interpretation reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF root_identity IS NOT NULL AND NOT truss.runtime_can_read_qualified(root_identity->'owner'->>'documentId',root_identity->'owner'->>'moduleId',qualified_actor) THEN
  RAISE EXCEPTION 'current create root reader required' USING ERRCODE='42501';END IF;
 RETURN convert_to(jsonb_build_object('outcome','success','disposition','applied','durability','pending','semantic',semantic)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.apply_create_group_qualified(bytea,bytea,bytea,bytea,text,text,oid,uuid,bytea,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.apply_create_group(original_input bytea,original_documents bytea,original_keys bytea,original_request bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 RETURN truss.apply_create_group_qualified(original_input,original_documents,original_keys,original_request,expected_release,expected_digest,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.apply_create_group(bytea,bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.group_type_reference(selected_document text,selected_module text,selected_record text,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE context jsonb;person oid;policy truss.module_access%ROWTYPE;selected_type truss.type_def%ROWTYPE;source_pin record;
BEGIN
 context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;
 IF selected_document IS NULL OR selected_module IS NULL OR selected_record IS NULL
 OR octet_length(selected_document) NOT BETWEEN 1 AND 4096 OR octet_length(selected_module) NOT BETWEEN 1 AND 4096
 OR octet_length(selected_record) NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'bounded qualified type selection required' USING ERRCODE='22023'; END IF;
 person:=truss.runtime_person(false);
 SELECT * INTO policy FROM truss.module_access WHERE document_id=selected_document AND module=selected_module FOR SHARE NOWAIT;
 IF NOT FOUND OR NOT EXISTS(WITH RECURSIVE memberships(role_oid) AS (
  SELECT person UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
  SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid WHERE r.rolname::text IN(policy.reader_role,policy.writer_role)) THEN RETURN NULL; END IF;
 SELECT * INTO selected_type FROM truss.type_def WHERE document_id=selected_document AND module=selected_module
  AND element=selected_record AND kind='record' AND retired_rev IS NULL AND NOT provisional;
 IF NOT FOUND THEN RETURN NULL; END IF;
 SELECT * INTO STRICT source_pin FROM truss.runtime_definition('type',selected_type.type_id);
 person:=truss.runtime_person(false);
 IF NOT EXISTS(WITH RECURSIVE memberships(role_oid) AS (
  SELECT person UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
  SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid WHERE r.rolname::text IN(policy.reader_role,policy.writer_role)) THEN RETURN NULL; END IF;
 RETURN convert_to(jsonb_build_object('kind','type','definitionPin',source_pin.definition_pin,'typeId',selected_type.type_id::text,
  'authoredIdentity',selected_type.element,'owner',jsonb_build_object('documentId',selected_document,'moduleId',selected_module))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.group_type_reference(text,text,text,text,text) FROM PUBLIC;

CREATE FUNCTION truss.prepare_group(original_records bytea,original_relationships bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE context jsonb;records jsonb;relationships jsonb;entry jsonb;reference bytea;types jsonb:='[]';rels jsonb:='[]';revision int;
BEGIN
 IF original_records IS NULL OR octet_length(original_records) NOT BETWEEN 2 AND 65536
  OR original_relationships IS NULL OR octet_length(original_relationships) NOT BETWEEN 2 AND 65536 THEN
  RAISE EXCEPTION 'bounded group preparation required' USING ERRCODE='54000';END IF;
 IF (convert_from(original_records,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE
  OR (convert_from(original_relationships,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'unique original JSON members required' USING ERRCODE='22023';END IF;
 records:=convert_from(original_records,'UTF8')::jsonb;relationships:=convert_from(original_relationships,'UTF8')::jsonb;
 IF jsonb_array_length(records) NOT BETWEEN 0 AND 128 OR jsonb_array_length(relationships) NOT BETWEEN 0 AND 128 THEN
  RAISE EXCEPTION 'bounded named record set required' USING ERRCODE='54000';END IF;
 context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;
 SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 FOR entry IN SELECT value FROM jsonb_array_elements(records) LOOP
  IF jsonb_typeof(entry) IS DISTINCT FROM 'object' OR entry-ARRAY['documentId','moduleId','recordId']<>'{}'::jsonb
   OR jsonb_typeof(entry->'documentId') IS DISTINCT FROM 'string' OR jsonb_typeof(entry->'moduleId') IS DISTINCT FROM 'string'
   OR jsonb_typeof(entry->'recordId') IS DISTINCT FROM 'string' THEN
   RAISE EXCEPTION 'qualified record name required' USING ERRCODE='22023';END IF;
  reference:=truss.group_type_reference(entry->>'documentId',entry->>'moduleId',entry->>'recordId',expected_release,expected_digest);
  types:=types||jsonb_build_array(CASE WHEN reference IS NULL THEN 'null'::jsonb ELSE convert_from(reference,'UTF8')::jsonb END);
 END LOOP;
 FOR entry IN SELECT value FROM jsonb_array_elements(relationships) LOOP
  IF jsonb_typeof(entry) IS DISTINCT FROM 'object' OR entry-ARRAY['documentId','moduleId','relationshipId']<>'{}'::jsonb
   OR jsonb_typeof(entry->'documentId') IS DISTINCT FROM 'string' OR jsonb_typeof(entry->'moduleId') IS DISTINCT FROM 'string'
   OR jsonb_typeof(entry->'relationshipId') IS DISTINCT FROM 'string' THEN
   RAISE EXCEPTION 'qualified relationship name required' USING ERRCODE='22023';END IF;
  reference:=truss.group_relationship_reference(entry->>'documentId',entry->>'moduleId',entry->>'relationshipId',expected_release,expected_digest);
  rels:=rels||jsonb_build_array(CASE WHEN reference IS NULL THEN 'null'::jsonb ELSE convert_from(reference,'UTF8')::jsonb END);
 END LOOP;
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM revision THEN
  RAISE EXCEPTION 'catalog changed during group preparation' USING ERRCODE='55P03';END IF;
 RETURN convert_to(jsonb_build_object('catalogRevision',revision::text,'context',context,'types',types,'relationships',rels)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.prepare_group(bytea,bytea,text,text) FROM PUBLIC;
