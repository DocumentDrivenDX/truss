-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Private shared namespace issuance. Comparison outputs are never authority.
CREATE FUNCTION truss.action_store_original_receipt(r truss.action_store_registration)
RETURNS bytea LANGUAGE sql STABLE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET DateStyle='ISO, YMD' AS $$
 SELECT pg_catalog.convert_to(pg_catalog.jsonb_build_object(
  'interfaceVersion','truss.action-store-issuance/0.1',
  'controlId',r.control_id::text,'logicalStoreId',r.logical_store_id::text,
  'storeIdentityHex',pg_catalog.encode(r.store_identity,'hex'),
  'tenantIdentityHex',pg_catalog.encode(r.tenant_identity,'hex'),
  'executorOids',to_jsonb(ARRAY(SELECT x::text FROM unnest(r.executor_oids) x)),
  'guardEpoch',r.guard_epoch::text,'epochIdentityHex',pg_catalog.encode(r.epoch_identity,'hex'),
  'registrationKeyHex',pg_catalog.encode(r.registration_key,'hex'),
  'installationId',r.installation_id::text,'databaseOid',r.database_oid::text,'schemaOid',r.schema_oid::text,
  'postmasterStartedAt',r.postmaster_started_at::text,
  'sourceEpoch',r.source_epoch,'sourceIncarnation',r.source_incarnation,
  'sourceProfileHex',pg_catalog.encode(r.source_profile_bytes,'hex'),
  'sourceEvidenceHex',pg_catalog.encode(r.source_evidence_bytes,'hex'),
  'runtimeReleaseId',r.runtime_release_id,'runtimeReleaseSha256',pg_catalog.encode(r.runtime_release_sha256,'hex'),
  'issuerXid',r.issuer_xid::text,'issuerActorOid',r.issuer_actor_oid::text,
  'issuedAt',r.issued_at::text,'profileId',r.profile_id,
  'initialBusinessSequence','0','initialPolicyVersion','0')::text,'UTF8')
$$;
REVOKE ALL ON FUNCTION truss.action_store_original_receipt(truss.action_store_registration) FROM PUBLIC;

CREATE FUNCTION truss.register_action_store_original(original_tenant bytea,original_key bytea,original_executors oid[],
 expected_release text,expected_release_sha256 bytea)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE r truss.action_store_registration%ROWTYPE;installed truss.catalog_runtime_installation%ROWTYPE;
 source truss.source_epoch_registry%ROWTYPE; actor oid;
