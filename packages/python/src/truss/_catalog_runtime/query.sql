-- Pure stock-PostgreSQL exact numeric input domain, never typmod coercion.
-- Explicit UMF CONTRACT-065 instant recipe; retain original cells/parameter text.
CREATE FUNCTION truss.query_timestamp_instant_key(token text,profile text) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE calendar date;whole_seconds bigint;offset_text text;offset_minutes int:=0;fraction text;
BEGIN
 IF profile IS DISTINCT FROM 'umf-rfc3339-exact-instant/1.0.0' THEN
  RAISE EXCEPTION 'selected exact instant profile required' USING ERRCODE='22023';END IF;
 IF token IS NULL THEN RETURN NULL;END IF;
 IF octet_length(token)>1048576 OR token !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?([Zz]|[+-][0-9]{2}:[0-9]{2})$'
  OR substring(token,1,4)::int=0 OR substring(token,12,2)::int>23 OR substring(token,15,2)::int>59 OR substring(token,18,2)::int>59 THEN
  RAISE EXCEPTION 'selected exact instant token required' USING ERRCODE='22023';END IF;
 calendar:=make_date(substring(token,1,4)::int,substring(token,6,2)::int,substring(token,9,2)::int);
 IF lower(right(token,1))<>'z' THEN
  offset_text:=right(token,6);
  IF substring(offset_text,2,2)::int>23 OR substring(offset_text,5,2)::int>59 THEN
   RAISE EXCEPTION 'selected exact instant offset required' USING ERRCODE='22023';END IF;
  offset_minutes:=(substring(offset_text,2,2)::int*60+substring(offset_text,5,2)::int)
   * CASE WHEN left(offset_text,1)='-' THEN -1 ELSE 1 END;
 END IF;
 whole_seconds:=(calendar-DATE '1970-01-01')::bigint*86400
  +substring(token,12,2)::int*3600+substring(token,15,2)::int*60+substring(token,18,2)::int-offset_minutes*60;
 fraction:=CASE WHEN substring(token,20,1)='.' THEN substring(token,21,length(token)-20-CASE WHEN lower(right(token,1))='z' THEN 1 ELSE 6 END) ELSE '' END;
 RETURN jsonb_build_array(whole_seconds::text,rtrim(fraction,'0'));
END;
$$;
REVOKE ALL ON FUNCTION truss.query_timestamp_instant_key(text,text) FROM PUBLIC;

CREATE FUNCTION truss.query_numeric_value(token text,family text) RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE mantissa text;exponent_text text;exponent_value int:=0;fraction_length int;coefficient text;scale_value int;magnitude int;
BEGIN
 IF token IS NULL OR family IS NULL OR octet_length(token)>1048576 THEN RETURN false;END IF;
 IF family='integer' THEN
  IF token !~ '^-?(0|[1-9][0-9]*)$' OR length(ltrim(ltrim(token,'-'),'0'))>131072 THEN RETURN false;END IF;
 ELSIF family='decimal' THEN
  IF token !~ '^-?(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)?$' THEN RETURN false;END IF;
  exponent_text:=substring(token from '[eE]([+-]?[0-9]+)$');
  IF exponent_text IS NOT NULL THEN
   IF length(exponent_text)>7 THEN RETURN false;END IF;
   exponent_value:=exponent_text::int;
  END IF;
  mantissa:=regexp_replace(ltrim(token,'-'),'[eE].*$','');
  fraction_length:=length(split_part(mantissa,'.',2));
  coefficient:=ltrim(replace(mantissa,'.',''),'0');
  scale_value:=fraction_length-exponent_value;
  magnitude:=length(coefficient)-scale_value;
  IF greatest(scale_value,0)>16383 OR magnitude>131072 THEN RETURN false;END IF;
 ELSE RETURN false;END IF;
 -- The lexical bounds prevent any implicit scale reduction at native input.
 RETURN pg_input_is_valid(token,'pg_catalog.numeric');
END;
$$;
REVOKE ALL ON FUNCTION truss.query_numeric_value(text,text) FROM PUBLIC;

