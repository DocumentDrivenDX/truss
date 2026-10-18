/** Source correspondence after owner validation. No storage IDs or binding choices. */
type SourceObject = Record<string, unknown>;
function object(value: unknown): SourceObject {
 if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error('Original catalog object required');
 return value as SourceObject;
}
function array(value: unknown): unknown[] { if (!Array.isArray(value)) throw Error('Original catalog array required');return value; }
function identity(value: unknown): string { if(typeof value !== 'string'||!value.length)throw Error('Original catalog identity required');return value; }
export function collectCatalogDeclarations(documentId:string,source:unknown){
 const document=object(source);if(document.id!==documentId)throw Error('Original catalog document mismatch');
 const modules=array(document.modules).map(object);
 const moduleIndex=new Map<string,SourceObject[]>();
 const elementIndexes=new Map<SourceObject,Map<string,SourceObject[]>>();
 for(const module of modules){
  const key=identity(module.id);const matches=moduleIndex.get(key)??[];matches.push(module);moduleIndex.set(key,matches);
  const elements=new Map<string,SourceObject[]>();
  for(const value of array(module.elements)){
   const element=object(value);const key=identity(element.id);const matches=elements.get(key)??[];matches.push(element);elements.set(key,matches);
  }
  elementIndexes.set(module,elements);
 }
 const records=[];const relationships=[];
 for(const module of modules){
  const moduleId=identity(module.id);
  for(const value of array(module.elements)){
   const declaration=object(value);if(declaration.kind!=='record')continue;
   const elementId=identity(declaration.id);
   const membership=Object.hasOwn(declaration,'members')?'declared' as const:'missing' as const;
   const fields=(membership==='declared'?array(declaration.members):[]).map(value=>{
    const reference=object(value);const fieldModule=identity(reference.module);const fieldId=identity(reference.element);
    const declaringModules=(moduleIndex.get(fieldModule)??[]);
    if(declaringModules.length!==1)throw Error('Original member module correspondence unavailable');
    const fields=(elementIndexes.get(declaringModules[0])!.get(fieldId)??[]);
    if(fields.length!==1||fields[0].kind!=='field')throw Error('Original member Field correspondence unavailable');
    return Object.freeze({fieldModule,fieldId,reference,declaration:fields[0]});
   });
   const keys=declaration.keys===undefined?[]:array(declaration.keys).map(value=>{
    const key=object(value);identity(key.id);
    // Preserve order and full reference content. Native component IDs are resolved
    // only after actual owner/property allocation; no inferred primary key.
    for(const value of array(key.fields)){const reference=object(value);if(!fields.some(field=>field.fieldModule===reference.module&&field.fieldId===reference.element))throw Error('Original key member correspondence unavailable')}
    return key;
   });
   records.push(Object.freeze({documentId,moduleId,elementId,declaration,membership,fields:Object.freeze(fields),keys:Object.freeze(keys)}));
  }
  if(module.relationships!==undefined)for(const value of array(module.relationships)){
   const declaration=object(value);identity(declaration.id);
   relationships.push(Object.freeze({documentId,moduleId,declaration}));
  }
 }
 return Object.freeze({records:Object.freeze(records),relationships:Object.freeze(relationships),scope:'original_declaration_correspondence_only' as const});
}
