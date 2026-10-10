import type {BootstrapDependencyReconciliation, DependencyQueryObservation} from '../../../02-design/contracts/bindings/truss-bootstrap-dependency-reconciliation-v0.1.proposal';
import type {BootstrapCollectionResult} from '../../../02-design/contracts/bindings/truss-bootstrap-collection-result-v0.1';
import type {ExactArtifact} from '../../../02-design/contracts/bindings/truss-acceptance-input-v0.1';
type Complete = Extract<BootstrapDependencyReconciliation,{outcome:'complete'}>;
type Incomplete = Extract<BootstrapDependencyReconciliation,{outcome:'incomplete'}>;
declare const query:DependencyQueryObservation;
declare const unavailable:Extract<BootstrapCollectionResult,{outcome:'unavailable'}>;
declare const artifact:ExactArtifact;
const completeQueries:Complete['completeQueries'] = [query];
// @ts-expect-error Complete reconciliation needs original query coverage.
const emptyQueries:Complete['completeQueries'] = [];
// @ts-expect-error Unavailable collection cannot supply complete query evidence.
const unavailableQuery:DependencyQueryObservation['collection'] = unavailable;
// @ts-expect-error Incomplete count agreement cannot publish multiplicity.
const incompleteCount:Incomplete['nativeMultiplicity'] = '1';
// @ts-expect-error Incomplete tuple resolution cannot publish semantic edge.
const incompleteEdge:Incomplete['resolvedSemanticEdge'] = artifact;
void [completeQueries, emptyQueries, unavailableQuery, incompleteCount, incompleteEdge];
