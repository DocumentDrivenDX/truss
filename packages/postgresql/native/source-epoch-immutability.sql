-- Private epoch registry guard. Issuance/current-pointer transitions and
-- installation/target-incarnation admission remain separate obligations.
CREATE FUNCTION truss.runtime_immutable_source_epoch() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_RELID<>'truss.source_epoch_registry'::regclass OR TG_NARGS<>0
  OR TG_WHEN<>'BEFORE' OR NOT (
   (TG_LEVEL='ROW' AND TG_OP IN ('UPDATE','DELETE'))
   OR (TG_LEVEL='STATEMENT' AND TG_OP='TRUNCATE')) THEN
  RAISE EXCEPTION 'unregistered immutable epoch event' USING ERRCODE='55000';
 END IF;
 RAISE EXCEPTION 'original source epoch registry evidence are immutable' USING ERRCODE='55000';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_immutable_source_epoch() FROM PUBLIC;
CREATE TRIGGER runtime_source_epoch_immutable BEFORE UPDATE OR DELETE
 ON truss.source_epoch_registry FOR EACH ROW EXECUTE FUNCTION truss.runtime_immutable_source_epoch();
ALTER TABLE truss.source_epoch_registry ENABLE ALWAYS TRIGGER runtime_source_epoch_immutable;
CREATE TRIGGER runtime_source_epoch_no_truncate BEFORE TRUNCATE
 ON truss.source_epoch_registry FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_immutable_source_epoch();
ALTER TABLE truss.source_epoch_registry ENABLE ALWAYS TRIGGER runtime_source_epoch_no_truncate;
