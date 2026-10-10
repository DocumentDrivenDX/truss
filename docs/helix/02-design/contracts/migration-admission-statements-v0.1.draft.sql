-- Separate unapplied PostgreSQL 17 candidate statement templates.
-- Require original schema_head exclusion, actual role/profile and byte/resource
-- admission. These are not a complete protected native procedure.

-- admission_metadata: separate fresh observation after head acquisition.
-- Singleton row absent means unavailable; lengths admit original artifact fetch.
SELECT configuration_generation::text, key_reuse, journal_mode,
       octet_length(installation_id_utf8)::text AS installation_bytes,
       octet_length(source_epoch_utf8)::text AS epoch_bytes,
       octet_length(configuration_bytes)::text AS configuration_bytes,
       octet_length(selected_binding_bytes)::text AS binding_bytes,
       octet_length(installed_inventory_bytes)::text AS inventory_bytes
FROM truss.installation_admission WHERE head_id = 1;

-- admission_original: fetch only after complete metadata/output budget admission.
SELECT installation_id_utf8, source_epoch_utf8, configuration_generation::text,
       key_reuse, journal_mode, configuration_bytes, selected_binding_bytes,
       installed_inventory_bytes
FROM truss.installation_admission WHERE head_id = 1;

-- admission_switch: original exclusion remains held; all target/native policy/
-- archive/receipt/feed obligations must have their same-transaction procedure.
-- $1 original installation UTF-8; $2 original epoch UTF-8; $3 original generation;
-- $4/$5/$6 exact original configuration/binding/inventory bytes;
-- $7/$8/$9 independently admitted target configuration/binding/inventory bytes;
-- $10/$11 original reuse/journal scalars. No identity/policy change is permitted.
UPDATE truss.installation_admission
SET configuration_generation = configuration_generation + 1,
    configuration_bytes = $7::bytea,
    selected_binding_bytes = $8::bytea,
    installed_inventory_bytes = $9::bytea
WHERE head_id = 1
  AND installation_id_utf8 = $1::bytea AND source_epoch_utf8 = $2::bytea
  AND configuration_generation = $3::bigint
  AND configuration_generation < 9223372036854775807
  AND configuration_bytes = $4::bytea AND selected_binding_bytes = $5::bytea
  AND installed_inventory_bytes = $6::bytea
  AND key_reuse = $10::text AND journal_mode = $11::text
RETURNING configuration_generation::text, configuration_sha256,
          selected_binding_sha256, installed_inventory_sha256;
-- Exactly one pending changed row required. No row is changed/integrity refusal
-- or overflow, not success. RETURNING is not a commit/complete-feed observation.
