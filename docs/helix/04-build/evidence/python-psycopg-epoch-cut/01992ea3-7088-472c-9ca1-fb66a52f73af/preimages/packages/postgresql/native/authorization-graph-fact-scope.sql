-- Private selected-association projection. Ordinary grants/installed authority
-- and complete required association membership are separate admission premises.
CREATE FUNCTION truss.runtime_guard_graph_fact_scope_row() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_RELID<>'truss.authorization_graph_fact_scope'::regclass
  OR TG_OP<>'INSERT' OR TG_WHEN<>'BEFORE' OR TG_LEVEL<>'ROW' OR TG_NARGS<>0
  OR NEW.original_writer_xid IS DISTINCT FROM pg_current_xact_id() THEN
  RAISE EXCEPTION 'original native graph fact scope required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.authorization_graph_fact_scope s WHERE s.original_writer_xid=NEW.original_writer_xid AND s.rel_type_id=NEW.rel_type_id)
  AND (SELECT count(*) FROM truss.authorization_graph_fact_scope s WHERE s.original_writer_xid=NEW.original_writer_xid)>=32 THEN
  RAISE EXCEPTION 'graph fact scope capacity exceeded' USING ERRCODE='54000';
 END IF;
 RETURN NEW;
END;
$$;
CREATE FUNCTION truss.runtime_guard_graph_fact_scope_mutation() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RAISE EXCEPTION 'retained graph fact scope is immutable' USING ERRCODE='55000';
END;
$$;
CREATE TRIGGER graph_fact_scope_original BEFORE INSERT ON truss.authorization_graph_fact_scope
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_guard_graph_fact_scope_row();
CREATE TRIGGER graph_fact_scope_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.authorization_graph_fact_scope
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_guard_graph_fact_scope_mutation();
ALTER TABLE truss.authorization_graph_fact_scope ENABLE ALWAYS TRIGGER graph_fact_scope_original;
ALTER TABLE truss.authorization_graph_fact_scope ENABLE ALWAYS TRIGGER graph_fact_scope_immutable;
CREATE FUNCTION truss.runtime_register_graph_fact_scope(selected_types integer[],original_evidence bytea)
RETURNS integer LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE native_xid xid8; native_context bytea; total integer;
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
  THEN session_user::text ELSE current_setting('role') END)
  OR current_setting('transaction_isolation')<>'read committed'
  OR current_setting('transaction_read_only')<>'off' THEN
  RAISE EXCEPTION 'original graph fact scope invoker required' USING ERRCODE='55000';
 END IF;
 IF selected_types IS NULL OR array_ndims(selected_types) IS DISTINCT FROM 1
  OR array_lower(selected_types,1) IS DISTINCT FROM 1 OR cardinality(selected_types) NOT BETWEEN 1 AND 32
  OR original_evidence IS NULL OR octet_length(original_evidence) NOT BETWEEN 1 AND 65536
  OR EXISTS(SELECT 1 FROM unnest(selected_types) v WHERE v IS NULL OR v<=0)
  OR (SELECT count(DISTINCT v) FROM unnest(selected_types) v)<>cardinality(selected_types) THEN
  RAISE EXCEPTION 'bounded complete graph fact comparison required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
  AND l.database=(SELECT oid FROM pg_database WHERE datname=current_database())
  AND l.locktype='relation' AND l.relation='truss.edge'::regclass AND l.mode='ShareLock') THEN
  RAISE EXCEPTION 'original graph fact table cut required' USING ERRCODE='55000';
 END IF;
 IF (SELECT count(*) FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
  AND l.database=(SELECT oid FROM pg_database WHERE datname=current_database())
  AND l.locktype='relation' AND l.mode='ShareLock'
  AND l.relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass))<>2
  OR EXISTS(SELECT 1 FROM pg_inherits i WHERE i.inhparent='truss.edge'::regclass OR i.inhrelid='truss.edge'::regclass) THEN
  RAISE EXCEPTION 'original epoch cut and non-inherited graph store required' USING ERRCODE='55000';
 END IF;
 native_xid:=pg_current_xact_id();
 native_context:=convert_to(jsonb_build_object('xid',native_xid::text,
  'databaseOid',(SELECT oid::text FROM pg_database WHERE datname=current_database()),
  'backendPid',pg_backend_pid()::text,'sessionUser',session_user::text,
  'actingUser',current_user::text,
  'actorRoleOid',(SELECT oid::text FROM pg_roles WHERE rolname=current_user),
  'sessionRoleOid',(SELECT oid::text FROM pg_roles WHERE rolname=session_user))::text,'UTF8');
 IF EXISTS(SELECT 1 FROM truss.authorization_graph_fact_scope s WHERE s.original_writer_xid=native_xid
  AND (s.original_context_bytes IS DISTINCT FROM native_context OR s.original_evidence_bytes IS DISTINCT FROM original_evidence)) THEN
  RAISE EXCEPTION 'original graph fact scope correspondence required' USING ERRCODE='55000';
 END IF;
 SELECT count(*) INTO total FROM (SELECT s.rel_type_id FROM truss.authorization_graph_fact_scope s
  WHERE s.original_writer_xid=native_xid UNION SELECT v FROM unnest(selected_types) v) required;
 IF total>32 THEN RAISE EXCEPTION 'graph fact scope capacity exceeded' USING ERRCODE='54000'; END IF;
 IF EXISTS(SELECT 1 FROM unnest(selected_types) v WHERE NOT EXISTS(SELECT 1 FROM truss.rel_def r WHERE r.rel_type_id=v)) THEN
  RAISE EXCEPTION 'original graph association definition required' USING ERRCODE='55000';
 END IF;
 INSERT INTO truss.authorization_graph_fact_scope
 SELECT native_xid,v,native_context,original_evidence FROM unnest(selected_types) v
 ON CONFLICT(original_writer_xid,rel_type_id) DO NOTHING;
 RETURN total;
