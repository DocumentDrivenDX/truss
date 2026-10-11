-- Private stronger epoch-state acquisition, not complete installed-source custody.
-- NOWAIT refuses pending epoch writers; no internal retry or substituted epoch.
CREATE FUNCTION truss.runtime_lock_fenced_fresh_source_epoch(
 expected_installation text, expected_epoch text, expected_incarnation text)
RETURNS TABLE(installation_id text,source_epoch text,target_incarnation text,
 profile_hex text,evidence_hex text,evidence_sha256 text,
 actual_writer_xid text,actual_database_oid text,actual_backend_pid text,
 original_actor text,effective_actor text,cut_scope text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
  THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker fenced epoch boundary required' USING ERRCODE='55000';
 END IF;
 IF current_setting('transaction_isolation') IS DISTINCT FROM 'read committed'
  OR current_setting('transaction_read_only') IS DISTINCT FROM 'off' THEN
  RAISE EXCEPTION 'fenced epoch requires native read committed read write' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.source_epoch_current, truss.source_epoch_registry IN SHARE MODE NOWAIT;
 RETURN QUERY SELECT e.installation_id,e.source_epoch,e.target_incarnation,
  e.profile_hex,e.evidence_hex,e.evidence_sha256,
  e.actual_writer_xid,e.actual_database_oid,e.actual_backend_pid,
  e.original_actor,e.effective_actor,'transaction_epoch_state_fence_only'::text
 FROM truss.runtime_lock_fresh_source_epoch(expected_installation,expected_epoch,expected_incarnation) e;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_lock_fenced_fresh_source_epoch(text,text,text) FROM PUBLIC;
