-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Optional PostgreSQL18.6 ALTER ROUTINE participation extension.
-- Reuses the independently qualified routine writer function; no full closure.
CREATE EVENT TRIGGER truss_z_routine_ddl_writer_barrier ON ddl_command_start
 WHEN TAG IN ('ALTER ROUTINE')
 EXECUTE FUNCTION truss.runtime_fence_routine_ddl_writer();
ALTER EVENT TRIGGER truss_z_routine_ddl_writer_barrier ENABLE ALWAYS;
