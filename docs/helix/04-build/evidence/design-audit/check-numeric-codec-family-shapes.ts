/** Shape correspondence only; synthetic adoption artifact is not authority. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const f of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(JSON.parse(await Bun.file('docs/helix/02-design/contracts/'+f).text()));
const base=JSON.parse(await Bun.file('docs/helix/04-build/evidence/weft-source-binding011/nested-definitions.json').text()).codec;
const check=ajv.getSchema('urn:truss:draft:jsonb-leaf-codec:0.1.0');if(!check)throw Error('missing schema');
const token=(family:string)=>({...base,rule:{family,storageRepresentation:'json-string',encoding:'preserve-admitted-source-token',decodedCarrierKind:family,numericAdoptionEvidence:base.authoredDefinition}});
const integer=token('integer'),decimal=token('decimal');
const missing=token('integer');delete missing.rule.numericAdoptionEvidence;
const cases=[['integer',integer,true],['decimal',decimal,true],['integer-as-decimal',{...integer,rule:{...integer.rule,decodedCarrierKind:'decimal'}},false],['decimal-as-integer',{...decimal,rule:{...decimal.rule,decodedCarrierKind:'integer'}},false],['missing-adoption',missing,false],['raw-json-number',{...integer,rule:{...integer.rule,storageRepresentation:'json-number'}},false],['numeric-as-string',{...decimal,rule:{...decimal.rule,decodedCarrierKind:'string'}},false]] as const;
const results=cases.map(([id,input,expected])=>{const accepted=check(input);if(accepted!==expected)throw Error(id+JSON.stringify(check.errors));return {id,expectedShapeValid:expected,observedShapeValid:accepted};});
await Bun.write('docs/helix/04-build/evidence/design-audit/numeric-codec-family-shapes.json',JSON.stringify({scope:'Seven draft shape controls, using synthetic exact artifact; no actual numeric adoption, codec/native execution or Weft registration',schemaSha256:new Bun.CryptoHasher('sha256').update(await Bun.file('docs/helix/02-design/contracts/truss-jsonb-leaf-codec-v0.1.proposal.schema.json').arrayBuffer()).digest('hex'),cases:results,nativeQualified:false},null,2)+'\n');console.log(JSON.stringify({cases:results.length,passed:true,nativeQualified:false}));export {};
