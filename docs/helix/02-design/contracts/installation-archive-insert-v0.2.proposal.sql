-- CONTRACT-008 body component for the 0.13 checked identity digest repair.
-- NOT a public routine, grant, installer or readiness proof.
-- Original installer admission/exclusion/account/role and complete role/identity
-- archive inventory must be established before this statement. No ON CONFLICT.
WITH original_parameters AS (
  SELECT $1::text AS installation_id,
         $2::text AS artifact_role,
         $3::text AS artifact_identity,
         pg_catalog.decode($4::text, 'hex') AS artifact_bytes
)
INSERT INTO truss.installation_archive (
  installation_id, artifact_role, artifact_identity, artifact_bytes,
  artifact_identity_sha256
)
SELECT installation_id, artifact_role, artifact_identity, artifact_bytes,
       pg_catalog.sha256(pg_catalog.convert_to(artifact_identity, 'UTF8'))
FROM original_parameters
RETURNING archive_row_id::text,
          pg_catalog.encode(artifact_sha256, 'hex') AS artifact_sha256,
          pg_catalog.encode(artifact_identity_sha256, 'hex') AS artifact_identity_sha256;
