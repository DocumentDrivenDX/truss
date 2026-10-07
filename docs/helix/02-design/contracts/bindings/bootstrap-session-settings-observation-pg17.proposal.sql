-- Unexecuted PG17 fixed allowlist only; no credential/general setting enumeration.
-- Observation does not SET or restore settings, admit writer role or prove whole cut.
SELECT s.name AS setting_name,
       pg_catalog.current_setting(s.name,false) AS observed_value
FROM (VALUES ('transaction_isolation'),('transaction_read_only'),
             ('transaction_deferrable'),('client_encoding'),('server_encoding'),
             ('search_path'),('row_security'),('session_replication_role'),
             ('extra_float_digits'),('standard_conforming_strings'),
             ('TimeZone'),('DateStyle'),('IntervalStyle'),
             ('statement_timeout'),('lock_timeout'),
             ('idle_in_transaction_session_timeout')) AS s(name)
ORDER BY s.name COLLATE pg_catalog."C";
