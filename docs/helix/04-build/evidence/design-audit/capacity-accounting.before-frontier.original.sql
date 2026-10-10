-- Private accounting component; not a public reservation/authority factory.
-- Original trusted producer supplies prevalidated plan/budgets and exact installed
-- originals. Full inventory/account/security/native-work admission is external.
-- No ordinary-role grant or installer readiness is established by this source.
CREATE FUNCTION truss.capacity_reserve_original(
  issued_ordinal bigint, context_bytes bytea, plan_bytes bytea,
  row_budget bigint, byte_budget bigint, layout_bytes bytea, resource_bytes bytea
) RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp AS $$
DECLARE
  actual_xid xid8;
  ledger truss.row_home_capacity%ROWTYPE;
  head_revision integer;
BEGIN
  IF issued_ordinal IS NULL OR issued_ordinal < 0
    OR context_bytes IS NULL OR octet_length(context_bytes) NOT BETWEEN 1 AND 1048576
    OR plan_bytes IS NULL OR octet_length(plan_bytes) NOT BETWEEN 1 AND 8388608
    OR octet_length(context_bytes) + octet_length(plan_bytes) > 8388608
    OR row_budget IS NULL OR row_budget NOT BETWEEN 1 AND 65536
    OR byte_budget IS NULL OR byte_budget NOT BETWEEN 1 AND 536870912
    OR layout_bytes IS NULL OR resource_bytes IS NULL THEN
    RAISE EXCEPTION 'original bounded reservation inputs required' USING ERRCODE='22023';
  END IF;
  actual_xid := pg_current_xact_id_if_assigned();
  IF actual_xid IS NULL THEN
    RAISE EXCEPTION 'original assigned transaction required' USING ERRCODE='55000';
  END IF;
  -- The original producer must enter before every lower policy/key/owner lock.
  SELECT h.rev INTO STRICT head_revision FROM truss.schema_head h WHERE h.id=1 FOR SHARE;
  SELECT c.* INTO STRICT ledger FROM truss.row_home_capacity c WHERE c.singleton_id=1 FOR UPDATE;
  IF ledger.original_layout_bytes IS DISTINCT FROM layout_bytes
    OR ledger.original_resource_profile_bytes IS DISTINCT FROM resource_bytes
    OR ledger.reservation_writer_xid IS NOT NULL THEN
    RAISE EXCEPTION 'original available ledger/profile required' USING ERRCODE='55000';
  END IF;
  IF EXISTS (SELECT 1 FROM truss.row_home_operation o WHERE o.original_writer_xid=actual_xid
      AND (o.phase <> 'application_finalized' OR o.operation_ordinal >= issued_ordinal)) THEN
    RAISE EXCEPTION 'original issued operation frontier required' USING ERRCODE='55000';
  END IF;
  -- Subtract before adding: no overflowing trial sum or capacity eviction.
  IF row_budget > 65536-ledger.retained_rows
    OR byte_budget > 536870912-ledger.retained_custody_bytes THEN
    RAISE EXCEPTION 'original capacity unavailable' USING ERRCODE='54000';
  END IF;
  UPDATE truss.row_home_capacity SET reserved_rows=row_budget,reserved_custody_bytes=byte_budget,
    reservation_writer_xid=actual_xid,reservation_operation_ordinal=issued_ordinal,
    reservation_context_bytes=context_bytes,reservation_plan_bytes=plan_bytes,
    reservation_initial_rows=row_budget,reservation_initial_custody_bytes=byte_budget
  WHERE singleton_id=1;
END;
$$;
REVOKE ALL ON FUNCTION truss.capacity_reserve_original(bigint,bytea,bytea,bigint,bigint,bytea,bytea) FROM PUBLIC;

CREATE FUNCTION truss.capacity_transfer_original(
  context_bytes bytea, plan_bytes bytea,
  new_rows bigint, positive_growth_bytes bigint, removed_bytes bigint
) RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp AS $$
DECLARE
  actual_xid xid8;
  ledger truss.row_home_capacity%ROWTYPE;
  operation truss.row_home_operation%ROWTYPE;
