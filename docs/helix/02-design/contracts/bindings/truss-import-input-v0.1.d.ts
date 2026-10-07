/** CONTRACT-004 candidate identity-first input; payload admission is deferred. */
import type {ProfilePin, ExactArtifact} from './truss-acceptance-input-v0.1';
import type {DirectLookupRequest} from './truss-direct-read-v0.1';
import type {TypedIdentity, ExactValue} from './truss-history-v0.1';
type ObjectKeySelection=Extract<DirectLookupRequest['selection'],{readonly operation:'object_key'}>;
export type ImportRecordInput = {
  readonly kind:'object'; readonly identity:ObjectKeySelection;
  /** Exact value/source/ownership input; decode only after eligible creation. */
  readonly payload:ExactArtifact; readonly payloadProfile:ProfilePin;
} | {
  readonly kind:'edge';
  readonly identity:{readonly relationshipDefinitionPin:string;readonly source:TypedIdentity;readonly target:TypedIdentity};
  readonly payload:ExactArtifact; readonly payloadProfile:ProfilePin;
};
export interface ImportInput {
  readonly interfaceVersion:'truss-import-input/0.1.0';
  readonly layoutProfile:ProfilePin; readonly importProfile:ProfilePin;
  readonly valueProfile:ProfilePin;
  readonly catalog:{readonly revision:string;readonly modelBundleSha256:string};
  readonly loadId:string; readonly assertedOrigin:ExactValue;
  /** Original submission order; never replace with object/edge phase order. */
  readonly records:readonly ImportRecordInput[];
}
