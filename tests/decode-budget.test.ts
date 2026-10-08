import {test,expect} from 'bun:test';
import {NativeDecodeBudget,decodeNativeTextArray,decodeNativeVector,decodeNativeRoutineCarriers} from '../packages/postgresql/src/index';
test('individually valid fields exhaust shared budget before second materialization',()=>{
  const ledger=new NativeDecodeBudget(9,20);
  const limits={maxBytes:100,maxNodes:20,maxDepth:6,ledger};
  expect(decodeNativeTextArray('{abc}','[1:1]',limits).kind).toBe('array');
  expect(()=>decodeNativeTextArray('{def}','[1:1]',limits)).toThrow('native-budget:exhausted');
  expect(ledger.remaining).toEqual({bytes:4,nodes:18,exhausted:true});
  expect(()=>decodeNativeVector('oidvector','', {...limits,maxTokens:20})).toThrow('native-budget:exhausted');
});
test('shared node cap and immutable snapshots',()=>{
  const ledger=new NativeDecodeBudget(100,3);
  decodeNativeVector('oidvector','1 2',{maxBytes:100,maxTokens:20,ledger});
  const snapshot=ledger.remaining;
  expect(()=>decodeNativeTextArray('{}',null,{maxBytes:100,maxNodes:20,maxDepth:6,ledger})).toThrow('native-budget:exhausted');
  expect(snapshot.exhausted).toBe(false);expect(Object.isFrozen(snapshot)).toBe(true);
  expect(()=>new NativeDecodeBudget(-1,3)).toThrow();
});
test('routine custody and projections consume one caller-owned ledger',()=>{
  const nullField={text:null,dimensions:null,rawJson:'null'};
  const ledger=new NativeDecodeBudget(10,20);
  expect(()=>decodeNativeRoutineCarriers({originalCatalogRowJson:'{}',inputCount:'0',inputTypesText:'',inputTypesDimensions:'[0:-1]',names:nullField,modes:nullField,settings:nullField},
    {maxBytes:100,maxNodes:20,maxDepth:6,maxTokens:20,ledger})).toThrow('native-budget:exhausted');
  expect(ledger.remaining.exhausted).toBe(true);
});
