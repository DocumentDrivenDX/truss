-- Fixed, independently authorized query sources; no arbitrary SQL gateway.
CREATE FUNCTION truss.query_scope(binding jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;selected_document jsonb;selected_record jsonb;selected_field jsonb;source truss.schema_doc%ROWTYPE;owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;module jsonb;
BEGIN
 PERFORM truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF jsonb_typeof(binding) IS DISTINCT FROM 'object' OR binding->>'interfaceVersion' IS DISTINCT FROM 'truss-runtime-binding/0.1'
 OR binding->>'schema' IS DISTINCT FROM 'truss' OR binding->>'installationId' IS DISTINCT FROM installation.installation_id::text
 OR binding->>'releaseId' IS DISTINCT FROM installation.release_id OR binding->>'releaseSha256' IS DISTINCT FROM installation.release_sha256
 OR installation.release_id<>'truss-catalog-runtime/0.26-candidate' OR (binding->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
 OR binding->>'maximumResultRows' IS NULL OR (binding->>'maximumResultRows')::int NOT BETWEEN 1 AND 10000 OR binding->>'maximumScanRows' IS NULL OR binding->>'maximumBytes' IS NULL OR (binding->>'maximumScanRows')::int NOT BETWEEN 1 AND 10000 OR (binding->>'maximumBytes')::int NOT BETWEEN 1 AND 16777216
 OR octet_length(binding::text)>4194304 OR jsonb_typeof(binding->'documents') IS DISTINCT FROM 'array' OR jsonb_array_length(binding->'documents') NOT BETWEEN 1 AND 32
 OR jsonb_typeof(binding->'records') IS DISTINCT FROM 'array' OR jsonb_array_length(binding->'records') NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'selected query context required' USING ERRCODE='0A000';END IF;
 FOR selected_document IN SELECT value FROM jsonb_array_elements(binding->'documents') LOOP
  SELECT * INTO source FROM truss.schema_doc d WHERE d.doc_id=selected_document->>'documentId' AND d.rev<= (binding->>'catalogRevision')::int ORDER BY d.rev DESC LIMIT 1;
  IF NOT FOUND OR source.doc_revision IS DISTINCT FROM selected_document->>'revision' OR source.content_sha256 IS DISTINCT FROM selected_document->>'sha256' THEN RAISE EXCEPTION 'original query source changed' USING ERRCODE='55P03';END IF;
  -- Full original source bytes are supplied only under complete selected_document scope.
  FOR module IN SELECT value FROM jsonb_array_elements(source.document::jsonb->'modules') LOOP
   IF NOT truss.runtime_can_read(source.doc_id,module->>'id') THEN RAISE EXCEPTION 'complete selected_document reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 END LOOP;
 FOR selected_record IN SELECT value FROM jsonb_array_elements(binding->'records') LOOP
  SELECT * INTO owner FROM truss.type_def t WHERE t.type_id=(selected_record->>'typeId')::int AND t.retired_rev IS NULL AND NOT t.provisional AND t.kind='record';
  IF NOT FOUND OR owner.document_id IS DISTINCT FROM selected_record->'identity'->>'documentId' OR owner.module IS DISTINCT FROM selected_record->'identity'->>'module' OR owner.element IS DISTINCT FROM selected_record->'identity'->>'element'
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'documents') d WHERE d.value->>'documentId'=owner.document_id AND d.value->>'revision'=selected_record->'identity'->>'revision')
   OR NOT truss.runtime_can_read(owner.document_id,owner.module) THEN RAISE EXCEPTION 'accepted authorized query record required' USING ERRCODE='42501';END IF;
  IF jsonb_typeof(selected_record->'fields') IS DISTINCT FROM 'array' OR jsonb_array_length(selected_record->'fields')<>(SELECT count(*) FROM truss.prop_def p WHERE p.type_id=owner.type_id AND p.retired_rev IS NULL)
   OR (SELECT count(DISTINCT f.value->>'propertyId') FROM jsonb_array_elements(selected_record->'fields') f)<>jsonb_array_length(selected_record->'fields') THEN RAISE EXCEPTION 'complete property mapping required' USING ERRCODE='0A000';END IF;
  FOR selected_field IN SELECT value FROM jsonb_array_elements(selected_record->'fields') LOOP
   SELECT * INTO property FROM truss.prop_def p WHERE p.type_id=owner.type_id AND p.prop_id=(selected_field->>'propertyId')::int AND p.retired_rev IS NULL;
   IF NOT FOUND OR property.element IS DISTINCT FROM selected_field->'identity'->>'element' OR property.declaration_module IS DISTINCT FROM selected_field->'identity'->>'module'
    OR selected_field->'identity'->>'documentId' IS DISTINCT FROM owner.document_id OR selected_field->'identity'->>'revision' IS DISTINCT FROM selected_record->'identity'->>'revision'
    OR NOT truss.runtime_can_read(owner.document_id,property.declaration_module) THEN RAISE EXCEPTION 'accepted authorized property mapping required' USING ERRCODE='42501';END IF;
  END LOOP;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_scope(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_binding(selected_documents jsonb,maximum_scan_rows int,maximum_result_rows int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;captured_revision int;selected_document_id text;archived jsonb;content text;source jsonb;modules jsonb:='[]';pins jsonb:='[]';records jsonb:='[]';binding jsonb;result bytea;
BEGIN
 PERFORM truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN RAISE EXCEPTION 'selected query release required' USING ERRCODE='0A000';END IF;
 IF maximum_scan_rows IS NULL OR maximum_scan_rows NOT BETWEEN 1 AND 10000 OR maximum_result_rows IS NULL OR maximum_result_rows NOT BETWEEN 1 AND 10000 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216
 OR jsonb_typeof(selected_documents) IS DISTINCT FROM 'array' OR jsonb_array_length(selected_documents) NOT BETWEEN 1 AND 32
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(selected_documents) v WHERE jsonb_typeof(v.value)<>'string')
 OR (SELECT count(DISTINCT v.value) FROM jsonb_array_elements(selected_documents) v)<>jsonb_array_length(selected_documents) THEN RAISE EXCEPTION 'bounded original document selection required' USING ERRCODE='22023';END IF;
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 FOR selected_document_id IN SELECT value FROM jsonb_array_elements_text(selected_documents) LOOP
  archived:=convert_from(truss.accepted_document(selected_document_id,maximum_bytes,expected_release,expected_digest),'UTF8')::jsonb;
  content:=convert_from(decode(archived->>'contentBase64','base64'),'UTF8');source:=content::jsonb;
  pins:=pins||jsonb_build_array(jsonb_build_object('documentId',selected_document_id,'revision',archived->>'documentRevision','sha256',archived->>'sha256'));
  modules:=modules||jsonb_build_array(jsonb_build_object('documentJson',content,'pin',jsonb_build_object('documentId',selected_document_id,'revision',archived->>'documentRevision','sha256',archived->>'sha256','umfVersion',source->>'umf'),
   'selectedModuleIds',(SELECT jsonb_agg(m.value->>'id' ORDER BY m.value->>'id') FROM jsonb_array_elements(source->'modules') m)));
  records:=records||coalesce((SELECT jsonb_agg(jsonb_build_object('identity',jsonb_build_object('documentId',t.document_id,'revision',archived->>'documentRevision','module',t.module,'element',t.element),'typeId',t.type_id::text,
    'fields',(SELECT coalesce(jsonb_agg(jsonb_build_object('identity',jsonb_build_object('documentId',t.document_id,'revision',archived->>'documentRevision','module',p.declaration_module,'element',p.element),'propertyId',p.prop_id::text) ORDER BY p.prop_id),'[]') FROM truss.prop_def p WHERE p.type_id=t.type_id AND p.retired_rev IS NULL)) ORDER BY t.type_id)
    FROM truss.type_def t WHERE t.document_id=selected_document_id AND t.retired_rev IS NULL AND NOT t.provisional AND t.kind='record'),'[]');
 END LOOP;
 binding:=jsonb_build_object('interfaceVersion','truss-runtime-binding/0.1','schema','truss','installationId',installation.installation_id::text,'releaseId',installation.release_id,'releaseSha256',installation.release_sha256,'catalogRevision',captured_revision,
 'documents',pins,'records',records,'maximumScanRows',maximum_scan_rows,'maximumResultRows',maximum_result_rows,'maximumBytes',maximum_bytes);
 PERFORM truss.query_scope(binding);
 result:=convert_to(jsonb_build_object('binding',binding,'bindingJson',binding::text,'modules',modules,'actorOid',(SELECT oid::text FROM pg_roles WHERE rolname=session_user))::text,'UTF8');
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'query binding byte limit' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_binding(jsonb,int,int,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.query_objects(binding jsonb,selected_type int) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE owner truss.type_def%ROWTYPE;object_row truss.object%ROWTYPE;property truss.prop_def%ROWTYPE;cell jsonb;row_count int:=0;byte_count bigint:=0;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type) THEN RAISE EXCEPTION 'selected query record required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=selected_type AND t.retired_rev IS NULL;
 FOR property IN SELECT * FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL LOOP
  IF property.scalar_type NOT IN ('string','boolean','integer') OR property.cardinality IS DISTINCT FROM 'one' OR property.home<>'json' OR property.item IS NOT NULL
   OR coalesce(property.facets,'{}')<>'{}'::jsonb OR property.nullability NOT IN ('required','absent-allowed') THEN RAISE EXCEPTION 'query scalar profile unavailable' USING ERRCODE='0A000';END IF;
 END LOOP;
 FOR object_row IN SELECT * FROM truss.object o WHERE o.type_id=selected_type ORDER BY o.id LIMIT (binding->>'maximumScanRows')::int+1 LOOP
  row_count:=row_count+1;byte_count:=byte_count+octet_length(object_row.props::text);
  IF row_count>(binding->>'maximumScanRows')::int OR byte_count>(binding->>'maximumBytes')::int THEN RAISE EXCEPTION 'bounded query source required' USING ERRCODE='54000';END IF;
  IF object_row.root_id IS NOT NULL OR object_row.ver<=0 OR object_row.rev> (binding->>'catalogRevision')::int
   OR EXISTS(SELECT 1 FROM truss.row_home_state s WHERE s.object_id=object_row.id AND s.object_type_id=object_row.type_id)
   OR EXISTS(SELECT 1 FROM jsonb_object_keys(object_row.props) k WHERE NOT EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.prop_id::text=k)) THEN RAISE EXCEPTION 'complete scalar source required' USING ERRCODE='0A000';END IF;
  FOR property IN SELECT * FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL LOOP
   cell:=object_row.props->property.prop_id::text;
   IF cell IS NULL THEN IF property.nullability='required' THEN RAISE EXCEPTION 'required query value missing' USING ERRCODE='55000';END IF;
   ELSIF truss.valid_scalar_cell(cell,property.scalar_type,property.nullability='absent-allowed') IS NOT TRUE THEN RAISE EXCEPTION 'malformed query scalar' USING ERRCODE='55000';
   ELSIF property.scalar_type='integer' AND cell->>'kind'<>'null' AND NOT pg_input_is_valid(cell->>'text','numeric') THEN RAISE EXCEPTION 'exact native numeric domain unavailable' USING ERRCODE='0A000';END IF;
  END LOOP;
  id:=object_row.id;props:=object_row.props;RETURN NEXT;
 END LOOP;
 -- PL/pgSQL buffers this complete validated source before caller predicates run.
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_objects(jsonb,int) FROM PUBLIC;
