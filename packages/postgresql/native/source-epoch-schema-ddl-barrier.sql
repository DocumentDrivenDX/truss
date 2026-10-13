-- Optional PostgreSQL18.6 schema-DDL writer participation extension.
-- Fences selected CREATE/ALTER/DROP SCHEMA tags using original epoch/marker ordering.
-- Does not issue a new epoch or prove role/grant/event-trigger/admin lifetime.
CREATE EVENT TRIGGER truss_schema_ddl_writer_barrier ON ddl_command_start
 WHEN TAG IN ('CREATE SCHEMA','ALTER SCHEMA','DROP SCHEMA')
 EXECUTE FUNCTION truss.runtime_fence_routine_ddl_writer();
ALTER EVENT TRIGGER truss_schema_ddl_writer_barrier ENABLE ALWAYS;
