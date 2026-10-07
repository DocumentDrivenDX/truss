-- Private bootstrap-only source; original head/namespace/install exclusion,
-- artifact decoding and complete absence proof must precede submission.
INSERT INTO truss.installation_admission
 (head_id, installation_id_utf8, source_epoch_utf8, configuration_generation,
  key_reuse, journal_mode, configuration_bytes, selected_binding_bytes,
  installed_inventory_bytes)
VALUES (1, $1::bytea, $2::bytea, $3::bigint, $4::text, $5::text,
 $6::bytea, $7::bytea, $8::bytea)
RETURNING head_id::pg_catalog.text AS head_id,
 configuration_generation::pg_catalog.text AS configuration_generation,
 pg_catalog.encode(configuration_sha256,'hex') AS configuration_sha256,
 pg_catalog.encode(selected_binding_sha256,'hex') AS selected_binding_sha256,
 pg_catalog.encode(installed_inventory_sha256,'hex') AS installed_inventory_sha256;
-- No upsert/ON CONFLICT repair. Exactly one INSERT completion and returned row
-- are necessary, not proof of original configuration/artifact/native parity.
