-- SPDX-License-Identifier: MIT OR Apache-2.0
-- PV1 finite original-person native invocation guards.

CREATE FUNCTION truss.person_temporal_group_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.temporal_group_context(text,text)'::regprocedure,'read');
 RETURN truss.temporal_group_context("expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_temporal_group_context(text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_apply_temporal_group(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.apply_temporal_group(bytea,bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.apply_temporal_group("original_input","original_documents","original_request","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_apply_temporal_group(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_apply_temporal_group_prepared(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text,app_prepared jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.apply_temporal_group_prepared(bytea,bytea,bytea,text,text,jsonb)'::regprocedure,'write');
 RETURN truss.apply_temporal_group_prepared("original_input","original_documents","original_request","expected_release","expected_digest","app_prepared");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_apply_temporal_group_prepared(bytea,bytea,bytea,text,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.person_temporal_import_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.temporal_import_context(text,text)'::regprocedure,'read');
 RETURN truss.temporal_import_context("expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_temporal_import_context(text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_temporal_import_key_selection(selected_document text,selected_module text,selected_record text,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.temporal_import_key_selection(text,text,text,text,text)'::regprocedure,'read');
 RETURN truss.temporal_import_key_selection("selected_document","selected_module","selected_record","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_temporal_import_key_selection(text,text,text,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_temporal_import_object_identity(original_identity bytea,original_document bytea,tuple_bytes bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.temporal_import_object_identity(bytea,bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.temporal_import_object_identity("original_identity","original_document","tuple_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_temporal_import_object_identity(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_temporal_writer_schema_basis(original_input bytea,original_documents bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.temporal_writer_schema_basis(bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.temporal_writer_schema_basis("original_input","original_documents","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_temporal_writer_schema_basis(bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_get_temporal_object(selected_document text,selected_module text,selected_record text,selected_id bigint,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.get_temporal_object(text,text,text,bigint,int,text,text)'::regprocedure,'read');
 RETURN truss.get_temporal_object("selected_document","selected_module","selected_record","selected_id","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_get_temporal_object(text,text,text,bigint,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_page_temporal_objects(selected_document text,selected_module text,selected_record text,page_limit int,maximum_bytes int,original_cursor bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.page_temporal_objects(text,text,text,int,int,bytea,text,text)'::regprocedure,'read');
 RETURN truss.page_temporal_objects("selected_document","selected_module","selected_record","page_limit","maximum_bytes","original_cursor","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_page_temporal_objects(text,text,text,int,int,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_lookup_temporal_key(selected_document text,selected_module text,selected_record text,selected_key text,original_document bytea,values_bytes bytea,tuple_bytes bytea,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.lookup_temporal_key(text,text,text,text,bytea,bytea,bytea,int,text,text)'::regprocedure,'read');
 RETURN truss.lookup_temporal_key("selected_document","selected_module","selected_record","selected_key","original_document","values_bytes","tuple_bytes","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_lookup_temporal_key(text,text,text,text,bytea,bytea,bytea,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_recover_temporal_group_request(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.recover_temporal_group_request(bytea,bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.recover_temporal_group_request("original_input","original_documents","original_request","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_recover_temporal_group_request(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.person_temporal_scope(expected_release text,expected_digest text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.temporal_scope(text,text)'::regprocedure,'read');
 PERFORM truss.temporal_scope("expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_temporal_scope(text,text) FROM PUBLIC;
