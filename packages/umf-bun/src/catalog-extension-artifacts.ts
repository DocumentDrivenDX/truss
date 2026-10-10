/** Scoped occurrence retention wrappers, not extension semantic admission. */
import {createHash} from 'node:crypto';
import {collectCatalogExtensionInventory} from './catalog-extension-inventory';
import type {createCatalogInputPreparation} from './catalog-input';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export function collectCatalogExtensionArtifacts(prepared:Prepared){
 const inventory=collectCatalogExtensionInventory(prepared);let retained=0;
 const extensions=inventory.entries.map((entry,index)=>{
  const bytes=Buffer.from(JSON.stringify({interfaceVersion:'truss-original-extension-occurrence/0.1.0',
   interpretation:'retained_uninterpreted',owner:entry.owner,scope:entry.scope,sourcePointer:entry.sourcePointer,
   extensionId:entry.extensionId,vocabulary:entry.vocabulary,payload:entry.payload,source:entry.source}));
  if(bytes.length>1048576||(retained+=bytes.length)>4194304)throw Error('Extension artifact output capacity exceeded');
  return Object.freeze({identity:`truss.original-extension-occurrence/${index}`,bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')});
 });
 return Object.freeze({extensions:Object.freeze(extensions),scope:'original_document_module_element_extension_artifacts_only' as const});
}
