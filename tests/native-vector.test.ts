import {test, expect} from 'bun:test';
import {decodeNativeVector, NativeVectorError} from '../packages/postgresql/src/index';
import vectors from '../docs/helix/02-design/contracts/bindings/bootstrap-native-vector-decoder-v0.1.vectors.proposal.json';
const limits = {maxBytes: 1024, maxTokens: 64};
test('original independent CONTRACT-008 vectors', () => {
  for (const vector of vectors.vectors) {
    const run = () => decodeNativeVector(vector.family as 'oidvector' | 'int2vector', vector.text, limits,
      'declaredCount' in vector ? vector.declaredCount : undefined);
    if ('refusal' in vector || 'semanticRefusal' in vector) {
      expect(run).toThrow(NativeVectorError);
    } else {
      expect(run().tokens).toEqual(vector.expectedTokens);
      expect(run().originalText).toBe(vector.text);
    }
  }
});
test('bounded exact parsing and immutable original spelling', () => {
  for (const text of ['01', '+1', '-0', '1\t2', ' 1', '1 ', '１', '1\n', '1\0'])
    expect(() => decodeNativeVector('int2vector', text, limits)).toThrow(NativeVectorError);
  expect(() => decodeNativeVector('oidvector', '1 2', {maxBytes: 3, maxTokens: 1})).toThrow('resource-limit');
  expect(() => decodeNativeVector('oidvector', '1', {maxBytes: 0, maxTokens: 1})).toThrow('resource-limit');
  expect(() => decodeNativeVector('oidvector', '1', limits, '01')).toThrow('count-correspondence');
  expect(() => decodeNativeVector('oidvector', '1', limits, '9'.repeat(10000))).toThrow('resource-limit');
  const result = decodeNativeVector('oidvector', '0 4294967295', limits, '2');
  expect(Object.isFrozen(result)).toBe(true);
  expect(Object.isFrozen(result.tokens)).toBe(true);
  expect(result.tokens).toEqual(['0', '4294967295']);
});
