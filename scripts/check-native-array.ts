/** Host-only read-only native text/dimensions/JSON correspondence probe. */
import {decodeNativeTextArray} from '../packages/postgresql/src/index';
import {writeFile} from 'node:fs/promises';
const sql = `SELECT json_agg(json_build_object('label',label,'text',a::text,'dimensions',array_dims(a),'raw',array_to_json(a))) FROM (VALUES ('null',NULL::text[]),('empty','{}'::text[]),('null-text','{NULL,"NULL"}'::text[]),('empty-text','{""}'::text[]),('bounds','[0:1]={a,b}'::text[]),('quoted','{"a,b","{c}"}'::text[]),('nested','{{a,b},{c,d}}'::text[])) AS v(label,a);`;
const result = Bun.spawnSync(['/usr/local/bin/docker','exec','ashlar-e2e-truss-pg17','psql','-U','postgres','-d','truss_e2e','-X','-A','-t','-c',sql]);
if(result.exitCode!==0) throw Error(new TextDecoder().decode(result.stderr));
const originalStdout=new TextDecoder('utf-8',{fatal:true}).decode(result.stdout);
const rows=JSON.parse(originalStdout);
if(!Array.isArray(rows)||rows.length!==7) throw Error('Incomplete original observation');
const decoded=rows.map(row=>{
  const value=decodeNativeTextArray(row.text,row.dimensions,{maxBytes:4096,maxNodes:128,maxDepth:6});
  const elements=value.kind==='native-null'?null:value.elements;
  if(JSON.stringify(elements)!==JSON.stringify(row.raw)) throw Error('Original native JSON correspondence');
  return {label:row.label,value};
});
await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/native-array.json',import.meta.url),JSON.stringify({
  profile:'truss-bootstrap-native-array-decoder/0.1.0',sql,originalStdout,decoded,
  qualification:'Seven constant ordinary text-array observations on existing local PostgreSQL 17.9; exact decoded JSON correspondence. No ACL interpretation, complete catalog collection, native installation or driver/resource qualification.'},null,2)+'\n');
console.log('Seven original native array observations match original JSON; no mutations.');
