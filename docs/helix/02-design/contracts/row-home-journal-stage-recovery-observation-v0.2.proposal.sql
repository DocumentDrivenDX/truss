-- Unadopted private original-operation recovery observation.
-- $1 original native xid8; $2 original operation ordinal; $3 original context bytes.
-- Only existing qualified original recovery/administrative custody may dispatch.
-- Caller-supplied IDs/context/hash do not authorize arbitrary historical lookup.
-- Complete visibility/retention/owner/source/profile/resource/transaction proof required.
-- Zero rows is unknown/unavailable, never an automatic rollback/not-applied proof.
SELECT s.original_writer_xid::pg_catalog.text AS original_writer_xid,
       s.operation_ordinal::pg_catalog.text AS operation_ordinal,
       s.stage_name::pg_catalog.text AS stage_name,
       s.stage_ordinal::pg_catalog.text AS stage_ordinal,
       s.effect_generation::pg_catalog.text AS effect_generation,
       pg_catalog.encode(s.body_bytes, 'hex') AS body_bytes_hex
FROM truss.row_home_journal_stage AS s
JOIN truss.row_home_operation AS o
  ON o.original_writer_xid = s.original_writer_xid
 AND o.operation_ordinal = s.operation_ordinal
WHERE o.original_writer_xid = $1::pg_catalog.xid8
  AND o.operation_ordinal = $2::pg_catalog.int8
  AND o.original_context_bytes = $3::pg_catalog.bytea
ORDER BY CASE s.stage_name
  WHEN 'start' THEN 0
  WHEN 'transition' THEN 1
  WHEN 'final' THEN 2
  WHEN 'reserved' THEN 3
  WHEN 'publication' THEN 4
  ELSE 5 END,
  s.stage_ordinal;
