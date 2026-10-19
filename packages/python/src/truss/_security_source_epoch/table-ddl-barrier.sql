-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Optional private PostgreSQL16.15 table-DDL participation adjunct.
-- Reuses the qualified six-tag routine writer boundary's original epoch/marker
-- lock ordering. This does not qualify event-trigger custody or whole source
-- closure. Selected CREATE/ALTER/DROP TABLE only; not grants/shared roles,
-- schemas, policies, trigger administration, extension or cascading closure.
CREATE EVENT TRIGGER truss_table_ddl_writer_barrier ON ddl_command_start
 WHEN TAG IN ('CREATE TABLE','ALTER TABLE','DROP TABLE')
 EXECUTE FUNCTION truss.runtime_fence_routine_ddl_writer();
ALTER EVENT TRIGGER truss_table_ddl_writer_barrier ENABLE ALWAYS;
