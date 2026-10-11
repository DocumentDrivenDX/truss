-- Private native READ COMMITTED epoch-lock projection. This is not complete
-- source/authority admission, an installed producer grant or a release receipt.
-- The host must bind original transaction/savepoint custody and exclude same-
-- transaction issuer changes. Autocommit or rollback past acquisition releases
-- the lock; matching xid/PID after return does not establish continued ownership.
CREATE FUNCTION truss.runtime_lock_fresh_source_epoch(
 expected_installation text, expected_epoch text, expected_incarnation text)
RETURNS TABLE(installation_id text,source_epoch text,target_incarnation text,
 profile_hex text,evidence_hex text,evidence_sha256 text,
 actual_writer_xid text,actual_database_oid text,actual_backend_pid text,
 original_actor text,effective_actor text,cut_scope text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE epoch record;
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
  THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker fresh epoch boundary required' USING ERRCODE='55000';
 END IF;
 -- Caller claims and an empty host ledger cannot refresh an inherited snapshot.
 -- Stronger isolation profiles need independent snapshot provenance before use.
 IF current_setting('transaction_isolation') IS DISTINCT FROM 'read committed'
  OR current_setting('transaction_read_only') IS DISTINCT FROM 'off' THEN
  RAISE EXCEPTION 'fresh epoch requires native read committed read write' USING ERRCODE='55000';
 END IF;
 SELECT * INTO STRICT epoch FROM truss.runtime_lock_source_epoch(
  expected_installation,expected_epoch,expected_incarnation);
 RETURN QUERY SELECT epoch.installation_id,epoch.source_epoch,epoch.target_incarnation,
  epoch.profile_hex,epoch.evidence_hex,epoch.evidence_sha256,
  pg_current_xact_id()::text,
  (SELECT d.oid::text FROM pg_database d WHERE d.datname=current_database()),
  pg_backend_pid()::text,session_user::text,current_user::text,
  'transaction_source_epoch_lock_only'::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_lock_fresh_source_epoch(text,text,text) FROM PUBLIC;
