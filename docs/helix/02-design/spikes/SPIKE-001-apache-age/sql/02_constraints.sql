-- C4: can ordinary PostgreSQL constraints on AGE label tables enforce declared rules,
-- and do Cypher CREATE / MERGE / SET honour them? (AGE 1.8.0, PostgreSQL 18.6)
\pset pager off
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
SELECT drop_graph('con', true) FROM ag_graph WHERE name = 'con';
SELECT create_graph('con');
DROP TABLE IF EXISTS public.trigger_log; DROP FUNCTION IF EXISTS public.log_person();
SELECT create_vlabel('con', 'Person');
SELECT create_vlabel('con', 'Order');
SELECT create_elabel('con', 'PLACED');

\echo '==== DDL on label tables'
-- unique key on a property (expression index; this is the expression Cypher generates for n.email)
CREATE UNIQUE INDEX person_email_uq ON con."Person" (agtype_access_operator(VARIADIC ARRAY[properties, '"email"'::agtype]));
-- required property
ALTER TABLE con."Person" ADD CONSTRAINT person_name_required CHECK (properties ? 'name'::text);
-- value limit (only when present)
ALTER TABLE con."Person" ADD CONSTRAINT person_age_range CHECK (NOT properties ? 'age'::text OR ((properties -> 'age'::text)::int BETWEEN 0 AND 150));
-- row trigger: does Cypher fire it?
CREATE TABLE public.trigger_log(at timestamptz default now(), tg_op text, props text);
CREATE FUNCTION public.log_person() RETURNS trigger LANGUAGE plpgsql AS $f$
BEGIN INSERT INTO public.trigger_log(tg_op, props) VALUES (TG_OP, NEW.properties::text); RETURN NEW; END $f$;
CREATE TRIGGER person_row_trg BEFORE INSERT OR UPDATE ON con."Person" FOR EACH ROW EXECUTE FUNCTION public.log_person();
-- edge endpoint restriction, variant 1: foreign keys (implemented by PostgreSQL as triggers)
ALTER TABLE con."PLACED" ADD CONSTRAINT placed_start_fk FOREIGN KEY (start_id) REFERENCES con."Person"(id);
ALTER TABLE con."PLACED" ADD CONSTRAINT placed_end_fk FOREIGN KEY (end_id) REFERENCES con."Order"(id);
\d con."Person"
\d con."PLACED"

\echo '==== C4.1 CREATE honours unique / required / range?'
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'Ann', email: 'a@x.com', age: 30}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'Dup', email: 'a@x.com'}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {email: 'noname@x.com'}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'Old', email: 'old@x.com', age: 200}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'Str', email: 'str@x.com', age: 'thirty'}) RETURN p.email $$) AS (e agtype);

\echo '==== C4.2 binary equality of the unique key: case and Unicode normalization'
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'Upper', email: 'A@x.com'}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'Pre', email: 'josé@x.com'}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'Comb', email: 'josé@x.com'}) RETURN p.email $$) AS (e agtype);
\echo '-- same number, different agtype numeric kinds: does 1 = 1.0 = 1::numeric collide in the unique index?'
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'I1', email: 1}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'F1', email: 1.0}) RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ CREATE (p:Person {name: 'N1', email: 1::numeric}) RETURN p.email $$) AS (e agtype);

\echo '==== C4.3 MERGE against the unique key'
SELECT * FROM cypher('con', $$ MERGE (p:Person {email: 'a@x.com'}) RETURN p.name $$) AS (n agtype);
SELECT * FROM cypher('con', $$ MERGE (p:Person {email: 'a@x.com', name: 'Different'}) RETURN p.name $$) AS (n agtype);
SELECT * FROM cypher('con', $$ MERGE (p:Person {email: 'm@x.com'}) ON CREATE SET p.name = 'Merged' RETURN p.name $$) AS (n agtype);

