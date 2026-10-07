import type {RetentionDropRequest,RetentionDropResult} from './truss-retention-tooling-v0.1';
declare const request:RetentionDropRequest;
declare const dropped:Extract<RetentionDropResult,{readonly outcome:'dropped'}>;
// @ts-expect-error A timestamp-only cutoff does not establish protected eligibility.
const cutoff:RetentionDropRequest={interfaceVersion:request.interfaceVersion,cutoff:'2026-10-06'};
// @ts-expect-error Supplied transaction partition deletion remains pending.
const committed:RetentionDropResult={...dropped,durability:'committed'};
// @ts-expect-error Refusal cannot advertise a new retained horizon.
const protectedResult:RetentionDropResult={outcome:'refused',reason:'protected',resultingRetainedHorizon:dropped.resultingRetainedHorizon};
void [cutoff,committed,protectedResult];
