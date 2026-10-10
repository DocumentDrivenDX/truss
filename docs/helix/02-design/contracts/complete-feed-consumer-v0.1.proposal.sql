-- CONTRACT-006 complete-feed registration/checkpoint candidate, not a procedure.
-- Baseline feed_consumer remains journal-only; these boundaries are not (xid,seq).
CREATE SEQUENCE truss.complete_feed_consumer_row_seq AS bigint
  MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 NO CYCLE;
CREATE TABLE truss.complete_feed_consumer (
  storage_row_id bigint PRIMARY KEY DEFAULT nextval('truss.complete_feed_consumer_row_seq'),
  source_epoch text COLLATE pg_catalog."C" NOT NULL,
  feed_profile text COLLATE pg_catalog."C" NOT NULL,
  scope_identity text COLLATE pg_catalog."C" NOT NULL,
  consumer_id text COLLATE pg_catalog."C" NOT NULL,
  registration_id text COLLATE pg_catalog."C" NOT NULL,
  worker_generation bigint NOT NULL,
  state_kind text COLLATE pg_catalog."C" NOT NULL,
  consumer_identity_bytes bytea NOT NULL,
  consumer_identity_sha256 bytea GENERATED ALWAYS AS
    (pg_catalog.sha256(consumer_identity_bytes)) STORED,
  original_registration_bytes bytea NOT NULL,
  current_state_bytes bytea NOT NULL,
  current_state_sha256 bytea GENERATED ALWAYS AS
    (pg_catalog.sha256(current_state_bytes)) STORED,
  applied_boundary_bytes bytea,
  applied_boundary_profile_bytes bytea,
  inclusive_protection_xid xid8 NOT NULL,
  protection_evidence_bytes bytea NOT NULL,
  procedure_profile_bytes bytea NOT NULL,
  downstream_profile_bytes bytea NOT NULL,
  registered_at timestamptz NOT NULL,
  acknowledged_at timestamptz,
  CONSTRAINT complete_feed_consumer_counter_domain CHECK
    (storage_row_id > 0 AND worker_generation >= 0),
  CONSTRAINT complete_feed_consumer_state CHECK
    (state_kind IN ('awaiting_seed','active','removed')),
  CONSTRAINT complete_feed_consumer_originals CHECK
    (octet_length(source_epoch) > 0 AND octet_length(feed_profile) > 0
      AND octet_length(scope_identity) > 0 AND octet_length(consumer_id) > 0
      AND octet_length(registration_id) > 0
      AND octet_length(consumer_identity_bytes) > 0
      AND octet_length(original_registration_bytes) > 0
      AND octet_length(current_state_bytes) > 0
      AND octet_length(protection_evidence_bytes) > 0
      AND octet_length(procedure_profile_bytes) > 0
      AND octet_length(downstream_profile_bytes) > 0),
  CONSTRAINT complete_feed_consumer_boundary_pair CHECK
    ((applied_boundary_bytes IS NULL) = (applied_boundary_profile_bytes IS NULL)),
  CONSTRAINT complete_feed_consumer_boundary_nonempty CHECK
    (applied_boundary_bytes IS NULL OR
      (octet_length(applied_boundary_bytes) > 0
        AND octet_length(applied_boundary_profile_bytes) > 0)),
  CONSTRAINT complete_feed_consumer_awaiting CHECK
    (state_kind <> 'awaiting_seed' OR
      (applied_boundary_bytes IS NULL AND acknowledged_at IS NULL)),
  CONSTRAINT complete_feed_consumer_active CHECK
    (state_kind <> 'active' OR applied_boundary_bytes IS NOT NULL)
);
CREATE INDEX complete_feed_consumer_identity_route ON truss.complete_feed_consumer
  (consumer_identity_sha256, storage_row_id);
-- Full registered identity is (sourceEpoch,feedProfile,scopeIdentity,consumerId).
-- Original exact identity encoder/profile and projected-column parity are
-- protected producer obligations; route digest is NONUNIQUE and not authority.
-- At most one nonremoved registration per full identity; never reuse a retained
-- registrationId. Removed rows preserve original state/proof for recovery.
-- Current state bytes preserve exact seed/transaction/coverage boundaries;
-- workerGeneration is fencing, not progress. No fragment is applied state.
-- Original protected floor/classifier/coverage derivation is mandatory; do not
-- subtract xid or infer a seq maximum. Removal ends active protection only
-- through the admitted retention/attempt reconciliation procedure.
-- Stored proof bytes/hashes cannot reconstruct a runtime VerifiedApplication.
-- Current host verification/authority plus full prior-boundary CAS precede ack.
-- acknowledged_at changes only for actual qualified durable application progress;
-- equal idempotent acknowledgments, worker claims and heartbeats do not refresh it.
-- Native clocks, canonical/profile bytes, body/privilege/retention/resource
-- admission, complete uniqueness/fencing/CAS and conversion remain unqualified.
