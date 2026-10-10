import {describe, expect, test} from 'bun:test';
import {projectSecurityGraphEndpoints, projectDeclaredSecurityGraphEndpoints, resolveSecurityGraphKeyLocator} from '../packages/postgresql/src/security-graph-locator';
const original = () => ({
  objects: [{id: '9007199254740993', typeId: '1'}, {id: '9007199254740993', typeId: '2'}],
  edges: [{id:'10', relationshipId: '3', sourceId: '9007199254740993', sourceType: '1', targetId: '9007199254740993', targetType: '2'}],
});
const declared = () => ({...original(),declarations:[{relationshipId:'3',sourceType:'1',targetType:'2'}],selectedRelationshipId:'3'});
const keyed=()=>({objects:original().objects,buckets:[
  {storageRowId:'1',typeId:'1',keyNumber:'1',objectId:'9007199254740993',namespaceHex:'aa',keyHex:'0102'},
  {storageRowId:'2',typeId:'2',keyNumber:'1',objectId:'9007199254740993',namespaceHex:'bb',keyHex:'0102'},
],expected:{typeId:'1',keyNumber:'1',namespaceHex:'aa',keyHex:'0102'}});
describe('candidate exact graph key resolution @covers US-056-AC2',()=>{
  test('joins full native typed owner without treating locator as business key',()=>{
    const input=keyed(),result=resolveSecurityGraphKeyLocator(input);expect(result).toEqual({id:'9007199254740993',typeId:'1'});
    input.buckets[0]!.objectId='1';input.expected.typeId='2';expect(result.id).toBe('9007199254740993');expect(Object.isFrozen(result)).toBe(true);
  });
  test('selects full namespace and bytes in exact type/key definition',()=>{
    for(const field of ['typeId','keyNumber','namespaceHex','keyHex'] as const){const input=keyed();input.expected[field]=field.endsWith('Hex')?'cc':'3';expect(()=>resolveSecurityGraphKeyLocator(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');}
    const input=keyed();input.expected.typeId='2';input.expected.namespaceHex='bb';expect(resolveSecurityGraphKeyLocator(input).typeId).toBe('2');
  });
  test('refuses missing materialization and unresolved typed owners',()=>{
    const missing=keyed();missing.buckets=[];expect(()=>resolveSecurityGraphKeyLocator(missing)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const unresolved=keyed();unresolved.buckets[0]!.typeId='3';expect(()=>resolveSecurityGraphKeyLocator(unresolved)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('refuses ambiguous full key ownership and duplicate storage/owner rows',()=>{
    const ambiguous=keyed();ambiguous.objects.push({id:'2',typeId:'1'});ambiguous.buckets.push({...ambiguous.buckets[0]!,storageRowId:'3',objectId:'2'});expect(()=>resolveSecurityGraphKeyLocator(ambiguous)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const duplicate=keyed();duplicate.buckets[1]!.storageRowId='1';expect(()=>resolveSecurityGraphKeyLocator(duplicate)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const owner=keyed();owner.buckets.push({...owner.buckets[0]!,storageRowId:'3',namespaceHex:'cc'});expect(()=>resolveSecurityGraphKeyLocator(owner)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('refuses malformed exact byte and native key carriers',()=>{
    for(const value of ['', 'A0','0','zz',null]){const input:any=keyed();input.buckets[0].keyHex=value;expect(()=>resolveSecurityGraphKeyLocator(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');}
    for(const value of ['32768','-32769','01',1]){const input:any=keyed();input.buckets[0].keyNumber=value;expect(()=>resolveSecurityGraphKeyLocator(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');}
    const zero=keyed();zero.buckets[0]!.storageRowId='0';expect(()=>resolveSecurityGraphKeyLocator(zero)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('retains exact native byte limits and refuses one byte over on either side',()=>{
    for(const [field,limit] of [['namespaceHex',65536],['keyHex',1048576]] as const){
      const input=keyed();input.expected[field]='ab'.repeat(limit);input.buckets[0]![field]=input.expected[field];expect(resolveSecurityGraphKeyLocator(input).typeId).toBe('1');
      const overExpected=structuredClone(input);overExpected.expected[field]+='ab';expect(()=>resolveSecurityGraphKeyLocator(overExpected)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
      const overStored=structuredClone(input);overStored.buckets[0]![field]+='ab';expect(()=>resolveSecurityGraphKeyLocator(overStored)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    }
  });
  test('accepts 4096 complete bucket rows and rejects 4097',()=>{
    const input={objects:Array.from({length:4096},(_,i)=>({id:String(i),typeId:'1'})),buckets:Array.from({length:4096},(_,i)=>({storageRowId:String(i+1),typeId:'1',keyNumber:'1',objectId:String(i),namespaceHex:'aa',keyHex:i.toString(16).padStart(4,'0')})),expected:{typeId:'1',keyNumber:'1',namespaceHex:'aa',keyHex:'0000'}};
    expect(resolveSecurityGraphKeyLocator(input).id).toBe('0');input.buckets.push({...input.buckets[0]!,storageRowId:'4097'});expect(()=>resolveSecurityGraphKeyLocator(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('bounds aggregate native key bytes before returning a selected match',()=>{
    const input=keyed();input.buckets.pop();const large='ab'.repeat(1048576);
    for(let i=0;i<15;i++){input.objects.push({id:String(i),typeId:'1'});input.buckets.push({...input.buckets[0]!,storageRowId:String(i+2),objectId:String(i),keyHex:large});}
    expect(resolveSecurityGraphKeyLocator(input).id).toBe('9007199254740993');
    input.objects.push({id:'15',typeId:'1'});input.buckets.push({...input.buckets[0]!,storageRowId:'17',objectId:'15',keyHex:large});expect(()=>resolveSecurityGraphKeyLocator(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('refuses caller bucket iterators/accessors without executing them',()=>{
    let calls=0;const input=keyed();Object.defineProperty(input.buckets,Symbol.iterator,{value:function*(){calls++;yield {};}});expect(()=>resolveSecurityGraphKeyLocator(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const accessor=keyed();Object.defineProperty(accessor.expected,'keyHex',{enumerable:true,get(){calls++;return '0102';}});expect(()=>resolveSecurityGraphKeyLocator(accessor)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');expect(calls).toBe(0);
  });
});
describe('candidate declared relationship projection @covers US-056-AC2',()=>{
  test('selects exact relationship and retains independently declared foreign edges',()=>{
    const input=declared();input.declarations.push({relationshipId:'4',sourceType:'1',targetType:'2'});input.edges.push({...input.edges[0]!,id:'11',relationshipId:'4'});
    expect(projectDeclaredSecurityGraphEndpoints(input).map(edge=>edge.id)).toEqual(['10']);
    input.selectedRelationshipId='4';expect(projectDeclaredSecurityGraphEndpoints(input).map(edge=>edge.id)).toEqual(['11']);
  });
  test('declared empty association is empty; missing selection is refusal',()=>{
    const input=declared();input.edges=[];expect(projectDeclaredSecurityGraphEndpoints(input)).toEqual([]);
    input.selectedRelationshipId='4';expect(()=>projectDeclaredSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('refuses undeclared edge relationship and reversed endpoint roles',()=>{
    const unknown=declared();unknown.edges[0]!.relationshipId='4';expect(()=>projectDeclaredSecurityGraphEndpoints(unknown)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const reversed=declared();reversed.edges[0]!.sourceType='2';reversed.edges[0]!.targetType='1';expect(()=>projectDeclaredSecurityGraphEndpoints(reversed)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('declared alternative endpoint types are preserved independently',()=>{
    const input=declared();input.declarations.push({relationshipId:'3',sourceType:'2',targetType:'1'});input.edges.push({...input.edges[0]!,id:'11',sourceType:'2',targetType:'1'});
    expect(projectDeclaredSecurityGraphEndpoints(input).map(edge=>[edge.source.typeId,edge.target.typeId])).toEqual([['1','2'],['2','1']]);
  });
  test('refuses duplicate, missing and malformed declarations',()=>{
    const duplicate=declared();duplicate.declarations.push({...duplicate.declarations[0]!});expect(()=>projectDeclaredSecurityGraphEndpoints(duplicate)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const missing=declared();missing.declarations=[];expect(()=>projectDeclaredSecurityGraphEndpoints(missing)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const malformed=declared();malformed.declarations[0]!.sourceType='2147483648';expect(()=>projectDeclaredSecurityGraphEndpoints(malformed)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('refuses declaration iterators and accessors without invoking them',()=>{
    const iterator=declared();let calls=0;Object.defineProperty(iterator.declarations,Symbol.iterator,{value:function*(){calls++;while(true)yield {};}});expect(()=>projectDeclaredSecurityGraphEndpoints(iterator)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const accessor=declared();Object.defineProperty(accessor.declarations[0],'sourceType',{enumerable:true,get(){calls++;return '1';}});expect(()=>projectDeclaredSecurityGraphEndpoints(accessor)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');expect(calls).toBe(0);
  });
});
describe('candidate typed graph locator boundary @covers US-056-AC2', () => {
  test('bounds dense original rows at exactly 4096 objects and edges', () => {
    expect(projectSecurityGraphEndpoints({objects:Array.from({length:4096},(_,i)=>({id:String(i),typeId:'1'})),edges:[]})).toEqual([]);
    const input=original();input.edges=Array.from({length:4096},(_,i)=>({...input.edges[0]!,id:String(i)}));
    expect(projectSecurityGraphEndpoints(input).length).toBe(4096);
    input.edges.push({...input.edges[0]!,id:'4096'});
    expect(()=>projectSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('refuses custom collection iterators without invoking them', () => {
    for(const side of ['objects','edges'] as const){
      const input=original();let calls=0;
      Object.defineProperty(input[side],Symbol.iterator,{value:function*(){calls++;while(true)yield {};}});
      expect(()=>projectSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
      expect(calls).toBe(0);
    }
  });
  test('refuses sparse, accessor and extended collection carriers', () => {
    for(const side of ['objects','edges'] as const){
      const sparse=original();delete sparse[side][0];
      expect(()=>projectSecurityGraphEndpoints(sparse)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
      const accessor=original();let calls=0;Object.defineProperty(accessor[side],'0',{get(){calls++;return {};},enumerable:true});
      expect(()=>projectSecurityGraphEndpoints(accessor)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');expect(calls).toBe(0);
      const extra:any=original();extra[side].extra=true;
      expect(()=>projectSecurityGraphEndpoints(extra)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    }
  });
  test('normalizes absent input and rejects top-level accessors',()=>{
    for(const input of [null,undefined,{},false])expect(()=>projectSecurityGraphEndpoints(input as any)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    let calls=0;const packet=original();Object.defineProperty(packet,'objects',{get(){calls++;return [];},enumerable:true});
    expect(()=>projectSecurityGraphEndpoints(packet)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');expect(calls).toBe(0);
  });
  test('retains exact large IDs and distinguishes equal IDs in different types', () => {
    const input = original(), result = projectSecurityGraphEndpoints(input);
    expect(result).toEqual([{id:'10', relationshipId: '3', source: input.objects[0]!, target: input.objects[1]!}]);
    input.objects[0]!.typeId = '2'; input.edges[0]!.sourceType = '2';
    expect(result[0]!.source.typeId).toBe('1');
    expect(Object.isFrozen(result) && Object.isFrozen(result[0]) && Object.isFrozen(result[0]!.source)).toBe(true);
  });
  test('preserves directional roles rather than sorting endpoints', () => {
    const input = original(); input.edges[0]!.sourceType = '2'; input.edges[0]!.targetType = '1';
    const result = projectSecurityGraphEndpoints(input);
    expect(result[0]!.source.typeId).toBe('2'); expect(result[0]!.target.typeId).toBe('1');
  });
  test('accepts signed native limits without rounding', () => {
    expect(projectSecurityGraphEndpoints({objects: [{id:'-9223372036854775808',typeId:'-2147483648'},{id:'9223372036854775807',typeId:'2147483647'}], edges:[{id:'10',relationshipId:'0',sourceId:'-9223372036854775808',sourceType:'-2147483648',targetId:'9223372036854775807',targetType:'2147483647'}]})[0]!.target.id).toBe('9223372036854775807');
  });
  for (const value of ['-0','01','+1','1.0','1e3',' 1','9223372036854775808','-9223372036854775809',1,1n,null]) {
    test('refuses malformed or overflowing object ID '+String(value), () => {
      const input: any = original(); input.objects[0].id = value;
      expect(() => projectSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    });
  }
  for (const value of ['2147483648','-2147483649',1,null]) {
    test('refuses invalid endpoint type '+String(value), () => {
      const input: any = original(); input.edges[0].sourceType = value;
      expect(() => projectSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    });
  }
  test('refuses unresolved typed endpoint despite a matching bare ID', () => {
    const input = original(); input.objects.pop();
    expect(() => projectSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('refuses duplicate objects and duplicate edge IDs', () => {
    const objects = original(); objects.objects.push({...objects.objects[0]!});
    expect(() => projectSecurityGraphEndpoints(objects)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    const edges = original(); edges.edges.push({...edges.edges[0]!});
    expect(() => projectSecurityGraphEndpoints(edges)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
  test('distinct edges with identical endpoints remain distinct', () => {
    const input = original(); input.edges.push({...input.edges[0]!,id:'11'});
    expect(projectSecurityGraphEndpoints(input).map(edge => edge.id)).toEqual(['10','11']);
  });
  test('separate relationship IDs remain distinct', () => {
    const input = original(); input.edges.push({...input.edges[0]!,id:'11',relationshipId:'4'});
    expect(projectSecurityGraphEndpoints(input).map(edge => edge.relationshipId)).toEqual(['3','4']);
  });
  test('rejects accessors without invoking them', () => {
    let calls=0; const input: any = original();
    Object.defineProperty(input.objects[0],'id',{enumerable:true,get(){calls++;return '1';}});
    expect(() => projectSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    expect(calls).toBe(0);
  });
  test('rejects extra meaning and oversized collections', () => {
    const input: any = original(); input.edges[0].extra = true;
    expect(() => projectSecurityGraphEndpoints(input)).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
    expect(() => projectSecurityGraphEndpoints({objects:Array(4097).fill({id:'1',typeId:'1'}),edges:[]})).toThrow('TRUSS_SECURITY_GRAPH_LOCATOR_UNSUPPORTED');
  });
});
