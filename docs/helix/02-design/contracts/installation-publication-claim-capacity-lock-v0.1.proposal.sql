-- Original compatible read/write coordinator only, before registration.
-- Required order: schema-head SHARE, installation guard SHARE, then this lock.
-- Retain through original registration commit/rollback. No lock upgrade after
-- effects. All profile registrants must use this same serialization scope.
LOCK TABLE truss.policy_publication_claim IN SHARE ROW EXCLUSIVE MODE;
