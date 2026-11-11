-- Fixed native spike for one declared subject home. Not a complete installer,
-- arbitrary-home API, authenticated issuer or protected query/release profile.
-- Installer independently qualifies owner, ACL, language and read dependencies.
CREATE FUNCTION truss.spike_acquire_ordinary_subject_cut(
 expected_installation text,expected_epoch text,expected_incarnation text)
RETURNS TABLE(installation_id text,source_epoch text,target_incarnation text,
 profile_hex text,evidence_hex text,evidence_sha256 text,
 actual_xid text,actual_database_oid text,actual_backend_pid text,
 original_actor text,privileged_actor text,staff_id text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE pointer truss.source_epoch_current%ROWTYPE;
 epoch truss.source_epoch_registry%ROWTYPE;
 subject text;
BEGIN
 IF current_setting('role') NOT IN ('none',session_user::text)
  OR current_setting('transaction_isolation') IS DISTINCT FROM 'read committed'
  OR current_setting('transaction_read_only') IS DISTINCT FROM 'off' THEN
  RAISE EXCEPTION 'original ordinary subject cut profile required' USING ERRCODE='55000';
 END IF;
 IF expected_installation IS NULL OR expected_epoch IS NULL OR expected_incarnation IS NULL
  OR octet_length(expected_installation) NOT BETWEEN 1 AND 1024
  OR octet_length(expected_epoch) NOT BETWEEN 1 AND 256
  OR octet_length(expected_incarnation) NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'bounded original subject cut comparison required' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.source_epoch_current,truss.source_epoch_registry,truss.spike_subject_fact IN SHARE MODE NOWAIT;
 SELECT c.* INTO STRICT pointer FROM truss.source_epoch_current c WHERE c.singleton_id=1;
 SELECT r.* INTO STRICT epoch FROM truss.source_epoch_registry r
  WHERE r.installation_id=pointer.installation_id AND r.source_epoch=pointer.source_epoch;
 IF pointer.installation_id IS DISTINCT FROM expected_installation
  OR pointer.source_epoch IS DISTINCT FROM expected_epoch
  OR epoch.target_incarnation IS DISTINCT FROM expected_incarnation
  OR epoch.evidence_sha256 IS DISTINCT FROM sha256(epoch.evidence_bytes) THEN
  RAISE EXCEPTION 'original subject cut correspondence required' USING ERRCODE='55000';
 END IF;
 SELECT s.staff_id INTO STRICT subject FROM truss.spike_subject_fact s WHERE s.actor=session_user::text;
 RETURN QUERY SELECT epoch.installation_id,epoch.source_epoch,epoch.target_incarnation,
  encode(epoch.profile_bytes,'hex'),encode(epoch.evidence_bytes,'hex'),encode(epoch.evidence_sha256,'hex'),
  pg_current_xact_id()::text,
  (SELECT d.oid::text FROM pg_database d WHERE d.datname=current_database()),
  pg_backend_pid()::text,session_user::text,current_user::text,subject;
END;
$$;
REVOKE ALL ON FUNCTION truss.spike_acquire_ordinary_subject_cut(text,text,text) FROM PUBLIC;
