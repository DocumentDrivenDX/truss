-- CONTRACT-001/009 candidate, PostgreSQL 17; unapplied, unqualified fragment.
-- Original singleton schema_head is the lock home. This row is observation state,
-- not an independent lock whose acquisition can replace the schema_head guard.
CREATE TABLE truss.installation_admission (
  head_id int PRIMARY KEY CHECK (head_id = 1)
    REFERENCES truss.schema_head (id) ON DELETE RESTRICT,
  installation_id_utf8 bytea NOT NULL CHECK (octet_length(installation_id_utf8) > 0),
  source_epoch_utf8 bytea NOT NULL CHECK (octet_length(source_epoch_utf8) > 0),
  configuration_generation bigint NOT NULL CHECK (configuration_generation >= 0),
  key_reuse text NOT NULL CHECK (key_reuse IN ('forbid', 'allow')),
  journal_mode text NOT NULL CHECK (journal_mode IN ('engine', 'trigger')),
  configuration_bytes bytea NOT NULL CHECK (octet_length(configuration_bytes) > 0),
  selected_binding_bytes bytea NOT NULL CHECK (octet_length(selected_binding_bytes) > 0),
  installed_inventory_bytes bytea NOT NULL CHECK (octet_length(installed_inventory_bytes) > 0),
  configuration_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(configuration_bytes)) STORED,
  selected_binding_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(selected_binding_bytes)) STORED,
  installed_inventory_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(installed_inventory_bytes)) STORED
);
-- No implicit bootstrap INSERT: initialization requires independently admitted
-- original installation/epoch/configuration/binding/inventory artifacts.
-- Protected procedure privileges, archive/receipt stores, fixed resource limits,
-- unavoidable scalar-to-artifact parity and update/finalizer guards remain open.
