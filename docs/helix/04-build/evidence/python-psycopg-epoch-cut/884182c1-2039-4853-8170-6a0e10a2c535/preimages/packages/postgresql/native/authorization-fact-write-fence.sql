-- Private installed per-relation fact guard; not complete authority admission.
-- Installer supplies/qualifies exact bindings and ALWAYS triggers separately.
CREATE FUNCTION truss.runtime_fence_authorization_fact_write() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_NARGS<>0 OR TG_WHEN<>'BEFORE' OR TG_LEVEL<>'STATEMENT'
  OR TG_OP NOT IN ('INSERT','UPDATE','DELETE','TRUNCATE') THEN
  RAISE EXCEPTION 'original authorization fact fence event required' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l
  WHERE l.locktype='relation' AND l.pid=pg_catalog.pg_backend_pid()
   AND l.database=(SELECT d.oid FROM pg_catalog.pg_database d WHERE d.datname=pg_catalog.current_database())
   AND l.relation=TG_RELID AND l.mode='ShareLock' AND l.granted) THEN
  RAISE EXCEPTION 'selected authorization fact cut excludes same-backend writes' USING ERRCODE='55000';
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_fence_authorization_fact_write() FROM PUBLIC;
