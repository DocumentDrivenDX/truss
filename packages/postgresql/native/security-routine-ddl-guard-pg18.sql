-- Private PostgreSQL18.6 routine-DDL generation spike, not a production installer.
-- Original installation owner must own this function. A native superuser installs
-- both event triggers. Selected CREATE/ALTER/DROP FUNCTION commands only; not all
-- routine/procedure/extension/role/source routes. Administrators can disable/drop
-- hooks and remain excluded. Do not compose with the existing exactly-one manual
-- authority CAS: each selected DDL already advances the generation.
CREATE FUNCTION truss.security_routine_ddl_guard() RETURNS event_trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE observed_generation bigint; observed_source_generation bigint;
        advanced_generation bigint; advanced_source_generation bigint;
BEGIN
 IF TG_EVENT NOT IN ('ddl_command_start','ddl_command_end')
    OR TG_TAG NOT IN ('CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION')
    OR pg_catalog.current_setting('server_version_num') OPERATOR(pg_catalog.<>) '180006'
    OR pg_catalog.current_setting('transaction_isolation') OPERATOR(pg_catalog.<>) 'read committed'
    OR pg_catalog.current_setting('transaction_read_only') OPERATOR(pg_catalog.<>) 'off'
 THEN RAISE EXCEPTION 'Unsupported routine DDL guard scope' USING ERRCODE='42501'; END IF;
 PERFORM rev FROM truss.schema_head WHERE id OPERATOR(pg_catalog.=) 1 FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Original routine DDL head missing' USING ERRCODE='42501'; END IF;
 SELECT generation,routine_source_generation INTO observed_generation,observed_source_generation
 FROM truss.policy_generation_guard WHERE singleton OPERATOR(pg_catalog.=) 1 FOR UPDATE;
 IF NOT FOUND OR observed_generation OPERATOR(pg_catalog.>=) 9223372036854775807
    OR observed_source_generation OPERATOR(pg_catalog.<) 0
    OR observed_source_generation OPERATOR(pg_catalog.>=) 9223372036854775807
 THEN RAISE EXCEPTION 'Original routine DDL generation refused' USING ERRCODE='42501'; END IF;
 -- Separate fresh VOLATILE SPI statement after the original guard wait.
 IF EXISTS(SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled)
 THEN RAISE EXCEPTION 'Outstanding publication blocks routine DDL' USING ERRCODE='42501'; END IF;
 IF TG_EVENT OPERATOR(pg_catalog.=) 'ddl_command_end' THEN
  UPDATE truss.policy_generation_guard SET generation=generation OPERATOR(pg_catalog.+) 1,
   routine_source_generation=routine_source_generation OPERATOR(pg_catalog.+) 1
  WHERE singleton OPERATOR(pg_catalog.=) 1 AND generation OPERATOR(pg_catalog.=) observed_generation
   AND routine_source_generation OPERATOR(pg_catalog.=) observed_source_generation
  RETURNING generation,routine_source_generation INTO advanced_generation,advanced_source_generation;
  IF NOT FOUND OR advanced_generation IS DISTINCT FROM observed_generation OPERATOR(pg_catalog.+) 1
     OR advanced_source_generation IS DISTINCT FROM observed_source_generation OPERATOR(pg_catalog.+) 1
  THEN RAISE EXCEPTION 'Original routine DDL advance refused' USING ERRCODE='42501'; END IF;
 END IF;
 RETURN;
END $$;
REVOKE ALL ON FUNCTION truss.security_routine_ddl_guard() FROM PUBLIC;
CREATE EVENT TRIGGER truss_security_routine_ddl_start ON ddl_command_start
 WHEN TAG IN ('CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION')
 EXECUTE FUNCTION truss.security_routine_ddl_guard();
CREATE EVENT TRIGGER truss_security_routine_ddl_end ON ddl_command_end
 WHEN TAG IN ('CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION')
 EXECUTE FUNCTION truss.security_routine_ddl_guard();

ALTER EVENT TRIGGER truss_security_routine_ddl_start ENABLE ALWAYS;
ALTER EVENT TRIGGER truss_security_routine_ddl_end ENABLE ALWAYS;
