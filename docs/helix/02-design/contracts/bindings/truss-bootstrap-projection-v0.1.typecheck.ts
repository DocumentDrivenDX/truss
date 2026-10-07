import type {BootstrapProjectionCustody,BootstrapProjectionResult,BootstrapFieldDisposition} from './truss-bootstrap-inventory-v0.1';
import type {ExactArtifact} from './truss-acceptance-input-v0.1';
declare const custody:BootstrapProjectionCustody;
declare const artifact:ExactArtifact;
declare const declared:Extract<BootstrapFieldDisposition,{kind:'declared'}>;
const refused:BootstrapProjectionResult={...custody,outcome:'incomplete',refusal:artifact};
// @ts-expect-error Incomplete projection has no canonical success artifact.
const falseComplete:BootstrapProjectionResult={...custody,outcome:'incomplete',refusal:artifact,canonicalBasis:artifact};
// @ts-expect-error Complete projection requires actual full basis and correspondence.
const missingBasis:BootstrapProjectionResult={...custody,outcome:'complete',canonicalBasis:artifact};
// @ts-expect-error Every declared fact needs a nonempty contribution inventory.
const emptyContribution:BootstrapFieldDisposition={...declared,contributions:[]};
// @ts-expect-error Complete original fact disposition inventory cannot be empty.
const emptyDispositions:BootstrapProjectionCustody={...custody,dispositions:[]};
void [refused,falseComplete,missingBasis,emptyContribution,emptyDispositions];
