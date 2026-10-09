/** Full candidate DDL installation in an isolated rollback-only namespace. */
import {SQL} from 'bun';
const url=process.env.TRUSS_OPERATION_TEST_URL;
if(!url?.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Owned fixture URL required');
const sql=new SQL(url,{max:1});const namespace='truss_epoch_layout_component';
let inventory:unknown,version='';
try {
 await sql.begin(async tx=>{
  const exists=await tx`SELECT to_regnamespace(${namespace})::text AS n`;
  if(exists[0].n!==null)throw Error('Component namespace exists; refuse overwrite');
  const ddl=await Bun.file('docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').text();
  // Explicit test-only namespace substitution; original bytes remain retained.
  await tx.unsafe(ddl.replace(/\btruss\b/g,namespace));
  const tables=await tx`SELECT c.relname AS name,count(a.attnum)::text AS columns FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE n.nspname=${namespace} AND c.relkind IN ('r','p') GROUP BY c.relname ORDER BY c.relname COLLATE pg_catalog."C"`;
  if(tables.length!==48||tables.reduce((n:bigint,t:{columns:string})=>n+BigInt(t.columns),0n)!==454n)throw Error('Complete installed table/column count mismatch');
  const epoch=await tx`SELECT c.relname,a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod) AS type,a.attnotnull,a.attgenerated FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE n.nspname=${namespace} AND c.relname IN ('source_epoch_registry','source_epoch_current') ORDER BY c.relname COLLATE pg_catalog."C",a.attnum`;
  const fks=await tx`SELECT c.relname,con.conname,pg_catalog.pg_get_constraintdef(con.oid) AS definition FROM pg_catalog.pg_constraint con JOIN pg_catalog.pg_class c ON c.oid=con.conrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=${namespace} AND c.relname IN ('source_epoch_registry','source_epoch_current') AND con.contype='f' ORDER BY c.relname COLLATE pg_catalog."C",con.conname COLLATE pg_catalog."C"`;
  if(epoch.length!==11||fks.length!==3)throw Error('Epoch columns/FKs mismatch');
  inventory={tables,tableCount:tables.length,columnCount:454,epochColumns:epoch,epochForeignKeys:fks};
  version=(await tx`SELECT version() AS version`)[0].version;
  throw Error('ROLLBACK_LAYOUT_COMPONENT');
 }).catch(e=>{if(e.message!=='ROLLBACK_LAYOUT_COMPONENT')throw e;});
 const after=await sql`SELECT to_regnamespace(${namespace})::text AS n`;
 if(after[0].n!==null)throw Error('Rollback leaked candidate namespace');
 const sources:Record<string,string>={};for(const path of ['scripts/check-source-epoch-layout.ts','docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json','docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql'])sources[path]=new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-layout-native.json',JSON.stringify({database:version,sources,inventory,rollbackNamespaceAbsent:true,scope:'Complete generated candidate DDL in explicitly substituted rollback-only namespace; table/column and epoch FK observations, not full semantic parity, protected installer or deployment adoption',qualified:false},null,2)+'\n');console.log('48 tables, 454 installed columns, 11 epoch columns, three epoch FKs; namespace rolled back.');
}finally{await sql.close();}