\echo '==== C4.4 SET / REMOVE honour the constraints?'
SELECT * FROM cypher('con', $$ MATCH (p:Person {name: 'Upper'}) SET p.email = 'a@x.com' RETURN p.email $$) AS (e agtype);
SELECT * FROM cypher('con', $$ MATCH (p:Person {name: 'Ann'}) SET p.age = -1 RETURN p.age $$) AS (a agtype);
SELECT * FROM cypher('con', $$ MATCH (p:Person {name: 'Ann'}) REMOVE p.name RETURN p $$) AS (p agtype);
SELECT * FROM cypher('con', $$ MATCH (p:Person {email: 'a@x.com'}) SET p.name = null RETURN p $$) AS (p agtype);

\echo '==== C4.5 did the BEFORE ROW trigger fire for Cypher writes?'
SELECT tg_op, props FROM public.trigger_log ORDER BY at;
SELECT * FROM cypher('con', $$ MATCH (p:Person) RETURN p.name, p.email ORDER BY p.name $$) AS (name agtype, email agtype);

\echo '==== C4.6 edge endpoints: foreign keys (trigger-based) under Cypher CREATE'
SELECT * FROM cypher('con', $$ CREATE (o:Order {no: 1}) RETURN o.no $$) AS (o agtype);
-- allowed direction Person -> Order
SELECT * FROM cypher('con', $$ MATCH (p:Person {email: 'a@x.com'}), (o:Order {no: 1}) CREATE (p)-[r:PLACED]->(o) RETURN type(r) $$) AS (r agtype);
-- wrong direction Order -> Person should violate both FKs
SELECT * FROM cypher('con', $$ MATCH (p:Person {email: 'a@x.com'}), (o:Order {no: 1}) CREATE (o)-[r:PLACED]->(p) RETURN type(r) $$) AS (r agtype);
SELECT _label_name((SELECT graphid FROM ag_graph WHERE name='con'), start_id) AS start_label, _label_name((SELECT graphid FROM ag_graph WHERE name='con'), end_id) AS end_label FROM con."PLACED";
\echo '-- same wrong edge through plain SQL INSERT (PostgreSQL enforces the FK here)'
INSERT INTO con."PLACED"(start_id, end_id) SELECT o.id, p.id FROM con."Order" o, con."Person" p WHERE p.properties @> '{"email":"a@x.com"}' LIMIT 1;
\echo '-- delete the Order vertex that an edge references (FK should block)'
SELECT * FROM cypher('con', $$ MATCH (o:Order {no: 1}) DELETE o $$) AS (x agtype);
SELECT * FROM cypher('con', $$ MATCH (o:Order {no: 1}) DETACH DELETE o $$) AS (x agtype);

\echo '==== C4.7 edge endpoints, variant 2: CHECK on the label id encoded in the graphid'
ALTER TABLE con."PLACED" DROP CONSTRAINT placed_start_fk, DROP CONSTRAINT placed_end_fk;
DO $d$ BEGIN
  EXECUTE format('ALTER TABLE con."PLACED" ADD CONSTRAINT placed_endpoint_labels CHECK (_extract_label_id(start_id) = %s AND _extract_label_id(end_id) = %s)',
                 _label_id('con','Person'), _label_id('con','Order'));
END $d$;
DELETE FROM con."PLACED";
SELECT * FROM cypher('con', $$ CREATE (o:Order {no: 2}) RETURN o.no $$) AS (o agtype);
SELECT * FROM cypher('con', $$ MATCH (p:Person {email: 'a@x.com'}), (o:Order {no: 2}) CREATE (p)-[r:PLACED]->(o) RETURN type(r) $$) AS (r agtype);
SELECT * FROM cypher('con', $$ MATCH (p:Person {email: 'a@x.com'}), (o:Order {no: 2}) CREATE (o)-[r:PLACED]->(p) RETURN type(r) $$) AS (r agtype);
SELECT count(*) AS placed_edges FROM con."PLACED";
