/** Review-only migration receipt adjunct. UMF owns import and DDL generation. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
const source=`
CREATE SEQUENCE truss.layout_migration_receipt_row_seq AS bigint
 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 NO CYCLE;
CREATE TABLE truss.layout_migration_receipt (
 storage_row_id bigint PRIMARY KEY DEFAULT nextval('truss.layout_migration_receipt_row_seq'),
 installation_id text COLLATE pg_catalog."C" NOT NULL,
 original_source_epoch text COLLATE pg_catalog."C" NOT NULL,
 original_target_incarnation text COLLATE pg_catalog."C" NOT NULL CHECK (octet_length(original_target_incarnation) BETWEEN 1 AND 1024),
 original_attempt_identity_bytes bytea NOT NULL CHECK (octet_length(original_attempt_identity_bytes) BETWEEN 1 AND 1024),
 receipt_profile_bytes bytea NOT NULL CHECK (octet_length(receipt_profile_bytes) BETWEEN 1 AND 65536),
 original_request_bytes bytea NOT NULL CHECK (octet_length(original_request_bytes)>0),
 original_receipt_bytes bytea NOT NULL CHECK (octet_length(original_receipt_bytes)>0),
 original_attempt_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_attempt_identity_bytes)) STORED,
 original_request_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_request_bytes)) STORED,
 original_receipt_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_receipt_bytes)) STORED,
 CHECK (storage_row_id>0),
 CHECK (octet_length(original_request_bytes)::bigint+octet_length(original_receipt_bytes)::bigint<=16777216),
 FOREIGN KEY (installation_id,original_source_epoch)
  REFERENCES truss.source_epoch_registry (installation_id,source_epoch) ON DELETE RESTRICT
);
CREATE INDEX layout_migration_receipt_attempt_route ON truss.layout_migration_receipt
 (installation_id,original_attempt_sha256,storage_row_id);
REVOKE ALL ON truss.layout_migration_receipt, truss.layout_migration_receipt_row_seq FROM PUBLIC;
`;
const model=await importPostgresqlSql(source,backend,{id:'truss-layout-migration-storage-candidate'});
const serialized=JSON.stringify(model)+'\n',ddl=await exportPostgresqlSql(model,backend);
if(await exportPostgresqlSql(readDocument(serialized,'json'),backend)!==ddl)throw Error('Original saved model export mismatch');
const modelPath='docs/helix/02-design/contracts/layout-migration-storage-v0.1.proposal.umf.json';
const ddlPath='docs/helix/04-build/evidence/layout-migration-storage.owner-export.sql';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const ownerSourcePins=Object.fromEntries(await Promise.all(['src/adapters/postgresql/index.ts','src/model/document.ts','src/model/native-json.ts','native/postgresql/runtime.ts'].map(async path=>[path,hash(await Bun.file('/Users/erik/Projects/umf/'+path).text())])));
const receipt={ownerSourcePins,modelPath,modelSha256:hash(serialized),ddlPath,ddlSha256:hash(ddl),producerSha256:hash(await Bun.file('scripts/build-layout-migration-storage.ts').text()),reloadedExportExact:true,qualified:false,scope:'UMF owner import and saved reload/export only; uncomposed adjunct, no native producer, guard, core projection, installation or migration qualification'};
for(const [path,bytes] of [[modelPath,serialized],[ddlPath,ddl],['docs/helix/04-build/evidence/design-audit/layout-migration-storage.json',JSON.stringify(receipt,null,2)+'\n']]){
 if(process.argv.includes('--check')){if(await Bun.file(path).text()!==bytes)throw Error('Stale layout migration storage: '+path)}else await Bun.write(path,bytes);
}
console.log('Layout migration receipt adjunct: UMF saved reload/export exact; unqualified.');
