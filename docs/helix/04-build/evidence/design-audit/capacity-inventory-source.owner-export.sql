CREATE FUNCTION truss.capacity_verify_inventory_original(layout_bytes bytea, resource_bytes bytea) RETURNS TABLE (observed_rows bigint, observed_custody_bytes bigint) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE
  ledger truss.row_home_capacity%ROWTYPE;
  operation truss.row_home_operation%ROWTYPE;
  touch truss.row_home_touch%ROWTYPE;
  revision integer;
  member_size bigint;
  targets oid[]:=ARRAY['truss.schema_head'::regclass::oid,'truss.row_home_capacity'::regclass::oid,
    'truss.row_home_operation'::regclass::oid,'truss.row_home_touch'::regclass::oid];
BEGIN
  IF layout_bytes IS NULL OR resource_bytes IS NULL THEN
    RAISE EXCEPTION 'original installation profiles required' USING ERRCODE='22023';
  END IF;
  -- Do not let owner bypass or FORCE RLS make a filtered inventory look complete.
  -- Physical identity, dependencies, triggers and write privileges remain external.
  IF EXISTS (SELECT 1 FROM pg_class c WHERE c.oid=ANY(targets)
      AND (c.relrowsecurity OR c.relforcerowsecurity OR c.relkind<>'r'))
    OR EXISTS (SELECT 1 FROM pg_inherits i WHERE i.inhrelid=ANY(targets) OR i.inhparent=ANY(targets)) THEN
    RAISE EXCEPTION 'original unfiltered noninherited inventory required' USING ERRCODE='55000';
  END IF;
  PERFORM truss.custody_codec_columns_original('operation');
  PERFORM truss.custody_codec_columns_original('touch');
  SELECT h.rev INTO STRICT revision FROM truss.schema_head h WHERE h.id=1 FOR SHARE;
  SELECT c.* INTO STRICT ledger FROM truss.row_home_capacity c WHERE c.singleton_id=1 FOR UPDATE;
  IF ledger.original_layout_bytes IS DISTINCT FROM layout_bytes
    OR ledger.original_resource_profile_bytes IS DISTINCT FROM resource_bytes THEN
    RAISE EXCEPTION 'original ledger profile correspondence required' USING ERRCODE='55000';
  END IF;
  observed_rows:=0; observed_custody_bytes:=0;
  -- No current-xid, phase, ordinal or caller-selected member filter.
  FOR operation IN SELECT o.* FROM truss.row_home_operation o LOOP
    member_size:=truss.custody_operation_size_original(operation);
    IF observed_rows>=65536 OR member_size>536870912-observed_custody_bytes THEN
      RAISE EXCEPTION 'complete retained inventory bound' USING ERRCODE='54000';
    END IF;
    observed_rows:=observed_rows+1; observed_custody_bytes:=observed_custody_bytes+member_size;
  END LOOP;
  FOR touch IN SELECT t.* FROM truss.row_home_touch t LOOP
    member_size:=truss.custody_touch_size_original(touch);
    IF observed_rows>=65536 OR member_size>536870912-observed_custody_bytes THEN
      RAISE EXCEPTION 'complete retained inventory bound' USING ERRCODE='54000';
    END IF;
    observed_rows:=observed_rows+1; observed_custody_bytes:=observed_custody_bytes+member_size;
  END LOOP;
  IF observed_rows IS DISTINCT FROM ledger.retained_rows
    OR observed_custody_bytes IS DISTINCT FROM ledger.retained_custody_bytes THEN
    RAISE EXCEPTION 'complete retained inventory/ledger parity required' USING ERRCODE='55000';
  END IF;
  RETURN NEXT;
END;
$$; REVOKE ALL ON FUNCTION truss.capacity_verify_inventory_original(bytea, bytea) FROM public