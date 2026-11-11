-- Worker role grants for the candidate control functions. The role "bulk-worker" (owner decision
-- 2026-11-10) is created by the installer or test harness, never here. It receives EXECUTE on the worker
-- surface only: no table privileges, no seal/submit, no cancel/control surface, no private helpers.
GRANT USAGE ON SCHEMA truss_bulk TO "bulk-worker";
GRANT EXECUTE ON FUNCTION truss_bulk.worker_event(text, text, jsonb, bytea) TO "bulk-worker";
