/** Review-only operation capture home; UMF owner generates DDL. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
const source=`
CREATE TABLE truss.operation_configuration (
 original_writer_xid xid8 NOT NULL,
 operation_ordinal bigint NOT NULL CHECK (operation_ordinal>=0),
 installation_id text COLLATE pg_catalog."C" NOT NULL,
 source_epoch text COLLATE pg_catalog."C" NOT NULL,
 target_incarnation text COLLATE pg_catalog."C" NOT NULL CHECK (octet_length(target_incarnation) BETWEEN 1 AND 1024),
 configuration_generation bigint NOT NULL CHECK (configuration_generation>=0),
 key_reuse text COLLATE pg_catalog."C" NOT NULL CHECK (key_reuse IN ('forbid','allow')),
 journal_mode text COLLATE pg_catalog."C" NOT NULL CHECK (journal_mode IN ('engine','trigger')),
 original_context_sha256 bytea NOT NULL CHECK (octet_length(original_context_sha256)=32),
 admission_profile_bytes bytea NOT NULL CHECK (octet_length(admission_profile_bytes) BETWEEN 1 AND 65536),
 configuration_bytes bytea NOT NULL CHECK (octet_length(configuration_bytes)>0),
 selected_binding_bytes bytea NOT NULL CHECK (octet_length(selected_binding_bytes)>0),
 installed_inventory_bytes bytea NOT NULL CHECK (octet_length(installed_inventory_bytes)>0),
 configuration_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(configuration_bytes)) STORED,
 selected_binding_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(selected_binding_bytes)) STORED,
 installed_inventory_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(installed_inventory_bytes)) STORED,
 PRIMARY KEY (original_writer_xid,operation_ordinal),
 FOREIGN KEY (original_writer_xid,operation_ordinal)
  REFERENCES truss.row_home_operation (original_writer_xid,operation_ordinal),
 FOREIGN KEY (installation_id,source_epoch)
  REFERENCES truss.source_epoch_registry (installation_id,source_epoch),
 CHECK (octet_length(configuration_bytes)::bigint+octet_length(selected_binding_bytes)::bigint+octet_length(installed_inventory_bytes)::bigint<=16777216)
);
REVOKE ALL ON truss.operation_configuration FROM PUBLIC;
`;
const model=await importPostgresqlSql(source,backend,{id:'truss-operation-configuration-storage-candidate'});
const serialized=JSON.stringify(model)+'\n',ddl=await exportPostgresqlSql(model,backend);
if(await exportPostgresqlSql(readDocument(serialized,'json'),backend)!==ddl)throw Error('Original reload/export mismatch');
const modelPath='docs/helix/02-design/contracts/operation-configuration-storage-v0.1.proposal.umf.json';
const ddlPath='docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const ownerSourcePins=Object.fromEntries(await Promise.all(['src/adapters/postgresql/index.ts','src/model/document.ts','src/model/native-json.ts','native/postgresql/runtime.ts'].map(async path=>[path,hash(await Bun.file('/Users/erik/Projects/umf/'+path).text())])));
const receipt={ownerSourcePins,modelPath,modelSha256:hash(serialized),ddlPath,ddlSha256:hash(ddl),producerSha256:hash(await Bun.file('scripts/build-operation-configuration-layout.ts').text()),reloadedExportExact:true,scope:'UMF owner import and saved reload/export only; adjunct not composed, initialized, immutable, core-projected or installed-qualified',qualified:false};
for(const [path,bytes] of [[modelPath,serialized],[ddlPath,ddl],['docs/helix/04-build/evidence/design-audit/operation-configuration-storage.json',JSON.stringify(receipt,null,2)+'\n']]){
 if(process.argv.includes('--check')){if(await Bun.file(path).text()!==bytes)throw Error('Stale operation configuration source: '+path)}else await Bun.write(path,bytes);
}
console.log('Operation configuration adjunct: UMF saved reload/export exact; unqualified.');
