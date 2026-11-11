-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Pins hash actual temporal-profiles.json definition bytes, not package versions.
CREATE FUNCTION truss.runtime_temporal_profiles() RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ SELECT '{"valueProfile":{"identity":"truss-exact-value-temporal","version":"0.1","sha256":"93a6cb473589d627af11763fbe735412a2e9a3aeeb0dac4b928a7574f8028e7a"},"mutationProfile":{"identity":"truss-owned-temporal-graph","version":"0.1","sha256":"0627b6b6bd8bfd975b56b98057f590dd46764e6adacd74672ead9e5b2d710fc0"},"importProfile":{"identity":"truss-temporal-object-import","version":"0.1","sha256":"0396d1afbc8620110cadfb57a50f4b27a423bc932fd5769915e9f94b9503a4d7"},"importPayloadProfile":{"identity":"truss-import-temporal-payload","version":"0.1.0","sha256":"a9ac1b424aa610eac3d47674c8493f2ccb767eeb4bd828baf11d156b836b6831"},"ownedImportProfile":{"identity":"truss-owned-temporal-object-import","version":"0.1","sha256":"a40d657011ad8e11f8808148f9046b6a023b0565fff35b1ecc6851d6d14c1e54"},"ownedImportPayloadProfile":{"identity":"truss-owned-import-temporal-payload","version":"0.1.0","sha256":"b9a150155650ac48d73d7670e7fc51132ef34b7a4e39d85a48e0437003bd6d6a"}}'::jsonb; $$;
REVOKE ALL ON FUNCTION truss.runtime_temporal_profiles() FROM PUBLIC;

