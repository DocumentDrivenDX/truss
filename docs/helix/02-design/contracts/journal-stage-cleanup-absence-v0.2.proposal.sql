-- Unadopted independent child absence observation for admitted cleanup only.
-- $1 original producing xid; $2 original operation ordinal. Exact retained
-- context/cohort/authority/exclusion/resource proof is admitted natively first.
-- Intentionally no parent JOIN: a missing parent must not hide surviving children.
-- No LIMIT/count-only/phase/body filter. Zero rows alone is not complete visibility.
SELECT s.original_writer_xid::pg_catalog.text AS original_writer_xid,
 s.operation_ordinal::pg_catalog.text AS operation_ordinal,
 s.stage_name AS stage_name,
 s.stage_ordinal::pg_catalog.text AS stage_ordinal,
 s.effect_generation::pg_catalog.text AS effect_generation,
 pg_catalog.encode(s.body_bytes, 'hex') AS body_bytes_hex
FROM truss.row_home_journal_stage AS s
WHERE s.original_writer_xid = $1::pg_catalog.xid8
 AND s.operation_ordinal = $2::pg_catalog.int8;
