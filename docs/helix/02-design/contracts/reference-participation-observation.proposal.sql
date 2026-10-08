-- Private read-only candidate, not installed or executed.
-- Original admitted parameters: $1 rel_type_id int4, $2 source_type int4,
-- $3 source_id int8, $4 target_type int4, $5 target_id int8.
-- Caller custody comes from the protected affected-scope registry, not public IDs.
-- Complete private visibility, parent exclusions, locked snapshot revalidation,
-- exact current relationship/type/bound admission and producer bounds are prerequisites.
-- Each limit is bound+1: the returned count is saturated, never an exact large degree.
SELECT
  (SELECT pg_catalog.count(*)::pg_catalog.text FROM
    (SELECT e.id FROM truss.edge AS e
     WHERE e.rel_type_id = $1::pg_catalog.int4
       AND e.source_type = $2::pg_catalog.int4
       AND e.source_id = $3::pg_catalog.int8
     LIMIT 3) AS outgoing_witness) AS outgoing_saturated_count,
  (SELECT pg_catalog.count(*)::pg_catalog.text FROM
    (SELECT e.id FROM truss.edge AS e
     WHERE e.rel_type_id = $1::pg_catalog.int4
       AND e.target_type = $4::pg_catalog.int4
       AND e.target_id = $5::pg_catalog.int8
     LIMIT 2) AS incoming_witness) AS incoming_saturated_count;
