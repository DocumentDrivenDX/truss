/** Unadopted report wire; rebind projection remains distinct from the complete group. */
import type {AcceptanceReport} from './truss-acceptance-report-v0.1';
import type {ProposedHistoricalEvent} from './truss-history-v0.2.proposal';
export type ProposedAcceptanceReport = Omit<AcceptanceReport,'interfaceVersion'|'rebinds'> & {
 readonly interfaceVersion:'truss-acceptance-report/0.2.0-proposal';
 readonly rebinds:readonly Extract<ProposedHistoricalEvent,{readonly operation:'rebind'}>[];
};
