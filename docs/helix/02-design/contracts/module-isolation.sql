-- Optional module isolation for layout 0.2 (CONTRACT-005). Apply after storage-layout.sql, by the owner of the
-- truss schema, only in a deployment that wants roles to see and write only the modules they are given.
-- A role's access to a module comes from a row of truss.module_access. The acting role is the one the database
-- reports (CONTRACT-002, db_role): the role set for the transaction, else the session user.
-- Every policy is a set-based EXISTS over type_def or rel_def and module_access, which the planner turns into a
-- semi-join. Policies that called functions row by row cost about twice as much on a 50-row page (SPIKE-003 F8),
-- and a SECURITY DEFINER function 2 to 3 times as much.

CREATE FUNCTION truss.acting_role() RETURNS text LANGUAGE sql STABLE AS
$$ SELECT COALESCE(NULLIF(current_setting('role'), 'none'), session_user)::text $$;

-- Catalog tables: a role sees the definitions of the modules it can read. The catalog is written only by a
-- revision acceptance, which runs as the owner, so these tables are enabled but not forced.
ALTER TABLE truss.module_access ENABLE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.module_access FOR SELECT
  USING (truss.acting_role() IN (reader_role, writer_role));
ALTER TABLE truss.type_def ENABLE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.type_def FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.module_access a WHERE a.module = type_def.module AND truss.acting_role() IN (a.reader_role, a.writer_role)));
ALTER TABLE truss.rel_def ENABLE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.rel_def FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.module_access a WHERE a.module = rel_def.module AND truss.acting_role() IN (a.reader_role, a.writer_role)));
ALTER TABLE truss.prop_def ENABLE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.prop_def FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.type_def t WHERE t.type_id = prop_def.type_id));
ALTER TABLE truss.key_def ENABLE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.key_def FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.type_def t WHERE t.type_id = key_def.type_id));
ALTER TABLE truss.rel_endpoint ENABLE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.rel_endpoint FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.rel_def r WHERE r.rel_type_id = rel_endpoint.rel_type_id));
-- schema_rev, schema_doc, schema_change and setting are not granted to module roles: they hold every module's documents.

-- Data tables are forced, so the owner and functions it owns obey the policies as the acting role.
ALTER TABLE truss.object ENABLE ROW LEVEL SECURITY; ALTER TABLE truss.object FORCE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.object FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object.type_id AND truss.acting_role() IN (a.reader_role, a.writer_role)));
CREATE POLICY iso_insert ON truss.object FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object.type_id AND truss.acting_role() = a.writer_role));
CREATE POLICY iso_update ON truss.object FOR UPDATE
  USING (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object.type_id AND truss.acting_role() = a.writer_role))
  WITH CHECK (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object.type_id AND truss.acting_role() = a.writer_role));
CREATE POLICY iso_delete ON truss.object FOR DELETE
  USING (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object.type_id AND truss.acting_role() = a.writer_role));
ALTER TABLE truss.object_key ENABLE ROW LEVEL SECURITY; ALTER TABLE truss.object_key FORCE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.object_key FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object_key.type_id AND truss.acting_role() IN (a.reader_role, a.writer_role)));
CREATE POLICY iso_insert ON truss.object_key FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object_key.type_id AND truss.acting_role() = a.writer_role));
CREATE POLICY iso_update ON truss.object_key FOR UPDATE
  USING (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object_key.type_id AND truss.acting_role() = a.writer_role))
  WITH CHECK (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object_key.type_id AND truss.acting_role() = a.writer_role));
CREATE POLICY iso_delete ON truss.object_key FOR DELETE
  USING (EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = object_key.type_id AND truss.acting_role() = a.writer_role));

-- An edge is visible to a role that can read its relationship's module and both endpoint types' modules, and
-- writable by the writer of the relationship's module who can read both endpoints.
ALTER TABLE truss.edge ENABLE ROW LEVEL SECURITY; ALTER TABLE truss.edge FORCE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.edge FOR SELECT
  USING (EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = edge.rel_type_id AND truss.acting_role() IN (a.reader_role, a.writer_role))
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.source_type AND truss.acting_role() IN (a.reader_role, a.writer_role))
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.target_type AND truss.acting_role() IN (a.reader_role, a.writer_role)));
CREATE POLICY iso_insert ON truss.edge FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = edge.rel_type_id AND truss.acting_role() = a.writer_role)
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.source_type AND truss.acting_role() IN (a.reader_role, a.writer_role))
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.target_type AND truss.acting_role() IN (a.reader_role, a.writer_role)));
CREATE POLICY iso_update ON truss.edge FOR UPDATE
  USING (EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = edge.rel_type_id AND truss.acting_role() = a.writer_role)
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.source_type AND truss.acting_role() IN (a.reader_role, a.writer_role))
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.target_type AND truss.acting_role() IN (a.reader_role, a.writer_role)))
  WITH CHECK (EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = edge.rel_type_id AND truss.acting_role() = a.writer_role)
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.source_type AND truss.acting_role() IN (a.reader_role, a.writer_role))
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.target_type AND truss.acting_role() IN (a.reader_role, a.writer_role)));
CREATE POLICY iso_delete ON truss.edge FOR DELETE
  USING (EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = edge.rel_type_id AND truss.acting_role() = a.writer_role)
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.source_type AND truss.acting_role() IN (a.reader_role, a.writer_role))
  AND EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = edge.target_type AND truss.acting_role() IN (a.reader_role, a.writer_role)));