END;
$$;
CREATE FUNCTION truss.runtime_fence_selected_graph_fact_row() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE protected boolean;
BEGIN
 IF TG_RELID<>'truss.edge'::regclass OR TG_NARGS<>0 OR TG_WHEN<>'BEFORE' OR TG_LEVEL<>'ROW'
  OR TG_OP NOT IN ('INSERT','UPDATE','DELETE') THEN
  RAISE EXCEPTION 'original selected graph fact event required' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
  AND l.database=(SELECT oid FROM pg_database WHERE datname=current_database())
  AND l.locktype='relation' AND l.relation=TG_RELID AND l.mode='ShareLock') THEN
  IF NOT EXISTS(SELECT 1 FROM truss.authorization_graph_fact_scope s WHERE s.original_writer_xid=pg_current_xact_id_if_assigned()) THEN
   RAISE EXCEPTION 'original selected graph fact scope unavailable' USING ERRCODE='55000';
  END IF;
  SELECT EXISTS(SELECT 1 FROM truss.authorization_graph_fact_scope s
   WHERE s.original_writer_xid=pg_current_xact_id_if_assigned()
   AND ((TG_OP<>'INSERT' AND s.rel_type_id=OLD.rel_type_id)
     OR (TG_OP<>'DELETE' AND s.rel_type_id=NEW.rel_type_id))) INTO protected;
  IF protected THEN
   RAISE EXCEPTION 'selected graph fact cut excludes association change' USING ERRCODE='55000';
  END IF;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_guard_graph_fact_scope_row(),
 truss.runtime_guard_graph_fact_scope_mutation(),truss.runtime_register_graph_fact_scope(integer[],bytea),
 truss.runtime_fence_selected_graph_fact_row() FROM PUBLIC;
-- Installation/profile adoption must independently verify these exact guards.
CREATE TRIGGER selected_graph_fact_row BEFORE INSERT OR UPDATE OR DELETE ON truss.edge
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_fence_selected_graph_fact_row();
ALTER TABLE truss.edge ENABLE ALWAYS TRIGGER selected_graph_fact_row;
CREATE TRIGGER selected_graph_fact_truncate BEFORE TRUNCATE ON truss.edge
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write();
ALTER TABLE truss.edge ENABLE ALWAYS TRIGGER selected_graph_fact_truncate;
