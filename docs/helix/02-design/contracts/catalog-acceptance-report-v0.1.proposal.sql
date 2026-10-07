-- Unadopted separate-report option for a future complete Truss layout.
-- Not an additive baseline installation: baseline schema_rev.report is still
-- NOT NULL. A complete selected replacement layout must reconcile that home.
-- No partial/empty accepted report is licensed by this fragment.
CREATE TABLE truss.catalog_acceptance_report (
  rev pg_catalog.int4 PRIMARY KEY REFERENCES truss.schema_rev(rev),
  report_bytes pg_catalog.bytea NOT NULL,
  CONSTRAINT catalog_acceptance_report_positive_revision CHECK (rev > 0),
  CONSTRAINT catalog_acceptance_report_nonempty CHECK
    (pg_catalog.octet_length(report_bytes) > 0)
);
-- Exact report encoding/admission, protected producer, immutable write grants,
-- head-transition completeness and historical disclosure require the selected
-- native profile. PK/FK/nonempty checks do not prove report semantic validity.
