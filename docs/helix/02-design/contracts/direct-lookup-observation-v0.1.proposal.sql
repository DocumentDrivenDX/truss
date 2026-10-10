-- Design-only baseline fixed lookup statements for CONTRACT-004.
-- No database execution or privilege/snapshot/decoder qualification.
-- Original current-authority/context/mapping/parameter admission is required.
-- Integral projection columns use native decimal text; predicates/order remain
-- native numeric. JSONB/temporal/bytea transport still needs exact profile admission.
-- LIMIT 2 detects an unexpected duplicate visible identity; a second row is
-- invalid observation, never an arbitrary winner or successful truncated set.

-- Object-ID lookup: $1 mapped type_id int; $2 positive object id bigint.
SELECT o.id::text AS id, o.type_id::text AS type_id, o.props::text AS props, o.retained::text AS retained,
       o.root_id::text AS root_id, o.root_type::text AS root_type,
       o.rev::text AS rev, o.ver::text AS ver, o.created_at::text AS created_at, o.updated_at::text AS updated_at,
       pg_catalog.current_setting('DateStyle') AS metadata_date_style,
       pg_catalog.current_setting('TimeZone') AS metadata_time_zone
FROM truss.object AS o
WHERE o.type_id = $1::int AND o.id = $2::bigint
LIMIT 2;

-- Proposed single-statement read-only full-byte bucket lookup.
-- Requires the selected bucket layout's full-equality integrity/native policy
-- profile; it is not available over the baseline table set.
-- $1 mapped signed type_id int; $2 mapped signed key_num smallint;
-- $3/$4 admitted 32-byte namespace/key route digests;
-- $5/$6 complete original namespace/key bytes (not caller proof).
-- The registered protected read path has qualified SELECT/RLS on BOTH homes
-- under original data-caller admission (CONTRACT-005); raw application context
-- grants are not implied. It does not invoke guard_touch/guard_insert, inspect
-- reservation identities or mutate.
-- Retained context is private semantic admission input, never public payload.
SELECT o.id::text AS id, o.type_id::text AS type_id, o.props::text AS props, o.retained::text AS retained,
       o.root_id::text AS root_id, o.root_type::text AS root_type,
       o.rev::text AS rev, o.ver::text AS ver, o.created_at::text AS created_at, o.updated_at::text AS updated_at,
       pg_catalog.current_setting('DateStyle') AS metadata_date_style,
       pg_catalog.current_setting('TimeZone') AS metadata_time_zone,
       b.type_id::text AS matched_type_id, b.key_num::text AS matched_key_num,
       b.object_id::text AS matched_object_id,
       pg_catalog.encode(b.namespace_bytes, 'hex') AS matched_namespace_hex,
       pg_catalog.encode(b.key_bytes, 'hex') AS matched_key_hex,
       pg_catalog.encode(b.original_context_bytes, 'hex') AS matched_context_hex
FROM truss.object_key_bucket AS b
JOIN truss.object AS o
  ON o.id = b.object_id AND o.type_id = b.type_id
WHERE b.type_id = $1::int AND b.key_num = $2::smallint
  AND b.namespace_sha256 = $3::bytea AND b.key_sha256 = $4::bytea
  AND b.namespace_bytes = $5::bytea AND b.key_bytes = $6::bytea
LIMIT 2;

-- Edge-ID lookup: $1 positive global edge id bigint.
SELECT e.id::text AS id, e.rel_type_id::text AS rel_type_id,
       e.source_id::text AS source_id, e.source_type::text AS source_type,
       e.target_id::text AS target_id, e.target_type::text AS target_type,
       e.props::text AS props, e.order_key, e.rev::text AS rev, e.ver::text AS ver, e.created_at::text AS created_at, e.updated_at::text AS updated_at,
       pg_catalog.current_setting('DateStyle') AS metadata_date_style,
       pg_catalog.current_setting('TimeZone') AS metadata_time_zone
FROM truss.edge AS e
WHERE e.id = $1::bigint
LIMIT 2;

-- Baseline object-key lookup: $1 mapped signed type_id int;
-- $2 mapped signed native key_num smallint; $3 verified exact baseline k text.
-- $3 is produced by the selected admitted key encoder/native transport, not
-- caller-supplied text/hash and not an order/comparison reinterpretation.
-- This statement does not implement the full-byte large-key bucket candidate.
SELECT o.id::text AS id, o.type_id::text AS type_id, o.props::text AS props, o.retained::text AS retained,
       o.root_id::text AS root_id, o.root_type::text AS root_type,
       o.rev::text AS rev, o.ver::text AS ver, o.created_at::text AS created_at, o.updated_at::text AS updated_at,
       pg_catalog.current_setting('DateStyle') AS metadata_date_style,
       pg_catalog.current_setting('TimeZone') AS metadata_time_zone
FROM truss.object_key AS k
JOIN truss.object AS o
  ON o.id = k.object_id AND o.type_id = k.type_id
WHERE k.type_id = $1::int AND k.key_num = $2::smallint
  AND k.k COLLATE "C" = $3::text COLLATE "C"
LIMIT 2;
