-- CONTRACT-001 / TD-009 physical design fragment; NEVER applied in this work.
-- PostgreSQL 17 candidate; no native parser/runtime qualification.
-- Requires original truss.object and truss.key_def typed homes.
-- Missing writer/derivation/generation triggers, privileges, migration/feed stores.
-- Fixed generic stores; these are not per-type tables or an executable installer.
CREATE SEQUENCE truss.key_storage_row_seq AS bigint
  MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 NO CYCLE;

CREATE TABLE truss.key_bucket_guard (
  namespace_sha256 bytea NOT NULL,
  key_sha256 bytea NOT NULL,
  generation bigint NOT NULL DEFAULT 0,
  CONSTRAINT key_bucket_guard_pkey PRIMARY KEY (namespace_sha256, key_sha256),
  CONSTRAINT key_bucket_namespace_digest_size CHECK (octet_length(namespace_sha256) = 32),
  CONSTRAINT key_bucket_key_digest_size CHECK (octet_length(key_sha256) = 32),
  CONSTRAINT key_bucket_generation_nonnegative CHECK (generation >= 0)
);

CREATE TABLE truss.object_key_bucket (
  storage_row_id bigint NOT NULL DEFAULT nextval('truss.key_storage_row_seq'),
  type_id int NOT NULL,
  key_num smallint NOT NULL,
  object_id bigint NOT NULL,
  namespace_bytes bytea NOT NULL,
  key_bytes bytea NOT NULL,
  -- Original qualified encoding/owner/definition context; not mutable catalog projection.
  original_context_bytes bytea NOT NULL,
  namespace_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(namespace_bytes)) STORED,
  key_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(key_bytes)) STORED,
  CONSTRAINT object_key_bucket_pkey PRIMARY KEY (storage_row_id),
  CONSTRAINT object_key_bucket_storage_id_positive CHECK (storage_row_id > 0),
  CONSTRAINT object_key_bucket_namespace_bound CHECK (octet_length(namespace_bytes) BETWEEN 1 AND 65536),
  CONSTRAINT object_key_bucket_key_bound CHECK (octet_length(key_bytes) BETWEEN 1 AND 1048576),
  CONSTRAINT object_key_bucket_context_nonempty CHECK (octet_length(original_context_bytes) > 0),
  CONSTRAINT object_key_bucket_one_per_object UNIQUE (object_id, type_id, key_num),
  CONSTRAINT object_key_bucket_definition_fk FOREIGN KEY (type_id, key_num)
    REFERENCES truss.key_def (type_id, key_num),
  CONSTRAINT object_key_bucket_object_fk FOREIGN KEY (object_id, type_id)
    REFERENCES truss.object (id, type_id) ON DELETE CASCADE,
  CONSTRAINT object_key_bucket_guard_fk FOREIGN KEY (namespace_sha256, key_sha256)
    REFERENCES truss.key_bucket_guard (namespace_sha256, key_sha256)
);
CREATE INDEX object_key_bucket_route ON truss.object_key_bucket (namespace_sha256, key_sha256, storage_row_id);

-- Object-key reservation projection; original identity stays in the immutable full artifact.
-- Edge endpoint reservations require their separate selected inventory, not this fragment.
CREATE TABLE truss.object_key_reservation_bucket (
  storage_row_id bigint NOT NULL DEFAULT nextval('truss.key_storage_row_seq'),
  namespace_bytes bytea NOT NULL,
  key_bytes bytea NOT NULL,
  original_reservation_bytes bytea NOT NULL,
  namespace_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(namespace_bytes)) STORED,
  key_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(key_bytes)) STORED,
  CONSTRAINT object_key_reservation_bucket_pkey PRIMARY KEY (storage_row_id),
  CONSTRAINT object_key_reservation_storage_id_positive CHECK (storage_row_id > 0),
  CONSTRAINT object_key_reservation_namespace_bound CHECK (octet_length(namespace_bytes) BETWEEN 1 AND 65536),
  CONSTRAINT object_key_reservation_key_bound CHECK (octet_length(key_bytes) BETWEEN 1 AND 1048576),
  CONSTRAINT object_key_reservation_original_nonempty CHECK (octet_length(original_reservation_bytes) > 0),
  CONSTRAINT object_key_reservation_guard_fk FOREIGN KEY (namespace_sha256, key_sha256)
    REFERENCES truss.key_bucket_guard (namespace_sha256, key_sha256)
);
CREATE INDEX object_key_reservation_bucket_route ON truss.object_key_reservation_bucket (namespace_sha256, key_sha256, storage_row_id);
