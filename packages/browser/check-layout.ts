/** Dependency/layout check only; this package does not export a provider yet. */
import {PGlite} from '@electric-sql/pglite';

const layout=await Bun.file(new URL('../python/src/truss/_catalog_runtime/layout.sql',import.meta.url)).text();
const layoutSha256=new Bun.CryptoHasher('sha256').update(layout).digest('hex');
if(layoutSha256!=='c203d09418fb4eddda829d791dda11c20341227c2d1d82e86d4c24afda5e7294')
  throw new Error('Review the changed original generated layout before updating this check');
const db=new PGlite({relaxedDurability:false});
try {
  const version=(await db.query<{version:string;version_num:string}>(
    "SELECT version(),current_setting('server_version_num') AS version_num")).rows[0]!;
  if(version.version_num!=='180006'||!version.version.includes('PGlite 0.5.10'))
    throw new Error('Exact PGlite0.5.10/PostgreSQL18.6 dependency required');
  await db.exec(layout);
  const tables=(await db.query<{tablename:string}>(
    "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='truss' ORDER BY tablename")).rows.map(r=>r.tablename);
  if(tables.length!==48||!['object','edge','schema_doc','object_key_bucket','journal','request_receipt'].every(t=>tables.includes(t)))
    throw new Error('Complete original layout table inventory required');
  const numeric=(await db.query<{integer_value:bigint;decimal_value:string}>(
    'SELECT 9007199254740993::int8 AS integer_value,1.2300::numeric(18,4) AS decimal_value')).rows[0]!;
  if(numeric.integer_value!==9007199254740993n||numeric.decimal_value!=='1.2300')
    throw new Error('Lossless native numeric transport required');
  const receipt={scope:'Bun in-memory layout/dependency execution only',pglite:'0.5.10',host:'Bun '+Bun.version,
    ...version,layoutSha256,tables,numericTransport:{integer:'bigint',decimal:'string'},
    publicProvider:false,browserPersistence:false,localAuthority:false,actionExecution:false};
  const encoded=JSON.stringify(receipt,null,2)+'\n';
  if(Bun.argv[2])await Bun.write(Bun.argv[2],encoded);
  console.log(encoded);
} finally {await db.close();}
