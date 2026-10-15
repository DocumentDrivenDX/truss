/** Original UMF adapter owns the private PG anchor storage syntax. */
const root=process.argv[2];
if(!root?.startsWith('/'))throw Error('Explicit original UMF checkout required');
const {backend}=await import(root+'/native/postgresql/runtime');
const {readDocument}=await import(root+'/src/model/document');
const {importPostgresqlSql,exportPostgresqlSql}=await import(root+'/src/adapters/postgresql');
const source=`CREATE SEQUENCE truss.preparation_attempt_anchor_seq AS integer MINVALUE 1 MAXVALUE 2147483647 NO CYCLE;
CREATE TABLE truss.preparation_attempt_anchor (
 anchor_id integer PRIMARY KEY DEFAULT nextval('truss.preparation_attempt_anchor_seq') CHECK(anchor_id>0),
 anchor_nonce uuid NOT NULL UNIQUE,
 store_control_id bigint NOT NULL REFERENCES truss.action_store_registration(control_id),
 store_receipt_bytes bytea NOT NULL CHECK(octet_length(store_receipt_bytes) BETWEEN 1 AND 4194304),
 program_identity bytea NOT NULL CHECK(octet_length(program_identity) BETWEEN 1 AND 1048576),
 database_oid oid NOT NULL CHECK(database_oid<>'0'::oid),
 postmaster_started_at timestamptz NOT NULL CHECK(isfinite(postmaster_started_at)),
 data_pid integer NOT NULL CHECK(data_pid>0),
 data_role_oid oid NOT NULL CHECK(data_role_oid<>'0'::oid),
 data_backend_started_at timestamptz NOT NULL CHECK(isfinite(data_backend_started_at)),
 coordinator_pid integer NOT NULL CHECK(coordinator_pid>0 AND coordinator_pid<>data_pid),
 coordinator_role_oid oid NOT NULL CHECK(coordinator_role_oid=data_role_oid),
 coordinator_backend_started_at timestamptz NOT NULL CHECK(isfinite(coordinator_backend_started_at)),
 coordinator_xact_started_at timestamptz NOT NULL CHECK(isfinite(coordinator_xact_started_at)),
 coordinator_xid xid8 NOT NULL CHECK(coordinator_xid>'0'::xid8),
 issuer_pid integer NOT NULL CHECK(issuer_pid>0 AND issuer_pid<>data_pid AND issuer_pid<>coordinator_pid),
 issuer_xid xid8 NOT NULL CHECK(issuer_xid>'0'::xid8 AND issuer_xid<>coordinator_xid),
 issued_at timestamptz NOT NULL CHECK(isfinite(issued_at)),
 profile_id text NOT NULL CHECK(profile_id='truss.preparation-attempt-anchor/0.1')
);
CREATE TRIGGER preparation_attempt_anchor_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.preparation_attempt_anchor
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.preparation_attempt_anchor ENABLE ALWAYS TRIGGER preparation_attempt_anchor_immutable;
REVOKE ALL ON TABLE truss.preparation_attempt_anchor FROM PUBLIC;
REVOKE ALL ON SEQUENCE truss.preparation_attempt_anchor_seq FROM PUBLIC;
REVOKE ALL ON TYPE truss.preparation_attempt_anchor FROM PUBLIC;`;
const doc=await importPostgresqlSql(source,backend,{id:'truss-preparation-attempt-anchor-storage-0.1'});
const raw=JSON.stringify(doc)+'\n';const ddl=await exportPostgresqlSql(doc,backend);
if(await exportPostgresqlSql(readDocument(raw,'json'),backend)!==ddl)throw Error('Saved anchor export differs');
await Bun.write('docs/helix/02-design/models/truss-preparation-attempt-anchor-storage-0.1.proposal.umf.json',raw);
await Bun.write('docs/helix/04-build/preparation-attempt-anchor.generated.sql',ddl);
await Bun.write('packages/python/src/truss/_security_bootstrap/preparation-attempt-anchor-storage.sql',ddl);
console.log(JSON.stringify({nativeStorageExport:true,savedRoundtrip:true,scope:'private identity component only; opaque program identity has no admission meaning'}));
