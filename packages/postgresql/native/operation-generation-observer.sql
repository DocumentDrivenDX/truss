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
  namespace_routes bytea[]:=ARRAY[]::bytea[];
  key_routes bytea[]:=ARRAY[]::bytea[];
  route record;
BEGIN
  IF TG_LEVEL<>'ROW' OR TG_WHEN<>'AFTER' OR TG_OP NOT IN ('INSERT','UPDATE','DELETE')
      OR TG_TABLE_SCHEMA<>'truss' OR TG_TABLE_NAME NOT IN ('row_home_state','row_home_node','row_home_scalar','object_key_bucket','object_key_reservation_bucket')
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
  IF TG_TABLE_NAME IN ('object_key_bucket','object_key_reservation_bucket') THEN
    IF TG_OP<>'INSERT' THEN namespace_routes:=array_append(namespace_routes,OLD.namespace_sha256);key_routes:=array_append(key_routes,OLD.key_sha256); END IF;
    IF TG_OP<>'DELETE' THEN namespace_routes:=array_append(namespace_routes,NEW.namespace_sha256);key_routes:=array_append(key_routes,NEW.key_sha256); END IF;
    FOR route IN SELECT DISTINCT n,k FROM unnest(namespace_routes,key_routes) r(n,k) ORDER BY n,k LOOP
      UPDATE truss.key_bucket_guard g SET generation=g.generation+1
        WHERE g.namespace_sha256=route.n AND g.key_sha256=route.k AND g.generation<9223372036854775807;
      IF NOT FOUND THEN
        IF EXISTS(SELECT 1 FROM truss.key_bucket_guard g WHERE g.namespace_sha256=route.n AND g.key_sha256=route.k) THEN
          RAISE EXCEPTION 'original key guard exhausted' USING ERRCODE='54000';
        END IF;
        RAISE EXCEPTION 'original key guard missing' USING ERRCODE='55000';
      END IF;
    END LOOP;
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

CREATE TRIGGER runtime_key_generation AFTER INSERT OR UPDATE OR DELETE ON truss.object_key_bucket
  FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_operation_generation();
CREATE TRIGGER runtime_reservation_generation AFTER INSERT OR UPDATE OR DELETE ON truss.object_key_reservation_bucket
  FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_operation_generation();
ALTER TABLE truss.object_key_bucket ENABLE ALWAYS TRIGGER runtime_key_generation;
ALTER TABLE truss.object_key_reservation_bucket ENABLE ALWAYS TRIGGER runtime_reservation_generation;
