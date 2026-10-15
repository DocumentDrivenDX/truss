-- Private selected-literal native composition component. No production grant,
-- protected selector/finalizer or complete source/legacy-writer qualification.
-- Trusted excluded installer/owners and original helper custody are premises.
CREATE FUNCTION truss.require_preparation_literal_data_cut(original_data_pid pg_catalog.int4)
RETURNS pg_catalog.void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE relation_name pg_catalog.text; required_mode pg_catalog.text;
BEGIN
 FOR relation_name,required_mode IN SELECT * FROM (VALUES
  ('truss.source_epoch_current','ShareLock'),('truss.source_epoch_registry','ShareLock'),
  ('truss.catalog_runtime_installation','ShareLock'),('truss.runtime_release','ShareLock'),
  ('truss.schema_head','ShareLock'),('truss.schema_rev','ShareLock'),('truss.schema_doc','ShareLock'),
  ('truss.schema_change','ShareLock'),('truss.type_def','ShareLock'),('truss.prop_def','ShareLock'),
  ('truss.key_def','ShareLock'),('truss.rel_def','ShareLock'),('truss.rel_endpoint','ShareLock'),
  ('truss.catalog_registration_request','ShareLock'),('truss.catalog_acceptance_report','ShareLock'),
  ('truss.relationship_lineage','ShareLock'),('truss.runtime_catalog_rebind_transition','ShareLock'),
  ('truss.runtime_catalog_key_backfill','ShareLock'),('truss.installation_archive','ShareLock'),
  ('truss.action_store_registration','ShareLock'),('truss.action_store_registration','RowExclusiveLock'),
  ('truss.preparation_program_registration','ShareLock'),('truss.preparation_program_sources','ShareLock'),
  ('truss.preparation_attempt_anchor','RowExclusiveLock'),('umf_security.preparation_data_claim','RowExclusiveLock'),
  ('truss.action_family_registration','ShareLock'),('truss.action_subject_binding','ShareLock'),
  ('truss.action_role_binding','ShareLock'),('truss.module_access','ShareLock'),
  ('pg_catalog.pg_authid','ShareLock'),('pg_catalog.pg_auth_members','ShareLock')) AS required(name,mode)
 LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_catalog.pg_locks l JOIN pg_catalog.pg_class c ON c.oid=l.relation
   WHERE l.locktype='relation' AND l.pid=original_data_pid AND l.granted AND l.mode=required_mode
    AND l.relation=to_regclass(relation_name)
    AND l.database=CASE WHEN c.relisshared THEN '0'::oid
      ELSE (SELECT oid FROM pg_catalog.pg_database WHERE datname=current_database()) END) THEN
   RAISE EXCEPTION 'original live D source/mapping/authority exclusions required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.require_preparation_literal_data_cut(int4) FROM PUBLIC;

