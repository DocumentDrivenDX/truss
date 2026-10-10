-- Unadopted five-phase DML source for the explicit-start-slot child-store branch.
-- Not granted directly to ordinary roles; protected native bodies first validate
-- full context/caller/mode/profile/generation/semantic/resource obligations.
-- $1 original operation ordinal; $2 actual stage generation; $3 original context.
-- Nontransition $4 complete body bytes; transition $4 ordinal and $5 body bytes.
-- SQL presence/prefix/nonempty predicates are coarse phase shape, not authority.
-- No UPSERT, body replacement, phase setter or automatic uncertain replay.

-- start: original native phase proof must precede this statement.
INSERT INTO truss.row_home_journal_stage
 (original_writer_xid, operation_ordinal, stage_name, stage_ordinal, effect_generation, body_bytes)
SELECT o.original_writer_xid, o.operation_ordinal, 'start', 0, o.effect_generation, $4::pg_catalog.bytea
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.phase = 'admitted' AND o.effect_generation >= 0
  AND o.readiness_generation IS NULL AND o.sealed_generation IS NULL
  AND o.application_generation IS NULL AND o.application_result_bytes IS NULL
  AND $4::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($4::pg_catalog.bytea) > 0
  AND NOT EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal)
RETURNING original_writer_xid::pg_catalog.text AS original_writer_xid,
 operation_ordinal::pg_catalog.text AS operation_ordinal,
 stage_name::pg_catalog.text AS stage_name,
 stage_ordinal::pg_catalog.text AS stage_ordinal,
 effect_generation::pg_catalog.text AS effect_generation,
 pg_catalog.encode(body_bytes, 'hex') AS body_bytes_hex;

-- transition: original native phase proof must precede this statement.
INSERT INTO truss.row_home_journal_stage
 (original_writer_xid, operation_ordinal, stage_name, stage_ordinal, effect_generation, body_bytes)
SELECT o.original_writer_xid, o.operation_ordinal, 'transition', $4::pg_catalog.int8, o.effect_generation, $5::pg_catalog.bytea
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.phase = 'admitted' AND o.effect_generation >= 0
  AND o.readiness_generation IS NULL AND o.sealed_generation IS NULL
  AND o.application_generation IS NULL AND o.application_result_bytes IS NULL
  AND $5::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($5::pg_catalog.bytea) > 0
  AND EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name = 'start' AND s.stage_ordinal = 0)
  AND NOT EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name IN ('final', 'reserved', 'publication'))
  AND $4::pg_catalog.int8 >= 0
  AND NOT EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name = 'transition' AND s.stage_ordinal >= $4::pg_catalog.int8)
  AND ($4::pg_catalog.int8 = 0 OR EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name = 'transition' AND s.stage_ordinal = $4::pg_catalog.int8 - 1))
RETURNING original_writer_xid::pg_catalog.text AS original_writer_xid,
 operation_ordinal::pg_catalog.text AS operation_ordinal,
 stage_name::pg_catalog.text AS stage_name,
 stage_ordinal::pg_catalog.text AS stage_ordinal,
 effect_generation::pg_catalog.text AS effect_generation,
 pg_catalog.encode(body_bytes, 'hex') AS body_bytes_hex;

-- final: original native phase proof must precede this statement.
INSERT INTO truss.row_home_journal_stage
 (original_writer_xid, operation_ordinal, stage_name, stage_ordinal, effect_generation, body_bytes)
SELECT o.original_writer_xid, o.operation_ordinal, 'final', 0, o.effect_generation, $4::pg_catalog.bytea
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.phase = 'admitted' AND o.effect_generation >= 0
  AND o.readiness_generation IS NULL AND o.sealed_generation IS NULL
  AND o.application_generation IS NULL AND o.application_result_bytes IS NULL
  AND $4::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($4::pg_catalog.bytea) > 0
  AND EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name = 'start' AND s.stage_ordinal = 0)
  AND NOT EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name IN ('final', 'reserved', 'publication'))
RETURNING original_writer_xid::pg_catalog.text AS original_writer_xid,
 operation_ordinal::pg_catalog.text AS operation_ordinal,
 stage_name::pg_catalog.text AS stage_name,
 stage_ordinal::pg_catalog.text AS stage_ordinal,
 effect_generation::pg_catalog.text AS effect_generation,
 pg_catalog.encode(body_bytes, 'hex') AS body_bytes_hex;

-- reserved: original native phase proof must precede this statement.
INSERT INTO truss.row_home_journal_stage
 (original_writer_xid, operation_ordinal, stage_name, stage_ordinal, effect_generation, body_bytes)
SELECT o.original_writer_xid, o.operation_ordinal, 'reserved', 0, o.effect_generation, $4::pg_catalog.bytea
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.phase = 'admitted' AND o.effect_generation >= 0
  AND o.readiness_generation IS NULL AND o.sealed_generation IS NULL
  AND o.application_generation IS NULL AND o.application_result_bytes IS NULL
  AND $4::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($4::pg_catalog.bytea) > 0
  AND EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name = 'final' AND s.stage_ordinal = 0)
  AND NOT EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name IN ('reserved', 'publication'))
RETURNING original_writer_xid::pg_catalog.text AS original_writer_xid,
 operation_ordinal::pg_catalog.text AS operation_ordinal,
 stage_name::pg_catalog.text AS stage_name,
 stage_ordinal::pg_catalog.text AS stage_ordinal,
 effect_generation::pg_catalog.text AS effect_generation,
 pg_catalog.encode(body_bytes, 'hex') AS body_bytes_hex;

-- publication: original native phase proof must precede this statement.
INSERT INTO truss.row_home_journal_stage
 (original_writer_xid, operation_ordinal, stage_name, stage_ordinal, effect_generation, body_bytes)
SELECT o.original_writer_xid, o.operation_ordinal, 'publication', 0, o.effect_generation, $4::pg_catalog.bytea
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND o.operation_ordinal = $1::pg_catalog.int8
  AND o.effect_generation = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
  AND o.phase = 'admitted' AND o.effect_generation >= 0
  AND o.readiness_generation IS NULL AND o.sealed_generation IS NULL
  AND o.application_generation IS NULL AND o.application_result_bytes IS NULL
  AND $4::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($4::pg_catalog.bytea) > 0
  AND EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name = 'final' AND s.stage_ordinal = 0)
  AND EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name = 'reserved' AND s.stage_ordinal = 0)
  AND NOT EXISTS (SELECT 1 FROM truss.row_home_journal_stage AS s WHERE s.original_writer_xid = o.original_writer_xid AND s.operation_ordinal = o.operation_ordinal AND s.stage_name IN ('publication'))
RETURNING original_writer_xid::pg_catalog.text AS original_writer_xid,
 operation_ordinal::pg_catalog.text AS operation_ordinal,
 stage_name::pg_catalog.text AS stage_name,
 stage_ordinal::pg_catalog.text AS stage_ordinal,
 effect_generation::pg_catalog.text AS effect_generation,
 pg_catalog.encode(body_bytes, 'hex') AS body_bytes_hex;
