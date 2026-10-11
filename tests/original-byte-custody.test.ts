import {test,expect} from 'bun:test';
import {runInNewContext} from 'node:vm';
import {copyOriginalByteCustody} from '../packages/postgresql/src/original-byte-custody';
import {mapAssertedOrigin} from '../packages/postgresql/src/asserted-origin-map';
import {decodeCapturedOriginContext} from '../packages/postgresql/src/captured-origin-context';
import {prepareCanonicalWireTree} from '../packages/postgresql/src/canonical-wire-tree';
import {createAcceptanceInputInspector} from '../packages/umf-bun/src/acceptance-input';
import {createCanonicalAcceptanceReportHandoff,createProposedComposedAcceptanceReportHandoff} from '../packages/umf-bun/src/canonical-report-handoff';
const dependencies='/Users/erik/Projects/umf/package.json';
const inspector=await createAcceptanceInputInspector(dependencies),report=await createCanonicalAcceptanceReportHandoff(dependencies),composed=await createProposedComposedAcceptanceReportHandoff(dependencies);
const input=(await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input;
const baseline=(await Bun.file('docs/helix/03-test/report-wire-untrusted.fixture.json').json()).report;
const proposal={...baseline,interfaceVersion:'truss-acceptance-report/0.3.0-proposal',lifecycleProfile:{identity:'test',version:'1',sha256:'a'.repeat(64)},reactivations:[]};
const encode=(s:string)=>new TextEncoder().encode(s),hex=(b:Uint8Array)=>Buffer.from(b).toString('hex');
const context3={interfaceVersion:'truss-native-operation-context/0.3',xid:'1',ordinal:'0',sessionUser:'login',actingUser:'reader',database:'fixture',backendPid:'1',actorRoleOid:'2',sessionRoleOid:'3',assertedOriginUtf8Hex:'6e756c6c',assertedOriginCaptureProfileHex:'01'};
const context4={...context3,interfaceVersion:'truss-native-operation-context/0.4',installationId:'test',sourceEpoch:'epoch',targetIncarnation:'incarnation',sourceEpochProfileHex:'01',sourceEpochEvidenceHex:'02'};
const routes=[['tree','{"flag":true}',prepareCanonicalWireTree],['input',JSON.stringify(input),(b:Uint8Array)=>inspector.inspect(b)],['report',JSON.stringify(baseline),(b:Uint8Array)=>report.prepare(b)],['composed',JSON.stringify(proposal),(b:Uint8Array)=>composed.prepare(b)],['origin','{"flag":true}',(b:Uint8Array)=>mapAssertedOrigin(b,'reader')],['context3',JSON.stringify(context3),(b:Uint8Array)=>{const r=decodeCapturedOriginContext(b);return {...r,originalUtf8Hex:r.originalContextUtf8Hex}}],['context4',JSON.stringify(context4),(b:Uint8Array)=>{const r=decodeCapturedOriginContext(b,'0.4');return {...r,originalUtf8Hex:r.originalContextUtf8Hex}}]] as const;
for(const [name,source,prepare] of routes)test(name+' keeps validation and archived bytes independent of caller callbacks',()=>{
 const bytes=encode(source),expected=prepare(bytes);let calls=0;
 const callback=()=>{calls++;throw Error('caller hook')};
 for(const property of ['length','buffer','slice','constructor'])Object.defineProperty(bytes,property,{get:callback});
 Object.defineProperty(bytes,Symbol.iterator,{value:callback});Object.defineProperty(bytes,Symbol.toStringTag,{get:callback});
 const result=prepare(bytes);expect(result.originalUtf8Hex).toBe(hex(encode(source)));expect(result).toEqual(expected);expect(calls).toBe(0);
 bytes.fill(0);expect(result.originalUtf8Hex).toBe(hex(encode(source)));
});
for(const [name,source,prepare] of routes)test(name+' does not invoke aliasing or throwing species',()=>{
 for(const throwing of [false,true]){
  const bytes=encode(source);let calls=0;
  Object.defineProperty(bytes,'constructor',{value:{[Symbol.species]:function(){calls++;if(throwing)throw Error('species');return bytes}}});
  expect(prepare(bytes).originalUtf8Hex).toBe(hex(encode(source)));expect(calls).toBe(0);
 }
});
test('actual carrier and capacity win over forged caller properties',()=>{
 let calls=0;
 const reasons={tree:'Original ordinary wire byte custody',input:'source_custody',report:'Original report wire byte custody',composed:'Original report wire byte custody',origin:'Original ordinary bounded origin bytes',context3:'Original bounded context bytes',context4:'Original bounded context bytes'};
 for(const [name,source,prepare] of routes){const value=encode(source),shared=new Uint8Array(new SharedArrayBuffer(value.length));shared.set(value);Object.defineProperty(shared,'buffer',{get(){calls++;return new ArrayBuffer(value.length)}});expect(()=>prepare(shared)).toThrow(reasons[name]);}
 expect(calls).toBe(0);
 for(const v of [new Uint16Array([347,305,349]),new Float64Array([91,49,93])])for(const [, ,prepare] of routes)expect(()=>prepare(v as unknown as Uint8Array)).toThrow();
 const large=new Uint8Array(1048577);Object.defineProperty(large,'length',{get(){calls++;return 2}});
 for(const [, ,prepare] of routes)expect(()=>prepare(large)).toThrow();expect(calls).toBe(0);
});
test('intrinsic copies preserve view bounds Buffer carriers and actual cross-realm storage',()=>{
 const view=encode('xx[null]yy').subarray(2,8),copy=copyOriginalByteCustody(view,true);expect(hex(copy)).toBe(hex(encode('[null]')));view.fill(0);expect(hex(copy)).toBe(hex(encode('[null]')));
 expect(hex(copyOriginalByteCustody(Buffer.from('null'),true))).toBe(hex(encode('null')));
 const foreign=runInNewContext('new Uint8Array([110,117,108,108])');expect(prepareCanonicalWireTree(foreign).originalUtf8Hex).toBe('6e756c6c');
 expect(copyOriginalByteCustody(new Uint8Array(1048576)).length).toBe(1048576);expect(()=>copyOriginalByteCustody(new Uint8Array(1048577))).toThrow('resource');
});
test('structural shared copying remains available without promising an atomic snapshot',()=>{
 const source=new Uint8Array(new SharedArrayBuffer(4));source.set(encode('null'));const copied=copyOriginalByteCustody(source);source.fill(0);expect(hex(copied)).toBe('6e756c6c');expect(()=>copyOriginalByteCustody(source,true)).toThrow('carrier');
});

test('selected smaller profile cap is intrinsic and detached storage refuses as custody',()=>{
 const bytes=new Uint8Array(65537);let calls=0;Object.defineProperty(bytes,'length',{get(){calls++;return 1}});
 expect(()=>copyOriginalByteCustody(bytes,true,65536)).toThrow('resource');expect(calls).toBe(0);expect(copyOriginalByteCustody(new Uint8Array(65536),true,65536).length).toBe(65536);
 const detached=encode('null');structuredClone(detached.buffer,{transfer:[detached.buffer]});expect(()=>copyOriginalByteCustody(detached,true)).toThrow('carrier');
});
