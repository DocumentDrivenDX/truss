-- CONTRACT-009 / ADR-005 PostgreSQL 17 candidate; separate statements, unapplied.
-- Protected native procedure derives $1/$2 from full admitted identities.
-- Earlier head/policy/namespace admission is mandatory, not supplied by this SQL.
-- A. Touch/retain route write-conflict guard without changing logical generation.
INSERT INTO truss.request_receipt_route_guard AS g
  (namespace_sha256, request_sha256, generation)
VALUES ($1::bytea, $2::bytea, 0)
ON CONFLICT (namespace_sha256, request_sha256)
DO UPDATE SET generation = g.generation
RETURNING generation;

-- B. Separate post-wait metadata statement; 10001 signals incomplete admission.
-- Complete identity/artifact lengths must be admitted before full-byte fetch.
SELECT r.storage_row_id, r.original_writer_xid::text,
  octet_length(r.original_writer_context_bytes) AS writer_context_bytes,
  r.expiry_writer_xid::text,
  octet_length(r.expiry_writer_context_bytes) AS expiry_writer_context_bytes,
  r.lifecycle_generation, r.payload_state,
  octet_length(r.namespace_identity_utf8) AS namespace_bytes,
  octet_length(r.request_id_utf8) AS request_bytes,
  octet_length(r.original_receipt_bytes) AS receipt_bytes,
  octet_length(r.expired_identity_bytes) AS expiry_bytes,
  p.protection_generation, p.original_update_writer_xid::text,
  octet_length(p.original_update_writer_context_bytes) AS protection_writer_context_bytes,
  octet_length(p.original_protection_bytes) AS protection_bytes,
  octet_length(p.original_update_evidence_bytes) AS update_evidence_bytes
FROM truss.request_receipt AS r
LEFT JOIN truss.request_receipt_protection AS p
  ON p.receipt_storage_row_id = r.storage_row_id
WHERE r.namespace_sha256 = $1::bytea AND r.request_sha256 = $2::bytea
ORDER BY r.storage_row_id
LIMIT 10001;

-- C. Fetch identities only after ALL B rows/identity bytes are admitted.
-- $3 is the exact complete admitted original metadata ID list, not caller IDs.
SELECT r.storage_row_id, r.namespace_identity_utf8, r.request_id_utf8
FROM truss.request_receipt AS r
WHERE r.namespace_sha256 = $1::bytea AND r.request_sha256 = $2::bytea
  AND r.storage_row_id = ANY($3::bigint[])
ORDER BY r.storage_row_id;

-- D. Final guarded read after complete private owner discovery and admission.
-- Original artifact/work/disclosure bounds and row/length parity are mandatory.
-- A separately registered provisional loader may use the same read shape under
-- private lookup/integrity custody BEFORE owner guards; it cannot disclose or
-- establish absence, commit, or final current-state admission from that read.
SELECT r.storage_row_id, r.original_writer_xid::text,
  r.original_writer_context_bytes, r.expiry_writer_xid::text,
  r.expiry_writer_context_bytes, r.lifecycle_generation, r.payload_state,
  r.original_receipt_bytes, r.expired_identity_bytes,
  p.protection_generation, p.original_update_writer_xid::text,
  p.original_update_writer_context_bytes, p.original_protection_bytes,
  p.original_update_evidence_bytes
FROM truss.request_receipt AS r
LEFT JOIN truss.request_receipt_protection AS p
  ON p.receipt_storage_row_id = r.storage_row_id
WHERE r.namespace_sha256 = $1::bytea AND r.request_sha256 = $2::bytea
  AND r.storage_row_id = $3::bigint;

-- E. Actual receipt/protection/expiry effect increments once per effect.
-- Same retained guard transaction; expected $3 is independently admitted state.
-- Zero rows means conflict/exhaustion/integrity refusal, never effect success.
UPDATE truss.request_receipt_route_guard
SET generation = generation + 1
WHERE namespace_sha256 = $1::bytea AND request_sha256 = $2::bytea
  AND generation = $3::bigint AND generation < 9223372036854775807
RETURNING generation;
-- A-E alone do NOT implement protected insert/expiry/protection or permissions.
-- Never install as independent ordinary grants or treat omitted rows as absence.

-- F. Existing-route observation lease: coordinator writable service only.
-- No INSERT/ON CONFLICT here: missing original guard is observation unavailable.
-- The supplied read-only data scope NEVER executes this statement.
UPDATE truss.request_receipt_route_guard
SET generation = generation
WHERE namespace_sha256 = $1::bytea AND request_sha256 = $2::bytea
RETURNING generation;

-- G. Read-only data context observation; no ID allocation or implicit mode change.
-- Exact one row; NULL observing_xid means unassigned, not unknown/rolled back.
SELECT pg_catalog.pg_current_xact_id_if_assigned()::text AS observing_xid,
  pg_catalog.current_setting('transaction_read_only') AS transaction_read_only,
  pg_catalog.current_setting('transaction_isolation') AS transaction_isolation;
-- F/G plus D require original coordinator lease/affinity and one complete
-- post-lease artifact read. These statements alone confer no permissions/custody.
