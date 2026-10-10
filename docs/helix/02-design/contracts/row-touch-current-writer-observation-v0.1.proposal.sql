-- Unadopted OC04/RF private current-writer touch lookup.
-- Five original resolver parameters: kind, owner id, discriminator,
-- property owner type and property id; no caller producing-xid parameter.
-- Actual assigned xid, original unique operation/context/liveness and complete
-- private visibility/cut proof must be admitted separately before zero-row absence.
SELECT
  t.transaction_id::pg_catalog.text AS transaction_id,
  t.owner_kind::pg_catalog.text AS owner_kind,
  t.owner_id::pg_catalog.text AS owner_id,
  t.owner_discriminator_id::pg_catalog.text AS owner_discriminator_id,
  t.property_owner_type_id::pg_catalog.text AS property_owner_type_id,
  t.property_id::pg_catalog.text AS property_id,
  t.dirty_generation::pg_catalog.text AS dirty_generation,
  t.sealed_generation::pg_catalog.text AS sealed_generation,
  pg_catalog.encode(t.original_layout_bytes, 'hex') AS original_layout_bytes_hex,
  pg_catalog.encode(t.original_home_bytes, 'hex') AS original_home_bytes_hex,
  pg_catalog.encode(t.original_owner_property_bytes, 'hex') AS original_owner_property_bytes_hex,
  pg_catalog.encode(t.original_operation_bytes, 'hex') AS original_operation_bytes_hex
FROM truss.row_home_touch AS t
WHERE t.transaction_id = pg_catalog.pg_current_xact_id_if_assigned()
  AND t.owner_kind = $1::pg_catalog.text COLLATE pg_catalog."C"
  AND t.owner_id = $2::pg_catalog.int8
  AND t.owner_discriminator_id = $3::pg_catalog.int4
  AND t.property_owner_type_id = $4::pg_catalog.int4
  AND t.property_id = $5::pg_catalog.int4;
-- No LIMIT1, phase/seal filter, native xid allocation or public disclosure.
