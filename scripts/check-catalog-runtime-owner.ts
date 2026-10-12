/** Verify that the packaged catalog SQL can be retained and exported by UMF. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';

const root='packages/python/src/truss/_catalog_runtime';
for (const name of ['layout','lineage','plan','runtime','barrier','view','read','keys','groups']) {
  const source=await Bun.file(`${root}/${name}.sql`).text();
  const model=await importPostgresqlSql(source,backend,{id:`truss-catalog-runtime-${name}`});
  const serialized=JSON.stringify(model)+'\n';
  const exported=await exportPostgresqlSql(model,backend);
  const reloaded=await exportPostgresqlSql(readDocument(serialized,'json'),backend);
  if(exported!==reloaded)throw Error(`UMF reload changed ${name} SQL`);
  console.log(JSON.stringify({source:`${root}/${name}.sql`,modelReloadExportEqual:true}));
}
