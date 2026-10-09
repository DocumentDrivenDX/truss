import {test,expect} from 'bun:test';
import {readFileSync} from 'node:fs';
import {orderCatalogDocuments} from '../packages/umf-bun/src/catalog-document-order';
const vectors=JSON.parse(readFileSync(new URL('../docs/helix/03-test/document-order-v0.1.proposal.vectors.json',import.meta.url),'utf8'));
function permutations<T>(values:T[]):T[][]{if(!values.length)return [[]];return values.flatMap((value,index)=>permutations(values.filter((_,i)=>i!==index)).map(rest=>[value,...rest]));}
for(const fixture of vectors.cases)test(fixture.name,()=>{
 for(const nodes of permutations<string>(fixture.nodes))for(const edges of permutations<[string,string]>(fixture.edges)){
  const run=()=>orderCatalogDocuments(nodes,edges,{identityBytes:256,documents:32,edges:128});
  if(fixture.expectedRefusal)expect(run).toThrow(fixture.expectedRefusal);
  else{expect(run().order).toEqual(fixture.expectedOrder);expect(orderCatalogDocuments(nodes,[...edges,...edges],{identityBytes:256,documents:32,edges:128}).order).toEqual(fixture.expectedOrder);}
 }
});
test('bounds charge duplicate edges; exact UTF-8 refuses malformed identity',()=>{
 expect(()=>orderCatalogDocuments(['A'],[['A','A'],['A','A']],{identityBytes:256,documents:1,edges:1})).toThrow('bound exceeded');
 expect(()=>orderCatalogDocuments(['A'],[],{identityBytes:256,documents:0,edges:0})).toThrow('bound exceeded');
 expect(()=>orderCatalogDocuments(['é'],[],{identityBytes:1,documents:1,edges:0})).toThrow('identity byte bound');
 expect(()=>orderCatalogDocuments(['\ud800'],[],{identityBytes:256,documents:1,edges:0})).toThrow('UTF-8');
 expect(orderCatalogDocuments([],[],{identityBytes:256,documents:0,edges:0}).order).toEqual([]);
});
test('long chain uses checked work stacks and dependency-first output',()=>{
 const nodes=Array.from({length:4096},(_,i)=>String(i));
 const edges=nodes.slice(1).map((id,i)=>[id,nodes[i]] as const);
 expect(orderCatalogDocuments(nodes,edges,{identityBytes:256,documents:4096,edges:4095}).order).toEqual(nodes);
});
