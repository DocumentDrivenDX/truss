-- Private PostgreSQL implementation of UMF CONTRACT-040's UMFK1 string grammar.
-- The protected writer supplies values from actual rows in authored key order.
-- Qualified document/type/Key namespace checks belong to that writer.
CREATE FUNCTION truss.verify_umf_string_key_tuple(tuple_bytes bytea,actual_values text[]) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog,pg_temp AS $$
DECLARE position int:=5;total int;component_count int;value_count int;
 number bigint;multiplier bigint;digit int;octet int;prefix_count int;
 field_value text;payload bytea;expected_length int;
BEGIN
 IF tuple_bytes IS NULL OR actual_values IS NULL OR array_ndims(actual_values) IS DISTINCT FROM 1
  OR array_lower(actual_values,1) IS DISTINCT FROM 1 THEN RETURN false; END IF;
 total:=octet_length(tuple_bytes);value_count:=cardinality(actual_values);
 IF total NOT BETWEEN 7 AND 1048576 OR value_count NOT BETWEEN 1 AND 1024
  OR substring(tuple_bytes FROM 1 FOR 5)<>convert_to('UMFK1','UTF8') THEN RETURN false; END IF;
 number:=0;multiplier:=1;prefix_count:=0;
 LOOP
  IF position>=total OR prefix_count>=3 THEN RETURN false; END IF;
  octet:=get_byte(tuple_bytes,position);position:=position+1;prefix_count:=prefix_count+1;
  digit:=octet & 127;number:=number+digit*multiplier;
  IF number>1024 THEN RETURN false; END IF;
  IF octet<128 THEN
   IF prefix_count>1 AND digit=0 THEN RETURN false; END IF;
   EXIT;
  END IF;
  multiplier:=multiplier*128;
 END LOOP;
 component_count:=number::int;
 IF component_count<>value_count THEN RETURN false; END IF;
 FOREACH field_value IN ARRAY actual_values LOOP
  IF field_value IS NULL OR octet_length(field_value)>1048576 OR position>=total OR get_byte(tuple_bytes,position)<>4 THEN RETURN false; END IF;
  position:=position+1;number:=0;multiplier:=1;prefix_count:=0;
  LOOP
   IF position>=total OR prefix_count>=3 THEN RETURN false; END IF;
   octet:=get_byte(tuple_bytes,position);position:=position+1;prefix_count:=prefix_count+1;
   digit:=octet & 127;number:=number+digit*multiplier;
   IF number>1048576 THEN RETURN false; END IF;
   IF octet<128 THEN
    IF prefix_count>1 AND digit=0 THEN RETURN false; END IF;
    EXIT;
   END IF;
   multiplier:=multiplier*128;
  END LOOP;
  payload:=convert_to(field_value,'UTF8');expected_length:=octet_length(payload);
  IF number<>expected_length OR number>total-position
   OR substring(tuple_bytes FROM position+1 FOR expected_length)<>payload THEN RETURN false; END IF;
  position:=position+expected_length;
 END LOOP;
 RETURN position=total;
END;
$$;
REVOKE ALL ON FUNCTION truss.verify_umf_string_key_tuple(bytea,text[]) FROM PUBLIC;

-- Private writer helper: derive expected components from actual object rows.
-- Caller holds the object's mutation lock and the accepted catalog-head lock.
CREATE FUNCTION truss.verify_object_string_key(selected_object bigint,selected_type int,selected_key smallint,tuple_bytes bytea)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE object_row truss.object%ROWTYPE; key_row truss.key_def%ROWTYPE;
 component record;cell jsonb;actual_values text[]:=ARRAY[]::text[];counted int:=0;
BEGIN
 SELECT * INTO object_row FROM truss.object WHERE id=selected_object AND type_id=selected_type;
 IF NOT FOUND OR object_row.root_id IS NOT NULL THEN RETURN false; END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.type_def WHERE type_id=selected_type
   AND kind='record' AND NOT provisional AND retired_rev IS NULL) THEN RETURN false; END IF;
 SELECT * INTO key_row FROM truss.key_def WHERE type_id=selected_type AND key_num=selected_key AND retired_rev IS NULL;
 IF NOT FOUND OR cardinality(key_row.prop_ids) NOT BETWEEN 1 AND 1024 THEN RETURN false; END IF;
 FOR component IN SELECT p.prop_id,p.scalar_type,p.retired_rev,p.home,p.cardinality,p.nullability
  FROM unnest(key_row.prop_ids) WITH ORDINALITY k(prop_id,ord)
  JOIN truss.prop_def p ON p.prop_id=k.prop_id AND p.type_id=selected_type ORDER BY k.ord LOOP
  counted:=counted+1;
  IF component.scalar_type IS DISTINCT FROM 'string' OR component.retired_rev IS NOT NULL
   OR component.home IS DISTINCT FROM 'json' OR component.cardinality IS DISTINCT FROM 'one'
   OR component.nullability IS DISTINCT FROM 'required' THEN RETURN false; END IF;
  cell:=object_row.props->component.prop_id::text;
  IF jsonb_typeof(cell) IS DISTINCT FROM 'object' OR cell->>'kind' IS DISTINCT FROM 'string'
   OR jsonb_typeof(cell->'text') IS DISTINCT FROM 'string' OR cell-'kind'-'text'<>'{}'::jsonb THEN RETURN false; END IF;
  actual_values:=array_append(actual_values,cell->>'text');
 END LOOP;
 IF counted<>cardinality(key_row.prop_ids) THEN RETURN false; END IF;
 RETURN truss.verify_umf_string_key_tuple(tuple_bytes,actual_values);
END;
$$;
REVOKE ALL ON FUNCTION truss.verify_object_string_key(bigint,int,smallint,bytea) FROM PUBLIC;

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
