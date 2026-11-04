-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Private native opaque continuation custody. Reuses the installed reader
-- validator's secret + fixed payload digest construction; no cursor registry
-- writes, extension, data authority or cross-page snapshot is introduced.
CREATE FUNCTION truss.query_temporal_cursor_encode(binding jsonb,original_context bytea,original_after text,sort_kinds jsonb)
RETURNS TABLE(cursor_bytes bytea,after_json text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;actor oid;after_value jsonb;selected_key jsonb;
 states jsonb:='[]';state jsonb;kind text;token text;ordinal int;payload jsonb;seal text;
BEGIN
 PERFORM truss.query_temporal_scope(binding);actor:=truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF original_context IS NULL OR octet_length(original_context) NOT BETWEEN 1 AND 4194304
  OR original_after IS NULL OR octet_length(original_after) NOT BETWEEN 1 AND 1048576
  OR (original_after IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
  OR jsonb_typeof(sort_kinds) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'bounded original temporal continuation inputs required' USING ERRCODE='22023';END IF;
 after_value:=original_after::jsonb;selected_key:=after_value->'selectedKey';
 IF after_value-ARRAY['version','selectedKey','sortValues','keyValues']<>'{}'::jsonb
  OR after_value->>'version' IS DISTINCT FROM 'weft.engine-temporal-after/0.2'
  OR jsonb_typeof(selected_key) IS DISTINCT FROM 'object' OR selected_key-ARRAY['module','record','key']<>'{}'::jsonb
  OR (SELECT count(*) FROM jsonb_object_keys(selected_key))<>3
  OR EXISTS(SELECT 1 FROM jsonb_each(selected_key) e WHERE jsonb_typeof(e.value)<>'string' OR octet_length(e.value#>>'{}') NOT BETWEEN 1 AND 4096)
  OR jsonb_typeof(after_value->'sortValues') IS DISTINCT FROM 'array'
  OR jsonb_typeof(after_value->'keyValues') IS DISTINCT FROM 'array'
  OR jsonb_array_length(after_value->'sortValues') NOT BETWEEN 1 AND 1024
  OR jsonb_array_length(after_value->'sortValues')<>jsonb_array_length(sort_kinds)
  OR jsonb_array_length(after_value->'keyValues') NOT BETWEEN 1 AND 1024
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(after_value->'keyValues') k WHERE jsonb_typeof(k.value)<>'string')
  OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r
   CROSS JOIN LATERAL jsonb_array_elements(r.value->'keys') k
   WHERE r.value->'identity'->>'module'=selected_key->>'module'
    AND r.value->'identity'->>'element'=selected_key->>'record' AND k.value->>'keyId'=selected_key->>'key') THEN
  RAISE EXCEPTION 'complete original selected Key and continuation tuple required' USING ERRCODE='22023';END IF;
 FOR ordinal IN 0..jsonb_array_length(sort_kinds)-1 LOOP
  kind:=sort_kinds->>ordinal;state:=after_value->'sortValues'->ordinal;
  IF kind IS NULL OR kind NOT IN ('string','date','instant','local') OR jsonb_typeof(sort_kinds->ordinal)<>'string'
   OR jsonb_typeof(state) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'closed temporal continuation kind and state required' USING ERRCODE='22023';END IF;
  IF state->>'state'='present' THEN
   IF state-ARRAY['state','value']<>'{}'::jsonb OR jsonb_typeof(state->'value') IS DISTINCT FROM 'string' THEN
    RAISE EXCEPTION 'exact present temporal continuation required' USING ERRCODE='22023';END IF;
   token:=state->>'value';
   IF kind<>'string' THEN token:=truss.query_temporal_canonical_text(kind,token);END IF;
   states:=states||jsonb_build_array(jsonb_build_object('state','present','value',token));
  ELSIF state=jsonb_build_object('state','missing') OR state=jsonb_build_object('state','null') THEN
   states:=states||jsonb_build_array(state);
  ELSE RAISE EXCEPTION 'closed temporal continuation state required' USING ERRCODE='22023';END IF;
 END LOOP;
 after_value:=jsonb_set(after_value,'{sortValues}',states);after_json:=after_value::text;
 payload:=jsonb_build_object('profile','truss-query-temporal-cursor/0.2','installationId',installation.installation_id::text,
  'sourceEpoch',installation.source_epoch::text,'releaseSha256',installation.release_sha256,'queryAbi',truss.query_temporal_abi(),
  'catalogRevision',(binding->>'catalogRevision'),'actorOid',actor::text,
  'contextSha256',encode(sha256(original_context),'hex'),'afterJson',after_json);
 SELECT encode(sha256(s.secret||sha256(convert_to(payload::text,'UTF8'))),'hex') INTO STRICT seal
  FROM truss.reader_catalog_validator_secret s;
 cursor_bytes:=convert_to(jsonb_build_object('payload',payload,'digest',seal)::text,'UTF8');
 IF octet_length(cursor_bytes)>65536 THEN RAISE EXCEPTION 'opaque temporal continuation limit exceeded' USING ERRCODE='54000';END IF;
 PERFORM truss.query_temporal_scope(binding);
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_cursor_encode(jsonb,bytea,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_cursor_decode(binding jsonb,original_context bytea,original_cursor bytea) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;actor oid;envelope jsonb;payload jsonb;expected text;
BEGIN
 PERFORM truss.query_temporal_scope(binding);actor:=truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF original_context IS NULL OR octet_length(original_context) NOT BETWEEN 1 AND 4194304
  OR original_cursor IS NULL OR octet_length(original_cursor) NOT BETWEEN 1 AND 65536
  OR (convert_from(original_cursor,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'bounded original opaque temporal cursor required' USING ERRCODE='22023';END IF;
 envelope:=convert_from(original_cursor,'UTF8')::jsonb;payload:=envelope->'payload';
 IF envelope-ARRAY['payload','digest']<>'{}'::jsonb OR (SELECT count(*) FROM jsonb_object_keys(envelope))<>2
  OR jsonb_typeof(payload) IS DISTINCT FROM 'object'
  OR payload-ARRAY['profile','installationId','sourceEpoch','releaseSha256','queryAbi','catalogRevision','actorOid','contextSha256','afterJson']<>'{}'::jsonb
  OR (SELECT count(*) FROM jsonb_object_keys(payload))<>9
  OR EXISTS(SELECT 1 FROM jsonb_each(payload) e WHERE e.key<>'queryAbi' AND jsonb_typeof(e.value)<>'string')
  OR jsonb_typeof(envelope->'digest') IS DISTINCT FROM 'string' OR (envelope->>'digest' ~ '^[0-9a-f]{64}$') IS NOT TRUE THEN
  RAISE EXCEPTION 'closed native temporal cursor envelope required' USING ERRCODE='22023';END IF;
 SELECT encode(sha256(s.secret||sha256(convert_to(payload::text,'UTF8'))),'hex') INTO STRICT expected
  FROM truss.reader_catalog_validator_secret s;
 IF envelope->>'digest' IS DISTINCT FROM expected OR payload->>'profile' IS DISTINCT FROM 'truss-query-temporal-cursor/0.2'
  OR payload->>'installationId' IS DISTINCT FROM installation.installation_id::text
  OR payload->>'sourceEpoch' IS DISTINCT FROM installation.source_epoch::text
  OR payload->>'releaseSha256' IS DISTINCT FROM installation.release_sha256
  OR payload->'queryAbi' IS DISTINCT FROM truss.query_temporal_abi()
  OR payload->>'catalogRevision' IS DISTINCT FROM binding->>'catalogRevision'
  OR payload->>'actorOid' IS DISTINCT FROM actor::text
  OR payload->>'contextSha256' IS DISTINCT FROM encode(sha256(original_context),'hex') THEN
  RAISE EXCEPTION 'original person and complete temporal cursor context required' USING ERRCODE='P1002';END IF;
 IF octet_length(payload->>'afterJson') NOT BETWEEN 1 AND 1048576
  OR ((payload->>'afterJson') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'original native temporal continuation packet required' USING ERRCODE='22023';END IF;
 PERFORM truss.query_temporal_scope(binding);
 RETURN payload->>'afterJson';
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_cursor_decode(jsonb,bytea,bytea) FROM PUBLIC;

CREATE FUNCTION truss.person_query_temporal_cursor_encode(binding jsonb,original_context bytea,original_after text,sort_kinds jsonb)
RETURNS TABLE(cursor_bytes bytea,after_json text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_temporal_cursor_encode(jsonb,bytea,text,jsonb)'::regprocedure,'read');
 RETURN QUERY SELECT * FROM truss.query_temporal_cursor_encode(binding,original_context,original_after,sort_kinds);
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_temporal_cursor_encode(jsonb,bytea,text,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.person_query_temporal_cursor_decode(binding jsonb,original_context bytea,original_cursor bytea) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_person_invocation('truss.query_temporal_cursor_decode(jsonb,bytea,bytea)'::regprocedure,'read');
 RETURN truss.query_temporal_cursor_decode(binding,original_context,original_cursor);
END;
$$;
REVOKE ALL ON FUNCTION truss.person_query_temporal_cursor_decode(jsonb,bytea,bytea) FROM PUBLIC;
