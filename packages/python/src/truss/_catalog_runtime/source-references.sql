-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Storage projections and original-source references; no retained schema copies.
CREATE FUNCTION truss.runtime_owned_catalog_declarations(documents_bytes bytea) RETURNS bytea
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 WITH documents AS MATERIALIZED (
  SELECT d.value->>'documentId' document_id,(d.value->>'originalText')::jsonb source,d.ordinality document_ordinal
  FROM jsonb_array_elements(convert_from(documents_bytes,'UTF8')::jsonb) WITH ORDINALITY d),
 modules AS MATERIALIZED (
  SELECT d.document_id,d.document_ordinal,m.value->>'id' module_id,m.value->'elements' module_elements,m.value->'relationships' module_relationships,m.ordinality module_ordinal
  FROM documents d CROSS JOIN LATERAL jsonb_array_elements(d.source->'modules') WITH ORDINALITY m),
 elements AS MATERIALIZED (
  SELECT m.document_id,m.document_ordinal,m.module_id,m.module_ordinal,e.value element,e.ordinality element_ordinal
  FROM modules m CROSS JOIN LATERAL jsonb_array_elements(m.module_elements) WITH ORDINALITY e),
 fields AS (
  SELECT r.document_ordinal,r.module_ordinal,r.element_ordinal,
   jsonb_agg(jsonb_build_object('fieldModule',ref.value->>'module','fieldId',ref.value->>'element',
    'reference',ref.value,'declaration',f.element) ORDER BY ref.ordinality) value
  FROM elements r CROSS JOIN LATERAL jsonb_array_elements(r.element->'members') WITH ORDINALITY ref
  JOIN elements f ON f.document_ordinal=r.document_ordinal AND f.module_id=ref.value->>'module' AND f.element->>'id'=ref.value->>'element'
  WHERE r.element->>'kind'='record' GROUP BY r.document_ordinal,r.module_ordinal,r.element_ordinal),
 records AS (
  SELECT r.document_ordinal,jsonb_agg(jsonb_build_object('documentId',r.document_id,'moduleId',r.module_id,
   'elementId',r.element->>'id','declaration',r.element,'membership',CASE WHEN r.element ? 'members' THEN 'declared' ELSE 'missing' END,
   'fields',coalesce(f.value,'[]'::jsonb),'keys',coalesce(r.element->'keys','[]'::jsonb)) ORDER BY r.module_ordinal,r.element_ordinal) value
  FROM elements r LEFT JOIN fields f USING(document_ordinal,module_ordinal,element_ordinal)
  WHERE r.element->>'kind'='record' GROUP BY r.document_ordinal),
 relationships AS (
  SELECT m.document_ordinal,jsonb_agg(jsonb_build_object('documentId',m.document_id,'moduleId',m.module_id,'declaration',r.value)
   ORDER BY m.module_ordinal,r.ordinality) value
  FROM modules m CROSS JOIN LATERAL jsonb_array_elements(m.module_relationships) WITH ORDINALITY r GROUP BY m.document_ordinal)
 SELECT convert_to(coalesce(jsonb_agg(jsonb_build_object('records',coalesce(r.value,'[]'::jsonb),
  'relationships',coalesce(rel.value,'[]'::jsonb),'scope','original_declaration_correspondence_only') ORDER BY d.document_ordinal),'[]'::jsonb)::text,'UTF8')
 FROM documents d LEFT JOIN records r USING(document_ordinal) LEFT JOIN relationships rel USING(document_ordinal);
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_catalog_declarations(bytea) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_request_documents(request truss.catalog_registration_request) RETURNS bytea
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result bytea;
BEGIN
 IF octet_length(request.document_bytes)>0 THEN RETURN request.document_bytes;END IF;
 SELECT convert_to(coalesce(jsonb_agg(jsonb_build_object('documentId',d.doc_id,'revision',d.doc_revision,
  'umfVersion',d.umf_version,'originalText',d.document,'validation',d.validation) ORDER BY d.ord),'[]'::jsonb)::text,'UTF8')
 INTO result FROM truss.schema_doc d WHERE d.rev=request.revision;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_request_documents(truss.catalog_registration_request) FROM PUBLIC;

CREATE FUNCTION truss.runtime_owned_request_declarations(request truss.catalog_registration_request) RETURNS bytea
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT CASE WHEN octet_length(request.declaration_bytes)>0 THEN request.declaration_bytes
 ELSE truss.runtime_owned_catalog_declarations(truss.runtime_owned_request_documents(request)) END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_request_declarations(truss.catalog_registration_request) FROM PUBLIC;
