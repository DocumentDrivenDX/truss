-- Private explicit shared-authority writer participation, PostgreSQL16.15.
-- Caller must invoke before its selected role/ACL mutation in the same transaction.
-- Not automatic role-DDL interception, epoch transition or full source admission.
-- Original installer/administrative exclusions and helper custody are prerequisites.
CREATE FUNCTION truss.runtime_fence_shared_authority_writer()
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
  THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker shared authority change boundary required' USING ERRCODE='55000';
 END IF;
 -- Retained native admissions outlive individual calls in this transaction.
 -- Refuse before writer modes/marker locking and before any selected DDL effect.
 IF EXISTS(SELECT 1 FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()) THEN
  RAISE EXCEPTION 'shared authority change cannot follow an original operation' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l
  WHERE l.locktype='relation' AND l.pid=pg_catalog.pg_backend_pid()
   AND l.database=(SELECT d.oid FROM pg_catalog.pg_database d WHERE d.datname=pg_catalog.current_database())
   AND l.relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)
   AND l.mode='ShareLock' AND l.granted) THEN
  RAISE EXCEPTION 'selected epoch cut excludes shared authority change' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.source_epoch_current, truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT;
 -- Table modes precede marker row: pending writers exclude the fenced reader
 -- through actual COMMIT/ABORT; marker serializes participating writers.
 PERFORM 1 FROM truss.installation_marker m WHERE m.singleton_id=1 FOR UPDATE NOWAIT;
 IF NOT FOUND THEN
  RAISE EXCEPTION 'original installation marker required for shared authority change' USING ERRCODE='55000';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_fence_shared_authority_writer() FROM PUBLIC;
