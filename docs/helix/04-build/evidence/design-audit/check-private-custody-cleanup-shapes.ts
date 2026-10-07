import Ajv from '/private/tmp/weft-build/node_modules/ajv/dist/2020.js';
const base='docs/helix/02-design/contracts/';
const source='private-custody-cleanup-selection-v0.1.proposal.schema.json';
const dependency='acceptance-input-v0.1.schema.json';
const ajv=new Ajv({strict:false});
ajv.addSchema(await Bun.file(base+dependency).json());
const validate=ajv.compile(await Bun.file(base+source).json());
const artifact={identity:'original-fixture',bytesBase64:'YQ==',sha256:'0'.repeat(64)};
const operation={kind:'operation',originalWriterXid:'7',operationOrdinal:'0',originalRow:artifact,originalSettlement:artifact};
const touch={kind:'touch',originalWriterXid:'7',ownerKind:'edge',ownerId:'-1',ownerDiscriminatorId:'2',propertyOwnerTypeId:'3',propertyId:'4',originalRow:artifact,originalSettlement:artifact};
const fixture=()=>({interfaceVersion:'truss-private-custody-cleanup-selection/0.1.0',profile:{identity:'fixture',version:'0.1.0',sha256:'0'.repeat(64)},originalInstallation:artifact,originalLayout:artifact,originalAdministrativeContext:artifact,originalResourceReservation:artifact,rows:[operation],dependencies:[],originalDependencyClosure:artifact,originalCapacityDisposition:artifact} as any);
const cases:[string,boolean,(x:any)=>void][]=[
 ['operation-only',true,()=>{}],['touch-only',true,x=>x.rows=[touch]],['mixed',true,x=>x.rows=[operation,touch]],
 ['512 combined rows shape',true,x=>x.rows=Array(512).fill(operation)],['513 combined rows',false,x=>x.rows=Array(513).fill(operation)],
 ['empty selection',false,x=>x.rows=[]],['missing settlement',false,x=>{x.rows=[{...operation}];delete x.rows[0].originalSettlement;}],
 ['fake property on operation',false,x=>x.rows=[{...operation,propertyId:'0'}]],['missing touch identity',false,x=>{x.rows=[{...touch}];delete x.rows[0].ownerDiscriminatorId;}],
 ['numeric ordinal',false,x=>x.rows=[{...operation,operationOrdinal:0}]],['noncanonical ordinal',false,x=>x.rows=[{...operation,operationOrdinal:'01'}]],
 ['invalid dependency disposition',false,x=>x.dependencies=[{originalDependency:artifact,disposition:'expire',originalDispositionEvidence:artifact}]],
 ['missing closure',false,x=>{delete x.originalDependencyClosure;}],['caller permit',false,x=>x.authorized=true],
 ['duplicate membership needs semantic refusal',true,x=>x.rows=[operation,operation]],
 ['overflow needs native-domain refusal',true,x=>x.rows=[{...operation,operationOrdinal:'9223372036854775808'}]],
 ['wrong snapshot bytes need semantic refusal',true,x=>x.rows=[{...touch,originalRow:artifact}]],
 ['empty dependencies need absence proof',true,()=>{}]
];
const observations=cases.map(([name,expected,mutate])=>{const x=fixture();mutate(x);const actual=Boolean(validate(x));if(actual!==expected)throw Error(name);return {name,expected,actual};});
const resultSource='private-custody-cleanup-result-v0.1.proposal.schema.json';
const resultSchema=await Bun.file(base+resultSource).json();
const validateResult=ajv.compile(resultSchema);
const resultFixture=()=>Object.fromEntries(Object.entries(resultSchema.properties).map(([name,rule]:[string,any])=>[name,rule.const??(name==='profile'?{identity:'fixture',version:'0.1.0',sha256:'0'.repeat(64)}:artifact)])) as any;
const resultCases:[string,boolean,(x:any)=>void][]=[
 ['pending complete result',true,()=>{}],['committed result',false,x=>x.durability='committed'],
 ['missing removed membership',false,x=>{delete x.removedRowInventory;}],
 ['missing dependency evidence',false,x=>{delete x.preservedDependencyInventory;}],
 ['missing capacity transition',false,x=>{delete x.capacityTransition;}],
 ['missing attempt custody',false,x=>{delete x.originalCleanupAttempt;}],
 ['reusable deletion permit',false,x=>x.deletePermit=true],
 ['implicit horizon advance',false,x=>x.retainedHorizon='next'],
 ['substituted original artifacts need semantic refusal',true,x=>x.originalRecheckObservation={...artifact,identity:'foreign'}],
 ['count-shaped artifact needs semantic refusal',true,x=>x.removedRowInventory={...artifact,bytesBase64:'MA=='}]
];
const resultObservations=resultCases.map(([name,expected,mutate])=>{const x=resultFixture();mutate(x);const actual=Boolean(validateResult(x));if(actual!==expected)throw Error(name);return {name,expected,actual};});
const snapshotSource='private-custody-snapshot-v0.1.proposal.schema.json';
const validateSnapshot=ajv.compile(await Bun.file(base+snapshotSource).json());
const originalOperation={kind:'operation',fields:{original_writer_xid:'7',operation_ordinal:'0',operation_kind:'mutation',phase:'application_finalized',effect_generation:'1',readiness_generation:'1',sealed_generation:'1',application_generation:'1',original_context_bytes_hex:'61',original_definition_bytes_hex:'62',original_input_bytes_hex:'63',original_prestate_bytes_hex:'64',admitted_candidate_bytes_hex:'65',effect_obligation_bytes_hex:'66',original_group_custody_bytes_hex:'67',application_result_bytes_hex:'68'}};
const originalTouch={kind:'touch',fields:{transaction_id:'7',owner_kind:'edge',owner_id:'-1',owner_discriminator_id:'2',property_owner_type_id:'3',property_id:'4',dirty_generation:'2',sealed_generation:'2',original_layout_bytes_hex:'61',original_home_bytes_hex:'62',original_owner_property_bytes_hex:'63',original_operation_bytes_hex:'64'}};
const snapshotCases:[string,boolean,any][]=[
 ['operation complete',true,originalOperation],['touch signed identity',true,originalTouch],
 ['native NULL proof preserved',true,{...originalTouch,fields:{...originalTouch.fields,sealed_generation:null}}],
 ['NULL result preserved for semantic phase review',true,{...originalOperation,fields:{...originalOperation.fields,application_result_bytes_hex:null}}],
 ['missing field',false,{...originalTouch,fields:{...originalTouch.fields,property_id:undefined}}],
 ['numeric identity coercion',false,{...originalTouch,fields:{...originalTouch.fields,owner_id:7}}],
 ['odd hex byte',false,{...originalOperation,fields:{...originalOperation.fields,original_input_bytes_hex:'a'}}],
 ['uppercase hex',false,{...originalOperation,fields:{...originalOperation.fields,original_input_bytes_hex:'AB'}}],
 ['empty required bytes need semantic refusal',true,{...originalOperation,fields:{...originalOperation.fields,original_input_bytes_hex:''}}],
 ['unknown phase retained for semantic refusal',true,{...originalOperation,fields:{...originalOperation.fields,phase:'foreign'}}],
 ['stale proof retained for semantic refusal',true,{...originalOperation,fields:{...originalOperation.fields,sealed_generation:'0'}}],
 ['native overflow retained for semantic refusal',true,{...originalTouch,fields:{...originalTouch.fields,owner_id:'9223372036854775808'}}]
];
const snapshotObservations=snapshotCases.map(([name,expected,x])=>{const actual=Boolean(validateSnapshot(x));if(actual!==expected)throw Error(name);return {name,expected,actual};});
const sourcePins=await Promise.all([source,resultSource,snapshotSource,dependency].map(async path=>({path:base+path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(base+path).arrayBuffer()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/private-custody-cleanup-shapes.json',JSON.stringify({scope:'Closed JSON schema shape only. No identity uniqueness, artifact byte/hash correspondence, settlement, native domains, authority, complete dependency/absence, deletion/capacity or native qualification.',bunVersion:Bun.version,sourcePins,observations,resultObservations,snapshotObservations},null,2)+'\n');
console.log(JSON.stringify({selectionCases:observations.length,resultCases:resultObservations.length,snapshotCases:snapshotObservations.length,failures:0}));
