import {SQL} from 'bun';
import {createCanonicalAcceptanceReportHandoff} from '../packages/umf-bun/src/canonical-report-handoff';
import {prepareCanonicalWireTree} from '../packages/postgresql/src/canonical-wire-tree';
const url=process.env.TRUSS_OPERATION_TEST_URL;if(!url)throw Error('Explicit isolated native test URL required');
const handoff=await createCanonicalAcceptanceReportHandoff('/Users/erik/Projects/umf/package.json');
const fixturePath='docs/helix/03-test/report-wire-untrusted.fixture.json';
const fixture=await Bun.file(fixturePath).json();
// Independent byte oracle: UTF-8 ordering, explicit lowercase C0 escapes,
// exact string values and array order. It does not validate/admit the report.
const quote=(s:string)=>'"'+s.replace(/[\u0000-\u001f"\\]/g,c=>c==='"'?'\\"':c==='\\'?'\\\\':'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'))+'"';
function oracle(value:unknown):string{
 if(value===null)return 'null';if(typeof value==='boolean')return String(value);if(typeof value==='string')return quote(value);
 if(Array.isArray(value))return '['+value.map(oracle).join(',')+']';
 if(typeof value!=='object')throw Error('Numeric/free oracle input required');
 const record=value as Record<string,unknown>,keys=Object.keys(record).sort((a,b)=>Buffer.compare(Buffer.from(a),Buffer.from(b)));
 return '{'+keys.map(k=>quote(k)+':'+oracle(record[k])).join(',')+'}';
}
const cases=[{name:'all seventeen untrusted complete-report fields',text:JSON.stringify(fixture.report),report:true},
 {name:'UTF-8 object order, NUL, controls and exact integer string',text:'{"𐀀":"\\u0000\\n\\t😀","":"9007199254740993","a":[true,false,null,{},[]]}',report:false},
 {name:'original whitespace and escape spelling',text:' \n{"z":"\\u0061","a":"\\\\\\\""}\n',report:false}];
// Complete host/oracle preparation before opening the native connection.
const preparedCases=cases.map(c=>{
 const original=new TextEncoder().encode(c.text),prepared=c.report?handoff.prepare(original):prepareCanonicalWireTree(original);
 const expected=Buffer.from(oracle(JSON.parse(c.text))).toString('hex');
 if(prepared.originalUtf8Hex!==Buffer.from(original).toString('hex'))throw Error('Original native case custody changed');
 return {...c,prepared,expected};
});
if(process.argv.includes('--preflight-only')){
 console.log(JSON.stringify({cases:preparedCases.map(c=>c.name),scope:'Host fixture, independent oracle and native carrier preparation only; no native execution.'}));
 process.exit(0);
}
const sql=new SQL(url,{max:1,connectionTimeout:5,idleTimeout:5});
try{
 const observations=await sql.begin(async tx=>{
  // Transaction-local temporary schema; no installed Truss schema or grants altered.
  await tx.unsafe('CREATE TEMP TABLE canonical_codec_anchor(value text) ON COMMIT DROP');
  for(const path of ['packages/postgresql/native/canonical-string-bytes.sql','packages/postgresql/native/canonical-tree-bytes.sql']){
   const source=await Bun.file(path).text();await tx.unsafe(source.replaceAll('truss.runtime_canonical_','pg_temp.runtime_canonical_'));
  }
  const version=await tx.unsafe('SELECT version() AS version');const results=[];
  for(const c of preparedCases){const {prepared,expected}=c;
   const rows=await tx.unsafe("SELECT encode(pg_temp.runtime_canonical_tree_bytes($1::text::jsonb),'hex') AS hex",[prepared.nativeTreeText]);
   if(rows.length!==1||rows[0].hex!==expected)throw Error('Independent native byte mismatch: '+c.name);
   results.push({name:c.name,canonicalSha256:new Bun.CryptoHasher('sha256').update(Buffer.from(expected,'hex')).digest('hex')});
  }
  return {version:version[0].version,cases:results};
 });
 const paths=['scripts/check-canonical-report-native.ts',fixturePath,'packages/postgresql/src/canonical-wire-tree.ts','packages/umf-bun/src/canonical-report-handoff.ts','packages/postgresql/native/canonical-string-bytes.sql','packages/postgresql/native/canonical-tree-bytes.sql'];
 const sources=Object.fromEntries(await Promise.all(paths.map(async p=>[p,new Bun.CryptoHasher('sha256').update(await Bun.file(p).arrayBuffer()).digest('hex')])));
 const receipt={...observations,sources,scope:'Temporary native codec functions and independent original wire byte oracle only. No installed layout, actual report producer/provenance admission, accepted commit or shared resource qualification.'};
 await Bun.write('docs/helix/04-build/evidence/canonical-report-native.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}finally{await sql.close()}
