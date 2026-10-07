/** Closed envelope shape only; fake fixture hashes cannot qualify original custody. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const f of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+f).json());
const validate=ajv.getSchema('urn:truss:draft:catalog-binding-source:0.1.0')!;
const pin={identity:'fixture',version:'0.1.0',sha256:'0'.repeat(64)};
const artifact={identity:'fixture',bytesBase64:'eA==',sha256:'0'.repeat(64)};
const original={interfaceVersion:'truss-catalog-binding-source/0.1.0',sourceProfile:pin,
 reference:{kind:'key',typeId:'-1',keyNumber:'0',owner:{documentId:'doc:A',moduleId:'sales'},definitionPin:'key',authoredIdentity:'key:A'},
 definition:artifact,provenance:{kind:'accepted_binding',acceptedCatalogRevision:'2',acceptedBindingSha256:'0'.repeat(64),bindingVocabulary:pin,authoredPointer:'/keys/0',extractionProfile:pin,owningRecordDefinitionPin:'record:A',owningRecordProvenance:{acceptedCatalogRevision:'1',documentOrdinal:'0',documentRevision:'r1',acceptedDocumentSha256:'0'.repeat(64),authoredPointer:'/records/0',extractionProfile:pin}},
 acceptedBinding:artifact,owningRecordDefinition:artifact,owningRecordDocument:artifact,derivationDependencies:[],originalSourceEvidence:artifact};
const results:any[]=[],failures:any[]=[];
// This known inert JSON fixture is copied as a tree so shared setup objects do
// not make a one-field control accidentally mutate several artifact slots.
function probe(name:string,expected:boolean,mutate:(v:any)=>void){const v=JSON.parse(JSON.stringify(original));mutate(v);const actual=Boolean(validate(v));const row={name,expected,actual};results.push(row);if(expected!==actual)failures.push({...row,errors:structuredClone(validate.errors)});}
probe('complete candidate with empty dependency list',true,()=>{});
probe('missing original binding',false,v=>delete v.acceptedBinding);
probe('digest-only binding',false,v=>delete v.acceptedBinding.bytesBase64);
probe('document provenance is not binding provenance',false,v=>v.provenance.kind='accepted_document');
probe('missing original Record document',false,v=>delete v.owningRecordDocument);
probe('missing original Record definition',false,v=>delete v.owningRecordDefinition);
probe('future receipt excluded',false,v=>v.receipt=artifact);
probe('future report excluded',false,v=>v.acceptedReport=artifact);
probe('unknown native projection excluded',false,v=>v.documentOrdinal='0');
probe('mismatched binding hash needs semantic refusal',true,v=>v.provenance.acceptedBindingSha256='1'.repeat(64));
probe('substituted Record document needs semantic refusal',true,v=>v.owningRecordDocument.identity='another-document');
probe('missing original source evidence',false,v=>delete v.originalSourceEvidence);
const receipt={scope:'Twelve binding-source envelope shape expectations; original fixture artifacts are untrusted and cross-artifact counterexamples deliberately shape-valid',cases:results.length,results,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/catalog-binding-source.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({scope:receipt.scope,cases:receipt.cases,failures}));
if(failures.length)process.exit(1);export {};
