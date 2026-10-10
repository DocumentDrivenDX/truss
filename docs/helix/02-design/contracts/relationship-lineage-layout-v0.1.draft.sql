-- CONTRACT-001/003 / ADR-004 candidate adjunct; unapplied/unqualified.
-- A new explicit layout MUST replace legacy UNIQUE(module, rel_id), close
-- original owner columns/policies/provenance and enforce total mapping natively.
-- This fragment is not independently activatable or compatible baseline 0.2 DDL.
CREATE TABLE truss.relationship_lineage (
  rel_type_id int PRIMARY KEY REFERENCES truss.rel_def (rel_type_id) ON DELETE RESTRICT,
  lineage_category text NOT NULL,
  identity_profile text NOT NULL,
  original_identity_bytes bytea NOT NULL,
  identity_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_identity_bytes)) STORED,
  CONSTRAINT relationship_lineage_category CHECK (lineage_category IN ('authored', 'composition_field')),
  CONSTRAINT relationship_lineage_profile_nonempty CHECK (length(identity_profile) > 0),
  CONSTRAINT relationship_lineage_identity_nonempty CHECK (octet_length(original_identity_bytes) > 0)
);
CREATE INDEX relationship_lineage_route
  ON truss.relationship_lineage (identity_sha256, rel_type_id);
-- Digest routing is NONUNIQUE; full exact identity equality defines lineage.
-- Protected catalog acceptance holds the original exclusive head for complete
-- collision/mapping admission, allocation, actual effects and finalization.
-- No ordinary write grants, caller-selected identity bytes or hash-only equality.
-- Retirement retains the original row/identity; numeric IDs are never reassigned.
