-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Owner-private epoch reconciliation only, not peer/incarnation authorization.
CREATE FUNCTION truss.require_preparation_peer_xid(
 original_pid pg_catalog.int4, claimed_xid pg_catalog.xid8)
RETURNS pg_catalog.xid8
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
 peer_status pg_catalog.text;
 full_xid pg_catalog.numeric;
 peer_xid pg_catalog.numeric;
BEGIN
 IF pg_catalog.current_setting('server_version_num') IS DISTINCT FROM '180006'
  OR pg_catalog.current_setting('transaction_isolation') IS DISTINCT FROM 'read committed'
  OR pg_catalog.current_setting('transaction_read_only') IS DISTINCT FROM 'off'
  OR pg_catalog.current_setting('role') IS DISTINCT FROM 'none'
  OR original_pid IS NULL OR original_pid<=0 OR claimed_xid IS NULL THEN
  RAISE EXCEPTION 'original native peer xid context required' USING ERRCODE='0A000';
 END IF;
 full_xid:=claimed_xid::pg_catalog.text::pg_catalog.numeric;
 -- Native xid8 range validation uses ReadNextFullTransactionId and the
 -- retained clog horizon; snapshot xmax is not the allocator upper bound.
 BEGIN
  peer_status:=pg_catalog.pg_xact_status(claimed_xid);
 EXCEPTION WHEN invalid_parameter_value THEN
  RAISE EXCEPTION 'original recent native peer xid required' USING ERRCODE='55000';
 END;
 IF peer_status IS DISTINCT FROM 'in progress' THEN
  RAISE EXCEPTION 'original active full native peer xid required' USING ERRCODE='55000';
 END IF;
 PERFORM pg_catalog.pg_stat_clear_snapshot();
 SELECT a.backend_xid::pg_catalog.text::pg_catalog.numeric INTO peer_xid
  FROM pg_catalog.pg_stat_activity a
  WHERE a.pid=original_pid
   AND a.datid=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
   AND a.state IN ('active','idle in transaction') AND a.xact_start IS NOT NULL;
 IF peer_xid IS NULL OR peer_xid IS DISTINCT FROM pg_catalog.mod(full_xid,4294967296) THEN
  RAISE EXCEPTION 'original active native peer xid required' USING ERRCODE='55000';
 END IF;
 RETURN claimed_xid;
END;
$$;
REVOKE ALL ON FUNCTION truss.require_preparation_peer_xid(
 pg_catalog.int4,pg_catalog.xid8) FROM PUBLIC;
