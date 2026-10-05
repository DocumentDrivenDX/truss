-- Self-asserting check for storage-layout.sql. Run on an empty database after the layout.
-- Each block raises an exception when an expected behavior does not hold.
-- Run: psql -v ON_ERROR_STOP=1 -f storage-layout.sql -f storage-layout.check.sql

-- journal partitions are created ahead of time; there is no default partition
CREATE TABLE truss.journal_current PARTITION OF truss.journal
  FOR VALUES FROM (date_trunc('month', now() - interval '1 month')) TO (date_trunc('month', now() + interval '2 months'));

INSERT INTO truss.schema_rev VALUES (1, now(), '{}');
UPDATE truss.schema_head SET rev = 1 WHERE id = 1;
INSERT INTO truss.schema_doc VALUES (1, 0, 'doc', 'r1', '0.7.0', 'sha', '{}', '{}');
INSERT INTO truss.type_def (type_id, module, element, kind, since_rev, doc_ord) VALUES
  (1, 'm', 'Solution', 'record', 1, 0), (2, 'm', 'UseCase', 'record', 1, 0), (3, 'm', 'Product', 'record', 1, 0);
INSERT INTO truss.type_def (type_id, module, element, kind, provisional, since_rev) VALUES
  (5, 'm', 'Ghost', 'record', true, 1);
INSERT INTO truss.prop_def (prop_id, type_id, element, name, scalar_type, nullability, cardinality, since_rev, doc_ord) VALUES
  (10, 1, 'Solution.name', 'name', 'string', 'required', 'one', 1, 0),
  (11, 2, 'Solution.name', 'name', 'string', 'required', 'one', 1, 0);  -- same element text on another type is allowed
INSERT INTO truss.key_def VALUES (1, 'primary', 1, ARRAY[10], true, 1, NULL), (2, 'primary', 1, ARRAY[11], true, 1, NULL);
INSERT INTO truss.rel_def (rel_type_id, module, rel_id, name, source_min, source_max, target_min, target_max,
                           lifecycle, directed, since_rev, doc_ord)
  VALUES (1, 'm', 'addresses', 'addresses', 0, NULL, 0, NULL, 'independent', true, 1, 0);
INSERT INTO truss.rel_endpoint VALUES (1, 1, 2);