BEGIN
 IF current_setting('server_version_num')<>'180006' OR current_setting('transaction_isolation')<>'read committed'
  OR current_setting('transaction_read_only')<>'off' OR current_setting('role')<>'none'
  OR current_user::text IS DISTINCT FROM session_user::text THEN
  RAISE EXCEPTION 'original native store registration context required' USING ERRCODE='55000';
 END IF;
 SELECT oid INTO actor FROM pg_catalog.pg_roles WHERE rolname=session_user AND rolsuper;
 IF actor IS NULL THEN RAISE EXCEPTION 'original direct store installer required' USING ERRCODE='55000';END IF;
 IF original_executors IS NULL OR cardinality(original_executors) NOT BETWEEN 0 AND 4
  OR cardinality(original_executors)<>(SELECT count(DISTINCT x) FROM unnest(original_executors) x) THEN
  RAISE EXCEPTION 'complete original executor enrollment required' USING ERRCODE='55000';END IF;
 IF original_tenant IS NULL OR octet_length(original_tenant) NOT BETWEEN 1 AND 4096
  OR original_key IS NULL OR octet_length(original_key) NOT BETWEEN 1 AND 256 THEN
  RAISE EXCEPTION 'bounded original registration inputs required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installed FROM truss.runtime_current_installation();
 IF installed.release_id IS DISTINCT FROM expected_release
  OR decode(installed.release_sha256,'hex') IS DISTINCT FROM expected_release_sha256 THEN
  RAISE EXCEPTION 'original native runtime required' USING ERRCODE='55000';END IF;
 -- The marker row is already held by the original administrative producer.
 -- One singleton logical scope prevents a new request from resetting namespace.
 SELECT * INTO r FROM truss.action_store_registration WHERE singleton FOR UPDATE NOWAIT;
 IF FOUND THEN
  IF r.registration_key IS DISTINCT FROM original_key OR r.tenant_identity IS DISTINCT FROM original_tenant
   OR r.executor_oids IS DISTINCT FROM original_executors OR r.profile_id<>'truss.action-store/native-pg18/0.1' THEN
   RAISE EXCEPTION 'existing original store scope refuses replacement' USING ERRCODE='55000';END IF;
  IF truss.action_store_original_receipt(r) IS DISTINCT FROM r.initial_receipt_bytes THEN
   RAISE EXCEPTION 'original store receipt correspondence required' USING ERRCODE='55000';END IF;
  RETURN r.initial_receipt_bytes;
 END IF;
 SELECT e.* INTO STRICT source FROM truss.source_epoch_current c JOIN truss.source_epoch_registry e
  ON e.installation_id=c.installation_id AND e.source_epoch=c.source_epoch
  WHERE c.singleton_id=1 AND c.installation_id=installed.installation_id::text FOR SHARE OF c,e NOWAIT;
 r.singleton:=true;r.control_id:=nextval('truss.action_store_control_seq'::regclass);
 r.logical_store_id:=gen_random_uuid();r.guard_epoch:=gen_random_uuid();
 r.store_identity:=convert_to('"'||r.logical_store_id::text||'"','UTF8');
 r.epoch_identity:=convert_to('"'||r.guard_epoch::text||'"','UTF8');
 r.executor_oids:=original_executors;
 r.tenant_identity:=original_tenant;r.registration_key:=original_key;r.installation_id:=installed.installation_id;
 SELECT d.oid,n.oid INTO STRICT r.database_oid,r.schema_oid
  FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n
  WHERE d.datname=current_database() AND n.nspname='truss';
 r.postmaster_started_at:=pg_postmaster_start_time();r.source_epoch:=source.source_epoch;
 r.source_incarnation:=source.target_incarnation;r.source_profile_bytes:=source.profile_bytes;r.source_evidence_bytes:=source.evidence_bytes;
 r.runtime_release_id:=installed.release_id;r.runtime_release_sha256:=decode(installed.release_sha256,'hex');
 r.issuer_xid:=pg_current_xact_id();r.issuer_actor_oid:=actor;r.issued_at:=clock_timestamp();
 r.profile_id:='truss.action-store/native-pg18/0.1';
 r.initial_receipt_bytes:=truss.action_store_original_receipt(r);
 INSERT INTO truss.action_store_registration(singleton,control_id,logical_store_id,store_identity,tenant_identity,executor_oids,
  guard_epoch,epoch_identity,registration_key,installation_id,database_oid,schema_oid,postmaster_started_at,
  source_epoch,source_incarnation,source_profile_bytes,source_evidence_bytes,runtime_release_id,runtime_release_sha256,
  issuer_xid,issuer_actor_oid,issued_at,initial_receipt_bytes,profile_id)
 VALUES(r.singleton,r.control_id,r.logical_store_id,r.store_identity,r.tenant_identity,r.executor_oids,r.guard_epoch,r.epoch_identity,
  r.registration_key,r.installation_id,r.database_oid,r.schema_oid,r.postmaster_started_at,r.source_epoch,r.source_incarnation,
  r.source_profile_bytes,r.source_evidence_bytes,r.runtime_release_id,r.runtime_release_sha256,r.issuer_xid,r.issuer_actor_oid,
  r.issued_at,r.initial_receipt_bytes,r.profile_id);
 RETURN r.initial_receipt_bytes;
END;
$$;
REVOKE ALL ON FUNCTION truss.register_action_store_original(bytea,bytea,oid[],text,bytea) FROM PUBLIC;

CREATE FUNCTION truss.observe_action_store_original(original_key bytea)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE r truss.action_store_registration%ROWTYPE;installed truss.catalog_runtime_installation%ROWTYPE;
 matched boolean; executor oid; recovery boolean;
