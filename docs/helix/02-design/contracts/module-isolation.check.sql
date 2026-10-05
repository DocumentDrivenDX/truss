-- Self-asserting check for module-isolation.sql. Run on an empty database after storage-layout.sql and the
-- layout check has NOT been run (this file builds its own catalog), then module-isolation.sql.
-- Run: psql -v ON_ERROR_STOP=1 -f storage-layout.sql -f module-isolation.sql -f module-isolation.check.sql
-- Run as a superuser, which bypasses row-level security; the checks set a role to see what it sees.

CREATE TABLE truss.journal_current PARTITION OF truss.journal
  FOR VALUES FROM (date_trunc('month', now() - interval '1 month')) TO (date_trunc('month', now() + interval '2 months'));
INSERT INTO truss.schema_rev VALUES (1, now(), '{}');
UPDATE truss.schema_head SET rev = 1 WHERE id = 1;
INSERT INTO truss.schema_doc VALUES (1, 0, 'doc', 'r1', '0.7.0', 'sha', '{}', '{}');
INSERT INTO truss.type_def (type_id, module, element, kind, since_rev, doc_ord) VALUES
  (1, 'a', 'Solution', 'record', 1, 0), (2, 'a', 'UseCase', 'record', 1, 0), (3, 'b', 'Product', 'record', 1, 0);
INSERT INTO truss.prop_def (prop_id, type_id, element, name, scalar_type, nullability, cardinality, since_rev, doc_ord) VALUES
  (10, 1, 'Solution.name', 'name', 'string', 'required', 'one', 1, 0), (11, 3, 'Product.name', 'name', 'string', 'required', 'one', 1, 0);
INSERT INTO truss.rel_def (rel_type_id, module, rel_id, name, source_min, source_max, target_min, target_max, lifecycle, directed, since_rev, doc_ord) VALUES
  (1, 'a', 'addresses', 'addresses', 0, NULL, 0, NULL, 'independent', true, 1, 0),
  (2, 'a', 'built_on', 'built_on', 0, NULL, 0, NULL, 'independent', true, 1, 0);
INSERT INTO truss.rel_endpoint VALUES (1, 1, 2), (2, 1, 3);

DROP ROLE IF EXISTS iso_ra; DROP ROLE IF EXISTS iso_wa; DROP ROLE IF EXISTS iso_wb;
CREATE ROLE iso_ra NOLOGIN; CREATE ROLE iso_wa NOLOGIN; CREATE ROLE iso_wb NOLOGIN;
-- iso_ra reads both modules (a shared reader); iso_wa writes a; iso_wb writes b.
INSERT INTO truss.module_access VALUES ('a', 'iso_ra', 'iso_wa'), ('b', 'iso_ra', 'iso_wb');
SELECT truss.grant_module_roles('a', true); SELECT truss.grant_module_roles('b', true);

INSERT INTO truss.object (id, type_id, props, rev) VALUES (101, 1, '{"10":"s"}', 1), (102, 2, '{}', 1), (103, 3, '{"11":"p"}', 1);
INSERT INTO truss.edge (id, rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES
  (201, 1, 101, 1, 102, 2, 1), (202, 2, 101, 1, 103, 3, 1);
INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev) VALUES ('o', 101, 1, 1, 'create', 1), ('o', 103, 3, 1, 'create', 1), ('e', 202, 2, 1, 'create', 1);
INSERT INTO truss.record_source (entity_kind, entity_id, load_id) VALUES ('o', 101, 'l1'), ('o', 103, 'l1');

