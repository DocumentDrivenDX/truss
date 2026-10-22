-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Denial-capable public invocations; private grants remain mandatory.
CREATE FUNCTION truss.require_person_invocation(original_function regprocedure,admission_kind text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE actor oid;enrolled boolean;installation truss.catalog_runtime_installation%ROWTYPE;original_owner oid;
BEGIN
 SELECT oid INTO STRICT actor FROM pg_roles WHERE rolname=session_user;
 IF admission_kind NOT IN ('read','write','catalog','registrar','audit','status') OR admission_kind IS NULL THEN
  RAISE EXCEPTION 'selected invocation family required' USING ERRCODE='22023';END IF;
 WITH RECURSIVE memberships(role_oid) AS (
  SELECT actor UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
 SELECT
  (admission_kind IN ('read','catalog','status') AND EXISTS(
    SELECT 1 FROM truss.module_access m JOIN memberships p
     ON p.role_oid IN (to_regrole(m.reader_role)::oid,to_regrole(m.writer_role)::oid)))
  OR (admission_kind='write' AND EXISTS(
    SELECT 1 FROM truss.module_access m JOIN memberships p ON p.role_oid=to_regrole(m.writer_role)::oid))
  OR (admission_kind IN ('catalog','registrar','status') AND EXISTS(
    SELECT 1 FROM truss.catalog_runtime_installation i JOIN memberships p ON p.role_oid=i.registrar_oid WHERE i.singleton))
  OR (admission_kind IN ('audit','status') AND EXISTS(
    SELECT 1 FROM truss.runtime_import_audit_access a JOIN memberships p ON p.role_oid=a.auditor_oid))
 INTO enrolled;
 -- No installation identity, role name, head or result is released on this path.
 IF enrolled IS DISTINCT FROM true THEN
  RAISE EXCEPTION 'current person invocation admission required' USING ERRCODE='P1403';END IF;
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation WHERE singleton;
 SELECT proowner INTO STRICT original_owner FROM pg_proc WHERE oid=original_function::oid;
 IF original_owner IS DISTINCT FROM installation.owner_oid
  OR (SELECT oid FROM pg_roles WHERE rolname=current_user) IS DISTINCT FROM installation.owner_oid THEN
  RAISE EXCEPTION 'original installed invocation owner required' USING ERRCODE='55000';END IF;
 IF NOT has_function_privilege(actor,original_function::oid,'EXECUTE') THEN
  RAISE EXCEPTION 'original invocation EXECUTE grant required' USING ERRCODE='42501';END IF;
 PERFORM truss.runtime_person(false);
END;
$$;
REVOKE ALL ON FUNCTION truss.require_person_invocation(regprocedure,text) FROM PUBLIC;

CREATE FUNCTION truss.person_accepted_document(selected_document text, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.accepted_document(text,integer,text,text)'::regprocedure,'catalog');
 RETURN truss.accepted_document("selected_document","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_accepted_document(selected_document text, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_apply_group(original_input bytea, original_documents bytea, original_request bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.apply_group(bytea,bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.apply_group("original_input","original_documents","original_request","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_apply_group(original_input bytea, original_documents bytea, original_request bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_apply_group_prepared(original_input bytea, original_documents bytea, original_request bytea, expected_release text, expected_digest text, app_prepared jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.apply_group_prepared(bytea,bytea,bytea,text,text,jsonb)'::regprocedure,'write');
 RETURN truss.apply_group_prepared("original_input","original_documents","original_request","expected_release","expected_digest","app_prepared");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_apply_group_prepared(original_input bytea, original_documents bytea, original_request bytea, expected_release text, expected_digest text, app_prepared jsonb) FROM PUBLIC;

CREATE FUNCTION truss.person_batched_import_context(expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.batched_import_context(text,text)'::regprocedure,'write');
 RETURN truss.batched_import_context("expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_batched_import_context(expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_build_import_records(original_drafts bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.build_import_records(bytea,text,text)'::regprocedure,'write');
 RETURN truss.build_import_records("original_drafts","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_build_import_records(original_drafts bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_catalog_accept_with_keys(input_bytes bytea, documents_bytes bytea, declarations_bytes bytea, source_bytes bytea, origin_bytes bytea, request_key text, key_receipts bytea, preview_mode boolean) RETURNS TABLE(revision text, registration_id text, report_bytes bytea, replayed boolean, unchanged boolean, actor_name text, violations_bytes bytea)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean)'::regprocedure,'registrar');
 RETURN QUERY SELECT * FROM truss.catalog_accept_with_keys("input_bytes","documents_bytes","declarations_bytes","source_bytes","origin_bytes","request_key","key_receipts","preview_mode");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_catalog_accept_with_keys(input_bytes bytea, documents_bytes bytea, declarations_bytes bytea, source_bytes bytea, origin_bytes bytea, request_key text, key_receipts bytea, preview_mode boolean) FROM PUBLIC;

CREATE FUNCTION truss.person_catalog_accept_with_keys(input_bytes bytea, documents_bytes bytea, declarations_bytes bytea, source_bytes bytea, origin_bytes bytea, request_key text, key_receipts bytea, preview_mode boolean, expected_revision integer, expected_documents bytea) RETURNS TABLE(revision text, registration_id text, report_bytes bytea, replayed boolean, unchanged boolean, actor_name text, violations_bytes bytea)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean,integer,bytea)'::regprocedure,'registrar');
 RETURN QUERY SELECT * FROM truss.catalog_accept_with_keys("input_bytes","documents_bytes","declarations_bytes","source_bytes","origin_bytes","request_key","key_receipts","preview_mode","expected_revision","expected_documents");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_catalog_accept_with_keys(input_bytes bytea, documents_bytes bytea, declarations_bytes bytea, source_bytes bytea, origin_bytes bytea, request_key text, key_receipts bytea, preview_mode boolean, expected_revision integer, expected_documents bytea) FROM PUBLIC;

CREATE FUNCTION truss.person_catalog_report(selected_revision integer) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.catalog_report(integer)'::regprocedure,'registrar');
 RETURN truss.catalog_report("selected_revision");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_catalog_report(selected_revision integer) FROM PUBLIC;

CREATE FUNCTION truss.person_catalog_revision(expected_release text, expected_digest text, selected_document text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.catalog_revision(text,text,text)'::regprocedure,'read');
 RETURN truss.catalog_revision("expected_release","expected_digest","selected_document");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_catalog_revision(expected_release text, expected_digest text, selected_document text) FROM PUBLIC;

CREATE FUNCTION truss.person_catalog_view_basis(selected_revision integer, maximum_count integer, maximum_bytes integer) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.catalog_view_basis(integer,integer,integer)'::regprocedure,'registrar');
 RETURN truss.catalog_view_basis("selected_revision","maximum_count","maximum_bytes");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_catalog_view_basis(selected_revision integer, maximum_count integer, maximum_bytes integer) FROM PUBLIC;

CREATE FUNCTION truss.person_get_edge(selected_document text, selected_module text, selected_relationship text, selected_id bigint, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.get_edge(text,text,text,bigint,integer,text,text)'::regprocedure,'read');
 RETURN truss.get_edge("selected_document","selected_module","selected_relationship","selected_id","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_get_edge(selected_document text, selected_module text, selected_relationship text, selected_id bigint, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_get_object(selected_document text, selected_module text, selected_record text, selected_id bigint, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.get_object(text,text,text,bigint,integer,text,text)'::regprocedure,'read');
 RETURN truss.get_object("selected_document","selected_module","selected_record","selected_id","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_get_object(selected_document text, selected_module text, selected_record text, selected_id bigint, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_group_context(expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.group_context(text,text)'::regprocedure,'read');
 RETURN truss.group_context("expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_group_context(expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_group_relationship_reference(selected_document text, selected_module text, selected_relationship text, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.group_relationship_reference(text,text,text,text,text)'::regprocedure,'read');
 RETURN truss.group_relationship_reference("selected_document","selected_module","selected_relationship","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_group_relationship_reference(selected_document text, selected_module text, selected_relationship text, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_group_type_reference(selected_document text, selected_module text, selected_record text, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.group_type_reference(text,text,text,text,text)'::regprocedure,'read');
 RETURN truss.group_type_reference("selected_document","selected_module","selected_record","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_group_type_reference(selected_document text, selected_module text, selected_record text, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_import_context(expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.import_context(text,text)'::regprocedure,'read');
 RETURN truss.import_context("expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_import_context(expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_import_edge_identity(original_identity bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.import_edge_identity(bytea,text,text)'::regprocedure,'write');
 RETURN truss.import_edge_identity("original_identity","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_import_edge_identity(original_identity bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_import_identity_key_selection(original_identity bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.import_identity_key_selection(bytea,text,text)'::regprocedure,'write');
 RETURN truss.import_identity_key_selection("original_identity","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_import_identity_key_selection(original_identity bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_import_key_selection(selected_document text, selected_module text, selected_record text, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.import_key_selection(text,text,text,text,text)'::regprocedure,'write');
 RETURN truss.import_key_selection("selected_document","selected_module","selected_record","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_import_key_selection(selected_document text, selected_module text, selected_record text, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_import_object_identity(original_identity bytea, original_document bytea, tuple_bytes bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.import_object_identity(bytea,bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.import_object_identity("original_identity","original_document","tuple_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_import_object_identity(original_identity bytea, original_document bytea, tuple_bytes bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_import_record_source(selected_attempt uuid, original_record bytea, load_id text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.import_record_source(uuid,bytea,text)'::regprocedure,'write');
 RETURN truss.import_record_source("selected_attempt","original_record","load_id");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_import_record_source(selected_attempt uuid, original_record bytea, load_id text) FROM PUBLIC;

CREATE FUNCTION truss.person_import_report_record_authority(original_identity bytea, kind text, expected_release text, expected_digest text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.import_report_record_authority(bytea,text,text,text)'::regprocedure,'write');
 PERFORM truss.import_report_record_authority("original_identity","kind","expected_release","expected_digest");
 RETURN;
END;
$$;
REVOKE ALL ON FUNCTION truss.person_import_report_record_authority(original_identity bytea, kind text, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_lookup_import_source(selection jsonb, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.lookup_import_source(jsonb,integer,text,text)'::regprocedure,'read');
 RETURN truss.lookup_import_source("selection","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_lookup_import_source(selection jsonb, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_lookup_string_key(selected_document text, selected_module text, selected_record text, selected_key text, original_document bytea, values_bytes bytea, tuple_bytes bytea, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.lookup_string_key(text,text,text,text,bytea,bytea,bytea,integer,text,text)'::regprocedure,'read');
 RETURN truss.lookup_string_key("selected_document","selected_module","selected_record","selected_key","original_document","values_bytes","tuple_bytes","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_lookup_string_key(selected_document text, selected_module text, selected_record text, selected_key text, original_document bytea, values_bytes bytea, tuple_bytes bytea, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_page_edges(selected_document text, selected_module text, selected_relationship text, anchor jsonb, direction text, page_limit integer, maximum_bytes integer, original_cursor bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.page_edges(text,text,text,jsonb,text,integer,integer,bytea,text,text)'::regprocedure,'read');
 RETURN truss.page_edges("selected_document","selected_module","selected_relationship","anchor","direction","page_limit","maximum_bytes","original_cursor","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_page_edges(selected_document text, selected_module text, selected_relationship text, anchor jsonb, direction text, page_limit integer, maximum_bytes integer, original_cursor bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_page_import_load_audit(filters jsonb, maximum_entries integer, original_cursor bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.page_import_load_audit(jsonb,integer,bytea,text,text)'::regprocedure,'audit');
 RETURN truss.page_import_load_audit("filters","maximum_entries","original_cursor","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_page_import_load_audit(filters jsonb, maximum_entries integer, original_cursor bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_page_mutation_group_audit(filters jsonb, maximum_events integer, original_cursor bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.page_mutation_group_audit(jsonb,integer,bytea,text,text)'::regprocedure,'audit');
 RETURN truss.page_mutation_group_audit("filters","maximum_events","original_cursor","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_page_mutation_group_audit(filters jsonb, maximum_events integer, original_cursor bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_page_objects(selected_document text, selected_module text, selected_record text, page_limit integer, maximum_bytes integer, original_cursor bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.page_objects(text,text,text,integer,integer,bytea,text,text)'::regprocedure,'read');
 RETURN truss.page_objects("selected_document","selected_module","selected_record","page_limit","maximum_bytes","original_cursor","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_page_objects(selected_document text, selected_module text, selected_record text, page_limit integer, maximum_bytes integer, original_cursor bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_person_runtime_status(expected_release text, expected_digest text, expected_layout jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.person_runtime_status(text,text,jsonb)'::regprocedure,'status');
 RETURN truss.person_runtime_status("expected_release","expected_digest","expected_layout");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_person_runtime_status(expected_release text, expected_digest text, expected_layout jsonb) FROM PUBLIC;

CREATE FUNCTION truss.person_prepare_group(original_records bytea, original_relationships bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.prepare_group(bytea,bytea,text,text)'::regprocedure,'read');
 RETURN truss.prepare_group("original_records","original_relationships","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_prepare_group(original_records bytea, original_relationships bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_preview_group_conditions(original_input bytea, original_documents bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.preview_group_conditions(bytea,bytea,text,text)'::regprocedure,'read');
 RETURN truss.preview_group_conditions("original_input","original_documents","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_preview_group_conditions(original_input bytea, original_documents bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_process_import_chunk(original_input bytea, original_documents bytea, invocation_id uuid, chunk_index integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.process_import_chunk(bytea,bytea,uuid,integer,text,text)'::regprocedure,'write');
 RETURN truss.process_import_chunk("original_input","original_documents","invocation_id","chunk_index","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_process_import_chunk(original_input bytea, original_documents bytea, invocation_id uuid, chunk_index integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_read_import_load_chunk(selected_invocation uuid, selected_chunk integer, page_limit integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.read_import_load_chunk(uuid,integer,integer,text,text)'::regprocedure,'audit');
 RETURN truss.read_import_load_chunk("selected_invocation","selected_chunk","page_limit","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_read_import_load_chunk(selected_invocation uuid, selected_chunk integer, page_limit integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_reader_catalog(maximum_count integer, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.reader_catalog(integer,integer,text,text)'::regprocedure,'catalog');
 RETURN truss.reader_catalog("maximum_count","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_reader_catalog(maximum_count integer, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_reader_catalog_if_changed(maximum_count integer, maximum_bytes integer, expected_release text, expected_digest text, validator text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.reader_catalog_if_changed(integer,integer,text,text,text)'::regprocedure,'catalog');
 RETURN truss.reader_catalog_if_changed("maximum_count","maximum_bytes","expected_release","expected_digest","validator");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_reader_catalog_if_changed(maximum_count integer, maximum_bytes integer, expected_release text, expected_digest text, validator text) FROM PUBLIC;

CREATE FUNCTION truss.person_recover_group_request(original_input bytea, original_documents bytea, original_request bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.recover_group_request(bytea,bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.recover_group_request("original_input","original_documents","original_request","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_recover_group_request(original_input bytea, original_documents bytea, original_request bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_registrar_status(expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.registrar_status(text,text)'::regprocedure,'catalog');
 RETURN truss.registrar_status("expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_registrar_status(expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_traverse_objects(start_identity jsonb, hops jsonb, maximum_objects integer, maximum_states integer, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.traverse_objects(jsonb,jsonb,integer,integer,integer,text,text)'::regprocedure,'read');
 RETURN truss.traverse_objects("start_identity","hops","maximum_objects","maximum_states","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_traverse_objects(start_identity jsonb, hops jsonb, maximum_objects integer, maximum_states integer, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_validate_batched_import_report(original_input bytea, original_outcomes bytea, original_context bytea, expected_release text, expected_digest text) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.validate_batched_import_report(bytea,bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.validate_batched_import_report("original_input","original_outcomes","original_context","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_validate_batched_import_report(original_input bytea, original_outcomes bytea, original_context bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_writer_schema_basis(original_input bytea, original_documents bytea, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.writer_schema_basis(bytea,bytea,text,text)'::regprocedure,'write');
 RETURN truss.writer_schema_basis("original_input","original_documents","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_writer_schema_basis(original_input bytea, original_documents bytea, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_query_binding(selected_documents jsonb, maximum_scan_rows integer, maximum_result_rows integer, maximum_bytes integer, expected_release text, expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_binding(jsonb,integer,integer,integer,text,text)'::regprocedure,'read');
 RETURN truss.query_binding("selected_documents","maximum_scan_rows","maximum_result_rows","maximum_bytes","expected_release","expected_digest");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_binding(selected_documents jsonb, maximum_scan_rows integer, maximum_result_rows integer, maximum_bytes integer, expected_release text, expected_digest text) FROM PUBLIC;

CREATE FUNCTION truss.person_query_binding_if_changed(selected_documents jsonb, maximum_scan_rows integer, maximum_result_rows integer, maximum_bytes integer, expected_release text, expected_digest text, validator text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_binding_if_changed(jsonb,integer,integer,integer,text,text,text)'::regprocedure,'read');
 RETURN truss.query_binding_if_changed("selected_documents","maximum_scan_rows","maximum_result_rows","maximum_bytes","expected_release","expected_digest","validator");
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_binding_if_changed(selected_documents jsonb, maximum_scan_rows integer, maximum_result_rows integer, maximum_bytes integer, expected_release text, expected_digest text, validator text) FROM PUBLIC;

CREATE FUNCTION truss.person_query_scope(binding jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_scope(jsonb)'::regprocedure,'read');
 PERFORM truss.query_scope("binding");
 RETURN;
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_scope(binding jsonb) FROM PUBLIC;

