/** CONTRACT-008 native comparison envelope; complete collection profiles remain selected. */
import type {ExactArtifact,ProfilePin,CanonicalTree} from './truss-acceptance-input-v0.1';
import type {InstalledPolicyInventory,QualifiedRelation,QualifiedRoutine} from './truss-installed-policy-v0.1';
export type BootstrapInventoryEntry = {
 readonly physicalIdentity:string;
 readonly ownership:{readonly inventoryProfile:ProfilePin;readonly inventoryArtifact:ExactArtifact;readonly entryId:string};
 readonly nativeProfile:ProfilePin;
 readonly definition:ExactArtifact;
 readonly owningInputPath:string;
} & ({readonly objectKind:'schema';readonly nativeIdentity:{readonly schema:string}} |
 {readonly objectKind:'table'|'index'|'sequence'|'partition'|'view'|'materialized_view';readonly nativeIdentity:QualifiedRelation} |
 {readonly objectKind:'column';readonly nativeIdentity:{readonly relation:QualifiedRelation;readonly name:string;readonly ordinal:string}} |
 {readonly objectKind:'policy'|'trigger';readonly nativeIdentity:{readonly relation:QualifiedRelation;readonly name:string}} |
 {readonly objectKind:'constraint';readonly nativeIdentity:{readonly name:string;readonly owner:
  {readonly kind:'relation';readonly relation:QualifiedRelation;readonly domain?:never} |
  {readonly kind:'domain';readonly domain:{readonly schema:string;readonly name:string};readonly relation?:never}}} |
 {readonly objectKind:'routine';readonly nativeIdentity:QualifiedRoutine} |
 {readonly objectKind:'role';readonly nativeIdentity:{readonly name:string}} |
 {readonly objectKind:'type'|'collation';readonly nativeIdentity:{readonly schema:string;readonly name:string}} |
 {readonly objectKind:'grant'|'extension';readonly nativeIdentity:{readonly identityProfile:ProfilePin;readonly value:CanonicalTree}});
export interface BootstrapNativeInventory {
 readonly interfaceVersion:'truss-bootstrap-native-inventory/0.1.0';
 readonly profile:ProfilePin;readonly layoutVersion:string;
 readonly namespace:{readonly databaseIdentity:string;readonly schemaName:string};
 readonly target:ExactArtifact;
 readonly observation:{readonly phase:'installation_transaction';readonly bootstrapAttemptId:string} |
  {readonly phase:'committed';readonly installationId:string;readonly commitEvidence:ExactArtifact};
 readonly entries:readonly [BootstrapInventoryEntry,...BootstrapInventoryEntry[]];
 readonly initialization:ExactArtifact;
 /** Exact observed installation data is independently checked, outside self-hashing basis. */
 readonly installationMetadata:{
  readonly marker:{readonly state:'not_yet_written'} | {readonly state:'present';readonly artifact:ExactArtifact};
  readonly archives:readonly ExactArtifact[];
  readonly correspondenceEvidence:ExactArtifact;
 };
 readonly policy:InstalledPolicyInventory;
 readonly collection:{readonly procedure:ExactArtifact;readonly rawObservations:readonly [ExactArtifact,...ExactArtifact[]];
  readonly completeScopeEvidence:ExactArtifact};
}

/** Immutable installed-layout comparison basis; volatile observation/custody is separate. */
export interface BootstrapInventoryBasis {
 readonly interfaceVersion:'truss-bootstrap-inventory-basis/0.1.0';
 readonly profile:ProfilePin;readonly layoutVersion:string;
 readonly namespace:BootstrapNativeInventory['namespace'];
 readonly targetMeaning:ExactArtifact;
 readonly entries:BootstrapNativeInventory['entries'];
 /** Original admitted initialization meaning, not today's mutable revision/settings rows. */
 readonly initializationMeaning:ExactArtifact;
 readonly policyMeaning:Omit<InstalledPolicyInventory,'writer'|'observer'|'extraction'|'administrativeCapabilities'> & {
  readonly administrativeCapabilities:readonly {readonly role:string;readonly capability:string;readonly permitted:boolean}[];
 };
 readonly requiredWriterRoles:readonly string[];
}

/** BP01–BP07 internal projection handoff; adds no shared compiler or native-inventory ABI. */
export interface BootstrapProjectionFact {
 readonly factIdentity:string;
 readonly originalArtifact:ExactArtifact;
 /** Exact original decoded-field locator under its admitted source grammar, not authority itself. */
 readonly locator:string;
 readonly sourceProfile:ProfilePin;
}
export type BootstrapFieldDisposition = {readonly fact:BootstrapProjectionFact} & (
 {readonly kind:'declared';readonly meaningProfile:ProfilePin;
  readonly contributions:readonly [{readonly basisPath:string;readonly value:CanonicalTree},
   ...{readonly basisPath:string;readonly value:CanonicalTree}[]];readonly correspondenceEvidence:ExactArtifact} |
 {readonly kind:'excluded';readonly reason:'physical'|'operational'|'outside_selected_scope';
  readonly exclusionProfile:ProfilePin;readonly originalMeaningEvidence:ExactArtifact;
  /** Independently checked when the excluded state matters to installed readiness. */
  readonly readiness:{readonly kind:'required';readonly evidence:ExactArtifact} |
   {readonly kind:'not_required';readonly rationale:ExactArtifact}} |
 {readonly kind:'unsupported';readonly reason:'unknown_field'|'unknown_meaning'|'unavailable_required_fact';
  readonly retainedEvidence:ExactArtifact});
export interface BootstrapProjectionCustody {
 readonly interfaceVersion:'truss-bootstrap-projection-result/0.1.0';
 readonly originalInventory:BootstrapNativeInventory;
 readonly projectionProfile:ProfilePin;
 readonly identityRegistry:ExactArtifact;
 /** Total fact inventory and exactly-once disposition verification are runtime obligations. */
 readonly factInventory:ExactArtifact;
 readonly dispositions:readonly [BootstrapFieldDisposition,...BootstrapFieldDisposition[]];
 readonly resourceEvidence:ExactArtifact;
}
export type BootstrapProjectionResult =
 (BootstrapProjectionCustody & {readonly outcome:'complete';readonly basis:BootstrapInventoryBasis;
  readonly canonicalBasis:ExactArtifact;readonly completeCorrespondence:ExactArtifact;
  readonly refusal?:never}) |
 (BootstrapProjectionCustody & {readonly outcome:'incomplete';
  readonly refusal:ExactArtifact;readonly basis?:never;readonly canonicalBasis?:never;
  readonly completeCorrespondence?:never});
/** These declarations never issue readiness, installation or commit authority. */
