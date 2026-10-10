-- Private immutable capsule component. Complete protected cleanup is unavailable.
CREATE FUNCTION truss.runtime_immutable_operation_configuration() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_RELID<>'truss.operation_configuration'::regclass OR TG_NARGS<>0
  OR TG_WHEN<>'BEFORE' OR NOT ((TG_LEVEL='ROW' AND TG_OP IN ('UPDATE','DELETE'))
   OR (TG_LEVEL='STATEMENT' AND TG_OP='TRUNCATE')) THEN
  RAISE EXCEPTION 'unregistered configuration capsule event' USING ERRCODE='55000';
 END IF;
 RAISE EXCEPTION 'original configuration capsule is immutable; cleanup unavailable' USING ERRCODE='55000';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_immutable_operation_configuration() FROM PUBLIC;
CREATE TRIGGER runtime_operation_configuration_immutable BEFORE UPDATE OR DELETE
 ON truss.operation_configuration FOR EACH ROW EXECUTE FUNCTION truss.runtime_immutable_operation_configuration();
ALTER TABLE truss.operation_configuration ENABLE ALWAYS TRIGGER runtime_operation_configuration_immutable;
CREATE TRIGGER runtime_operation_configuration_no_truncate BEFORE TRUNCATE
 ON truss.operation_configuration FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_immutable_operation_configuration();
ALTER TABLE truss.operation_configuration ENABLE ALWAYS TRIGGER runtime_operation_configuration_no_truncate;
