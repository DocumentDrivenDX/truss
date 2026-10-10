-- Unadopted protected subsequent property-touch generation advance.
-- Original observer parameters only, after complete OC/event/tuple admission:
-- $1 kind, $2 owner id, $3 discriminator, $4 property owner type, $5 property id;
-- $6 expected dirty generation; $7 layout bytes; $8 home bytes;
-- $9 owner/property bytes; $10 complete prior contribution bytes;
-- $11 complete independently verified next contribution bytes.
UPDATE truss.row_home_touch AS t
SET dirty_generation = t.dirty_generation + 1,
    sealed_generation = NULL,
    original_operation_bytes = $11::pg_catalog.bytea
WHERE t.transaction_id = pg_catalog.pg_current_xact_id_if_assigned()
  AND t.owner_kind = $1::pg_catalog.text COLLATE pg_catalog."C"
  AND t.owner_id = $2::pg_catalog.int8
  AND t.owner_discriminator_id = $3::pg_catalog.int4
  AND t.property_owner_type_id = $4::pg_catalog.int4
  AND t.property_id = $5::pg_catalog.int4
  AND t.dirty_generation = $6::pg_catalog.int8
  AND t.dirty_generation > 0
  AND t.dirty_generation < 9223372036854775807
  AND t.original_layout_bytes = $7::pg_catalog.bytea
  AND t.original_home_bytes = $8::pg_catalog.bytea
  AND t.original_owner_property_bytes = $9::pg_catalog.bytea
  AND t.original_operation_bytes = $10::pg_catalog.bytea
  AND $11::pg_catalog.bytea IS NOT NULL
  AND pg_catalog.octet_length($11::pg_catalog.bytea) > 0
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
-- New contribution bytes preserve all prior originals and admitted current event.
-- Equality/nonnull alone cannot prove complete contribution grammar or authority.
-- Exactly one returned full row; all tuples and operation reset share containment.
-- No upsert, partial tuple success, ordinary-role grant or direct seal authority.
