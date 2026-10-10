-- Unadopted OC04 private contributing-event generation reset effect.
-- Parameters come only from the original OC02-OC04 protected resolver:
-- $1 operation ordinal; $2 expected current generation; $3 original context bytea.
-- Original event/scope/resource/native authority proof precedes invocation.
UPDATE truss.row_home_operation AS o
SET effect_generation = o.effect_generation + 1,
    phase = 'admitted',
    readiness_generation = NULL,
    sealed_generation = NULL,
    application_generation = NULL,
    application_result_bytes = NULL
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.phase IN ('admitted', 'effects_ready', 'row_sealed')
  AND o.effect_generation >= 0
  AND o.effect_generation < 9223372036854775807
RETURNING
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
  pg_catalog.encode(o.application_result_bytes, 'hex') AS application_result_bytes_hex;
-- Exactly one returned complete row and original field parity are required.
-- Zero rows is refusal, not no-op, success, automatic upsert or ordinal search.
-- Native guard timing/error/containment and complete touch/event updates remain
-- obligations of the protected enclosing body; no ordinary-role UPDATE grant.
