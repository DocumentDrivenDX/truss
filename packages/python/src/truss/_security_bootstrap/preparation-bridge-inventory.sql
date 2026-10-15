-- Private selected-home definition correspondence adjunct, PG18.6 only.
-- Trusted original installation/dispatch and excluded administrative writers are
-- premises. No role membership, allocator state, policy, permit or execution.
-- Callers set a short lock_timeout BEFORE dispatch (including E claim dispatch).
CREATE FUNCTION truss.preparation_bridge_inventory()
RETURNS pg_catalog.jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' SET bytea_output='hex' AS $$
DECLARE homes pg_catalog.oid[]; routines pg_catalog.oid[]; result pg_catalog.jsonb;
BEGIN
 SELECT array_agg(c.oid ORDER BY c.oid) INTO homes
 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 WHERE (n.nspname='truss' AND c.relname IN
  ('preparation_attempt_anchor','preparation_program_registration','action_store_registration',
   'preparation_attempt_anchor_seq','preparation_program_registration_program_id_seq','action_store_control_seq',
   'preparation_program_sources'))
 OR (n.nspname='umf_security' AND c.relname='preparation_data_claim');
 IF cardinality(homes) IS DISTINCT FROM
  (CASE WHEN to_regclass('truss.preparation_program_sources') IS NULL THEN 7 ELSE 8 END) THEN
  RAISE EXCEPTION 'exact bridge table/sequence homes required' USING ERRCODE='55000';END IF;
 SELECT array_agg(p.oid ORDER BY p.oid) INTO routines
 FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
 WHERE (n.nspname='umf_security' AND p.proname IN ('claim_preparation_data','require_preparation_data_claim'))
 OR (n.nspname='truss' AND p.proname IN
  ('catalog_immutable','require_preparation_peer_xid','create_preparation_attempt_anchor',
   'check_preparation_attempt_coordinator','check_preparation_attempt_data',
   'resolve_preparation_program_binding','acquire_action_store_source_cut',
   'acquire_preparation_catalog_cut','observe_action_store_original',
   'runtime_fence_routine_ddl_writer','preparation_bridge_inventory',
   'acquire_preparation_bridge_cut','observe_preparation_bridge','read_preparation_program_sources'));
 -- This is an explicit adjunct, not a PL/pgSQL dependency-closure claim.
 SELECT jsonb_build_object(
  'profile','truss.preparation-bridge-definitions/0.1','authority',false,
  'homes',(SELECT jsonb_agg(jsonb_build_object('oid',c.oid,'namespace',n.nspname,
    'name',c.relname,'kind',c.relkind,'owner',c.relowner,'acl',c.relacl,
    'rowType',c.reltype,'accessMethod',c.relam,'tablespace',c.reltablespace,
    'options',c.reloptions,'persistence',c.relpersistence,'rls',c.relrowsecurity,
    'forceRls',c.relforcerowsecurity,'partition',c.relispartition) ORDER BY c.oid)
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE c.oid=ANY(homes)),
  'columns',(SELECT jsonb_agg(to_jsonb(a) ORDER BY a.attrelid,a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid=ANY(homes)),
  'defaults',(SELECT jsonb_agg(to_jsonb(d) ORDER BY d.oid) FROM pg_catalog.pg_attrdef d WHERE d.adrelid=ANY(homes)),
  'constraints',(SELECT jsonb_agg(to_jsonb(c) ORDER BY c.oid) FROM pg_catalog.pg_constraint c WHERE c.conrelid=ANY(homes)),
  'indexes',(SELECT jsonb_agg(jsonb_build_object('index',to_jsonb(i),'class',jsonb_build_object(
    'oid',c.oid,'owner',c.relowner,'acl',c.relacl,'accessMethod',c.relam,'options',c.reloptions,
    'tablespace',c.reltablespace)) ORDER BY i.indexrelid)
    FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class c ON c.oid=i.indexrelid WHERE i.indrelid=ANY(homes)),
  'types',(SELECT jsonb_agg(to_jsonb(t) ORDER BY t.oid) FROM pg_catalog.pg_type t WHERE t.typrelid=ANY(homes)),
  'triggers',(SELECT jsonb_agg(to_jsonb(t) ORDER BY t.oid) FROM pg_catalog.pg_trigger t WHERE t.tgrelid=ANY(homes)),
  'sequenceDefinitions',(SELECT jsonb_agg(to_jsonb(s) ORDER BY s.seqrelid) FROM pg_catalog.pg_sequence s WHERE s.seqrelid=ANY(homes)),
  'routines',(SELECT jsonb_agg(jsonb_build_object('definition',to_jsonb(p),'language',to_jsonb(l)) ORDER BY p.oid)
    FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE p.oid=ANY(routines)),
  'namespaces',(SELECT jsonb_agg(to_jsonb(n) ORDER BY n.oid) FROM pg_catalog.pg_namespace n WHERE n.nspname IN ('truss','umf_security')),
  'eventTriggers',(SELECT jsonb_agg(to_jsonb(e) ORDER BY e.oid) FROM pg_catalog.pg_event_trigger e),
  'dependencies',(SELECT jsonb_agg(to_jsonb(d) ORDER BY d.classid,d.objid,d.objsubid,d.refclassid,d.refobjid,d.refobjsubid,d.deptype)
    FROM pg_catalog.pg_depend d WHERE (d.classid='pg_catalog.pg_class'::regclass AND d.objid=ANY(homes))
      OR (d.classid='pg_catalog.pg_proc'::regclass AND d.objid=ANY(routines))),
  'writerScope',jsonb_build_object('tableAclAndOwners','homes','routineAclAndDefiners','routines',
   'supportedDdl','original all-tag epoch barrier','sharedRoleWriters','excluded; not fenced here',
   'administrativeBypass','excluded; event_triggers must remain enabled',
   'sequenceState','not covered','fullSemanticDependencies','not covered')) INTO result;
 IF octet_length(result::text)>2097152 THEN
  RAISE EXCEPTION 'bounded bridge inventory required' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.preparation_bridge_inventory() FROM PUBLIC;

-- Legacy metadata-only fixtures have no source attachment home. A selected
-- source-aware profile must require this non-null attachment; no fallback from
-- an installed but missing/uncommitted program attachment is allowed.
-- Original MVCC visibility from another issuer proves durable settlement; do
-- not depend on retained historical CLOG status for this long-lived row.
CREATE FUNCTION truss.read_preparation_program_sources(original_program pg_catalog.int8)
RETURNS pg_catalog.jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE result pg_catalog.jsonb;
BEGIN
 IF to_regclass('truss.preparation_program_sources') IS NULL THEN RETURN NULL;END IF;
 LOCK TABLE ONLY truss.preparation_program_sources IN ACCESS SHARE MODE NOWAIT;
 SELECT jsonb_build_object('programId',s.program_id::text,
  'packetHex',encode(s.original_source_packet,'hex'),'producerHex',encode(s.producer_identity,'hex'),
  'issuerXid',s.issuer_xid::text) INTO result FROM ONLY truss.preparation_program_sources s
  WHERE s.program_id=original_program AND s.issuer_xid IS DISTINCT FROM pg_current_xact_id() FOR SHARE NOWAIT;
 IF NOT FOUND THEN RAISE EXCEPTION 'original committed program sources required' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.read_preparation_program_sources(int8) FROM PUBLIC;

CREATE FUNCTION truss.acquire_preparation_bridge_cut(original_anchor pg_catalog.int4, original_nonce pg_catalog.uuid)
RETURNS pg_catalog.jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE original_program pg_catalog.int8;
BEGIN
 PERFORM truss.acquire_preparation_catalog_cut();
 -- Compatible with independent E INSERT and row locking; exclude explicit
 -- ACCESS EXCLUSIVE while D owns this cut. Program enrollment is already fixed.
 LOCK TABLE ONLY truss.preparation_attempt_anchor, truss.action_store_registration,
  umf_security.preparation_data_claim IN ROW EXCLUSIVE MODE NOWAIT;
 original_program:=truss.resolve_preparation_program_binding(original_anchor,original_nonce,pg_current_xact_id());
 IF to_regclass('truss.preparation_program_sources') IS NOT NULL THEN
  LOCK TABLE ONLY truss.preparation_program_sources IN SHARE MODE NOWAIT;
 END IF;
 IF current_setting('event_triggers') IS DISTINCT FROM 'on' OR NOT EXISTS(
  SELECT 1 FROM pg_catalog.pg_event_trigger e JOIN pg_catalog.pg_proc p ON p.oid=e.evtfoid
  JOIN pg_catalog.pg_roles r ON r.oid=e.evtowner JOIN pg_catalog.pg_language l ON l.oid=p.prolang
  WHERE e.evtname='truss_database_ddl_writer_barrier' AND e.evtevent='ddl_command_start'
   AND e.evtenabled='A' AND e.evttags IS NULL AND r.rolsuper
   AND p.oid='truss.runtime_fence_routine_ddl_writer()'::regprocedure
   AND p.proowner=e.evtowner AND NOT p.prosecdef AND p.prokind='f'
   AND p.prorettype='pg_catalog.event_trigger'::regtype AND NOT p.proretset
   AND p.pronargs=0 AND p.pronargdefaults=0 AND p.proargtypes=''::oidvector
   AND NOT p.proisstrict AND NOT p.proleakproof AND p.proparallel='u' AND p.prosupport=0
   AND l.lanname='plpgsql' AND p.provolatile='v'
   AND p.proconfig=ARRAY['search_path=pg_catalog, pg_temp']::text[]
   AND p.prosrc=__ORIGINAL_DDL_BODY__
   AND NOT EXISTS(SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
    WHERE a.grantee<>p.proowner OR a.grantor<>p.proowner OR a.privilege_type<>'EXECUTE' OR a.is_grantable)) THEN
  RAISE EXCEPTION 'original all-tag source epoch DDL barrier required' USING ERRCODE='55000';END IF;
 RETURN truss.preparation_bridge_inventory() || jsonb_build_object(
  'sourceAttachment',truss.read_preparation_program_sources(original_program));
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_preparation_bridge_cut(int4,uuid) FROM PUBLIC;

CREATE FUNCTION truss.observe_preparation_bridge(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE claim record; relation_name pg_catalog.text; required_mode pg_catalog.text;
 pass pg_catalog.int4; inventory pg_catalog.jsonb;
BEGIN
 -- Preacquire before even the owner's claim consumer reads these homes.
 -- Do not reacquire D's SHARE cuts behind a waiting administrator.
 LOCK TABLE ONLY truss.preparation_attempt_anchor,truss.preparation_program_registration,
  truss.action_store_registration,umf_security.preparation_data_claim,
  truss.source_epoch_current,truss.source_epoch_registry,
  truss.catalog_runtime_installation IN ACCESS SHARE MODE NOWAIT;
 IF to_regclass('truss.preparation_program_sources') IS NOT NULL THEN
  LOCK TABLE ONLY truss.preparation_program_sources IN ACCESS SHARE MODE NOWAIT;
 END IF;
 FOR pass IN 1..2 LOOP
 SELECT * INTO STRICT claim FROM umf_security.require_preparation_data_claim(original_anchor,original_nonce);
 FOR relation_name,required_mode IN SELECT * FROM (VALUES
  ('truss.source_epoch_current','ShareLock'),('truss.source_epoch_registry','ShareLock'),
  ('truss.preparation_program_registration','ShareLock'),
  ('truss.preparation_attempt_anchor','RowExclusiveLock'),
  ('truss.action_store_registration','RowExclusiveLock'),
  ('umf_security.preparation_data_claim','RowExclusiveLock')) AS required(name,mode)
 LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.locktype='relation'
   AND l.pid=claim.data_pid AND l.database=(SELECT oid FROM pg_database WHERE datname=current_database())
   AND l.relation=to_regclass(relation_name) AND l.mode=required_mode AND l.granted) THEN
   RAISE EXCEPTION 'original live D bridge exclusions required' USING ERRCODE='55000';END IF;
 END LOOP;
 IF to_regclass('truss.preparation_program_sources') IS NOT NULL AND NOT EXISTS(
  SELECT 1 FROM pg_catalog.pg_locks l WHERE l.locktype='relation' AND l.pid=claim.data_pid
  AND l.database=(SELECT oid FROM pg_database WHERE datname=current_database())
  AND l.relation=to_regclass('truss.preparation_program_sources') AND l.mode='ShareLock' AND l.granted) THEN
  RAISE EXCEPTION 'original live D source attachment exclusion required' USING ERRCODE='55000';END IF;
 -- require_preparation_data_claim established original PID/full XID, not merely
 -- a historical successful-cut flag. Snapshot-reset/reconnect is never attempted.
 IF pass=1 THEN inventory:=truss.preparation_bridge_inventory() || jsonb_build_object(
  'sourceAttachment',truss.read_preparation_program_sources(claim.program_id));END IF;
 END LOOP;
 RETURN inventory;
END;
$$;
REVOKE ALL ON FUNCTION truss.observe_preparation_bridge(int4,uuid) FROM PUBLIC;
