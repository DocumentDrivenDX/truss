/** Compact source-reference wire profile; Python compatibility bytes are derived on request. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {CatalogView as LegacyView, CatalogDefinitionEntry as LegacyEntry} from './truss-catalog-view-v0.1';
export interface CatalogDefinitionEntry extends Omit<LegacyEntry,'definition'|'dependencies'|'provenance'> {
  /** Exact fragment SHA256; identity is reference.definitionPin. */
  readonly definition: {readonly sha256: string};
  /** Ordered pins resolving to definitions in this complete view. */
  readonly dependencies: readonly string[];
  readonly provenance: Omit<Extract<LegacyEntry['provenance'],{kind:'accepted_document'}>,'extractionProfile'>;
}
export interface CatalogView extends Omit<LegacyView,'interfaceVersion'|'definitions'> {
  readonly interfaceVersion: 'truss-catalog-view/0.2.0';
  readonly extractionProfile: ProfilePin;
  readonly definitions: readonly CatalogDefinitionEntry[];
}
