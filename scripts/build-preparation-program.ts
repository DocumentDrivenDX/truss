// SPDX-License-Identifier: MIT OR Apache-2.0
/** Immutable original compiler packet storage; no native execution admission. */
const root=process.argv[2];
if(!root?.startsWith('/'))throw Error('Explicit original UMF checkout required');
const {backend}=await import(root+'/native/postgresql/runtime');
const {readDocument}=await import(root+'/src/model/document');
const {importPostgresqlSql,exportPostgresqlSql}=await import(root+'/src/adapters/postgresql');
const source=`CREATE TABLE truss.preparation_program_registration (
 program_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 program_identity uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
 store_control_id bigint NOT NULL REFERENCES truss.action_store_registration(control_id),
 store_receipt_bytes bytea NOT NULL CHECK(octet_length(store_receipt_bytes) BETWEEN 1 AND 4194304),
 registration_key bytea NOT NULL CHECK(octet_length(registration_key) BETWEEN 1 AND 256),
 compiler_source_pin text NOT NULL CHECK(compiler_source_pin ~ '^[0-9a-f]{40}$'),
 original_configuration bytea NOT NULL CHECK(octet_length(original_configuration) BETWEEN 1 AND 8388608),
 original_request bytea NOT NULL CHECK(octet_length(original_request) BETWEEN 1 AND 8388608),
 original_plan_artifact bytea NOT NULL CHECK(octet_length(original_plan_artifact) BETWEEN 1 AND 8388608),
 original_binding_artifact bytea NOT NULL CHECK(octet_length(original_binding_artifact) BETWEEN 1 AND 8388608),
 original_lowering bytea NOT NULL CHECK(octet_length(original_lowering) BETWEEN 1 AND 8388608),
 issuer_xid xid8 NOT NULL CHECK(issuer_xid>'0'::xid8),
 issuer_actor_oid oid NOT NULL CHECK(issuer_actor_oid<>'0'::oid),
 issued_at timestamptz NOT NULL CHECK(isfinite(issued_at)),
 UNIQUE(store_control_id,registration_key)
);
CREATE TRIGGER preparation_program_registration_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.preparation_program_registration FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.preparation_program_registration ENABLE ALWAYS TRIGGER preparation_program_registration_immutable;
REVOKE ALL ON TABLE truss.preparation_program_registration FROM PUBLIC;
REVOKE ALL ON SEQUENCE truss.preparation_program_registration_program_id_seq FROM PUBLIC;
REVOKE ALL ON TYPE truss.preparation_program_registration FROM PUBLIC;`;
const doc=await importPostgresqlSql(source,backend,{id:'truss-preparation-program-storage-0.1'});
const raw=JSON.stringify(doc)+'\n';const ddl=await exportPostgresqlSql(doc,backend);
if(await exportPostgresqlSql(readDocument(raw,'json'),backend)!==ddl)throw Error('Saved program export differs');
await Bun.write('docs/helix/02-design/models/truss-preparation-program-storage-0.1.proposal.umf.json',raw);
await Bun.write('docs/helix/04-build/preparation-program.generated.sql',ddl);
await Bun.write('packages/python/src/truss/_security_bootstrap/preparation-program-storage.sql',ddl);
console.log(JSON.stringify({nativeStorageExport:true,savedRoundtrip:true,scope:'Original compiler byte custody only; not an admitted selector or permission'}));
