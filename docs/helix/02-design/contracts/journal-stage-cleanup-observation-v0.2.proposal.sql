-- Unadopted whole-original-operation private stage cleanup source.
-- $1 original xid; $2 original operation ordinal; $3 immutable original context.
-- Protected native RT eligibility/settlement/authority/exclusion/resource and full
-- child/dependency/snapshot admission MUST precede dispatch. Not a public query.
-- No row phase/generation or current-xid shortcut establishes eligibility.
SELECT s.original_writer_xid::pg_catalog.text AS original_writer_xid,
 s.operation_ordinal::pg_catalog.text AS operation_ordinal,
 s.stage_name AS stage_name,
 s.stage_ordinal::pg_catalog.text AS stage_ordinal,
 s.effect_generation::pg_catalog.text AS effect_generation,
 pg_catalog.encode(s.body_bytes, 'hex') AS body_bytes_hex
FROM truss.row_home_journal_stage AS s
JOIN truss.row_home_operation AS o ON s.original_writer_xid = o.original_writer_xid
 AND s.operation_ordinal = o.operation_ordinal
 AND o.original_writer_xid = $1::pg_catalog.xid8
 AND o.operation_ordinal = $2::pg_catalog.int8
 AND o.original_context_bytes = $3::pg_catalog.bytea;
