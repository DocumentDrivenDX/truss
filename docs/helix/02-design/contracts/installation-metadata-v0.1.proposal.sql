-- CONTRACT-008 / TD-045 fresh-install metadata candidate; NOT an installer.
-- Ordinary writers receive no marker/archive DML or archive allocator authority.
-- Marker row data and archived observation bytes are outside their own immutable
-- inventory preimage; definitions/creation recipe remain inside it.
CREATE TABLE truss.installation_marker (
  singleton_id smallint PRIMARY KEY CHECK (singleton_id = 1),
  marker_interface_version text COLLATE pg_catalog."C" NOT NULL
    CHECK (marker_interface_version = 'truss-bootstrap-marker/0.1.0'),
  installation_id text COLLATE pg_catalog."C" NOT NULL UNIQUE,
  layout_version text COLLATE pg_catalog."C" NOT NULL,
  bundle_sha256 bytea NOT NULL CHECK (octet_length(bundle_sha256) = 32),
  inventory_profile text COLLATE pg_catalog."C" NOT NULL,
  inventory_sha256 bytea NOT NULL CHECK (octet_length(inventory_sha256) = 32),
  database_identity text COLLATE pg_catalog."C" NOT NULL,
  schema_name text COLLATE pg_catalog."C" NOT NULL,
  installed_at timestamptz NOT NULL,
  installed_at_text text COLLATE pg_catalog."C" NOT NULL,
  CONSTRAINT installation_marker_identity_bounds CHECK (
    char_length(installation_id) BETWEEN 1 AND 256 AND octet_length(installation_id) <= 1024
    AND char_length(layout_version) BETWEEN 1 AND 256
    AND char_length(inventory_profile) BETWEEN 1 AND 256
    AND char_length(database_identity) BETWEEN 1 AND 1024
    AND char_length(schema_name) BETWEEN 1 AND 256
    AND char_length(installed_at_text) BETWEEN 1 AND 128)
);
-- installed_at_text retains the actual original native clock observation; the
-- protected producer proves text/native precision/instant equality under the
-- selected clock profile. A caller clock or generic cast does not prove it.
CREATE SEQUENCE truss.installation_archive_row_seq AS bigint
  MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 NO CYCLE;
CREATE TABLE truss.installation_archive (
  archive_row_id bigint PRIMARY KEY DEFAULT nextval('truss.installation_archive_row_seq'),
  installation_id text COLLATE pg_catalog."C" NOT NULL,
  artifact_role text COLLATE pg_catalog."C" NOT NULL,
  artifact_identity text COLLATE pg_catalog."C" NOT NULL,
  artifact_bytes bytea NOT NULL,
  artifact_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(artifact_bytes)) STORED,
  artifact_identity_sha256 bytea GENERATED ALWAYS AS
    (pg_catalog.sha256(pg_catalog.convert_to(artifact_identity, 'UTF8'))) STORED,
  CONSTRAINT installation_archive_row_positive CHECK (archive_row_id > 0),
  CONSTRAINT installation_archive_role CHECK
    (artifact_role IN ('bundle','expected_inventory','installed_inventory','input','marker')),
  CONSTRAINT installation_archive_identity_bound CHECK
    (octet_length(artifact_identity) BETWEEN 1 AND 65536),
  CONSTRAINT installation_archive_bytes_bound CHECK
    (octet_length(artifact_bytes) BETWEEN 1 AND 16777216),
  CONSTRAINT installation_archive_marker_fk FOREIGN KEY (installation_id)
    REFERENCES truss.installation_marker (installation_id) ON DELETE RESTRICT
    DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX installation_archive_identity_route ON truss.installation_archive
  (installation_id, artifact_identity_sha256, archive_row_id);
-- Route is NONUNIQUE. Full installation/role/artifact identity and complete
-- original bytes define correspondence; collisions and equal bytes under
-- distinct identities remain retained. Protected installer enforces exactly
-- one original artifact per full role/identity and complete mandatory roles.
-- The deferred FK permits archives before marker within the same transaction;
-- it does not validate complete archives, original attempt or native authority.
-- 16 MiB per artifact matches the existing generation profile. Whole operation
-- row/byte/peak/work/deadline bounds and native index-size admission remain required.
-- No credentials/connection strings belong in installation identity fields.
