-- Private native issuance component. Only the installed lifecycle producer may
-- receive a grant after authority/profile/target evidence qualification.
-- Inputs are comparison/evidence carriers, never caller authorization.
CREATE FUNCTION truss.runtime_issue_source_epoch(
 expected_installation text, expected_predecessor text, admitted_incarnation text,
 admitted_profile bytea, original_evidence bytea)
RETURNS text LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE current_epoch text; issued text;
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
  THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker lifecycle boundary required' USING ERRCODE='55000';
 END IF;
 IF expected_installation IS NULL OR octet_length(expected_installation) NOT BETWEEN 1 AND 1024
  OR admitted_incarnation IS NULL OR octet_length(admitted_incarnation) NOT BETWEEN 1 AND 1024
  OR admitted_profile IS NULL OR octet_length(admitted_profile) NOT BETWEEN 1 AND 65536
  OR original_evidence IS NULL OR octet_length(original_evidence) NOT BETWEEN 1 AND 1048576
  OR (expected_predecessor IS NOT NULL AND octet_length(expected_predecessor) NOT BETWEEN 1 AND 256) THEN
  RAISE EXCEPTION 'bounded original lifecycle inputs required' USING ERRCODE='55000';
 END IF;
 -- Retained operation rows cover completed calls as well as unfinished ones:
 -- their enclosing transaction must not change source incarnation afterwards.
 IF EXISTS(SELECT 1 FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()) THEN
  RAISE EXCEPTION 'source epoch cannot transition behind an original writer' USING ERRCODE='55000';
 END IF;
 -- Marker serializes the empty-pointer initial case as well as transitions.
 PERFORM 1 FROM truss.installation_marker m WHERE m.installation_id=expected_installation FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'original installation marker required' USING ERRCODE='55000'; END IF;
 SELECT c.source_epoch INTO current_epoch FROM truss.source_epoch_current c WHERE c.singleton_id=1 FOR UPDATE;
 IF FOUND THEN
  IF expected_predecessor IS NULL OR current_epoch IS DISTINCT FROM expected_predecessor
   OR NOT EXISTS(SELECT 1 FROM truss.source_epoch_current c WHERE c.singleton_id=1 AND c.installation_id=expected_installation) THEN
   RAISE EXCEPTION 'original predecessor correspondence required' USING ERRCODE='55000';
  END IF;
 ELSE
  IF expected_predecessor IS NOT NULL OR EXISTS(SELECT 1 FROM truss.source_epoch_registry r WHERE r.installation_id=expected_installation) THEN
   RAISE EXCEPTION 'fresh original initial epoch required' USING ERRCODE='55000';
  END IF;
 END IF;
 -- Native version-4 UUID; collision fails unique constraint, no silent reuse.
 issued:=pg_catalog.gen_random_uuid()::text;
 INSERT INTO truss.source_epoch_registry(installation_id,source_epoch,target_incarnation,predecessor_epoch,transition_reason,profile_bytes,evidence_bytes)
 VALUES(expected_installation,issued,admitted_incarnation,expected_predecessor,
  CASE WHEN expected_predecessor IS NULL THEN 'initial' ELSE 'restore' END,admitted_profile,original_evidence);
 IF current_epoch IS NULL THEN
  INSERT INTO truss.source_epoch_current VALUES(1,expected_installation,issued);
 ELSE
  UPDATE truss.source_epoch_current SET source_epoch=issued WHERE singleton_id=1;
 END IF;
 RETURN issued;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_issue_source_epoch(text,text,text,bytea,bytea) FROM PUBLIC;
