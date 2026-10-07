-- Review candidate only; not part of the adopted layout or installer.
-- Apply only to the exact baseline whose edge table has no retained home.
-- Existing rows remain SQL NULL: this does not recover previously lost content.
-- Truss must qualify the selected exact-value/presence profile independently.
ALTER TABLE truss.edge ADD COLUMN retained pg_catalog.jsonb;
ALTER TABLE truss.edge ADD CONSTRAINT edge_retained_is_object
  CHECK (retained IS NULL OR pg_catalog.jsonb_typeof(retained) = 'object');
