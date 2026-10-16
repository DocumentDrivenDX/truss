-- Owner-private identity resolution only: no permission, permit or SQL execution.
-- An admitted guard must independently establish compiler/source/DDL custody,
-- current Subject/action/owner authority, and the complete operation lifecycle.
CREATE FUNCTION truss.resolve_preparation_program_binding(
 original_anchor pg_catalog.int4, original_nonce pg_catalog.uuid,
 original_data_xid pg_catalog.xid8)
RETURNS pg_catalog.int8
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE a truss.preparation_attempt_anchor%ROWTYPE;
 p truss.preparation_program_registration%ROWTYPE;
BEGIN
 IF current_setting('server_version_num')<>'180006'
  OR current_setting('transaction_isolation')<>'repeatable read'
  OR current_setting('transaction_read_only')<>'off'
  OR current_setting('role')<>'none'
  OR original_data_xid IS NULL
  OR original_data_xid IS DISTINCT FROM pg_current_xact_id()
  OR truss.check_preparation_attempt_data(original_anchor,original_nonce) IS NOT TRUE THEN
  RAISE EXCEPTION 'original data transaction and committed anchor required' USING ERRCODE='55000';
 END IF;
 LOCK TABLE ONLY truss.preparation_program_registration IN SHARE MODE NOWAIT;
 SELECT * INTO STRICT a FROM ONLY truss.preparation_attempt_anchor
  WHERE anchor_id=original_anchor AND anchor_nonce=original_nonce;
 SELECT r.* INTO p FROM ONLY truss.preparation_program_registration r
  WHERE convert_to('"'||r.program_identity::text||'"','UTF8')=a.program_identity
   AND r.store_control_id=a.store_control_id
   AND r.store_receipt_bytes=a.store_receipt_bytes
   AND r.issuer_xid IS DISTINCT FROM pg_current_xact_id()
  FOR SHARE NOWAIT;
 IF NOT FOUND THEN
  RAISE EXCEPTION 'original enrolled same-store program required' USING ERRCODE='55000';
 END IF;
 RETURN p.program_id;
END;
$$;
REVOKE ALL ON FUNCTION truss.resolve_preparation_program_binding(int4,uuid,xid8) FROM PUBLIC;