-- Fixed, independently authorized query sources; no arbitrary SQL gateway.
CREATE FUNCTION truss.query_scope(binding jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;selected_document jsonb;selected_record jsonb;selected_field jsonb;source truss.schema_doc%ROWTYPE;owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;module jsonb;selected_relation jsonb;relation truss.rel_def%ROWTYPE;selected_key jsonb;key_definition truss.key_def%ROWTYPE;
BEGIN
 PERFORM truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF jsonb_typeof(binding) IS DISTINCT FROM 'object' OR binding->>'interfaceVersion' IS DISTINCT FROM 'truss-runtime-binding/0.4'
 OR binding->>'schema' IS DISTINCT FROM 'truss' OR binding->>'installationId' IS DISTINCT FROM installation.installation_id::text
 OR binding->>'releaseId' IS DISTINCT FROM installation.release_id OR binding->>'releaseSha256' IS DISTINCT FROM installation.release_sha256
 OR installation.release_id<>'truss-catalog-runtime/0.61-candidate' OR (binding->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
 OR binding->>'maximumResultRows' IS NULL OR (binding->>'maximumResultRows')::int NOT BETWEEN 1 AND 10000 OR binding->>'maximumScanRows' IS NULL OR binding->>'maximumBytes' IS NULL OR (binding->>'maximumScanRows')::int NOT BETWEEN 1 AND 10000 OR (binding->>'maximumBytes')::int NOT BETWEEN 1 AND 16777216
 OR octet_length(binding::text)>4194304 OR jsonb_typeof(binding->'documents') IS DISTINCT FROM 'array' OR jsonb_array_length(binding->'documents') NOT BETWEEN 1 AND 32
 OR jsonb_typeof(binding->'relationships') IS DISTINCT FROM 'array' OR jsonb_array_length(binding->'relationships')>1024
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
  IF truss.runtime_object_values_readable(owner.type_id) IS NOT TRUE THEN RAISE EXCEPTION 'current query interpretation reader required' USING ERRCODE='42501';END IF;
  FOR selected_field IN SELECT value FROM jsonb_array_elements(selected_record->'fields') LOOP
   SELECT * INTO property FROM truss.prop_def p WHERE p.type_id=owner.type_id AND p.prop_id=(selected_field->>'propertyId')::int AND p.retired_rev IS NULL;
   IF NOT FOUND OR property.element IS DISTINCT FROM selected_field->'identity'->>'element' OR property.declaration_module IS DISTINCT FROM selected_field->'identity'->>'module'
    OR selected_field->'identity'->>'documentId' IS DISTINCT FROM owner.document_id OR selected_field->'identity'->>'revision' IS DISTINCT FROM selected_record->'identity'->>'revision'
    OR NOT truss.runtime_can_read(owner.document_id,property.declaration_module) THEN RAISE EXCEPTION 'accepted authorized property mapping required' USING ERRCODE='42501';END IF;
  END LOOP;
  IF jsonb_typeof(selected_record->'keys') IS DISTINCT FROM 'array' OR jsonb_array_length(selected_record->'keys')<>(SELECT count(*) FROM truss.key_def k WHERE k.type_id=owner.type_id AND k.retired_rev IS NULL)
   OR (SELECT count(DISTINCT k.value->>'keyId') FROM jsonb_array_elements(selected_record->'keys') k)<>jsonb_array_length(selected_record->'keys') THEN RAISE EXCEPTION 'complete current key mapping required' USING ERRCODE='0A000';END IF;
  FOR selected_key IN SELECT value FROM jsonb_array_elements(selected_record->'keys') LOOP
   SELECT * INTO key_definition FROM truss.key_def k WHERE k.type_id=owner.type_id AND k.key_id=selected_key->>'keyId' AND k.retired_rev IS NULL;
   IF NOT FOUND OR selected_key->'propertyIds' IS DISTINCT FROM (SELECT coalesce(jsonb_agg(p.prop_id::text ORDER BY p.n),'[]') FROM unnest(key_definition.prop_ids) WITH ORDINALITY p(prop_id,n)) THEN
    RAISE EXCEPTION 'exact ordered native key mapping required' USING ERRCODE='55000';END IF;
  END LOOP;
 END LOOP;
 FOR selected_relation IN SELECT value FROM jsonb_array_elements(binding->'relationships') LOOP
  SELECT * INTO relation FROM truss.rel_def r WHERE r.rel_type_id=(selected_relation->>'relationshipTypeId')::int AND r.retired_rev IS NULL;
  IF NOT FOUND OR relation.document_id IS DISTINCT FROM selected_relation->'identity'->>'documentId' OR relation.module IS DISTINCT FROM selected_relation->'identity'->>'module'
   OR relation.rel_id IS DISTINCT FROM selected_relation->'identity'->>'relationship' OR relation.lifecycle<>'independent' OR NOT relation.directed OR relation.composition OR relation.assoc_type_id IS NOT NULL
   OR NOT truss.runtime_can_read(relation.document_id,relation.module)
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'documents') d WHERE d.value->>'documentId'=relation.document_id AND d.value->>'revision'=selected_relation->'identity'->>'revision')
   OR (SELECT count(*) FROM truss.rel_endpoint e WHERE e.rel_type_id=relation.rel_type_id)<>1
   OR NOT EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=relation.rel_type_id AND e.source_type=(selected_relation->>'sourceTypeId')::int AND e.target_type=(selected_relation->>'targetTypeId')::int)
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE r.value->>'typeId'=selected_relation->>'sourceTypeId')
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE r.value->>'typeId'=selected_relation->>'targetTypeId') THEN
   RAISE EXCEPTION 'accepted authorized relationship mapping required' USING ERRCODE='42501';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_scope(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_binding(selected_documents jsonb,maximum_scan_rows int,maximum_result_rows int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;captured_revision int;selected_document_id text;archived jsonb;content text;source jsonb;modules jsonb:='[]';pins jsonb:='[]';records jsonb:='[]';relationships jsonb:='[]';binding jsonb;result bytea;
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
    'keys',(SELECT coalesce(jsonb_agg(jsonb_build_object('keyId',k.key_id,'propertyIds',(SELECT jsonb_agg(p.prop_id::text ORDER BY p.n) FROM unnest(k.prop_ids) WITH ORDINALITY p(prop_id,n))) ORDER BY k.key_num),'[]') FROM truss.key_def k WHERE k.type_id=t.type_id AND k.retired_rev IS NULL),
    'fields',(SELECT coalesce(jsonb_agg(jsonb_build_object('identity',jsonb_build_object('documentId',t.document_id,'revision',archived->>'documentRevision','module',p.declaration_module,'element',p.element),'propertyId',p.prop_id::text) ORDER BY p.prop_id),'[]') FROM truss.prop_def p WHERE p.type_id=t.type_id AND p.retired_rev IS NULL)) ORDER BY t.type_id)
    FROM truss.type_def t WHERE t.document_id=selected_document_id AND t.retired_rev IS NULL AND NOT t.provisional AND t.kind='record'),'[]');
  relationships:=relationships||coalesce((SELECT jsonb_agg(jsonb_build_object('identity',jsonb_build_object('documentId',r.document_id,'revision',archived->>'documentRevision','module',r.module,'relationship',r.rel_id),
   'relationshipTypeId',r.rel_type_id::text,'sourceTypeId',e.source_type::text,'targetTypeId',e.target_type::text) ORDER BY r.rel_type_id)
   FROM truss.rel_def r JOIN truss.rel_endpoint e ON e.rel_type_id=r.rel_type_id WHERE r.document_id=selected_document_id AND r.retired_rev IS NULL AND r.lifecycle='independent' AND r.directed AND NOT r.composition AND r.assoc_type_id IS NULL
   AND (SELECT count(*) FROM truss.rel_endpoint ep WHERE ep.rel_type_id=r.rel_type_id)=1),'[]');
 END LOOP;
 binding:=jsonb_build_object('interfaceVersion','truss-runtime-binding/0.4','schema','truss','installationId',installation.installation_id::text,'releaseId',installation.release_id,'releaseSha256',installation.release_sha256,'catalogRevision',captured_revision,
 'documents',pins,'records',records,'relationships',relationships,'maximumScanRows',maximum_scan_rows,'maximumResultRows',maximum_result_rows,'maximumBytes',maximum_bytes);
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
  IF truss.valid_property_definition(property) IS NOT TRUE THEN RAISE EXCEPTION 'query value profile unavailable' USING ERRCODE='0A000';END IF;
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
   ELSIF truss.valid_property_value(cell,property) IS NOT TRUE THEN RAISE EXCEPTION 'malformed query scalar' USING ERRCODE='55000';
   ELSIF property.scalar_type IN ('integer','decimal') AND cell->>'kind'<>'null' AND truss.query_numeric_value(cell->>'text',property.scalar_type) IS NOT TRUE THEN RAISE EXCEPTION 'exact native numeric domain unavailable' USING ERRCODE='22003';END IF;
  END LOOP;
  id:=object_row.id;props:=object_row.props;RETURN NEXT;
 END LOOP;
 -- PL/pgSQL buffers this complete validated source before caller predicates run.
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_objects(jsonb,int) FROM PUBLIC;


