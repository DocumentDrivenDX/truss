-- Internal canonical-event generation producer, not the complete row-touch observer.
-- Full scope/capacity/touch and journal producers must precede public write readiness.
CREATE FUNCTION truss.runtime_observe_operation_generation() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  actual_xid xid8 := pg_current_xact_id_if_assigned();
  operation truss.row_home_operation%ROWTYPE;
  resolved_count bigint;
BEGIN
  IF TG_LEVEL<>'ROW' OR TG_WHEN<>'AFTER' OR TG_OP NOT IN ('INSERT','UPDATE','DELETE')
      OR TG_TABLE_SCHEMA<>'truss' OR TG_TABLE_NAME NOT IN ('row_home_state','row_home_node','row_home_scalar')
      OR TG_NARGS<>0 OR actual_xid IS NULL THEN
    RAISE EXCEPTION 'unregistered canonical event' USING ERRCODE='55000';
  END IF;
  SELECT count(*) INTO resolved_count FROM truss.row_home_operation AS o
    WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized';
  IF resolved_count<>1 THEN
    RAISE EXCEPTION 'canonical event needs one original unfinished operation' USING ERRCODE='55000';
  END IF;
  SELECT * INTO STRICT operation FROM truss.row_home_operation AS o
    WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized' FOR UPDATE;
  IF operation.effect_generation=9223372036854775807 THEN
    RAISE EXCEPTION 'operation generation exhausted' USING ERRCODE='54000';
  END IF;
  UPDATE truss.row_home_operation AS o SET
    effect_generation=o.effect_generation+1, phase='admitted',
    readiness_generation=NULL,sealed_generation=NULL,application_generation=NULL,
    application_result_bytes=NULL
    WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=operation.operation_ordinal;
  RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_observe_operation_generation() FROM PUBLIC;
CREATE TRIGGER runtime_state_generation AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_state
  FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_operation_generation();
CREATE TRIGGER runtime_node_generation AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_node
  FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_operation_generation();
CREATE TRIGGER runtime_scalar_generation AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_scalar
  FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_operation_generation();
ALTER TABLE truss.row_home_state ENABLE ALWAYS TRIGGER runtime_state_generation;
ALTER TABLE truss.row_home_node ENABLE ALWAYS TRIGGER runtime_node_generation;
ALTER TABLE truss.row_home_scalar ENABLE ALWAYS TRIGGER runtime_scalar_generation;
