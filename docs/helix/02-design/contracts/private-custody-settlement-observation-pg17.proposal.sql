-- Unadopted read-only PostgreSQL 17 settlement observation source.
-- $1 is the independently admitted original full xid8, not a caller status claim.
-- Original installation/source-epoch/authority and bounded native context admission
-- precede this query. A returned status alone is not cleanup eligibility.
SELECT ($1::pg_catalog.xid8)::pg_catalog.text AS original_writer_xid,
       pg_catalog.pg_xact_status($1::pg_catalog.xid8)::pg_catalog.text AS transaction_status;
