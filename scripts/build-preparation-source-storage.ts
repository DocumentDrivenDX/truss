// SPDX-License-Identifier: MIT OR Apache-2.0
/** One immutable source attachment to the original program; no new identity. */
const root=process.argv[2];if(!root?.startsWith('/'))throw Error('Explicit UMF checkout required');
const {backend}=await import(root+'/native/postgresql/runtime');
const {readDocument}=await import(root+'/src/model/document');
const {importPostgresqlSql,exportPostgresqlSql}=await import(root+'/src/adapters/postgresql');
const source=`CREATE TABLE truss.preparation_program_sources (
 program_id bigint PRIMARY KEY REFERENCES truss.preparation_program_registration(program_id),
 original_source_packet bytea NOT NULL CHECK(octet_length(original_source_packet) BETWEEN 1 AND 67108864),
 producer_identity bytea NOT NULL CHECK(octet_length(producer_identity) BETWEEN 1 AND 8192),
 issuer_xid xid8 NOT NULL CHECK(issuer_xid>'0'::xid8),
 issuer_actor_oid oid NOT NULL CHECK(issuer_actor_oid<>'0'::oid),
 issued_at timestamptz NOT NULL CHECK(isfinite(issued_at))
);
CREATE TRIGGER preparation_program_sources_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.preparation_program_sources FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.preparation_program_sources ENABLE ALWAYS TRIGGER preparation_program_sources_immutable;
REVOKE ALL ON TABLE truss.preparation_program_sources FROM PUBLIC;
REVOKE ALL ON TYPE truss.preparation_program_sources FROM PUBLIC;`;
const document=await importPostgresqlSql(source,backend,{id:'truss-preparation-program-sources-0.1'});
const saved=JSON.stringify(document)+'\n';const ddl=await exportPostgresqlSql(document,backend);
if(await exportPostgresqlSql(readDocument(saved,'json'),backend)!==ddl)throw Error('Saved source model export differs');
await Bun.write('docs/helix/02-design/models/truss-preparation-program-sources-0.1.proposal.umf.json',saved);
await Bun.write('docs/helix/04-build/preparation-program-sources.generated.sql',ddl);
await Bun.write('packages/python/src/truss/_security_bootstrap/preparation-program-sources-storage.sql',ddl);
console.log(JSON.stringify({nativeStorageExport:true,savedRoundtrip:true,scope:'Original source attachment, not authority'}));
