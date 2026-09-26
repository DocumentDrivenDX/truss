-- SPIKE-002 option C: generic (type-independent) traversal indexes, created after the bulk load.
CREATE INDEX IF NOT EXISTS edge_source_idx ON c.edge (source_id, rel_type_id) INCLUDE (target_id);
CREATE INDEX IF NOT EXISTS edge_target_idx ON c.edge (target_id, rel_type_id) INCLUDE (source_id);
CREATE INDEX IF NOT EXISTS journal_object_idx ON c.journal (object_id);
