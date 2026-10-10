-- Private already-encoded membership persistence; installed namespace/codec authority
-- and complete all-key planning remain the original protected producer's obligation.
CREATE FUNCTION truss.runtime_stage_object_key(owner_id bigint,owner_type_id int,key_number smallint,
  original_namespace bytea,encoded_key bytea,original_context bytea)
RETURNS text LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  op truss.row_home_operation%ROWTYPE;
  namespace_route bytea;
  key_route bytea;
  generation bigint;
  scan_count bigint;
  scan_bytes bigint;
  reuse_policy text;
  stored_id bigint;
BEGIN
  SELECT * INTO STRICT op FROM truss.row_home_operation o
    WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.phase<>'admitted' OR owner_id IS NULL OR owner_type_id IS NULL OR key_number IS NULL
      OR original_namespace IS NULL OR octet_length(original_namespace) NOT BETWEEN 1 AND 65536
      OR encoded_key IS NULL OR octet_length(encoded_key) NOT BETWEEN 1 AND 1048576
      OR original_context IS NULL OR octet_length(original_context) NOT BETWEEN 1 AND 1048576 THEN
    RAISE EXCEPTION 'original key membership admission required' USING ERRCODE='22023';
  END IF;
  IF convert_from(encoded_key,'UTF8') !~ '^umf-key-tuple-v1:hex:([0-9a-f]{2})+$' THEN
    RAISE EXCEPTION 'unsupported canonical key transport' USING ERRCODE='22023';
  END IF;
  SELECT s.value #>> '{}' INTO STRICT reuse_policy FROM truss.setting s WHERE s.key='key_reuse';
  IF reuse_policy NOT IN ('forbid','allow') OR reuse_policy IS NULL THEN
    RAISE EXCEPTION 'unsupported original key reuse policy' USING ERRCODE='55000';
  END IF;
  namespace_route:=sha256(original_namespace);key_route:=sha256(encoded_key);
  -- A native uniqueness race is a retry/refusal, never proof of empty membership.
  UPDATE truss.key_bucket_guard g SET generation=g.generation
    WHERE g.namespace_sha256=namespace_route AND g.key_sha256=key_route RETURNING g.generation INTO generation;
  IF NOT FOUND THEN
    INSERT INTO truss.key_bucket_guard(namespace_sha256,key_sha256,generation)
      VALUES(namespace_route,key_route,0) RETURNING key_bucket_guard.generation INTO generation;
  END IF;
  SELECT count(*),coalesce(sum(bytes),0) INTO scan_count,scan_bytes FROM (
    (SELECT (octet_length(b.namespace_bytes)::bigint+octet_length(b.key_bytes)) AS bytes
      FROM truss.object_key_bucket b WHERE b.namespace_sha256=namespace_route AND b.key_sha256=key_route LIMIT 10001)
    UNION ALL
    (SELECT (octet_length(b.namespace_bytes)::bigint+octet_length(b.key_bytes)) AS bytes
      FROM truss.object_key_reservation_bucket b WHERE b.namespace_sha256=namespace_route AND b.key_sha256=key_route LIMIT 10001)
  ) candidates;
  IF scan_count>10000 OR scan_bytes>16777216 THEN RAISE EXCEPTION 'key collision inventory bound' USING ERRCODE='54000'; END IF;
  IF EXISTS(SELECT 1 FROM truss.object_key_bucket b WHERE b.namespace_sha256=namespace_route AND b.key_sha256=key_route
      AND b.namespace_bytes=original_namespace AND b.key_bytes=encoded_key)
      OR (reuse_policy='forbid' AND EXISTS(SELECT 1 FROM truss.object_key_reservation_bucket b
        WHERE b.namespace_sha256=namespace_route AND b.key_sha256=key_route
          AND b.namespace_bytes=original_namespace AND b.key_bytes=encoded_key)) THEN
    RAISE EXCEPTION 'original full-byte key identity conflicts' USING ERRCODE='23505';
  END IF;
  IF generation=9223372036854775807 OR op.effect_generation=9223372036854775807 THEN
    RAISE EXCEPTION 'key membership generation exhausted' USING ERRCODE='54000';
  END IF;
  PERFORM 1 FROM truss.key_def k WHERE k.type_id=owner_type_id AND k.key_num=key_number AND k.retired_rev IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'missing active original key definition' USING ERRCODE='55000'; END IF;
  PERFORM 1 FROM truss.object o WHERE o.id=owner_id AND o.type_id=owner_type_id FOR NO KEY UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'missing typed original key owner' USING ERRCODE='55000'; END IF;
  INSERT INTO truss.object_key_bucket(type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
    VALUES(owner_type_id,key_number,owner_id,original_namespace,encoded_key,original_context)
    RETURNING storage_row_id INTO stored_id;
  RETURN stored_id::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_object_key(bigint,int,smallint,bytea,bytea,bytea) FROM PUBLIC;
