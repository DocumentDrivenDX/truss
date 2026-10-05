-- Self-asserting check for storage-layout.sql. Run on an empty database after the layout.
-- Each block raises an exception when an expected behavior does not hold.
-- Run: psql -v ON_ERROR_STOP=1 -f storage-layout.sql -f storage-layout.check.sql

INSERT INTO truss.schema_rev VALUES (1, now(), '{}');
INSERT INTO truss.type_def (type_id, module, element, kind, since_rev) VALUES
  (1, 'm', 'Solution', 'record', 1), (2, 'm', 'UseCase', 'record', 1), (3, 'm', 'Product', 'record', 1);
INSERT INTO truss.prop_def (prop_id, type_id, element, name, scalar_type, nullability, cardinality, since_rev) VALUES
  (10, 1, 'm.Solution.name', 'name', 'string', 'required', 'one', 1);
INSERT INTO truss.rel_def (rel_type_id, module, rel_id, name, source_min, source_max, target_min, target_max,
                           lifecycle, directed, since_rev)
  VALUES (1, 'm', 'addresses', 'addresses', 0, NULL, 0, NULL, 'independent', true, 1);
INSERT INTO truss.rel_endpoint VALUES (1, 1, 2);

-- Declared partition and key index for type 1, created when the type is accepted.
CREATE TABLE truss.object_t1 PARTITION OF truss.object FOR VALUES IN (1);
CREATE UNIQUE INDEX object_t1_key ON truss.object_t1 (((props ->> '10') COLLATE "C"));

DO $$
DECLARE s bigint; u bigint; p bigint; e bigint; n int; part text;
BEGIN
  INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"lease"}', 1) RETURNING id INTO s;
  INSERT INTO truss.object (type_id, props, rev) VALUES (2, '{}', 1) RETURNING id INTO u;
  INSERT INTO truss.object (type_id, props, rev) VALUES (3, '{}', 1) RETURNING id INTO p;

  -- rows route to the declared partition, and an undeclared type falls into the default partition
  SELECT tableoid::regclass::text INTO part FROM truss.object WHERE id = s;
  IF part <> 'truss.object_t1' THEN RAISE EXCEPTION 'type 1 not routed to its partition: %', part; END IF;
  SELECT tableoid::regclass::text INTO part FROM truss.object WHERE id = u;
  IF part <> 'truss.object_default' THEN RAISE EXCEPTION 'type 2 not in default partition: %', part; END IF;

  -- ids and edge ids share one sequence
  INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev)
    VALUES (1, s, 1, u, 2, 1) RETURNING id INTO e;
  IF e <= p THEN RAISE EXCEPTION 'edge id % not drawn from the shared sequence', e; END IF;

  -- endpoint types are enforced by the database
  BEGIN
    INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev)
      VALUES (1, s, 1, p, 3, 1);
    RAISE EXCEPTION 'edge to a disallowed endpoint type was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;

  -- an edge to a missing object is refused
  BEGIN
    INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev)
      VALUES (1, s, 1, 999999, 2, 1);
    RAISE EXCEPTION 'edge to a missing object was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;

  -- an object with edges cannot be deleted
  BEGIN
    DELETE FROM truss.object WHERE id = s;
    RAISE EXCEPTION 'object with an edge was deleted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;

  -- the same id with another type is a different key and is not an object
  BEGIN
    INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev)
      VALUES (1, s, 2, u, 2, 1);
    RAISE EXCEPTION 'edge with a wrong source type was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;

  -- unique business key per declared type, exact comparison
  BEGIN
    INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"lease"}', 1);
    RAISE EXCEPTION 'duplicate key was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"Lease"}', 1);   -- case differs: distinct

  -- props must be a JSON object; explicit null survives; absent differs from null
  BEGIN
    INSERT INTO truss.object (type_id, props, rev) VALUES (2, '[1]', 1);
    RAISE EXCEPTION 'non-object props accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  UPDATE truss.object SET props = jsonb_set(props, '{10}', 'null'::jsonb) WHERE id = s;
  SELECT count(*) INTO n FROM truss.object WHERE id = s AND props ? '10' AND props -> '10' = 'null'::jsonb;
  IF n <> 1 THEN RAISE EXCEPTION 'explicit null was not preserved'; END IF;
  BEGIN
    UPDATE truss.object SET props = jsonb_set(props, '{10}', NULL) WHERE id = s;   -- SQL NULL erases the map
    RAISE EXCEPTION 'SQL NULL props accepted';
  EXCEPTION WHEN not_null_violation THEN NULL; END;

  -- large integers survive when read as text
  UPDATE truss.object SET props = '{"10":9007199254740993}' WHERE id = s;
  SELECT count(*) INTO n FROM truss.object WHERE id = s AND (props ->> '10') = '9007199254740993';
  IF n <> 1 THEN RAISE EXCEPTION 'integer beyond 2^53 changed'; END IF;

  -- the journal accepts rows, routes by time, and orders per entity by version
  INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev, origin)
    VALUES ('o', s, 1, 1, 'create', 1, '{"actor":"t"}'), ('o', s, 1, 2, 'update', 1, '{}');
  SELECT count(*) INTO n FROM truss.journal WHERE entity_kind = 'o' AND entity_id = s;
  IF n <> 2 THEN RAISE EXCEPTION 'journal rows missing'; END IF;
  BEGIN
    INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev) VALUES ('x', 1, 1, 1, 'create', 1);
    RAISE EXCEPTION 'bad entity_kind accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;

  -- a partition for a type that already has rows in the default partition cannot be created in place
  BEGIN
    CREATE TABLE truss.object_t2 PARTITION OF truss.object FOR VALUES IN (2);
    RAISE EXCEPTION 'partition created over existing default-partition rows';
  EXCEPTION WHEN check_violation THEN NULL; END;
  -- a partition for a type with no rows is created freely
  CREATE TABLE truss.object_t4 PARTITION OF truss.object FOR VALUES IN (4);
END $$;
SELECT 'storage-layout check passed' AS result;
