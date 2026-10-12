-- Private epoch-state fence; does not exclude routine/role/configuration writers.
CREATE FUNCTION truss.runtime_fence_selected_epoch_writes() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_NARGS<>0 OR TG_WHEN<>'BEFORE' OR TG_LEVEL<>'STATEMENT'
  OR TG_OP NOT IN ('INSERT','UPDATE','DELETE','TRUNCATE')
  OR TG_RELID NOT IN ('truss.source_epoch_current'::regclass,
                     'truss.source_epoch_registry'::regclass) THEN
  RAISE EXCEPTION 'original epoch fence event required' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l
  WHERE l.locktype='relation' AND l.pid=pg_catalog.pg_backend_pid()
   AND l.database=(SELECT d.oid FROM pg_catalog.pg_database d WHERE d.datname=pg_catalog.current_database())
   AND l.relation IN ('truss.source_epoch_current'::regclass,
                     'truss.source_epoch_registry'::regclass)
   AND l.mode='ShareLock' AND l.granted) THEN
  RAISE EXCEPTION 'selected epoch cut excludes same-backend writes' USING ERRCODE='55000';
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_fence_selected_epoch_writes() FROM PUBLIC;
CREATE TRIGGER runtime_selected_epoch_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE
 ON truss.source_epoch_current FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_selected_epoch_writes();
ALTER TABLE truss.source_epoch_current ENABLE ALWAYS TRIGGER runtime_selected_epoch_write_fence;
CREATE TRIGGER runtime_selected_epoch_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE
 ON truss.source_epoch_registry FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_selected_epoch_writes();
ALTER TABLE truss.source_epoch_registry ENABLE ALWAYS TRIGGER runtime_selected_epoch_write_fence;
