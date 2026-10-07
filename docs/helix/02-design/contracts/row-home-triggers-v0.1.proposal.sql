-- Unadopted trigger fragment: referenced routines are not yet defined/qualified.
-- No WHEN/UPDATE OF filter; all actual canonical row effects are observed.
CREATE TRIGGER row_home_state_touch_observe
  AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_state
  FOR EACH ROW EXECUTE FUNCTION truss.row_touch_observe();
CREATE TRIGGER row_home_node_touch_observe
  AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_node
  FOR EACH ROW EXECUTE FUNCTION truss.row_touch_observe();
CREATE TRIGGER row_home_scalar_touch_observe
  AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_scalar
  FOR EACH ROW EXECUTE FUNCTION truss.row_touch_observe();
CREATE CONSTRAINT TRIGGER row_home_touch_commit_guard
  AFTER INSERT OR UPDATE ON truss.row_home_touch
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION truss.row_touch_commit_check();
CREATE CONSTRAINT TRIGGER row_home_capacity_commit_guard
  AFTER INSERT OR UPDATE ON truss.row_home_capacity
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION truss.row_touch_commit_check();
CREATE CONSTRAINT TRIGGER row_home_operation_commit_guard
  AFTER INSERT OR UPDATE ON truss.row_home_operation
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION truss.row_touch_commit_check();
-- Ordinary DELETE/TRUNCATE of touch/capacity is denied separately by privileges.
-- Routine bodies, type/security/owner/grants, complete producer/retention/init
-- registry and full native inventory/behavior proof remain required.
