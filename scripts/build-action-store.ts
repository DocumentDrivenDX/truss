/** Original UMF native owner generates a private shared action-store home. */
const root=process.argv[2];
if(!root?.startsWith('/'))throw Error('Explicit original UMF owner checkout required');
const {backend}=await import(root+'/native/postgresql/runtime');
const {readDocument}=await import(root+'/src/model/document');
const {importPostgresqlSql,exportPostgresqlSql,getPostgresqlNode}=await import(root+'/src/adapters/postgresql');
const {renderTree}=await import(root+'/src/model/native-json');
const {validateDocument}=await import(root+'/src/validation/document');
const source=`CREATE SEQUENCE truss.action_store_control_seq AS bigint MINVALUE 1 MAXVALUE 9223372036854775807 NO CYCLE;
CREATE TABLE truss.action_store_registration (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 control_id bigint NOT NULL UNIQUE DEFAULT nextval('truss.action_store_control_seq') CHECK(control_id>0),
 logical_store_id uuid NOT NULL UNIQUE,
 store_identity bytea NOT NULL UNIQUE CHECK(store_identity=convert_to('"'||logical_store_id::text||'"','UTF8')),
 tenant_identity bytea NOT NULL CHECK(octet_length(tenant_identity) BETWEEN 1 AND 4096),
 executor_oids oid[] NOT NULL CHECK(cardinality(executor_oids) BETWEEN 0 AND 4),
 guard_epoch uuid NOT NULL UNIQUE CHECK(guard_epoch<>logical_store_id),
 epoch_identity bytea NOT NULL CHECK(epoch_identity=convert_to('"'||guard_epoch::text||'"','UTF8')),
 registration_key bytea NOT NULL UNIQUE CHECK(octet_length(registration_key) BETWEEN 1 AND 256),
 installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),
 source_installation_id text GENERATED ALWAYS AS (installation_id::text) STORED,
 database_oid oid NOT NULL CHECK(database_oid<>'0'::oid),
 schema_oid oid NOT NULL CHECK(schema_oid<>'0'::oid),
 postmaster_started_at timestamptz NOT NULL CHECK(isfinite(postmaster_started_at)),
 source_epoch text NOT NULL CHECK(octet_length(source_epoch) BETWEEN 1 AND 256),
 source_incarnation text NOT NULL CHECK(octet_length(source_incarnation) BETWEEN 1 AND 1024),
 source_profile_bytes bytea NOT NULL CHECK(octet_length(source_profile_bytes) BETWEEN 1 AND 65536),
 source_evidence_bytes bytea NOT NULL CHECK(octet_length(source_evidence_bytes) BETWEEN 1 AND 1048576),
 runtime_release_id text NOT NULL CHECK(octet_length(runtime_release_id) BETWEEN 1 AND 1024),
 runtime_release_sha256 bytea NOT NULL CHECK(octet_length(runtime_release_sha256)=32),
 issuer_xid xid8 NOT NULL CHECK(issuer_xid>'0'::xid8),
 issuer_actor_oid oid NOT NULL CHECK(issuer_actor_oid<>'0'::oid),
 issued_at timestamptz NOT NULL CHECK(isfinite(issued_at)),
 initial_receipt_bytes bytea NOT NULL CHECK(octet_length(initial_receipt_bytes) BETWEEN 1 AND 4194304),
 profile_id text NOT NULL CHECK(profile_id='truss.action-store/native-pg18/0.1'),
 FOREIGN KEY(source_installation_id,source_epoch) REFERENCES truss.source_epoch_registry(installation_id,source_epoch)
);
CREATE TRIGGER action_store_registration_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.action_store_registration
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.action_store_registration ENABLE ALWAYS TRIGGER action_store_registration_immutable;
REVOKE ALL ON TABLE truss.action_store_registration FROM PUBLIC;
REVOKE ALL ON SEQUENCE truss.action_store_control_seq FROM PUBLIC;
REVOKE ALL ON TYPE truss.action_store_registration FROM PUBLIC;`;
const doc=await importPostgresqlSql(source,backend,{id:'truss-action-store-storage-0.1'});
const raw=JSON.stringify(doc)+'\n';const ddl=await exportPostgresqlSql(doc,backend);
if(await exportPostgresqlSql(readDocument(raw,'json'),backend)!==ddl)throw Error('Saved owner store export changed');
const table=JSON.parse(renderTree(getPostgresqlNode(doc,'/stmts'))).find((s:any)=>s.stmt.CreateStmt).stmt.CreateStmt;
const id='truss-action-store';const ref=(element:string)=>({module:id,element});
const record:any={id:'action_store_registration',name:'action_store_registration',kind:'record',members:[],references:[],keys:[],extensions:{'truss.layout.native':{definition:table}}};
const elements:any[]=[];
for(const e of table.tableElts){const c=e.ColumnDef;if(!c)continue;const key=record.id+'.'+c.colname;const type=c.typeName.names.at(-1).String.sval;
 const field:any={id:key,name:c.colname,kind:'field',cardinality:'one',nullability:(c.constraints??[]).some((w:any)=>['CONSTR_PRIMARY','CONSTR_NOTNULL'].includes(w.Constraint.contype))?'required':'unspecified',extensions:{'truss.layout.native':{definition:c,nativeType:type}}};
 if(['int8','int4'].includes(type))field.scalarType='integer';if(type==='text')field.scalarType='string';if(type==='bool')field.scalarType='boolean';
 record.members.push(ref(key));record.references.push({role:'member',...ref(key)});
 for(const w of c.constraints??[]){const constraint=w.Constraint;if(constraint.contype==='CONSTR_PRIMARY')record.keys.push({id:'primary',name:'primary',primary:true,fields:[ref(key)]});if(constraint.contype==='CONSTR_FOREIGN'){
  field.references=[{role:'physical-fk:installation',...ref('catalog_runtime_installation.installation_id')}];record.references.push({role:'physical-fk:installation',...ref('catalog_runtime_installation')});}}
 elements.push(field);
}
for(const e of table.tableElts){const c=e.Constraint;if(c?.contype==='CONSTR_FOREIGN'){
 record.references.push({role:'physical-fk:source-epoch',...ref('source_epoch_registry')});
 for(let i=0;i<c.fk_attrs.length;i++){const field=elements.find((f:any)=>f.name===c.fk_attrs[i].String.sval);field.references=[{role:'physical-fk:source-epoch',...ref('source_epoch_registry.'+c.pk_attrs[i].String.sval)}];}
}}
elements.push(record);
for(const [name,fields] of [['catalog_runtime_installation',['installation_id']],['source_epoch_registry',['installation_id','source_epoch']]] as const){
 for(const field of fields)elements.push({id:name+'.'+field,name:field,kind:'field',cardinality:'one',nullability:'required',...(name==='source_epoch_registry'?{scalarType:'string'}:{}),extensions:{'truss.layout.native':{projection:'Original referenced key column only'}}});
 elements.push({id:name,name,kind:'record',members:fields.map(f=>ref(name+'.'+f)),references:fields.map(f=>({role:'member',...ref(name+'.'+f)})),extensions:{'truss.layout.native':{projection:'Referenced key projection, not a replacement owner catalog'}}});
}
const core:any={umf:'0.8.0',id:'truss-action-store-core-0.1',vocabularies:{'truss.layout.native':{version:'0.1.0'}},modules:[{id,namespace:'truss',elements}],extensions:{'truss.layout.native':{scope:'Private source checkpoint, not installed or admitted. One logical store per installation; logical identity is distinct from installation UUID. Exact original store/tenant/guard epoch bytes. Guard epoch does not reset replay scope. Native UUID/OID/xid8/bytea/timestamptz semantics retained; no portable key/DDL qualification.'}}};
const valid=validateDocument(core);if(!valid.valid)throw Error(JSON.stringify(valid.diagnostics));
await Bun.write('docs/helix/02-design/models/truss-action-store-storage-0.1.proposal.umf.json',raw);
await Bun.write('docs/helix/02-design/models/truss-action-store-core-0.1.proposal.umf.json',JSON.stringify(core)+'\n');
await Bun.write('docs/helix/04-build/action-store.generated.sql',ddl);
await Bun.write('packages/python/src/truss/_security_bootstrap/action-store-storage.sql',ddl);
console.log(JSON.stringify({columns:record.members.length,ownerExport:true,savedExportIdentical:true,valid:valid.valid,complete:valid.complete,installed:false}));
