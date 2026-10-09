/** Private producer design under CONTRACT-003; no callable public acceptance API. */
import type {AcceptanceInput,ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
/** Representation is selected by original installed registration, never guessed. */
export type OriginalAcceptanceInputSource = {
 readonly representation:'raw-json-transport';
 readonly artifact:ExactArtifact;
 readonly decoderProfile:ProfilePin;
} | {
 readonly representation:'canonical-tree-utf8';
 readonly artifact:ExactArtifact;
 readonly canonicalProfile:'truss-canonical/0.1.0';
} | {
 readonly representation:'framed-fingerprint-preimage';
 readonly artifact:ExactArtifact;
 readonly canonicalProfile:'truss-canonical/0.1.0';
 readonly domain:'truss-acceptance-input/0.1.0';
};
declare const originalInputCustody:unique symbol;
declare const originalInputAccount:unique symbol;
/** Issued only by the trusted original operation/custody resolver; labels are not proof. */
export interface OriginalAcceptanceInputCustody {
 readonly [originalInputCustody]:true;
}
/** Precharged original operation account, not caller-provided remaining counters. */
export interface OriginalAcceptanceInputAccount {
 readonly [originalInputAccount]:true;
}
export interface AcceptanceInputProducerRequest {
 readonly source:OriginalAcceptanceInputSource;
 readonly custody:OriginalAcceptanceInputCustody;
 readonly account:OriginalAcceptanceInputAccount;
 readonly installedInputProfile:ProfilePin;
}
/** Private, immutable original output. Brands require issuer/liveness verification. */
declare const admittedOriginalInput:unique symbol;
export interface AdmittedOriginalAcceptanceInput {
 readonly [admittedOriginalInput]:true;
 readonly source:OriginalAcceptanceInputSource;
 readonly input:AcceptanceInput;
 readonly canonicalTree:ExactArtifact;
 readonly framedPreimage:ExactArtifact;
 readonly canonicalProfile:'truss-canonical/0.1.0';
 readonly domain:'truss-acceptance-input/0.1.0';
 readonly installedInputProfile:ProfilePin;
}
export type AcceptanceInputProducerResult = {
 readonly status:'admitted';readonly original:AdmittedOriginalAcceptanceInput;
} | {
 readonly status:'refused';
 readonly reason:'invalid_source'|'invalid_input'|'artifact_integrity'|'unsupported_representation'|'unsupported_profile'|'custody'|'resource';
};
/** Complete bounded interpretation only; no catalog effects, report/head or commit. */
export interface RegisteredAcceptanceInputProducer {
 produce(request:AcceptanceInputProducerRequest):AcceptanceInputProducerResult;
}
