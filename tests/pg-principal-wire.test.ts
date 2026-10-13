import {test,expect} from 'bun:test';
import {decodeResponseFrame,ResponseIngress} from '../packages/pg-runtime/src/wire';
const encode=new TextEncoder();
const frame=(kind:string,body:Uint8Array)=>{const result=new Uint8Array(body.length+5);result[0]=kind.charCodeAt(0);new DataView(result.buffer).setUint32(1,body.length+4);result.set(body,5);return result;};
const status=(name:string,value:string)=>frame('S',encode.encode(name+'\0'+value+'\0'));
const limits={maxFrameBytes:1024,maxFields:16,maxTotalBytes:4096,maxFrames:16};
test('ParameterStatus preserves original UTF-8 name/value bytes',()=>{
 const bytes=status('application_name','Δ context');const result=decodeResponseFrame(bytes,limits);
 expect(result.fields).toEqual([{name:'application_name',value:'Δ context'}]);expect(result.originalHex).toBe(Buffer.from(bytes).toString('hex'));
});
test('ParameterStatus cannot manufacture command or Ready completion',()=>{
 const ingress=new ResponseIngress(limits);ingress.feed(status('application_name','changed'),()=>{});expect(()=>ingress.finish()).toThrow();
 const ready=new ResponseIngress(limits);ready.feed(status('application_name','changed'),()=>{});expect(()=>ready.feed(frame('Z',encode.encode('I')),()=>{})).toThrow();
});
test('Fragmented ParameterStatus interleaves with confirmed reset without changing completion',()=>{
 const ingress=new ResponseIngress(limits);const kinds:string[]=[];
 for(const original of [status('session_authorization','ordinary'),frame('C',encode.encode('RESET\0')),status('application_name','restored'),frame('Z',encode.encode('I'))])for(const byte of original)ingress.feed(new Uint8Array([byte]),f=>kinds.push(String.fromCharCode(f[0])));
 ingress.finish();expect(kinds).toEqual(['S','C','S','Z']);expect(ingress.accounting.frames).toBe(4);
 expect(()=>ingress.feed(status('application_name','late'),()=>{})).toThrow();
});
test('Malformed, non-UTF8 and over-budget parameter reports refuse',()=>{
 for(const bytes of [frame('S',encode.encode('name\0missing-terminator')),frame('S',new Uint8Array([110,0,255,0])),frame('S',encode.encode('name\0value\0extra\0'))])expect(()=>decodeResponseFrame(bytes,limits)).toThrow();
 expect(()=>decodeResponseFrame(status('name','value'),{...limits,maxFields:0})).toThrow();
 expect(()=>new ResponseIngress({...limits,maxFrames:0}).feed(status('name','value'),()=>{})).toThrow();
});

test('pending reset cannot publish a lease after another reset closes admission',async()=>{
 const run=Bun.spawn([process.execPath,import.meta.dir+'/pg-principal-admission-race-runner.ts'],{stdout:'pipe',stderr:'pipe'});
 const [stdout,stderr,code]=await Promise.all([new Response(run.stdout).text(),new Response(run.stderr).text(),run.exited]);
 if(code!==0)throw Error(stderr);expect(code).toBe(0);
 const receipt=JSON.parse(stdout);expect(receipt.quarantinedCount).toBe(2);
 expect(receipt.second.error).toContain('Host admission closed');
});
