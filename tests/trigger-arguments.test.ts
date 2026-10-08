import {test,expect} from 'bun:test';
import {decodeNativeTriggerArguments} from '../packages/postgresql/src/index';
import vectors from '../docs/helix/02-design/contracts/bindings/bootstrap-trigger-arguments-v0.1.vectors.proposal.json';
const limits = {maxBytes:4096,maxArguments:64};
test('all twelve independent original trigger argument vectors',()=>{
  for(const v of vectors.vectors){
    const run=()=>decodeNativeTriggerArguments(v.count,v.hex,v.byteLength,limits,'UTF8');
    if('refusal' in v) expect(run).toThrow('trigger-arguments:'+v.refusal);
    else {expect(run().arguments).toEqual(v.expectedStrings);expect(run().originalHex).toBe(v.hex);}
  }
});
test('exact encoding and allocation controls',()=>{
  expect(decodeNativeTriggerArguments('1','efbbbf00','4',limits,'UTF8').arguments).toEqual(['\ufeff']);
  for(const hex of ['c08000','eda08000','f490808000'])
    expect(()=>decodeNativeTriggerArguments('1',hex,String(hex.length/2),limits,'UTF8')).toThrow('encoding');
  expect(()=>decodeNativeTriggerArguments('32768','','0',limits,'UTF8')).toThrow('count');
  expect(()=>decodeNativeTriggerArguments('01','','0',limits,'UTF8')).toThrow('count');
  expect(()=>decodeNativeTriggerArguments('1','AA00','2',limits,'UTF8')).toThrow('hex-domain');
  expect(()=>decodeNativeTriggerArguments('1','00','1',{...limits,maxBytes:0},'UTF8')).toThrow('resource-limit');
  expect(()=>decodeNativeTriggerArguments('1','00','1',{...limits,maxArguments:0},'UTF8')).toThrow('resource-limit');
  const value=decodeNativeTriggerArguments('1','00','1',limits,'UTF8');
  expect(Object.isFrozen(value)).toBe(true);expect(Object.isFrozen(value.arguments)).toBe(true);
});
