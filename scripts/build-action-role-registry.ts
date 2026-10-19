// SPDX-License-Identifier: MIT OR Apache-2.0
/** Private original action declaration/mapping storage, exported by UMF. */
const root=process.argv[2];
if(!root?.startsWith('/'))throw Error('Explicit original UMF checkout required');
const {backend}=await import(root+'/native/postgresql/runtime');
const {readDocument}=await import(root+'/src/model/document');
const {importPostgresqlSql,exportPostgresqlSql}=await import(root+'/src/adapters/postgresql');
const source=`CREATE TABLE truss.action_family_registration (
 family_registration_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),
 store_control_id bigint NOT NULL REFERENCES truss.action_store_registration(control_id),
 store_identity bytea NOT NULL CHECK(octet_length(store_identity) BETWEEN 1 AND 4096),
 family_identity bytea NOT NULL CHECK(octet_length(family_identity) BETWEEN 1 AND 4096),
 original_action_pin bytea NOT NULL CHECK(octet_length(original_action_pin) BETWEEN 1 AND 1048576),
 original_model_artifact bytea NOT NULL CHECK(octet_length(original_model_artifact) BETWEEN 1 AND 4194304),
 original_preparation_artifact bytea NOT NULL CHECK(octet_length(original_preparation_artifact) BETWEEN 1 AND 4194304),
 declared_roles bytea[] NOT NULL CHECK(cardinality(declared_roles) BETWEEN 1 AND 64 AND array_ndims(declared_roles)=1 AND array_lower(declared_roles,1)=1 AND array_position(declared_roles,NULL) IS NULL),
 person_required boolean NOT NULL CHECK(person_required),
 profile_id text NOT NULL CHECK(profile_id='umf.actions.roles'),
 profile_version text NOT NULL CHECK(profile_version='1')
);
CREATE INDEX action_family_registration_route ON truss.action_family_registration(sha256(store_identity),sha256(family_identity));
CREATE TRIGGER action_family_registration_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.action_family_registration FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.action_family_registration ENABLE ALWAYS TRIGGER action_family_registration_immutable;
CREATE TABLE truss.action_role_binding (
 binding_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 family_registration_id bigint NOT NULL REFERENCES truss.action_family_registration(family_registration_id),
 installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),
 store_identity bytea NOT NULL CHECK(octet_length(store_identity) BETWEEN 1 AND 4096),
 family_identity bytea NOT NULL CHECK(octet_length(family_identity) BETWEEN 1 AND 4096),
 role_identity bytea NOT NULL CHECK(octet_length(role_identity) BETWEEN 1 AND 2048),
 native_role_oid oid NOT NULL,
 original_action_pin bytea NOT NULL CHECK(octet_length(original_action_pin) BETWEEN 1 AND 1048576),
 profile_id text NOT NULL CHECK(profile_id='umf.actions.roles'),
 profile_version text NOT NULL CHECK(profile_version='1')
);
CREATE INDEX action_role_binding_route ON truss.action_role_binding(sha256(family_identity),sha256(role_identity));
REVOKE ALL ON TABLE truss.action_family_registration,truss.action_role_binding FROM PUBLIC;
REVOKE ALL ON SEQUENCE truss.action_family_registration_family_registration_id_seq,truss.action_role_binding_binding_id_seq FROM PUBLIC;
REVOKE ALL ON TYPE truss.action_family_registration,truss.action_role_binding FROM PUBLIC;`;
const doc=await importPostgresqlSql(source,backend,{id:'truss-action-role-registry-storage-0.1'});
const raw=JSON.stringify(doc)+'\n';const ddl=await exportPostgresqlSql(doc,backend);
if(await exportPostgresqlSql(readDocument(raw,'json'),backend)!==ddl)throw Error('Saved registry export differs');
await Bun.write('docs/helix/02-design/models/truss-action-role-registry-storage-0.1.proposal.umf.json',raw);
await Bun.write('docs/helix/04-build/action-role-registry.generated.sql',ddl);
await Bun.write('packages/python/src/truss/_security_bootstrap/action-role-registry-storage.sql',ddl);
console.log(JSON.stringify({nativeStorageExport:true,savedRoundtrip:true,scope:'Original action declarations and role mappings; not selection program or authority'}));
