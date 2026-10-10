-- Design-only fixed observation statements for CONTRACT-004 direct pages.
-- Not installed, executed or native-qualified. UMF source preservation is
-- checked separately; complete query/parameter extraction remains unavailable.
-- No authority is supplied
-- by these parameters: original read context, mapping and current disclosure
-- admission must precede submission under the selected ordinary observer role.
-- $lookahead is admitted page limit + 1, checked without integer overflow.
-- Integral projection columns use native decimal text; predicates/order remain
-- native numeric. JSONB/temporal/bytea transport still needs exact profile admission.

-- Object parameters: $1 mapped native type_id int; $2 has_after boolean;
-- $3 original after.id bigint (NULL only on first page); $4 lookahead int.
-- All signed catalog IDs are preserved. Stored record IDs remain positive.
SELECT o.id::text AS id, o.type_id::text AS type_id, o.props::text AS props, o.retained::text AS retained,
       o.root_id::text AS root_id, o.root_type::text AS root_type,
       o.rev::text AS rev, o.ver::text AS ver,
       o.created_at::text AS created_at, o.updated_at::text AS updated_at,
       pg_catalog.current_setting('DateStyle') AS metadata_date_style,
       pg_catalog.current_setting('TimeZone') AS metadata_time_zone
FROM truss.object AS o
WHERE o.type_id = $1::int
  AND (NOT $2::boolean OR o.id > $3::bigint)
ORDER BY o.id ASC
LIMIT $4::int;

-- Edge parameters: $1 mapped selected object type_id int; $2 object id bigint;
-- $3 admitted direction text: outgoing/incoming/both;
-- $4 complete unique mapped rel_type_id int[]; empty means all admitted kinds;
-- $5 has_after boolean; $6 after.order_key_is_null boolean;
-- $7 after.order_key text (NULL only on first/null-key continuation);
-- $8 after.edge_id bigint (NULL only on first page); $9 lookahead int.
-- Structured cursor/context validation occurs before binding: NULL/unknown
-- direction or malformed continuation is refusal, not an empty valid page.
SELECT e.id::text AS id, e.rel_type_id::text AS rel_type_id,
       e.source_id::text AS source_id, e.source_type::text AS source_type,
       e.target_id::text AS target_id, e.target_type::text AS target_type,
       e.props::text AS props, e.order_key, e.rev::text AS rev, e.ver::text AS ver, e.created_at::text AS created_at, e.updated_at::text AS updated_at,
       pg_catalog.current_setting('DateStyle') AS metadata_date_style,
       pg_catalog.current_setting('TimeZone') AS metadata_time_zone
FROM truss.edge AS e
WHERE (
    ($3::text IN ('outgoing', 'both')
      AND e.source_type = $1::int AND e.source_id = $2::bigint)
    OR
    ($3::text IN ('incoming', 'both')
      AND e.target_type = $1::int AND e.target_id = $2::bigint)
  )
  AND (cardinality($4::int[]) = 0 OR e.rel_type_id = ANY($4::int[]))
  AND (
    NOT $5::boolean
    OR (
      NOT $6::boolean
      AND (
        e.order_key IS NULL
        OR e.order_key COLLATE "C" > $7::text COLLATE "C"
        OR (e.order_key COLLATE "C" = $7::text COLLATE "C"
            AND e.id > $8::bigint)
      )
    )
    OR ($6::boolean AND e.order_key IS NULL AND e.id > $8::bigint)
  )
ORDER BY e.order_key COLLATE "C" ASC NULLS LAST, e.id ASC
LIMIT $9::int;
