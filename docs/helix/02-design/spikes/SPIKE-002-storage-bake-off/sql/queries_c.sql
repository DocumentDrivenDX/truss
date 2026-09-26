-- q1_fetch (instantiated from generic template)
SELECT id, props::text, retained::text FROM c.object o
  WHERE o.type_id = 1 AND ((o.props->>'1')::bigint) = :k;

-- q2_hop1 (instantiated from generic template)
SELECT x.id, x.props::text FROM c.object s
  JOIN c.edge e0 ON e0.source_id = s.id AND e0.rel_type_id = 3
  JOIN c.object x ON x.id = e0.target_id
  WHERE s.type_id = 3 AND ((s.props->>'12')::bigint) = :k;

-- q3_hop2 (instantiated from generic template)
SELECT x.id, x.props::text FROM c.object s
  JOIN c.edge e0 ON e0.target_id = s.id AND e0.rel_type_id = 2
  JOIN c.edge e1 ON e1.source_id = e0.source_id AND e1.rel_type_id = 3
  JOIN c.object x ON x.id = e1.target_id
  WHERE s.type_id = 1 AND ((s.props->>'1')::bigint) = :k;

-- q4_hop3 (instantiated from generic template)
SELECT x.id, x.props::text FROM c.object s
  JOIN c.edge e0 ON e0.target_id = s.id AND e0.rel_type_id = 2
  JOIN c.edge e1 ON e1.source_id = e0.source_id AND e1.rel_type_id = 3
  JOIN c.edge e2 ON e2.source_id = e1.target_id AND e2.rel_type_id = 4
  JOIN c.object x ON x.id = e2.target_id
  WHERE s.type_id = 1 AND ((s.props->>'1')::bigint) = :k;

-- q5_range (instantiated from generic template)
SELECT id, props::text FROM c.object
  WHERE type_id = 3 AND ((props->>'16')::numeric) BETWEEN :lo AND :lo + 10;

-- q6_update (instantiated from generic template)
WITH old AS (SELECT o.id, o.props->'14' AS v FROM c.object o WHERE o.type_id = 3 AND ((o.props->>'12')::bigint) = :k FOR NO KEY UPDATE),
  upd AS (UPDATE c.object o SET props = jsonb_set(o.props, '{14}', to_jsonb(:s::text)) FROM old WHERE o.id = old.id RETURNING o.id)
INSERT INTO c.journal (object_id, prop_id, op, old_value, new_value, rev, origin)
  SELECT old.id, 14, 'set', old.v, to_jsonb(:s::text), 0, 'bench' FROM old JOIN upd USING (id);

-- q6_update_nojournal (instantiated from generic template)
UPDATE c.object o SET props = jsonb_set(o.props, '{14}', to_jsonb(:s::text)) WHERE o.type_id = 3 AND ((o.props->>'12')::bigint) = :k;
