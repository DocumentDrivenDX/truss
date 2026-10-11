/** UMF owner import/reload/export of the private configured completion producer. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
const path='packages/postgresql/native/catalog-completion/configured-state-candidate';
const sql=await Bun.file(path+'.sql').text();
const document=await importPostgresqlSql(sql,backend,{id:'truss-configured-catalog-completion-candidate'});
const saved=JSON.stringify(document)+'\n';
const exported=await exportPostgresqlSql(document,backend);
if(await exportPostgresqlSql(readDocument(saved,'json'),backend)!==exported)throw Error('Saved model export correspondence required');
await Bun.write(path+'.umf.json',saved);
await Bun.write(path+'.sql',exported);
console.log(JSON.stringify({scope:'private configured completion owner import/reload/export only',model:path+'.umf.json'}));
