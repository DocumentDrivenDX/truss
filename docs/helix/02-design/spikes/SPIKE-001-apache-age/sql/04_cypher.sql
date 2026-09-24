-- C6: Cypher read/write coverage and composition with SQL (AGE 1.8.0 / PG 18.6).
\pset pager off
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
SELECT drop_graph('cov', true) FROM ag_graph WHERE name = 'cov';
SELECT create_graph('cov');
SELECT * FROM cypher('cov', $$
  CREATE (a:Customer {cid: 1, name: 'Ann'}), (b:Customer {cid: 2, name: 'Bob'}), (c:Customer {cid: 3, name: 'Cy'}),
         (p1:Product {sku: 'P1'}), (p2:Product {sku: 'P2'}),
         (o1:Order {no: 10}), (o2:Order {no: 11}), (o3:Order {no: 12}),
         (a)-[:PLACED]->(o1), (a)-[:PLACED]->(o2), (b)-[:PLACED]->(o3),
         (o1)-[:CONTAINS {qty: 2}]->(p1), (o2)-[:CONTAINS {qty: 1}]->(p2), (o3)-[:CONTAINS {qty: 5}]->(p1),
         (a)-[:REFERRED]->(b), (b)-[:REFERRED]->(c)
$$) AS (x agtype);

\echo '==== C6.1 multi-hop pattern: customers whose orders include P1 (two hops)'
SELECT * FROM cypher('cov', $$ MATCH (c:Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(:Product {sku: 'P1'}) RETURN c.name ORDER BY c.name $$) AS (name agtype);
\echo '==== C6.2 variable-length paths'
SELECT * FROM cypher('cov', $$ MATCH (a:Customer {cid: 1})-[:REFERRED*1..3]->(x) RETURN x.name ORDER BY x.name $$) AS (name agtype);
SELECT * FROM cypher('cov', $$ MATCH p = (a:Customer {cid: 1})-[:REFERRED*]->(x) RETURN length(p), x.name ORDER BY length(p) $$) AS (len agtype, name agtype);
SELECT * FROM cypher('cov', $$ MATCH (a:Customer {cid: 1})-[*0..2]-(x) RETURN count(DISTINCT x) $$) AS (n agtype);
\echo '==== C6.3 OPTIONAL MATCH'
SELECT * FROM cypher('cov', $$ MATCH (c:Customer) OPTIONAL MATCH (c)-[:PLACED]->(o:Order) RETURN c.name, count(o) ORDER BY c.name $$) AS (name agtype, orders agtype);
\echo '==== C6.4 aggregation, collect, WITH, ORDER BY, SKIP/LIMIT'
SELECT * FROM cypher('cov', $$ MATCH (c:Customer)-[:PLACED]->(o)-[k:CONTAINS]->(p) WITH c, sum(k.qty) AS units, collect(p.sku) AS skus RETURN c.name, units, skus ORDER BY units DESC LIMIT 5 $$) AS (name agtype, units agtype, skus agtype);
\echo '==== C6.5 UNWIND, list comprehension, CASE, EXISTS subquery'
SELECT * FROM cypher('cov', $$ UNWIND [1, 2, 3, 3] AS i RETURN i, [x IN range(1, i) WHERE x % 2 = 1 | x * 10] AS odds, CASE WHEN i > 2 THEN 'big' ELSE 'small' END $$) AS (i agtype, odds agtype, size agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer) WHERE EXISTS { (c)-[:PLACED]->() } RETURN c.name ORDER BY c.name $$) AS (name agtype);
\echo '==== C6.6 parameters (prepared statement) for reads and writes'
PREPARE q_orders(agtype) AS SELECT * FROM cypher('cov', $$ MATCH (c:Customer {cid: $cid})-[:PLACED]->(o) RETURN o.no ORDER BY o.no $$, $1) AS (no agtype);
EXECUTE q_orders('{"cid": 1}');
PREPARE w_customer(agtype) AS SELECT * FROM cypher('cov', $$ CREATE (c:Customer {cid: $cid, name: $name}) RETURN c.cid $$, $1) AS (cid agtype);
EXECUTE w_customer('{"cid": 4, "name": "Dee"}');
\echo '==== C6.7 writes: update one property, SET +=, REMOVE, MERGE with ON CREATE / ON MATCH, DELETE, DETACH DELETE'
SELECT * FROM cypher('cov', $$ MATCH (c:Customer {cid: 4}) SET c.tier = 'gold' RETURN properties(c) $$) AS (p agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer {cid: 4}) SET c += {tier: 'silver', region: 'EU'} RETURN properties(c) $$) AS (p agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer {cid: 4}) REMOVE c.region RETURN properties(c) $$) AS (p agtype);
SELECT * FROM cypher('cov', $$ MERGE (c:Customer {cid: 5}) ON CREATE SET c.created = true ON MATCH SET c.matched = true RETURN properties(c) $$) AS (p agtype);
SELECT * FROM cypher('cov', $$ MERGE (c:Customer {cid: 5}) ON CREATE SET c.created = true ON MATCH SET c.matched = true RETURN properties(c) $$) AS (p agtype);
SELECT * FROM cypher('cov', $$ MATCH (a:Customer {cid: 4}), (b:Customer {cid: 5}) MERGE (a)-[r:REFERRED]->(b) RETURN type(r) $$) AS (r agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer {cid: 5}) DELETE c $$) AS (x agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer {cid: 5}) DETACH DELETE c $$) AS (x agtype);
\echo '==== C6.8 constructs expected to be missing or limited'
SELECT * FROM cypher('cov', $$ CREATE (x:A:B {k: 1}) RETURN labels(x) $$) AS (l agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer) FOREACH (x IN [1] | SET c.touched = true) $$) AS (x agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer) CALL { WITH c MATCH (c)-[:PLACED]->(o) RETURN count(o) AS n } RETURN c.name, n $$) AS (name agtype, n agtype);
SELECT * FROM cypher('cov', $$ MATCH (c:Customer) RETURN c.name, [(c)-[:PLACED]->(o) | o.no] AS orders ORDER BY c.name $$) AS (name agtype, orders agtype);
SELECT * FROM cypher('cov', $$ MATCH p = shortestPath((a:Customer {cid: 1})-[*]-(b:Customer {cid: 3})) RETURN length(p) $$) AS (len agtype);
SELECT * FROM cypher('cov', $$ MATCH (a:Customer {cid: 1}) RETURN a.name UNION MATCH (b:Customer {cid: 2}) RETURN b.name $$) AS (name agtype);
SELECT * FROM cypher('cov', $$ LOAD CSV FROM 'file:///x.csv' AS row RETURN row $$) AS (r agtype);
SELECT * FROM cypher('cov', $$ CREATE CONSTRAINT FOR (c:Customer) REQUIRE c.cid IS UNIQUE $$) AS (x agtype);
SELECT * FROM cypher('cov', $$ CREATE INDEX FOR (c:Customer) ON (c.cid) $$) AS (x agtype);
\echo '-- shortest path via the 1.8.0 SRF (signature from pg_proc; arguments probed)'
\df ag_catalog.age_shortest_path

