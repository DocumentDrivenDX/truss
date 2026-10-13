-- Private PostgreSQL18.6 unfiltered ddl_command_start participation adjunct.
-- Native event-supported commands only; no role/database/tablespace/parameter
-- privilege/ALTER SYSTEM/event-trigger administration coverage. No protection
-- against an excluded administrator disabling event_triggers or the handler.
-- Reuses the original invoker epoch/marker boundary; no automatic new epoch.
CREATE EVENT TRIGGER truss_database_ddl_writer_barrier ON ddl_command_start
 EXECUTE FUNCTION truss.runtime_fence_routine_ddl_writer();
ALTER EVENT TRIGGER truss_database_ddl_writer_barrier ENABLE ALWAYS;
