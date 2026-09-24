-- C5: property indexes and whether the planner uses them for Cypher equality and range predicates.
-- Runs on the 'bench' graph from bench/00_load.sql (100k Person, 500k KNOWS). AGE 1.8.0 / PG 18.6.
\pset pager off
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
DROP INDEX IF EXISTS bench.person_props_gin;
DROP INDEX IF EXISTS bench.person_uid_btree;
DROP INDEX IF EXISTS bench.person_age_btree;

\echo '==== C5.0 no property indexes (only AGE 1.8 automatic id / endpoint indexes)'
\d bench."Person"
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person {uid: 4242}) RETURN p $$) AS (p agtype);

\echo '==== C5.1 GIN on properties'
CREATE INDEX person_props_gin ON bench."Person" USING gin (properties);
ANALYZE bench."Person";
\echo '-- map-pattern equality (compiled to @> containment)'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person {uid: 4242}) RETURN p $$) AS (p agtype);
\echo '-- WHERE equality (compiled to agtype_access_operator = ...)'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person) WHERE p.uid = 4242 RETURN p $$) AS (p agtype);

\echo '==== C5.2 BTREE on property expressions'
CREATE INDEX person_uid_btree ON bench."Person" (agtype_access_operator(VARIADIC ARRAY[properties, '"uid"'::agtype]));
CREATE INDEX person_age_btree ON bench."Person" (agtype_access_operator(VARIADIC ARRAY[properties, '"age"'::agtype]));
ANALYZE bench."Person";
\echo '-- WHERE equality'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person) WHERE p.uid = 4242 RETURN p $$) AS (p agtype);
\echo '-- WHERE range on uid (selective)'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person) WHERE p.uid >= 1000 AND p.uid < 1010 RETURN p.uid $$) AS (u agtype);
\echo '-- WHERE range on age (about 1/90 of rows per value)'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person) WHERE p.age > 88 RETURN count(*) $$) AS (c agtype);
\echo '-- map-pattern equality with GIN and BTREE both present'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person {uid: 4242}) RETURN p $$) AS (p agtype);
\echo '-- parameterised equality through a prepared statement'
PREPARE by_uid(agtype) AS SELECT * FROM cypher('bench', $$ MATCH (p:Person) WHERE p.uid = $u RETURN p.name $$, $1) AS (n agtype);
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) EXECUTE by_uid('{"u": 4242}');
\echo '-- age.enable_containment = off turns map patterns into -> access'
SET age.enable_containment = off;
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (p:Person {uid: 4242}) RETURN p $$) AS (p agtype);
RESET age.enable_containment;

\echo '==== C5.3 one-hop traversal from an indexed start vertex: are the edge endpoint indexes used?'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM cypher('bench', $$ MATCH (a:Person)-[:KNOWS]->(b:Person) WHERE a.uid = 4242 RETURN b.uid $$) AS (u agtype);
\echo '==== C5.4 relational baseline plans for the same predicates'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT * FROM rel.person WHERE uid = 4242;
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY ON) SELECT b.uid FROM rel.person a JOIN rel.knows k ON k.src = a.id JOIN rel.person b ON b.id = k.dst WHERE a.uid = 4242;
