/** Structural proposal controls; semantic/native/owner adoption stays separate. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const f of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))
  ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+f).json());
const artifact={identity:'unqualified-fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const pin={identity:'unqualified-profile',version:'0.1.0',sha256:'b'.repeat(64)};
const logical={documentId:'d',revision:'r',module:'m',element:'e'};
const home={interfaceVersion:'truss-property-home/0.1.0',layoutInventory:artifact,recordKind:'object',relationPhysicalIdentity:'table-object',propsColumnPhysicalIdentity:'column-object-props',discriminatorColumnPhysicalIdentity:'column-object-type',relationName:'object',propsColumnName:'props',discriminatorColumnName:'type_id',ownerCatalogId:'-1',propertyCatalogId:'0',memberName:'0',accessor:'jsonb-top-level-member',presenceProfile:pin,valueProfile:pin};
const relationship={logical:{documentId:'d',revision:'r',module:'m',relationship:'rel'},source:artifact,relationshipId:'-1',sourceTypeId:'1',targetTypeId:'2',sourceKeyId:'source-key',targetKeyId:'target-key',sourceOrderedPropertyIds:['3'],targetOrderedPropertyIds:['4','5'],relationshipProfile:pin,acceptedDefinition:artifact};
const binding={interfaceVersion:'truss-postgresql-binding/0.1.0',bindingProfile:pin,bindingProfileId:'unqualified-profile/0.1.0',basis:{modelBundle:artifact,catalogRevision:'0',acceptedCatalog:artifact,layoutProfile:pin,layoutInventory:artifact,layoutSql:artifact,exporterProfile:pin,namespace:'truss',identityProfile:pin,valueProfile:pin,keyProfile:pin,readContextProfile:pin,readContextDefinition:artifact},entities:[{logical,typeId:'1',acceptedDefinition:artifact,source:artifact}],properties:[{logical:{...logical,element:'p'},ownerTypeId:'1',propertyId:'3',home:'props',homeProfile:pin,homeDefinition:artifact,valueProfile:pin,valueDefinition:artifact,presenceProfile:pin,presenceDefinition:artifact,acceptedDefinition:artifact,source:artifact}],keys:[{ownerTypeId:'1',keyId:'k',keyNumber:'-1',orderedPropertyIds:['3'],comparisonProfile:pin,comparisonDefinition:artifact,encodingProfile:pin,encodingDefinition:artifact,acceptedDefinition:artifact}],relationships:[relationship],executionObligations:[],qualification:[]};
const root='urn:truss:draft:postgresql-binding:0.1.0';
const hv=ajv.getSchema('urn:truss:draft:property-home:0.1.0')!;
const bv=ajv.getSchema(root)!;
const rv=ajv.getSchema('urn:truss:draft:row-home:0.1.0')!;
const row={interfaceVersion:'truss-row-home/0.1.0',layoutInventory:artifact,recordKind:'object',ownerCatalogId:'1',propertyCatalogId:'3',stateRelationPhysicalIdentity:'state',nodeRelationPhysicalIdentity:'node',scalarRelationPhysicalIdentity:'scalar',joinProfile:pin,joinDefinition:artifact,access:'scalar-root',presenceDefinition:artifact,valueDefinition:artifact,storedDomainObligation:'fixture-obligation'};
const without=(value:Record<string,unknown>,key:string)=>Object.fromEntries(Object.entries(value).filter(([k])=>k!==key));
const cases:[string,Function,unknown,boolean][]=[
 ['complete proposed envelope; unqualified',bv,binding,true],
 ['independent unequal endpoint key arity',bv,{...binding,relationships:[relationship]},true],
 ['old paired endpoint mapping',bv,{...binding,relationships:[{...relationship,orderedComponentMapping:[{sourcePropertyId:'3',targetPropertyId:'4'}]}]},false],
 ['old identity names',bv,{...binding,entities:[{...binding.entities[0],logical:{documentId:'d',documentRevision:'r',moduleId:'m',elementId:'e'}}]},false],
 ['relationship element substitution',bv,{...binding,relationships:[{...relationship,logical}]},false],
 ['profile string missing',bv,without(binding,'bindingProfileId'),false],
 ['host-number catalog ID',bv,{...binding,entities:[{...binding.entities[0],typeId:1}]},false],
 ['duplicate maps require semantic refusal',bv,{...binding,entities:[binding.entities[0],binding.entities[0]]},true],
 ['native overflow requires semantic refusal',bv,{...binding,entities:[{...binding.entities[0],typeId:'2147483648'}]},true],
 ['row scalar-root home',rv,row,true],
 ['row complete-tree declaration',rv,{...row,access:'complete-value-tree'},true],
 ['row join missing',rv,without(row,'joinDefinition'),false],
 ['row SQL injected',rv,{...row,sql:'SELECT anything'},false],
 ['row edge association missing',rv,{...row,recordKind:'edge'},false],
 ['row edge association declared',rv,{...row,recordKind:'edge',edgeAssociationProfile:pin,edgeAssociationDefinition:artifact},true],
 ['row host numeric property',rv,{...row,propertyCatalogId:3},false],
 ['row unknown obligation needs semantic refusal',rv,{...row,storedDomainObligation:'unknown'},true],
 ['object props home',hv,home,true],
 ['edge props home',hv,{...home,recordKind:'edge',relationName:'edge',discriminatorColumnName:'rel_type_id',edgeAssociationProfile:pin,edgeAssociationDefinition:artifact},true],
 ['edge association missing',hv,{...home,recordKind:'edge',relationName:'edge',discriminatorColumnName:'rel_type_id'},false],
 ['object association contamination',hv,{...home,edgeAssociationProfile:pin,edgeAssociationDefinition:artifact},false],
 ['wrong discriminator',hv,{...home,discriminatorColumnName:'rel_type_id'},false],
 ['wrong relation',hv,{...home,relationName:'edge'},false],
 ['SQL accessor injection',hv,{...home,accessor:'props->caller_sql'},false],
 ['unowned extra path',hv,{...home,path:['nested']},false],
 ['noncanonical member ID',hv,{...home,memberName:'-0'},false],
 ['member/property mismatch requires semantic refusal',hv,{...home,memberName:'2'},true],
 ['row home needs separate profile',hv,{...home,recordKind:'row'},false],
];
const observations=cases.map(([name,validate,value,expected])=>({name,expected,actual:Boolean(validate(value))}));
const failures=observations.filter(x=>x.actual!==x.expected);
const schemaSources=await Promise.all(['truss-postgresql-binding-v0.1.proposal.schema.json','truss-property-home-v0.1.proposal.schema.json','truss-row-home-v0.1.proposal.schema.json'].map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file('docs/helix/02-design/contracts/'+path).arrayBuffer()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/weft-binding-shapes.json',JSON.stringify({scope:'28 structural acceptance/refusal controls only; accepted invalid-semantic fixtures explicitly demonstrate required later admission. No digest/custody/native completeness or backend adoption proof.',bunVersion:Bun.version,schemaSources,observations,failures},null,2)+'\n');
console.log(JSON.stringify({cases:observations.length,failures}));
if(failures.length)process.exit(1);
export {};
