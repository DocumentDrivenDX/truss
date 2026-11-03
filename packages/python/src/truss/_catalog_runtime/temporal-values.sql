-- Bounded native identity of original accepted declarations/owner bytes and
-- actual cached property/type metadata. A cache hit never caches authority.
CREATE FUNCTION truss.temporal_writer_basis_custody() RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selected_revision int;registration record;metadata jsonb;metadata_bytes bytea;complete_bytes bigint;
BEGIN
 SELECT rev INTO STRICT selected_revision FROM truss.schema_head WHERE id=1;
 SELECT declaration_bytes,source_bytes INTO STRICT registration FROM truss.catalog_registration_request WHERE revision=selected_revision;
 IF (SELECT count(*) FROM (SELECT 1 FROM truss.prop_def WHERE retired_rev IS NULL LIMIT 65537) p)>65536
  OR (SELECT count(*) FROM (SELECT 1 FROM truss.runtime_type_schema WHERE rev=selected_revision LIMIT 65537) t)>65536 THEN
  RAISE EXCEPTION 'bounded complete temporal schema basis required' USING ERRCODE='54000';END IF;
 -- One statement snapshot: sum each native row's textual bytes plus exact
 -- array separators BEFORE constructing either complete JSON aggregate. The
 -- CASE subqueries are entered only for an admitted complete byte budget.
 WITH bounds AS MATERIALIZED (
  SELECT octet_length(convert_to(jsonb_build_object('properties','[]'::jsonb,'types','[]'::jsonb)::text,'UTF8'))::bigint
   +(SELECT coalesce(sum(octet_length(convert_to(to_jsonb(p)::text,'UTF8'))::bigint+2),0)
     -(CASE WHEN count(*)>0 THEN 2 ELSE 0 END) FROM truss.prop_def p WHERE p.retired_rev IS NULL)
   +(SELECT coalesce(sum(octet_length(convert_to(to_jsonb(t)::text,'UTF8'))::bigint+2),0)
     -(CASE WHEN count(*)>0 THEN 2 ELSE 0 END) FROM truss.runtime_type_schema t WHERE t.rev=selected_revision) bytes
 )
 SELECT bounds.bytes,CASE WHEN bounds.bytes<=16777216 THEN jsonb_build_object('properties',
   (SELECT coalesce(jsonb_agg(to_jsonb(p) ORDER BY p.prop_id),'[]'::jsonb) FROM truss.prop_def p WHERE p.retired_rev IS NULL),
   'types',(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.type_id),'[]'::jsonb) FROM truss.runtime_type_schema t WHERE t.rev=selected_revision)) END
 INTO complete_bytes,metadata FROM bounds;
 IF metadata IS NULL THEN RAISE EXCEPTION 'bounded complete temporal schema bytes required before aggregation' USING ERRCODE='54000';END IF;
 metadata_bytes:=convert_to(metadata::text,'UTF8');
 IF octet_length(metadata_bytes)<>complete_bytes OR octet_length(metadata_bytes)>16777216 THEN
  RAISE EXCEPTION 'complete temporal schema byte custody changed' USING ERRCODE='55000';END IF;
 RETURN jsonb_build_object('valueProfile',truss.runtime_temporal_profiles()->'valueProfile','queryAbi',truss.query_temporal_abi(),
  'inputProfile','truss-group-temporal-input/0.1.0','personOid',truss.runtime_person(false)::text,
  'declarationSha256',encode(sha256(registration.declaration_bytes),'hex'),
  'ownerSourceSha256',encode(sha256(registration.source_bytes),'hex'),
  'nativeSchemaSha256',encode(sha256(metadata_bytes),'hex'));
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_writer_basis_custody() FROM PUBLIC;

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
 IF app_prepared IS NOT NULL AND (jsonb_typeof(app_prepared) IS DISTINCT FROM 'object'
  OR app_prepared-ARRAY['profile','basis','inputSha256','schemas','operations','valueProfile','queryAbi']<>'{}'::jsonb
  OR (SELECT count(*) FROM jsonb_object_keys(app_prepared))<>7
  OR app_prepared->>'profile' IS DISTINCT FROM 'truss-python-temporal-record-patch/0.1'
  OR app_prepared->'valueProfile' IS DISTINCT FROM truss.runtime_temporal_profiles()->'valueProfile'
  OR app_prepared->'queryAbi' IS DISTINCT FROM truss.query_temporal_abi()) THEN
  RAISE EXCEPTION 'closed selected temporal prepared packet required' USING ERRCODE='0A000';END IF;
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
 RETURN truss.writer_schema_basis_at_profile(original_input,original_documents,expected_release,expected_digest,true);
END;
$$;
REVOKE ALL ON FUNCTION truss.temporal_writer_schema_basis(bytea,bytea,text,text) FROM PUBLIC;
