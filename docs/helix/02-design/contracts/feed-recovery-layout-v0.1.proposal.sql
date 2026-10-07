-- CONTRACT-006 recovery homes; protected producers and native admission required.
CREATE SEQUENCE truss.feed_administration_receipt_row_seq AS bigint MINVALUE 1 START WITH 1 NO CYCLE;
CREATE TABLE truss.complete_feed_administration_receipt (
 storage_row_id bigint PRIMARY KEY DEFAULT nextval('truss.feed_administration_receipt_row_seq'),
 source_epoch text COLLATE pg_catalog."C" NOT NULL CHECK (source_epoch <> ''),
 administrative_namespace text COLLATE pg_catalog."C" NOT NULL CHECK (administrative_namespace <> ''),
 request_id text COLLATE pg_catalog."C" NOT NULL CHECK (request_id <> ''),
 identity_bytes bytea NOT NULL CHECK (octet_length(identity_bytes) > 0),
 identity_sha256 bytea GENERATED ALWAYS AS (sha256(identity_bytes)) STORED,
 canonical_input_bytes bytea NOT NULL CHECK (octet_length(canonical_input_bytes) > 0),
 input_profile_bytes bytea NOT NULL CHECK (octet_length(input_profile_bytes) > 0),
 receipt_bytes bytea NOT NULL CHECK (octet_length(receipt_bytes) > 0),
 receipt_profile_bytes bytea NOT NULL CHECK (octet_length(receipt_profile_bytes) > 0),
 actual_database_role text COLLATE pg_catalog."C" NOT NULL CHECK (actual_database_role <> ''),
 authorization_evidence_bytes bytea NOT NULL CHECK (octet_length(authorization_evidence_bytes) > 0),
 producing_xid xid8 NOT NULL,
 original_production_evidence_bytes bytea NOT NULL CHECK (octet_length(original_production_evidence_bytes) > 0),
 CHECK (storage_row_id > 0)
);
CREATE INDEX feed_administration_receipt_identity_route ON truss.complete_feed_administration_receipt (identity_sha256, storage_row_id);
CREATE SEQUENCE truss.feed_seed_attempt_row_seq AS bigint MINVALUE 1 START WITH 1 NO CYCLE;
CREATE TABLE truss.complete_feed_seed_attempt (
 storage_row_id bigint PRIMARY KEY DEFAULT nextval('truss.feed_seed_attempt_row_seq'),
 attempt_identity_bytes bytea NOT NULL CHECK (octet_length(attempt_identity_bytes) > 0),
 attempt_identity_sha256 bytea GENERATED ALWAYS AS (sha256(attempt_identity_bytes)) STORED,
 activation_profile_bytes bytea NOT NULL CHECK (octet_length(activation_profile_bytes) > 0),
 source_context_bytes bytea NOT NULL CHECK (octet_length(source_context_bytes) > 0),
 original_worker_bytes bytea NOT NULL CHECK (octet_length(original_worker_bytes) > 0),
 state_kind text COLLATE pg_catalog."C" NOT NULL CHECK (state_kind IN ('protected','extracting','staged','active','abandoned')),
 current_state_bytes bytea NOT NULL CHECK (octet_length(current_state_bytes) > 0),
 inclusive_replay_xmin xid8 NOT NULL,
 protection_evidence_bytes bytea NOT NULL CHECK (octet_length(protection_evidence_bytes) > 0),
 invalidation_evidence_bytes bytea CHECK (invalidation_evidence_bytes IS NULL OR octet_length(invalidation_evidence_bytes) > 0),
 classifier_retirement_evidence_bytes bytea CHECK (classifier_retirement_evidence_bytes IS NULL OR octet_length(classifier_retirement_evidence_bytes) > 0),
 CHECK (storage_row_id > 0)
);
CREATE INDEX feed_seed_attempt_identity_route ON truss.complete_feed_seed_attempt (attempt_identity_sha256, storage_row_id);
CREATE SEQUENCE truss.feed_seed_artifact_row_seq AS bigint MINVALUE 1 START WITH 1 NO CYCLE;
CREATE TABLE truss.complete_feed_seed_artifact (
 storage_row_id bigint PRIMARY KEY DEFAULT nextval('truss.feed_seed_artifact_row_seq'),
 attempt_row_id bigint NOT NULL REFERENCES truss.complete_feed_seed_attempt(storage_row_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
 artifact_role text COLLATE pg_catalog."C" NOT NULL CHECK (artifact_role IN ('baseline','inventory','visibility_classifier','binding_anchor','extraction','stage_validation','downstream_activation','source_confirmation','invalidation','abandonment_containment')),
 artifact_ordinal bigint NOT NULL CHECK (artifact_ordinal >= 0),
 artifact_identity_bytes bytea NOT NULL CHECK (octet_length(artifact_identity_bytes) > 0),
 artifact_identity_sha256 bytea GENERATED ALWAYS AS (sha256(artifact_identity_bytes)) STORED,
 artifact_profile_bytes bytea NOT NULL CHECK (octet_length(artifact_profile_bytes) > 0),
 payload_bytes bytea NOT NULL CHECK (octet_length(payload_bytes) > 0),
 payload_sha256 bytea GENERATED ALWAYS AS (sha256(payload_bytes)) STORED,
 production_custody_evidence_bytes bytea NOT NULL CHECK (octet_length(production_custody_evidence_bytes) > 0),
 CHECK (storage_row_id > 0)
);
CREATE INDEX feed_seed_artifact_identity_route ON truss.complete_feed_seed_artifact (attempt_row_id, artifact_identity_sha256, storage_row_id);
-- All route indexes are nonunique. Protected producers serialize full-byte identity
-- and ordinal/cardinality checks; enforce decoded/projection parity, immutable
-- originals, worker/state CAS, role/custody, finite resource admission and retention.
-- Observation evidence produced after commit is separate from original production
-- bytes: no commit proof is manufactured inside its own producing transaction.
-- No consumer FK/cascade and no automatic expiry. Invalidation is not abandonment.
