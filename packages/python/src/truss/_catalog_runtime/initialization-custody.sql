-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Private original initializer evidence, under the installing-host/admin trust boundary.
CREATE TABLE truss.runtime_initialization_custody (
 installation_id uuid PRIMARY KEY REFERENCES truss.catalog_runtime_installation(installation_id),
 witness_bytes bytea NOT NULL CHECK (pg_catalog.octet_length(witness_bytes) BETWEEN 1 AND 16384),
 witness_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(witness_bytes)) STORED NOT NULL);
CREATE TRIGGER runtime_initialization_custody_immutable
 BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.runtime_initialization_custody
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_initialization_custody FROM PUBLIC;
REVOKE ALL ON TYPE truss.runtime_initialization_custody FROM PUBLIC;
