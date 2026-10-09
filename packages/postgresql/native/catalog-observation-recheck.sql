-- Private native observation liveness check; not report/issuer/finalizer authority.
CREATE FUNCTION truss.runtime_require_catalog_observation(expected_writer_xid text,expected_ordinal text,expected_generation text)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; actual_xid xid8:=pg_current_xact_id_if_assigned();
BEGIN
 IF expected_writer_xid IS NULL OR expected_ordinal IS NULL OR expected_generation IS NULL
  OR octet_length(expected_writer_xid) NOT BETWEEN 1 AND 20
  OR octet_length(expected_ordinal) NOT BETWEEN 1 AND 19 OR octet_length(expected_generation) NOT BETWEEN 1 AND 19 THEN
  RAISE EXCEPTION 'bounded original catalog observation tuple required' USING ERRCODE='55000';
 END IF;
 IF expected_writer_xid !~ '^[1-9][0-9]{0,19}$' OR expected_ordinal !~ '^(0|[1-9][0-9]{0,18})$'
  OR expected_generation !~ '^(0|[1-9][0-9]{0,18})$' OR actual_xid IS NULL OR actual_xid::text<>expected_writer_xid THEN
  RAISE EXCEPTION 'original native transaction observation required' USING ERRCODE='55000';
 END IF;
 SELECT o.* INTO op FROM truss.row_home_operation o WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'original unfinished catalog operation required' USING ERRCODE='55000'; END IF;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' OR op.operation_ordinal::text<>expected_ordinal OR op.effect_generation::text<>expected_generation
  OR NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'catalog observation stale or unrelated' USING ERRCODE='55000';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_require_catalog_observation(text,text,text) FROM PUBLIC;