CREATE FUNCTION truss.runtime_is_owned_profile(selected_profile jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN selected_profile IS NOT NULL AND (selected_profile=truss.runtime_owned_profile()
  OR selected_profile=truss.runtime_temporal_profiles()->'mutationProfile');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_is_owned_profile(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.require_temporal_capability(expected_release text,expected_digest text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;property record;source truss.schema_doc%ROWTYPE;
 packet jsonb;owner_result jsonb;owner_record jsonb;owner_field jsonb;expected jsonb;matches int;
BEGIN
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM 'truss-catalog-runtime/0.76-candidate'
  OR expected_release IS DISTINCT FROM installation.release_id OR expected_digest IS DISTINCT FROM installation.release_sha256
  OR truss.query_temporal_abi() IS DISTINCT FROM '{"identity":"truss-postgresql-logical-query","version":"1.3","sha256":"0ecf5aa206dfcfcba21581fc328d7d073b48dbc8b61b2fc199278cf5f3e31b0b"}'::jsonb THEN
  RAISE EXCEPTION 'explicit actual native0.76 and ABI1.3 capability required' USING ERRCODE='0A000';END IF;
 FOR property IN SELECT p.*,t.module record_module,t.element record_element FROM truss.prop_def p JOIN truss.type_def t USING(type_id)
  WHERE p.retired_rev IS NULL AND t.retired_rev IS NULL AND p.scalar_type='localTimestamp' LOOP
  SELECT d.* INTO source FROM truss.schema_doc d WHERE d.rev=property.definition_rev AND d.ord=property.definition_doc_ord
   AND d.doc_id=property.definition_document_id;
  IF NOT FOUND OR source.validation->>'storageFormat' IS DISTINCT FROM 'truss-catalog-source/2.1' THEN
   RAISE EXCEPTION 'original accepted local source custody required' USING ERRCODE='0A000';END IF;
  packet:=source.validation->'inspection';
  IF packet->>'contentSha256' IS DISTINCT FROM source.content_sha256 OR packet->>'documentId' IS DISTINCT FROM source.doc_id
   OR packet->>'revision' IS DISTINCT FROM source.doc_revision
   OR packet->>'resultSha256' IS DISTINCT FROM encode(sha256(convert_to(packet->>'resultJson','UTF8')),'hex') THEN
   RAISE EXCEPTION 'original accepted local inspection digest required' USING ERRCODE='55000';END IF;
  owner_result:=(packet->>'resultJson')::jsonb;
  SELECT count(*),(jsonb_agg(r.value)->0) INTO matches,owner_record FROM jsonb_array_elements(owner_result->'records') r
   WHERE r.value->'ref'=jsonb_build_object('module',property.record_module,'element',property.record_element);
  IF matches<>1 THEN RAISE EXCEPTION 'complete accepted local Record custody required' USING ERRCODE='55000';END IF;
  SELECT count(*),(jsonb_agg(f.value)->0) INTO matches,owner_field FROM jsonb_array_elements(owner_record->'fields') f
   WHERE f.value->'ref'=jsonb_build_object('module',property.declaration_module,'element',property.element);
  IF matches<>1 OR owner_field->>'scalarType' IS DISTINCT FROM 'timestamp' OR owner_field->>'temporal' IS DISTINCT FROM 'local' THEN
   RAISE EXCEPTION 'accepted local owner Field correspondence required' USING ERRCODE='55000';END IF;
  expected:=jsonb_build_object('profile','truss.local-timestamp/0.1','kind','local','source',jsonb_build_object(
   'documentId',source.doc_id,'sha256',source.content_sha256,'record',owner_record->'ref','field',owner_field->'ref',
   'fieldViewPointer',owner_field->>'viewPointer'));
  IF property.native_temporal IS DISTINCT FROM expected THEN
   RAISE EXCEPTION 'actual accepted native local descriptor required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.require_temporal_capability(text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_group_context_for_input(original_input bytea,expected_release text,expected_digest text,qualified_actor oid) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selected text;
BEGIN
 IF original_input IS NULL OR octet_length(original_input) NOT BETWEEN 1 AND 1048576
  OR (convert_from(original_input,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'bounded original selected group input required' USING ERRCODE='22023';END IF;
 selected:=(convert_from(original_input,'UTF8')::jsonb)->>'interfaceVersion';
 IF selected NOT IN ('truss-group-input/0.1.0','truss-group-temporal-input/0.1.0') OR selected IS NULL THEN
  RAISE EXCEPTION 'closed original group input provider required' USING ERRCODE='0A000';END IF;
 RETURN truss.group_context_qualified_at_profile(expected_release,expected_digest,qualified_actor,
  selected='truss-group-temporal-input/0.1.0');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_group_context_for_input(bytea,text,text,oid) FROM PUBLIC;

CREATE FUNCTION truss.valid_authored_object_cell(selected_type int,selected_name text,cell jsonb) RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF cell->>'kind'='localTimestamp' THEN
  RETURN EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.type_id=selected_type AND p.name=selected_name AND p.retired_rev IS NULL
   AND p.scalar_type='localTimestamp' AND p.cardinality='one' AND truss.valid_property_value(cell,p) IS TRUE);
 END IF;
 RETURN truss.valid_flat_cell(cell);
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_authored_object_cell(int,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.canonical_authored_object_cell(selected_type int,selected_name text,cell jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF truss.valid_authored_object_cell(selected_type,selected_name,cell) IS NOT TRUE THEN
  RAISE EXCEPTION 'actual selected property value family required' USING ERRCODE='22023';END IF;
 IF cell->>'kind'='localTimestamp' THEN RETURN cell;END IF;
 RETURN truss.canonical_flat_cell(cell);
END;
$$;
REVOKE ALL ON FUNCTION truss.canonical_authored_object_cell(int,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_is_owned_import_payload_profile(selected_profile jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN selected_profile IS NOT NULL AND selected_profile IN (
  truss.runtime_import_profiles()->'ownedImportPayloadProfile',truss.runtime_temporal_profiles()->'ownedImportPayloadProfile');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_is_owned_import_payload_profile(jsonb) FROM PUBLIC;
