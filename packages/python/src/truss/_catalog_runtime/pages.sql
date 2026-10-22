-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Live ID-keyset object paging, not an authority token or held snapshot.
CREATE FUNCTION truss.page_objects(selected_document text,selected_module text,selected_record text,
 page_limit int,maximum_bytes int,original_cursor bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;selected_type truss.type_def%ROWTYPE;
 captured_revision int;source_pin record;cursor_value jsonb;after_id bigint:=0;candidate record;
 objects jsonb:='[]';lookahead_root_owner jsonb;object_bytes bytea;object_value jsonb;continuation jsonb;result bytea;counted int:=0;last_id bigint;
BEGIN
 PERFORM truss.runtime_person(false);
 IF selected_document IS NULL OR selected_module IS NULL OR selected_record IS NULL
  OR octet_length(selected_document) NOT BETWEEN 1 AND 4096 OR octet_length(selected_module) NOT BETWEEN 1 AND 4096
  OR octet_length(selected_record) NOT BETWEEN 1 AND 4096 OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 1000
  OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 THEN
  RAISE EXCEPTION 'bounded page selection and limits required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected object page runtime required' USING ERRCODE='0A000';END IF;
 IF current_setting('transaction_read_only')='on' THEN SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 ELSE SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;END IF;
 IF captured_revision<1 THEN RAISE EXCEPTION 'accepted page catalog required' USING ERRCODE='0A000';END IF;
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 SELECT * INTO selected_type FROM truss.type_def WHERE document_id=selected_document AND module=selected_module
  AND element=selected_record AND kind='record' AND NOT provisional AND retired_rev IS NULL AND since_rev<=captured_revision;
 IF NOT FOUND THEN RETURN NULL;END IF;
 IF NOT truss.runtime_object_values_readable(selected_type.type_id) THEN RETURN NULL;END IF;
 SELECT * INTO STRICT source_pin FROM truss.runtime_owned_definition_metadata('type',selected_type.type_id);
 IF original_cursor IS NOT NULL THEN
  IF octet_length(original_cursor) NOT BETWEEN 1 AND 65536 OR (convert_from(original_cursor,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
   RAISE EXCEPTION 'bounded original page cursor required' USING ERRCODE='22023';END IF;
  cursor_value:=convert_from(original_cursor,'UTF8')::jsonb;
  IF (SELECT count(*) FROM jsonb_object_keys(cursor_value))<>11 OR EXISTS(SELECT 1 FROM jsonb_each(cursor_value) e WHERE jsonb_typeof(e.value)<>'string')
   OR cursor_value-ARRAY['profile','installationId','sourceEpoch','releaseSha256','documentId','moduleId','recordId','typeId','definitionPin','catalogRevision','afterId']<>'{}'::jsonb
   OR cursor_value->>'documentId' IS DISTINCT FROM selected_document OR cursor_value->>'moduleId' IS DISTINCT FROM selected_module OR cursor_value->>'recordId' IS DISTINCT FROM selected_record
   OR jsonb_typeof(cursor_value->'afterId') IS DISTINCT FROM 'string' OR cursor_value->>'afterId' !~ '^[1-9][0-9]{0,18}$'
   OR (length(cursor_value->>'afterId')=19 AND (cursor_value->>'afterId') COLLATE "C">'9223372036854775807' COLLATE "C") THEN
   RAISE EXCEPTION 'exact page cursor selection required' USING ERRCODE='22023';END IF;
  IF cursor_value->>'profile' IS DISTINCT FROM 'truss-python-object-page/0.1'
   OR cursor_value->>'installationId' IS DISTINCT FROM installation.installation_id::text
   OR cursor_value->>'sourceEpoch' IS DISTINCT FROM installation.source_epoch::text
   OR cursor_value->>'releaseSha256' IS DISTINCT FROM installation.release_sha256
   OR cursor_value->>'typeId' IS DISTINCT FROM selected_type.type_id::text OR cursor_value->>'definitionPin' IS DISTINCT FROM source_pin.definition_pin
   OR cursor_value->>'catalogRevision' IS DISTINCT FROM captured_revision::text THEN
   RAISE EXCEPTION 'current page cursor context required' USING ERRCODE='P1002';END IF;
  after_id:=(cursor_value->>'afterId')::bigint;
 END IF;
 FOR candidate IN SELECT id FROM truss.object WHERE type_id=selected_type.type_id AND id>after_id ORDER BY id LIMIT page_limit+1 LOOP
  counted:=counted+1;
  IF counted>page_limit THEN
   object_bytes:=truss.get_object(selected_document,selected_module,selected_record,candidate.id,16777216,expected_release,expected_digest);
   IF object_bytes IS NULL THEN RAISE EXCEPTION 'page lookahead no longer admitted' USING ERRCODE='55P03';END IF;
   object_value:=convert_from(object_bytes,'UTF8')::jsonb;
   IF object_value->>'catalogRevision' IS DISTINCT FROM captured_revision::text THEN RAISE EXCEPTION 'catalog changed during page lookahead' USING ERRCODE='55P03';END IF;
   IF object_value->>'profile'='truss-python-logical-object/0.1' THEN lookahead_root_owner:=object_value->'root'->'owner';END IF;
   continuation:=jsonb_build_object('profile','truss-python-object-page/0.1','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'releaseSha256',installation.release_sha256,'documentId',selected_document,
    'moduleId',selected_module,'recordId',selected_record,'typeId',selected_type.type_id::text,'definitionPin',source_pin.definition_pin,
    'catalogRevision',captured_revision::text,'afterId',last_id::text);
   IF octet_length(continuation::text)>65536 THEN RAISE EXCEPTION 'page cursor byte limit exceeded' USING ERRCODE='54000';END IF;
   EXIT;
  END IF;
  object_bytes:=truss.get_object(selected_document,selected_module,selected_record,candidate.id,maximum_bytes,expected_release,expected_digest);
  IF object_bytes IS NULL THEN RAISE EXCEPTION 'page observation no longer admitted' USING ERRCODE='55P03';END IF;
  object_value:=convert_from(object_bytes,'UTF8')::jsonb;
  IF object_value->>'catalogRevision' IS DISTINCT FROM captured_revision::text THEN RAISE EXCEPTION 'catalog changed during page observation' USING ERRCODE='55P03';END IF;
  objects:=objects||jsonb_build_array(object_value);last_id:=candidate.id;
  IF octet_length(objects::text)>maximum_bytes THEN RAISE EXCEPTION 'complete page byte limit exceeded' USING ERRCODE='54000';END IF;
 END LOOP;
 PERFORM truss.runtime_person(false);
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RAISE EXCEPTION 'current page reader required' USING ERRCODE='P1403';END IF;
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN RAISE EXCEPTION 'catalog changed during page observation' USING ERRCODE='55P03';END IF;
 result:=convert_to(jsonb_build_object('profile','truss-python-object-page/0.1','catalogRevision',captured_revision,'objects',objects,'continuation',continuation)::text,'UTF8');
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'complete page byte limit exceeded' USING ERRCODE='54000';END IF;
 IF NOT truss.runtime_object_values_readable(selected_type.type_id) THEN RAISE EXCEPTION 'current buffered page interpretation reader required' USING ERRCODE='P1403';END IF;
 FOR object_value IN SELECT value FROM jsonb_array_elements(objects) LOOP
  IF object_value->>'profile'='truss-python-logical-object/0.1' AND NOT truss.runtime_can_read(
   object_value->'root'->'owner'->>'documentId',object_value->'root'->'owner'->>'moduleId') THEN
   RAISE EXCEPTION 'current buffered aggregate root reader required' USING ERRCODE='P1403';END IF;
 END LOOP;
 IF lookahead_root_owner IS NOT NULL AND NOT truss.runtime_can_read(lookahead_root_owner->>'documentId',lookahead_root_owner->>'moduleId') THEN
  RAISE EXCEPTION 'current lookahead aggregate root reader required' USING ERRCODE='P1403';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.page_objects(text,text,text,int,int,bytea,text,text) FROM PUBLIC;
