-- SPDX-License-Identifier: MIT OR Apache-2.0
-- PV1 explicit native providers; shared owned engine consumes original bytes.
CREATE FUNCTION truss.temporal_group_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN truss.group_context_qualified_at_profile(expected_release,expected_digest,truss.runtime_person(false),true);
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_group_context(text,text) FROM PUBLIC;

CREATE FUNCTION truss.apply_temporal_group_prepared(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text,app_prepared jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 -- No temporal patch issuer exists yet. Even a correctly labelled packet is
 -- untrusted: validating labels alone cannot establish its original2.1 source
 -- and descriptor basis. The explicit unprepared temporal provider below is
 -- available; an ordinary patch must never be accepted or silently discarded.
 IF app_prepared IS NOT NULL THEN
  RAISE EXCEPTION 'selected temporal prepared optimization unavailable' USING ERRCODE='0A000';END IF;
 RETURN truss.apply_group_prepared_at_profile(original_input,original_documents,original_request,expected_release,expected_digest,app_prepared,true);
END;
$$;
REVOKE ALL ON FUNCTION truss.apply_temporal_group_prepared(bytea,bytea,bytea,text,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.apply_temporal_group(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 RETURN truss.apply_temporal_group_prepared(original_input,original_documents,original_request,expected_release,expected_digest,NULL);
END;
$$;
REVOKE ALL ON FUNCTION truss.apply_temporal_group(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.get_temporal_object(selected_document text,selected_module text,selected_record text,selected_id bigint,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE result bytea;
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 result:=truss.get_object_at_profile(selected_document,selected_module,selected_record,selected_id,maximum_bytes,expected_release,expected_digest,true);
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.get_temporal_object(text,text,text,bigint,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.lookup_temporal_key(selected_document text,selected_module text,selected_record text,selected_key text,original_document bytea,values_bytes bytea,tuple_bytes bytea,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE result bytea;
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 result:=truss.lookup_key_at_profile(selected_document,selected_module,selected_record,selected_key,original_document,values_bytes,tuple_bytes,maximum_bytes,expected_release,expected_digest,true);
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.lookup_temporal_key(text,text,text,text,bytea,bytea,bytea,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.temporal_scope(expected_release text,expected_digest text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.runtime_person(false);
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_scope(text,text) FROM PUBLIC;

CREATE FUNCTION truss.page_temporal_objects(selected_document text,selected_module text,selected_record text,page_limit int,maximum_bytes int,original_cursor bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 RETURN truss.page_objects_at_profile(selected_document,selected_module,selected_record,page_limit,maximum_bytes,original_cursor,expected_release,expected_digest,true);
END;
$$;
REVOKE ALL ON FUNCTION truss.page_temporal_objects(text,text,text,int,int,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.recover_temporal_group_request(original_input bytea,original_documents bytea,original_request bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN truss.recover_group_request_at_profile(original_input,original_documents,original_request,expected_release,expected_digest,true);
END;
$$;
REVOKE ALL ON FUNCTION truss.recover_temporal_group_request(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.temporal_import_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN truss.import_context_at_profile(expected_release,expected_digest,true);
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_import_context(text,text) FROM PUBLIC;

CREATE FUNCTION truss.temporal_import_key_selection(selected_document text,selected_module text,selected_record text,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN truss.import_key_selection(selected_document,selected_module,selected_record,expected_release,expected_digest);
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_import_key_selection(text,text,text,text,text) FROM PUBLIC;

CREATE FUNCTION truss.temporal_import_object_identity(original_identity bytea,original_document bytea,tuple_bytes bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN truss.import_object_identity_at_profile(original_identity,original_document,tuple_bytes,expected_release,expected_digest,true);
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_import_object_identity(bytea,bytea,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.temporal_writer_schema_basis(original_input bytea,original_documents bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 IF original_input IS NULL OR octet_length(original_input) NOT BETWEEN 1 AND 1048576
  OR (convert_from(original_input,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  OR (convert_from(original_input,'UTF8')::jsonb)->>'interfaceVersion' IS DISTINCT FROM 'truss-group-temporal-input/0.1.0' THEN
  RAISE EXCEPTION 'original selected temporal patch input required' USING ERRCODE='0A000';END IF;
 -- No ordinary cache packet is relabelled. Until the selected temporal patch
 -- optimization issues a complete2.1 source/native descriptor basis, NULL is
 -- explicit optimization unavailability; callers use unprepared TEMPORAL only.
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_writer_schema_basis(bytea,bytea,text,text) FROM PUBLIC;
