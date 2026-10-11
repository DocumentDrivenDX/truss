-- Private archive-cut component. Installation/trigger/source authority is separate.
-- The held SHARE lock, not xid or an application flag, fences this backend's writes.
CREATE FUNCTION truss.runtime_fence_selected_archive_writes() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_RELID<>'truss.installation_archive'::regclass OR TG_NARGS<>0
  OR TG_WHEN<>'BEFORE' OR TG_LEVEL<>'STATEMENT'
  OR TG_OP NOT IN ('INSERT','UPDATE','DELETE','TRUNCATE') THEN
  RAISE EXCEPTION 'original archive write fence event required' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l
  WHERE l.locktype='relation' AND l.database=(SELECT oid FROM pg_catalog.pg_database
   WHERE datname=pg_catalog.current_database())
   AND l.relation=TG_RELID AND l.pid=pg_catalog.pg_backend_pid()
   AND l.mode='ShareLock' AND l.granted) THEN
  RAISE EXCEPTION 'selected archive cut excludes same-backend writes' USING ERRCODE='55000';
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_fence_selected_archive_writes() FROM PUBLIC;
CREATE TRIGGER runtime_selected_archive_write_fence
 BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.installation_archive
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_selected_archive_writes();
ALTER TABLE truss.installation_archive ENABLE ALWAYS TRIGGER runtime_selected_archive_write_fence;
