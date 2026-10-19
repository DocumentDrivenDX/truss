-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Selected graph Subject metadata only; no target argument or resource exporter.
CREATE FUNCTION truss.graph_subject_current()
RETURNS TABLE(staff_key pg_catalog.text,installation_id pg_catalog.text,database_oid pg_catalog.text,role_oid pg_catalog.text,profile_sha256 pg_catalog.text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF pg_catalog.current_setting('role') OPERATOR(pg_catalog.<>) 'none'
  OR pg_catalog.current_setting('transaction_isolation') OPERATOR(pg_catalog.<>) 'read committed'
  OR pg_catalog.current_setting('transaction_read_only') OPERATOR(pg_catalog.<>) 'off' THEN
  RAISE EXCEPTION 'original fresh graph Subject caller required' USING ERRCODE='55000';
 END IF;
 LOCK TABLE ONLY truss.catalog_graph_subject_profile IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_subject_map IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.schema_head IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.schema_doc IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.type_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.prop_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.key_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_runtime_installation IN SHARE MODE NOWAIT;
 RETURN QUERY SELECT m.staff_key,i.installation_id::pg_catalog.text,
  (SELECT d.oid::pg_catalog.text FROM pg_catalog.pg_database d WHERE d.datname OPERATOR(pg_catalog.=) pg_catalog.current_database()),
  r.oid::pg_catalog.text,pg_catalog.encode(pg_catalog.sha256(p.profile_bytes),'hex')
 FROM ONLY truss.catalog_graph_subject_profile p
 JOIN ONLY truss.catalog_runtime_installation i ON i.singleton AND i.installation_id OPERATOR(pg_catalog.=) p.installation_id
 JOIN pg_catalog.pg_roles r ON r.rolname OPERATOR(pg_catalog.=) SESSION_USER
 JOIN ONLY truss.catalog_subject_map m ON m.role_oid OPERATOR(pg_catalog.=) r.oid
 JOIN ONLY truss.schema_head h ON h.id OPERATOR(pg_catalog.=) 1 AND h.rev OPERATOR(pg_catalog.=) p.native_revision
 JOIN ONLY truss.schema_doc d ON d.rev OPERATOR(pg_catalog.=) p.native_revision AND d.doc_id OPERATOR(pg_catalog.=) p.document_id AND d.doc_revision OPERATOR(pg_catalog.=) p.document_revision AND d.content_sha256 OPERATOR(pg_catalog.=) p.document_sha256
 JOIN ONLY truss.type_def t ON t.type_id OPERATOR(pg_catalog.=) p.type_id AND t.document_id OPERATOR(pg_catalog.=) p.document_id AND t.module OPERATOR(pg_catalog.=) p.module_id AND t.element OPERATOR(pg_catalog.=) 'Staff'
 JOIN ONLY truss.prop_def f ON f.type_id OPERATOR(pg_catalog.=) t.type_id AND f.prop_id OPERATOR(pg_catalog.=) p.property_id AND f.definition_document_id OPERATOR(pg_catalog.=) p.document_id AND f.declaration_module OPERATOR(pg_catalog.=) p.module_id AND f.element OPERATOR(pg_catalog.=) 'staffId'
 JOIN ONLY truss.key_def k ON k.type_id OPERATOR(pg_catalog.=) t.type_id AND k.key_id OPERATOR(pg_catalog.=) 'pk' AND k.prop_ids OPERATOR(pg_catalog.=) ARRAY[p.property_id]
 JOIN ONLY truss.object o ON o.type_id OPERATOR(pg_catalog.=) t.type_id AND o.root_id IS NULL
 WHERE p.singleton OPERATOR(pg_catalog.=) 1 AND r.rolcanlogin AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole AND NOT r.rolreplication AND NOT r.rolbypassrls
 AND NOT pg_catalog.pg_has_role(r.oid,i.owner_oid,'MEMBER')
 AND t.kind OPERATOR(pg_catalog.=) 'record' AND NOT t.provisional AND t.retired_rev IS NULL AND f.retired_rev IS NULL AND k.retired_rev IS NULL
 AND f.home OPERATOR(pg_catalog.=) 'json' AND f.scalar_type OPERATOR(pg_catalog.=) 'string' AND f.cardinality OPERATOR(pg_catalog.=) 'one' AND f.nullability OPERATOR(pg_catalog.=) 'required'
 AND pg_catalog.jsonb_typeof(o.props OPERATOR(pg_catalog.->) p.property_id::pg_catalog.text) OPERATOR(pg_catalog.=) 'object'
 AND (o.props OPERATOR(pg_catalog.->) p.property_id::pg_catalog.text) OPERATOR(pg_catalog.->>) 'kind' OPERATOR(pg_catalog.=) 'string'
 AND pg_catalog.jsonb_typeof((o.props OPERATOR(pg_catalog.->) p.property_id::pg_catalog.text) OPERATOR(pg_catalog.->) 'text') OPERATOR(pg_catalog.=) 'string'
 AND ((o.props OPERATOR(pg_catalog.->) p.property_id::pg_catalog.text) OPERATOR(pg_catalog.->>) 'text') COLLATE pg_catalog."C" OPERATOR(pg_catalog.=) m.staff_key;
END;
$$;
REVOKE ALL ON FUNCTION truss.graph_subject_current() FROM PUBLIC;
