CREATE TABLE truss.capacity_check_memo (singleton_id smallint PRIMARY KEY REFERENCES truss.row_home_capacity (singleton_id), writer_xid xid8, dirty_generation bigint NOT NULL, verified_generation bigint, CONSTRAINT capacity_check_memo_singleton CHECK (singleton_id = 1), CONSTRAINT capacity_check_memo_complete CHECK (((writer_xid IS NULL AND dirty_generation = 0 AND verified_generation IS NULL) OR (writer_xid IS NOT NULL AND dirty_generation >= 1 AND (verified_generation IS NULL OR verified_generation BETWEEN 1 AND dirty_generation))) IS TRUE)); INSERT INTO truss.capacity_check_memo VALUES (1, NULL, 0, NULL); REVOKE ALL ON truss.capacity_check_memo FROM public; CREATE FUNCTION truss.capacity_cache_invalidate_original() RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE actual_xid xid8; memo truss.capacity_check_memo%ROWTYPE; next_generation bigint;
BEGIN
  IF TG_RELID<>'truss.row_home_capacity'::regclass OR TG_OP<>'UPDATE' OR TG_WHEN<>'AFTER' THEN
    RAISE EXCEPTION 'original capacity update required; deletion/truncation unavailable' USING ERRCODE='55000';
  END IF;
  actual_xid:=pg_current_xact_id_if_assigned();
  IF actual_xid IS NULL THEN RAISE EXCEPTION 'actual assigned capacity transaction required' USING ERRCODE='55000'; END IF;
  SELECT m.* INTO STRICT memo FROM truss.capacity_check_memo m WHERE m.singleton_id=1 FOR UPDATE;
  IF memo.writer_xid IS DISTINCT FROM actual_xid THEN next_generation:=1;
  ELSE
    IF memo.dirty_generation=9223372036854775807 THEN
      RAISE EXCEPTION 'original capacity generation exhausted' USING ERRCODE='54000';
    END IF;
    next_generation:=memo.dirty_generation+1;
  END IF;
  -- Even equal counter images invalidate. Memo updates do not change the ledger.
  UPDATE truss.capacity_check_memo SET writer_xid=actual_xid,
    dirty_generation=next_generation,verified_generation=NULL WHERE singleton_id=1;
  RETURN NEW;
END;
$$; REVOKE ALL ON FUNCTION truss.capacity_cache_invalidate_original() FROM public; CREATE FUNCTION truss.capacity_cache_check_original() RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE actual_xid xid8; memo truss.capacity_check_memo%ROWTYPE; layout_bytes bytea;resource_bytes bytea;
BEGIN
  IF TG_RELID<>'truss.capacity_check_memo'::regclass OR TG_OP<>'UPDATE' OR TG_WHEN<>'AFTER' THEN
    RAISE EXCEPTION 'original capacity memo callback required' USING ERRCODE='55000';
  END IF;
  actual_xid:=pg_current_xact_id_if_assigned();
  SELECT m.* INTO STRICT memo FROM truss.capacity_check_memo m WHERE m.singleton_id=1;
  IF actual_xid IS NULL OR memo.writer_xid IS DISTINCT FROM actual_xid THEN
    RAISE EXCEPTION 'original capacity memo transaction required' USING ERRCODE='55000';
  END IF;
  IF memo.verified_generation IS NOT DISTINCT FROM memo.dirty_generation THEN RETURN NULL; END IF;
  SELECT c.original_layout_bytes,c.original_resource_profile_bytes INTO STRICT layout_bytes,resource_bytes
    FROM truss.row_home_capacity c WHERE c.singleton_id=1;
  -- Stored profile equality is not independently registered profile authority.
  PERFORM truss.capacity_commit_check_original(layout_bytes,resource_bytes);
  UPDATE truss.capacity_check_memo SET verified_generation=dirty_generation WHERE singleton_id=1;
  RETURN NULL;
END;
$$; REVOKE ALL ON FUNCTION truss.capacity_cache_check_original() FROM public; CREATE TRIGGER capacity_cache_invalidate AFTER UPDATE ON truss.row_home_capacity FOR EACH ROW EXECUTE FUNCTION truss.capacity_cache_invalidate_original(); CREATE TRIGGER capacity_cache_delete BEFORE DELETE ON truss.row_home_capacity FOR EACH ROW EXECUTE FUNCTION truss.capacity_cache_invalidate_original(); CREATE TRIGGER capacity_cache_truncate BEFORE TRUNCATE ON truss.row_home_capacity EXECUTE FUNCTION truss.capacity_cache_invalidate_original(); CREATE CONSTRAINT TRIGGER capacity_cache_check AFTER UPDATE ON truss.capacity_check_memo DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.capacity_cache_check_original()