CREATE FUNCTION truss.acquire_preparation_literal_permit_cut(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
BEGIN
 -- Source/head/mapping first. No authority evaluation through the RR snapshot.
 PERFORM truss.acquire_preparation_bridge_cut(original_anchor,original_nonce);
 LOCK TABLE ONLY truss.module_access IN SHARE MODE NOWAIT;
 LOCK TABLE pg_catalog.pg_authid,pg_catalog.pg_auth_members IN SHARE MODE NOWAIT;
 PERFORM truss.require_preparation_literal_data_cut(pg_backend_pid());
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_preparation_literal_permit_cut(int4,uuid) FROM PUBLIC;

CREATE FUNCTION truss.issue_preparation_literal_permit(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE claim record; after_claim record; original_observation pg_catalog.jsonb;
BEGIN
 IF truss.check_preparation_attempt_coordinator(original_anchor,original_nonce) IS NOT TRUE THEN
  RAISE EXCEPTION 'original coordinator transaction required' USING ERRCODE='55000';END IF;
 -- This function invokes actual native checks; no copied success value is input.
 original_observation:=truss.observe_preparation_bridge(original_anchor,original_nonce);
 SELECT * INTO STRICT claim FROM umf_security.require_preparation_data_claim(original_anchor,original_nonce);
 PERFORM truss.require_preparation_literal_data_cut(claim.data_pid);
 PERFORM truss.check_preparation_literal_authority(original_anchor,original_nonce);
 PERFORM truss.mint_preparation_permit_binding(original_anchor,claim.data_pid,claim.data_xid);
 SELECT * INTO STRICT after_claim FROM umf_security.require_preparation_data_claim(original_anchor,original_nonce);
 IF after_claim IS DISTINCT FROM claim OR truss.check_preparation_attempt_coordinator(original_anchor,original_nonce) IS NOT TRUE
  OR truss.observe_preparation_bridge(original_anchor,original_nonce) IS DISTINCT FROM original_observation THEN
  RAISE EXCEPTION 'original claim/coordinator/source changed during mint' USING ERRCODE='55000';END IF;
 PERFORM truss.require_preparation_literal_data_cut(claim.data_pid);
END;
$$;
REVOKE ALL ON FUNCTION truss.issue_preparation_literal_permit(int4,uuid) FROM PUBLIC;

CREATE FUNCTION truss.require_preparation_literal_permit(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE anchor truss.preparation_attempt_anchor%ROWTYPE; program_id pg_catalog.int8;
 coordinator pg_catalog.pg_stat_activity%ROWTYPE; pass pg_catalog.int4;
BEGIN
 -- Verify-only census before helpers that could otherwise reacquire lost cuts.
 PERFORM truss.require_preparation_literal_data_cut(pg_backend_pid());
 SELECT * INTO STRICT anchor FROM ONLY truss.preparation_attempt_anchor
  WHERE anchor_id=original_anchor AND anchor_nonce=original_nonce;
 -- Trusted engine sequencing waits for C's successful issuer completion and
 -- leaves C idle until original D settlement. An active mint is insufficient.
 FOR pass IN 1..2 LOOP
  PERFORM pg_stat_clear_snapshot();
  SELECT * INTO coordinator FROM pg_catalog.pg_stat_activity WHERE pid=anchor.coordinator_pid;
  IF NOT FOUND OR coordinator.state IS DISTINCT FROM 'idle in transaction'
   OR coordinator.datid IS DISTINCT FROM anchor.database_oid
   OR coordinator.usesysid IS DISTINCT FROM anchor.coordinator_role_oid
   OR coordinator.backend_start IS DISTINCT FROM anchor.coordinator_backend_started_at
   OR coordinator.xact_start IS DISTINCT FROM anchor.coordinator_xact_started_at
   OR pg_xact_status(anchor.coordinator_xid) IS DISTINCT FROM 'in progress'
   OR coordinator.backend_xid::text::numeric IS DISTINCT FROM mod(anchor.coordinator_xid::text::numeric,4294967296) THEN
   RAISE EXCEPTION 'original idle coordinator issuer completion required' USING ERRCODE='55000';END IF;
  PERFORM truss.require_preparation_literal_data_cut(pg_backend_pid());
  IF pass=1 THEN
   -- D must not read the later independently committed E claim through old RR.
   -- Original C's guarded mint binds that claim to D's actual full xid8.
   IF truss.check_preparation_attempt_data(original_anchor,original_nonce) IS NOT TRUE THEN
    RAISE EXCEPTION 'original live data/coordinator incarnations required' USING ERRCODE='55000';END IF;
   program_id:=truss.resolve_preparation_program_binding(original_anchor,original_nonce,pg_current_xact_id());
   PERFORM truss.read_preparation_program_sources(program_id);
  END IF;
  IF truss.check_preparation_permit_binding(original_anchor,anchor.coordinator_pid) IS NOT TRUE THEN
   RAISE EXCEPTION 'original guarded coordinator permit required' USING ERRCODE='55000';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.require_preparation_literal_permit(int4,uuid) FROM PUBLIC;