ALTER TABLE truss.edge_limit ENABLE ROW LEVEL SECURITY; ALTER TABLE truss.edge_limit FORCE ROW LEVEL SECURITY;
CREATE POLICY iso_all ON truss.edge_limit
  USING (EXISTS (SELECT 1 FROM truss.edge e WHERE e.id = edge_limit.edge_id))
  WITH CHECK (EXISTS (SELECT 1 FROM truss.edge e WHERE e.id = edge_limit.edge_id));

-- Journal rows and tombstones follow the type (entity_kind 'o') or relationship ('e') they name.
ALTER TABLE truss.journal ENABLE ROW LEVEL SECURITY; ALTER TABLE truss.journal FORCE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.journal FOR SELECT
  USING (CASE journal.entity_kind WHEN 'o' THEN EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = journal.entity_type AND truss.acting_role() IN (a.reader_role, a.writer_role))
    ELSE EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = journal.entity_type AND truss.acting_role() IN (a.reader_role, a.writer_role)) END);
CREATE POLICY iso_insert ON truss.journal FOR INSERT
  WITH CHECK (CASE journal.entity_kind WHEN 'o' THEN EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = journal.entity_type AND truss.acting_role() = a.writer_role)
    ELSE EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = journal.entity_type AND truss.acting_role() = a.writer_role) END);
ALTER TABLE truss.key_tombstone ENABLE ROW LEVEL SECURITY; ALTER TABLE truss.key_tombstone FORCE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.key_tombstone FOR SELECT
  USING (CASE key_tombstone.entity_kind WHEN 'o' THEN EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = key_tombstone.type_id AND truss.acting_role() IN (a.reader_role, a.writer_role))
    ELSE EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = key_tombstone.type_id AND truss.acting_role() IN (a.reader_role, a.writer_role)) END);
CREATE POLICY iso_insert ON truss.key_tombstone FOR INSERT
  WITH CHECK (CASE key_tombstone.entity_kind WHEN 'o' THEN EXISTS (SELECT 1 FROM truss.type_def d JOIN truss.module_access a ON a.module = d.module WHERE d.type_id = key_tombstone.type_id AND truss.acting_role() = a.writer_role)
    ELSE EXISTS (SELECT 1 FROM truss.rel_def d JOIN truss.module_access a ON a.module = d.module WHERE d.rel_type_id = key_tombstone.type_id AND truss.acting_role() = a.writer_role) END);

-- record_source follows the record it describes, through that table's own policy.
ALTER TABLE truss.record_source ENABLE ROW LEVEL SECURITY; ALTER TABLE truss.record_source FORCE ROW LEVEL SECURITY;
CREATE POLICY iso_select ON truss.record_source FOR SELECT
  USING (CASE record_source.entity_kind
    WHEN 'o' THEN EXISTS (SELECT 1 FROM truss.object o WHERE o.id = record_source.entity_id)
    ELSE EXISTS (SELECT 1 FROM truss.edge e WHERE e.id = record_source.entity_id) END);
CREATE POLICY iso_insert ON truss.record_source FOR INSERT
  WITH CHECK (CASE record_source.entity_kind
    WHEN 'o' THEN EXISTS (SELECT 1 FROM truss.object o WHERE o.id = record_source.entity_id)
    ELSE EXISTS (SELECT 1 FROM truss.edge e WHERE e.id = record_source.entity_id) END);

-- Privileges are still the deployment's: policies only narrow what a granted privilege reaches. This grants a
-- module's roles the privileges the policies assume. With writes false only SELECT is granted.
CREATE FUNCTION truss.grant_module_roles(m text, writes boolean DEFAULT false) RETURNS void LANGUAGE plpgsql AS
$$
DECLARE a truss.module_access; r text;
BEGIN
  SELECT * INTO a FROM truss.module_access WHERE module = m;
  IF NOT FOUND THEN RAISE EXCEPTION 'module % has no module_access row', m; END IF;
  FOREACH r IN ARRAY ARRAY[a.reader_role, a.writer_role] LOOP
    EXECUTE format('GRANT USAGE ON SCHEMA truss TO %I', r);
    EXECUTE format('GRANT SELECT ON truss.module_access, truss.type_def, truss.prop_def, truss.key_def, truss.rel_def, truss.rel_endpoint, '
                   'truss.object, truss.object_key, truss.edge, truss.journal, truss.key_tombstone, truss.record_source TO %I', r);
  END LOOP;
  IF writes THEN
    EXECUTE format('GRANT INSERT, UPDATE, DELETE ON truss.object, truss.object_key, truss.edge, truss.edge_limit TO %I', a.writer_role);
    EXECUTE format('GRANT INSERT ON truss.journal, truss.key_tombstone, truss.record_source TO %I', a.writer_role);
    EXECUTE format('GRANT USAGE ON SEQUENCE truss.id_seq, truss.journal_seq TO %I', a.writer_role);
  END IF;
END
$$;
