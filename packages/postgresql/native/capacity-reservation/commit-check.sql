-- Private explicit capacity closeout, not the seven semantic commit guards.
-- Original protected finalizer must call under its registered transaction custody.
CREATE FUNCTION truss.capacity_commit_check_original(layout_bytes bytea, resource_bytes bytea)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE ledger truss.row_home_capacity%ROWTYPE;
BEGIN
  -- Full scope, original head/ledger exclusion and complete size/counter parity.
  PERFORM truss.capacity_verify_inventory_original(layout_bytes,resource_bytes);
  SELECT c.* INTO STRICT ledger FROM truss.row_home_capacity c WHERE c.singleton_id=1;
  IF ledger.reserved_rows<>0 OR ledger.reserved_custody_bytes<>0
    OR ledger.reservation_writer_xid IS NOT NULL
    OR ledger.reservation_operation_ordinal IS NOT NULL
    OR ledger.reservation_context_bytes IS NOT NULL
    OR ledger.reservation_plan_bytes IS NOT NULL
    OR ledger.reservation_initial_rows IS NOT NULL
    OR ledger.reservation_initial_custody_bytes IS NOT NULL THEN
    RAISE EXCEPTION 'original reservation must be released before commit' USING ERRCODE='55000';
  END IF;
  -- A persisted foreign unfinished row is not exempt from closeout. No repair,
  -- phase rewrite, capacity eviction or current-xid-only accounting here.
  IF EXISTS (SELECT 1 FROM truss.row_home_operation o WHERE o.phase<>'application_finalized') THEN
    RAISE EXCEPTION 'complete retained operation closeout required' USING ERRCODE='55000';
  END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.capacity_commit_check_original(bytea,bytea) FROM PUBLIC;
