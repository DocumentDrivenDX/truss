-- Authored-key reads over the writer's active exact key memberships. No route writes.
CREATE FUNCTION truss.key_read_selection(selected_document text,selected_module text,selected_record text,selected_key text,original_document bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;record_type truss.type_def%ROWTYPE;key_definition truss.key_def%ROWTYPE;archive truss.schema_doc%ROWTYPE;component record;counted int:=0;revision int;
BEGIN
 PERFORM truss.runtime_person(false);
 IF selected_document IS NULL OR selected_module IS NULL OR selected_record IS NULL OR selected_key IS NULL
 OR octet_length(selected_document) NOT BETWEEN 1 AND 4096 OR octet_length(selected_module) NOT BETWEEN 1 AND 4096 OR octet_length(selected_record) NOT BETWEEN 1 AND 4096 OR octet_length(selected_key) NOT BETWEEN 1 AND 4096
 OR original_document IS NULL OR octet_length(original_document) NOT BETWEEN 1 AND 1048576 THEN RAISE EXCEPTION 'bounded key selection required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN RAISE EXCEPTION 'selected installed runtime required' USING ERRCODE='0A000';END IF;
 IF current_setting('transaction_read_only')='on' THEN SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 ELSE SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;END IF;
 IF revision<1 THEN RAISE EXCEPTION 'accepted key catalog required' USING ERRCODE='0A000';END IF;
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 SELECT * INTO record_type FROM truss.type_def WHERE document_id=selected_document AND module=selected_module AND element=selected_record AND kind='record' AND NOT provisional AND retired_rev IS NULL AND since_rev<=revision;
 IF NOT FOUND THEN RETURN NULL;END IF;
 SELECT * INTO key_definition FROM truss.key_def WHERE type_id=record_type.type_id AND key_id=selected_key AND retired_rev IS NULL;
 IF NOT FOUND THEN RETURN NULL;END IF;
 IF cardinality(key_definition.prop_ids) NOT BETWEEN 1 AND 1024 THEN RAISE EXCEPTION 'bounded complete key required' USING ERRCODE='0A000';END IF;
 FOR component IN SELECT DISTINCT p.declaration_module FROM unnest(key_definition.prop_ids) i(prop_id) JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=record_type.type_id LOOP
  IF NOT truss.runtime_can_read(selected_document,component.declaration_module) THEN RETURN NULL;END IF;
 END LOOP;
 FOR component IN SELECT p.* FROM unnest(key_definition.prop_ids) WITH ORDINALITY k(prop_id,n) JOIN truss.prop_def p ON p.prop_id=k.prop_id AND p.type_id=record_type.type_id ORDER BY k.n LOOP
  counted:=counted+1;
  IF component.scalar_type IS DISTINCT FROM 'string' OR component.nullability IS DISTINCT FROM 'required' OR component.cardinality IS DISTINCT FROM 'one' OR component.home IS DISTINCT FROM 'json' OR component.retired_rev IS NOT NULL THEN RAISE EXCEPTION 'supported string key required' USING ERRCODE='0A000';END IF;
 END LOOP;
 IF counted<>cardinality(key_definition.prop_ids) THEN RAISE EXCEPTION 'complete native key definition required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT archive FROM truss.schema_doc WHERE doc_id=record_type.document_id ORDER BY rev DESC LIMIT 1;
 IF original_document IS DISTINCT FROM convert_to(archive.document,'UTF8') OR archive.doc_id IS DISTINCT FROM selected_document OR encode(sha256(original_document),'hex') IS DISTINCT FROM archive.content_sha256 THEN RAISE EXCEPTION 'original accepted key source required' USING ERRCODE='22023';END IF;
 PERFORM truss.runtime_person(false);
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 FOR component IN SELECT DISTINCT p.declaration_module FROM unnest(key_definition.prop_ids) i(prop_id) JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=record_type.type_id LOOP
  IF NOT truss.runtime_can_read(selected_document,component.declaration_module) THEN RETURN NULL;END IF;
 END LOOP;
 PERFORM truss.runtime_person(false);
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM revision THEN
  RAISE EXCEPTION 'catalog changed during key selection' USING ERRCODE='55P03';END IF;
 RETURN convert_to(jsonb_build_object('typeId',record_type.type_id,'keyNumber',key_definition.key_num,'componentCount',counted,'catalogRevision',revision)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.key_read_selection(text,text,text,text,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.lookup_string_key(selected_document text,selected_module text,selected_record text,selected_key text,original_document bytea,values_bytes bytea,tuple_bytes bytea,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selection_bytes bytea;selection jsonb;values_json jsonb;actual_values text[];installation truss.catalog_runtime_installation%ROWTYPE;source_pin record;namespace bytea;transport bytea;candidate_count bigint;candidate_bytes bigint;matches bigint;member truss.object_key_bucket%ROWTYPE;result bytea;component record;candidate record;buffered_values text[];
BEGIN
 selection_bytes:=truss.key_read_selection(selected_document,selected_module,selected_record,selected_key,original_document,expected_release,expected_digest);
 IF selection_bytes IS NULL THEN RETURN NULL;END IF;
 selection:=convert_from(selection_bytes,'UTF8')::jsonb;
 IF maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 OR values_bytes IS NULL OR octet_length(values_bytes) NOT BETWEEN 1 AND 1048576 OR tuple_bytes IS NULL OR octet_length(tuple_bytes) NOT BETWEEN 1 AND 1048576 THEN RAISE EXCEPTION 'bounded key values required' USING ERRCODE='22023';END IF;
 values_json:=convert_from(values_bytes,'UTF8')::jsonb;
 IF jsonb_typeof(values_json) IS DISTINCT FROM 'array' OR jsonb_array_length(values_json)<>(selection->>'componentCount')::int OR EXISTS(SELECT 1 FROM jsonb_array_elements(values_json) v WHERE jsonb_typeof(v.value) IS DISTINCT FROM 'string') THEN RAISE EXCEPTION 'ordered string key values required' USING ERRCODE='22023';END IF;
 SELECT array_agg(v.value ORDER BY v.n) INTO actual_values FROM jsonb_array_elements_text(values_json) WITH ORDINALITY v(value,n);
 IF truss.verify_umf_string_key_tuple(tuple_bytes,actual_values) IS NOT TRUE THEN RAISE EXCEPTION 'original key encoding required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 SELECT * INTO STRICT source_pin FROM truss.runtime_definition('key',(selection->>'typeId')::int,(selection->>'keyNumber')::int);
 namespace:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
  'sourceEpoch',installation.source_epoch::text,'typeId',selection->>'typeId','keyNumber',selection->>'keyNumber',
  'definitionPin',source_pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
 transport:=convert_to('umf-key-tuple-v1:hex:'||encode(tuple_bytes,'hex'),'UTF8');
 IF octet_length(transport)>1048576 THEN RAISE EXCEPTION 'key transport budget exceeded' USING ERRCODE='54000';END IF;
 candidate_count:=0;candidate_bytes:=0;matches:=0;
 -- One bounded indexed candidate cursor; its complete route observation is a
 -- single native query snapshot, rather than unbounded follow-up scans.
 FOR candidate IN SELECT storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,
   octet_length(original_context_bytes) AS context_size
   FROM truss.object_key_bucket WHERE namespace_sha256=sha256(namespace) AND key_sha256=sha256(transport)
   ORDER BY storage_row_id LIMIT 10001 LOOP
  candidate_count:=candidate_count+1;
  candidate_bytes:=candidate_bytes+octet_length(candidate.namespace_bytes)+octet_length(candidate.key_bytes)+candidate.context_size;
  IF candidate_count>10000 OR candidate_bytes>16777216 THEN RAISE EXCEPTION 'bounded key route exceeded' USING ERRCODE='54000';END IF;
  IF candidate.namespace_bytes=namespace AND candidate.key_bytes=transport THEN
   matches:=matches+1;
   IF matches>1 THEN RAISE EXCEPTION 'unique exact key membership required' USING ERRCODE='55000';END IF;
   member.storage_row_id:=candidate.storage_row_id;member.type_id:=candidate.type_id;member.key_num:=candidate.key_num;member.object_id:=candidate.object_id;
  END IF;
 END LOOP;
 IF matches=0 THEN RETURN NULL;END IF;
 IF member.type_id<>(selection->>'typeId')::int OR member.key_num<>(selection->>'keyNumber')::smallint THEN RAISE EXCEPTION 'qualified key membership required' USING ERRCODE='55000';END IF;
 IF current_setting('transaction_read_only')<>'on' THEN
  PERFORM 1 FROM truss.object WHERE id=member.object_id AND type_id=member.type_id FOR SHARE NOWAIT;
  IF NOT FOUND THEN RAISE EXCEPTION 'live member object required' USING ERRCODE='55000';END IF;
 END IF;
 IF truss.verify_object_string_key(member.object_id,member.type_id,member.key_num,tuple_bytes) IS NOT TRUE THEN RAISE EXCEPTION 'current object key membership required' USING ERRCODE='55000';END IF;
 result:=truss.get_object(selected_document,selected_module,selected_record,member.object_id,maximum_bytes,expected_release,expected_digest);
 IF result IS NULL THEN RETURN NULL;END IF;
 IF convert_from(result,'UTF8')::jsonb->>'catalogRevision' IS DISTINCT FROM selection->>'catalogRevision' THEN
  RAISE EXCEPTION 'catalog changed during key observation' USING ERRCODE='55P03';END IF;
 SELECT array_agg(cell.value->>1 ORDER BY i.n) INTO buffered_values
  FROM truss.key_def k CROSS JOIN LATERAL unnest(k.prop_ids) WITH ORDINALITY i(prop_id,n)
  JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=k.type_id
  CROSS JOIN LATERAL jsonb_array_elements(convert_from(result,'UTF8')::jsonb->'values') cell(value)
  WHERE k.type_id=member.type_id AND k.key_num=member.key_num AND cell.value->>0=p.name;
 IF truss.verify_umf_string_key_tuple(tuple_bytes,buffered_values) IS NOT TRUE THEN RAISE EXCEPTION 'key changed during observation' USING ERRCODE='55P03';END IF;
 -- Do not authorize the buffered object against earlier role membership.
 IF NOT truss.runtime_can_read(selected_document,selected_module) THEN RETURN NULL;END IF;
 FOR component IN SELECT DISTINCT p.declaration_module FROM truss.key_def k CROSS JOIN LATERAL unnest(k.prop_ids) i(prop_id) JOIN truss.prop_def p ON p.prop_id=i.prop_id AND p.type_id=k.type_id WHERE k.type_id=member.type_id AND k.key_num=member.key_num LOOP
  IF NOT truss.runtime_can_read(selected_document,component.declaration_module) THEN RETURN NULL;END IF;
 END LOOP;
 PERFORM truss.runtime_person(false);
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.lookup_string_key(text,text,text,text,bytea,bytea,bytea,int,text,text) FROM PUBLIC;