CREATE FUNCTION truss.query_edges(binding jsonb,selected_relationship int) RETURNS TABLE(id bigint,source_id bigint,target_id bigint)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE relation truss.rel_def%ROWTYPE;edge_row truss.edge%ROWTYPE;source_object truss.object%ROWTYPE;target_object truss.object%ROWTYPE;row_count int:=0;byte_count bigint:=0;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'relationships') r WHERE (r.value->>'relationshipTypeId')::int=selected_relationship) THEN RAISE EXCEPTION 'selected query relationship required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT relation FROM truss.rel_def r WHERE r.rel_type_id=selected_relationship AND r.retired_rev IS NULL;
 FOR edge_row IN SELECT * FROM truss.edge e WHERE e.rel_type_id=selected_relationship ORDER BY e.id LIMIT (binding->>'maximumScanRows')::int+1 LOOP
  row_count:=row_count+1;byte_count:=byte_count+octet_length(edge_row.props::text);
  IF row_count>(binding->>'maximumScanRows')::int OR byte_count>(binding->>'maximumBytes')::int THEN RAISE EXCEPTION 'bounded query edge source required' USING ERRCODE='54000';END IF;
  SELECT * INTO source_object FROM truss.object o WHERE o.id=edge_row.source_id AND o.type_id=edge_row.source_type;
  IF NOT FOUND THEN RAISE EXCEPTION 'query source endpoint missing' USING ERRCODE='55000';END IF;
  SELECT * INTO target_object FROM truss.object o WHERE o.id=edge_row.target_id AND o.type_id=edge_row.target_type;
  IF NOT FOUND OR edge_row.ver<=0 OR edge_row.rev>(binding->>'catalogRevision')::int OR source_object.ver<=0 OR target_object.ver<=0
   OR source_object.rev>(binding->>'catalogRevision')::int OR target_object.rev>(binding->>'catalogRevision')::int OR source_object.root_id IS NOT NULL OR target_object.root_id IS NOT NULL
   OR NOT EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=selected_relationship AND e.source_type=edge_row.source_type AND e.target_type=edge_row.target_type) THEN
   RAISE EXCEPTION 'complete independent query endpoints required' USING ERRCODE='55000';END IF;
  id:=edge_row.id;source_id:=edge_row.source_id;target_id:=edge_row.target_id;RETURN NEXT;
 END LOOP;
 -- Buffer the complete validated edge bag before correlation and key predicates.
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_edges(jsonb,int) FROM PUBLIC;


