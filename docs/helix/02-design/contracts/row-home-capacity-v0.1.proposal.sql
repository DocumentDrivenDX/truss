-- Unadopted installation-scoped capacity ledger; not a reservation procedure.
-- One protected row per actual installed namespace/layout, not a caller key.
CREATE TABLE truss.row_home_capacity (
  singleton_id smallint PRIMARY KEY,
  retained_rows bigint NOT NULL,
  retained_custody_bytes bigint NOT NULL,
  reserved_rows bigint NOT NULL,
  reserved_custody_bytes bigint NOT NULL,
  original_layout_bytes bytea NOT NULL,
  original_resource_profile_bytes bytea NOT NULL,
  CONSTRAINT row_home_capacity_singleton CHECK (singleton_id = 1),
  CONSTRAINT row_home_capacity_nonnegative CHECK
    (retained_rows >= 0 AND retained_custody_bytes >= 0
      AND reserved_rows >= 0 AND reserved_custody_bytes >= 0),
  CONSTRAINT row_home_capacity_reference_caps CHECK
    (retained_rows + reserved_rows <= 65536
      AND retained_custody_bytes + reserved_custody_bytes <= 536870912),
  CONSTRAINT row_home_capacity_originals CHECK
    (octet_length(original_layout_bytes) > 0
      AND octet_length(original_resource_profile_bytes) > 0)
);
-- Initial row and original byte/profile admission must be installed atomically.
-- Nonnegative bounded arithmetic is not actual full retained/reserved parity.
-- Original transaction reservation registry, protected routines, grants and
-- head-then-capacity exclusion remain required before ordinary writer admission.
-- No caller reset, row deletion or direct counter adjustment is authorized.
-- Actual native storage/index/WAL overhead has a separate deployment budget.
