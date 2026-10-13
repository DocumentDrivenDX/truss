-- Private physical statement-coordination spike, PostgreSQL18.6 only.
-- Install under the original installation owner, revoke PUBLIC execute, bind
-- original identity/profile bytes and actual relation OID in immutable TG_ARGV.
-- Attach BEFORE and AFTER STATEMENT for INSERT/UPDATE/DELETE/TRUNCATE, ENABLE ALWAYS.
-- Advance once per AFTER trigger event, including zero-row events; UPSERT/MERGE
-- may fire multiple events per command. This does not authorize logical writes or establish complete source/role routes.
CREATE FUNCTION truss.security_data_writer_guard() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original_identity bytea; original_profile bytea; observed_generation bigint;
        expected_identity bytea; expected_profile bytea; advanced_generation bigint;
BEGIN
 IF TG_LEVEL OPERATOR(pg_catalog.<>) 'STATEMENT'
    OR TG_WHEN NOT IN ('BEFORE','AFTER') OR TG_OP NOT IN ('INSERT','UPDATE','DELETE','TRUNCATE')
    OR TG_NARGS OPERATOR(pg_catalog.<>) 3
    OR TG_RELID OPERATOR(pg_catalog.<>) TG_ARGV[2]::pg_catalog.oid
    OR pg_catalog.current_setting('server_version_num') OPERATOR(pg_catalog.<>) '180006'
    OR pg_catalog.current_setting('transaction_isolation') OPERATOR(pg_catalog.<>) 'read committed'
    OR pg_catalog.current_setting('transaction_read_only') OPERATOR(pg_catalog.<>) 'off'
 THEN RAISE EXCEPTION 'Unsupported original data writer scope' USING ERRCODE='42501'; END IF;
 expected_identity:=pg_catalog.decode(TG_ARGV[0],'hex');
 expected_profile:=pg_catalog.decode(TG_ARGV[1],'hex');
 PERFORM rev FROM truss.schema_head WHERE id OPERATOR(pg_catalog.=) 1 FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Original data writer head missing' USING ERRCODE='42501'; END IF;
 SELECT installation_identity_bytes,policy_profile_bytes,generation
 INTO original_identity,original_profile,observed_generation
 FROM truss.policy_generation_guard WHERE singleton OPERATOR(pg_catalog.=) 1 FOR UPDATE;
 IF NOT FOUND OR original_identity IS DISTINCT FROM expected_identity
    OR original_profile IS DISTINCT FROM expected_profile
    OR observed_generation OPERATOR(pg_catalog.>=) 9223372036854775807
 THEN RAISE EXCEPTION 'Original data writer guard refused' USING ERRCODE='42501'; END IF;
 -- Fresh VOLATILE SPI statement AFTER the original exclusive guard drains SHARE registrants.
 IF EXISTS(SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled)
 THEN RAISE EXCEPTION 'Outstanding publication blocks data writer' USING ERRCODE='42501'; END IF;
 IF TG_WHEN OPERATOR(pg_catalog.=) 'AFTER' THEN
  UPDATE truss.policy_generation_guard SET generation=generation OPERATOR(pg_catalog.+) 1
  WHERE singleton OPERATOR(pg_catalog.=) 1 AND generation OPERATOR(pg_catalog.=) observed_generation
   AND installation_identity_bytes OPERATOR(pg_catalog.=) expected_identity
   AND policy_profile_bytes OPERATOR(pg_catalog.=) expected_profile
   AND NOT EXISTS(SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled)
  RETURNING generation INTO advanced_generation;
  IF NOT FOUND OR advanced_generation OPERATOR(pg_catalog.<>) (observed_generation OPERATOR(pg_catalog.+) 1)
  THEN RAISE EXCEPTION 'Original data writer advance refused' USING ERRCODE='42501'; END IF;
 END IF;
 RETURN NULL;
END $$;
REVOKE ALL ON FUNCTION truss.security_data_writer_guard() FROM PUBLIC;
