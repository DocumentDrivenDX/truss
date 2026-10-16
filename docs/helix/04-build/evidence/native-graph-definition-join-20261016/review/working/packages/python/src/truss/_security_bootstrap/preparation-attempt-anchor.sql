-- Private native attempt identity only. No program, authorization or permit
-- admission. All routines remain owner-private; no production installer exists.
CREATE FUNCTION truss.create_preparation_attempt_anchor(
 original_store_key pg_catalog.bytea, original_data_pid pg_catalog.int4,
 original_coordinator_pid pg_catalog.int4, original_coordinator_xid pg_catalog.xid8,
 original_program_identity pg_catalog.bytea)
RETURNS TABLE(anchor_id pg_catalog.int4,anchor_nonce pg_catalog.uuid)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE r truss.preparation_attempt_anchor%ROWTYPE;
 store truss.action_store_registration%ROWTYPE;
 d pg_catalog.pg_stat_activity%ROWTYPE; a pg_catalog.pg_stat_activity%ROWTYPE;
 observation pg_catalog.jsonb;
BEGIN
 IF current_setting('server_version_num')<>'180006'
  OR current_setting('transaction_isolation')<>'read committed'
  OR current_setting('transaction_read_only')<>'off' OR current_setting('role')<>'none'
  OR NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=session_user AND rolsuper)
  OR original_data_pid IS NULL OR original_coordinator_pid IS NULL
  OR original_data_pid=original_coordinator_pid OR pg_backend_pid() IN (original_data_pid,original_coordinator_pid)
  OR original_program_identity IS NULL OR octet_length(original_program_identity) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'original private control anchor context required' USING ERRCODE='55000';
 END IF;
 observation:=convert_from(truss.observe_action_store_original(original_store_key),'UTF8')::jsonb;
 IF observation->>'bindingCorrespondence' IS DISTINCT FROM 'matches' THEN
  RAISE EXCEPTION 'original unfenced committed store required' USING ERRCODE='55000';END IF;
 SELECT s.* INTO STRICT store FROM ONLY truss.action_store_registration s WHERE s.singleton AND s.registration_key=original_store_key;
 IF observation->>'receiptHex' IS DISTINCT FROM encode(store.initial_receipt_bytes,'hex') THEN
  RAISE EXCEPTION 'original store receipt required' USING ERRCODE='55000';END IF;
 PERFORM truss.require_preparation_peer_xid(original_coordinator_pid,original_coordinator_xid);
 PERFORM pg_stat_clear_snapshot();
 SELECT * INTO STRICT d FROM pg_catalog.pg_stat_activity WHERE pid=original_data_pid;
 SELECT * INTO STRICT a FROM pg_catalog.pg_stat_activity WHERE pid=original_coordinator_pid;
 IF d.datid IS DISTINCT FROM store.database_oid OR a.datid IS DISTINCT FROM store.database_oid
  OR d.usesysid IS DISTINCT FROM a.usesysid OR NOT d.usesysid=ANY(store.executor_oids)
  OR d.state IS DISTINCT FROM 'idle' OR d.xact_start IS NOT NULL OR d.backend_xid IS NOT NULL
  OR a.state NOT IN ('active','idle in transaction') OR a.xact_start IS NULL
  OR a.backend_xid::text::numeric IS DISTINCT FROM mod(original_coordinator_xid::text::numeric,4294967296)
  OR d.backend_type IS DISTINCT FROM 'client backend' OR a.backend_type IS DISTINCT FROM 'client backend'
  OR NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles p WHERE p.oid=d.usesysid AND p.rolcanlogin
    AND NOT p.rolsuper AND NOT p.rolcreaterole AND NOT p.rolcreatedb AND NOT p.rolreplication AND NOT p.rolbypassrls
    AND NOT pg_has_role(p.oid,(SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton),'MEMBER')) THEN
  RAISE EXCEPTION 'original idle data and active ordinary coordinator incarnations required' USING ERRCODE='55000';END IF;
 r.anchor_id:=nextval('truss.preparation_attempt_anchor_seq'::regclass);
 r.anchor_nonce:=gen_random_uuid();r.store_control_id:=store.control_id;r.store_receipt_bytes:=store.initial_receipt_bytes;
 r.program_identity:=original_program_identity;r.database_oid:=store.database_oid;r.postmaster_started_at:=pg_postmaster_start_time();
 r.data_pid:=d.pid;r.data_role_oid:=d.usesysid;r.data_backend_started_at:=d.backend_start;
 r.coordinator_pid:=a.pid;r.coordinator_role_oid:=a.usesysid;r.coordinator_backend_started_at:=a.backend_start;
 r.coordinator_xact_started_at:=a.xact_start;r.coordinator_xid:=original_coordinator_xid;
 r.issuer_pid:=pg_backend_pid();r.issuer_xid:=pg_current_xact_id();r.issued_at:=clock_timestamp();
 r.profile_id:='truss.preparation-attempt-anchor/0.1';
 INSERT INTO truss.preparation_attempt_anchor SELECT r.*;
 RETURN QUERY SELECT r.anchor_id,r.anchor_nonce;