DO $$
DECLARE s bigint; u bigint; p bigint; e bigint; c bigint; n int;
BEGIN
  -- the catalog head: revision 0 at the start, read with FOR SHARE, updated in place
  SELECT count(*) INTO n FROM truss.schema_head WHERE id = 1 AND rev = 1;
  IF n <> 1 THEN RAISE EXCEPTION 'schema_head not at revision 1'; END IF;
  PERFORM rev FROM truss.schema_head WHERE id = 1 FOR SHARE;
  BEGIN
    INSERT INTO truss.schema_head VALUES (2, 1);
    RAISE EXCEPTION 'a second head row was accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;

  INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"lease"}', 1) RETURNING id INTO s;
  INSERT INTO truss.object (type_id, props, rev) VALUES (2, '{}', 1) RETURNING id INTO u;
  INSERT INTO truss.object (type_id, props, rev) VALUES (3, '{}', 1) RETURNING id INTO p;

  -- a type with no objects, and a provisional type, need nothing but catalog rows
  INSERT INTO truss.object (type_id, props, rev) VALUES (5, '{}', 1);

  -- ids and edge ids share one sequence
  INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev)
    VALUES (1, s, 1, u, 2, 1) RETURNING id INTO e;
  IF e <= p THEN RAISE EXCEPTION 'edge id % not drawn from the shared sequence', e; END IF;

  -- maximum multiplicity of one: a second edge for the same source is refused, and the row goes with its edge
  INSERT INTO truss.edge_limit VALUES (1, 's', s, e);
  BEGIN
    INSERT INTO truss.edge_limit VALUES (1, 's', s, e);
    RAISE EXCEPTION 'a second edge_limit row for one source was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;

  -- one edge per relationship, source and target; a second relationship between the same records is allowed
  BEGIN
    INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES (1, s, 1, u, 2, 1);
    RAISE EXCEPTION 'a second edge for one relationship, source and target was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  INSERT INTO truss.rel_def (rel_type_id, module, rel_id, name, source_min, source_max, target_min, target_max,
                             lifecycle, directed, since_rev, doc_ord)
    VALUES (2, 'm', 'supersedes', 'supersedes', 0, NULL, 0, NULL, 'independent', true, 1, 0);
  INSERT INTO truss.rel_endpoint VALUES (2, 1, 2);
  INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES (2, s, 1, u, 2, 1);

  -- endpoint types are enforced by the database
  BEGIN
    INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES (1, s, 1, p, 3, 1);
    RAISE EXCEPTION 'edge to a disallowed endpoint type was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  BEGIN
    INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES (1, s, 1, 999999, 2, 1);
    RAISE EXCEPTION 'edge to a missing object was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  -- an object with edges cannot be deleted
  BEGIN
    DELETE FROM truss.object WHERE id = s;
    RAISE EXCEPTION 'object with an edge was deleted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  -- the same id with another type is a different key and is not an object
  BEGIN
    INSERT INTO truss.edge (rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES (1, s, 2, p, 3, 1);
    RAISE EXCEPTION 'edge with a wrong source type was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;

  -- key identity: unique per (type, key, value), exact text, one key row per object per key
  INSERT INTO truss.object_key VALUES (1, 1, 'lease', s);
  INSERT INTO truss.object_key VALUES (2, 1, 'lease', u);          -- same text, another type: distinct
  BEGIN
    INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"lease"}', 1) RETURNING id INTO c;
    INSERT INTO truss.object_key VALUES (1, 1, 'lease', c);
    RAISE EXCEPTION 'duplicate key was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"Lease"}', 1) RETURNING id INTO c;
  INSERT INTO truss.object_key VALUES (1, 1, 'Lease', c);           -- case differs: distinct
  BEGIN
    INSERT INTO truss.object_key VALUES (1, 1, 'other', s);
    RAISE EXCEPTION 'a second key row for one object and key was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  BEGIN
    INSERT INTO truss.object_key VALUES (1, 1, 'ghost', 999999);
    RAISE EXCEPTION 'key row for a missing object was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  BEGIN
    INSERT INTO truss.object_key VALUES (1, 9, 'x', c);
    RAISE EXCEPTION 'key row for an undefined key was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  -- deleting an object removes its key row, so the value can be used again
  DELETE FROM truss.object WHERE id = c AND type_id = 1;
  SELECT count(*) INTO n FROM truss.object_key WHERE object_id = c; IF n <> 0 THEN RAISE EXCEPTION 'key row survived its object'; END IF;
  INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"Lease"}', 1) RETURNING id INTO c;
  INSERT INTO truss.object_key VALUES (1, 1, 'Lease', c);

  -- a composed object carries its root by (id, type); a root that does not exist is refused; both or neither
  INSERT INTO truss.object (type_id, props, rev, root_id, root_type) VALUES (2, '{}', 1, s, 1);
  BEGIN
    INSERT INTO truss.object (type_id, props, rev, root_id, root_type) VALUES (2, '{}', 1, 999999, 1);
    RAISE EXCEPTION 'object with a missing root was accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  BEGIN
    INSERT INTO truss.object (type_id, props, rev, root_id) VALUES (2, '{}', 1, s);
    RAISE EXCEPTION 'root_id without root_type was accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;

  -- props must be a JSON object; explicit null survives; SQL NULL is refused; large integers survive as text
  BEGIN
    INSERT INTO truss.object (type_id, props, rev) VALUES (2, '[1]', 1);
    RAISE EXCEPTION 'non-object props accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  UPDATE truss.object SET props = jsonb_set(props, '{10}', 'null'::jsonb) WHERE id = s AND type_id = 1;
  SELECT count(*) INTO n FROM truss.object WHERE id = s AND props ? '10' AND props -> '10' = 'null'::jsonb;
  IF n <> 1 THEN RAISE EXCEPTION 'explicit null was not preserved'; END IF;
  BEGIN
    UPDATE truss.object SET props = jsonb_set(props, '{10}', NULL) WHERE id = s AND type_id = 1;
    RAISE EXCEPTION 'SQL NULL props accepted';
  EXCEPTION WHEN not_null_violation THEN NULL; END;
  UPDATE truss.object SET props = '{"10":9007199254740993}' WHERE id = s AND type_id = 1;
  SELECT count(*) INTO n FROM truss.object WHERE id = s AND (props ->> '10') = '9007199254740993';
  IF n <> 1 THEN RAISE EXCEPTION 'integer beyond 2^53 changed'; END IF;

  -- a request id in the journal origin is found by its partial index, and rows without one are not indexed
  INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev, origin)
    VALUES ('o', 777777, 1, 3, 'update', 1, '{"request":{"id":"r-1","hash":"h"}}');
  SELECT count(*) INTO n FROM truss.journal WHERE origin ? 'request' AND origin #>> '{request,id}' = 'r-1';
  IF n <> 1 THEN RAISE EXCEPTION 'request id lookup found % rows', n; END IF;
  SELECT count(*) INTO n FROM pg_indexes WHERE schemaname = 'truss' AND tablename = 'journal' AND indexname = 'journal_request';
  IF n <> 1 THEN RAISE EXCEPTION 'journal_request index missing'; END IF;

  -- a feed consumer has one position
  INSERT INTO truss.feed_consumer VALUES ('c1', '0'::xid8, 0);
  BEGIN
    INSERT INTO truss.feed_consumer VALUES ('c1', '1'::xid8, 1);
    RAISE EXCEPTION 'a second position for one consumer was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;

  -- a revision records who accepted it, as a JSON object
  BEGIN
    INSERT INTO truss.schema_rev (rev, report, origin) VALUES (90, '{}', '[]');
    RAISE EXCEPTION 'a non-object revision origin was accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;

  -- a tombstone reserves a key text and cannot be written twice; a tombstone for an edge has key_num 0
  INSERT INTO truss.key_tombstone (entity_kind, type_id, key_num, k, entity_id, ver) VALUES ('o', 1, 1, 'gone', s, 2);
  BEGIN
    INSERT INTO truss.key_tombstone (entity_kind, type_id, key_num, k, entity_id, ver) VALUES ('o', 1, 1, 'gone', s, 3);
    RAISE EXCEPTION 'a second tombstone for one key was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  BEGIN
    INSERT INTO truss.key_tombstone (entity_kind, type_id, key_num, k, entity_id, ver) VALUES ('e', 1, 1, '["1","2"]', e, 2);
    RAISE EXCEPTION 'an edge tombstone with key_num 1 was accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  -- record_source holds one row per record and a JSON object
  INSERT INTO truss.record_source (entity_kind, entity_id, load_id, source) VALUES ('o', s, 'load-1', '{"author":"a","at":"2026-08-14"}');
  BEGIN
    INSERT INTO truss.record_source (entity_kind, entity_id, load_id) VALUES ('o', s, 'load-2');
    RAISE EXCEPTION 'a second record_source row for one record was accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  BEGIN
    INSERT INTO truss.record_source (entity_kind, entity_id, load_id, source) VALUES ('o', 99999, 'load-1', '[]');
    RAISE EXCEPTION 'a non-object source was accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;

  -- the journal accepts rows, routes by time, and refuses a time no partition covers
  INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev, origin)
    VALUES ('o', s, 1, 1, 'create', 1, '{"actor":"t"}'), ('o', s, 1, 2, 'update', 1, '{}');
  SELECT count(*) INTO n FROM truss.journal WHERE entity_kind = 'o' AND entity_id = s;
  IF n <> 2 THEN RAISE EXCEPTION 'journal rows missing'; END IF;
  BEGIN
    INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev) VALUES ('x', 1, 1, 1, 'create', 1);
    RAISE EXCEPTION 'bad entity_kind accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  BEGIN
    INSERT INTO truss.journal (at, entity_kind, entity_id, entity_type, ver, op, rev)
      VALUES (now() + interval '10 years', 'o', 1, 1, 1, 'create', 1);
    RAISE EXCEPTION 'journal row accepted with no partition';
  EXCEPTION WHEN check_violation THEN NULL; END;

  -- settings and the type listing index
  SELECT count(*) INTO n FROM truss.setting WHERE key = 'key_reuse' AND value = '"forbid"';
  IF n <> 1 THEN RAISE EXCEPTION 'key_reuse setting missing'; END IF;
  SELECT count(*) INTO n FROM truss.setting WHERE key = 'journal_mode' AND value = '"engine"';
  IF n <> 1 THEN RAISE EXCEPTION 'journal_mode setting missing'; END IF;
  SELECT count(*) INTO n FROM pg_indexes WHERE schemaname = 'truss' AND tablename = 'object' AND indexname = 'object_type_id';
  IF n <> 1 THEN RAISE EXCEPTION 'object_type_id index missing'; END IF;
  -- no table of the layout is partitioned except the journal
  SELECT count(*) INTO n FROM pg_partitioned_table pt JOIN pg_class c ON c.oid = pt.partrelid
    WHERE c.relnamespace = 'truss'::regnamespace AND c.relname <> 'journal';
  IF n <> 0 THEN RAISE EXCEPTION 'unexpected partitioned table'; END IF;
END $$;
SELECT 'storage-layout check passed' AS result;