BEGIN
  IF new_rows IS NULL OR new_rows < 0 OR positive_growth_bytes IS NULL OR positive_growth_bytes < 0
    OR removed_bytes IS NULL OR removed_bytes < 0
    OR positive_growth_bytes < new_rows
    OR context_bytes IS NULL OR octet_length(context_bytes) NOT BETWEEN 1 AND 1048576
    OR plan_bytes IS NULL OR octet_length(plan_bytes) NOT BETWEEN 1 AND 8388608
    OR octet_length(context_bytes)+octet_length(plan_bytes)>8388608 THEN
    RAISE EXCEPTION 'original nonnegative event deltas required' USING ERRCODE='22023';
  END IF;
  actual_xid := pg_current_xact_id_if_assigned();
  IF actual_xid IS NULL THEN RAISE EXCEPTION 'original assigned transaction required' USING ERRCODE='55000'; END IF;
  -- No FOR UPDATE: the original reserve UPDATE already owns the ledger through
  -- termination. Observers cannot acquire an earlier capacity lock here.
  SELECT c.* INTO STRICT ledger FROM truss.row_home_capacity c WHERE c.singleton_id=1;
  IF ledger.reservation_writer_xid IS DISTINCT FROM actual_xid
    OR ledger.reservation_context_bytes IS DISTINCT FROM context_bytes
    OR ledger.reservation_plan_bytes IS DISTINCT FROM plan_bytes THEN
    RAISE EXCEPTION 'original held reservation required' USING ERRCODE='55000';
  END IF;
  -- Unique unfinished scope, not latest ordinal or a caller-selected operation.
  SELECT o.* INTO STRICT operation FROM truss.row_home_operation o
  WHERE o.original_writer_xid=actual_xid AND o.phase <> 'application_finalized';
  IF operation.operation_ordinal IS DISTINCT FROM ledger.reservation_operation_ordinal
    OR operation.original_context_bytes IS DISTINCT FROM ledger.reservation_context_bytes THEN
    RAISE EXCEPTION 'original operation/reservation correspondence required' USING ERRCODE='55000';
  END IF;
  IF new_rows > ledger.reserved_rows OR positive_growth_bytes > ledger.reserved_custody_bytes
    OR removed_bytes > ledger.retained_custody_bytes THEN
    RAISE EXCEPTION 'original event capacity unavailable' USING ERRCODE='54000';
  END IF;
  -- Producer independently derives complete OLD/NEW membership and exact row/
  -- carrier/overhead deltas; arithmetic cannot authenticate these supplied deltas.
  UPDATE truss.row_home_capacity
  SET retained_rows=retained_rows+new_rows,
    retained_custody_bytes=retained_custody_bytes-removed_bytes+positive_growth_bytes,
    reserved_rows=reserved_rows-new_rows,
    reserved_custody_bytes=reserved_custody_bytes-positive_growth_bytes
  WHERE singleton_id=1;
  -- Shrink never refunds remaining capacity. Immutable initial budgets remain.
END;
$$;
REVOKE ALL ON FUNCTION truss.capacity_transfer_original(bytea,bytea,bigint,bigint,bigint) FROM PUBLIC;

CREATE FUNCTION truss.capacity_release_original(context_bytes bytea, plan_bytes bytea)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp AS $$
DECLARE
  actual_xid xid8;
  ledger truss.row_home_capacity%ROWTYPE;
  operation truss.row_home_operation%ROWTYPE;
BEGIN
  IF context_bytes IS NULL OR octet_length(context_bytes) NOT BETWEEN 1 AND 1048576
    OR plan_bytes IS NULL OR octet_length(plan_bytes) NOT BETWEEN 1 AND 8388608
    OR octet_length(context_bytes)+octet_length(plan_bytes)>8388608 THEN
    RAISE EXCEPTION 'original bounded release inputs required' USING ERRCODE='22023';
  END IF;
  actual_xid := pg_current_xact_id_if_assigned();
  IF actual_xid IS NULL THEN RAISE EXCEPTION 'original assigned transaction required' USING ERRCODE='55000'; END IF;
  SELECT c.* INTO STRICT ledger FROM truss.row_home_capacity c WHERE c.singleton_id=1;
  IF ledger.reservation_writer_xid IS DISTINCT FROM actual_xid
    OR ledger.reservation_context_bytes IS DISTINCT FROM context_bytes
    OR ledger.reservation_plan_bytes IS DISTINCT FROM plan_bytes THEN
    RAISE EXCEPTION 'original held reservation required' USING ERRCODE='55000';
  END IF;
  SELECT o.* INTO STRICT operation FROM truss.row_home_operation o
  WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=ledger.reservation_operation_ordinal;
  IF operation.phase <> 'application_finalized'
    OR operation.original_context_bytes IS DISTINCT FROM ledger.reservation_context_bytes THEN
    RAISE EXCEPTION 'original finalized operation required' USING ERRCODE='55000';
  END IF;
  -- Full protected finalizer establishes complete original guards/results; phase
  -- CHECKs alone do not confer it. Release only remaining, never initial totals.
  UPDATE truss.row_home_capacity SET reserved_rows=0,reserved_custody_bytes=0,
    reservation_writer_xid=NULL,reservation_operation_ordinal=NULL,
    reservation_context_bytes=NULL,reservation_plan_bytes=NULL,
    reservation_initial_rows=NULL,reservation_initial_custody_bytes=NULL
  WHERE singleton_id=1;
END;
$$;
REVOKE ALL ON FUNCTION truss.capacity_release_original(bytea,bytea) FROM PUBLIC;
