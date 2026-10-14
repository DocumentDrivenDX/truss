/** Candidate seal storage through the committed UMF native owner. Not installed. */
import {backend} from '/Users/erik/.codex/worktrees/0e51/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlNode} from '/Users/erik/.codex/worktrees/0e51/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/validation/document';
const source=`CREATE SEQUENCE truss.runtime_preparation_seal_seq AS bigint MINVALUE 1 MAXVALUE 9223372036854775807 NO CYCLE;
CREATE TABLE truss.runtime_preparation_seal (
 seal_id bigint PRIMARY KEY DEFAULT nextval('truss.runtime_preparation_seal_seq') CHECK(seal_id>0),
 attempt_id uuid NOT NULL UNIQUE,
 installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),
 store_epoch text NOT NULL COLLATE pg_catalog."C" CHECK(octet_length(store_epoch) BETWEEN 1 AND 1024),
 initiator_oid oid NOT NULL CHECK(initiator_oid<>'0'::oid), writer_xid xid8 NOT NULL CHECK(writer_xid>'0'::xid8), data_backend_pid int NOT NULL CHECK(data_backend_pid>0),
 data_context_bytes bytea NOT NULL CHECK(octet_length(data_context_bytes) BETWEEN 1 AND 65536),
 authority_context_bytes bytea NOT NULL CHECK(octet_length(authority_context_bytes) BETWEEN 1 AND 16777216),
 source_context_bytes bytea NOT NULL CHECK(octet_length(source_context_bytes) BETWEEN 1 AND 16777216),
 action_bytes bytea NOT NULL CHECK(octet_length(action_bytes) BETWEEN 1 AND 1048576),
 selection_bytes bytea NOT NULL CHECK(octet_length(selection_bytes) BETWEEN 1 AND 16777216),
 manifest_bytes bytea NOT NULL CHECK(octet_length(manifest_bytes) BETWEEN 1 AND 16777216),
 cut_bytes bytea NOT NULL CHECK(octet_length(cut_bytes) BETWEEN 1 AND 65536),
 profile_bytes bytea NOT NULL CHECK(octet_length(profile_bytes) BETWEEN 1 AND 65536),
 manifest_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(manifest_bytes)) STORED,
 sealed_at timestamptz NOT NULL DEFAULT clock_timestamp() CHECK(pg_catalog.isfinite(sealed_at))
);
CREATE TRIGGER runtime_preparation_seal_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.runtime_preparation_seal
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.runtime_preparation_seal ENABLE ALWAYS TRIGGER runtime_preparation_seal_immutable;
REVOKE ALL ON TABLE truss.runtime_preparation_seal FROM PUBLIC;
REVOKE ALL ON SEQUENCE truss.runtime_preparation_seal_seq FROM PUBLIC;
REVOKE ALL ON TYPE truss.runtime_preparation_seal FROM PUBLIC;`;
const native=await importPostgresqlSql(source,backend,{id:'truss-preparation-seal-storage-0.1'});
const raw=JSON.stringify(native)+'\n';
const ddl=await exportPostgresqlSql(native,backend);
if(await exportPostgresqlSql(readDocument(raw,'json'),backend)!==ddl)throw Error('Saved native owner export changed');
const stmts=JSON.parse(renderTree(getPostgresqlNode(native,'/stmts')));
const table=stmts.find((s:any)=>s.stmt.CreateStmt).stmt.CreateStmt;
const id='truss-preparation-seal';const ref=(element:string)=>({module:id,element});
const record:any={id:'runtime_preparation_seal',name:'runtime_preparation_seal',kind:'record',members:[],references:[],keys:[],extensions:{'truss.layout.native':{definition:table,identity:'One immutable original seal per attempt; unequal repeats refuse. No UPSERT.'}}};
const elements:any[]=[];
for(const e of table.tableElts){
 const c=e.ColumnDef;if(!c)continue;
 const key=record.id+'.'+c.colname;const nativeType=c.typeName.names.at(-1).String.sval;
 const field:any={id:key,name:c.colname,kind:'field',cardinality:'one',nullability:(c.constraints??[]).some((w:any)=>['CONSTR_PRIMARY','CONSTR_NOTNULL'].includes(w.Constraint.contype))?'required':'unspecified',extensions:{'truss.layout.native':{definition:c,nativeType}}};
 if(['int8','int4'].includes(nativeType))field.scalarType='integer';
 record.members.push(ref(key));record.references.push({role:'member',...ref(key)});
 for(const w of c.constraints??[]){
  if(w.Constraint.contype==='CONSTR_PRIMARY')record.keys.push({id:'primary',name:'primary',primary:true,fields:[ref(key)]});
  if(w.Constraint.contype==='CONSTR_FOREIGN'){
   field.references=[{role:'physical-fk:installation',...ref('catalog_runtime_installation.installation_id')}];
   record.references.push({role:'physical-fk:installation',...ref('catalog_runtime_installation')});
  }
 }
 elements.push(field);
}
elements.push(record,
 {id:'catalog_runtime_installation.installation_id',name:'installation_id',kind:'field',cardinality:'one',nullability:'required',extensions:{'truss.layout.native':{nativeType:'uuid'}}},
 {id:'catalog_runtime_installation',name:'catalog_runtime_installation',kind:'record',members:[ref('catalog_runtime_installation.installation_id')],references:[{role:'member',...ref('catalog_runtime_installation.installation_id')}],extensions:{'truss.layout.native':{projection:'Original referenced installation column only; not a replacement catalog model'}}});
const core:any={umf:'0.8.0',id:'truss-preparation-seal-core-0.1',vocabularies:{'truss.layout.native':{version:'0.1.0'}},modules:[{id,namespace:'truss',elements}],extensions:{'truss.layout.native':{scope:'Uninstalled candidate. Native UUID/OID/xid8/bytea/timestamptz and constraints retained; no portable UUID key or native qualification.',storeEpoch:'Bulk store/guard epoch; metadata-source registry epoch, accepted catalog revision and original helper correspondence remain in source_context_bytes.',capsules:'Versioned exact original data session/incarnation, initiating person, authority, source, action RevisionRef, selection and opaque cut. Original binding must match this same live installation/store epoch and admitted cut; disposable-export IDs are historical compiler evidence, never authority elsewhere. Bytes or digest shape is not authority.',sealedAt:'Native row write time, not COMMIT confirmation.',dependencies:'Existing original catalog_immutable helper and installation record; no FK to a post-snapshot coordinator row.'}}};
const validation=validateDocument(core);
if(!validation.valid)throw Error(JSON.stringify(validation.diagnostics));
const base='docs/helix/02-design/models/truss-preparation-seal-';
await Bun.write(base+'storage-0.1.proposal.umf.json',raw);
await Bun.write(base+'core-0.1.proposal.umf.json',JSON.stringify(core)+'\n');
await Bun.write('docs/helix/04-build/preparation-seal.generated.sql',ddl);
await Bun.write('packages/python/src/truss/_security_bootstrap/preparation-seal-storage.sql',ddl);
console.log(JSON.stringify({columns:record.members.length,ownerExport:true,savedExportIdentical:true,valid:validation.valid,complete:validation.complete,installed:false}));
