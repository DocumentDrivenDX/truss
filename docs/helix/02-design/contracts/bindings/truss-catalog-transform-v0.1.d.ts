/** CONTRACT-003 candidate per-property transform; purity is a host obligation. */
import type {CanonicalTree, ProfilePin, ExactArtifact} from './truss-acceptance-input-v0.1';
import type {Presence, TypedIdentity} from './truss-history-v0.1';
export interface CatalogTransformInput {
  readonly interfaceVersion: 'truss-catalog-transform/0.1.0';
  readonly registration: ProfilePin;
  readonly dependencyProfile: ProfilePin;
  readonly targetDefinitionIdentity: string;
  readonly beforeDefinitionPin: string;
  readonly afterDefinitionPin: string;
  readonly priorCatalogRevision: string;
  readonly candidateCatalogRevision: string;
  readonly record: TypedIdentity;
  readonly propertyId: string;
  readonly before: Presence;
  /** Declared same-record prior-state inputs; no implicit access to candidate outputs. */
  readonly dependencies: readonly {
    readonly propertyId: string; readonly definitionPin: string;
    readonly before: Presence;
  }[];
  readonly parameters: CanonicalTree;
}
export type CatalogTransformResult = {
  readonly outcome: 'candidate'; readonly after: Presence;
} | {
  readonly outcome: 'rejected'; readonly code: string;
  readonly path: readonly string[];
};
/** No executor or connection is supplied; declaration is not a sandbox. */
export type RegisteredCatalogTransform = (input: CatalogTransformInput) => CatalogTransformResult;
export interface CatalogTransformRegistration {
  readonly manifest:ExactArtifact;
  readonly profile: ProfilePin;
  readonly operation: RegisteredCatalogTransform;
  readonly resourceProfile: ProfilePin;
  readonly execution: {readonly kind: 'trusted_cooperative'} |
    {readonly kind: 'isolated'; readonly executionProfile: ProfilePin};
  readonly inputValueProfile: ProfilePin;
  readonly outputValueProfile: ProfilePin;
  readonly dependencyProfile: ProfilePin;
  readonly declaredDependencies: readonly {
    readonly propertyId: string; readonly definitionPin: string;
  }[];
  readonly supportedDefinitionPairs: readonly {
    readonly beforeDefinitionPin: string; readonly afterDefinitionPin: string;
  }[];
}

import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
declare const catalogTransformRegistrationBrand:unique symbol;
export interface CatalogTransformRegistrationHandle {
 readonly [catalogTransformRegistrationBrand]:true;
 readonly selection:CapabilitySelection & {readonly family:'catalog'};
 readonly profile:ProfilePin;
}
export type CatalogTransformRegistrationResult={readonly status:'ok';readonly registration:CatalogTransformRegistrationHandle}|
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'|'duplicate_profile'|'invalid_inventory';readonly registration?:never};
/** Inert assembly-scoped custody; never invokes callback or validates native data. */
export declare function registerCatalogTransform(assembly:ReferenceAssembly,
 selection:CapabilitySelection & {readonly family:'catalog'},
 registration:CatalogTransformRegistration):CatalogTransformRegistrationResult;
