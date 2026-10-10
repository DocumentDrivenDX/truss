-- Private component only: original archive custody; no insertion or retention authority.
CREATE FUNCTION truss.runtime_immutable_catalog_source() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF TG_RELID NOT IN ('truss.schema_rev'::regclass,'truss.schema_doc'::regclass)
   OR TG_NARGS<>0 OR TG_WHEN<>'BEFORE'
   OR NOT ((TG_LEVEL='ROW' AND TG_OP IN ('UPDATE','DELETE'))
     OR (TG_LEVEL='STATEMENT' AND TG_OP='TRUNCATE')) THEN
  RAISE EXCEPTION 'unregistered immutable catalog source event' USING ERRCODE='55000';
 END IF;
 RAISE EXCEPTION 'original catalog revision and document archives are immutable' USING ERRCODE='55000';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_immutable_catalog_source() FROM PUBLIC;
CREATE TRIGGER runtime_catalog_source_immutable BEFORE UPDATE OR DELETE
 ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.runtime_immutable_catalog_source();
ALTER TABLE truss.schema_rev ENABLE ALWAYS TRIGGER runtime_catalog_source_immutable;
CREATE TRIGGER runtime_catalog_source_no_truncate BEFORE TRUNCATE
 ON truss.schema_rev FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_immutable_catalog_source();
ALTER TABLE truss.schema_rev ENABLE ALWAYS TRIGGER runtime_catalog_source_no_truncate;
CREATE TRIGGER runtime_catalog_source_immutable BEFORE UPDATE OR DELETE
 ON truss.schema_doc FOR EACH ROW EXECUTE FUNCTION truss.runtime_immutable_catalog_source();
ALTER TABLE truss.schema_doc ENABLE ALWAYS TRIGGER runtime_catalog_source_immutable;
CREATE TRIGGER runtime_catalog_source_no_truncate BEFORE TRUNCATE
 ON truss.schema_doc FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_immutable_catalog_source();
ALTER TABLE truss.schema_doc ENABLE ALWAYS TRIGGER runtime_catalog_source_no_truncate;
