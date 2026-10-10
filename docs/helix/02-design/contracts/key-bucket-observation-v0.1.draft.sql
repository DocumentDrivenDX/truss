-- TD-009 / CONTRACT-001 proposed statement templates, not executed.
-- Each named statement is issued SEPARATELY by the admitted native procedure.
-- $1/$2 are 32-byte production digests from independently admitted full inputs.
-- Requires catalog/configuration/business lock hierarchy and operation savepoint.
-- Privileged integrity visibility and ordinary result disclosure remain unqualified.

-- guard_touch: zero rows requires the separate protected insertion branch.
-- Fixed-snapshot native write conflict requires whole-transaction retry.
UPDATE truss.key_bucket_guard
SET generation = generation
WHERE namespace_sha256 = $1::bytea AND key_sha256 = $2::bytea
RETURNING generation::text;

-- guard_insert: ONLY after no guard touch; unique collision is not empty membership.
-- Do not suppress conflict with ON CONFLICT DO NOTHING and reuse old snapshot.
INSERT INTO truss.key_bucket_guard (namespace_sha256, key_sha256, generation)
VALUES ($1::bytea, $2::bytea, 0)
RETURNING generation::text;

-- live_metadata: fresh qualified statement AFTER all planned guard admissions.
SELECT storage_row_id::text AS storage_row_id,
       octet_length(namespace_bytes)::text AS namespace_bytes_length,
       octet_length(key_bytes)::text AS key_bytes_length,
       octet_length(original_context_bytes)::text AS original_artifact_bytes_length
FROM truss.object_key_bucket
WHERE namespace_sha256 = $1::bytea AND key_sha256 = $2::bytea
ORDER BY storage_row_id
LIMIT 10001;

-- reservation_metadata: account together with live rows and all planned buckets.
SELECT storage_row_id::text AS storage_row_id,
       octet_length(namespace_bytes)::text AS namespace_bytes_length,
       octet_length(key_bytes)::text AS key_bytes_length,
       octet_length(original_reservation_bytes)::text AS original_artifact_bytes_length
FROM truss.object_key_reservation_bucket
WHERE namespace_sha256 = $1::bytea AND key_sha256 = $2::bytea
ORDER BY storage_row_id
LIMIT 10001;

-- live_full: $3 is the admitted complete bounded metadata identity array.
-- Native bytea decoding and total encoded-output/work budgets are separate gates.
SELECT storage_row_id::text AS storage_row_id, type_id::text AS type_id,
       key_num::text AS key_num, object_id::text AS object_id,
       namespace_bytes, key_bytes, original_context_bytes
FROM truss.object_key_bucket
WHERE namespace_sha256 = $1::bytea AND key_sha256 = $2::bytea
  AND storage_row_id = ANY ($3::bigint[])
ORDER BY storage_row_id;

-- reservation_full: original reservation artifact is never reduced to a digest.
SELECT storage_row_id::text AS storage_row_id,
       namespace_bytes, key_bytes, original_reservation_bytes
FROM truss.object_key_reservation_bucket
WHERE namespace_sha256 = $1::bytea AND key_sha256 = $2::bytea
  AND storage_row_id = ANY ($3::bigint[])
ORDER BY storage_row_id;

-- generation_advance: $3 is independently derived actual membership effect count.
-- Zero/overflow/absent guard cannot silently pass a mutation; restore/recover scope.
UPDATE truss.key_bucket_guard
SET generation = generation + $3::bigint
WHERE namespace_sha256 = $1::bytea AND key_sha256 = $2::bytea
  AND $3::bigint > 0
  AND generation <= 9223372036854775807 - $3::bigint
RETURNING generation::text;
