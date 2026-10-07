-- Unadopted two-store subset of CONTRACT-006's four-store native feed profile.
-- No installer composition, ordinary-role grants, producer/finalizer or commit guard.
-- Full context/profile text index representability must be selected explicitly.
CREATE TABLE truss.feed_tx (
  source_epoch pg_catalog.text COLLATE pg_catalog."C" NOT NULL,
  feed_profile pg_catalog.text COLLATE pg_catalog."C" NOT NULL,
  original_writer_xid pg_catalog.xid8 NOT NULL,
  registration_counter pg_catalog.int8 NOT NULL DEFAULT 0,
  membership_generation pg_catalog.int8 NOT NULL DEFAULT 0,
  finalized_generation pg_catalog.int8,
  original_context_bytes pg_catalog.bytea NOT NULL,
  manifest_profile_bytes pg_catalog.bytea NOT NULL,
  manifest_bytes pg_catalog.bytea,
  manifest_sha256 pg_catalog.bytea,
  CONSTRAINT feed_tx_pk PRIMARY KEY (source_epoch, feed_profile, original_writer_xid),
  CONSTRAINT feed_tx_context_nonempty CHECK (
    pg_catalog.octet_length(source_epoch) > 0 AND pg_catalog.octet_length(feed_profile) > 0
    AND pg_catalog.octet_length(original_context_bytes) > 0
    AND pg_catalog.octet_length(manifest_profile_bytes) > 0),
  CONSTRAINT feed_tx_generation_domain CHECK (
    registration_counter >= 0 AND membership_generation >= 0
    AND (finalized_generation IS NULL OR
      (finalized_generation >= 0 AND finalized_generation <= membership_generation))),
  CONSTRAINT feed_tx_manifest_completeness CHECK (
    (finalized_generation IS NULL AND manifest_bytes IS NULL AND manifest_sha256 IS NULL)
    OR (finalized_generation IS NOT NULL AND manifest_bytes IS NOT NULL
      AND manifest_sha256 IS NOT NULL AND pg_catalog.octet_length(manifest_bytes) > 0
      AND pg_catalog.octet_length(manifest_sha256) = 32))
);
CREATE TABLE truss.feed_member (
  source_epoch pg_catalog.text COLLATE pg_catalog."C" NOT NULL,
  feed_profile pg_catalog.text COLLATE pg_catalog."C" NOT NULL,
  original_writer_xid pg_catalog.xid8 NOT NULL,
  registration_address pg_catalog.int8 NOT NULL,
  fact_kind pg_catalog.text COLLATE pg_catalog."C" NOT NULL,
  original_fact_key_bytes pg_catalog.bytea NOT NULL,
  original_fact_key_profile_bytes pg_catalog.bytea NOT NULL,
  original_payload_bytes pg_catalog.bytea NOT NULL,
  original_payload_profile_bytes pg_catalog.bytea NOT NULL,
  original_payload_sha256 pg_catalog.bytea NOT NULL,
  original_owner_context_bytes pg_catalog.bytea NOT NULL,
  original_write_at pg_catalog.timestamptz NOT NULL,
  original_fact_clock_bytes pg_catalog.bytea NOT NULL,
  delivery_ordinal pg_catalog.int8,
  CONSTRAINT feed_member_pk PRIMARY KEY (
    source_epoch, feed_profile, original_writer_xid, registration_address),
  CONSTRAINT feed_member_tx_fk FOREIGN KEY (source_epoch, feed_profile, original_writer_xid)
    REFERENCES truss.feed_tx (source_epoch, feed_profile, original_writer_xid),
  CONSTRAINT feed_member_delivery_unique UNIQUE (
    source_epoch, feed_profile, original_writer_xid, delivery_ordinal),
  CONSTRAINT feed_member_address_domain CHECK (
    registration_address > 0 AND (delivery_ordinal IS NULL OR delivery_ordinal >= 0)),
  CONSTRAINT feed_member_originals_nonempty CHECK (
    pg_catalog.octet_length(fact_kind) > 0 AND pg_catalog.octet_length(original_fact_key_bytes) > 0
    AND pg_catalog.octet_length(original_fact_key_profile_bytes) > 0
    AND pg_catalog.octet_length(original_payload_bytes) > 0
    AND pg_catalog.octet_length(original_payload_profile_bytes) > 0
    AND pg_catalog.octet_length(original_owner_context_bytes) > 0
    AND pg_catalog.octet_length(original_fact_clock_bytes) > 0
    AND pg_catalog.octet_length(original_payload_sha256) = 32)
);
-- Full fact-key uniqueness uses protected complete comparison, not a digest index.
-- NULL delivery ordinals permit pending members; contiguous finalized order is native proof.
-- Original clock bytes/profile qualify timestamp meaning/precision; not commit time.
-- Stale finalized_generation is structurally allowed but forbidden at native commit.
-- Empty feed_tx commit, late membership, bypass roles and retention remain native guards.
