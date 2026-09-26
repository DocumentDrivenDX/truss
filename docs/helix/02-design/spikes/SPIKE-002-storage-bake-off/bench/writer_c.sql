\set c random(1, 20000)
\set p random(1, 5000)
WITH o AS (INSERT INTO c.object (type_id, props, rev)
           VALUES (3, jsonb_build_object('12', nextval('c.key_seq'), '13', '2026-09-25T10:00:00Z', '14', 'placed', '15', 'web', '16', 20.00), 0) RETURNING id),
 cu AS (SELECT id FROM c.object WHERE type_id = 1 AND ((props->>'1')::bigint) = :c),
 e1 AS (INSERT INTO c.edge (rel_type_id, source_id, source_type, target_id, target_type) SELECT 2, o.id, 3, cu.id, 1 FROM o, cu),
 l AS (INSERT INTO c.object (type_id, props, rev)
       SELECT 4, jsonb_build_object('17', nextval('c.key_seq'), '18', g, '19', 2, '20', 5.00, '21', 10.00), 0 FROM generate_series(1, 2) g RETURNING id),
 e2 AS (INSERT INTO c.edge (rel_type_id, source_id, source_type, target_id, target_type) SELECT 3, o.id, 3, l.id, 4 FROM o, l),
 pr AS (SELECT id FROM c.object WHERE type_id = 5 AND ((props->>'22')::bigint) = :p),
 e3 AS (INSERT INTO c.edge (rel_type_id, source_id, source_type, target_id, target_type) SELECT 4, l.id, 4, pr.id, 5 FROM l, pr)
INSERT INTO c.journal (object_id, op, rev, origin) SELECT id, 'create', 0, 'writer' FROM o;
