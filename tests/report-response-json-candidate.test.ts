import {expect,test} from 'bun:test';
import {decodeReportResponseJson as decode,ReportResponseJsonError} from '../docs/helix/04-build/evidence/design-audit/report-response-json-candidate';
import {decodeAcceptanceJson} from '../packages/postgresql/src/acceptance-json';
import base from '../docs/helix/03-test/report-wire-untrusted.fixture.json';
import fixture from '../docs/helix/03-test/report-response-boundary-v0.1.proposal.fixture.json';
const sha=(source:Uint8Array)=>new Bun.CryptoHasher('sha256').update(source).digest('hex');
function source(target:number):Uint8Array{
 const report:any=structuredClone(base.report);
 Object.assign(report,{interfaceVersion:'truss-acceptance-report/0.3.0-proposal',lifecycleProfile:{identity:'synthetic',version:'0.1.0',sha256:'a'.repeat(64)},reactivations:[],rebinds:[]});
 report.diagnostics=[];
 for(let i=0;i<8;i++){
  const raw=Buffer.alloc(i<7?380000:0,97);
  report.diagnostics.push({source:{kind:'input'},diagnosticProfile:{identity:'synthetic',version:'0.1.0',sha256:'a'.repeat(64)},diagnostic:{identity:'diagnostic-'+i,bytesBase64:raw.toString('base64'),sha256:sha(raw)},classification:'upstream_validation'});
 }
 const encode=()=>new TextEncoder().encode(JSON.stringify(report));
 const available=target-encode().length;
 const raw=Buffer.alloc(Math.floor(available/4)*3,97),last=report.diagnostics[7].diagnostic;
 last.bytesBase64=raw.toString('base64');last.sha256=sha(raw);
 last.identity+='x'.repeat(target-encode().length);
 return encode();
}
test('frozen complete report response boundary preserves nineteen fields and request refusal',()=>{
 const bytes=source(4194304);
 expect(bytes.length).toBe(fixture.cases[0].sourceBytes);
 expect(sha(bytes)).toBe(fixture.cases[0].sourceSha256);
 const report=decode(bytes) as Record<string,unknown>;
 expect(Object.keys(report).length).toBe(19);
 expect((report.diagnostics as unknown[]).length).toBe(8);
 expect(()=>decodeAcceptanceJson(bytes)).toThrow();
 const over=source(4194305);
 expect(sha(over)).toBe(fixture.cases[1].sourceSha256);
 expect(()=>decode(over)).toThrow(ReportResponseJsonError);
});
test('numeric nodes, duplicate keys and Unicode refusals remain',()=>{
 for(const text of ['{"rev":9007199254740993}','{"a":null,"a":false}','{"a":"\\ud800"}'])
  expect(()=>decode(new TextEncoder().encode(text))).toThrow(ReportResponseJsonError);
 expect(decode(new TextEncoder().encode('{"rev":"9007199254740993","nil":"\\u0000"}'))).toEqual({rev:'9007199254740993',nil:'\0'});
});
test('logical work exhaustion refuses distinct long keys below byte and member caps',()=>{
 const value:Record<string,null>={};
 for(let i=0;i<64;i++)value['a'.repeat(16384)+i]=null;
 const bytes=new TextEncoder().encode(JSON.stringify(value));
 expect(bytes.length).toBeLessThan(4194304);
 try{decode(bytes);throw Error('Expected work refusal');}
 catch(error){expect(error).toBeInstanceOf(ReportResponseJsonError);expect((error as ReportResponseJsonError).reason).toBe('resource');}
});
