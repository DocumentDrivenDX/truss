ALTER TABLE truss.catalog_runtime_installation ADD COLUMN managed_grants jsonb NOT NULL DEFAULT ('{"interfaceVersion":"truss-managed-grants/0.1","roles":[],"observations":[]}'::jsonb) CHECK ((jsonb_typeof(managed_grants) = 'object' AND (managed_grants ->> 'interfaceVersion') = 'truss-managed-grants/0.1' AND jsonb_typeof(managed_grants -> 'roles') = 'array' AND jsonb_array_length(managed_grants -> 'roles') <= 32 AND jsonb_typeof(managed_grants -> 'observations') = 'array' AND jsonb_array_length(managed_grants -> 'observations') <= 16384 AND octet_length(managed_grants::text) <= 4194304) IS TRUE); CREATE OR REPLACE FUNCTION truss.runtime_current_installation() RETURNS SETOF truss.catalog_runtime_installation LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE; transition record;
BEGIN
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation;
 IF jsonb_typeof(installation.managed_grants) IS DISTINCT FROM 'object'
   OR installation.managed_grants->>'interfaceVersion' IS DISTINCT FROM 'truss-managed-grants/0.1' THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant policy shape or bounds changed';
 END IF;
 IF (SELECT count(*) FROM pg_catalog.jsonb_object_keys(installation.managed_grants))<>3 THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant policy shape or bounds changed';
 END IF;
 IF jsonb_typeof(installation.managed_grants->'roles') IS DISTINCT FROM 'array'
   OR jsonb_typeof(installation.managed_grants->'observations') IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant policy shape or bounds changed';
 END IF;
 IF jsonb_array_length(installation.managed_grants->'roles')>32
   OR jsonb_array_length(installation.managed_grants->'observations')>16384 THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant policy shape or bounds changed';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.jsonb_array_elements(installation.managed_grants->'roles') AS saved(role)
   WHERE jsonb_typeof(saved.role) IS DISTINCT FROM 'object'
     OR CASE WHEN jsonb_typeof(saved.role)='object'
       THEN (SELECT count(*) FROM pg_catalog.jsonb_object_keys(saved.role))<>2 ELSE false END) THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant role identity is malformed';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.jsonb_array_elements(installation.managed_grants->'roles') AS saved(role)
   WHERE jsonb_typeof(saved.role->'name') IS DISTINCT FROM 'string'
     OR octet_length(saved.role->>'name') NOT BETWEEN 1 AND 63
     OR jsonb_typeof(saved.role->'oid') IS DISTINCT FROM 'number'
     OR CASE WHEN saved.role->>'oid' ~ '^[1-9][0-9]{0,9}$'
       THEN (saved.role->>'oid')::numeric>4294967295 ELSE true END) THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant role identity is malformed';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.jsonb_array_elements(installation.managed_grants->'roles') AS saved(role)
   GROUP BY saved.role->>'name' HAVING count(*)>1)
   OR EXISTS(SELECT 1 FROM pg_catalog.jsonb_array_elements(installation.managed_grants->'roles') AS saved(role)
   GROUP BY saved.role->>'oid' HAVING count(*)>1)
   OR EXISTS(SELECT 1 FROM pg_catalog.jsonb_array_elements(installation.managed_grants->'roles') AS saved(role)
   WHERE (saved.role->>'oid')::oid IN (installation.owner_oid,installation.registrar_oid)) THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant role identity is duplicated or reserved';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_catalog.jsonb_array_elements(installation.managed_grants->'roles') AS saved(role)
   LEFT JOIN pg_catalog.pg_roles r ON r.oid=(saved.role->>'oid')::pg_catalog.oid
   WHERE r.rolname IS DISTINCT FROM saved.role->>'name') THEN
  RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Managed grant role identity drifted';
 END IF;
 SELECT * INTO transition FROM truss.runtime_migration_receipt ORDER BY writer_xid DESC LIMIT 1;
 IF FOUND THEN
  installation.release_id:=transition.target_release;
  installation.release_sha256:=transition.target_sha256;
  installation.layout_profile:=transition.target_layout_profile;
  installation.preparation_configuration:=transition.target_configuration;
 END IF;
 RETURN NEXT installation;
END; $$