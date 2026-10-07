-- Unadopted ADR-004 reactivation alternative; not a baseline installation.
-- Native identifier domains remain signed. key_num is local to type_id.
-- Byte payload profiles, protected producer and conversion remain unqualified.
CREATE TABLE truss.key_lifecycle_history (
  rev int NOT NULL REFERENCES truss.schema_rev (rev),
  seq int NOT NULL,
  type_id int NOT NULL,
  key_num smallint NOT NULL,
  transition_kind text COLLATE pg_catalog."C" NOT NULL CHECK (transition_kind IN
    ('definition_change', 'retirement', 'reactivation')),
  before_retired_rev int REFERENCES truss.schema_rev (rev),
  after_retired_rev int REFERENCES truss.schema_rev (rev),
  before_definition_bytes bytea NOT NULL,
  after_definition_bytes bytea NOT NULL,
  PRIMARY KEY (rev, seq),
  FOREIGN KEY (type_id, key_num) REFERENCES truss.key_def (type_id, key_num),
  CHECK (rev > 0),
  CHECK (octet_length(before_definition_bytes) > 0),
  CHECK (octet_length(after_definition_bytes) > 0),
  CHECK (
    (transition_kind = 'retirement'
      AND before_retired_rev IS NULL AND after_retired_rev IS NOT NULL
      AND after_retired_rev = rev)
    OR
    (transition_kind = 'reactivation'
      AND before_retired_rev IS NOT NULL AND before_retired_rev < rev
      AND after_retired_rev IS NULL)
    OR
    (transition_kind = 'definition_change'
      AND before_retired_rev IS NOT DISTINCT FROM after_retired_rev
      AND (before_retired_rev IS NULL OR before_retired_rev < rev))
  )
);
CREATE INDEX key_lifecycle_history_by_key
  ON truss.key_lifecycle_history (type_id, key_num, rev, seq);
