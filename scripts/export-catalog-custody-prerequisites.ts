// SPDX-License-Identifier: MIT OR Apache-2.0
/** Export candidate capture functions through UMF's owner AST, preserving reload parity. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
const root=process.argv[2];
if(!root)throw Error('Explicit candidate directory required');
for(const name of ['composition-admission','registration-capture','registrar','prerequisites']){
  const path=root+'/'+name;
  const model=await importPostgresqlSql(await Bun.file(path+'.sql').text(),backend,{id:'truss-catalog-custody-'+name+'-candidate'});
  const saved=JSON.stringify(model)+'\n';
  const original=await exportPostgresqlSql(model,backend);
  if(await exportPostgresqlSql(readDocument(saved,'json'),backend)!==original)throw Error('Owner reload/export mismatch');
  await Bun.write(path+'.umf.json',saved);
  await Bun.write(path+'.owner-export.sql',original);
}
