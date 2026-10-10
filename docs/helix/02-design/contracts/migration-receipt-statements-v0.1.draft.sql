-- Separate unapplied PostgreSQL 17 templates; not a native recovery procedure.
-- Hold qualified exclusive original schema_head for the complete lookup; all
-- receipt insert/purge paths must participate. Digest inputs are independently
-- derived from original complete UTF-8 installation/epoch/attempt bytes.

-- receipt_metadata: fixed candidate 10,000 complete routing rows plus lookahead.
SELECT storage_row_id::text, prior_generation::text, resulting_generation::text,
       octet_length(installation_id_utf8)::text AS installation_bytes,
       octet_length(source_epoch_utf8)::text AS epoch_bytes,
       octet_length(migration_attempt_id_utf8)::text AS attempt_identity_bytes,
       octet_length(original_request_bytes)::text AS request_bytes,
       octet_length(original_attempt_bytes)::text AS original_attempt_bytes,
       octet_length(receipt_bytes)::text AS receipt_bytes
FROM truss.key_migration_receipt
WHERE installation_sha256 = $1::bytea AND epoch_sha256 = $2::bytea
  AND attempt_sha256 = $3::bytea
ORDER BY storage_row_id LIMIT 10001;

-- receipt_originals: only complete admitted row IDs; no unbounded bucket fetch.
SELECT storage_row_id::text, installation_id_utf8, source_epoch_utf8,
       migration_attempt_id_utf8, original_request_bytes, original_attempt_bytes,
       receipt_bytes, prior_generation::text, resulting_generation::text
FROM truss.key_migration_receipt
WHERE installation_sha256 = $1::bytea AND epoch_sha256 = $2::bytea
  AND attempt_sha256 = $3::bytea AND storage_row_id = ANY($4::bigint[])
ORDER BY storage_row_id;
-- Row/byte/profile/cancellation/output limits must admit metadata before fetch;
-- exact ID/order/count/length correspondence must be rechecked afterwards.
-- No receipt INSERT template is an unavoidable atomic switch/finalizer procedure.
