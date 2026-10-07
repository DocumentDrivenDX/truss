/** Unadopted ADR-004 reactivation branch; not accepted wire or native support. */
import type {AcceptanceReport} from './truss-acceptance-report-v0.1';
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
export type CatalogReactivationIdentity =
  | {readonly kind:'type';readonly typeId:string}
  | {readonly kind:'property';readonly propertyId:string}
  | {readonly kind:'key';readonly typeId:string;readonly keyNumber:string}
  | {readonly kind:'relationship';readonly relationshipId:string};
export interface CatalogReactivation {
  readonly identity:CatalogReactivationIdentity;
  readonly owner:QualifiedOwner;
  /** Full original qualified lineage; digest alone cannot identify a return. */
  readonly lineage:ExactArtifact;
  readonly beforeRetiredRevision:string;
  /** Complete original catalog/source/lifecycle snapshots, not current guesses. */
  readonly beforeDefinition:ExactArtifact;
  readonly afterDefinition:ExactArtifact;
}
export interface ReactivationAcceptanceReport extends Omit<AcceptanceReport,'interfaceVersion'> {
  readonly interfaceVersion:'truss-acceptance-report/0.2.0';
  readonly lifecycleProfile:ProfilePin;
  /** Exactly one entry per actual same-ID retired-to-active transition. */
  readonly reactivations:readonly CatalogReactivation[];
}
