-- Unadopted private source; original native finalizer owns all parameters.
-- Slots 1/2 context, 3 captured generation, 4 original private address,
-- 5 independently computed delivery ordinal. Same original exclusion/savepoint.
UPDATE truss.feed_member AS m
SET delivery_ordinal = $5::pg_catalog.int8
WHERE m.source_epoch = $1::pg_catalog.text
  AND m.feed_profile = $2::pg_catalog.text
  AND m.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND m.registration_address = $4::pg_catalog.int8
  AND m.delivery_ordinal IS NULL
  AND $4::pg_catalog.int8 > 0
  AND $5::pg_catalog.int8 >= 0
  AND EXISTS (
    SELECT 1 FROM truss.feed_tx AS t
    WHERE t.source_epoch = m.source_epoch
      AND t.feed_profile = m.feed_profile
      AND t.original_writer_xid = m.original_writer_xid
      AND t.membership_generation = $3::pg_catalog.int8
      AND t.finalized_generation IS NULL
      AND t.manifest_bytes IS NULL
      AND t.manifest_sha256 IS NULL
  )
RETURNING m.source_epoch, m.feed_profile,
  m.original_writer_xid::pg_catalog.text AS original_writer_xid,
  m.registration_address::pg_catalog.text AS registration_address,
  m.delivery_ordinal::pg_catalog.text AS delivery_ordinal;

-- Publication ONLY after complete independent original order/prerequisite/byte
-- correspondence and actual generation verification. SQL does not produce proof.
-- Slots 1/2 context, 3 captured generation, 4 exact canonical preimage tree bytes,
-- 5 exact 32-byte domain-framed semantic digest (not direct artifact byte hash).
UPDATE truss.feed_tx AS t
SET finalized_generation = $3::pg_catalog.int8,
    manifest_bytes = $4::pg_catalog.bytea,
    manifest_sha256 = $5::pg_catalog.bytea
WHERE t.source_epoch = $1::pg_catalog.text
  AND t.feed_profile = $2::pg_catalog.text
  AND t.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND t.membership_generation = $3::pg_catalog.int8
  AND $3::pg_catalog.int8 > 0
  AND t.finalized_generation IS NULL
  AND t.manifest_bytes IS NULL
  AND t.manifest_sha256 IS NULL
RETURNING t.source_epoch, t.feed_profile,
  t.original_writer_xid::pg_catalog.text AS original_writer_xid,
  t.membership_generation::pg_catalog.text AS membership_generation,
  t.finalized_generation::pg_catalog.text AS finalized_generation,
  pg_catalog.encode(t.manifest_bytes, 'hex') AS manifest_bytes_hex,
  pg_catalog.encode(t.manifest_sha256, 'hex') AS manifest_sha256_hex;
