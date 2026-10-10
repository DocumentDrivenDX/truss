/** ADR-002 default home for absent storage binding. No row-home inference. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import type {CatalogPropertyHome} from './catalog-new-stage';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export function prepareDefaultCatalogHomes(prepared:Prepared){
 requireOriginalCatalogPreparation(prepared);
 if(prepared.original.input.binding.state!=='absent')throw Error('Original explicit binding home interpretation required');
 const homes:CatalogPropertyHome[]=prepared.declarations.flatMap(document=>document.records.flatMap(record=>record.fields.map(field=>Object.freeze({documentId:record.documentId,moduleId:record.moduleId,elementId:record.elementId,fieldModule:field.fieldModule,fieldId:field.fieldId,home:'json' as const}))));
 return Object.freeze({homes:Object.freeze(homes),originalInputSha256:createHash('sha256').update(Buffer.from(prepared.original.originalUtf8Hex,'hex')).digest('hex'),source:'ADR-002-D4-absent-binding-json-default' as const,scope:'original_default_home_preparation_only' as const});
}