\echo '==== C6.9 composition with SQL: join cypher() with a relational table, CTE, subquery, write inside CTE'
DROP TABLE IF EXISTS public.crm; CREATE TABLE public.crm(cid int PRIMARY KEY, segment text);
INSERT INTO public.crm VALUES (1, 'enterprise'), (2, 'smb'), (3, 'smb');
SELECT crm.segment, g.name FROM public.crm JOIN cypher('cov', $$ MATCH (c:Customer) RETURN c.cid, c.name $$) AS g(cid agtype, name agtype) ON crm.cid = g.cid::int ORDER BY 1, 2;
WITH g AS (SELECT * FROM cypher('cov', $$ MATCH (c:Customer)-[:PLACED]->(o) RETURN c.cid, count(o) $$) AS (cid agtype, n agtype))
SELECT crm.segment, sum(g.n::int) FROM g JOIN public.crm ON crm.cid = g.cid::int GROUP BY 1 ORDER BY 1;
SELECT name FROM public.crm c, LATERAL (SELECT * FROM cypher('cov', $$ MATCH (x:Customer) RETURN x.name, x.cid $$) AS (name agtype, xcid agtype)) g WHERE g.xcid::int = c.cid ORDER BY 1;
\echo '-- correlated use: pass a SQL column into cypher() as a parameter (only a constant/param is allowed as third argument)'
SELECT c.cid, g.* FROM public.crm c, LATERAL (SELECT * FROM cypher('cov', $$ MATCH (x:Customer {cid: $cid}) RETURN x.name $$, jsonb_build_object('cid', c.cid)::agtype) AS (name agtype)) g ORDER BY 1;
\echo '-- write cypher inside a JOIN (documented as unsupported) and inside a CTE'
SELECT * FROM public.crm JOIN cypher('cov', $$ CREATE (n:Tmp {v: 1}) RETURN n.v $$) AS g(v agtype) ON true;
WITH w AS (SELECT * FROM cypher('cov', $$ CREATE (n:Tmp {v: 2}) RETURN n.v $$) AS (v agtype)) SELECT * FROM w;
\echo '-- same transaction: SQL write + Cypher write roll back together'
BEGIN;
INSERT INTO public.crm VALUES (99, 'txn');
SELECT * FROM cypher('cov', $$ CREATE (n:Customer {cid: 99}) RETURN n.cid $$) AS (c agtype);
ROLLBACK;
SELECT (SELECT count(*) FROM public.crm WHERE cid = 99) AS sql_rows, (SELECT count(*) FROM cypher('cov', $$ MATCH (n:Customer {cid: 99}) RETURN n $$) AS (n agtype)) AS graph_rows;

\echo '==== nice-to-have: shortest path via the age_shortest_path SRF (added in 1.8.0, #2430)'
SELECT path FROM age_shortest_path('"cov"'::agtype,
    (SELECT id FROM cypher('cov', $$ MATCH (n:Customer {cid: 1}) RETURN id(n) $$) AS (id agtype)),
    (SELECT id FROM cypher('cov', $$ MATCH (n:Customer {cid: 3}) RETURN id(n) $$) AS (id agtype))) AS path;
