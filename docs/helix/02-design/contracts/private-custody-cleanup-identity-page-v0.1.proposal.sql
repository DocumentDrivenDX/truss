-- Unadopted bounded private identity discovery for one original producing xid.
-- Query 1/2: operation first/continuation; Query 3/4: touch first/continuation.
-- 513 is 512 selected identities plus explicitly charged lookahead only.
-- No original byte carriers, phase filter or settlement/authority assertion.
SELECT
  o.original_writer_xid::pg_catalog.text AS original_writer_xid,
  o.operation_ordinal::pg_catalog.text AS operation_ordinal
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = $1::pg_catalog.text::pg_catalog.xid8
ORDER BY o.operation_ordinal
LIMIT 513;
SELECT
  o.original_writer_xid::pg_catalog.text AS original_writer_xid,
  o.operation_ordinal::pg_catalog.text AS operation_ordinal
FROM truss.row_home_operation AS o
WHERE o.original_writer_xid = $1::pg_catalog.text::pg_catalog.xid8
  AND o.operation_ordinal > $2::pg_catalog.text::pg_catalog.int8
ORDER BY o.operation_ordinal
LIMIT 513;
SELECT
  t.transaction_id::pg_catalog.text AS original_writer_xid,
  t.owner_kind::pg_catalog.text AS owner_kind,
  t.owner_id::pg_catalog.text AS owner_id,
  t.owner_discriminator_id::pg_catalog.text AS owner_discriminator_id,
  t.property_owner_type_id::pg_catalog.text AS property_owner_type_id,
  t.property_id::pg_catalog.text AS property_id
FROM truss.row_home_touch AS t
WHERE t.transaction_id = $1::pg_catalog.text::pg_catalog.xid8
ORDER BY t.owner_kind COLLATE pg_catalog."C", t.owner_id, t.owner_discriminator_id, t.property_owner_type_id, t.property_id
LIMIT 513;
SELECT
  t.transaction_id::pg_catalog.text AS original_writer_xid,
  t.owner_kind::pg_catalog.text AS owner_kind,
  t.owner_id::pg_catalog.text AS owner_id,
  t.owner_discriminator_id::pg_catalog.text AS owner_discriminator_id,
  t.property_owner_type_id::pg_catalog.text AS property_owner_type_id,
  t.property_id::pg_catalog.text AS property_id
FROM truss.row_home_touch AS t
WHERE t.transaction_id = $1::pg_catalog.text::pg_catalog.xid8
  AND ROW(t.owner_kind COLLATE pg_catalog."C", t.owner_id, t.owner_discriminator_id, t.property_owner_type_id, t.property_id) > ROW($2::pg_catalog.text COLLATE pg_catalog."C", $3::pg_catalog.text::pg_catalog.int8, $4::pg_catalog.text::pg_catalog.int4, $5::pg_catalog.text::pg_catalog.int4, $6::pg_catalog.text::pg_catalog.int4)
ORDER BY t.owner_kind COLLATE pg_catalog."C", t.owner_id, t.owner_discriminator_id, t.property_owner_type_id, t.property_id
LIMIT 513;
-- First-page queries require no invented minimum cursor.
-- Exact cursor/cut/identity/resource admission precedes parameter binding.
