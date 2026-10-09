/** Private bounded ordering of already-validated graphs; no acceptance authority. */
export function orderCatalogDocuments(nodes:readonly string[],edges:readonly (readonly [string,string])[],limits:{documents:number;edges:number;identityBytes:number}){
 for(const value of [limits.documents,limits.edges,limits.identityBytes])if(!Number.isSafeInteger(value)||value<0)throw Error('Selected graph bounds required');
 if(nodes.length>limits.documents||edges.length>limits.edges)throw Error('Selected graph bound exceeded');
 const ids=new Map<string,number>(),bytes:Buffer[]=[],forward:number[][]=[],reverse:number[][]=[];
 for(const id of nodes){
  if(typeof id!=='string'||id.length===0||id.includes('\0')||/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(id))throw Error('Exact UTF-8 document identity required');
  if(id.length>limits.identityBytes)throw Error('Selected identity byte bound exceeded');
  if(ids.has(id))throw Error('duplicate_document_identity');
  const encoded=Buffer.from(id,'utf8');if(encoded.length>limits.identityBytes)throw Error('Selected identity byte bound exceeded');
  ids.set(id,ids.size);bytes.push(encoded);forward.push([]);reverse.push([]);
 }
 for(const edge of edges){
  if(edge.length!==2)throw Error('Closed dependency pair required');
  const from=ids.get(edge[0]),to=ids.get(edge[1]);
  if(from===undefined||to===undefined)throw Error('missing_dependency_identity');
  forward[from].push(to);reverse[to].push(from);
 }
 // Iterative Kosaraju: every original edge is charged before duplicate collapse.
 const seen=new Set<number>(),finished:number[]=[];
 for(let root=0;root<nodes.length;root++){
  if(seen.has(root))continue;seen.add(root);
  const stack:{node:number;next:number}[]=[{node:root,next:0}];
  while(stack.length){const frame=stack[stack.length-1];
   if(frame.next<forward[frame.node].length){const child=forward[frame.node][frame.next++];if(!seen.has(child)){seen.add(child);stack.push({node:child,next:0});}}
   else{finished.push(frame.node);stack.pop();}
  }
 }
 const membership=new Map<number,number>(),components:number[][]=[];
 for(const root of finished.reverse()){
  if(membership.has(root))continue;const component:number[]=[],index=components.length,stack=[root];membership.set(root,index);
  while(stack.length){const node=stack.pop()!;component.push(node);for(const child of reverse[node])if(!membership.has(child)){membership.set(child,index);stack.push(child);}}
  component.sort((a,b)=>Buffer.compare(bytes[a],bytes[b]));components.push(component);
 }
 const dependencies=components.map(()=>new Set<number>()),dependents=components.map(()=>new Set<number>());
 for(let node=0;node<nodes.length;node++)for(const target of forward[node]){const a=membership.get(node)!,b=membership.get(target)!;if(a!==b){dependencies[a].add(b);dependents[b].add(a);}}
 const compare=(a:number,b:number)=>{const x=components[a],y=components[b];for(let i=0;i<Math.min(x.length,y.length);i++){const result=Buffer.compare(bytes[x[i]],bytes[y[i]]);if(result)return result;}return x.length-y.length;};
 const ready=components.map((_,i)=>i).filter(i=>dependencies[i].size===0),ordered:string[][]=[];
 while(ready.length){ready.sort(compare);const index=ready.shift()!;ordered.push(components[index].map(node=>nodes[node]));for(const dependent of dependents[index]){dependencies[dependent].delete(index);if(dependencies[dependent].size===0)ready.push(dependent);}}
 if(ordered.length!==components.length)throw Error('Component graph ordering failed');
 return Object.freeze({components:Object.freeze(ordered.map(component=>Object.freeze(component))),order:Object.freeze(ordered.flat()),scope:'validated_graph_order_only' as const});
}
