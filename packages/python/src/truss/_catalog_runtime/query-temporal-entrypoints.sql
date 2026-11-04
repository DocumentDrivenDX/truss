-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Exact F7 public native entrypoints. Inventory/grants must come from the
-- authentic completed native0.76 installer, not a relabelled0.75 inventory.
CREATE FUNCTION truss.person_query_temporal_binding(selected_documents jsonb,maximum_scan_rows int,maximum_result_rows int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_temporal_binding(jsonb,int,int,int,text,text)'::regprocedure,'read');
 RETURN truss.query_temporal_binding(selected_documents,maximum_scan_rows,maximum_result_rows,maximum_bytes,expected_release,expected_digest);
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_temporal_binding(jsonb,int,int,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_query_temporal_objects(binding jsonb,selected_type int,requirements jsonb) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_temporal_objects(jsonb,int,jsonb)'::regprocedure,'read');
 RETURN QUERY SELECT * FROM truss.query_temporal_objects(binding,selected_type,requirements);
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_temporal_objects(jsonb,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.person_query_temporal_page_objects(binding jsonb,selected_type int,selected_key text,requirements jsonb) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_temporal_page_objects(jsonb,int,text,jsonb)'::regprocedure,'read');
 RETURN QUERY SELECT * FROM truss.query_temporal_page_objects(binding,selected_type,selected_key,requirements);
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_temporal_page_objects(jsonb,int,text,jsonb) FROM PUBLIC;
