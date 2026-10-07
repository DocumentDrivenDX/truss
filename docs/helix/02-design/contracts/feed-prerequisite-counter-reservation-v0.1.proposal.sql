-- Two separate protected prerequisite registration candidates; no member allocation.
-- Statement-local slots 1/2 epoch/profile, 3 captured family counter,
-- 4 captured membership generation, 5/6 original context/manifest profile bytea.
-- Complete duplicate/authority/resource admission and original containment first.
-- Exact repeats skip mutation; new prerequisite insert shares its reservation.
-- catalog prerequisite: slot 3 is this family's original counter.
UPDATE truss.feed_tx AS t
SET prerequisite_registration_counter = t.prerequisite_registration_counter + 1,
    membership_generation = t.membership_generation + 1
WHERE t.source_epoch = $1::pg_catalog.text
  AND t.feed_profile = $2::pg_catalog.text
  AND t.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND t.prerequisite_registration_counter = $3::pg_catalog.int8
  AND t.membership_generation = $4::pg_catalog.int8
  AND t.original_context_bytes = $5::pg_catalog.bytea
  AND t.manifest_profile_bytes = $6::pg_catalog.bytea
  AND t.prerequisite_registration_counter < 9223372036854775807::pg_catalog.int8
  AND t.membership_generation < 9223372036854775807::pg_catalog.int8
RETURNING t.source_epoch, t.feed_profile,
  t.original_writer_xid::pg_catalog.text AS original_writer_xid,
  t.registration_counter::pg_catalog.text AS registration_counter,
  t.prerequisite_registration_counter::pg_catalog.text AS prerequisite_registration_counter,
  t.configuration_registration_counter::pg_catalog.text AS configuration_registration_counter,
  t.membership_generation::pg_catalog.text AS membership_generation,
  t.finalized_generation::pg_catalog.text AS finalized_generation,
  pg_catalog.encode(t.original_context_bytes, 'hex') AS original_context_bytes_hex,
  pg_catalog.encode(t.manifest_profile_bytes, 'hex') AS manifest_profile_bytes_hex,
  pg_catalog.encode(t.manifest_bytes, 'hex') AS manifest_bytes_hex,
  pg_catalog.encode(t.manifest_sha256, 'hex') AS manifest_sha256_hex;

-- configuration prerequisite: slot 3 is this family's original counter.
UPDATE truss.feed_tx AS t
SET configuration_registration_counter = t.configuration_registration_counter + 1,
    membership_generation = t.membership_generation + 1
WHERE t.source_epoch = $1::pg_catalog.text
  AND t.feed_profile = $2::pg_catalog.text
  AND t.original_writer_xid = pg_catalog.pg_current_xact_id_if_assigned()
  AND t.configuration_registration_counter = $3::pg_catalog.int8
  AND t.membership_generation = $4::pg_catalog.int8
  AND t.original_context_bytes = $5::pg_catalog.bytea
  AND t.manifest_profile_bytes = $6::pg_catalog.bytea
  AND t.configuration_registration_counter < 9223372036854775807::pg_catalog.int8
  AND t.membership_generation < 9223372036854775807::pg_catalog.int8
RETURNING t.source_epoch, t.feed_profile,
  t.original_writer_xid::pg_catalog.text AS original_writer_xid,
  t.registration_counter::pg_catalog.text AS registration_counter,
  t.prerequisite_registration_counter::pg_catalog.text AS prerequisite_registration_counter,
  t.configuration_registration_counter::pg_catalog.text AS configuration_registration_counter,
  t.membership_generation::pg_catalog.text AS membership_generation,
  t.finalized_generation::pg_catalog.text AS finalized_generation,
  pg_catalog.encode(t.original_context_bytes, 'hex') AS original_context_bytes_hex,
  pg_catalog.encode(t.manifest_profile_bytes, 'hex') AS manifest_profile_bytes_hex,
  pg_catalog.encode(t.manifest_bytes, 'hex') AS manifest_bytes_hex,
  pg_catalog.encode(t.manifest_sha256, 'hex') AS manifest_sha256_hex;
