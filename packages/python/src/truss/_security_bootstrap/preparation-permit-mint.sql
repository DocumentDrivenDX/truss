-- Internal binding primitive only. Do not grant to a login/coordinator.
-- Original native guarded issuer must establish current authority first.
CREATE FUNCTION truss.mint_preparation_permit_binding(
 original_anchor pg_catalog.int4, original_data_pid pg_catalog.int4,
 original_data_xid pg_catalog.xid8)
RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
 full_xid pg_catalog.numeric;
 low_piece pg_catalog.numeric;
 high_piece pg_catalog.numeric;
BEGIN
 IF pg_catalog.current_setting('server_version_num') IS DISTINCT FROM '180006'
  OR pg_catalog.current_setting('transaction_isolation') IS DISTINCT FROM 'read committed'
  OR pg_catalog.current_setting('transaction_read_only') IS DISTINCT FROM 'off'
  OR pg_catalog.current_setting('role') IS DISTINCT FROM 'none'
  OR original_anchor IS NULL OR original_anchor<=0
  OR original_data_pid IS NULL OR original_data_pid<=0
  OR original_data_xid IS NULL THEN
  RAISE EXCEPTION 'original native permit binding context required' USING ERRCODE='0A000';
 END IF;
 -- A single native backend owns one complete live tuple. The slot is
 -- backend-specific; it does not serialize unrelated coordinators.
 IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l
  WHERE l.locktype='advisory' AND l.pid=pg_catalog.pg_backend_pid()
   AND l.database=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
   AND l.classid=2147400100::pg_catalog.oid
   AND l.objid=pg_catalog.pg_backend_pid()::pg_catalog.oid AND l.objsubid=2 AND l.granted) THEN
  RAISE EXCEPTION 'original coordinator already owns a permit binding' USING ERRCODE='55000';
 END IF;
 full_xid := original_data_xid::pg_catalog.text::pg_catalog.numeric;
 IF full_xid=0 THEN
  RAISE EXCEPTION 'original assigned full xid8 required' USING ERRCODE='22023';
 END IF;
 low_piece := pg_catalog.mod(full_xid,4294967296);
 -- NUMERIC / may round before truncation near 2^64. div is the exact
 -- integral quotient; native maximum-xid controls cover this distinction.
 high_piece := pg_catalog.div(full_xid,4294967296);
 IF low_piece>=2147483648 THEN low_piece:=low_piece-4294967296; END IF;
 IF high_piece>=2147483648 THEN high_piece:=high_piece-4294967296; END IF;
 IF NOT pg_catalog.pg_try_advisory_xact_lock(2147400100,pg_catalog.pg_backend_pid())
  OR NOT pg_catalog.pg_try_advisory_xact_lock_shared(2147400101,original_anchor)
  OR NOT pg_catalog.pg_try_advisory_xact_lock_shared(2147400102,original_data_pid)
  OR NOT pg_catalog.pg_try_advisory_xact_lock_shared(2147400103,low_piece::pg_catalog.int4)
  OR NOT pg_catalog.pg_try_advisory_xact_lock_shared(2147400104,high_piece::pg_catalog.int4) THEN
  RAISE EXCEPTION 'original native permit binding unavailable' USING ERRCODE='55P03';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.mint_preparation_permit_binding(
 pg_catalog.int4,pg_catalog.int4,pg_catalog.xid8) FROM PUBLIC;
