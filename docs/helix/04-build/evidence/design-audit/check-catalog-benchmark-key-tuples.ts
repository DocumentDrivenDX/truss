/** Owner portable-key operation only, not Truss catalog/native key qualification. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {encodeCoreKeyTuple,verifyCoreKeyTuple,readCoreKeyTupleBytes} from '/Users/erik/Projects/umf/src/model/key-tuple';
const owner='/Users/erik/Projects/umf';
const git=(args:string[])=>{const r=Bun.spawnSync(['git','-C',owner,...args]);if(r.exitCode)throw Error('owner observation failed');return new TextDecoder().decode(r.stdout).trim();};
const before={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};
const path='docs/helix/02-design/contracts/bindings/catalog-enumeration-benchmark-v0.1.proposal.umf.json';
const raw=await Bun.file(path).text(),source=readDocument(raw,'json');
const cases=[
 {id:'unicode-code-first-owner',element:'T0001',key:'by-code',values:[{string:'t-α'}],expectedHex:'554d464b31010404742dceb1'},
 {id:'unicode-code-last-owner',element:'T1000',key:'by-code',values:[{string:'t-α'}],expectedHex:'554d464b31010404742dceb1'},
 {id:'composite-large-integer',element:'T0001',key:'by-label-rank',values:[{string:'label'},{integerToken:'9007199254740993'}],expectedHex:'554d464b310204056c6162656c021039303037313939323534373430393933'},
 {id:'composite-large-integer-exponent',element:'T0001',key:'by-label-rank',values:[{string:'label'},{integerToken:'9007199254740993e0'}],expectedHex:'554d464b310204056c6162656c021039303037313939323534373430393933'},
 {id:'composite-zero',element:'T1000',key:'by-label-rank',values:[{string:'x'},{integerToken:'0'}],expectedHex:'554d464b3102040178020130'},
 {id:'composite-unicode-negative',element:'T1000',key:'by-label-rank',values:[{string:'α'},{integerToken:'-42'}],expectedHex:'554d464b31020402ceb102032d3432'}
];
const outcomes=cases.map(c=>{
 const identity={module:'catalog-benchmark',element:c.element,key:c.key};
 const receipt=encodeCoreKeyTuple(source,identity,c.values as any);verifyCoreKeyTuple(receipt,source);
 const bytes=readCoreKeyTupleBytes(receipt,source),actualHex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
 if(actualHex!==c.expectedHex||receipt.bytesHex!==c.expectedHex||receipt.version!=='2.0.0')throw Error('independent expected bytes mismatch: '+c.id);
 return {...c,identity,operation:receipt.operation,version:receipt.version,profile:receipt.profile,actualHex,receiptVerified:true};
});
const identity={module:'catalog-benchmark',element:'T0001',key:'by-label-rank'};
const controls:any[]=[];
for(const [id,key,values,code] of [
 ['missing-component',identity,[{string:'label'}],'KEY_TUPLE_ARITY'],
 ['reversed-wrappers',identity,[{integerToken:'42'},{string:'label'}],'KEY_TUPLE_VALUE'],
 ['missing-key',{...identity,key:'missing'},[{string:'label'},{integerToken:'42'}],'KEY_TUPLE_MISSING'],
 ['fractional-integer',identity,[{string:'label'},{integerToken:'1.5'}],'KEY_TUPLE_ROUNDING']
] as const){
 let actual:string|undefined;try{encodeCoreKeyTuple(source,key,values as any);}catch(e){actual=(e as any).code;}
 if(actual!==code)throw Error('wrong refusal: '+id+' '+actual);controls.push({id,code:actual});
}
if(JSON.stringify(before)!==JSON.stringify({head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])})||await Bun.file(path).text()!==raw)throw Error('original sources changed');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
await Bun.write('docs/helix/04-build/evidence/design-audit/catalog-benchmark-key-tuples.json',JSON.stringify({scope:'Six independently authored exact bytes and four typed refusals against selected UMF key operation 2.0.0/core 0.7 source. Full owner receipts verified in memory; original fixture/inputs/bytes retained here. No Truss identity/catalog/codec/comparator/key-row/uniqueness, Weft binding or native support.',source:{path,sha256:hash(raw)},owner:{root:owner,...before,keyTupleSourceSha256:hash(await Bun.file(owner+'/src/model/key-tuple.ts').text())},outcomes,controls},null,2)+'\n');
console.log(JSON.stringify({byteCases:outcomes.length,controls:controls.length,operationVersion:'2.0.0',nativeExecution:false}));