END;
$$;
REVOKE ALL ON FUNCTION truss.create_preparation_attempt_anchor(bytea,int4,int4,xid8,bytea) FROM PUBLIC;

CREATE FUNCTION truss.check_preparation_attempt_coordinator(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE r truss.preparation_attempt_anchor%ROWTYPE; actual pg_catalog.pg_stat_activity%ROWTYPE;
BEGIN
 IF current_setting('server_version_num')<>'180006' OR current_setting('transaction_isolation')<>'read committed'
  OR current_setting('transaction_read_only')<>'off' OR current_setting('role')<>'none' THEN
  RAISE EXCEPTION 'original coordinator context required' USING ERRCODE='55000';END IF;
 SELECT * INTO r FROM ONLY truss.preparation_attempt_anchor WHERE anchor_id=original_anchor AND anchor_nonce=original_nonce;
 IF NOT FOUND OR r.coordinator_pid IS DISTINCT FROM pg_backend_pid()
  OR r.coordinator_xid IS DISTINCT FROM pg_current_xact_id()
  OR r.postmaster_started_at IS DISTINCT FROM pg_postmaster_start_time()
  OR pg_xact_status(r.issuer_xid) IS DISTINCT FROM 'committed' THEN RETURN false;END IF;
 PERFORM pg_stat_clear_snapshot();
 SELECT * INTO STRICT actual FROM pg_catalog.pg_stat_activity WHERE pid=pg_backend_pid();
 RETURN actual.datid=r.database_oid AND actual.usesysid=r.coordinator_role_oid
  AND actual.backend_start=r.coordinator_backend_started_at AND actual.xact_start=r.coordinator_xact_started_at;
END;
$$;
REVOKE ALL ON FUNCTION truss.check_preparation_attempt_coordinator(int4,uuid) FROM PUBLIC;

CREATE FUNCTION truss.check_preparation_attempt_data(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE r truss.preparation_attempt_anchor%ROWTYPE; d pg_catalog.pg_stat_activity%ROWTYPE; a pg_catalog.pg_stat_activity%ROWTYPE;
BEGIN
 IF current_setting('server_version_num')<>'180006' OR current_setting('transaction_isolation')<>'repeatable read'
  OR current_setting('transaction_read_only')<>'off' OR current_setting('role')<>'none' THEN
  RAISE EXCEPTION 'original data anchor context required' USING ERRCODE='55000';END IF;
 PERFORM truss.acquire_action_store_source_cut();
 SELECT * INTO r FROM ONLY truss.preparation_attempt_anchor WHERE anchor_id=original_anchor AND anchor_nonce=original_nonce;
 IF NOT FOUND OR r.data_pid IS DISTINCT FROM pg_backend_pid()
  OR r.postmaster_started_at IS DISTINCT FROM pg_postmaster_start_time()
  OR pg_xact_status(r.issuer_xid) IS DISTINCT FROM 'committed'
  OR pg_xact_status(r.coordinator_xid) IS DISTINCT FROM 'in progress'
  OR NOT EXISTS(SELECT 1 FROM ONLY truss.action_store_registration s WHERE s.control_id=r.store_control_id
    AND s.initial_receipt_bytes=r.store_receipt_bytes AND s.database_oid=r.database_oid
    AND s.postmaster_started_at=r.postmaster_started_at) THEN RETURN false;END IF;
 PERFORM pg_stat_clear_snapshot();
 SELECT * INTO STRICT d FROM pg_catalog.pg_stat_activity WHERE pid=pg_backend_pid();
 SELECT * INTO a FROM pg_catalog.pg_stat_activity WHERE pid=r.coordinator_pid;
 RETURN coalesce(d.datid=r.database_oid AND d.usesysid=r.data_role_oid AND d.backend_start=r.data_backend_started_at
  AND a.datid=r.database_oid AND a.usesysid=r.coordinator_role_oid
  AND a.backend_start=r.coordinator_backend_started_at AND a.xact_start=r.coordinator_xact_started_at
  AND a.state IN ('active','idle in transaction')
  AND a.backend_xid::text::numeric=mod(r.coordinator_xid::text::numeric,4294967296),false);
END;
$$;
REVOKE ALL ON FUNCTION truss.check_preparation_attempt_data(int4,uuid) FROM PUBLIC;
