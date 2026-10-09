import {test,expect} from 'bun:test';
import {requireUnchangedCatalogTransition} from '../packages/umf-bun/src/catalog-transition-correspondence';
const source={umf:'0.7.0',extensions:{unknown:{meaning:'雪🙂',present:null}}};
const target={...structuredClone(source),umf:'0.8.0'};
const receipt=()=>({source:structuredClone(source),target:structuredClone(target)});
const rollback=()=>({source:structuredClone(target),target:structuredClone(source)});
test('complete source and interpretation target correspond independently',()=>{
 expect(()=>requireUnchangedCatalogTransition(JSON.stringify(source),source,receipt(),receipt(),rollback())).not.toThrow();
});
test('restored original does not admit a later edited target',()=>{
 const changed=receipt();changed.target.extensions.unknown.meaning='edited';
 const restored=rollback();restored.source=changed.target;
 expect(()=>requireUnchangedCatalogTransition(JSON.stringify(source),source,changed,receipt(),restored)).toThrow('target correspondence');
 const onlyRollback=rollback();onlyRollback.source.extensions.unknown.present='edited' as any;
 expect(()=>requireUnchangedCatalogTransition(JSON.stringify(source),source,receipt(),receipt(),onlyRollback)).toThrow('target correspondence');
});
test('every original source occurrence remains exact including unknown content',()=>{
 for(const slot of ['source','transition','verified','rollback'] as const){
  const current=structuredClone(source),transition=receipt(),verified=receipt(),restored=rollback();
  const selected=slot==='source'?current:slot==='transition'?transition.source:slot==='verified'?verified.source:restored.target;
  delete (selected.extensions.unknown as any).present;
  expect(()=>requireUnchangedCatalogTransition(JSON.stringify(source),current,transition,verified,restored)).toThrow('source correspondence');
 }
});
