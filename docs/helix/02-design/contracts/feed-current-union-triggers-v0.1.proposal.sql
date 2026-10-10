-- Proposed four-store validation scheduling; referenced body is undefined/unqualified.
-- No WHEN or UPDATE OF filter; retain all original OLD/NEW attribution.
CREATE CONSTRAINT TRIGGER feed_tx_current_union_guard
  AFTER INSERT OR UPDATE OR DELETE ON truss.feed_tx
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION truss.feed_current_union_check();
CREATE CONSTRAINT TRIGGER feed_member_current_union_guard
  AFTER INSERT OR UPDATE OR DELETE ON truss.feed_member
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION truss.feed_current_union_check();
CREATE CONSTRAINT TRIGGER feed_prerequisite_current_union_guard
  AFTER INSERT OR UPDATE OR DELETE ON truss.feed_prerequisite
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION truss.feed_current_union_check();
CREATE CONSTRAINT TRIGGER feed_configuration_prerequisite_current_union_guard
  AFTER INSERT OR UPDATE OR DELETE ON truss.feed_configuration_prerequisite
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION truss.feed_current_union_check();
-- These declarations do not observe all upstream producers or qualify retention.
-- Native helper body, roles/grants, enabled/partition/dependency and event custody
-- must be selected and independently qualified before installer admission.
