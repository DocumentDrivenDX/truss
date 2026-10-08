import {test,expect} from 'bun:test';
import {decodeNativeTextArray} from '../packages/postgresql/src/index';
import vectors from '../docs/helix/02-design/contracts/bindings/bootstrap-native-array-decoder-v0.1.vectors.proposal.json';
const limits = {maxBytes:4096,maxNodes:128,maxDepth:6};
test('all original independent array vectors',()=>{
  for(const v of vectors.vectors){
    const run=()=>decodeNativeTextArray(v.text,v.dimensions,limits);
    if(v.expected.kind==='refusal') expect(run).toThrow('native-correspondence');
    else {const actual=run(); expect(actual.kind).toBe(v.expected.kind);
      if(actual.kind==='array'){expect(actual.bounds).toEqual(v.expected.bounds);expect(actual.elements).toEqual(v.expected.elements);}
      expect(actual.originalText).toBe(v.text);}
  }
});
test('escaping, complete shape, original scalar and budgets',()=>{
  expect(decodeNativeTextArray('{"a\\"b","c\\\\d"}','[1:2]',limits)).toMatchObject({elements:['a"b','c\\d']});
  for(const text of ['{a,}','{a}x','{{a},{b,c}}','{a,{b}}','{"a}','{a b}','{\ud800}','{a\0}'])
    expect(()=>decodeNativeTextArray(text,'[1:1]',limits)).toThrow();
  expect(()=>decodeNativeTextArray('{é}','[1:1]',{...limits,maxBytes:3})).toThrow('resource-limit');
  expect(()=>decodeNativeTextArray('{a}','[1:1]',{...limits,maxNodes:1})).toThrow('resource-limit');
  expect(()=>decodeNativeTextArray('{{a}}','[1:1][1:1]',{...limits,maxDepth:1})).toThrow('resource-limit');
  expect(()=>decodeNativeTextArray('[0:1]={a,b}','[1:2]',limits)).toThrow('native-correspondence');
  const v=decodeNativeTextArray('{é,"NULL",NULL}','[1:3]',limits);
  expect(Object.isFrozen(v)).toBe(true);
  if(v.kind==='array'){expect(Object.isFrozen(v.elements)).toBe(true);expect(v.elements).toEqual(['é','NULL',null]);}
});
