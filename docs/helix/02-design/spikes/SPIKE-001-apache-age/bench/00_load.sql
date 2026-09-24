-- C5 / C12 dataset: identical data in (a) a hand-designed relational schema and (b) an AGE graph.
-- 100,000 Person vertices, 500,000 directed KNOWS edges (random, no self loops, seeded).
-- AGE 1.8.0 hardcodes the loader base directory /tmp/age/ (AGE_BASE_CSV_DIRECTORY in age_load.c),
-- so the CSVs are staged there and passed to the loader by bare file name.
\pset pager off
\timing on
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

DROP SCHEMA IF EXISTS rel CASCADE;
CREATE SCHEMA rel;
CREATE TABLE rel.person (id bigint PRIMARY KEY, uid bigint NOT NULL UNIQUE, name text NOT NULL, age int NOT NULL);
CREATE TABLE rel.knows (src bigint NOT NULL REFERENCES rel.person(id), dst bigint NOT NULL REFERENCES rel.person(id));
SELECT setseed(0.42);
INSERT INTO rel.person SELECT i, i, 'person-' || i, i % 90 FROM generate_series(1, 100000) i;
INSERT INTO rel.knows
SELECT s, CASE WHEN d >= s THEN d + 1 ELSE d END
FROM (SELECT 1 + floor(random() * 100000)::bigint AS s, 1 + floor(random() * 99999)::bigint AS d FROM generate_series(1, 500000)) x;
CREATE INDEX knows_src_dst ON rel.knows (src, dst);
CREATE INDEX knows_dst ON rel.knows (dst);
ANALYZE rel.person; ANALYZE rel.knows;

\set pfile '/tmp/age/person.csv'
\set efile '/tmp/age/knows.csv'
COPY (SELECT id, uid, name, age FROM rel.person ORDER BY id) TO :'pfile' WITH (FORMAT csv, HEADER true);
COPY (SELECT src AS start_id, 'Person' AS start_vertex_type, dst AS end_id, 'Person' AS end_vertex_type FROM rel.knows) TO :'efile' WITH (FORMAT csv, HEADER true);

SELECT drop_graph('bench', true) FROM ag_graph WHERE name = 'bench';
SELECT create_graph('bench');
SELECT create_vlabel('bench', 'Person');
SELECT create_elabel('bench', 'KNOWS');
-- id_field_exists => true keeps CSV ids as graphid entry ids; load_as_agtype => true parses numbers as agtype integers
SELECT load_labels_from_file('bench', 'Person', 'person.csv', true, true);
SELECT load_edges_from_file('bench', 'KNOWS', 'knows.csv', true);
ANALYZE bench."Person"; ANALYZE bench."KNOWS";

SELECT count(*) AS rel_persons FROM rel.person;
SELECT count(*) AS rel_edges FROM rel.knows;
SELECT * FROM cypher('bench', $$ MATCH (p:Person) RETURN count(p) $$) AS (age_persons agtype);
SELECT * FROM cypher('bench', $$ MATCH ()-[k:KNOWS]->() RETURN count(k) $$) AS (age_edges agtype);
SELECT * FROM cypher('bench', $$ MATCH (p:Person) RETURN p ORDER BY p.uid LIMIT 2 $$) AS (sample agtype);
SELECT pg_size_pretty(pg_total_relation_size('rel.person')) AS rel_person_size, pg_size_pretty(pg_total_relation_size('rel.knows')) AS rel_knows_size,
       pg_size_pretty(pg_total_relation_size('bench."Person"')) AS age_person_size, pg_size_pretty(pg_total_relation_size('bench."KNOWS"')) AS age_knows_size;