BEGIN
 IF current_setting('server_version_num')<>'180006' OR current_setting('transaction_isolation')<>'read committed'
  OR current_setting('transaction_read_only')<>'off' OR current_setting('role')<>'none' OR original_key IS NULL OR octet_length(original_key) NOT BETWEEN 1 AND 256 THEN
  RAISE EXCEPTION 'original bounded store observation context required' USING ERRCODE='55000';END IF;
 LOCK TABLE truss.source_epoch_current,truss.source_epoch_registry IN SHARE MODE NOWAIT;
 PERFORM 1 FROM truss.installation_marker WHERE singleton_id=1 FOR SHARE NOWAIT;
 LOCK TABLE ONLY truss.catalog_runtime_installation,truss.action_store_registration IN SHARE MODE NOWAIT;
 SELECT * INTO r FROM ONLY truss.action_store_registration WHERE singleton AND registration_key=original_key FOR SHARE NOWAIT;
 IF NOT FOUND THEN RETURN NULL;END IF;
 SELECT oid,rolsuper INTO STRICT executor,recovery FROM pg_catalog.pg_roles WHERE rolname=session_user;
 -- Current native connecting role, not inherited function privilege or forwarded
 -- effective owner. Direct excluded superuser recovery is a separate path.
 IF NOT recovery AND NOT executor=ANY(r.executor_oids) THEN
  RAISE EXCEPTION 'original exact connecting store executor required' USING ERRCODE='55000';END IF;
 -- Reject leaked default or later grants before exposing any retained tenant/receipt.
 IF EXISTS(SELECT 1 FROM pg_catalog.pg_proc p CROSS JOIN LATERAL
   pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
   WHERE p.oid IN ('truss.observe_action_store_original(bytea)'::regprocedure,'truss.acquire_action_store_source_cut()'::regprocedure)
    AND (a.grantee<>p.proowner AND NOT a.grantee=ANY(r.executor_oids) OR a.grantor<>p.proowner OR a.is_grantable)) THEN
  RAISE EXCEPTION 'original exact store executor enrollment required' USING ERRCODE='55000';END IF;
 IF EXISTS(SELECT 1 FROM unnest(r.executor_oids) x WHERE NOT EXISTS(
   SELECT 1 FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
   WHERE p.oid='truss.observe_action_store_original(bytea)'::regprocedure AND a.grantee=x AND a.privilege_type='EXECUTE')) THEN
  RAISE EXCEPTION 'complete original store executor grant required' USING ERRCODE='55000';END IF;
 IF r.issuer_xid IS NOT DISTINCT FROM pg_current_xact_id_if_assigned() THEN
  RAISE EXCEPTION 'original issuance requires independently committed observation' USING ERRCODE='55000';END IF;
 IF truss.action_store_original_receipt(r) IS DISTINCT FROM r.initial_receipt_bytes THEN
  RAISE EXCEPTION 'original retained namespace receipt required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installed FROM truss.runtime_current_installation();
 SELECT r.installation_id=installed.installation_id AND r.database_oid=d.oid AND r.schema_oid=n.oid
  AND r.postmaster_started_at=pg_postmaster_start_time()
  AND r.runtime_release_id=installed.release_id AND r.runtime_release_sha256=decode(installed.release_sha256,'hex')
  AND EXISTS(SELECT 1 FROM truss.source_epoch_current c JOIN truss.source_epoch_registry e
    ON e.installation_id=c.installation_id AND e.source_epoch=c.source_epoch
    WHERE c.singleton_id=1 AND c.installation_id=r.installation_id::text AND e.source_epoch=r.source_epoch
     AND e.target_incarnation=r.source_incarnation AND e.profile_bytes=r.source_profile_bytes AND e.evidence_bytes=r.source_evidence_bytes)
 INTO STRICT matched FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n
  WHERE d.datname=current_database() AND n.nspname='truss';
 -- Fencing does not discard initial receipt, reset replay or imply rollback.
 RETURN convert_to(jsonb_build_object('interfaceVersion','truss.action-store-observation/0.1',
  'receiptHex',encode(r.initial_receipt_bytes,'hex'),'bindingCorrespondence',CASE WHEN matched THEN 'matches' ELSE 'fenced' END,
  'authority',false)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.observe_action_store_original(bytea) FROM PUBLIC;

CREATE FUNCTION truss.acquire_action_store_source_cut()
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE enrolled oid[];executor oid;recovery boolean;
BEGIN
 IF current_setting('server_version_num')<>'180006' OR current_setting('transaction_isolation')<>'repeatable read'
  OR current_setting('transaction_read_only')<>'off' OR current_setting('role')<>'none' THEN
  RAISE EXCEPTION 'original data store source cut required' USING ERRCODE='55000';END IF;
 LOCK TABLE ONLY truss.action_store_registration IN SHARE MODE NOWAIT;
 SELECT executor_oids INTO enrolled FROM ONLY truss.action_store_registration WHERE singleton FOR SHARE NOWAIT;
 IF NOT FOUND THEN RAISE EXCEPTION 'original issued store required' USING ERRCODE='55000';END IF;
 SELECT oid,rolsuper INTO STRICT executor,recovery FROM pg_catalog.pg_roles WHERE rolname=session_user;
 IF NOT recovery AND NOT executor=ANY(enrolled) THEN
  RAISE EXCEPTION 'original exact connecting data executor required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_action_store_source_cut() FROM PUBLIC;
