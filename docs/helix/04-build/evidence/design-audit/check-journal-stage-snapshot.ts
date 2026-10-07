/** Shape checks only; no native body, descriptor, eligibility or settlement proof. */
const {default:Ajv}=await import(process.argv[2]);
const path='docs/helix/02-design/contracts/journal-stage-snapshot-v0.2.proposal.schema.json';
const schema=await Bun.file(path).json(),v=new Ajv({strict:true}).compile(schema);
const fixture=()=>({interfaceVersion:'truss-journal-stage-snapshot/0.2.0-proposal',kind:'journal-stage',fields:{original_writer_xid:'7',operation_ordinal:'0',stage_name:'publication',stage_ordinal:'0',effect_generation:'2',body_bytes_hex:'7b7d'}}) as any;
const cases:[string,(x:any)=>void,boolean][]=[
 ['complete raw snapshot',()=>{},true],['missing body',x=>{delete x.fields.body_bytes_hex},false],['extra commit claim',x=>{x.committed=true},false],['numeric generation',x=>{x.fields.effect_generation=2},false],['wrong kind',x=>{x.kind='operation'},false],['odd hex',x=>{x.fields.body_bytes_hex='abc'},false],['uppercase hex',x=>{x.fields.body_bytes_hex='AB'},false],['noncanonical ordinal',x=>{x.fields.stage_ordinal='00'},false],['unknown phase remains integrity counterexample',x=>{x.fields.stage_name='unknown'},true],['empty bytes remain integrity counterexample',x=>{x.fields.body_bytes_hex=''},true],['native range overflow requires semantic refusal',x=>{x.fields.operation_ordinal='999999999999999999999999'},true],['future generation requires native refusal',x=>{x.fields.effect_generation='3'},true]];
const results=cases.map(([name,change,expected])=>{const x=fixture();change(x);const actual=v(x);if(actual!==expected)throw Error(name+JSON.stringify(v.errors));return {name,expected,actual}});
const sourceHashes=await Promise.all([path,import.meta.path].map(async p=>({path:p,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(p).text()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-stage-snapshot-audit.json',JSON.stringify({scope:'closed raw snapshot shape only',bunVersion:Bun.version,sourceHashes,results,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({cases:results.length,nativeExecuted:false}));
