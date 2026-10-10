-- Unadopted protected transactional staging alternative to backend-local scratch.
-- Requires the selected original row_home_operation registry and all native guards.
-- No separate operation identity, public capability, phase setter or commit receipt.
CREATE TABLE truss.row_home_journal_stage (
  original_writer_xid pg_catalog.xid8 NOT NULL,
  operation_ordinal pg_catalog.int8 NOT NULL,
  stage_name pg_catalog.text COLLATE pg_catalog."C" NOT NULL,
  stage_ordinal pg_catalog.int8 NOT NULL,
  effect_generation pg_catalog.int8 NOT NULL,
  body_bytes pg_catalog.bytea NOT NULL,
  CONSTRAINT row_home_journal_stage_pk PRIMARY KEY
    (original_writer_xid, operation_ordinal, stage_name, stage_ordinal),
  CONSTRAINT row_home_journal_stage_operation_fk FOREIGN KEY
    (original_writer_xid, operation_ordinal)
    REFERENCES truss.row_home_operation (original_writer_xid, operation_ordinal)
    ON DELETE RESTRICT,
  CONSTRAINT row_home_journal_stage_phase CHECK
    (stage_name IN ('start', 'transition', 'final', 'reserved', 'publication')),
  CONSTRAINT row_home_journal_stage_ordinals CHECK
    (operation_ordinal >= 0 AND stage_ordinal >= 0 AND effect_generation >= 0
      AND (stage_name = 'transition' OR stage_ordinal = 0)),
  CONSTRAINT row_home_journal_stage_body CHECK
    (pg_catalog.octet_length(body_bytes) > 0)
);
-- body_bytes is immutable after admitted insertion. No ordinary role writes/reads.
-- Native producer must capture actual xid/ordinal/generation and full phase grammar.
-- Nonempty bytes/CHECKs/FK do not prove authority, completeness, resource or phase order.
-- Capacity/privilege/install/rollback/retention/cleanup/full source proof remains open.
