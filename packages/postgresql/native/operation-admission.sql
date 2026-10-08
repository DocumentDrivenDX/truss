-- Internal operation admission on the original 0.13 registry.
-- No public EXECUTE or capability readiness. Full producer/finalizer follows separately.
CREATE FUNCTION truss.runtime_admit_operation(
  kind text, definition_bytes bytea, input_bytes bytea, prestate_bytes bytea,
  candidate_bytes bytea, obligation_bytes bytea, group_bytes bytea
) RETURNS TABLE(writer_xid text, ordinal text, context_hex text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  native_xid xid8;
  head_revision int;
  next_ordinal bigint;
  native_context bytea;
  item bytea;
  total_bytes bigint := 0;
BEGIN
  IF kind IS NULL OR kind NOT IN ('mutation','import','catalog-transform',
       'catalog-acceptance','home-migration','administrative-repair') THEN
    RAISE EXCEPTION 'unsupported operation kind' USING ERRCODE='22023';
  END IF;
  FOREACH item IN ARRAY ARRAY[definition_bytes,input_bytes,prestate_bytes,
      candidate_bytes,obligation_bytes,group_bytes] LOOP
    IF item IS NULL OR octet_length(item) NOT BETWEEN 1 AND 1048576 THEN
      RAISE EXCEPTION 'original artifact bound' USING ERRCODE='22023';
    END IF;
    total_bytes := total_bytes + octet_length(item);
  END LOOP;
  IF total_bytes > 4194304 THEN
    RAISE EXCEPTION 'operation artifact aggregate bound' USING ERRCODE='54000';
  END IF;
  -- Catalog exclusion precedes operation-registry and business locks.
  -- Never upgrade an earlier shared head admission in this internal profile.
  IF kind='catalog-acceptance' THEN
    IF EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
        AND l.relation='truss.schema_head'::regclass AND l.mode IN ('RowShareLock','RowExclusiveLock'))
        AND NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
          AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock')) THEN
      RAISE EXCEPTION 'earlier shared head admission cannot upgrade to catalog exclusion' USING ERRCODE='55000';
    END IF;
    LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
  END IF;
  SELECT h.rev INTO STRICT head_revision FROM truss.schema_head h WHERE h.id=1 FOR SHARE;
  native_xid := pg_current_xact_id();
  IF EXISTS (SELECT 1 FROM truss.row_home_operation AS o
      WHERE o.original_writer_xid=native_xid AND o.phase<>'application_finalized') THEN
    RAISE EXCEPTION 'unfinished operation' USING ERRCODE='55000';
  END IF;
  SELECT coalesce(max(o.operation_ordinal)+1,0) INTO next_ordinal
    FROM truss.row_home_operation AS o WHERE o.original_writer_xid=native_xid;
  native_context := convert_to(jsonb_build_object(
    'interfaceVersion','truss-native-operation-context/0.1',
    'xid',native_xid::text,'ordinal',next_ordinal::text,
    'sessionUser',session_user::text,'actingUser',current_user::text,
    'database',current_database(),'backendPid',pg_backend_pid()::text
  )::text,'UTF8');
  INSERT INTO truss.row_home_operation(original_writer_xid,operation_ordinal,
    operation_kind,phase,effect_generation,original_context_bytes,
    original_definition_bytes,original_input_bytes,original_prestate_bytes,
    admitted_candidate_bytes,effect_obligation_bytes,original_group_custody_bytes)
  VALUES(native_xid,next_ordinal,kind,'admitted',0,native_context,
    definition_bytes,input_bytes,prestate_bytes,candidate_bytes,obligation_bytes,group_bytes);
  RETURN QUERY SELECT native_xid::text,next_ordinal::text,encode(native_context,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_admit_operation(text,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC;
