/** Existing UMF encoder compared with independently authored byte expectations. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {encodeCoreKeyTuple,verifyCoreKeyTuple,readCoreKeyTupleBytes} from '/Users/erik/Projects/umf/src/model/key-tuple';
const sourcePath='docs/helix/02-design/contracts/bindings/reference-account-items-v0.1.proposal.umf.json';
const raw=await Bun.file(sourcePath).text();const source=readDocument(raw,'json');
const cases=[
 {name:'Account A',element:'Account',value:'account-α',expectedHex:'554d464b3101040a6163636f756e742dceb1'},
 {name:'Item B',element:'Item',value:'item-b',expectedHex:'554d464b310104066974656d2d62'},
 {name:'Item C',element:'Item',value:'item-c',expectedHex:'554d464b310104066974656d2d63'},
 {name:'Item D',element:'Item',value:'item-d',expectedHex:'554d464b310104066974656d2d64'},
 {name:'same payload other Record',element:'Item',value:'account-α',expectedHex:'554d464b3101040a6163636f756e742dceb1'}];
const owner='/Users/erik/Projects/umf';const git=(args:string[])=>{const r=Bun.spawnSync(['git','-C',owner,...args]);if(r.exitCode)throw Error('owner observation failed');return new TextDecoder().decode(r.stdout).trim();};const before={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};
const outcomes=cases.map(c=>{const receipt=encodeCoreKeyTuple(source,{module:'integration',element:c.element,key:'by-code'},[{string:c.value}]);verifyCoreKeyTuple(receipt,source);const bytes=readCoreKeyTupleBytes(receipt,source);const actualHex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');if(actualHex!==c.expectedHex||receipt.bytesHex!==c.expectedHex||receipt.version!=='2.0.0')throw Error('independent byte mismatch');return {...c,receipt};});
let controls=0;try{encodeCoreKeyTuple(source,{module:'integration',element:'Item',key:'by-code'},[{integerToken:'42'}]);}catch{controls++;}
const forged=structuredClone(outcomes[0]!.receipt);forged.bytesHex=outcomes[1]!.receipt.bytesHex;try{verifyCoreKeyTuple(forged,source);}catch{controls++;}
if(controls!==2)throw Error('malformed tuple accepted');
const after={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};if(JSON.stringify(before)!==JSON.stringify(after)||await Bun.file(sourcePath).text()!==raw)throw Error('source changed');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
await Bun.write('docs/helix/04-build/evidence/design-audit/reference-account-items-key-tuples.json',JSON.stringify({scope:'UMF key operation 2.0.0/umf-key-tuple-v1 five independently authored exact string-key byte expectations and two refusals; not native uniqueness, Truss key admission or Weft mapping',source:{path:sourcePath,sha256:hash(raw)},owner:{root:owner,...before,keyTupleSourceSha256:hash(await Bun.file(owner+'/src/model/key-tuple.ts').text())},outcomes,controls,samePayloadDifferentRecordBytesEqual:outcomes[0]!.receipt.bytesHex===outcomes[4]!.receipt.bytesHex},null,2)+'\n');
console.log(JSON.stringify({byteCases:5,controls,operationVersion:'2.0.0',samePayloadDifferentRecordBytesEqual:true}));
