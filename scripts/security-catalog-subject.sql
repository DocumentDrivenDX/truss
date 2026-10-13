-- Owned fixture: private role-OID/Staff-key issuer table, never PUBLIC data.
CREATE FUNCTION truss.catalog_subject_current(actor text) RETURNS TABLE(staff_id text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_subject_map IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_runtime_installation IN SHARE MODE NOWAIT;
 RETURN QUERY SELECT o.props->p.prop_id::text->>'text'
 FROM truss.catalog_subject_map m JOIN pg_catalog.pg_roles r ON r.oid OPERATOR(pg_catalog.=) m.role_oid
 JOIN truss.type_def t ON t.document_id OPERATOR(pg_catalog.=) 'domain' AND t.module OPERATOR(pg_catalog.=) 'm' AND t.element OPERATOR(pg_catalog.=) 'Staff'
 JOIN truss.prop_def p ON p.type_id OPERATOR(pg_catalog.=) t.type_id AND p.definition_document_id OPERATOR(pg_catalog.=) 'domain' AND p.declaration_module OPERATOR(pg_catalog.=) 'm' AND p.element OPERATOR(pg_catalog.=) 'staffId'
 JOIN truss.object o ON o.type_id OPERATOR(pg_catalog.=) t.type_id
 WHERE actor OPERATOR(pg_catalog.=) SESSION_USER::text AND r.rolname OPERATOR(pg_catalog.=) SESSION_USER AND NOT r.rolsuper AND NOT r.rolbypassrls
 AND t.kind OPERATOR(pg_catalog.=) 'record' AND NOT t.provisional AND t.retired_rev IS NULL AND p.retired_rev IS NULL
 AND p.home OPERATOR(pg_catalog.=) 'json' AND p.scalar_type OPERATOR(pg_catalog.=) 'string' AND p.cardinality OPERATOR(pg_catalog.=) 'one' AND p.nullability OPERATOR(pg_catalog.=) 'required'
 AND o.root_id IS NULL AND pg_catalog.jsonb_typeof(o.props->p.prop_id::text) OPERATOR(pg_catalog.=) 'object'
 AND o.props->p.prop_id::text->>'kind' OPERATOR(pg_catalog.=) 'string' AND pg_catalog.jsonb_typeof(o.props->p.prop_id::text->'text') OPERATOR(pg_catalog.=) 'string'
 AND o.props->p.prop_id::text->>'text' OPERATOR(pg_catalog.=) m.staff_key;
END;
$$;
CREATE FUNCTION truss.catalog_subject_context(actor text) RETURNS TABLE(installation_id text,database_oid text,role_oid text)
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
 SELECT i.installation_id::text,(SELECT d.oid::text FROM pg_catalog.pg_database d WHERE d.datname OPERATOR(pg_catalog.=) pg_catalog.current_database()),r.oid::text
 FROM truss.catalog_runtime_installation i CROSS JOIN pg_catalog.pg_roles r JOIN truss.catalog_subject_map m ON m.role_oid OPERATOR(pg_catalog.=) r.oid
 WHERE i.singleton AND actor OPERATOR(pg_catalog.=) SESSION_USER::text AND r.rolname OPERATOR(pg_catalog.=) SESSION_USER AND NOT r.rolsuper AND NOT r.rolbypassrls;
$$;
REVOKE ALL ON FUNCTION truss.catalog_subject_current(text),truss.catalog_subject_context(text) FROM PUBLIC;
