-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Hashes actual packaged descriptor bytes; native enrollment remains mandatory.
CREATE FUNCTION truss.query_temporal_abi() RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ SELECT '{"identity":"truss-postgresql-logical-query","version":"1.3","sha256":"0ecf5aa206dfcfcba21581fc328d7d073b48dbc8b61b2fc199278cf5f3e31b0b"}'::jsonb; $$;
REVOKE ALL ON FUNCTION truss.query_temporal_abi() FROM PUBLIC;
