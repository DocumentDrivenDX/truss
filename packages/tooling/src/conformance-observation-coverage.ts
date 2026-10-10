/** Private coverage check over shape-admitted bounded projections.
 * Required keys must come from original registered procedures, never case claims.
 * This function does not establish that provenance or perform observations. */
export type ConformanceObservationKey = {
  surface: 'result' | 'state' | 'journal' | 'report' | 'performance';
  step: string;
  boundary: string;
};
export function checkAdmittedConformanceObservationCoverage(
  required: readonly ConformanceObservationKey[],
  expected: readonly ConformanceObservationKey[],
): boolean {
  const key = (entry: ConformanceObservationKey) =>
    JSON.stringify([entry.surface, entry.step, entry.boundary]);
  const requiredKeys = new Set(required.map(key));
  const expectedKeys = new Set(expected.map(key));
  if (requiredKeys.size !== required.length || expectedKeys.size !== expected.length)
    return false;
  return requiredKeys.size === expectedKeys.size &&
    [...requiredKeys].every(value => expectedKeys.has(value));
}
