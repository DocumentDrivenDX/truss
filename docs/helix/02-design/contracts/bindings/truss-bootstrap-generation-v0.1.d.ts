/** CONTRACT-008 proposed pure generation surface; candidates are not installed proof. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
export interface BootstrapBundle {
 readonly interfaceVersion:'truss-bootstrap-bundle/0.1.0';
 readonly layoutVersion:string;
 readonly model:{readonly document:ExactArtifact;readonly coreVersion:string;
  readonly vocabularies:readonly ProfilePin[];readonly nativeProfile:ProfilePin};
 readonly generator:{readonly operation:ProfilePin;readonly backend:ProfilePin};
 readonly target:{readonly postgresqlVersion:string;readonly encoding:string;
  readonly localeProfile:ProfilePin;readonly settings:ExactArtifact};
 readonly names:{readonly schema:string;readonly identifierMap:ExactArtifact;readonly profile:ProfilePin};
 readonly initialization:{readonly profile:ProfilePin;readonly orderedInput:ExactArtifact};
 readonly expectedCatalog:{readonly profile:ProfilePin;readonly inventory:ExactArtifact};
 readonly canonicalizationProfile:ProfilePin;
}
export interface BootstrapCoverageEntry {
 readonly physicalIdentity:string;
 readonly objectKind:string;
 readonly owningInputPath:string;
 readonly statementOrdinal:string;
 readonly disposition:'generated'|'initialization';
}
export interface BootstrapStatementInventory {
 readonly interfaceVersion:'truss-bootstrap-statements/0.1.0';
 readonly compositionProfile:ProfilePin;
 readonly statements:readonly [{
  readonly ordinal:string;readonly sql:ExactArtifact;
  readonly sources:readonly [string,...string[]];
 },...{
  readonly ordinal:string;readonly sql:ExactArtifact;
  readonly sources:readonly [string,...string[]];
 }[]];
 /** Explicit joins preserve complete SQL bytes without lexical statement splitting. */
 readonly joins:readonly string[];
}
export type BootstrapGenerationResult = {
 readonly outcome:'candidate';
 readonly bundle:BootstrapBundle;
 /** Raw content digest of canonical bundleArtifact bytes, without identity-domain prefix. */
 readonly bundleSha256:string;
 readonly bundleArtifact:ExactArtifact;
 /** Complete SQL text and independent ordered statement/source correspondence. */
 readonly sql:ExactArtifact;
 readonly statementInventory:BootstrapStatementInventory;
 readonly coverage:readonly BootstrapCoverageEntry[];
 readonly obligations:readonly ExactArtifact[];
 readonly qualification:{readonly state:'unverified'} |
  {readonly state:'qualified';readonly targetProfile:ProfilePin;readonly evidence:ExactArtifact};
 readonly sourcePins:{
  /** Original model/generator/target/names/initialization/inventory inputs, no qualification receipt. */
  readonly generation:readonly [ExactArtifact,...ExactArtifact[]];
  /** Independently supplied qualification/custody inputs, never included in bundle identity. */
  readonly qualification:readonly ExactArtifact[];
 };
} | {
 readonly outcome:'blocked';
 readonly diagnosticProfile:ProfilePin;
 readonly diagnostics:ExactArtifact;
 readonly sql?:never;
 readonly coverage?:never;
 readonly statementInventory?:never;
};
export interface BootstrapGenerationRequest {
 readonly interfaceVersion:'truss-bootstrap-generation/0.1.0';
 readonly bundle:BootstrapBundle;
 readonly resourceProfile:ProfilePin;
 /** Supplied original independent evidence is re-admitted; no native tests run during generation. */
 readonly qualification:{readonly state:'absent'} | {
  readonly state:'supplied';readonly targetProfile:ProfilePin;readonly evidence:ExactArtifact;
 };
 readonly limits:{readonly inputBytes:string;readonly outputBytes:string;
  readonly statements:string;readonly workUnits:string};
 readonly signal?:AbortSignal;
}
export interface BootstrapGenerationTooling {
 readonly generationProfile:ProfilePin;
 /** Pure bounded computation using existing pinned UMF APIs and registered composition; no connection/code loading. */
 generate(request:BootstrapGenerationRequest):Promise<BootstrapGenerationResult>;
}
