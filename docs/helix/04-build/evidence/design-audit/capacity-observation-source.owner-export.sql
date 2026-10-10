CREATE FUNCTION truss.capacity_operation_observe_original() RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE ledger truss.row_home_capacity%ROWTYPE; old_size bigint:=0; new_size bigint; added bigint:=0;
BEGIN
  IF TG_RELID<>'truss.row_home_operation'::regclass OR TG_OP NOT IN ('INSERT','UPDATE')
    OR (TG_OP='INSERT' AND TG_WHEN<>'AFTER') OR (TG_OP='UPDATE' AND TG_WHEN<>'BEFORE') THEN
    RAISE EXCEPTION 'original operation capacity event required' USING ERRCODE='55000';
  END IF;
  SELECT c.* INTO STRICT ledger FROM truss.row_home_capacity c WHERE c.singleton_id=1;
  IF ledger.reservation_writer_xid IS DISTINCT FROM pg_current_xact_id_if_assigned()
    OR NEW.original_writer_xid IS DISTINCT FROM ledger.reservation_writer_xid
    OR NEW.operation_ordinal IS DISTINCT FROM ledger.reservation_operation_ordinal
    OR NEW.original_context_bytes IS DISTINCT FROM ledger.reservation_context_bytes THEN
    RAISE EXCEPTION 'original operation event/reservation correspondence required' USING ERRCODE='55000';
  END IF;
  IF TG_OP='INSERT' THEN added:=1;
  ELSE
    IF OLD.original_writer_xid IS DISTINCT FROM NEW.original_writer_xid
      OR OLD.operation_ordinal IS DISTINCT FROM NEW.operation_ordinal
      OR OLD.original_context_bytes IS DISTINCT FROM NEW.original_context_bytes
      OR OLD.phase='application_finalized' THEN
      RAISE EXCEPTION 'original unfinished operation update required' USING ERRCODE='55000';
    END IF;
    old_size:=truss.custody_operation_size_original(OLD);
  END IF;
  new_size:=truss.custody_operation_size_original(NEW);
  -- BEFORE UPDATE sees the original unfinished registry row during finalization.
  -- Other BEFORE triggers/dependencies must be closed and final parity verified.
  PERFORM truss.capacity_transfer_original(ledger.reservation_context_bytes,ledger.reservation_plan_bytes,
    added,greatest(new_size-old_size,0),greatest(old_size-new_size,0));
  RETURN NEW;
END;
$$; REVOKE ALL ON FUNCTION truss.capacity_operation_observe_original() FROM public; CREATE FUNCTION truss.capacity_touch_observe_original() RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE ledger truss.row_home_capacity%ROWTYPE; old_size bigint:=0; new_size bigint; added bigint:=0;
BEGIN
  IF TG_RELID<>'truss.row_home_touch'::regclass OR TG_OP NOT IN ('INSERT','UPDATE')
    OR (TG_OP='INSERT' AND TG_WHEN<>'AFTER') OR (TG_OP='UPDATE' AND TG_WHEN<>'BEFORE') THEN
    RAISE EXCEPTION 'original touch capacity event required' USING ERRCODE='55000';
  END IF;
  SELECT c.* INTO STRICT ledger FROM truss.row_home_capacity c WHERE c.singleton_id=1;
  IF ledger.reservation_writer_xid IS DISTINCT FROM pg_current_xact_id_if_assigned()
    OR NEW.transaction_id IS DISTINCT FROM ledger.reservation_writer_xid THEN
    RAISE EXCEPTION 'original touch event/reservation correspondence required' USING ERRCODE='55000';
  END IF;
  IF TG_OP='INSERT' THEN added:=1;
  ELSE
    IF ROW(OLD.transaction_id,OLD.owner_kind,OLD.owner_id,OLD.owner_discriminator_id,OLD.property_owner_type_id,OLD.property_id)
      IS DISTINCT FROM ROW(NEW.transaction_id,NEW.owner_kind,NEW.owner_id,NEW.owner_discriminator_id,NEW.property_owner_type_id,NEW.property_id) THEN
      RAISE EXCEPTION 'original touch member identity required' USING ERRCODE='55000';
    END IF;
    old_size:=truss.custody_touch_size_original(OLD);
  END IF;
  new_size:=truss.custody_touch_size_original(NEW);
  PERFORM truss.capacity_transfer_original(ledger.reservation_context_bytes,ledger.reservation_plan_bytes,
    added,greatest(new_size-old_size,0),greatest(old_size-new_size,0));
  RETURN NEW;
END;
$$; REVOKE ALL ON FUNCTION truss.capacity_touch_observe_original() FROM public; CREATE TRIGGER capacity_operation_insert AFTER INSERT ON truss.row_home_operation FOR EACH ROW EXECUTE FUNCTION truss.capacity_operation_observe_original(); CREATE TRIGGER capacity_operation_update BEFORE UPDATE ON truss.row_home_operation FOR EACH ROW EXECUTE FUNCTION truss.capacity_operation_observe_original(); CREATE TRIGGER capacity_operation_delete BEFORE DELETE ON truss.row_home_operation FOR EACH ROW EXECUTE FUNCTION truss.capacity_operation_observe_original(); CREATE TRIGGER capacity_operation_truncate BEFORE TRUNCATE ON truss.row_home_operation EXECUTE FUNCTION truss.capacity_operation_observe_original(); CREATE TRIGGER capacity_touch_insert AFTER INSERT ON truss.row_home_touch FOR EACH ROW EXECUTE FUNCTION truss.capacity_touch_observe_original(); CREATE TRIGGER capacity_touch_update BEFORE UPDATE ON truss.row_home_touch FOR EACH ROW EXECUTE FUNCTION truss.capacity_touch_observe_original(); CREATE TRIGGER capacity_touch_delete BEFORE DELETE ON truss.row_home_touch FOR EACH ROW EXECUTE FUNCTION truss.capacity_touch_observe_original(); CREATE TRIGGER capacity_touch_truncate BEFORE TRUNCATE ON truss.row_home_touch EXECUTE FUNCTION truss.capacity_touch_observe_original()