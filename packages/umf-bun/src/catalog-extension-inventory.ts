/** Original UMF extension occurrences; preservation never implies interpretation. */
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import type {AssertionOwner} from '../../../docs/helix/02-design/contracts/bindings/truss-enforcement-report-v0.1';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export function collectCatalogExtensionInventory(prepared:Prepared){
 requireOriginalCatalogPreparation(prepared);
 const entries:{owner:AssertionOwner;scope:'document'|'module'|'element';sourcePointer:string;extensionId:string;vocabulary:unknown;payload:unknown;source:Prepared['original']['input']['documents'][number]['artifact']}[]=[];
 const pointer=(key:string)=>key.replace(/~/g,'~0').replace(/\//g,'~1');
 for(let index=0;index<prepared.documents.length;index++){
  const document=prepared.documents[index],source=document.interpretation.source;
  const artifact=prepared.original.input.documents[index].artifact;
  const add=(node:any,path:string,owner:AssertionOwner,scope:'document'|'module'|'element')=>{
   for(const extensionId of Object.keys(node.extensions??{})){
    if(entries.length>=4096)throw Error('Original extension occurrence capacity exceeded');
    if(!Object.hasOwn(source.vocabularies,extensionId))throw Error('Original extension vocabulary declaration missing');
    entries.push(Object.freeze({owner:Object.freeze(owner),scope,sourcePointer:path+'/extensions/'+pointer(extensionId),extensionId,
     vocabulary:source.vocabularies[extensionId],payload:node.extensions[extensionId],source:artifact}));
   }
  };
  add(source,'',{scope:'document',documentId:document.documentId},'document');
  for(let mi=0;mi<source.modules.length;mi++){
   const module=source.modules[mi],owner={documentId:document.documentId,moduleId:module.id};
   add(module,`/modules/${mi}`,owner,'module');
   for(let ei=0;ei<module.elements.length;ei++)add(module.elements[ei],`/modules/${mi}/elements/${ei}`,owner,'element');
  }
 }
 // Source and payload references come from the already frozen prepared input;
 // retain the whole original artifact, never reserialize a fragment as authored bytes.
 return Object.freeze({entries:Object.freeze(entries),scope:'original_document_module_element_extension_occurrences_only' as const});
}
