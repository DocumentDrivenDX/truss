/** CONTRACT-008 internal overlap proposal; no native/runtime admission implied. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {BootstrapCompleteCollection} from './truss-bootstrap-collection-result-v0.1';
export interface DependencyQueryObservation {
 readonly queryIdentity:string;
 readonly collection:BootstrapCompleteCollection;
 /** Actual fixed predicate selection; never reconstructed from returned rows. */
 readonly selectorProfile:ProfilePin;
 readonly originalSelector:ExactArtifact;
 readonly originalTermination:ExactArtifact;
 readonly countedRows:readonly {readonly rowOrdinal:string;readonly originalRow:ExactArtifact}[];
}
export interface DependencyTupleQueryCount {
 readonly originalQueryIdentity:string;
 readonly applicabilityEvidence:ExactArtifact;
 /** Exact canonical nonnegative count, including an applicable zero. */
 readonly nativeCount:string;
 readonly originalRowOrdinals:readonly string[];
}
interface ReconciliationCustody {
 readonly interfaceVersion:'truss-bootstrap-dependency-reconciliation/0.1.0';
 readonly originalScope:ExactArtifact;
 readonly originalCut:ExactArtifact;
 readonly originalAttempt:ExactArtifact;
 readonly originalNativeTuple:ExactArtifact;
 readonly tupleProfile:ProfilePin;
 readonly completeQueries:readonly [DependencyQueryObservation,...DependencyQueryObservation[]];
 readonly resourceEvidence:ExactArtifact;
}
export type BootstrapDependencyReconciliation = ReconciliationCustody & (
 {readonly outcome:'complete';
  /** All same-cut complete applicable selectors, not only positive observations. */
  readonly applicableCounts:readonly [DependencyTupleQueryCount,...DependencyTupleQueryCount[]];
  /** Exact positive canonical count after all applicable counts agree. */
  readonly nativeMultiplicity:string;
  readonly agreementEvidence:ExactArtifact;
  readonly resolvedSemanticEdge:ExactArtifact;
  readonly semanticProfile:ProfilePin} |
 {readonly outcome:'incomplete';
  readonly reason:'conflicting_counts'|'unresolved_selector'|'unresolved_tuple'|'unresolved_endpoint'|'cut'|'resource';
  readonly retainedCounts:readonly DependencyTupleQueryCount[];
  readonly unresolvedEvidence:ExactArtifact;
  readonly nativeMultiplicity?:never;
  readonly agreementEvidence?:never;
  readonly resolvedSemanticEdge?:never});
/** Runtime must verify counts/ordinal membership, original row bytes, exact selector
 * applicability, complete query-set membership, identical cut and full resolution.
 * This wire does not identify physical rows across duplicate observations. */
