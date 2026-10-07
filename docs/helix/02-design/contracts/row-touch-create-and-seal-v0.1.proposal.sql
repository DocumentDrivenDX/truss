-- Unadopted private first-touch/seal runtime effects, not authority bodies.
-- First parameters: complete tuple then four original custody byte carriers.
-- Seal parameters: complete tuple, expected dirty generation, four carriers.
-- No upsert, caller seal flag, inferred owner or ordinary-role writer grant.
-- First touch only after protected complete absence/tuple/custody reservation.
INSERT INTO truss.row_home_touch AS t (
  transaction_id, owner_kind, owner_id, owner_discriminator_id,
  property_owner_type_id, property_id, dirty_generation, sealed_generation,
  original_layout_bytes, original_home_bytes, original_owner_property_bytes,
  original_operation_bytes
)
SELECT pg_catalog.pg_current_xact_id_if_assigned(),
  $1::pg_catalog.text, $2::pg_catalog.int8, $3::pg_catalog.int4,
  $4::pg_catalog.int4, $5::pg_catalog.int4, 1, NULL,
  $6::pg_catalog.bytea, $7::pg_catalog.bytea, $8::pg_catalog.bytea,
  $9::pg_catalog.bytea
WHERE pg_catalog.pg_current_xact_id_if_assigned() IS NOT NULL
  AND $6::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($6::pg_catalog.bytea) > 0
  AND $7::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($7::pg_catalog.bytea) > 0
  AND $8::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($8::pg_catalog.bytea) > 0
  AND $9::pg_catalog.bytea IS NOT NULL AND pg_catalog.octet_length($9::pg_catalog.bytea) > 0
RETURNING
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
  pg_catalog.encode(t.original_operation_bytes, 'hex') AS original_operation_bytes_hex;
-- Seal only after complete RF scope and original operation effects readiness.
UPDATE truss.row_home_touch AS t
SET sealed_generation = t.dirty_generation
WHERE t.transaction_id = pg_catalog.pg_current_xact_id_if_assigned()
  AND t.owner_kind = $1::pg_catalog.text COLLATE pg_catalog."C"
  AND t.owner_id = $2::pg_catalog.int8
  AND t.owner_discriminator_id = $3::pg_catalog.int4
  AND t.property_owner_type_id = $4::pg_catalog.int4
  AND t.property_id = $5::pg_catalog.int4
  AND t.dirty_generation = $6::pg_catalog.int8
  AND t.dirty_generation > 0
  AND t.original_layout_bytes = $7::pg_catalog.bytea
  AND t.original_home_bytes = $8::pg_catalog.bytea
  AND t.original_owner_property_bytes = $9::pg_catalog.bytea
  AND t.original_operation_bytes = $10::pg_catalog.bytea
RETURNING
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
  pg_catalog.encode(t.original_operation_bytes, 'hex') AS original_operation_bytes_hex;
-- Exact one-row native completion and complete returned snapshot required.
