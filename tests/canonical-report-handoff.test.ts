import {test,expect} from 'bun:test';
import {createCanonicalAcceptanceReportHandoff} from '../packages/umf-bun/src/canonical-report-handoff';
const codec=await createCanonicalAcceptanceReportHandoff('/Users/erik/Projects/umf/package.json');
const fixture=(await Bun.file('docs/helix/03-test/report-wire-untrusted.fixture.json').json()).report;
const wire=(value:unknown)=>new TextEncoder().encode(JSON.stringify(value));
test('all seventeen report fields reach the native codec carrier without accepted authority',()=>{
 const source=wire(fixture),result=codec.prepare(source),tree=JSON.parse(result.nativeTreeText);expect(tree.kind).toBe('object');expect(tree.members.length).toBe(17);expect(Buffer.from(result.originalUtf8Hex,'hex')).toEqual(Buffer.from(source));expect(result.scope).toBe('complete_report_wire_codec_handoff_only');
});
test('each missing complete-report field and extra acceptance claims refuse',()=>{
 for(const field of Object.keys(fixture)){const candidate=structuredClone(fixture);delete candidate[field];expect(()=>codec.prepare(wire(candidate))).toThrow('complete report wire')}
 expect(()=>codec.prepare(wire({...fixture,accepted:true}))).toThrow('complete report wire');
});
test('numeric counts and projected assertion scope cannot become complete report codec input',()=>{
 expect(()=>codec.prepare(wire({...fixture,counts:{...fixture.counts,typesAdded:0}}))).toThrow('numeric_node');expect(()=>codec.prepare(wire({...fixture,assertions:{...fixture.assertions,scope:{kind:'authorized_projection',authorizedScopeIdentity:'scope'}}}))).toThrow('complete report wire');
});
test('shape-valid source and effect forgeries remain visibly codec-only',()=>{
 const candidate=structuredClone(fixture);candidate.documents=[];candidate.originalExecution.origin.databaseRole='invented';expect(codec.prepare(wire(candidate)).scope).toBe('complete_report_wire_codec_handoff_only');
});
test('pinned 0.1 codec refuses proposed or guessed report versions without conversion',()=>{
 for(const version of ['truss-acceptance-report/0.2.0-proposal','truss-acceptance-report/0.3.0-proposal','truss-acceptance-report/0.1','unknown']){
  expect(()=>codec.prepare(wire({...fixture,interfaceVersion:version}))).toThrow('complete report wire');
 }
 expect(codec.prepare(wire(fixture)).scope).toBe('complete_report_wire_codec_handoff_only');
});