DO $$
DECLARE n int;
BEGIN
  -- acting role: the role set for the transaction
  SET LOCAL ROLE iso_wa;
  IF truss.acting_role() <> 'iso_wa' THEN RAISE EXCEPTION 'acting_role is %', truss.acting_role(); END IF;

  -- the writer of a sees module a's objects and catalog, not b's
  SELECT count(*) INTO n FROM truss.object; IF n <> 2 THEN RAISE EXCEPTION 'wa sees % objects', n; END IF;
  SELECT count(*) INTO n FROM truss.type_def; IF n <> 2 THEN RAISE EXCEPTION 'wa sees % types', n; END IF;
  SELECT count(*) INTO n FROM truss.prop_def; IF n <> 1 THEN RAISE EXCEPTION 'wa sees % props', n; END IF;
  SELECT count(*) INTO n FROM truss.module_access; IF n <> 1 THEN RAISE EXCEPTION 'wa sees % access rows', n; END IF;
  -- an edge to another module's object is invisible, and so is its journal row's object
  SELECT count(*) INTO n FROM truss.edge; IF n <> 1 THEN RAISE EXCEPTION 'wa sees % edges', n; END IF;
  SELECT count(*) INTO n FROM truss.journal WHERE entity_kind = 'o'; IF n <> 1 THEN RAISE EXCEPTION 'wa sees % journal rows', n; END IF;
  SELECT count(*) INTO n FROM truss.record_source; IF n <> 1 THEN RAISE EXCEPTION 'wa sees % sources', n; END IF;
  -- schema documents are not readable at all
  BEGIN PERFORM 1 FROM truss.schema_doc; RAISE EXCEPTION 'wa read schema_doc'; EXCEPTION WHEN insufficient_privilege THEN NULL; END;

  -- writes: its own module only
  INSERT INTO truss.object (id, type_id, props, rev) VALUES (104, 1, '{"10":"t"}', 1);
  BEGIN INSERT INTO truss.object (id, type_id, props, rev) VALUES (105, 3, '{"11":"q"}', 1); RAISE EXCEPTION 'wa wrote module b';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  UPDATE truss.object SET ver = ver + 1 WHERE id = 103; GET DIAGNOSTICS n = ROW_COUNT; IF n <> 0 THEN RAISE EXCEPTION 'wa updated b''s object'; END IF;
  DELETE FROM truss.object WHERE id = 103; GET DIAGNOSTICS n = ROW_COUNT; IF n <> 0 THEN RAISE EXCEPTION 'wa deleted b''s object'; END IF;
  -- an edge from a to a is allowed; an edge to b is refused because wa cannot read b
  INSERT INTO truss.edge (id, rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES (203, 1, 104, 1, 102, 2, 1);
  BEGIN INSERT INTO truss.edge (id, rel_type_id, source_id, source_type, target_id, target_type, rev) VALUES (204, 2, 104, 1, 103, 3, 1); RAISE EXCEPTION 'wa created an edge into b';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev) VALUES ('o', 104, 1, 1, 'create', 1);
  BEGIN INSERT INTO truss.journal (entity_kind, entity_id, entity_type, ver, op, rev) VALUES ('o', 103, 3, 2, 'update', 1); RAISE EXCEPTION 'wa journaled b';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  RESET ROLE;

  -- the shared reader sees both modules and the edge between them, and cannot write
  SET LOCAL ROLE iso_ra;
  SELECT count(*) INTO n FROM truss.object; IF n <> 4 THEN RAISE EXCEPTION 'ra sees % objects', n; END IF;
  SELECT count(*) INTO n FROM truss.edge; IF n <> 3 THEN RAISE EXCEPTION 'ra sees % edges', n; END IF;
  SELECT count(*) INTO n FROM truss.module_access; IF n <> 2 THEN RAISE EXCEPTION 'ra sees % access rows', n; END IF;
  BEGIN INSERT INTO truss.object (id, type_id, props, rev) VALUES (106, 1, '{}', 1); RAISE EXCEPTION 'a reader wrote';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  RESET ROLE;

  -- the writer of b sees b only, and no edge, since every edge touches a
  SET LOCAL ROLE iso_wb;
  SELECT count(*) INTO n FROM truss.object; IF n <> 1 THEN RAISE EXCEPTION 'wb sees % objects', n; END IF;
  SELECT count(*) INTO n FROM truss.edge; IF n <> 0 THEN RAISE EXCEPTION 'wb sees % edges', n; END IF;
  RESET ROLE;

  -- a role with no module sees nothing
  CREATE ROLE iso_none NOLOGIN; GRANT USAGE ON SCHEMA truss TO iso_none; GRANT SELECT ON truss.object, truss.type_def, truss.module_access TO iso_none;
  SET LOCAL ROLE iso_none;
  SELECT count(*) INTO n FROM truss.object; IF n <> 0 THEN RAISE EXCEPTION 'a role without a module sees % objects', n; END IF;
  SELECT count(*) INTO n FROM truss.type_def; IF n <> 0 THEN RAISE EXCEPTION 'a role without a module sees % types', n; END IF;
  RESET ROLE;
END $$;
SELECT 'module-isolation check passed' AS result;
