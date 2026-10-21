-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Person-scoped catalog metadata; no complete unauthorized source crosses the facade.
-- Private actor is issued by the current native invocation, never retained
-- or accepted from a public caller. Module policy/membership checks stay live.
-- Reuse plans for repeated private point lookups; function-local settings
-- restore the caller policy on return, including exceptional return.
CREATE FUNCTION truss.runtime_can_read_qualified(document_id text,module_id text,qualified_actor oid) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET plan_cache_mode='force_generic_plan' AS $$
DECLARE person oid;policy truss.module_access%ROWTYPE;
BEGIN
 person:=qualified_actor;
 IF current_setting('transaction_read_only')='on' THEN
 SELECT * INTO policy FROM truss.module_access p WHERE p.document_id=runtime_can_read_qualified.document_id AND p.module=module_id;
 ELSE
 SELECT * INTO policy FROM truss.module_access p WHERE p.document_id=runtime_can_read_qualified.document_id AND p.module=module_id FOR SHARE NOWAIT;
 END IF;
 IF NOT FOUND THEN RETURN false; END IF;
 RETURN EXISTS(WITH RECURSIVE memberships(role_oid) AS (
  SELECT person UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
  SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid WHERE r.rolname::text IN(policy.reader_role,policy.writer_role));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_can_read_qualified(text,text,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_can_read(document_id text,module_id text) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN truss.runtime_can_read_qualified(document_id,module_id,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_can_read(text,text) FROM PUBLIC;

CREATE FUNCTION truss.reader_catalog(maximum_count int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;captured_revision int;modules jsonb:='[]';owner record;module jsonb;encoded bytea;definition_count int:=0;dependency record;
BEGIN
 PERFORM truss.runtime_person(false);
 IF maximum_count IS NULL OR maximum_count NOT BETWEEN 1 AND 65536 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 THEN RAISE EXCEPTION 'bounded catalog limits required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN RAISE EXCEPTION 'selected runtime required' USING ERRCODE='0A000';END IF;
 IF current_setting('transaction_read_only')='on' THEN
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 ELSE
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 END IF;
 IF captured_revision<1 THEN RAISE EXCEPTION 'accepted catalog required' USING ERRCODE='0A000';END IF;
 FOR owner IN SELECT d.doc_id,d.rev AS source_catalog_revision,d.doc_revision,d.content_sha256,m.value->>'id' AS module_id
  FROM truss.schema_doc d CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m(value)
  WHERE d.rev<=captured_revision AND d.rev=(SELECT max(latest.rev) FROM truss.schema_doc latest WHERE latest.doc_id=d.doc_id AND latest.rev<=captured_revision) ORDER BY d.doc_id COLLATE "C",m.value->>'id' COLLATE "C" LOOP
  IF NOT truss.runtime_can_read(owner.doc_id,owner.module_id) THEN CONTINUE;END IF;
  module:=jsonb_build_object('documentId',owner.doc_id,'moduleId',owner.module_id,'documentRevision',owner.doc_revision,'documentSha256',owner.content_sha256,'sourceCatalogRevision',owner.source_catalog_revision,
   'types',(SELECT coalesce(jsonb_agg(jsonb_build_object('typeId',t.type_id,'recordId',t.element,'kind',t.kind,'provisional',t.provisional) ORDER BY t.type_id),'[]') FROM truss.type_def t WHERE t.document_id=owner.doc_id AND t.module=owner.module_id AND t.retired_rev IS NULL),
   'properties',(SELECT coalesce(jsonb_agg(jsonb_build_object('propertyId',p.prop_id,'typeId',p.type_id,'fieldId',p.element,'name',p.name,'scalarType',p.scalar_type,'nullability',p.nullability,'cardinality',p.cardinality,'itemDefinition',p.item-'declaration') ORDER BY p.prop_id),'[]') FROM truss.prop_def p JOIN truss.type_def t USING(type_id) WHERE t.document_id=owner.doc_id AND t.module=owner.module_id AND t.retired_rev IS NULL AND p.retired_rev IS NULL AND truss.runtime_can_read(t.document_id,p.declaration_module) AND (p.cardinality NOT IN ('array','map') OR truss.runtime_item_chain_readable(p.item))),
   'keys',(SELECT coalesce(jsonb_agg(jsonb_build_object('typeId',k.type_id,'keyId',k.key_id,'keyNumber',k.key_num,'propertyIds',k.prop_ids,'primary',k.is_primary) ORDER BY k.type_id,k.key_num),'[]') FROM truss.key_def k JOIN truss.type_def t USING(type_id) WHERE t.document_id=owner.doc_id AND t.module=owner.module_id AND t.retired_rev IS NULL AND k.retired_rev IS NULL AND NOT EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.prop_id=ANY(k.prop_ids) AND NOT truss.runtime_can_read(t.document_id,p.declaration_module))),
   'relationships',(SELECT coalesce(jsonb_agg(jsonb_build_object('relationshipId',r.rel_type_id,'authoredId',r.rel_id,'name',r.name,'sourceMin',r.source_min,'sourceMax',r.source_max,'targetMin',r.target_min,'targetMax',r.target_max,'directed',r.directed,
      'endpoints',(SELECT jsonb_agg(jsonb_build_object('sourceType',e.source_type,'targetType',e.target_type) ORDER BY e.source_type,e.target_type) FROM truss.rel_endpoint e WHERE e.rel_type_id=r.rel_type_id)) ORDER BY r.rel_type_id),'[]') FROM truss.rel_def r
    WHERE r.document_id=owner.doc_id AND r.module=owner.module_id AND r.retired_rev IS NULL
    AND NOT EXISTS(SELECT 1 FROM truss.rel_endpoint e JOIN truss.type_def s ON s.type_id=e.source_type JOIN truss.type_def t ON t.type_id=e.target_type WHERE e.rel_type_id=r.rel_type_id AND (NOT truss.runtime_can_read(s.document_id,s.module) OR NOT truss.runtime_can_read(t.document_id,t.module)))
    AND NOT EXISTS(SELECT 1 FROM truss.rel_endpoint e JOIN truss.key_def k ON k.type_id=e.target_type AND k.key_id=r.target_key JOIN truss.type_def t ON t.type_id=k.type_id JOIN truss.prop_def p ON p.prop_id=ANY(k.prop_ids) WHERE e.rel_type_id=r.rel_type_id AND NOT truss.runtime_can_read(t.document_id,p.declaration_module))
    AND (r.assoc_type_id IS NULL OR EXISTS(SELECT 1 FROM truss.type_def a WHERE a.type_id=r.assoc_type_id AND truss.runtime_can_read(a.document_id,a.module)))));
  definition_count:=definition_count+1+jsonb_array_length(module->'types')+jsonb_array_length(module->'properties')+jsonb_array_length(module->'keys')+jsonb_array_length(module->'relationships');
  IF definition_count>maximum_count THEN RAISE EXCEPTION 'catalog count limit' USING ERRCODE='54000';END IF;
  modules:=modules||jsonb_build_array(module);
  IF octet_length(modules::text)>maximum_bytes THEN RAISE EXCEPTION 'catalog byte limit' USING ERRCODE='54000';END IF;
 END LOOP;
 -- Membership may have changed while the projection was assembled.
 FOR module IN SELECT value FROM jsonb_array_elements(modules) LOOP
  IF NOT truss.runtime_can_read(module->>'documentId',module->>'moduleId') THEN RAISE EXCEPTION 'current reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 -- Recheck every dependency actually used in the buffered projection, even if
 -- that owner was revoked before its own module was visited and emitted.
 FOR dependency IN
  SELECT DISTINCT document_id,module_id FROM (
   SELECT t.document_id,p.declaration_module AS module_id
    FROM jsonb_array_elements(modules) m CROSS JOIN LATERAL jsonb_array_elements(m.value->'properties') f
    JOIN truss.prop_def p ON p.prop_id=(f.value->>'propertyId')::int JOIN truss.type_def t USING(type_id)
   UNION
   SELECT node.value->>'documentId',node.value->'reference'->>'module'
    FROM jsonb_array_elements(modules) m CROSS JOIN LATERAL jsonb_array_elements(m.value->'properties') f
    JOIN truss.prop_def p ON p.prop_id=(f.value->>'propertyId')::int
    CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(p.item)||coalesce(p.item->'descendants','[]'::jsonb)) node
    WHERE p.cardinality IN ('array','map')
   UNION
   SELECT t.document_id,p.declaration_module
    FROM jsonb_array_elements(modules) m CROSS JOIN LATERAL jsonb_array_elements(m.value->'keys') k
    JOIN truss.type_def t ON t.type_id=(k.value->>'typeId')::int
    CROSS JOIN LATERAL jsonb_array_elements_text(k.value->'propertyIds') f JOIN truss.prop_def p ON p.prop_id=f.value::int
   UNION
   SELECT t.document_id,t.module
    FROM jsonb_array_elements(modules) m CROSS JOIN LATERAL jsonb_array_elements(m.value->'relationships') r
    JOIN truss.rel_endpoint e ON e.rel_type_id=(r.value->>'relationshipId')::int
    JOIN truss.type_def t ON t.type_id IN(e.source_type,e.target_type)
   UNION
   SELECT t.document_id,t.module
    FROM jsonb_array_elements(modules) m CROSS JOIN LATERAL jsonb_array_elements(m.value->'relationships') r
    JOIN truss.rel_def d ON d.rel_type_id=(r.value->>'relationshipId')::int JOIN truss.type_def t ON t.type_id=d.assoc_type_id
   UNION
   SELECT t.document_id,p.declaration_module
    FROM jsonb_array_elements(modules) m CROSS JOIN LATERAL jsonb_array_elements(m.value->'relationships') r
    JOIN truss.rel_def d ON d.rel_type_id=(r.value->>'relationshipId')::int JOIN truss.rel_endpoint e ON e.rel_type_id=d.rel_type_id
    JOIN truss.key_def k ON k.type_id=e.target_type AND k.key_id=d.target_key
    JOIN truss.type_def t ON t.type_id=k.type_id JOIN truss.prop_def p ON p.prop_id=ANY(k.prop_ids)
  ) used_owners LOOP
  IF NOT truss.runtime_can_read(dependency.document_id,dependency.module_id) THEN RAISE EXCEPTION 'current dependency reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 PERFORM truss.runtime_person(false);
 encoded:=convert_to(jsonb_build_object('catalogRevision',captured_revision,'layoutProfile',installation.layout_profile,'modules',modules)::text,'UTF8');
 IF octet_length(encoded)>maximum_bytes THEN RAISE EXCEPTION 'catalog byte limit' USING ERRCODE='54000';END IF;
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN
  RAISE EXCEPTION 'catalog changed during reader observation' USING ERRCODE='55P03';END IF;
 RETURN encoded;
END;
$$;
REVOKE ALL ON FUNCTION truss.reader_catalog(int,int,text,text) FROM PUBLIC;

-- Cache validators are installation-scoped opaque fingerprints, never grants.
-- Every invocation still validates the current person, catalog basis and all
-- effective module policies before returning either a snapshot or a hit.
CREATE FUNCTION truss.reader_catalog_if_changed(maximum_count int,maximum_bytes int,expected_release text,expected_digest text,validator text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;captured_revision int;actor oid;captured_actor oid;
 effective_policies jsonb;captured_policies jsonb;native_context jsonb;captured_native_context jsonb;
 scope_digest bytea;current_validator text;catalog_bytes bytea;response_bytes bytea;
BEGIN
 actor:=truss.runtime_person(false);
 IF maximum_count IS NULL OR maximum_count NOT BETWEEN 1 AND 65536 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216
  OR validator IS NOT NULL AND (octet_length(validator) NOT BETWEEN 1 AND 4096 OR validator !~ '^[0-9a-f]{64}$') THEN
  RAISE EXCEPTION 'bounded catalog validator request required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected runtime required' USING ERRCODE='0A000';END IF;
 IF current_setting('transaction_read_only')='on' THEN
  SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 ELSE
  SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 END IF;
 IF captured_revision<1 THEN RAISE EXCEPTION 'accepted catalog required' USING ERRCODE='0A000';END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_array(p.document_id,p.module,truss.runtime_can_read_qualified(p.document_id,p.module,actor))
   ORDER BY p.document_id COLLATE "C",p.module COLLATE "C"),'[]'::jsonb)
 INTO effective_policies FROM truss.module_access p;
 WITH RECURSIVE memberships(role_oid) AS (
  SELECT actor UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid
 ), role_states(active_oid,privilege_oid) AS (
  SELECT actor,actor UNION
  SELECT CASE WHEN m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid) THEN m.roleid ELSE s.active_oid END,m.roleid
   FROM pg_auth_members m JOIN role_states s ON m.member=s.privilege_oid
   WHERE m.inherit_option OR m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid)
 ) SELECT jsonb_build_object(
  'effectiveMemberships',(SELECT coalesce(jsonb_agg(role_oid::text ORDER BY role_oid),'[]'::jsonb) FROM memberships),
  'roleStates',(SELECT coalesce(jsonb_agg(jsonb_build_array(active_oid::text,privilege_oid::text) ORDER BY active_oid,privilege_oid),'[]'::jsonb) FROM role_states),
  'nativeRoleFlags',(SELECT coalesce(jsonb_agg(jsonb_build_array(r.oid::text,r.rolname,r.rolcanlogin,r.rolsuper,r.rolcreaterole,r.rolcreatedb,r.rolreplication,r.rolbypassrls,r.rolinherit)
    ORDER BY r.oid),'[]'::jsonb) FROM pg_roles r WHERE r.oid IN(SELECT role_oid FROM memberships) OR r.oid IN(installation.owner_oid,installation.registrar_oid)),
  'transactionIsolation',current_setting('transaction_isolation'),
  'transactionReadOnly',current_setting('transaction_read_only'),
  'roleSetting',current_setting('role'),
  'currentUser',(SELECT oid::text FROM pg_roles WHERE rolname=current_user),
  'serverVersion',current_setting('server_version_num')) INTO native_context;
 PERFORM truss.runtime_person(false);
 captured_actor:=actor;captured_policies:=effective_policies;captured_native_context:=native_context;
 scope_digest:=sha256(convert_to(jsonb_build_object('installation',installation.installation_id::text,
   'release',installation.release_id,'releaseSha256',installation.release_sha256,'layoutProfile',installation.layout_profile,'revision',captured_revision,
   'actor',actor::text,'maximumCount',maximum_count,'maximumBytes',maximum_bytes,
   'effectivePolicies',effective_policies,'nativeContext',native_context)::text,'UTF8'));
 SELECT sha256(s.secret||scope_digest) INTO STRICT scope_digest FROM truss.reader_catalog_validator_secret s;
 current_validator:=encode(scope_digest,'hex');
 IF validator IS NOT NULL AND validator=current_validator THEN
  response_bytes:=convert_to(jsonb_build_object('outcome','unchanged','validator',current_validator)::text,'UTF8');
 ELSE
  catalog_bytes:=truss.reader_catalog(maximum_count,maximum_bytes,expected_release,expected_digest);
  response_bytes:=convert_to(jsonb_build_object('outcome','snapshot','validator',current_validator,
    'catalog',convert_from(catalog_bytes,'UTF8')::jsonb)::text,'UTF8');
  IF octet_length(response_bytes)>maximum_bytes THEN RAISE EXCEPTION 'conditional catalog byte limit' USING ERRCODE='54000';END IF;
 END IF;
 -- Re-read the whole authority basis immediately before either response. A
 -- valid person identity alone is insufficient after a membership or policy
 -- change while the projection was being assembled.
 actor:=truss.runtime_person(false);
 SELECT coalesce(jsonb_agg(jsonb_build_array(p.document_id,p.module,truss.runtime_can_read_qualified(p.document_id,p.module,actor))
   ORDER BY p.document_id COLLATE "C",p.module COLLATE "C"),'[]'::jsonb)
 INTO effective_policies FROM truss.module_access p;
 WITH RECURSIVE memberships(role_oid) AS (
  SELECT actor UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid
 ), role_states(active_oid,privilege_oid) AS (
  SELECT actor,actor UNION
  SELECT CASE WHEN m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid) THEN m.roleid ELSE s.active_oid END,m.roleid
   FROM pg_auth_members m JOIN role_states s ON m.member=s.privilege_oid
   WHERE m.inherit_option OR m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid)
 ) SELECT jsonb_build_object(
  'effectiveMemberships',(SELECT coalesce(jsonb_agg(role_oid::text ORDER BY role_oid),'[]'::jsonb) FROM memberships),
  'roleStates',(SELECT coalesce(jsonb_agg(jsonb_build_array(active_oid::text,privilege_oid::text) ORDER BY active_oid,privilege_oid),'[]'::jsonb) FROM role_states),
  'nativeRoleFlags',(SELECT coalesce(jsonb_agg(jsonb_build_array(r.oid::text,r.rolname,r.rolcanlogin,r.rolsuper,r.rolcreaterole,r.rolcreatedb,r.rolreplication,r.rolbypassrls,r.rolinherit)
    ORDER BY r.oid),'[]'::jsonb) FROM pg_roles r WHERE r.oid IN(SELECT role_oid FROM memberships) OR r.oid IN(installation.owner_oid,installation.registrar_oid)),
  'transactionIsolation',current_setting('transaction_isolation'),
  'transactionReadOnly',current_setting('transaction_read_only'),
  'roleSetting',current_setting('role'),
  'currentUser',(SELECT oid::text FROM pg_roles WHERE rolname=current_user),
  'serverVersion',current_setting('server_version_num')) INTO native_context;
 IF actor IS DISTINCT FROM captured_actor OR effective_policies IS DISTINCT FROM captured_policies
  OR native_context IS DISTINCT FROM captured_native_context
  OR (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN
  RAISE EXCEPTION 'catalog authority changed during conditional reader observation' USING ERRCODE='55P03';END IF;
 PERFORM truss.runtime_person(false);
 RETURN response_bytes;
END;
$$;
REVOKE ALL ON FUNCTION truss.reader_catalog_if_changed(int,int,text,text,text) FROM PUBLIC;

CREATE FUNCTION truss.registrar_status(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;actor oid;is_registrar boolean;
BEGIN
 actor:=truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected runtime required' USING ERRCODE='0A000';END IF;
 WITH RECURSIVE memberships(role_oid) AS (
  SELECT actor UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
 SELECT coalesce(bool_or(role_oid=installation.registrar_oid),false) INTO is_registrar FROM memberships;
 PERFORM truss.runtime_person(false);
 RETURN convert_to(jsonb_build_object('registrar',is_registrar)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.registrar_status(text,text) FROM PUBLIC;

CREATE FUNCTION truss.accepted_document(selected_document text,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;captured_revision int;archive truss.schema_doc%ROWTYPE;module jsonb;source jsonb;request truss.catalog_registration_request%ROWTYPE;encoded bytea;
BEGIN
 PERFORM truss.runtime_person(false);
 IF selected_document IS NULL OR octet_length(selected_document) NOT BETWEEN 1 AND 4096 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 THEN RAISE EXCEPTION 'bounded document selection required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN RAISE EXCEPTION 'selected runtime required' USING ERRCODE='0A000';END IF;
 IF current_setting('transaction_read_only')='on' THEN
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 ELSE
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 END IF;
 IF captured_revision<1 THEN RAISE EXCEPTION 'accepted catalog required' USING ERRCODE='0A000';END IF;
 SELECT * INTO archive FROM truss.schema_doc WHERE rev<=captured_revision AND doc_id=selected_document ORDER BY rev DESC LIMIT 1;
 IF NOT FOUND OR jsonb_array_length(archive.document::jsonb->'modules')=0 THEN RAISE EXCEPTION 'authorized document required' USING ERRCODE='42501';END IF;
 FOR module IN SELECT value FROM jsonb_array_elements(archive.document::jsonb->'modules') LOOP
  IF NOT truss.runtime_can_read(selected_document,module->>'id') THEN RAISE EXCEPTION 'authorized document required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF octet_length(archive.document)>maximum_bytes THEN RAISE EXCEPTION 'document byte limit' USING ERRCODE='54000';END IF;
 IF encode(sha256(convert_to(archive.document,'UTF8')),'hex') IS DISTINCT FROM archive.content_sha256 THEN RAISE EXCEPTION 'exact accepted source required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT request FROM truss.catalog_registration_request WHERE catalog_registration_request.revision=archive.rev;
 SELECT value INTO STRICT source FROM jsonb_array_elements(convert_from(request.input_bytes,'UTF8')::jsonb->'documents') WHERE value->>'documentId'=selected_document;
 IF source->>'documentRevision' IS DISTINCT FROM archive.doc_revision OR source->'artifact'->>'sha256' IS DISTINCT FROM archive.content_sha256 OR (CASE WHEN (convert_from(request.input_bytes,'UTF8')::jsonb)->>'interfaceVersion'='truss-acceptance-input/0.2.0' THEN source->'artifact' ? 'bytesBase64'
  ELSE decode(source->'artifact'->>'bytesBase64','base64') IS DISTINCT FROM convert_to(archive.document,'UTF8') END) THEN RAISE EXCEPTION 'original accepted source required' USING ERRCODE='55000';END IF;
 encoded:=convert_to((jsonb_build_object('documentId',selected_document,'documentRevision',archive.doc_revision,'artifactIdentity',source->'artifact'->>'identity','contentBase64',encode(convert_to(archive.document,'UTF8'),'base64'),'sha256',archive.content_sha256,'catalogRevision',captured_revision,'sourceCatalogRevision',archive.rev,'registrationId',request.registration_id::text,'validation',archive.validation->'sourceValidation')
  ||CASE WHEN archive.validation ? 'dddValidation' THEN jsonb_build_object('dddProfile',archive.validation->'dddProfile','dddValidation',archive.validation->'dddValidation') ELSE '{}'::jsonb END)::text,'UTF8');
 IF octet_length(encoded)>maximum_bytes THEN RAISE EXCEPTION 'encoded document byte limit' USING ERRCODE='54000';END IF;
 FOR module IN SELECT value FROM jsonb_array_elements(archive.document::jsonb->'modules') LOOP
  IF NOT truss.runtime_can_read(selected_document,module->>'id') THEN RAISE EXCEPTION 'current reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 PERFORM truss.runtime_person(false);
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN
  RAISE EXCEPTION 'catalog changed during document observation' USING ERRCODE='55P03';END IF;
 RETURN encoded;
END;
$$;
REVOKE ALL ON FUNCTION truss.accepted_document(text,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.catalog_revision(expected_release text,expected_digest text,selected_document text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;revision int;archive truss.schema_doc%ROWTYPE;module jsonb;
BEGIN
 PERFORM truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected runtime required' USING ERRCODE='0A000';END IF;
 -- No share lock: this is a cache key, not admission of a write.
 SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 IF revision<1 THEN RAISE EXCEPTION 'accepted catalog required' USING ERRCODE='0A000';END IF;
 IF selected_document IS NULL THEN RETURN convert_to(jsonb_build_object('catalogRevision',revision::text)::text,'UTF8');END IF;
 IF octet_length(selected_document) NOT BETWEEN 1 AND 4096 THEN RAISE EXCEPTION 'bounded document selection required' USING ERRCODE='22023';END IF;
 SELECT * INTO archive FROM truss.schema_doc WHERE rev<=revision AND doc_id=selected_document ORDER BY rev DESC LIMIT 1;
 IF NOT FOUND OR jsonb_array_length(archive.document::jsonb->'modules')=0 THEN RAISE EXCEPTION 'authorized document required' USING ERRCODE='42501';END IF;
 FOR module IN SELECT value FROM jsonb_array_elements(archive.document::jsonb->'modules') LOOP
  IF NOT truss.runtime_can_read(selected_document,module->>'id') THEN RAISE EXCEPTION 'authorized document required' USING ERRCODE='42501';END IF;
 END LOOP;
 RETURN convert_to(jsonb_build_object('catalogRevision',revision::text,'documentId',selected_document,'documentRevision',archive.doc_revision,'sourceCatalogRevision',archive.rev::text)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_revision(text,text,text) FROM PUBLIC;
