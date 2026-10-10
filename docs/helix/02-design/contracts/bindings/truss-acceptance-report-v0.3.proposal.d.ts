/** Candidate lifecycle/history composition; runtime/native admission is separate. */
import type {ProposedAcceptanceReport} from './truss-acceptance-report-v0.2.proposal';
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
export type ReactivatedCatalogIdentity =
 {readonly kind:'type';readonly typeId:string} |
 {readonly kind:'property';readonly propertyId:string} |
 {readonly kind:'key';readonly typeId:string;readonly keyNumber:string} |
 {readonly kind:'relationship';readonly relationshipId:string};
export interface CatalogReactivation {
 readonly identity:ReactivatedCatalogIdentity;
 readonly owner:QualifiedOwner;
 readonly lineage:ExactArtifact;
 /** Canonical native revision text; positive/prior-order semantics are validated. */
 readonly beforeRetiredRevision:string;
 readonly beforeDefinition:ExactArtifact;
 readonly afterDefinition:ExactArtifact;
}
export type ProposedComposedAcceptanceReport = Omit<ProposedAcceptanceReport,'interfaceVersion'> & {
 readonly interfaceVersion:'truss-acceptance-report/0.3.0-proposal';
 readonly lifecycleProfile:ProfilePin;
 readonly reactivations:readonly CatalogReactivation[];
};
