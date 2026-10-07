/** CONTRACT-003 candidate enumeration, not a UMF schema or Weft mapping. */
import type {ProfilePin, ExactArtifact} from './truss-acceptance-input-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
interface DefinitionIdentity {
  readonly definitionPin: string;
  readonly owner: QualifiedOwner;
  /** For core-Key references, exact Record.keys[].id under extraction provenance. */
  readonly authoredIdentity: string;
}
/** Key numbers are local to a type; they are not global catalog IDs. */
export type CatalogDefinitionReference = DefinitionIdentity & ({
  readonly kind: 'type'; readonly typeId: string;
} | {
  readonly kind: 'property'; readonly propertyId: string; readonly typeId: string;
} | {
  readonly kind: 'key'; readonly typeId: string; readonly keyNumber: string;
} | {
  readonly kind: 'relationship'; readonly relationshipId: string;
});
export interface CatalogDefinitionEntry {
  readonly reference: CatalogDefinitionReference;
  readonly lifecycle: 'active' | 'retired';
  readonly resolution: 'defined' | 'provisional';
  /** Exact archived definition, including unrecognized extension content. */
  readonly definition: ExactArtifact;
  readonly provenance: {
    readonly kind: 'accepted_document';
    readonly acceptedCatalogRevision: string;
    readonly documentOrdinal: string;
    readonly documentRevision: string;
    readonly acceptedDocumentSha256: string;
    readonly authoredPointer: string;
    readonly extractionProfile: ProfilePin;
  } | {
    readonly kind: 'accepted_binding';
    readonly acceptedCatalogRevision: string;
    readonly acceptedBindingSha256: string;
    readonly bindingVocabulary: ProfilePin;
    readonly authoredPointer: string;
    readonly extractionProfile: ProfilePin;
    readonly owningRecordDefinitionPin: string;
    readonly owningRecordProvenance: {
      readonly acceptedCatalogRevision: string;
      readonly documentOrdinal: string;
      readonly documentRevision: string;
      readonly acceptedDocumentSha256: string;
      readonly authoredPointer: string;
      readonly extractionProfile: ProfilePin;
    };
  };
  /** Ordered semantic references; order is never guessed from storage IDs. */
  readonly dependencies: readonly CatalogDefinitionReference[];
}
export interface CatalogView {
  readonly interfaceVersion: 'truss-catalog-view/0.1.0';
  readonly catalogRevision: string;
  readonly layoutProfile: ProfilePin;
  readonly viewProfile: ProfilePin;
  readonly consistencyEvidenceSha256: string;
  readonly scope: {readonly kind: 'complete'} | {
    readonly kind: 'authorized_projection'; readonly authorizedScopeIdentity: string;
    readonly closure: 'complete_within_projection';
  };
  readonly definitions: readonly CatalogDefinitionEntry[];
  readonly inventorySha256: string;
}
export interface CatalogViewRequest {
  readonly interfaceVersion: 'truss-catalog-view-request/0.1.0';
  readonly layoutProfile: ProfilePin;
  readonly viewProfile: ProfilePin;
  readonly selection: {readonly kind: 'current'} |
    {readonly kind: 'historical'; readonly catalogRevision: string};
  readonly scope: {readonly kind: 'complete'} | {
    readonly kind: 'authorized_projection';
    readonly owners: readonly [QualifiedOwner, ...QualifiedOwner[]];
  };
  /** Explicit caller budget under the selected profile, never truncation permission. */
  readonly limits: {readonly definitionCount: string; readonly encodedBytes: string};
}
export type CatalogViewResult = {readonly outcome: 'available'; readonly view: CatalogView} | {
  readonly outcome: 'unavailable';
  readonly reason: 'context' | 'closure' | 'definition' | 'profile' | 'resource';
  readonly view?: never;
};
