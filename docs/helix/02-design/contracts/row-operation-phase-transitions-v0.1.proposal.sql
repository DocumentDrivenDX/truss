-- Unadopted OC05 protected generation-scoped phase transition effects.
-- $1 original resolver ordinal; $2 verified effect generation; $3 context bytea.
-- $4 (finalization only) complete independently verified original result bytes.
-- These guards do not implement readiness, RF, non-row or result proof bodies.
-- readiness only after its complete original native proof.
UPDATE truss.row_home_operation AS o
SET phase = 'effects_ready', readiness_generation = o.effect_generation
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.effect_generation >= 0
  AND o.phase = 'admitted' AND o.readiness_generation IS NULL AND o.sealed_generation IS NULL AND o.application_generation IS NULL AND o.application_result_bytes IS NULL
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
-- row sealing only after its complete original native proof.
UPDATE truss.row_home_operation AS o
SET phase = 'row_sealed', sealed_generation = o.effect_generation
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.effect_generation >= 0
  AND o.phase = 'effects_ready' AND o.readiness_generation = o.effect_generation AND o.sealed_generation IS NULL AND o.application_generation IS NULL AND o.application_result_bytes IS NULL
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
-- application finalization only after its complete original native proof.
UPDATE truss.row_home_operation AS o
SET phase = 'application_finalized', application_generation = o.effect_generation, application_result_bytes = $4::pg_catalog.bytea
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.effect_generation >= 0
  AND o.phase = 'row_sealed' AND o.readiness_generation = o.effect_generation AND o.sealed_generation = o.effect_generation AND o.application_generation IS NULL AND o.application_result_bytes IS NULL AND $4::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($4::pg_catalog.bytea) > 0
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
-- Require exactly one complete returned row and exact original/update parity.
-- No stale proof reuse, skipped phase, automatic retry or ordinary UPDATE grant.
