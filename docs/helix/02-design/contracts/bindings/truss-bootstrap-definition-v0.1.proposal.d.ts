/** CONTRACT-008 internal resolved-definition proposal; no runtime/native qualification. */
import type {ExactArtifact, ProfilePin, CanonicalTree} from './truss-acceptance-input-v0.1';
import type {BootstrapCatalogAddress} from './truss-bootstrap-collection-result-v0.1';
export type DefinitionAssociation =
 {readonly kind:'object'; readonly address:BootstrapCatalogAddress} |
 {readonly kind:'adjunct'; readonly parent:BootstrapCatalogAddress;
  readonly keyProfile:ProfilePin; readonly key:CanonicalTree} |
 {readonly kind:'context'; readonly contextProfile:ProfilePin;
  readonly originalContext:ExactArtifact};
interface FieldOrigin {
 readonly observationIdentity:string;
 /** Exact path under the admitted raw observation grammar, not a SQL identifier. */
 readonly originalPath:string;
 readonly originalValue:ExactArtifact;
}
export type DefinitionFieldClassification = FieldOrigin & (
 {readonly kind:'stable'; readonly interpretationProfile:ProfilePin;
  readonly interpretedValue:CanonicalTree} |
 {readonly kind:'operational_evidence'; readonly exclusionProfile:ProfilePin;
  readonly governingReason:string} |
 {readonly kind:'preserved_unsupported'; readonly reason:string});
export interface DefinitionDependency {
 readonly originalObservationIdentity:string;
 readonly originalPath:string;
 readonly originalDependency:ExactArtifact;
 /** Identity reference avoids recursive definition-digest construction. */
 readonly resolution:{readonly kind:'definition';readonly definitionIdentity:string} |
  {readonly kind:'terminal';readonly terminalProfile:ProfilePin;readonly evidence:ExactArtifact};
}
interface DefinitionCustody {
 readonly interfaceVersion:'truss-bootstrap-definition/0.1.0';
 readonly definitionIdentity:string;
 readonly association:DefinitionAssociation;
 readonly originalScope:ExactArtifact;
 readonly originalCut:ExactArtifact;
 readonly originalAttempt:ExactArtifact;
 readonly routeProfile:ProfilePin;
 readonly observations:readonly [ExactArtifact,...ExactArtifact[]];
 readonly resourceEvidence:ExactArtifact;
}
export type BootstrapDefinitionAssembly =
 (DefinitionCustody & {readonly outcome:'complete';
  readonly interpretationProfile:ProfilePin;
  readonly fields:readonly (FieldOrigin & (
   {readonly kind:'stable';readonly interpretationProfile:ProfilePin;readonly interpretedValue:CanonicalTree} |
   {readonly kind:'operational_evidence';readonly exclusionProfile:ProfilePin;readonly governingReason:string}))[];
  readonly dependencies:readonly DefinitionDependency[];
  readonly interpretedDefinition:ExactArtifact;
  /** Original complete membership/classification/closure/consistency proof. */
  readonly admissionEvidence:ExactArtifact}) |
 (DefinitionCustody & {readonly outcome:'incomplete';
  readonly reason:'unsupported'|'unresolved'|'conflicting'|'resource'|'cut'|'authority';
  readonly fields:readonly DefinitionFieldClassification[];
  readonly unresolvedEvidence:ExactArtifact;
  readonly interpretedDefinition?:never;
  readonly admissionEvidence?:never});
/** Types do not prove total field coverage, reference closure or original custody. */
