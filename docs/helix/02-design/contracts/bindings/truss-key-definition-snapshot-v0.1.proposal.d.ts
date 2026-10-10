/** Unadopted ADR-004 history proposal; no source/native support assertion. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
export interface KeyDefinitionSnapshot {
  readonly interfaceVersion:'truss-key-definition-snapshot/0.1.0';
  readonly snapshotProfile:ProfilePin;
  readonly catalogRevision:string;
  readonly owner:QualifiedOwner;
  readonly lineage:ExactArtifact;
  readonly typeId:string;
  readonly keyNumber:string;
  readonly keyId:string;
  readonly propertyIds:readonly string[];
  readonly isPrimary:boolean;
  readonly sinceRevision:string;
  readonly retiredRevision:string|null;
  /** Full original native definition, not just the mirrors above. */
  readonly nativeDefinition:ExactArtifact;
  readonly sourceDefinition:ExactArtifact;
  readonly acceptedBinding:ExactArtifact;
  readonly interpretation:ExactArtifact;
}
