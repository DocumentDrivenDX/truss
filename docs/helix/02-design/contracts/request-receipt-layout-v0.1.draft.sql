-- ADR-005 / CONTRACT-009 candidate PostgreSQL 17; unapplied, unqualified.
-- Original namespace UTF-8 is admitted through trusted namespace custody.
-- Digest routes serialize collisions; protected procedures compare full identities.
-- Request-level fixed route guard, acquired after policy/namespace guards.
CREATE TABLE truss.request_receipt_route_guard (
  namespace_sha256 bytea NOT NULL CONSTRAINT rr_guard_namespace_digest CHECK (octet_length(namespace_sha256) = 32),
  request_sha256 bytea NOT NULL CONSTRAINT rr_guard_request_digest CHECK (octet_length(request_sha256) = 32),
  generation bigint NOT NULL CONSTRAINT rr_guard_generation CHECK (generation >= 0),
  CONSTRAINT rr_guard_pk PRIMARY KEY (namespace_sha256, request_sha256)
);
-- Guard routing is not logical namespace/request identity. Guard rows persist;
-- deleting/recreating them would invalidate original snapshot/conflict custody.
CREATE SEQUENCE truss.request_receipt_row_seq AS bigint
  MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 NO CYCLE;
CREATE TABLE truss.request_receipt (
  storage_row_id bigint CONSTRAINT rr_receipt_pk PRIMARY KEY DEFAULT nextval('truss.request_receipt_row_seq'),
  namespace_identity_utf8 bytea NOT NULL
    CONSTRAINT rr_namespace_identity_bytes CHECK (octet_length(namespace_identity_utf8) BETWEEN 1 AND 65536),
  request_id_utf8 bytea NOT NULL
    CONSTRAINT rr_request_identity_bytes CHECK (octet_length(request_id_utf8) BETWEEN 1 AND 65536),
  original_writer_xid xid8 NOT NULL,
  original_writer_context_bytes bytea NOT NULL
    CONSTRAINT rr_writer_context_bytes CHECK (octet_length(original_writer_context_bytes) BETWEEN 1 AND 1048576),
  lifecycle_generation bigint NOT NULL CONSTRAINT rr_lifecycle_generation CHECK (lifecycle_generation >= 0),
  payload_state text NOT NULL CONSTRAINT rr_payload_state CHECK (payload_state IN ('complete','expired')),
  original_receipt_bytes bytea,
  expired_identity_bytes bytea,
  namespace_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(namespace_identity_utf8)) STORED,
  request_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(request_id_utf8)) STORED,
  CONSTRAINT request_receipt_positive_storage CHECK (storage_row_id > 0),
  CONSTRAINT request_receipt_payload_shape CHECK (
    (payload_state = 'complete' AND original_receipt_bytes IS NOT NULL
      AND octet_length(original_receipt_bytes) BETWEEN 1 AND 67108864
      AND expired_identity_bytes IS NULL
      AND expiry_writer_xid IS NULL AND expiry_writer_context_bytes IS NULL)
    OR
    (payload_state = 'expired' AND original_receipt_bytes IS NULL
      AND expired_identity_bytes IS NOT NULL
      AND octet_length(expired_identity_bytes) BETWEEN 1 AND 1048576
      AND expiry_writer_xid IS NOT NULL AND expiry_writer_context_bytes IS NOT NULL)
  ),
  expiry_writer_xid xid8,
  expiry_writer_context_bytes bytea
    CONSTRAINT rr_expiry_writer_context_bytes CHECK (expiry_writer_context_bytes IS NULL OR octet_length(expiry_writer_context_bytes) BETWEEN 1 AND 1048576)
);
CREATE INDEX request_receipt_route ON truss.request_receipt
  (namespace_sha256, request_sha256, storage_row_id);
-- Fixed-size route is deliberately nonunique. No full large-bytea B-tree identity.
-- Unavoidable native route guard + full-identity duplicate admission is required.
-- No ordinary INSERT/UPDATE/DELETE/TRUNCATE or sequence grants are implied.
CREATE TABLE truss.request_receipt_protection (
  receipt_storage_row_id bigint CONSTRAINT rr_protection_pk PRIMARY KEY
    CONSTRAINT rr_protection_receipt_fk REFERENCES truss.request_receipt(storage_row_id) ON DELETE RESTRICT,
  protection_generation bigint NOT NULL CONSTRAINT rr_protection_generation CHECK (protection_generation >= 0),
  original_protection_bytes bytea NOT NULL
    CONSTRAINT rr_protection_artifact_bytes CHECK (octet_length(original_protection_bytes) BETWEEN 1 AND 1048576),
  original_update_evidence_bytes bytea NOT NULL
    CONSTRAINT rr_protection_evidence_bytes CHECK (octet_length(original_update_evidence_bytes) BETWEEN 1 AND 1048576),
  original_update_writer_xid xid8 NOT NULL,
  original_update_writer_context_bytes bytea NOT NULL
    CONSTRAINT rr_protection_update_context_bytes CHECK (octet_length(original_update_writer_context_bytes) BETWEEN 1 AND 1048576)
);
-- Creation/update generation, original-clock/commit/profile/current authority,
-- monotonic deadlines, expired-state prohibition and protected purge remain
-- privileged procedure assertions; these checks cannot decode artifact meaning.
-- Protections never imply that the pending protection transaction committed.

-- Protected original insert derives top-level pg_current_xact_id() and original
-- installation/epoch/connection/context evidence itself; no caller XID admission.
-- Original provenance is immutable across expiry/protection and never from xmin.
