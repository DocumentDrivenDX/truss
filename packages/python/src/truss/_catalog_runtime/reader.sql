-- Person-scoped catalog metadata; no complete unauthorized source crosses the facade.
CREATE FUNCTION truss.runtime_can_read(document_id text,module_id text) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE person oid;policy truss.module_access%ROWTYPE;
BEGIN
 person:=truss.runtime_person(false);
 IF current_setting('transaction_read_only')='on' THEN
 SELECT * INTO policy FROM truss.module_access p WHERE p.document_id=runtime_can_read.document_id AND p.module=module_id;
 ELSE
 SELECT * INTO policy FROM truss.module_access p WHERE p.document_id=runtime_can_read.document_id AND p.module=module_id FOR SHARE NOWAIT;
 END IF;
 IF NOT FOUND THEN RETURN false; END IF;
 RETURN EXISTS(WITH RECURSIVE memberships(role_oid) AS (
  SELECT person UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
  SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid WHERE r.rolname::text IN(policy.reader_role,policy.writer_role));
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
 FOR owner IN SELECT d.doc_id,d.doc_revision,d.content_sha256,m.value->>'id' AS module_id
  FROM truss.schema_doc d CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m(value)
  WHERE d.rev<=captured_revision AND d.rev=(SELECT max(latest.rev) FROM truss.schema_doc latest WHERE latest.doc_id=d.doc_id AND latest.rev<=captured_revision) ORDER BY d.doc_id COLLATE "C",m.value->>'id' COLLATE "C" LOOP
  IF NOT truss.runtime_can_read(owner.doc_id,owner.module_id) THEN CONTINUE;END IF;
  module:=jsonb_build_object('documentId',owner.doc_id,'moduleId',owner.module_id,'documentRevision',owner.doc_revision,'documentSha256',owner.content_sha256,
   'types',(SELECT coalesce(jsonb_agg(jsonb_build_object('typeId',t.type_id,'recordId',t.element,'kind',t.kind,'provisional',t.provisional) ORDER BY t.type_id),'[]') FROM truss.type_def t WHERE t.document_id=owner.doc_id AND t.module=owner.module_id AND t.retired_rev IS NULL),
   'properties',(SELECT coalesce(jsonb_agg(jsonb_build_object('propertyId',p.prop_id,'typeId',p.type_id,'fieldId',p.element,'name',p.name,'scalarType',p.scalar_type,'nullability',p.nullability,'cardinality',p.cardinality,'itemDefinition',p.item-'declaration') ORDER BY p.prop_id),'[]') FROM truss.prop_def p JOIN truss.type_def t USING(type_id) WHERE t.document_id=owner.doc_id AND t.module=owner.module_id AND t.retired_rev IS NULL AND p.retired_rev IS NULL AND truss.runtime_can_read(t.document_id,p.declaration_module) AND (p.cardinality NOT IN ('array','map') OR truss.runtime_can_read(p.item->>'documentId',p.item->'reference'->>'module'))),
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
   SELECT p.item->>'documentId',p.item->'reference'->>'module'
    FROM jsonb_array_elements(modules) m CROSS JOIN LATERAL jsonb_array_elements(m.value->'properties') f
    JOIN truss.prop_def p ON p.prop_id=(f.value->>'propertyId')::int WHERE p.cardinality IN ('array','map')
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
 IF source->>'documentRevision' IS DISTINCT FROM archive.doc_revision OR source->'artifact'->>'sha256' IS DISTINCT FROM archive.content_sha256 OR decode(source->'artifact'->>'bytesBase64','base64') IS DISTINCT FROM convert_to(archive.document,'UTF8') THEN RAISE EXCEPTION 'original accepted source required' USING ERRCODE='55000';END IF;
 encoded:=convert_to(jsonb_build_object('documentId',selected_document,'documentRevision',archive.doc_revision,'artifactIdentity',source->'artifact'->>'identity','contentBase64',encode(convert_to(archive.document,'UTF8'),'base64'),'sha256',archive.content_sha256,'catalogRevision',captured_revision,'sourceCatalogRevision',archive.rev,'registrationId',request.registration_id::text)::text,'UTF8');
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
