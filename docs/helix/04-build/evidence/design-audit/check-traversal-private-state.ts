/** Private codec shapes, never native frontier completeness or issuer qualification. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
for(const n of ['direct-cursor','direct-traversal-request','traversal-query'])a.addSchema(await Bun.file(`docs/helix/02-design/contracts/${n}-v0.1.schema.json`).json());
const check=a.compile(await Bun.file('docs/helix/02-design/contracts/traversal-private-state-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const owner={documentId:'doc',moduleId:'module'};const start={id:'1',typeId:'1',definitionPin:'fixture',owner};
const query={domain:'truss-direct-traversal-query/0.1.0',context:{catalogRevision:'2',layoutProfile:pin,readProfile:pin,authorizedScopeIdentity:'scope',consistency:{kind:'held_snapshot',snapshotIdentity:'snapshot'}},start,hops:[{relationship:{relationshipId:'2',definitionPin:'fixture',owner},direction:'outgoing'}]};
const base={interfaceVersion:'truss-traversal-private-state/0.1.0',stageIdentity:'stage',generation:'0',workVersion:'0',accountingVersion:'0',query,resourceProfile:pin,counters:{examinedEdges:'0',pathStates:'1',retainedBytes:'1000',activeWorkMilliseconds:'0'},terminalIdentities:[]};
const working={...base,phase:'working',frontier:[{path:[start],nextHop:'0',scan:{state:'first'}}]};
const sealed={...base,phase:'sealed'};
const cases:[string,unknown,boolean][]=[
 ['missing accounting version rejects',Object.fromEntries(Object.entries(working).filter(([k])=>k!=='accountingVersion')),false],
 ['stale ledger version semantic refusal',{...working,accountingVersion:'99'},true],
 ['initial frontier',working,true],['sealed empty',sealed,true],
 ['after exact edge',{...working,frontier:[{...working.frontier[0],scan:{state:'after',id:'2',orderKey:{state:'null'}}}]},true],
 ['working requires frontier',{...base,phase:'working'},false],
 ['empty frontier must seal',{...working,frontier:[]},false],
 ['sealed cannot retain frontier',{...sealed,frontier:working.frontier},false],
 ['no query budget controls',{...working,query:{...query,resultLimit:'10'}},false],
 ['no mutable page offset',{...sealed,offset:'10'},false],
 ['host numeric counter rejects',{...working,counters:{...base.counters,pathStates:1}},false],
 ['after needs edge ordering',{...working,frontier:[{...working.frontier[0],scan:{state:'after',id:'2'}}]},false],
 ['four path members rejects',{...working,frontier:[{...working.frontier[0],path:[start,start,start,start]}]},false],
 ['path repetition semantic refusal',{...working,frontier:[{...working.frontier[0],path:[start,start],nextHop:'1'}]},true],
 ['wrong hop position semantic refusal',{...working,frontier:[{...working.frontier[0],nextHop:'2'}]},true],
 ['false sealed completeness native refusal',{...sealed,terminalIdentities:[{...start,id:'99'}]},true],
 ['reset work counter semantic refusal',{...sealed,counters:{...base.counters,pathStates:'0'}},true]
];
const failures=cases.filter(([,v,e])=>Boolean(check(v))!==e).map(([n])=>n);
console.log(JSON.stringify({scope:'private codec shapes; semantic counterexamples intentionally shape-valid',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
