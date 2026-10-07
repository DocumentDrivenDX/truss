-- Unadopted EL08-EL12 observer declarations for exact legacy namespace/layout.
-- Referenced routines and actual context/phase/resource/privilege realization
-- remain missing. Do not install this fragment independently.
CREATE TRIGGER edge_limit_edge_observe
  AFTER INSERT OR UPDATE OR DELETE ON truss.edge
  FOR EACH ROW EXECUTE FUNCTION truss.edge_limit_observe();
CREATE TRIGGER edge_limit_marker_observe
  AFTER INSERT OR UPDATE OR DELETE ON truss.edge_limit
  FOR EACH ROW EXECUTE FUNCTION truss.edge_limit_observe();
CREATE TRIGGER edge_limit_catalog_observe
  AFTER INSERT OR UPDATE OR DELETE ON truss.rel_def
  FOR EACH ROW EXECUTE FUNCTION truss.edge_limit_catalog_observe();
-- No WHEN/UPDATE OF/arguments/transition-table filter. TRUNCATE and disabling,
-- role/replication mode changes or routine/table/trigger alteration are denied
-- separately by the original qualified privilege/setting profile.
-- Existing operation-registry deferred dispatcher performs full current EL
-- non-row validation; these AFTER observers are not independent commit proof.
