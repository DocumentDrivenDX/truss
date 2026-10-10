import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql/index';
import {writeDocument,readDocument} from '/Users/erik/Projects/umf/src/index';
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
const root='/private/tmp/claude-501/truss-spec-wt/docs/helix/02-design';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
for (const [id,file] of [['truss-layout-0.2','storage-layout.sql'],['truss-module-isolation-0.2','module-isolation.sql']]) {
 const source=await Bun.file(`${root}/contracts/${file}`).text();
 const model=await importPostgresqlSql(source,backend,{id});
 const modelJson=writeDocument(model,'json');
 const roundtrip=readDocument(modelJson,'json');
 if(getPostgresqlSource(roundtrip)!==source)throw Error('Source archive changed');
 const generated=await exportPostgresqlSql(roundtrip,backend);
 const repeated=await exportPostgresqlSql(readDocument(modelJson,'json'),backend);
 if(generated!==repeated)throw Error('Generation nondeterministic');
 await Bun.write(`${root}/models/${id}.umf.json`,modelJson+'\n');
 await Bun.write(`${root}/models/${id}.generated.sql`,generated+'\n');
 await Bun.write(`${root}/models/${id}.generation.json`,JSON.stringify({profile:'truss-native-layout-capture/0.1.0',id,layoutVersion:'0.2',source:file,sourceSha256:hash(source),modelSha256:hash(modelJson+'\n'),generatedSqlSha256:hash(generated+'\n'),umfVersion:model.umf,backendIdentity:backend.identity,checks:{sourceArchiveExact:true,jsonRoundtrip:true,deterministicExport:true,umfNativeExportGuard:true},qualification:'design-candidate',notEstablished:['independent catalog parity','PostgreSQL 16/17 execution','PL/pgSQL body validation','complete coverage inventory','browser execution','authority transition']},null,2)+'\n');
 console.log(`${id}: retained source and deterministic UMF native generation; not installation-qualified`);
}
