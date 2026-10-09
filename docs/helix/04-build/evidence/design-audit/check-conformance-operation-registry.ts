/** Registry descriptor shapes only; no executable registration or trusted authority. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
ajv.addSchema(await Bun.file(root+'acceptance-input-v0.1.schema.json').json());
const validate=ajv.compile(await Bun.file(root+'conformance-operation-registry-v0.1.proposal.schema.json').json());
const pin={identity:'shape-only',version:'0.1',sha256:'a'.repeat(64)};
const artifact={identity:'shape-only',bytesBase64:'',sha256:pin.sha256};
const observer={profile:pin,procedure:artifact,independenceEvidence:artifact};
const entry={operation:'direct.lookup',operationProfile:pin,target:{kind:'registered_method',declaration:artifact,method:'lookup',bindingProfile:pin},callProcedure:artifact,callProfile:pin,argumentSchema:{artifact,pointer:''},resultSchema:{artifact,pointer:'/$defs/outcome'},scopeKinds:['adopted'],semanticContractInventory:artifact,observers:{result:observer,state:observer,journal:observer,report:observer},resourceProfile:pin};
const base={interfaceVersion:'truss-conformance-operation-registry/0.1.0',registryProfile:pin,entries:[entry]};
let count=0;
function witness(name:string,wanted:boolean,change:(x:any)=>void){const x=structuredClone(base);change(x);if(Boolean(validate(x))!==wanted)throw Error(name+': '+JSON.stringify(validate.errors));count++;}
witness('complete descriptor',true,()=>{});
witness('harness procedure descriptor',true,x=>x.entries[0].target={kind:'registered_harness_procedure',procedure:artifact,procedureProfile:pin});
witness('missing declaration',false,x=>delete x.entries[0].target.declaration);
witness('missing required observer',false,x=>delete x.entries[0].observers.journal);
witness('missing independence evidence',false,x=>delete x.entries[0].observers.state.independenceEvidence);
witness('no executable import',false,x=>x.entries[0].target.module='writer.ts');
witness('no SQL callback',false,x=>x.entries[0].sql='SELECT 1');
witness('invalid schema pointer',false,x=>x.entries[0].resultSchema.pointer='/~2');
witness('duplicate scope kind',false,x=>x.entries[0].scopeKinds=['adopted','adopted']);
witness('empty registry',false,x=>x.entries=[]);
witness('duplicate operation requires semantic refusal',true,x=>x.entries.push(structuredClone(x.entries[0])));
witness('unknown method requires trusted registration refusal',true,x=>x.entries[0].target.method='invented');
witness('shared observer evidence is not independence proof',true,()=>{});
witness('reverse identity artifact member refused',false,x=>x.entries[0].identityPaths=artifact);
console.log(count+' registry descriptor shape controls passed. Method recognition, original custody and observer independence remain unqualified.');
export {};
