-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Explicit chunked profile. Legacy import functions and settlement stay intact.
CREATE FUNCTION truss.runtime_batched_import_profile() RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT jsonb_build_object('identity','truss-batched-scalar-import','version','0.1','sha256',
 encode(sha256(convert_to('Batched scalar imports v1: 1024 original records; 128 records per chunk; whole-input object-before-edge order; per-record containment and original indices; skip before payload decoding; caller pending or explicit engine chunk settlement; exact source and current whole-report authority; bounded input report and transaction work.','UTF8')),'hex'));
$$;
REVOKE ALL ON FUNCTION truss.runtime_batched_import_profile() FROM PUBLIC;

CREATE FUNCTION truss.batched_import_context(expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 RETURN convert_to((convert_from(truss.import_context(expected_release,expected_digest),'UTF8')::jsonb
  ||jsonb_build_object('importProfile',truss.runtime_batched_import_profile()))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.batched_import_context(text,text) FROM PUBLIC;

CREATE TABLE truss.runtime_import_budget(
 writer_xid xid8 PRIMARY KEY,
 records bigint NOT NULL CHECK(records BETWEEN 0 AND 4096),
 submitted_bytes bigint NOT NULL CHECK(submitted_bytes BETWEEN 0 AND 268435456));
REVOKE ALL ON TABLE truss.runtime_import_budget FROM PUBLIC;

CREATE FUNCTION truss.build_import_records(original_drafts bytea,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
 DECLARE drafts jsonb;draft jsonb;context jsonb;metadata jsonb;cache jsonb:='{}';cache_key text;
 identity jsonb;component jsonb;components jsonb;matches int;cell jsonb;payload jsonb;payload_bytes bytea;
 records jsonb[]:='{}';item jsonb;selected_type int;definition truss.prop_def%ROWTYPE;
BEGIN
 context:=convert_from(truss.batched_import_context(expected_release,expected_digest),'UTF8')::jsonb;
 IF original_drafts IS NULL OR octet_length(original_drafts)>8388608 THEN RAISE EXCEPTION 'bounded import drafts required' USING ERRCODE='54000';END IF;
 IF (convert_from(original_drafts,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'unique original import drafts required' USING ERRCODE='22023';END IF;
 drafts:=convert_from(original_drafts,'UTF8')::jsonb;
 IF jsonb_array_length(drafts)>1024 THEN RAISE EXCEPTION 'bounded import drafts required' USING ERRCODE='54000';END IF;
 FOR draft IN SELECT value FROM jsonb_array_elements(drafts) LOOP
  IF (draft->>'kind' IN ('object','edge')) IS NOT TRUE OR jsonb_typeof(draft->'values') IS DISTINCT FROM 'array'
   OR EXISTS(SELECT 1 FROM unnest(ARRAY['documentId','moduleId']) k WHERE jsonb_typeof(draft->k) IS DISTINCT FROM 'string' OR octet_length(draft->>k) NOT BETWEEN 1 AND 4096)
   THEN RAISE EXCEPTION 'closed exact import draft required' USING ERRCODE='22023';END IF;
  PERFORM truss.runtime_module_writer(draft->>'documentId',draft->>'moduleId');
  cache_key:=jsonb_build_array(draft->>'kind',draft->>'documentId',draft->>'moduleId',draft->>'recordId',draft->>'relationshipId')::text;
  metadata:=cache->cache_key;
  IF draft->>'kind'='object' THEN
   IF draft-ARRAY['kind','documentId','moduleId','recordId','values','source']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed object import draft required' USING ERRCODE='22023';END IF;
   IF metadata IS NULL THEN
    metadata:=convert_from(truss.import_key_selection(draft->>'documentId',draft->>'moduleId',draft->>'recordId',expected_release,expected_digest),'UTF8')::jsonb;
    cache:=cache||jsonb_build_object(cache_key,metadata);
   END IF;
   selected_type:=(metadata->'type'->>'typeId')::int;components:='[]';
   FOR component IN SELECT value FROM jsonb_array_elements(metadata->'components') LOOP
    SELECT count(*),jsonb_agg(v.value->'value')->0 INTO matches,cell FROM jsonb_array_elements(draft->'values') v WHERE v.value->>'name'=component->>'name';
    IF matches<>1 THEN RAISE EXCEPTION 'complete original primary values required' USING ERRCODE='22023';END IF;
    SELECT * INTO STRICT definition FROM truss.prop_def WHERE type_id=selected_type AND prop_id=(component->>'propertyId')::int AND retired_rev IS NULL;
    IF NOT truss.runtime_can_read(draft->>'documentId',definition.declaration_module) THEN RAISE EXCEPTION 'current primary reader required' USING ERRCODE='42501';END IF;
    components:=components||jsonb_build_array(jsonb_build_object('propertyId',component->>'propertyId','definitionPin',component->>'definitionPin','value',cell));
   END LOOP;
   identity:=jsonb_build_object('operation','object_key','type',metadata->'type','keyNumber',metadata->>'keyNumber',
    'keyDefinitionPin',metadata->>'keyDefinitionPin','keyEncodingProfile',metadata->'keyEncodingProfile','components',components);
   payload:=jsonb_build_object('interfaceVersion','truss-import-payload/0.1.0','kind','object','values',draft->'values','ownership',jsonb_build_object('state','rootless'));
  ELSE
   IF draft-ARRAY['kind','documentId','moduleId','relationshipId','sourceEndpoint','targetEndpoint','values','orderKey','source']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed edge import draft required' USING ERRCODE='22023';END IF;
   IF metadata IS NULL THEN
    metadata:=convert_from(truss.group_relationship_reference(draft->>'documentId',draft->>'moduleId',draft->>'relationshipId',expected_release,expected_digest),'UTF8')::jsonb;
    IF metadata IS NULL THEN RAISE EXCEPTION 'accepted relationship required' USING ERRCODE='22023';END IF;
    cache:=cache||jsonb_build_object(cache_key,metadata);
   END IF;
   identity:=jsonb_build_object('relationshipDefinitionPin',metadata->>'definitionPin','source',draft->'sourceEndpoint','target',draft->'targetEndpoint');
   payload:=jsonb_build_object('interfaceVersion','truss-import-payload/0.1.0','kind','edge','values',draft->'values','orderKey',draft->'orderKey');
  END IF;
  IF draft->'source' IS NOT NULL AND draft->'source'<>'null'::jsonb THEN payload:=payload||jsonb_build_object('source',draft->'source');END IF;
  payload_bytes:=convert_to(payload::text,'UTF8');
  IF octet_length(payload_bytes)>1048576 THEN RAISE EXCEPTION 'bounded record payload required' USING ERRCODE='54000';END IF;
  records:=array_append(records,jsonb_build_object('kind',draft->>'kind','identity',identity,'payloadProfile',context->'importPayloadProfile',
   'payload',jsonb_build_object('identity',encode(sha256(payload_bytes),'hex'),'bytesBase64',replace(encode(payload_bytes,'base64'),E'\n',''),'sha256',encode(sha256(payload_bytes),'hex'))));
 END LOOP;
 -- Repeat each cached definition's original authority proof before publishing.
 FOR draft IN SELECT DISTINCT ON (value->>'kind',value->>'documentId',value->>'moduleId',value->>'recordId',value->>'relationshipId') value FROM jsonb_array_elements(drafts) LOOP
  cache_key:=jsonb_build_array(draft->>'kind',draft->>'documentId',draft->>'moduleId',draft->>'recordId',draft->>'relationshipId')::text;
  IF draft->>'kind'='object' THEN
   IF convert_from(truss.import_key_selection(draft->>'documentId',draft->>'moduleId',draft->>'recordId',expected_release,expected_digest),'UTF8')::jsonb IS DISTINCT FROM cache->cache_key THEN RAISE EXCEPTION 'original builder definition changed' USING ERRCODE='42501';END IF;
  ELSE
   IF convert_from(truss.group_relationship_reference(draft->>'documentId',draft->>'moduleId',draft->>'relationshipId',expected_release,expected_digest),'UTF8')::jsonb IS DISTINCT FROM cache->cache_key THEN RAISE EXCEPTION 'original relationship authority changed' USING ERRCODE='42501';END IF;
  END IF;
 END LOOP;
 RETURN convert_to(jsonb_build_object('context',context,'records',to_jsonb(records))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.build_import_records(bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.process_import_chunk(original_input bytea,original_documents bytea,invocation_id uuid,chunk_index int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE input jsonb;documents jsonb;context jsonb;group_context jsonb;source_map jsonb;selected record;record jsonb;metadata jsonb;
 payload_bytes bytea;payload jsonb;operation jsonb;group_input jsonb;applied jsonb;created jsonb;state text;code text;
 outcomes jsonb[]:='{}';original_records jsonb[]:='{}';counted int;chunk_size int;total_chunks int;budget_rows int;input_digest text;
 origin jsonb;selected_outcome jsonb;result jsonb;source_at text;
BEGIN
 context:=convert_from(truss.batched_import_context(expected_release,expected_digest),'UTF8')::jsonb;
 IF original_input IS NULL OR octet_length(original_input)>8388608 OR original_documents IS NULL OR octet_length(original_documents)>4194304 THEN RAISE EXCEPTION 'bounded original import required' USING ERRCODE='54000';END IF;
 IF (convert_from(original_input,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE OR (convert_from(original_documents,'UTF8') IS JSON ARRAY WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'unique original import required' USING ERRCODE='22023';END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;documents:=convert_from(original_documents,'UTF8')::jsonb;
 IF input-ARRAY['interfaceVersion','layoutProfile','importProfile','valueProfile','catalog','loadId','assertedOrigin','records','chunkSize']<>'{}'::jsonb
  OR input->>'interfaceVersion' IS DISTINCT FROM 'truss-batched-import-input/0.1.0'
  OR input->'layoutProfile' IS DISTINCT FROM context->'layoutProfile' OR input->'importProfile' IS DISTINCT FROM context->'importProfile'
  OR input->'valueProfile' IS DISTINCT FROM context->'valueProfile' OR input->'catalog' IS DISTINCT FROM context->'catalog'
  OR jsonb_typeof(input->'records') IS DISTINCT FROM 'array' OR jsonb_array_length(input->'records')>1024
  OR jsonb_typeof(input->'chunkSize') IS DISTINCT FROM 'string' OR input->>'chunkSize' !~ '^[1-9][0-9]{0,2}$'
  OR (input->>'chunkSize')::int>128 OR jsonb_typeof(input->'loadId') IS DISTINCT FROM 'string' OR octet_length(input->>'loadId') NOT BETWEEN 1 AND 4096
  OR jsonb_typeof(input->'assertedOrigin') IS DISTINCT FROM 'object' OR input->'assertedOrigin'->>'kind' IS DISTINCT FROM 'map'
  OR jsonb_typeof(input->'assertedOrigin'->'entries') IS DISTINCT FROM 'array'
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e WHERE e.value->>'key'='x-load-id' OR e.value->'value'->>'kind' NOT IN ('null','string'))
  OR (SELECT count(*)<>count(DISTINCT e.value->>'key') FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e)
  THEN RAISE EXCEPTION 'selected original chunk profile required' USING ERRCODE='22023';END IF;
 IF (input->'assertedOrigin')-ARRAY['kind','entries']<>'{}'::jsonb
  OR jsonb_array_length(input->'assertedOrigin'->'entries')>1024
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'assertedOrigin'->'entries') e WHERE
   jsonb_typeof(e.value) IS DISTINCT FROM 'object' OR e.value-ARRAY['key','value']<>'{}'::jsonb
   OR jsonb_typeof(e.value->'key') IS DISTINCT FROM 'string' OR jsonb_typeof(e.value->'value') IS DISTINCT FROM 'object'
   OR (e.value->'value')-ARRAY['kind','text']<>'{}'::jsonb
   OR (e.value->'value'->>'kind' IN ('null','string')) IS NOT TRUE
   OR e.value->'value'->>'kind'='null' AND e.value->'value' ? 'text'
   OR e.value->'value'->>'kind'='string' AND jsonb_typeof(e.value->'value'->'text') IS DISTINCT FROM 'string') THEN
  RAISE EXCEPTION 'closed original asserted origin required' USING ERRCODE='22023';END IF;
 origin:=jsonb_set(input->'assertedOrigin','{entries}',(input->'assertedOrigin'->'entries')||jsonb_build_array(jsonb_build_object('key','x-load-id','value',jsonb_build_object('kind','string','text',input->>'loadId'))));
 IF octet_length((input->'assertedOrigin')::text)>1048576 OR octet_length(origin::text)>1048576 THEN
  RAISE EXCEPTION 'bounded original asserted origin required' USING ERRCODE='54000';END IF;
 chunk_size:=(input->>'chunkSize')::int;counted:=jsonb_array_length(input->'records');total_chunks:=greatest(1,(counted+chunk_size-1)/chunk_size);
 IF invocation_id IS NULL OR chunk_index IS NULL OR chunk_index<0 OR chunk_index>=total_chunks THEN RAISE EXCEPTION 'derived original chunk required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(documents)>512 OR EXISTS(SELECT 1 FROM jsonb_array_elements(documents) d WHERE d.value-ARRAY['documentId','sourceText']<>'{}'::jsonb OR jsonb_typeof(d.value->'sourceText') IS DISTINCT FROM 'string')
  OR (SELECT count(*)<>count(DISTINCT d.value->>'documentId') FROM jsonb_array_elements(documents) d) THEN RAISE EXCEPTION 'complete unique original documents required' USING ERRCODE='22023';END IF;
 SELECT coalesce(jsonb_object_agg(d.value->>'documentId',d.value->>'sourceText'),'{}') INTO source_map FROM jsonb_array_elements(documents) d;
 -- Byte/hash admission precedes identity routing, including skipped records.
 -- Payload interpretation remains after the native live/reserved-identity skip.
 FOR record IN SELECT value FROM jsonb_array_elements(input->'records') LOOP
  IF jsonb_typeof(record) IS DISTINCT FROM 'object' OR record-ARRAY['kind','identity','payload','payloadProfile']<>'{}'::jsonb
   OR (record->>'kind' IN ('object','edge')) IS NOT TRUE OR record->'payloadProfile' IS DISTINCT FROM context->'importPayloadProfile'
   OR jsonb_typeof(record->'payload') IS DISTINCT FROM 'object' OR (record->'payload')-ARRAY['identity','bytesBase64','sha256']<>'{}'::jsonb THEN RAISE EXCEPTION 'closed original import record required' USING ERRCODE='22023';END IF;
  payload_bytes:=decode(record->'payload'->>'bytesBase64','base64');
  IF record->'payload'->>'identity' IS DISTINCT FROM record->'payload'->>'sha256' OR payload_bytes IS NULL OR octet_length(payload_bytes) NOT BETWEEN 1 AND 1048576 OR encode(sha256(payload_bytes),'hex') IS DISTINCT FROM record->'payload'->>'sha256' THEN RAISE EXCEPTION 'original payload byte integrity required' USING ERRCODE='22023';END IF;
 END LOOP;
 -- Only finished transactions below every active snapshot are eligible; cleanup
 -- is bounded independently of this call's admitted work.
 DELETE FROM truss.runtime_import_budget WHERE writer_xid IN
  (SELECT writer_xid FROM truss.runtime_import_budget WHERE writer_xid<pg_snapshot_xmin(pg_current_snapshot()) ORDER BY writer_xid LIMIT 128);
 INSERT INTO truss.runtime_import_budget VALUES(pg_current_xact_id(),least(chunk_size,greatest(0,counted-chunk_index*chunk_size)),octet_length(original_input)+octet_length(original_documents))
 ON CONFLICT(writer_xid) DO UPDATE SET records=truss.runtime_import_budget.records+EXCLUDED.records,submitted_bytes=truss.runtime_import_budget.submitted_bytes+EXCLUDED.submitted_bytes
 WHERE truss.runtime_import_budget.records+EXCLUDED.records<=4096 AND truss.runtime_import_budget.submitted_bytes+EXCLUDED.submitted_bytes<=268435456;
 GET DIAGNOSTICS budget_rows=ROW_COUNT;IF budget_rows<>1 THEN RAISE EXCEPTION 'cumulative import work budget exceeded' USING ERRCODE='54000';END IF;
 group_context:=convert_from(truss.group_context(expected_release,expected_digest),'UTF8')::jsonb;
 FOR selected IN SELECT value AS record,(ordinality-1)::int AS input_index FROM jsonb_array_elements(input->'records') WITH ORDINALITY
  ORDER BY (value->>'kind'='edge'),ordinality OFFSET chunk_index*chunk_size LIMIT chunk_size LOOP
  record:=selected.record;original_records:=array_append(original_records,jsonb_build_object('inputIndex',selected.input_index::text,'record',record));
  code:=NULL;
  BEGIN
   IF record->'payloadProfile' IS DISTINCT FROM context->'importPayloadProfile' THEN RAISE EXCEPTION 'selected payload profile required' USING ERRCODE='0A000';END IF;
   IF record->>'kind'='object' THEN
    metadata:=convert_from(truss.import_object_identity(convert_to((record->'identity')::text,'UTF8'),convert_to(source_map->>(record->'identity'->'type'->'owner'->>'documentId'),'UTF8'),NULL,expected_release,expected_digest),'UTF8')::jsonb;
   ELSIF record->>'kind'='edge' THEN metadata:=convert_from(truss.import_edge_identity(convert_to((record->'identity')::text,'UTF8'),expected_release,expected_digest),'UTF8')::jsonb;
   ELSE RAISE EXCEPTION 'object or edge import required' USING ERRCODE='22023';END IF;
   IF metadata->>'state'='skipped' THEN
    selected_outcome:=jsonb_build_object('inputIndex',selected.input_index::text,'outcome','skipped','reason',metadata->>'reason');
    IF metadata ? 'identity' THEN selected_outcome:=selected_outcome||jsonb_build_object('identity',metadata->'identity');END IF;
   ELSE
    code:='invalid_payload';
    BEGIN
    payload_bytes:=decode(record->'payload'->>'bytesBase64','base64');
    IF octet_length(payload_bytes) NOT BETWEEN 1 AND 1048576 OR encode(sha256(payload_bytes),'hex') IS DISTINCT FROM record->'payload'->>'sha256'
     OR (convert_from(payload_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'original payload integrity required' USING ERRCODE='22023';END IF;
    payload:=convert_from(payload_bytes,'UTF8')::jsonb;
    IF payload->>'interfaceVersion' IS DISTINCT FROM 'truss-import-payload/0.1.0' OR payload->>'kind' IS DISTINCT FROM record->>'kind' THEN RAISE EXCEPTION 'exact original payload required' USING ERRCODE='22023';END IF;
    IF jsonb_typeof(payload->'values') IS DISTINCT FROM 'array'
     OR jsonb_array_length(payload->'values')>1024
     OR (SELECT count(*)<>count(DISTINCT v.value->>'name') FROM jsonb_array_elements(payload->'values') v)
     OR EXISTS(SELECT 1 FROM jsonb_array_elements(payload->'values') v WHERE jsonb_typeof(v.value) IS DISTINCT FROM 'object'
      OR v.value-ARRAY['name','value']<>'{}'::jsonb OR jsonb_typeof(v.value->'name') IS DISTINCT FROM 'string') THEN
     RAISE EXCEPTION 'unique original authored values required' USING ERRCODE='22023';END IF;
    IF record->>'kind'='object' THEN
     IF payload-ARRAY['interfaceVersion','kind','values','ownership','source']<>'{}'::jsonb
      OR payload->'ownership' IS DISTINCT FROM '{"state":"rootless"}'::jsonb
      OR EXISTS(SELECT 1 FROM jsonb_array_elements(metadata->'primaryFields') f WHERE NOT EXISTS(
       SELECT 1 FROM jsonb_array_elements(payload->'values') v WHERE v.value->>'name'=f.value->>'name' AND v.value->'value'=f.value->'value')) THEN
      RAISE EXCEPTION 'original primary field/payload agreement required' USING ERRCODE='22023';END IF;
    ELSIF payload-ARRAY['interfaceVersion','kind','values','orderKey','source']<>'{}'::jsonb
     OR payload->'orderKey' IS DISTINCT FROM '{"state":"null"}'::jsonb AND
      (jsonb_typeof(payload->'orderKey') IS DISTINCT FROM 'object' OR (payload->'orderKey')-ARRAY['state','text']<>'{}'::jsonb
       OR payload->'orderKey'->>'state' IS DISTINCT FROM 'text' OR jsonb_typeof(payload->'orderKey'->'text') IS DISTINCT FROM 'string') THEN
     RAISE EXCEPTION 'closed original edge payload required' USING ERRCODE='22023';END IF;
    IF payload ? 'source' AND (jsonb_typeof(payload->'source') IS DISTINCT FROM 'object'
     OR (payload->'source')-ARRAY['kind','entries']<>'{}'::jsonb OR payload->'source'->>'kind' IS DISTINCT FROM 'map'
     OR jsonb_typeof(payload->'source'->'entries') IS DISTINCT FROM 'array'
     OR (SELECT count(*)<>count(DISTINCT e.value->>'key') FROM jsonb_array_elements(payload->'source'->'entries') e)
     OR EXISTS(SELECT 1 FROM jsonb_array_elements(payload->'source'->'entries') e WHERE e.value-ARRAY['key','value']<>'{}'::jsonb
      OR jsonb_typeof(e.value->'key') IS DISTINCT FROM 'string' OR e.value->>'key' IN ('author','at','system') AND
       (e.value->'value'->>'kind' IN ('string','null')) IS NOT TRUE)) THEN
     RAISE EXCEPTION 'closed original source fields required' USING ERRCODE='22023';END IF;
    SELECT e.value->'value'->>'text' INTO source_at FROM jsonb_array_elements(coalesce(payload->'source'->'entries','[]'::jsonb)) e WHERE e.value->>'key'='at' AND e.value->'value'->>'kind'='string';
    IF source_at IS NOT NULL THEN
     BEGIN PERFORM truss.query_timestamp_instant_key(source_at,'umf-rfc3339-exact-instant/1.0.0');
     EXCEPTION WHEN data_exception THEN RAISE EXCEPTION 'selected source.at exact instant required' USING ERRCODE='22023';END;
    END IF;
    IF record->>'kind'='object' THEN operation:=jsonb_build_object('operation','create_object','typeDefinitionPin',metadata->>'definitionPin','values',payload->'values','ownership',payload->'ownership');
    ELSE operation:=jsonb_build_object('operation','create_edge','relationshipDefinitionPin',record->'identity'->>'relationshipDefinitionPin','source',jsonb_build_object('state','stored','identity',record->'identity'->'source'),'target',jsonb_build_object('state','stored','identity',record->'identity'->'target'),'values',payload->'values','orderKey',payload->'orderKey');END IF;
    group_input:=jsonb_build_object('interfaceVersion','truss-group-input/0.1.0','layoutProfile',group_context->'layoutProfile','mutationProfile',group_context->'mutationProfile','valueProfile',group_context->'valueProfile','catalog',jsonb_build_object('selection','current'),'preconditions','[]'::jsonb,'operations',jsonb_build_array(operation),'assertedOrigin',origin);
    EXCEPTION WHEN SQLSTATE '22021' OR SQLSTATE '22P05' OR SQLSTATE '22P02' THEN
     RAISE EXCEPTION 'eligible original payload encoding required' USING ERRCODE='22023';
    END;
    code:=NULL;
    applied:=convert_from(truss.apply_group(convert_to(group_input::text,'UTF8'),original_documents,convert_to('{"state":"none"}','UTF8'),expected_release,expected_digest),'UTF8')::jsonb;
    IF applied->>'outcome'<>'success' THEN
     state:=CASE WHEN applied->>'outcome'='failed' THEN applied->>'nativeState' WHEN applied->>'reason'='resource' THEN '54000' WHEN applied->>'reason'='observation' THEN '55P03' ELSE '0A000' END;
     IF state IS NULL THEN state:='22023';END IF;RAISE EXCEPTION 'import record refused' USING ERRCODE=state;
    END IF;
    created:=applied->'semantic'->'results'->0;
    PERFORM truss.import_record_source((applied->>'attemptId')::uuid,convert_to(record::text,'UTF8'),input->>'loadId');
    selected_outcome:=jsonb_build_object('inputIndex',selected.input_index::text,'outcome','created','identity',created->'identity','version',created->>'version','groupAttemptId',applied->>'attemptId');
   END IF;
  EXCEPTION WHEN SQLSTATE '22023' OR SQLSTATE '23505' OR SQLSTATE '42501' OR SQLSTATE '0A000' OR SQLSTATE 'P1004' OR SQLSTATE 'P1005' THEN
   GET STACKED DIAGNOSTICS state=RETURNED_SQLSTATE;
   code:=coalesce(code,CASE state WHEN '22023' THEN 'invalid' WHEN '23505' THEN 'conflict' WHEN '42501' THEN 'unauthorized' WHEN '0A000' THEN 'unsupported_profile' WHEN 'P1004' THEN 'missing_endpoint' ELSE 'dependencies' END);
   selected_outcome:=jsonb_build_object('inputIndex',selected.input_index::text,'outcome','rejected','code',code);
  END;
  outcomes:=array_append(outcomes,selected_outcome);
 END LOOP;
 FOR selected IN SELECT r.value AS original,o.value AS result FROM unnest(original_records) r(value) JOIN unnest(outcomes) o(value) ON r.value->>'inputIndex'=o.value->>'inputIndex' LOOP
  IF selected.result->>'outcome' IN ('created','skipped') THEN PERFORM truss.import_report_record_authority(convert_to(jsonb_build_object('originalIdentity',selected.original->'record'->'identity','outcomeIdentity',selected.result->'identity')::text,'UTF8'),selected.original->'record'->>'kind',expected_release,expected_digest);END IF;
 END LOOP;
 IF convert_from(truss.batched_import_context(expected_release,expected_digest),'UTF8')::jsonb IS DISTINCT FROM context THEN RAISE EXCEPTION 'original import context changed' USING ERRCODE='42501';END IF;
 input_digest:=encode(sha256(convert_to('truss-batched-import-input/0.1.0'||chr(10),'UTF8')||original_input),'hex');
 PERFORM truss.runtime_record_import_load(invocation_id,chunk_index,total_chunks,input->>'loadId',input->'assertedOrigin',input_digest,counted,input->'records',to_jsonb(original_records),to_jsonb(outcomes),expected_release,expected_digest);
 result:=jsonb_build_object('context',context,'outcomes',to_jsonb(outcomes),'hostTransactionId','truss-pending-transaction:'||(context->>'sourceEpoch')||':'||pg_current_xact_id()::text);
 IF octet_length(result::text)>8388608 THEN RAISE EXCEPTION 'bounded complete import report required' USING ERRCODE='54000';END IF;
 RETURN convert_to(result::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.process_import_chunk(bytea,bytea,uuid,int,text,text) FROM PUBLIC;


CREATE FUNCTION truss.validate_batched_import_report(original_input bytea,original_outcomes bytea,original_context bytea,expected_release text,expected_digest text) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE input jsonb;outcomes jsonb;context jsonb;item jsonb;record jsonb;
BEGIN
 IF octet_length(original_input)>8388608 OR octet_length(original_outcomes)>8388608 OR octet_length(original_context)>1048576 THEN RAISE EXCEPTION 'bounded original report required' USING ERRCODE='54000';END IF;
 input:=convert_from(original_input,'UTF8')::jsonb;outcomes:=convert_from(original_outcomes,'UTF8')::jsonb;context:=convert_from(original_context,'UTF8')::jsonb;
 IF convert_from(truss.batched_import_context(expected_release,expected_digest),'UTF8')::jsonb IS DISTINCT FROM context THEN RAISE EXCEPTION 'original report context required' USING ERRCODE='42501';END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(outcomes) LOOP
  IF item->>'outcome' IN ('created','skipped') THEN
   record:=input->'records'->(item->>'inputIndex')::int;
   PERFORM truss.import_report_record_authority(convert_to(jsonb_build_object('originalIdentity',record->'identity','outcomeIdentity',item->'identity')::text,'UTF8'),record->>'kind',expected_release,expected_digest);
  END IF;
 END LOOP;
 IF convert_from(truss.batched_import_context(expected_release,expected_digest),'UTF8')::jsonb IS DISTINCT FROM context THEN RAISE EXCEPTION 'original report authority changed' USING ERRCODE='42501';END IF;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.validate_batched_import_report(bytea,bytea,bytea,text,text) FROM PUBLIC;
