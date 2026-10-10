/** Temporary native encoding versus independent whole-wire bytes; no acceptance authority. */
import {createProposedComposedAcceptanceReportHandoff} from '../../../../../packages/umf-bun/src/canonical-report-handoff';
const args=process.argv.slice(2);
if(args.length>1||(args.length===1&&args[0]!=='--python'))throw Error('Only --python carrier mode is supported');
const pythonMode=args[0]==='--python';
const bridgePath='docs/helix/04-build/evidence/design-audit/prepare_python_native_report_carrier.py';
const hash=(bytes:string|Uint8Array)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
const fixturePath='docs/helix/03-test/report-wire-untrusted.fixture.json';
const base=structuredClone((await Bun.file(fixturePath).json()).report);
base.interfaceVersion='truss-acceptance-report/0.3.0-proposal';
base.lifecycleProfile={identity:'synthetic',version:'0.1.0',sha256:'a'.repeat(64)};
base.reactivations=[];base.rebinds=[];
if(Object.keys(base).length!==19)throw Error('Complete original report field membership required');
// Unicode-string oracle follows the published byte grammar, independently of
// native byte inspection, task frames and scalar helpers.
const quote=(value:string)=>'"'+value.replace(/[\u0000-\u001f"\\]/g,c=>c==='"'?'\\"':c==='\\'?'\\\\':'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'))+'"';
function oracle(value:unknown):string{
 if(value===null)return 'null';if(typeof value==='boolean')return String(value);
 if(typeof value==='string')return quote(value);
 if(Array.isArray(value))return '['+value.map(oracle).join(',')+']';
 if(!value||typeof value!=='object')throw Error('Numeric-free independent oracle required');
 const record=value as Record<string,unknown>;
 const keys=Object.keys(record).sort((a,b)=>Buffer.compare(Buffer.from(a),Buffer.from(b)));
 return '{'+keys.map(key=>quote(key)+':'+oracle(record[key])).join(',')+'}';
}
const withAsserted=(asserted:unknown)=>{const report=structuredClone(base);report.originalExecution.origin.asserted=asserted;return report;};
const integerKeySource=JSON.stringify(withAsserted('raw-key-order-sentinel')).replace('"raw-key-order-sentinel"','{"10":"ten","2":"two","01":"leading","0":"zero"}');
const cases:{name:string;report:any;source?:string}[]=[{name:'complete-wire-original-integer-key-order',report:JSON.parse(integerKeySource),source:integerKeySource},{name:'complete-nineteen-field-wire',report:structuredClone(base)},
 {name:'complete-wire-short-escape-expansion',report:withAsserted({'x-large-original':'\n'.repeat(200000)})},
 {name:'complete-wire-large-original-key',report:withAsserted({['x-'+ 'é'.repeat(40000)]:'original'})},
 {name:'complete-wire-UTF8-key-order-and-array-order',report:withAsserted({'𐀀':'supplementary','':'private','e\u0301':'decomposed','é':'composed','x-order':[null,false,true,'',{},[]],'x-NUL\0':'\0\n\\"'})}];
const codec=await createProposedComposedAcceptanceReportHandoff('/Users/erik/Projects/umf/package.json');
let pythonEnvironment:unknown;
const prepared=[];
for(const c of cases){
 const source=Buffer.from(c.source??JSON.stringify(c.report)),handoff=codec.prepare(source),expected=Buffer.from(oracle(c.report));
 if(handoff.originalUtf8Hex!==source.toString('hex'))throw Error('Original complete report wire changed');
 if(pythonMode){
  const bridge=Bun.spawn(['/private/tmp/truss-python-report-schema-env/bin/python',bridgePath],{env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},stdin:'pipe',stdout:'pipe',stderr:'pipe'});
  bridge.stdin.write(source);bridge.stdin.end();
  const [out,err,code]=await Promise.all([new Response(bridge.stdout).text(),new Response(bridge.stderr).text(),bridge.exited]);
  if(code)throw Error('Python carrier preparation refused: '+err);
  const python=JSON.parse(out);
  if(pythonEnvironment!==undefined&&JSON.stringify(pythonEnvironment)!==JSON.stringify(python.environment))throw Error('Python environment changed during observation');
  pythonEnvironment=python.environment;
  if(python.originalUtf8Hex!==handoff.originalUtf8Hex||python.nativeTaskCount!==handoff.nativeTaskCount)throw Error('Full Python/TypeScript carrier correspondence differs: '+c.name);
  const carrierBytesEqual=python.nativeTreeText===handoff.nativeTreeText;
  if(c.name==='complete-wire-original-integer-key-order'&&carrierBytesEqual)throw Error('Original integer-key order divergence control missing');
  prepared.push({...c,name:c.name+'-typescript',source,handoff,expected,carrierBytesEqual});
  prepared.push({...c,name:c.name+'-python',source,handoff:{...handoff,nativeTreeText:python.nativeTreeText},expected,carrierBytesEqual});
 }else prepared.push({...c,source,handoff,expected});
}
const scalarPath='docs/helix/02-design/contracts/report-scalar-bytes-v0.2.proposal.sql';
const treePath='docs/helix/02-design/contracts/report-tree-bytes-v0.2.proposal.sql';
const scalar=await Bun.file(scalarPath).text(),tree=await Bun.file(treePath).text();
const temporary=(source:string)=>source.replaceAll('truss.runtime_report_','pg_temp.runtime_report_');
const argument=(text:string)=>`convert_from(decode('${Buffer.from(text).toString('hex')}','hex'),'UTF8')::jsonb`;
const sql=['BEGIN;',"SET LOCAL statement_timeout='15s';",'CREATE TEMP TABLE tree_anchor(value text) ON COMMIT DROP;',temporary(scalar),temporary(tree),"SELECT 'server|'||current_setting('server_version_num');"];
for(const c of prepared)sql.push(`SELECT '${c.name}|'||encode(pg_temp.runtime_report_tree_bytes_v0_2(${argument(c.handoff.nativeTreeText)}),'hex');`);
const invalid=[{name:'duplicate-original-key',state:'22023',value:{kind:'object',members:[{keyUtf8Hex:'61',node:{kind:'null'}},{keyUtf8Hex:'61',node:{kind:'null'}}]}},
 {name:'invalid-UTF8-key',state:'22021',value:{kind:'object',members:[{keyUtf8Hex:'80',node:{kind:'null'}}]}},
 {name:'invalid-UTF8-value',state:'22021',value:{kind:'string',utf8Hex:'eda080'}},
 {name:'unknown-node-kind',state:'22023',value:{kind:'number',value:'1'}},
 {name:'container-capacity',state:'54000',value:{kind:'array',items:Array.from({length:4097},()=>({kind:'null'}))}},
 {name:'whole-output-capacity',state:'54000',value:{kind:'array',items:Array.from({length:5},()=>({kind:'string',utf8Hex:'0a'.repeat(200000)}))}}];
for(const c of invalid){
 sql.push(`DO $$ BEGIN BEGIN PERFORM pg_temp.runtime_report_tree_bytes_v0_2(${argument(JSON.stringify(c.value))}); RAISE EXCEPTION 'invalid tree accepted'; EXCEPTION WHEN SQLSTATE '${c.state}' THEN NULL; END; END $$;`);
 sql.push(`SELECT '${c.name}|refused_${c.state}';`);
}
sql.push('ROLLBACK;');
const nativeProcess=Bun.spawn(['docker','exec','-i','truss-runtime-admission','psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-U','postgres','-d','postgres'],{stdin:'pipe',stdout:'pipe',stderr:'pipe'});
nativeProcess.stdin.write(sql.join('\n'));nativeProcess.stdin.end();
const [stdout,stderr,status]=await Promise.all([new Response(nativeProcess.stdout).text(),new Response(nativeProcess.stderr).text(),nativeProcess.exited]);
if(status)throw Error(stderr);
const lines=stdout.trim().split('\n');
if(lines.length!==1+prepared.length+invalid.length||!lines[0].startsWith('server|'))throw Error('Complete native observation inventory required');
const results=[];
for(let i=0;i<prepared.length;i++){
 const c=prepared[i]!;if(lines[i+1]!==c.name+'|'+c.expected.toString('hex'))throw Error('Complete independent native bytes differ: '+c.name);
 results.push({name:c.name,originalFields:Object.keys(c.report).length,sourceBytes:c.source.length,originalSourceSha256:hash(c.source),canonicalBytes:c.expected.length,canonicalSha256:hash(c.expected),completeOriginalBytesEqual:true,...('carrierBytesEqual' in c?{carrierBytesEqual:c.carrierBytesEqual}:{})});
}
for(let i=0;i<invalid.length;i++){
 const c=invalid[i]!;if(lines[prepared.length+i+1]!==c.name+'|refused_'+c.state)throw Error('Expected native refusal differs: '+c.name);
 results.push({name:c.name,observedSqlState:c.state});
}
const paths=[import.meta.path,fixturePath,scalarPath,treePath,'packages/umf-bun/src/canonical-report-handoff.ts','packages/postgresql/src/canonical-wire-tree.ts','packages/postgresql/src/acceptance-json.ts'];
if(pythonMode)paths.push(bridgePath,'docs/helix/04-build/evidence/design-audit/python_report_wire_candidate.py','docs/helix/04-build/evidence/design-audit/python_raw_json_candidate.py','docs/helix/04-build/evidence/design-audit/python_native_report_carrier_candidate.py');
const sourcePins=Object.fromEntries(await Promise.all(paths.map(async path=>[path,hash(new Uint8Array(await Bun.file(path).arrayBuffer()))])));
const receipt={status:'passed_temporary_complete_wire_encoding',pythonEnvironment,carrierHost:pythonMode?'Python 3.11 private candidate':'TypeScript private candidate',serverVersionNum:lines[0].slice(7),schemaPins:codec.schemaPins,sourcePins,results,scope:'Five complete nineteen-field synthetic report wires (both host carriers separately in Python mode) and six private inert-tree refusal controls in temporary functions, explicitly rolled back. Full-byte encoding parity only; no semantic report provenance, installed native authority/grants, resource account or accepted commit.'};
await Bun.write('docs/helix/04-build/evidence/design-audit/'+(pythonMode?'python-report-tree-native.json':'report-tree-native.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(results.length+' native tree observations passed; complete wire encoding only');
