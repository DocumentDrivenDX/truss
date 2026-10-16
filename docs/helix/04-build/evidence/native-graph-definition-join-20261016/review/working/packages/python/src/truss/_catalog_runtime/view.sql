-- Verified accepted catalog basis for the Python view extractor.
CREATE FUNCTION truss.catalog_view_basis(selected_revision int,maximum_count int,maximum_bytes int) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET bytea_output=hex AS $$
DECLARE captured_revision int; request truss.catalog_registration_request%ROWTYPE;
 installation truss.catalog_runtime_installation%ROWTYPE; expected jsonb;
 origin bytea; original_report bytea; basis jsonb; encoded bytea; definition_count bigint;
BEGIN
 PERFORM truss.catalog_actor();
 IF current_setting('transaction_read_only')='on' THEN RETURN NULL; END IF;
 IF maximum_count IS NULL OR maximum_bytes IS NULL OR maximum_count NOT BETWEEN 1 AND 65536 OR maximum_bytes NOT BETWEEN 1 AND 16777216 THEN
  RAISE EXCEPTION 'bounded catalog view limits required' USING ERRCODE='22023'; END IF;
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 IF selected_revision IS NOT NULL AND selected_revision<>captured_revision THEN RETURN NULL; END IF;
 -- This append-only profile exposes the current complete catalog; genesis is not accepted.
 IF captured_revision<1 THEN RETURN NULL; END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 SELECT * INTO STRICT request FROM truss.catalog_registration_request WHERE revision=captured_revision;
 IF request.installation_id<>installation.installation_id THEN
  RAISE EXCEPTION 'installed catalog provenance required' USING ERRCODE='55000'; END IF;
 PERFORM truss.catalog_check_source_correspondence(request.input_bytes,request.document_bytes,request.declaration_bytes);
 origin:=convert_to((convert_from(request.origin_bytes,'UTF8')::jsonb||jsonb_build_object('actor',request.actor_name,'db_role',request.actor_name))::text,'UTF8');
 expected:=truss.catalog_all_expected_records();
 PERFORM truss.catalog_check_records(expected);
 SELECT report_bytes INTO STRICT original_report FROM truss.catalog_acceptance_report WHERE rev=captured_revision;
 IF sha256(original_report) IS DISTINCT FROM request.report_sha256 OR original_report IS DISTINCT FROM truss.catalog_make_report(request) THEN
  RAISE EXCEPTION 'original accepted report required' USING ERRCODE='55000'; END IF;
 SELECT (SELECT count(*) FROM truss.type_def)+(SELECT count(*) FROM truss.prop_def)
       +(SELECT count(*) FROM truss.key_def)+(SELECT count(*) FROM truss.rel_def) INTO definition_count;
 IF definition_count>maximum_count THEN RAISE EXCEPTION 'catalog definition budget exceeded' USING ERRCODE='54000'; END IF;
 basis:=jsonb_build_object('revision',captured_revision::text,'layoutProfile',installation.layout_profile,
  'installationId',installation.installation_id::text,'registrationId',request.registration_id::text,
  'releaseId',installation.release_id,'releaseSha256',installation.release_sha256,
  'reportSha256',encode(request.report_sha256,'hex'),
  'documents',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY rev,ord),'[]'::jsonb) FROM truss.schema_doc d WHERE rev<=captured_revision),
  'types',(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY type_id),'[]'::jsonb) FROM truss.type_def t),
  'properties',(SELECT coalesce(jsonb_agg(to_jsonb(p) ORDER BY prop_id),'[]'::jsonb) FROM truss.prop_def p),
  'keys',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY type_id,key_num),'[]'::jsonb) FROM truss.key_def k),
  'relationships',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY rel_type_id),'[]'::jsonb) FROM truss.rel_def r),
  'endpoints',(SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY rel_type_id,source_type,target_type),'[]'::jsonb) FROM truss.rel_endpoint e));
 encoded:=convert_to(basis::text,'UTF8');
 IF octet_length(encoded)>maximum_bytes THEN RAISE EXCEPTION 'catalog basis budget exceeded' USING ERRCODE='54000'; END IF;
 PERFORM truss.catalog_actor();
 RETURN encoded;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_view_basis(int,int,int) FROM PUBLIC;
