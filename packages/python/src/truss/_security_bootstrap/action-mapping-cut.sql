-- Mapping-only RR exclusion. Fresh source/current authority remains separate.
CREATE FUNCTION truss.acquire_action_mapping_cut()
RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
 -- Original Subject helper checks PG18.6/RR/read-write/no SET ROLE and the
 -- original connecting Subject. This order precedes native role/policy cuts.
 PERFORM truss.acquire_action_subject_cut();
 LOCK TABLE ONLY truss.action_role_binding IN SHARE MODE NOWAIT;
 IF (SELECT count(*) FROM ONLY truss.action_role_binding) > 4096 THEN
  RAISE EXCEPTION 'original action mapping scope bound exceeded' USING ERRCODE='54000';
 END IF;
 PERFORM 1 FROM ONLY truss.action_role_binding
  ORDER BY binding_id FOR SHARE NOWAIT;
 -- Updates/deletes newer than RR refuse. A newly committed invisible insert
 -- is not detected here; complete fresh RC correspondence is still required.
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_action_mapping_cut() FROM PUBLIC;
