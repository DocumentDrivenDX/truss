-- Unadopted OC01-OC07 private observations; no ordinary role grant or execution.
-- Query 1 preserves no-assigned-xid as NULL; it must never assign a new xid.
SELECT pg_catalog.pg_current_xact_id_if_assigned()::pg_catalog.text AS original_writer_xid;
-- Query 2 retains all actual-transaction operations, including unknown phases.
-- No caller xid, phase filter, LIMIT, DISTINCT, latest ordinal or repair.
SELECT
  o.original_writer_xid::pg_catalog.text AS original_writer_xid,
  o.operation_ordinal::pg_catalog.text AS operation_ordinal,
  o.operation_kind::pg_catalog.text AS operation_kind,
  o.phase::pg_catalog.text AS phase,
  o.effect_generation::pg_catalog.text AS effect_generation,
  o.readiness_generation::pg_catalog.text AS readiness_generation,
  o.sealed_generation::pg_catalog.text AS sealed_generation,
  o.application_generation::pg_catalog.text AS application_generation,
  pg_catalog.encode(o.original_context_bytes, 'hex') AS original_context_bytes_hex,
  pg_catalog.encode(o.original_definition_bytes, 'hex') AS original_definition_bytes_hex,
  pg_catalog.encode(o.original_input_bytes, 'hex') AS original_input_bytes_hex,
  pg_catalog.encode(o.original_prestate_bytes, 'hex') AS original_prestate_bytes_hex,
  pg_catalog.encode(o.admitted_candidate_bytes, 'hex') AS admitted_candidate_bytes_hex,
  pg_catalog.encode(o.effect_obligation_bytes, 'hex') AS effect_obligation_bytes_hex,
  pg_catalog.encode(o.original_group_custody_bytes, 'hex') AS original_group_custody_bytes_hex,
  pg_catalog.encode(o.application_result_bytes, 'hex') AS application_result_bytes_hex
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned();
-- Both queries require the same original admitted connection/transaction/cut.
-- Decode every nullable generation/result separately; NULL is not empty bytes.
-- Source grammar/array order does not provide runtime authority or work bounds.
