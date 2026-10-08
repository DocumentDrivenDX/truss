import {test,expect} from 'bun:test';
import {decodeNativeRoutineCarriers} from '../packages/postgresql/src/index';
const limits={maxBytes:4096,maxNodes:128,maxDepth:6,maxTokens:64};
const source={originalCatalogRowJson:'{"uninterpreted":123456789012345678901234}',inputCount:'2',inputTypesText:'23 25',inputTypesDimensions:'[0:1]',
  names:{text:'{x,y}',dimensions:'[1:2]',rawJson:'["x","y"]'},
  modes:{text:null,dimensions:null,rawJson:'null'},
  settings:{text:'{"search_path=pg_catalog, pg_temp"}',dimensions:'[1:1]',rawJson:'["search_path=pg_catalog, pg_temp"]'}};
test('routine carriers preserve original opaque row and compare text semantics',()=>{
  const value=decodeNativeRoutineCarriers(source,limits);
  expect(value.originalCatalogRowJson).toBe(source.originalCatalogRowJson);
  expect(value.inputTypes.tokens).toEqual(['23','25']);
  expect(value.settings).toMatchObject({elements:['search_path=pg_catalog, pg_temp']});
  expect(value.modes.kind).toBe('native-null');
});
test('mismatched original projections and vector bounds refuse',()=>{
  expect(()=>decodeNativeRoutineCarriers({...source,inputTypesDimensions:'[1:2]'},limits)).toThrow();
  expect(()=>decodeNativeRoutineCarriers({...source,inputCount:'3'},limits)).toThrow();
  expect(()=>decodeNativeRoutineCarriers({...source,names:{...source.names,rawJson:'["y","x"]'}},limits)).toThrow();
  expect(()=>decodeNativeRoutineCarriers({...source,modes:{...source.modes,rawJson:'[]'}},limits)).toThrow();
});
