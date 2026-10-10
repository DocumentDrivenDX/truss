-- Private target-only reference candidate; no native execution/qualification.
-- $1 original rel_type_id int4, $2 target_type int4, $3 target_id int8.
-- All parameters are non-null and admitted from protected original scope custody.
-- Complete visibility, locked snapshot and native producer/resource admission required.
SELECT pg_catalog.count(*)::pg_catalog.text AS saturated_count
FROM (SELECT e.id FROM truss.edge AS e
      WHERE e.rel_type_id = $1::pg_catalog.int4
        AND e.target_type = $2::pg_catalog.int4
        AND e.target_id = $3::pg_catalog.int8
      LIMIT 2) AS incoming_witness;
