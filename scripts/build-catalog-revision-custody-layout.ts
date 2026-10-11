/** Review-only original catalog custody home; DDL is exported by UMF. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
const source=`
CREATE TABLE truss.catalog_revision_custody (
 original_writer_xid xid8 NOT NULL,
 operation_ordinal bigint NOT NULL CHECK (operation_ordinal>=0),
 original_revision integer NOT NULL CHECK (original_revision>0),
 capture_generation bigint NOT NULL CHECK (capture_generation>=0),
 original_producer_profile_bytes bytea NOT NULL CHECK (octet_length(original_producer_profile_bytes) BETWEEN 1 AND 65536),
 original_fact_key_bytes bytea NOT NULL CHECK (octet_length(original_fact_key_bytes) BETWEEN 1 AND 65536),
 original_fact_key_profile_bytes bytea NOT NULL CHECK (octet_length(original_fact_key_profile_bytes) BETWEEN 1 AND 65536),
 original_payload_bytes bytea NOT NULL CHECK (octet_length(original_payload_bytes) BETWEEN 1 AND 4194304),
 original_payload_profile_bytes bytea NOT NULL CHECK (octet_length(original_payload_profile_bytes) BETWEEN 1 AND 65536),
 original_owner_context_bytes bytea NOT NULL CHECK (octet_length(original_owner_context_bytes) BETWEEN 1 AND 16777216),
 original_write_at timestamptz NOT NULL CHECK (isfinite(original_write_at) AND original_write_at >= TIMESTAMPTZ '0001-01-01 00:00:00+00' AND original_write_at < TIMESTAMPTZ '10000-01-01 00:00:00+00'),
 original_fact_clock_bytes bytea NOT NULL CHECK (octet_length(original_fact_clock_bytes) BETWEEN 1 AND 65536),
 PRIMARY KEY (original_writer_xid,operation_ordinal),
 FOREIGN KEY (original_writer_xid,operation_ordinal) REFERENCES truss.row_home_operation (original_writer_xid,operation_ordinal) ON DELETE RESTRICT,
 FOREIGN KEY (original_revision) REFERENCES truss.schema_rev (rev) ON DELETE RESTRICT,
 CHECK (octet_length(original_producer_profile_bytes)::bigint+octet_length(original_fact_key_bytes)::bigint+octet_length(original_fact_key_profile_bytes)::bigint+octet_length(original_payload_bytes)::bigint+octet_length(original_payload_profile_bytes)::bigint+octet_length(original_owner_context_bytes)::bigint+octet_length(original_fact_clock_bytes)::bigint<=16777216)
);
REVOKE ALL ON truss.catalog_revision_custody FROM PUBLIC;
CREATE FUNCTION truss.runtime_refuse_catalog_revision_custody_mutation_candidate()
RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RAISE EXCEPTION 'original catalog revision custody is immutable' USING ERRCODE='55000';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_refuse_catalog_revision_custody_mutation_candidate() FROM PUBLIC;
CREATE TRIGGER catalog_revision_custody_immutable_row BEFORE UPDATE OR DELETE ON truss.catalog_revision_custody
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_refuse_catalog_revision_custody_mutation_candidate();
ALTER TABLE truss.catalog_revision_custody ENABLE ALWAYS TRIGGER catalog_revision_custody_immutable_row;
CREATE TRIGGER catalog_revision_custody_immutable_truncate BEFORE TRUNCATE ON truss.catalog_revision_custody
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_refuse_catalog_revision_custody_mutation_candidate();
ALTER TABLE truss.catalog_revision_custody ENABLE ALWAYS TRIGGER catalog_revision_custody_immutable_truncate;

`;
const model=await importPostgresqlSql(source,backend,{id:'truss-catalog-revision-custody-storage-candidate'});
const serialized=JSON.stringify(model)+'\n',ddl=await exportPostgresqlSql(model,backend);
if(await exportPostgresqlSql(readDocument(serialized,'json'),backend)!==ddl)throw Error('Original reload/export mismatch');
const modelPath='docs/helix/02-design/contracts/catalog-revision-custody-storage-v0.1.proposal.umf.json';
const ddlPath='docs/helix/04-build/evidence/catalog-revision-custody-storage.owner-export.sql';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const ownerSourcePins=Object.fromEntries(await Promise.all(['src/adapters/postgresql/index.ts','src/model/document.ts','src/model/native-json.ts','native/postgresql/runtime.ts'].map(async path=>[path,hash(await Bun.file('/Users/erik/Projects/umf/'+path).text())])));
const receipt={ownerSourcePins,modelPath,modelSha256:hash(serialized),ddlPath,ddlSha256:hash(ddl),producerSha256:hash(await Bun.file('scripts/build-catalog-revision-custody-layout.ts').text()),reloadedExportExact:true,scope:'Storage proposal only; native guard behavior, versioned installation, capture, core projection and native behavior remain unqualified',qualified:false};
for(const [path,bytes] of [[modelPath,serialized],[ddlPath,ddl],['docs/helix/04-build/evidence/design-audit/catalog-revision-custody-storage.json',JSON.stringify(receipt,null,2)+'\n']]){
 if(process.argv.includes('--check')){if(await Bun.file(path).text()!==bytes)throw Error('Stale catalog custody source: '+path)}else await Bun.write(path,bytes);
}
console.log('Catalog custody proposal: UMF saved reload/export exact; unqualified.');
