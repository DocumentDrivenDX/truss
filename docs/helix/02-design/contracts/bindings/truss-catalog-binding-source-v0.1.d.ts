/** CONTRACT-001/003 candidate original binding source; valid shape is not custody. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {CatalogDefinitionEntry, CatalogDefinitionReference} from './truss-catalog-view-v0.1';
export interface CatalogBindingSource {
  readonly interfaceVersion: 'truss-catalog-binding-source/0.1.0';
  readonly sourceProfile: ProfilePin;
  readonly reference: CatalogDefinitionReference;
  readonly definition: ExactArtifact;
  readonly provenance: Extract<CatalogDefinitionEntry['provenance'], {readonly kind:'accepted_binding'}>;
  readonly acceptedBinding: ExactArtifact;
  readonly owningRecordDefinition: ExactArtifact;
  readonly owningRecordDocument: ExactArtifact;
  readonly derivationDependencies: readonly ExactArtifact[];
  readonly originalSourceEvidence: ExactArtifact;
}
