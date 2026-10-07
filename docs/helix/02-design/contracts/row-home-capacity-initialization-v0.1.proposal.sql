-- Unadopted fresh-only bootstrap initialization, never repair/reconciliation.
-- $1 is complete original admitted layout-definition bytes, not future marker bytes.
-- $2 is complete original admitted touch-retention resource profile bytes.
-- Installer proves fresh empty touch scope under original installation exclusion.
INSERT INTO truss.row_home_capacity
  (singleton_id, retained_rows, retained_custody_bytes, reserved_rows,
   reserved_custody_bytes, original_layout_bytes, original_resource_profile_bytes)
VALUES (1, 0, 0, 0, 0, $1::bytea, $2::bytea)
RETURNING singleton_id, retained_rows, retained_custody_bytes, reserved_rows,
  reserved_custody_bytes, original_layout_bytes, original_resource_profile_bytes;
-- No ON CONFLICT/reset/upsert; populated conversion has a separate profile.
-- Complete independent re-observation remains required before bootstrap marker.
