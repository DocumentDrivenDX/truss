-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Owner-private physical binding check, NOT an authorization gate.
-- Anchor/store/source/coordinator incarnation must be derived by a separately
-- qualified native guard. No login/coordinator receives direct execution.
CREATE FUNCTION truss.check_preparation_permit_binding(
 original_anchor pg_catalog.int4, original_coordinator_pid pg_catalog.int4)
RETURNS pg_catalog.bool
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE full_xid pg_catalog.numeric;
BEGIN
 IF pg_catalog.current_setting('server_version_num') IS DISTINCT FROM '180006'
  OR pg_catalog.current_setting('transaction_isolation') IS DISTINCT FROM 'repeatable read'
  OR pg_catalog.current_setting('transaction_read_only') IS DISTINCT FROM 'off'
  OR pg_catalog.current_setting('role') IS DISTINCT FROM 'none'
  OR original_anchor IS NULL OR original_anchor<=0
  OR original_coordinator_pid IS NULL OR original_coordinator_pid<=0 THEN
  RAISE EXCEPTION 'original native data binding context required' USING ERRCODE='0A000';
 END IF;
 full_xid:=pg_catalog.pg_current_xact_id()::pg_catalog.text::pg_catalog.numeric;
 PERFORM pg_catalog.pg_stat_clear_snapshot();
 RETURN (WITH expected(classid,objid,mode) AS (VALUES
   (2147400100::pg_catalog.oid,original_coordinator_pid::pg_catalog.oid,'ExclusiveLock'::pg_catalog.text),
   (2147400101::pg_catalog.oid,original_anchor::pg_catalog.oid,'ShareLock'::pg_catalog.text),
   (2147400102::pg_catalog.oid,pg_catalog.pg_backend_pid()::pg_catalog.oid,'ShareLock'::pg_catalog.text),
   (2147400103::pg_catalog.oid,pg_catalog.mod(full_xid,4294967296)::pg_catalog.int8::pg_catalog.oid,'ShareLock'::pg_catalog.text),
   (2147400104::pg_catalog.oid,pg_catalog.div(full_xid,4294967296)::pg_catalog.int8::pg_catalog.oid,'ShareLock'::pg_catalog.text)),
  held AS MATERIALIZED (SELECT l.classid,l.objid,l.mode FROM pg_catalog.pg_locks l
   WHERE l.pid=original_coordinator_pid AND l.locktype='advisory' AND l.objsubid=2 AND l.granted
   AND l.database=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()))
  SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_stat_activity a
    WHERE a.pid=original_coordinator_pid
     AND a.datid=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
     AND a.state IN ('active','idle in transaction') AND a.xact_start IS NOT NULL)
   AND NOT EXISTS(SELECT 1 FROM expected e WHERE NOT EXISTS(
    SELECT 1 FROM held h WHERE h.classid=e.classid AND h.objid=e.objid AND h.mode=e.mode)));
END;
$$;
REVOKE ALL ON FUNCTION truss.check_preparation_permit_binding(
 pg_catalog.int4,pg_catalog.int4) FROM PUBLIC;
