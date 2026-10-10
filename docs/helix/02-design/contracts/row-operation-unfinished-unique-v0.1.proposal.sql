-- Unadopted OC01/OC02 at-most-one unfinished operation candidate.
-- Existing protected registry phase/identity checks and native producers remain required.
CREATE UNIQUE INDEX row_home_operation_unfinished_xid
  ON truss.row_home_operation (original_writer_xid)
  WHERE phase OPERATOR(pg_catalog.<>) 'application_finalized';
-- This does not prove existence, authentic xid/context, phase transitions or commit closure.
