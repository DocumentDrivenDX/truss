-- Private key-route exclusion and complete bounded conflict observation.
-- The writer derives namespace/verified tuple transport before calling this.
CREATE FUNCTION truss.lock_string_key_bucket(original_namespace bytea,canonical_key bytea)
RETURNS TABLE(generation bigint,member_ids bigint[],reservation_ids bigint[])
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE namespace_route bytea;key_route bytea;guard_generation bigint;
 exclusion bigint;candidate_count bigint;candidate_bytes bigint;
 inserted_namespace bytea;inserted_key bytea;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN
  RAISE EXCEPTION 'current key observation requires READ COMMITTED' USING ERRCODE='0A000'; END IF;
 IF original_namespace IS NULL OR octet_length(original_namespace) NOT BETWEEN 1 AND 65536
  OR canonical_key IS NULL OR octet_length(canonical_key) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'bounded original key routing bytes required' USING ERRCODE='22023'; END IF;
 IF convert_from(canonical_key,'UTF8') !~ '^umf-key-tuple-v1:hex:([0-9a-f]{2})+$' THEN
  RAISE EXCEPTION 'selected canonical key transport required' USING ERRCODE='22023'; END IF;
 namespace_route:=sha256(original_namespace);key_route:=sha256(canonical_key);
 exclusion:=('x'||substring(encode(sha256(namespace_route||key_route),'hex') FROM 1 FOR 16))::bit(64)::bigint;
 IF NOT pg_try_advisory_xact_lock(exclusion) THEN
  RAISE EXCEPTION 'key route is in flight' USING ERRCODE='55P03'; END IF;
 SELECT g.generation INTO guard_generation FROM truss.key_bucket_guard g
  WHERE namespace_sha256=namespace_route AND key_sha256=key_route FOR UPDATE NOWAIT;
 IF NOT FOUND THEN
  INSERT INTO truss.key_bucket_guard(namespace_sha256,key_sha256,generation)
   VALUES(namespace_route,key_route,0)
   RETURNING namespace_sha256,key_sha256,key_bucket_guard.generation INTO inserted_namespace,inserted_key,guard_generation;
  IF NOT FOUND OR inserted_namespace IS DISTINCT FROM namespace_route OR inserted_key IS DISTINCT FROM key_route OR guard_generation IS DISTINCT FROM 0 THEN
   RAISE EXCEPTION 'exact zero-generation native key guard creation required' USING ERRCODE='55000'; END IF;
  SELECT g.generation INTO guard_generation FROM truss.key_bucket_guard g
   WHERE namespace_sha256=namespace_route AND key_sha256=key_route FOR UPDATE NOWAIT;
  IF NOT FOUND OR guard_generation IS DISTINCT FROM 0 THEN
   RAISE EXCEPTION 'exact native key guard readback required' USING ERRCODE='55000'; END IF;
 END IF;
 SELECT count(*),coalesce(sum(size),0) INTO candidate_count,candidate_bytes FROM (
  (SELECT octet_length(namespace_bytes)::bigint+octet_length(key_bytes) AS size
   FROM truss.object_key_bucket WHERE namespace_sha256=namespace_route AND key_sha256=key_route LIMIT 10001)
  UNION ALL
  (SELECT octet_length(namespace_bytes)::bigint+octet_length(key_bytes) AS size
   FROM truss.object_key_reservation_bucket WHERE namespace_sha256=namespace_route AND key_sha256=key_route LIMIT 10001)
 ) candidates;
 IF candidate_count>10000 OR candidate_bytes>16777216 THEN
  RAISE EXCEPTION 'complete collision bucket exceeds limits' USING ERRCODE='54000'; END IF;
 IF guard_generation=9223372036854775807 THEN
  RAISE EXCEPTION 'key guard generation exhausted' USING ERRCODE='54000'; END IF;
 RETURN QUERY SELECT guard_generation,
  ARRAY(SELECT storage_row_id FROM truss.object_key_bucket WHERE namespace_sha256=namespace_route AND key_sha256=key_route
    AND namespace_bytes=original_namespace AND key_bytes=canonical_key ORDER BY storage_row_id),
  ARRAY(SELECT storage_row_id FROM truss.object_key_reservation_bucket WHERE namespace_sha256=namespace_route AND key_sha256=key_route
    AND namespace_bytes=original_namespace AND key_bytes=canonical_key ORDER BY storage_row_id);
END;
$$;
REVOKE ALL ON FUNCTION truss.lock_string_key_bucket(bytea,bytea) FROM PUBLIC;
