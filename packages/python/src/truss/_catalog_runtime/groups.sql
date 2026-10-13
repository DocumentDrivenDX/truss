-- Connected rootless scalar-string create group runtime. Feed stays unavailable.
ALTER TABLE truss.catalog_runtime_installation ADD COLUMN source_epoch uuid NOT NULL DEFAULT pg_catalog.gen_random_uuid();

-- Match the existing original-definition pin recipe without reserializing source.
CREATE FUNCTION truss.runtime_definition(selected_kind text,selected_type int,selected_number int DEFAULT NULL,historical_revision int DEFAULT NULL)
RETURNS TABLE(definition_pin text,original_fragment bytea,original_pointer text,document_id text,module_id text,element_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE basis jsonb;definition jsonb; archive truss.schema_doc%ROWTYPE; native_type truss.type_def%ROWTYPE;
 source_module text;source_element text;module_json json;module_index int;element_json json;element_index int;
 key_json json;key_index int;fragment json;pointer text;pin_input text;
BEGIN
 IF historical_revision IS NULL THEN
  SELECT * INTO STRICT native_type FROM truss.type_def WHERE type_id=selected_type AND NOT provisional AND retired_rev IS NULL;
 ELSE
  basis:=truss.catalog_all_expected_records(historical_revision);
  SELECT * INTO STRICT native_type FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t WHERE t.type_id=selected_type;
 END IF;
 IF selected_kind='type' THEN
  definition:=to_jsonb(native_type);source_module:=native_type.module;source_element:=native_type.element;
 ELSIF selected_kind='property' THEN
  IF historical_revision IS NULL THEN
   SELECT to_jsonb(p),p.declaration_module,p.element INTO STRICT definition,source_module,source_element FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=selected_number AND p.retired_rev IS NULL;
  ELSE
   SELECT to_jsonb(p),p.declaration_module,p.element INTO STRICT definition,source_module,source_element FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.type_id=selected_type AND p.prop_id=selected_number;
  END IF;
 ELSIF selected_kind='key' THEN
  IF historical_revision IS NULL THEN
   SELECT to_jsonb(k) INTO STRICT definition FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_num=selected_number AND k.retired_rev IS NULL;
  ELSE
   SELECT to_jsonb(k) INTO STRICT definition FROM jsonb_populate_recordset(NULL::truss.key_def,basis->'key_def') k WHERE k.type_id=selected_type AND k.key_num=selected_number;
  END IF;
  source_module:=native_type.module;source_element:=native_type.element;
 ELSE RAISE EXCEPTION 'supported definition kind required' USING ERRCODE='22023'; END IF;
 IF definition->>'definition_source_kind'<>'accepted_document' OR (definition->>'definition_rev')::int<1 THEN
  RAISE EXCEPTION 'original accepted definition source required' USING ERRCODE='0A000'; END IF;
 SELECT * INTO STRICT archive FROM truss.schema_doc d WHERE d.rev=(definition->>'definition_rev')::int AND d.ord=(definition->>'definition_doc_ord')::int
  AND d.doc_id=definition->>'definition_document_id';
 SELECT m.value,m.ordinality::int-1 INTO STRICT module_json,module_index
  FROM json_array_elements(archive.document::json->'modules') WITH ORDINALITY m WHERE m.value->>'id'=source_module;
 SELECT e.value,e.ordinality::int-1 INTO STRICT element_json,element_index
  FROM json_array_elements(module_json->'elements') WITH ORDINALITY e WHERE e.value->>'id'=source_element;
 fragment:=element_json;pointer:='/modules/'||module_index||'/elements/'||element_index;
 IF selected_kind='key' THEN
  SELECT k.value,k.ordinality::int-1 INTO STRICT key_json,key_index
   FROM json_array_elements(element_json->'keys') WITH ORDINALITY k WHERE k.value->>'id'=definition->>'key_id';
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
REVOKE ALL ON FUNCTION truss.runtime_definition(text,int,int,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_group_profiles() RETURNS jsonb LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ SELECT jsonb_build_object(
'mutationProfile',jsonb_build_object('identity','truss-rootless-scalar-graph','version','0.2','sha256','e2b24e52e1b374245d728db33ab34c63f6bea983e986064a4a444286d9d3c9b0'),
'valueProfile',jsonb_build_object('identity','truss-scalar-string-values','version','0.2','sha256','5e6a7f879e17066a8ffdeb8731da89906f0e5cb231e4b4357bd4fbea0158163f'),
'canonicalizationProfile',jsonb_build_object('identity','truss-pg18-jsonb-text','version','0.1','sha256','e5eec0aa3dfd5195250bb2e781626c6229f645d71a5c21095ee3d10008aadc97'),
'requestFingerprintProfile',jsonb_build_object('identity','truss-python-create-request-bytes','version','0.1','sha256','69974e716b09892428ce6f3fe5c4b01825bad35104b25dcd861152da60965baa'),
'adapterProfile',jsonb_build_object('identity','truss-psycopg-create-provider','version','0.1','sha256','f20735a94e87213d77f713cbbabd2bdf2e4f2b459041c53bb984f5b706112ba9'),
'positionProfile',jsonb_build_object('identity','truss-authority-receipt-visibility','version','0.1','sha256','97d54f46af687510fd3ae10aaa37c761d17d6b371d12171ea15a0d402b8855e9'),
'policyProfile',jsonb_build_object('identity','truss-qualified-module-writer','version','0.1','sha256','398cee9241e057bb95c415a165b1812ac689433eaac2684c70a15084e681b88b')); $$;
REVOKE ALL ON FUNCTION truss.runtime_group_profiles() FROM PUBLIC;

CREATE FUNCTION truss.runtime_module_writer(selected_document text,selected_module text) RETURNS oid
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE person oid;policy truss.module_access%ROWTYPE;
BEGIN
 person:=truss.runtime_person(false);
 SELECT * INTO policy FROM truss.module_access WHERE document_id=selected_document AND module=selected_module FOR SHARE NOWAIT;
 IF NOT FOUND OR NOT EXISTS(WITH RECURSIVE memberships(role_oid) AS (
  SELECT person UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
  SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid WHERE r.rolname::text=policy.writer_role) THEN
  RAISE EXCEPTION 'current qualified module writer required' USING ERRCODE='42501'; END IF;
 RETURN person;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_module_writer(text,text) FROM PUBLIC;

CREATE FUNCTION truss.group_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE person oid;installation truss.catalog_runtime_installation%ROWTYPE;revision int;
BEGIN
 person:=truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected installed group runtime required' USING ERRCODE='0A000'; END IF;
 SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 IF revision<1 THEN RAISE EXCEPTION 'accepted catalog required' USING ERRCODE='0A000'; END IF;
 RETURN convert_to((truss.runtime_group_profiles()||jsonb_build_object('layoutProfile',installation.layout_profile,
  'authorizedScopeIdentity','truss-person:'||installation.installation_id||':'||person::text,
  'installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-scalar-create/0.2'))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.group_context(text,text) FROM PUBLIC;

-- Resolve only requested, currently writable definitions. Original whole documents
-- are caller-supplied, independently compared in full to the retained archive.
CREATE FUNCTION truss.group_create_metadata(original_input bytea,original_documents bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE input jsonb;documents jsonb;operation jsonb;context jsonb;selected_type truss.type_def%ROWTYPE;
 source_pin record;archive truss.schema_doc%ROWTYPE;metadata jsonb:='[]';counted int:=0;source_text text;
BEGIN
 context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;
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
  IF operation->>'operation' IS DISTINCT FROM 'create_object' OR operation->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb THEN
   RAISE EXCEPTION 'rootless creates only in selected group profile' USING ERRCODE='0A000'; END IF;
  SELECT t.* INTO STRICT selected_type FROM truss.type_def t CROSS JOIN LATERAL truss.runtime_definition('type',t.type_id) p
   WHERE t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL AND p.definition_pin=operation->>'typeDefinitionPin';
  PERFORM truss.runtime_module_writer(selected_type.document_id,selected_type.module);
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
 IF EXISTS(SELECT 1 FROM truss.runtime_object_transition WHERE object_id=selected_id AND type_id=selected_type AND writer_xid=pg_current_xact_id()) THEN
  PERFORM truss.runtime_object_validate(selected_id,selected_type);
  SELECT to_jsonb(j) INTO actual_journal FROM truss.journal j WHERE j.at=(expected->'journal'->>'at')::timestamptz AND j.seq=(expected->'journal'->>'seq')::bigint;
  IF actual_journal IS DISTINCT FROM expected->'journal' THEN RAISE EXCEPTION 'original creation journal required' USING ERRCODE='55000';END IF;
  FOR key_expected IN SELECT value FROM jsonb_array_elements(expected->'keys') LOOP
   SELECT to_jsonb(r) INTO actual_reservation FROM truss.object_key_reservation_bucket r WHERE storage_row_id=(key_expected->'reservation'->>'storage_row_id')::bigint;
   IF actual_reservation IS DISTINCT FROM key_expected->'reservation' THEN RAISE EXCEPTION 'original creation reservation required' USING ERRCODE='55000';END IF;
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
 IF (SELECT coalesce(jsonb_agg(to_jsonb(j) ORDER BY j.at,j.seq),'[]'::jsonb)
     FROM truss.journal j WHERE j.xid=group_row.writer_xid)
 IS DISTINCT FROM (SELECT coalesce(jsonb_agg(e.value ORDER BY (e.value->>'at')::timestamptz,(e.value->>'seq')::bigint),'[]'::jsonb) FROM (
     SELECT e.value->'journal' AS value FROM truss.runtime_create_group g CROSS JOIN LATERAL jsonb_array_elements(g.expected_members) e(value) WHERE g.writer_xid=group_row.writer_xid
     UNION ALL SELECT j.value FROM truss.runtime_object_transition t CROSS JOIN LATERAL jsonb_array_elements(t.journal) j WHERE t.writer_xid=group_row.writer_xid
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
 IF TG_TABLE_NAME='object' THEN PERFORM truss.runtime_create_validate_member(NEW.id,NEW.type_id);
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

CREATE FUNCTION truss.apply_create_group(original_input bytea,original_documents bytea,original_keys bytea,original_request bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE input jsonb;request jsonb;key_inputs jsonb;metadata jsonb;context jsonb;installation truss.catalog_runtime_installation%ROWTYPE;
 source_pin record;actor_oid oid;writer xid8;group_uuid uuid:=gen_random_uuid();current_index int:=0;operation jsonb;operation_meta jsonb;
 selected_type truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;key_definition truss.key_def%ROWTYPE;
 supplied_value jsonb;props jsonb;retained jsonb;planned jsonb:='[]';planned_keys jsonb:='[]';key_plan jsonb;key_input jsonb;
 values_text text[];values_cells jsonb;key_facets jsonb;component record;namespace bytea;transport bytea;tuple_bytes bytea;owner_receipt jsonb;
 route record;observed record;planned_row jsonb;actual_row jsonb;object_row truss.object%ROWTYPE;
 object_identity jsonb;properties_json jsonb;retained_json jsonb;after_record jsonb;event jsonb;event_bytes bytea;origin_bytes bytea;
 journal_row truss.journal%ROWTYPE;expected_journal jsonb;actual_journal jsonb;event_digest text;
 results jsonb:='[]';aliases jsonb:='[]';members jsonb:='[]';member_keys jsonb;
 membership truss.object_key_bucket%ROWTYPE;reservation truss.object_key_reservation_bucket%ROWTYPE;
 receipt truss.request_receipt%ROWTYPE;existing truss.request_receipt%ROWTYPE;receipt_json jsonb;receipt_bytes bytea;
 semantic jsonb;semantic_bytes bytea;observation_bytes bytea;request_namespace bytea;request_bytes bytea;request_route bigint;new_generation bigint;
 captured_revision int;old_request_generation bigint;intended_group truss.runtime_create_group%ROWTYPE;scope_identity text;outcome jsonb;native_state text;candidate_count int;
BEGIN
 -- Metadata locks head and every requested policy, then revalidates full sources.
 metadata:=convert_from(truss.group_create_metadata(original_input,original_documents,expected_release,expected_digest),'UTF8')::jsonb;
 context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;
 actor_oid:=truss.runtime_person(false);writer:=pg_current_xact_id();
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF original_keys IS NULL OR octet_length(original_keys) NOT BETWEEN 1 AND 8388608
 OR original_request IS NULL OR octet_length(original_request) NOT BETWEEN 1 AND 65536 THEN
  RAISE EXCEPTION 'bounded group keys and request required' USING ERRCODE='54000'; END IF;
 IF (convert_from(original_keys,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE OR (convert_from(original_request,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'unique key/request JSON members required' USING ERRCODE='22023'; END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;request:=convert_from(original_request,'UTF8')::jsonb;
 key_inputs:=convert_from(original_keys,'UTF8')::jsonb;scope_identity:=context->>'authorizedScopeIdentity';
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
 IF request<>'{"state":"none"}'::jsonb THEN
  IF request->>'state' IS DISTINCT FROM 'present' OR request-ARRAY['state','identity']<>'{}'::jsonb
   OR request->'identity'->>'authorizedScopeIdentity' IS DISTINCT FROM scope_identity
   OR request->'identity'->>'inputProfile' IS DISTINCT FROM 'truss-group-input/0.1.0'
   OR request->'identity'->>'interfaceVersion' IS DISTINCT FROM 'truss-request-identity/0.1.0'
   OR jsonb_typeof(request->'identity'->'requestId') IS DISTINCT FROM 'string'
   OR octet_length(request->'identity'->>'requestId') NOT BETWEEN 1 AND 1024
   OR (request->'identity')-ARRAY['authorizedScopeIdentity','requestId','claimedSha256','inputProfile','interfaceVersion']<>'{}'::jsonb THEN
   RAISE EXCEPTION 'actual person request namespace required' USING ERRCODE='22023'; END IF;
  IF request->'identity' ? 'claimedSha256' AND request->'identity'->>'claimedSha256' IS DISTINCT FROM encode(sha256(original_input),'hex') THEN
   RAISE EXCEPTION 'original input fingerprint required' USING ERRCODE='22023'; END IF;
  request_namespace:=convert_to(scope_identity,'UTF8');request_bytes:=convert_to(request->'identity'->>'requestId','UTF8');
  request_route:=('x'||substr(encode(sha256(convert_to('group-request','UTF8')||sha256(request_namespace)||sha256(request_bytes)),'hex'),1,16))::bit(64)::bigint;
  IF NOT pg_try_advisory_xact_lock(request_route) THEN RAISE EXCEPTION 'request in flight' USING ERRCODE='55P03'; END IF;
  SELECT generation INTO old_request_generation FROM truss.request_receipt_route_guard
   WHERE namespace_sha256=sha256(request_namespace) AND request_sha256=sha256(request_bytes) FOR UPDATE NOWAIT;
  IF NOT FOUND THEN
   INSERT INTO truss.request_receipt_route_guard VALUES(sha256(request_namespace),sha256(request_bytes),0) RETURNING generation INTO old_request_generation;
   IF old_request_generation IS DISTINCT FROM 0 THEN RAISE EXCEPTION 'exact request guard required' USING ERRCODE='55000'; END IF;
  END IF;
  SELECT count(*) INTO candidate_count FROM (SELECT 1 FROM truss.request_receipt
   WHERE namespace_sha256=sha256(request_namespace) AND request_sha256=sha256(request_bytes) LIMIT 10001) q;
  IF candidate_count>10000 THEN RAISE EXCEPTION 'bounded receipt route required' USING ERRCODE='54000'; END IF;
  SELECT count(*) INTO candidate_count FROM truss.request_receipt WHERE namespace_sha256=sha256(request_namespace) AND request_sha256=sha256(request_bytes) AND namespace_identity_utf8=request_namespace AND request_id_utf8=request_bytes;
  IF candidate_count>1 THEN RAISE EXCEPTION 'unique exact request receipt required' USING ERRCODE='55000'; END IF;
  SELECT * INTO existing FROM truss.request_receipt WHERE namespace_sha256=sha256(request_namespace) AND request_sha256=sha256(request_bytes)
   AND namespace_identity_utf8=request_namespace AND request_id_utf8=request_bytes;
  IF FOUND THEN
   IF existing.payload_state<>'complete' THEN RETURN convert_to('{"outcome":"unavailable","reason":"receipt_expired"}','UTF8'); END IF;
   receipt_json:=convert_from(existing.original_receipt_bytes,'UTF8')::jsonb;
   IF receipt_json->>'profile' IS DISTINCT FROM 'truss-create-receipt/0.1' THEN
    RAISE EXCEPTION 'selected receipt profile required' USING ERRCODE='0A000'; END IF;
   IF decode(receipt_json->>'inputBase64','base64') IS DISTINCT FROM original_input THEN
    RAISE EXCEPTION 'request input or origin changed' USING ERRCODE='P1001'; END IF;
   FOR operation_meta IN SELECT value FROM jsonb_array_elements(metadata) LOOP
    PERFORM truss.runtime_module_writer(operation_meta->>'documentId',operation_meta->>'moduleId');
   END LOOP;
   observation_bytes:=convert_to(jsonb_build_object('profile','truss-native-create-replay-observation/0.1',
    'sourceEpoch',installation.source_epoch::text,'observingXid',writer::text,'originalWriterXid',existing.original_writer_xid::text,
    'receiptStorageId',existing.storage_row_id::text,'receiptGeneration',existing.lifecycle_generation::text,
    'receiptSha256',encode(sha256(existing.original_receipt_bytes),'hex'),'actorOid',actor_oid::text,'actor',session_user::text,
    'scopeIdentity',scope_identity,'releaseId',installation.release_id,'releaseSha256',installation.release_sha256,
    'basis',CASE WHEN existing.original_writer_xid=writer THEN 'same_transaction' ELSE 'committed_receipt' END)::text,'UTF8');
   RETURN convert_to(jsonb_build_object('outcome','success','disposition','replayed',
    'durability',CASE WHEN existing.original_writer_xid=writer THEN 'pending' ELSE 'committed' END,
    'semantic',receipt_json->'semantic','receiptBase64',replace(encode(existing.original_receipt_bytes,'base64'),chr(10),''),
    'receiptSha256',encode(sha256(existing.original_receipt_bytes),'hex'),
    'observationBase64',replace(encode(observation_bytes,'base64'),chr(10),''),'observationSha256',encode(sha256(observation_bytes),'hex'))::text,'UTF8');
  END IF;
 END IF;
 IF (SELECT count(*) FROM (SELECT 1 FROM truss.runtime_create_group WHERE writer_xid=writer LIMIT 129) g)>=128 THEN
  RAISE EXCEPTION 'bounded groups per transaction required' USING ERRCODE='54000'; END IF;
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
    SELECT 1 FROM truss.runtime_object_attempt a WHERE a.writer_xid=writer AND a.actor_oid=truss.runtime_person(false) AND NOT a.complete
    AND convert_from(a.input_bytes,'UTF8')::jsonb->'operations'->a.next_index=operation
    AND a.documents_bytes=original_documents) THEN
   RAISE EXCEPTION 'mandatory relationship unsupported by create-only profile' USING ERRCODE='0A000'; END IF;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(operation->'values') v WHERE jsonb_typeof(v.value->'name') IS DISTINCT FROM 'string'
   OR octet_length(v.value->>'name') NOT BETWEEN 1 AND 4096 OR v.value-ARRAY['name','value']<>'{}'::jsonb
   OR truss.valid_scalar_cell(v.value->'value') IS NOT TRUE)
   OR jsonb_array_length(operation->'values')<>(SELECT count(DISTINCT v.value->>'name') FROM jsonb_array_elements(operation->'values') v) THEN
   RAISE EXCEPTION 'unique exact scalar authored values required' USING ERRCODE='22023'; END IF;
  props:='{}';retained:='{}';
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=selected_type.type_id AND retired_rev IS NULL ORDER BY prop_id LOOP
   IF coalesce(property.scalar_type,'') NOT IN ('string','integer','decimal','boolean','timestamp','binary') OR property.cardinality IS DISTINCT FROM 'one' OR property.home<>'json'
    OR property.nullability NOT IN ('required','absent-allowed') OR property.item IS NOT NULL
    OR (property.facets IS NOT NULL AND property.facets<>'{}'::jsonb AND NOT ((property.scalar_type='integer' AND property.facets='{"integerWidth":{"bits":64,"signed":true}}'::jsonb) OR (property.scalar_type='decimal' AND property.facets='{"precision":18,"scale":4}'::jsonb) OR property.facets='{}'::jsonb)) THEN
    RAISE EXCEPTION 'selected scalar property profile required' USING ERRCODE='0A000'; END IF;
   SELECT v.value->'value' INTO supplied_value FROM jsonb_array_elements(operation->'values') v WHERE v.value->>'name'=property.name;
   IF NOT FOUND THEN
    IF property.nullability='required' THEN RAISE EXCEPTION 'missing required value' USING ERRCODE='22023'; END IF;
   ELSE
    IF truss.valid_scalar_property(supplied_value,property.scalar_type,property.nullability='absent-allowed',property.facets) IS NOT TRUE THEN
     RAISE EXCEPTION 'exact property family and value required' USING ERRCODE='22023'; END IF;
    props:=props||jsonb_build_object(property.prop_id::text,supplied_value);
   END IF;
  END LOOP;
  SELECT coalesce(jsonb_object_agg(v.value->>'name',v.value->'value'),'{}'::jsonb) INTO retained
   FROM jsonb_array_elements(operation->'values') v WHERE NOT EXISTS(SELECT 1 FROM truss.prop_def p
    WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL AND p.name=v.value->>'name');
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
   SELECT k.value INTO STRICT key_input FROM jsonb_array_elements(key_inputs) k WHERE k.value->>'operationIndex'=current_index::text
    AND k.value->>'keyNumber'=key_definition.key_num::text;
   tuple_bytes:=decode(key_input->>'tupleHex','hex');
   IF NOT truss.verify_umf_scalar_key_tuple(tuple_bytes,values_cells,key_facets) THEN RAISE EXCEPTION 'original key values disagree' USING ERRCODE='22023'; END IF;
   owner_receipt:=convert_from(decode(key_input->>'receiptBase64','base64'),'UTF8')::jsonb;
   IF owner_receipt->>'operation' IS DISTINCT FROM 'encode-core-key-tuple' OR owner_receipt->>'profile' IS DISTINCT FROM 'umf-key-tuple-v1'
    OR owner_receipt->>'bytesHex' IS DISTINCT FROM encode(tuple_bytes,'hex')
    OR owner_receipt->'identity' IS DISTINCT FROM jsonb_build_object('module',selected_type.module,'element',selected_type.element,'key',key_definition.key_id)
    OR owner_receipt->'values' IS DISTINCT FROM truss.umf_key_values(values_cells)
    OR owner_receipt->'source' IS DISTINCT FROM (SELECT d.document::jsonb FROM truss.schema_doc d WHERE d.doc_id=selected_type.document_id ORDER BY d.rev DESC LIMIT 1) THEN
    RAISE EXCEPTION 'original owner key receipt required' USING ERRCODE='22023'; END IF;
   SELECT * INTO STRICT source_pin FROM truss.runtime_definition('key',selected_type.type_id,key_definition.key_num);
   namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected_type.type_id::text,'keyNumber',key_definition.key_num::text,
    'definitionPin',source_pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');
   planned_keys:=planned_keys||jsonb_build_array(jsonb_build_object('operationIndex',current_index,'typeId',selected_type.type_id,
    'keyNumber',key_definition.key_num,'namespace',encode(namespace,'hex'),'transport',encode(transport,'hex'),
    'tupleHex',encode(tuple_bytes,'hex'),'receiptBase64',key_input->>'receiptBase64'));
  END LOOP;
  current_index:=current_index+1;
 END LOOP;
 IF jsonb_array_length(key_inputs)<>jsonb_array_length(planned_keys)
  OR jsonb_array_length(planned_keys)<>(SELECT count(DISTINCT (k.value->>'namespace',k.value->>'transport')) FROM jsonb_array_elements(planned_keys) k)
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
  object_row.root_id:=NULL;object_row.root_type:=NULL;object_row.rev:=captured_revision;object_row.ver:=1;
  object_row.created_at:=clock_timestamp();object_row.updated_at:=object_row.created_at;
  planned_row:=to_jsonb(object_row);
  INSERT INTO truss.object SELECT (jsonb_populate_record(NULL::truss.object,planned_row)).* RETURNING to_jsonb(object) INTO actual_row;
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
   membership.original_context_bytes:=convert_to(jsonb_build_object('profile','truss-created-key-context/0.1',
    'groupId',group_uuid::text,'sourceEpoch',installation.source_epoch::text,'xid',writer::text,
    'actorOid',actor_oid::text,'actor',session_user::text,'operationIndex',current_index::text,
    'ownerReceiptBase64',key_plan->>'receiptBase64')::text,'UTF8');
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
  properties_json:='[]';
  FOR property IN SELECT * FROM truss.prop_def WHERE type_id=object_row.type_id AND retired_rev IS NULL ORDER BY prop_id LOOP
   IF object_row.props ? property.prop_id::text THEN
    SELECT * INTO STRICT source_pin FROM truss.runtime_definition('property',object_row.type_id,property.prop_id);
    properties_json:=properties_json||jsonb_build_array(jsonb_build_object('propertyId',property.prop_id::text,
     'definitionPin',source_pin.definition_pin,'value',object_row.props->property.prop_id::text));
   END IF;
  END LOOP;
  SELECT coalesce(jsonb_agg(jsonb_build_object('name',key,'value',value) ORDER BY key COLLATE "C"),'[]'::jsonb) INTO retained_json
   FROM jsonb_each(coalesce(object_row.retained,'{}'::jsonb));
  after_record:=jsonb_build_object('interfaceVersion','truss-history-record/0.1.0','kind','object','identity',object_identity,
   'recordVersion','1','catalogRevision',captured_revision::text,'createdAt',to_char(object_row.created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'updatedAt',to_char(object_row.updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'properties',properties_json,'retained',retained_json,'ownership',jsonb_build_object('state','rootless'));
  journal_row.seq:=nextval('truss.journal_seq');journal_row.at:=clock_timestamp();journal_row.xid:=writer;
  journal_row.entity_kind:='o';journal_row.entity_id:=object_row.id;journal_row.entity_type:=object_row.type_id;
  journal_row.ver:=1;journal_row.op:='create';journal_row.prop_id:=NULL;journal_row.old_value:=NULL;journal_row.rev:=captured_revision;
  event:=jsonb_build_object('interfaceVersion','truss-history-event/0.2.0-proposal','sourceEpoch',installation.source_epoch::text,
   'historyProfile','truss-native-scalar-create/0.2','xid',writer::text,'seq',journal_row.seq::text,'identity',object_identity,
   'eventVersion','1','eventCatalogRevision',captured_revision::text,'operation','create','after',after_record,
   'origin',jsonb_build_object('asserted',input->'assertedOrigin','databaseRole',session_user::text));
  event_digest:=encode(sha256(convert_to(jsonb_build_array(event)::text,'UTF8')),'hex');
  event:=event||jsonb_build_object('mutationGroup',jsonb_build_object('profile','truss-history-group/0.1.0','eventCount','1','orderedEventDigest',event_digest));
  event_bytes:=convert_to(event::text,'UTF8');origin_bytes:=convert_to((event->'origin')::text,'UTF8');
  journal_row.new_value:=truss.runtime_exact_wrapper('event',event_bytes);journal_row.origin:=truss.runtime_exact_wrapper('origin',origin_bytes);
  expected_journal:=to_jsonb(journal_row);
  INSERT INTO truss.journal SELECT (jsonb_populate_record(NULL::truss.journal,expected_journal)).* RETURNING to_jsonb(journal) INTO actual_journal;
  IF actual_journal IS DISTINCT FROM expected_journal THEN RAISE EXCEPTION 'exact complete journal append required' USING ERRCODE='55000'; END IF;
  members:=members||jsonb_build_array(jsonb_build_object('object',to_jsonb(object_row),'keys',member_keys,'journal',expected_journal));
  outcome:=jsonb_build_object('operation','create_object','outcome','created','identity',object_identity,'version','1',
   'events',jsonb_build_array(jsonb_build_object('sourceEpoch',installation.source_epoch::text,'historyProfile','truss-native-scalar-create/0.2',
    'xid',writer::text,'seq',journal_row.seq::text)));
  IF operation ? 'alias' THEN outcome:=outcome||jsonb_build_object('alias',operation->>'alias');
   aliases:=aliases||jsonb_build_array(jsonb_build_object('alias',operation->>'alias','identity',object_identity)); END IF;
  results:=results||jsonb_build_array(outcome);current_index:=current_index+1;
 END LOOP;
 semantic:=jsonb_build_object('interfaceVersion','truss-group-result/0.1.0','executedCatalogRevision',captured_revision::text,
  'layoutProfile',input->'layoutProfile','mutationProfile',input->'mutationProfile','results',results,'aliases',aliases);
 semantic_bytes:=convert_to(semantic::text,'UTF8');
 IF octet_length(semantic_bytes)>16777216 THEN RAISE EXCEPTION 'bounded group result required' USING ERRCODE='54000'; END IF;
 IF request<>'{"state":"none"}'::jsonb THEN
  receipt_bytes:=convert_to(jsonb_build_object('profile','truss-create-receipt/0.1','groupId',group_uuid::text,
   'inputBase64',replace(encode(original_input,'base64'),chr(10),''),'semantic',semantic)::text,'UTF8');
  receipt.storage_row_id:=nextval('truss.request_receipt_row_seq');receipt.namespace_identity_utf8:=request_namespace;receipt.request_id_utf8:=request_bytes;
  receipt.original_writer_xid:=writer;receipt.original_writer_context_bytes:=convert_to(jsonb_build_object('profile','truss-create-writer-context/0.1',
   'installationId',installation.installation_id::text,'sourceEpoch',installation.source_epoch::text,'groupId',group_uuid::text,
   'actor',session_user::text,'actorOid',actor_oid::text,'xid',writer::text)::text,'UTF8');
  receipt.lifecycle_generation:=0;receipt.payload_state:='complete';receipt.original_receipt_bytes:=receipt_bytes;
  receipt.expired_identity_bytes:=NULL;receipt.expiry_writer_xid:=NULL;receipt.expiry_writer_context_bytes:=NULL;
  receipt.namespace_sha256:=sha256(request_namespace);receipt.request_sha256:=sha256(request_bytes);receipt_json:=to_jsonb(receipt);
  INSERT INTO truss.request_receipt(storage_row_id,namespace_identity_utf8,request_id_utf8,original_writer_xid,
   original_writer_context_bytes,lifecycle_generation,payload_state,original_receipt_bytes)
   VALUES(receipt.storage_row_id,request_namespace,request_bytes,writer,receipt.original_writer_context_bytes,0,'complete',receipt_bytes)
   RETURNING to_jsonb(request_receipt) INTO actual_row;
  IF actual_row IS DISTINCT FROM receipt_json THEN RAISE EXCEPTION 'exact durable request receipt required' USING ERRCODE='55000'; END IF;
  UPDATE truss.request_receipt_route_guard SET generation=generation+1 WHERE namespace_sha256=sha256(request_namespace) AND request_sha256=sha256(request_bytes)
   RETURNING generation INTO new_generation;
  IF new_generation IS DISTINCT FROM old_request_generation+1 THEN RAISE EXCEPTION 'exact request generation required' USING ERRCODE='55000'; END IF;
 END IF;
 intended_group.group_id:=group_uuid;intended_group.writer_xid:=writer;intended_group.actor_oid:=actor_oid;intended_group.actor_name:=session_user::text;
 intended_group.original_input_bytes:=original_input;intended_group.original_document_bytes:=original_documents;intended_group.original_key_bytes:=original_keys;
 intended_group.semantic_bytes:=semantic_bytes;intended_group.expected_members:=members;
 intended_group.receipt_storage_row_id:=receipt.storage_row_id;intended_group.expected_receipt:=receipt_json;
 planned_row:=to_jsonb(intended_group);
 INSERT INTO truss.runtime_create_group SELECT (jsonb_populate_record(NULL::truss.runtime_create_group,planned_row)).*
  RETURNING to_jsonb(runtime_create_group) INTO actual_row;
 IF actual_row IS DISTINCT FROM planned_row THEN RAISE EXCEPTION 'complete intended group insert required' USING ERRCODE='55000'; END IF;
 SELECT to_jsonb(g) INTO actual_row FROM truss.runtime_create_group g WHERE group_id=group_uuid;
 IF actual_row IS DISTINCT FROM planned_row THEN RAISE EXCEPTION 'complete intended group readback required' USING ERRCODE='55000'; END IF;
 FOR current_index IN 0..jsonb_array_length(members)-1 LOOP
  INSERT INTO truss.runtime_create_member VALUES((members->current_index->'object'->>'id')::bigint,
   (members->current_index->'object'->>'type_id')::int,group_uuid,current_index);
  PERFORM truss.runtime_create_validate_member((members->current_index->'object'->>'id')::bigint,(members->current_index->'object'->>'type_id')::int);
 END LOOP;
 PERFORM truss.runtime_create_validate_group(group_uuid);
 FOR operation_meta IN SELECT value FROM jsonb_array_elements(metadata) LOOP
  PERFORM truss.runtime_module_writer(operation_meta->>'documentId',operation_meta->>'moduleId');
 END LOOP;
 RETURN convert_to(jsonb_build_object('outcome','success','disposition','applied','durability','pending','semantic',semantic)::text,'UTF8');
EXCEPTION
 WHEN insufficient_privilege OR query_canceled OR serialization_failure OR deadlock_detected THEN RAISE;
 WHEN OTHERS THEN
  GET STACKED DIAGNOSTICS native_state=RETURNED_SQLSTATE;
  IF native_state IN ('0A000','54000','55P03') THEN
   outcome:=jsonb_build_object('outcome','unavailable','reason',CASE native_state WHEN '0A000' THEN 'profile' WHEN '54000' THEN 'resource' ELSE 'observation' END);
  ELSE
   outcome:=jsonb_build_object('outcome','failed','code',CASE WHEN native_state='P1001' THEN 'request_conflict' ELSE 'group_failed' END,
    'operationIndex',greatest(least(current_index,jsonb_array_length(input->'operations')-1),0)::text,'nativeState',native_state);
  END IF;
  RETURN convert_to(outcome::text,'UTF8');
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
