-- SPDX-License-Identifier: MIT OR Apache-2.0
CREATE TABLE truss.runtime_migration_receipt (
 attempt_id uuid PRIMARY KEY, request_bytes bytea NOT NULL,
 request_sha256 text NOT NULL CHECK(request_sha256=encode(sha256(request_bytes),'hex')),
 source_sha256 text NOT NULL, target_sha256 text NOT NULL,
 target_release text NOT NULL, target_layout_profile jsonb NOT NULL,target_configuration jsonb NOT NULL,
 recipe_sha256 text NOT NULL, recipe_bytes bytea NOT NULL,
 source_inventory_bytes bytea NOT NULL,target_inventory_bytes bytea NOT NULL,
 step_evidence_bytes bytea NOT NULL,preservation_bytes bytea NOT NULL,
 writer_xid xid8 NOT NULL DEFAULT pg_current_xact_id(),
 applied_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE FUNCTION truss.runtime_migration_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,pg_temp AS $$ BEGIN
 RAISE EXCEPTION 'migration receipts are immutable' USING ERRCODE='55000'; END; $$;
CREATE TRIGGER runtime_migration_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
 ON truss.runtime_migration_receipt FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_migration_immutable();
ALTER TABLE truss.runtime_migration_receipt ENABLE ALWAYS TRIGGER runtime_migration_immutable;
CREATE FUNCTION truss.runtime_current_installation() RETURNS SETOF truss.catalog_runtime_installation
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE; transition record;
BEGIN
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation;
 SELECT * INTO transition FROM truss.runtime_migration_receipt ORDER BY writer_xid DESC LIMIT 1;
 IF FOUND THEN
  installation.release_id:=transition.target_release;
  installation.release_sha256:=transition.target_sha256;
  installation.layout_profile:=transition.target_layout_profile;
  installation.preparation_configuration:=transition.target_configuration;
 END IF;
 RETURN NEXT installation;
END; $$;
REVOKE ALL ON FUNCTION truss.runtime_current_installation(),truss.runtime_migration_immutable() FROM PUBLIC;