CREATE FUNCTION truss.query_page_objects(binding jsonb,selected_type int,selected_key text) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE key_definition truss.key_def%ROWTYPE;component truss.prop_def%ROWTYPE;row record;counted int:=0;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type) THEN RAISE EXCEPTION 'selected query record required' USING ERRCODE='42501';END IF;
 SELECT * INTO key_definition FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_id=selected_key AND k.retired_rev IS NULL;
 IF NOT FOUND OR cardinality(key_definition.prop_ids) NOT BETWEEN 1 AND 1024 THEN RAISE EXCEPTION 'bounded authored page key required' USING ERRCODE='0A000';END IF;
 FOR component IN SELECT p.* FROM unnest(key_definition.prop_ids) WITH ORDINALITY k(prop_id,n) JOIN truss.prop_def p ON p.prop_id=k.prop_id AND p.type_id=selected_type ORDER BY k.n LOOP
  counted:=counted+1;
  IF component.retired_rev IS NOT NULL OR component.scalar_type NOT IN ('string','boolean','integer','decimal') OR component.nullability<>'required' OR component.cardinality<>'one' OR component.home<>'json' OR NOT ((component.scalar_type IN ('string','boolean') AND coalesce(component.facets,'{}')='{}'::jsonb OR component.scalar_type='integer' AND (coalesce(component.facets,'{}')='{}'::jsonb OR component.facets='{"integerWidth":{"bits":64,"signed":true}}'::jsonb) OR component.scalar_type='decimal' AND component.facets IN ('{"precision":18,"scale":4}'::jsonb,'{"precision":18,"scale":2}'::jsonb)) IS TRUE) THEN RAISE EXCEPTION 'required exact page key components required' USING ERRCODE='0A000';END IF;
 END LOOP;
 IF counted<>cardinality(key_definition.prop_ids) THEN RAISE EXCEPTION 'complete page key required' USING ERRCODE='55000';END IF;
 FOR row IN SELECT q.* FROM truss.query_objects(binding,selected_type) q LOOP
  id:=row.id;props:=row.props;RETURN NEXT;
 END LOOP;
 -- The preceding SRF validates and bounds the complete source in this snapshot.
 -- Validated typed tuple equality matches emitted C-text/bool/numeric ROW.
 IF EXISTS(SELECT 1 FROM (SELECT (SELECT jsonb_agg(CASE property.scalar_type WHEN 'boolean' THEN o.props->property.prop_id::text->'value' WHEN 'integer' THEN to_jsonb((o.props->property.prop_id::text->>'text')::numeric) WHEN 'decimal' THEN to_jsonb((o.props->property.prop_id::text->>'text')::numeric) ELSE to_jsonb(o.props->property.prop_id::text->>'text') END ORDER BY p.n)
  FROM unnest(key_definition.prop_ids) WITH ORDINALITY p(prop_id,n) JOIN truss.prop_def property ON property.prop_id=p.prop_id AND property.type_id=selected_type) AS key_values
  FROM truss.object o WHERE o.type_id=selected_type) source GROUP BY source.key_values HAVING count(*)>1) THEN
  RAISE EXCEPTION 'unique authored page key required' USING ERRCODE='55000';END IF;
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_page_objects(jsonb,int,text) FROM PUBLIC;
