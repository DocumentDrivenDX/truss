CREATE FUNCTION truss.runtime_immutable_layout_migration_receipt() RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
BEGIN
 IF TG_RELID<>'truss.layout_migration_receipt'::regclass OR TG_NARGS<>0
  OR TG_WHEN<>'BEFORE' OR NOT ((TG_LEVEL='ROW' AND TG_OP IN ('UPDATE','DELETE'))
   OR (TG_LEVEL='STATEMENT' AND TG_OP='TRUNCATE')) THEN
  RAISE EXCEPTION 'unregistered migration receipt event' USING ERRCODE='55000';
 END IF;
 RAISE EXCEPTION 'original migration receipt is immutable; cleanup unavailable' USING ERRCODE='55000';
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_immutable_layout_migration_receipt() FROM public; CREATE TRIGGER runtime_layout_migration_receipt_immutable BEFORE DELETE OR UPDATE ON truss.layout_migration_receipt FOR EACH ROW EXECUTE FUNCTION truss.runtime_immutable_layout_migration_receipt(); ALTER TABLE truss.layout_migration_receipt ENABLE ALWAYS TRIGGER runtime_layout_migration_receipt_immutable; CREATE TRIGGER runtime_layout_migration_receipt_no_truncate BEFORE TRUNCATE ON truss.layout_migration_receipt EXECUTE FUNCTION truss.runtime_immutable_layout_migration_receipt(); ALTER TABLE truss.layout_migration_receipt ENABLE ALWAYS TRIGGER runtime_layout_migration_receipt_no_truncate