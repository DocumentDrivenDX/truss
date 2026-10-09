import {test,expect} from 'bun:test';
import {createCanonicalAcceptanceReportHandoff,createProposedComposedAcceptanceReportHandoff} from '../packages/umf-bun/src/canonical-report-handoff';
const dependencies='/Users/erik/Projects/umf/package.json';
const baseline=await createCanonicalAcceptanceReportHandoff(dependencies);
const composed=await createProposedComposedAcceptanceReportHandoff(dependencies);
const original=(await Bun.file('docs/helix/03-test/report-wire-untrusted.fixture.json').json()).report;
const pin={identity:'synthetic',version:'0.1.0',sha256:'a'.repeat(64)};
const artifact={identity:'synthetic',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const present={present:true,value:{kind:'null'}},absent={present:false};
const rebind={interfaceVersion:'truss-history-event/0.2.0-proposal',sourceEpoch:'epoch',historyProfile:'synthetic',xid:'1',seq:'1',identity:{id:'1',typeId:'1',definitionPin:'synthetic',owner:{documentId:'doc',moduleId:'module'}},eventVersion:'2',eventCatalogRevision:'1',mutationGroup:{profile:'truss-history-group/0.1.0',eventCount:'1',orderedEventDigest:'0'.repeat(64)},origin:{asserted:{kind:'null'},databaseRole:'role'},operation:'rebind',retainedName:'a',propertyId:'1',beforeDefinitionContext:'before',afterDefinitionPin:'after',retainedBefore:present,retainedAfter:absent,propertyBefore:absent,propertyAfter:present};
const candidate={...original,interfaceVersion:'truss-acceptance-report/0.3.0-proposal',lifecycleProfile:pin,reactivations:[{identity:{kind:'key',typeId:'1',keyNumber:'1'},owner:{documentId:'doc',moduleId:'module'},lineage:artifact,beforeRetiredRevision:'1',beforeDefinition:artifact,afterDefinition:artifact}],rebinds:[rebind]};
const wire=(value:unknown)=>new TextEncoder().encode(JSON.stringify(value));
test('explicit composed codec preserves nineteen fields and full original bytes',()=>{
 const bytes=wire(candidate),result=composed.prepare(bytes);
 expect(JSON.parse(result.nativeTreeText).members.length).toBe(19);
 expect(Buffer.from(result.originalUtf8Hex,'hex')).toEqual(Buffer.from(bytes));
 expect(result.scope).toBe('complete_report_wire_codec_handoff_only');
 expect(Object.keys(composed.schemaPins).length).toBe(11);
});
test('baseline and composed versions cannot silently substitute for each other',()=>{
 expect(()=>baseline.prepare(wire(candidate))).toThrow('complete report wire');
 expect(()=>composed.prepare(wire(original))).toThrow('complete report wire');
 for(const field of ['lifecycleProfile','reactivations']){
  const changed={...candidate} as Record<string,unknown>;delete changed[field];
  expect(()=>composed.prepare(wire(changed))).toThrow('complete report wire');
 }
});
test('rebind-only selected event version and exact owner-local key shape remain closed',()=>{
 for(const event of [{...rebind,interfaceVersion:'truss-history-event/0.1.0'},{...rebind,operation:'retain'}])
  expect(()=>composed.prepare(wire({...candidate,rebinds:[event]}))).toThrow('complete report wire');
 expect(()=>composed.prepare(wire({...candidate,reactivations:[{...candidate.reactivations[0],identity:{kind:'key',keyNumber:'1'}}]}))).toThrow('complete report wire');
});
test('codec scope cannot establish completeness or native transition meaning',()=>{
 expect(composed.prepare(wire({...candidate,reactivations:[],rebinds:[]})).scope).toBe('complete_report_wire_codec_handoff_only');
});
test('every selected field is mandatory and unknown claims refuse',()=>{
 for(const field of Object.keys(candidate)){
  const changed={...candidate} as Record<string,unknown>;delete changed[field];
  expect(()=>composed.prepare(wire(changed))).toThrow('complete report wire');
 }
 expect(()=>composed.prepare(wire({...candidate,accepted:true}))).toThrow('complete report wire');
});
test('prepared byte custody survives caller mutation and rejects oversized wire',()=>{
 const source=wire(candidate),expected=Buffer.from(source),result=composed.prepare(source);
 source.fill(0);
 expect(Buffer.from(result.originalUtf8Hex,'hex')).toEqual(expected);
 expect(()=>composed.prepare(new Uint8Array(1048577))).toThrow('capacity');
});
