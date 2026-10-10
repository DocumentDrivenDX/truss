/** Private candidate shape/source basis. Not registered interpretation or acceptance. */
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {resolveCatalogEndpointSuppliedSources,type EndpointSourceSelection} from './catalog-endpoint-source-references';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
const SCHEMA_SHA='b4362c9c6842f51d061c39021cfe6c38dc18dac183e46d0e005c5cad97fd2493';
const EXTENSION='truss-endpoint-intent-candidate',VERSION='0.1.0';
export async function createCatalogEndpointIntentBasis(dependenciesPackage:string){
 const bytes=await readFile(new URL('../../../docs/helix/02-design/contracts/truss-endpoint-intent-v0.1.proposal.schema.json',import.meta.url));
 if(createHash('sha256').update(bytes).digest('hex')!==SCHEMA_SHA)throw Error('Original candidate endpoint schema required');
 const require=createRequire(dependenciesPackage),Ajv=require('ajv/dist/2020').default;
 const validate=new Ajv({strict:true}).compile(JSON.parse(bytes.toString('utf8')));
 return Object.freeze({extensionId:EXTENSION,schemaSha256:SCHEMA_SHA,collect(prepared:Prepared,maximumOccurrences:number){
  requireOriginalCatalogPreparation(prepared);
  if(!Number.isSafeInteger(maximumOccurrences)||maximumOccurrences<0)throw Error('Selected endpoint occurrence bound required');
  let occurrences=0;const documents=[];
  for(const document of prepared.documents){
   const source=document.interpretation.source as any;
   if(!Object.hasOwn(source.extensions??{},EXTENSION))continue;
   if(document.umfVersion!=='0.7.0'||source.vocabularies?.[EXTENSION]?.version!==VERSION)throw Error('Original candidate extension/source version required');
   const payload=source.extensions[EXTENSION];
   if(!validate(payload))throw Error('Closed complete candidate endpoint carrier required');
   const selections:EndpointSourceSelection[]=[],references:any[]=[],dependencies=new Map<string,string>();
   const charge=()=>{if(++occurrences>maximumOccurrences)throw Error('Selected endpoint occurrence bound exceeded')};
   for(let i=0;i<payload.dependencies.length;i++){
    charge();const dependency=payload.dependencies[i];
    const key=JSON.stringify([dependency.document,dependency.revision]);
    if(dependencies.has(key))throw Error('Duplicate declared dependency selection');
    dependencies.set(key,dependency.sourceReference);
    selections.push({...dependency});
    references.push(Object.freeze({pointer:`/extensions/${EXTENSION}/dependencies/${i}`,kind:'dependency',selection:Object.freeze({...dependency})}));
   }
   const intentIds=new Set<string>();
   const collectEndpoint=(endpoint:any,pointer:string)=>{
    charge();
    if(endpoint.definition.state==='pending'){
     references.push(Object.freeze({pointer,kind:'pending',document:endpoint.document,module:endpoint.module,element:endpoint.element,expectedRevision:endpoint.definition.expectedRevision}));return;
    }
    const selection={document:endpoint.document,revision:endpoint.definition.revision,sourceReference:endpoint.definition.sourceReference};
    if(selection.document!==document.documentId&&dependencies.get(JSON.stringify([selection.document,selection.revision]))!==selection.sourceReference)
     throw Error('Selected external endpoint requires its exact declared dependency');
    selections.push(selection);
    references.push(Object.freeze({pointer,kind:'selected',selection:Object.freeze(selection),module:endpoint.module,element:endpoint.element}));
   };
   for(let i=0;i<payload.intents.length;i++){
    const intent=payload.intents[i],prefix=`/extensions/${EXTENSION}/intents/${i}`;
    const key=JSON.stringify([intent.module,intent.id]);
    if(intentIds.has(key))throw Error('Duplicate original qualified intent');intentIds.add(key);
    if(!source.modules.some((module:any)=>module.id===intent.module))throw Error('Original declaring module required');
    for(const bounds of [intent.sourceBounds,intent.targetBounds])if(bounds.max!=='*'&&(bounds.min.length>bounds.max.length||(bounds.min.length===bounds.max.length&&bounds.min>bounds.max)))
     throw Error('Candidate lower bound exceeds upper bound');
    const sets=[['sources',intent.sources],['targets',intent.targets]] as const;
    for(const [slot,endpoints] of sets){
     const seen=new Set<string>();
     for(let j=0;j<endpoints.length;j++){
      const endpoint=endpoints[j],lineage=JSON.stringify([endpoint.document,endpoint.module,endpoint.element]);
      if(seen.has(lineage))throw Error('Duplicate endpoint lineage in original set');seen.add(lineage);
      collectEndpoint(endpoint,`${prefix}/${slot}/${j}`);
     }
    }
    if(intent.associationRecord!==null)collectEndpoint(intent.associationRecord,prefix+'/associationRecord');
   }
   const supplied=resolveCatalogEndpointSuppliedSources(prepared,document.documentId,selections,maximumOccurrences);
   documents.push(Object.freeze({documentId:document.documentId,documentRevision:document.revision,payload,
    referenceOccurrences:Object.freeze(references),supplied}));
  }
  return Object.freeze({documents:Object.freeze(documents),occurrences,
   scope:'original_endpoint_intent_shape_and_supplied_source_basis_only' as const});
 }});
}
