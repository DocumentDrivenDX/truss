/** Source retention only; native tests prove the verifier's behavior separately. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
const object=process.argv[2]==='object';
const path='packages/postgresql/native/'+(object?'verify-object-string-key':'verify-umf-string-key-tuple');
const source=await Bun.file(path+'.sql').text();
const model=await importPostgresqlSql(source,backend,{id:object?'truss-object-string-key-verifier':'truss-umf-string-key-verifier'});
const original=JSON.stringify(model)+'\n';
const sql=await exportPostgresqlSql(model,backend);
if(await exportPostgresqlSql(readDocument(original,'json'),backend)!==sql)throw Error('Saved verifier model changed SQL export');
await Bun.write(path+'.umf.json',original);
console.log(JSON.stringify({source:path+'.sql',model:path+'.umf.json',scope:'owner import/reload/export retention only'}));
