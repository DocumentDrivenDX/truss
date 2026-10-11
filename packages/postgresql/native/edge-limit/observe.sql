-- Private component. Original family/guard/allocation admission remains required.
-- Install after event-frame.sql, row-touch custody and capacity observation.
CREATE FUNCTION truss.edge_limit_observe() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET timezone='UTC' SET datestyle='ISO, YMD' SET bytea_output='hex' AS $$
DECLARE op truss.row_home_operation%ROWTYPE; planned truss.row_home_operation%ROWTYPE;
 observed truss.row_home_operation%ROWTYPE; ledger truss.row_home_capacity%ROWTYPE;
 actual_xid xid8:=pg_current_xact_id_if_assigned(); context jsonb; frame jsonb;
 old_image jsonb:='null'::jsonb; new_image jsonb:='null'::jsonb;
BEGIN
 IF TG_LEVEL<>'ROW' OR TG_WHEN<>'AFTER' OR TG_OP NOT IN ('INSERT','UPDATE','DELETE')
  OR TG_NARGS<>0 OR TG_TABLE_SCHEMA<>'truss' OR actual_xid IS NULL
  OR TG_RELID NOT IN ('truss.edge'::regclass,'truss.edge_limit'::regclass)
  OR TG_NAME<>(CASE TG_TABLE_NAME WHEN 'edge' THEN 'edge_limit_edge_observe' ELSE 'edge_limit_marker_observe' END) THEN
  RAISE EXCEPTION 'registered original edge event required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=TG_RELID AND t.tgname=TG_NAME
  AND t.tgfoid='truss.edge_limit_observe()'::regprocedure AND t.tgtype=29 AND t.tgenabled='A'
  AND t.tgnargs=0 AND t.tgattr=''::int2vector AND t.tgqual IS NULL AND NOT t.tgisinternal
  AND t.tgconstraint=0 AND NOT t.tgdeferrable AND NOT t.tginitdeferred
  AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL)
  OR EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=TG_RELID
   AND t.tgname='runtime_catalog_generation') THEN
  RAISE EXCEPTION 'nonoverlapping original edge observer required' USING ERRCODE='55000';
 END IF;
 BEGIN
  SELECT o.* INTO STRICT op FROM truss.row_home_operation o
   WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized' FOR UPDATE;
 EXCEPTION WHEN no_data_found OR too_many_rows THEN
  RAISE EXCEPTION 'exactly one unfinished original operation required' USING ERRCODE='55000';
 END;
 IF op.phase NOT IN ('admitted','effects_ready','row_sealed')
  OR op.operation_kind NOT IN ('mutation','import','catalog-transform','catalog-acceptance','home-migration','administrative-repair') THEN
  RAISE EXCEPTION 'original unfinished event frontier required' USING ERRCODE='55000';
 END IF;
 IF TG_TABLE_NAME='rel_def' AND (op.operation_kind<>'catalog-acceptance'
  OR NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
   AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock'))) THEN
  RAISE EXCEPTION 'original exclusive catalog acceptance required' USING ERRCODE='55000';
 END IF;
 IF op.effect_generation=9223372036854775807 THEN
  RAISE EXCEPTION 'edge event generation exhausted' USING ERRCODE='54000';
 END IF;
 context:=truss.row_touch_registry_original(op);
 PERFORM truss.row_touch_active_context_original(context);
 frame:=truss.edge_limit_frame_original(op.effect_obligation_bytes,op.effect_generation);
 IF TG_OP<>'INSERT' THEN old_image:=to_jsonb(OLD);END IF;
 IF TG_OP<>'DELETE' THEN new_image:=to_jsonb(NEW);END IF;
 IF frame->'event' IS DISTINCT FROM jsonb_build_object('relation',TG_TABLE_NAME,
  'opcode',TG_OP,'oldImage',old_image,'newImage',new_image) THEN
  RAISE EXCEPTION 'complete original OLD NEW event correspondence required' USING ERRCODE='55000';
 END IF;
 SELECT l.* INTO STRICT ledger FROM truss.row_home_capacity l WHERE l.singleton_id=1;
 IF ledger.reservation_writer_xid IS DISTINCT FROM actual_xid
  OR ledger.reservation_operation_ordinal IS DISTINCT FROM op.operation_ordinal
  OR ledger.reservation_context_bytes IS DISTINCT FROM op.original_context_bytes
  OR ledger.reservation_plan_bytes IS DISTINCT FROM op.effect_obligation_bytes
  OR ledger.original_layout_bytes IS DISTINCT FROM truss.row_touch_artifact_original(context->'originalLayout')
  OR ledger.original_resource_profile_bytes IS DISTINCT FROM truss.row_touch_artifact_original(context->'originalResourceProfile') THEN
  RAISE EXCEPTION 'original edge event reservation required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
  AND l.relation='truss.schema_head'::regclass AND l.mode IN
   ('RowShareLock','ShareLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'original catalog exclusion required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid='truss.row_home_operation'::regclass
  AND t.tgname='capacity_operation_update'
  AND t.tgfoid='truss.capacity_operation_observe_original()'::regprocedure
  AND t.tgtype=19 AND t.tgenabled='A' AND t.tgnargs=0 AND t.tgattr=''::int2vector
  AND t.tgqual IS NULL AND NOT t.tgisinternal AND t.tgconstraint=0
  AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL) THEN
  RAISE EXCEPTION 'original operation capacity hook required' USING ERRCODE='55000';
 END IF;
 planned:=op;planned.effect_generation:=op.effect_generation+1;planned.phase:='admitted';
 planned.readiness_generation:=NULL;planned.sealed_generation:=NULL;
 planned.application_generation:=NULL;planned.application_result_bytes:=NULL;
 UPDATE truss.row_home_operation o SET effect_generation=planned.effect_generation,
  phase=planned.phase,readiness_generation=NULL,sealed_generation=NULL,
  application_generation=NULL,application_result_bytes=NULL
  WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=op.operation_ordinal
   AND o IS NOT DISTINCT FROM op RETURNING o.* INTO STRICT observed;
 IF observed IS DISTINCT FROM planned THEN
  RAISE EXCEPTION 'edge event registry update correspondence required' USING ERRCODE='55000';
 END IF;
 SELECT o.* INTO STRICT observed FROM truss.row_home_operation o
  WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=op.operation_ordinal;
 IF observed IS DISTINCT FROM planned THEN
  RAISE EXCEPTION 'edge event registry final correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.edge_limit_observe() FROM PUBLIC;
CREATE FUNCTION truss.edge_limit_catalog_observe() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET timezone='UTC' SET datestyle='ISO, YMD' SET bytea_output='hex' AS $$
DECLARE op truss.row_home_operation%ROWTYPE; planned truss.row_home_operation%ROWTYPE;
 observed truss.row_home_operation%ROWTYPE; ledger truss.row_home_capacity%ROWTYPE;
 actual_xid xid8:=pg_current_xact_id_if_assigned(); context jsonb; frame jsonb;
 old_image jsonb:='null'::jsonb; new_image jsonb:='null'::jsonb;
BEGIN
 IF TG_LEVEL<>'ROW' OR TG_WHEN<>'AFTER' OR TG_OP NOT IN ('INSERT','UPDATE','DELETE')
  OR TG_NARGS<>0 OR TG_TABLE_SCHEMA<>'truss' OR actual_xid IS NULL
  OR TG_RELID<>'truss.rel_def'::regclass OR TG_NAME<>'edge_limit_catalog_observe' THEN
  RAISE EXCEPTION 'registered original edge event required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=TG_RELID AND t.tgname=TG_NAME
  AND t.tgfoid='truss.edge_limit_catalog_observe()'::regprocedure AND t.tgtype=29 AND t.tgenabled='A'
  AND t.tgnargs=0 AND t.tgattr=''::int2vector AND t.tgqual IS NULL AND NOT t.tgisinternal
  AND t.tgconstraint=0 AND NOT t.tgdeferrable AND NOT t.tginitdeferred
  AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL)
  OR EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=TG_RELID
   AND t.tgname='runtime_catalog_generation') THEN
  RAISE EXCEPTION 'nonoverlapping original edge observer required' USING ERRCODE='55000';
 END IF;
 BEGIN
  SELECT o.* INTO STRICT op FROM truss.row_home_operation o
   WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized' FOR UPDATE;
 EXCEPTION WHEN no_data_found OR too_many_rows THEN
  RAISE EXCEPTION 'exactly one unfinished original operation required' USING ERRCODE='55000';
 END;
 IF op.phase NOT IN ('admitted','effects_ready','row_sealed')
  OR op.operation_kind NOT IN ('mutation','import','catalog-transform','catalog-acceptance','home-migration','administrative-repair') THEN
  RAISE EXCEPTION 'original unfinished event frontier required' USING ERRCODE='55000';
 END IF;
 IF TG_TABLE_NAME='rel_def' AND (op.operation_kind<>'catalog-acceptance'
  OR NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
   AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock'))) THEN
  RAISE EXCEPTION 'original exclusive catalog acceptance required' USING ERRCODE='55000';
 END IF;
 IF op.effect_generation=9223372036854775807 THEN
  RAISE EXCEPTION 'edge event generation exhausted' USING ERRCODE='54000';
 END IF;
 context:=truss.row_touch_registry_original(op);
 PERFORM truss.row_touch_active_context_original(context);
 frame:=truss.edge_limit_frame_original(op.effect_obligation_bytes,op.effect_generation);
 IF TG_OP<>'INSERT' THEN old_image:=to_jsonb(OLD);END IF;
 IF TG_OP<>'DELETE' THEN new_image:=to_jsonb(NEW);END IF;
 IF frame->'event' IS DISTINCT FROM jsonb_build_object('relation',TG_TABLE_NAME,
  'opcode',TG_OP,'oldImage',old_image,'newImage',new_image) THEN
  RAISE EXCEPTION 'complete original OLD NEW event correspondence required' USING ERRCODE='55000';
 END IF;
 SELECT l.* INTO STRICT ledger FROM truss.row_home_capacity l WHERE l.singleton_id=1;
 IF ledger.reservation_writer_xid IS DISTINCT FROM actual_xid
  OR ledger.reservation_operation_ordinal IS DISTINCT FROM op.operation_ordinal
  OR ledger.reservation_context_bytes IS DISTINCT FROM op.original_context_bytes
  OR ledger.reservation_plan_bytes IS DISTINCT FROM op.effect_obligation_bytes
  OR ledger.original_layout_bytes IS DISTINCT FROM truss.row_touch_artifact_original(context->'originalLayout')
  OR ledger.original_resource_profile_bytes IS DISTINCT FROM truss.row_touch_artifact_original(context->'originalResourceProfile') THEN
  RAISE EXCEPTION 'original edge event reservation required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
  AND l.relation='truss.schema_head'::regclass AND l.mode IN
   ('RowShareLock','ShareLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'original catalog exclusion required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid='truss.row_home_operation'::regclass
  AND t.tgname='capacity_operation_update'
  AND t.tgfoid='truss.capacity_operation_observe_original()'::regprocedure
  AND t.tgtype=19 AND t.tgenabled='A' AND t.tgnargs=0 AND t.tgattr=''::int2vector
  AND t.tgqual IS NULL AND NOT t.tgisinternal AND t.tgconstraint=0
  AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL) THEN
  RAISE EXCEPTION 'original operation capacity hook required' USING ERRCODE='55000';
 END IF;
 planned:=op;planned.effect_generation:=op.effect_generation+1;planned.phase:='admitted';
 planned.readiness_generation:=NULL;planned.sealed_generation:=NULL;
 planned.application_generation:=NULL;planned.application_result_bytes:=NULL;
 UPDATE truss.row_home_operation o SET effect_generation=planned.effect_generation,
  phase=planned.phase,readiness_generation=NULL,sealed_generation=NULL,
  application_generation=NULL,application_result_bytes=NULL
  WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=op.operation_ordinal
   AND o IS NOT DISTINCT FROM op RETURNING o.* INTO STRICT observed;
 IF observed IS DISTINCT FROM planned THEN
  RAISE EXCEPTION 'edge event registry update correspondence required' USING ERRCODE='55000';
 END IF;
 SELECT o.* INTO STRICT observed FROM truss.row_home_operation o
  WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=op.operation_ordinal;
 IF observed IS DISTINCT FROM planned THEN
  RAISE EXCEPTION 'edge event registry final correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.edge_limit_catalog_observe() FROM PUBLIC;
CREATE TRIGGER edge_limit_edge_observe AFTER INSERT OR UPDATE OR DELETE ON truss.edge
 FOR EACH ROW EXECUTE FUNCTION truss.edge_limit_observe();
ALTER TABLE truss.edge ENABLE ALWAYS TRIGGER edge_limit_edge_observe;
CREATE TRIGGER edge_limit_marker_observe AFTER INSERT OR UPDATE OR DELETE ON truss.edge_limit
 FOR EACH ROW EXECUTE FUNCTION truss.edge_limit_observe();
ALTER TABLE truss.edge_limit ENABLE ALWAYS TRIGGER edge_limit_marker_observe;
-- Explicitly replace the existing relationship generation observer.
DROP TRIGGER IF EXISTS runtime_catalog_generation ON truss.rel_def;
CREATE TRIGGER edge_limit_catalog_observe AFTER INSERT OR UPDATE OR DELETE ON truss.rel_def
 FOR EACH ROW EXECUTE FUNCTION truss.edge_limit_catalog_observe();
ALTER TABLE truss.rel_def ENABLE ALWAYS TRIGGER edge_limit_catalog_observe;
